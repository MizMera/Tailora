from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Exists, OuterRef
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
import json
from django.db import transaction
from django.core.cache import cache

from .models import LookbookPost, PostLike, PostComment, PostSave, UserFollow, StyleChallenge, PostDraft, AIEngagementData
from .services import AIEngagementOptimizer
from outfits.models import Outfit
from users.models import User


@login_required
def feed_view(request):
    """Main social feed with Following and Community tabs"""
    # Get feed type from query param (default to 'community' for better discovery)
    feed_type = request.GET.get('feed', 'community')
    
    # Get users the current user follows
    following_ids = UserFollow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)
    
    if feed_type == 'following':
        # Show posts from followed users + own posts
        posts = LookbookPost.objects.filter(
            Q(user_id__in=following_ids) | Q(user=request.user),
            visibility__in=['public', 'followers']
        ).select_related('user', 'outfit').prefetch_related('likes', 'comments').annotate(
            is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user)),
            is_saved=Exists(PostSave.objects.filter(post=OuterRef('pk'), user=request.user))
        ).order_by('-created_at')[:30]
    else:
        # Community feed - show all public posts from everyone
        posts = LookbookPost.objects.filter(
            visibility='public'
        ).exclude(
            user=request.user  # Optionally exclude own posts in community view
        ).select_related('user', 'outfit').prefetch_related('likes', 'comments').annotate(
            is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user)),
            is_saved=Exists(PostSave.objects.filter(post=OuterRef('pk'), user=request.user)),
            is_following=Exists(UserFollow.objects.filter(follower=request.user, following=OuterRef('user')))
        ).order_by('-created_at')[:30]
    
    # Get active challenges
    active_challenges = StyleChallenge.objects.filter(status='active')[:3]
    
    # User stats
    followers_count = UserFollow.objects.filter(following=request.user).count()
    following_count = UserFollow.objects.filter(follower=request.user).count()
    posts_count = LookbookPost.objects.filter(user=request.user).count()
    
    # Community stats
    total_community_posts = LookbookPost.objects.filter(visibility='public').count()
    total_members = User.objects.filter(is_active=True).count()
    
    # Get drafts data - exclude published
    drafts = PostDraft.objects.filter(
        user=request.user,
        status__in=['draft', 'scheduled']
    )
    draft_count = drafts.count()
    
    # Get recent drafts (max 3)
    recent_drafts = drafts.filter(status='draft').order_by('-updated_at')[:3]
    
    # Get scheduled posts
    scheduled_posts = drafts.filter(
        status='scheduled', 
        scheduled_for__gt=timezone.now()
    ).order_by('scheduled_for')[:3]
    
    # Suggested users to follow (for community tab)
    suggested_users = []
    if feed_type == 'community':
        suggested_users = User.objects.exclude(
            id=request.user.id
        ).exclude(
            id__in=following_ids
        ).annotate(
            num_followers=Count('followers'),
            num_posts=Count('lookbook_posts')
        ).filter(
            num_posts__gt=0  # Only suggest users with posts
        ).order_by('-num_followers')[:5]
    
    context = {
        'posts': posts,
        'feed_type': feed_type,
        'active_challenges': active_challenges,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
        'total_community_posts': total_community_posts,
        'total_members': total_members,
        'suggested_users': suggested_users,
        'drafts': drafts.exists(),
        'draft_count': draft_count,
        'recent_drafts': recent_drafts,
        'scheduled_posts': scheduled_posts,
    }
    
    return render(request, 'social/feed.html', context)


@login_required
def discover_view(request):
    """Discover page showing trending and popular posts"""
    # Get all public posts
    posts = LookbookPost.objects.filter(
        visibility='public'
    ).select_related('user', 'outfit').prefetch_related('likes').annotate(
        is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user)),
        is_saved=Exists(PostSave.objects.filter(post=OuterRef('pk'), user=request.user))
    ).order_by('-likes_count', '-created_at')[:30]
    
    context = {
        'posts': posts,
        'is_discover': True,
    }
    
    return render(request, 'social/discover.html', context)


@login_required
def create_post(request):
    """Create a new lookbook post with AI optimization and scheduling support"""
    if request.method == 'POST':
        outfit_id = request.POST.get('outfit')
        caption = request.POST.get('caption', '')
        visibility = request.POST.get('visibility', 'public')
        hashtags_raw = request.POST.get('hashtags', '').split()
        
        # New AI and draft features
        use_ai = request.POST.get('use_ai') == 'true'
        save_as_draft = request.POST.get('save_as_draft') == 'true'
        schedule_post = request.POST.get('schedule_post') == 'true'
        scheduled_time_str = request.POST.get('scheduled_time') or request.POST.get('scheduled_time_custom')
        enhancement_style = request.POST.get('photo_style', '') if request.POST.get('enhance_photos') == 'true' else ''
        
        # Detect if user selected an AI "Best Time to Post"
        ai_time_selected = bool(request.POST.get('scheduled_time'))
        
        # Process hashtags
        hashtags = []
        for tag in hashtags_raw:
            tag = tag.strip()
            if tag and not tag.startswith('#'):
                tag = f"#{tag}"
            if tag:
                hashtags.append(tag)
        
        if not outfit_id:
            messages.error(request, 'Please select an outfit.')
            return redirect('social:create_post')
        
        outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
        
        # Get enhanced images
        enhanced_images_json = request.POST.get('enhanced_images', '{}')
        try:
            enhanced_images = json.loads(enhanced_images_json)
        except json.JSONDecodeError:
            enhanced_images = {}
        
        # Handle scheduling
        scheduled_for = None
        if schedule_post and scheduled_time_str:
            try:
                from django.utils.dateparse import parse_datetime
                scheduled_for = parse_datetime(scheduled_time_str)
                
                if scheduled_for:
                    if timezone.is_naive(scheduled_for):
                        scheduled_for = timezone.make_aware(scheduled_for, timezone.get_current_timezone())
                    
                    if scheduled_for <= timezone.now():
                        messages.error(request, 'Scheduled time must be in the future.')
                        return redirect('social:create_post')
                else:
                    messages.error(request, 'Invalid scheduled time format.')
                    return redirect('social:create_post')
            except Exception as e:
                messages.error(request, f'Error with scheduled time: {e}')
                return redirect('social:create_post')
        elif ai_time_selected and scheduled_time_str:
            try:
                from django.utils.dateparse import parse_datetime
                scheduled_for = parse_datetime(scheduled_time_str)
                
                if scheduled_for:
                    if timezone.is_naive(scheduled_for):
                        scheduled_for = timezone.make_aware(scheduled_for, timezone.get_current_timezone())
                    
                    if scheduled_for <= timezone.now():
                        messages.error(request, 'Scheduled time must be in the future.')
                        return redirect('social:create_post')
            except Exception as e:
                pass  # Continue without scheduled time
        
        # Handle AI optimization if requested
        ai_insights = None
        if use_ai:
            try:
                ai_optimizer = AIEngagementOptimizer(request.user)
                ai_hashtags = ai_optimizer.generate_hashtag_suggestions(caption)
                ai_captions = ai_optimizer.generate_caption_suggestions(outfit.name)
                best_time = ai_optimizer.analyze_best_time()
                
                ai_insights = {
                    'hashtags': ai_hashtags,
                    'captions': ai_captions,
                    'best_time': best_time,
                    'confidence': ai_optimizer.calculate_confidence_score({
                        'caption': caption,
                        'hashtags': hashtags,
                        'outfit': outfit.name,
                        'suggested_time': best_time
                    })
                }
            except Exception as e:
                ai_insights = None
        
        # Handle draft/schedule
        if save_as_draft:
            draft = PostDraft.objects.create(
                user=request.user,
                outfit=outfit,
                caption=caption,
                hashtags=hashtags,
                enhanced_images=enhanced_images,
                visibility=visibility,
                scheduled_for=scheduled_for,
                status='scheduled' if schedule_post and scheduled_for else 'draft'
            )
            
            # Add AI data to draft if available
            if ai_insights:
                draft.ai_optimized_hashtags = ai_insights['hashtags']
                draft.ai_suggested_captions = ai_insights['captions']
                draft.ai_best_time = ai_insights['best_time']
                draft.save()
            
            if schedule_post and scheduled_for:
                from django.utils.formats import date_format
                formatted_time = date_format(scheduled_for, "F j, Y g:i A")
                messages.success(request, f'✅ Post scheduled for {formatted_time}')
            else:
                messages.success(request, '✅ Saved as draft!')
            
            return redirect('social:draft_list')
        
        else:
            # If AI time is selected, create a scheduled draft
            if ai_time_selected and scheduled_for:
                draft = PostDraft.objects.create(
                    user=request.user,
                    outfit=outfit,
                    caption=caption,
                    hashtags=hashtags,
                    enhanced_images=enhanced_images,
                    visibility=visibility,
                    scheduled_for=scheduled_for,
                    status='scheduled'
                )
                
                if ai_insights:
                    draft.ai_optimized_hashtags = ai_insights['hashtags']
                    draft.ai_suggested_captions = ai_insights['captions']
                    draft.ai_best_time = ai_insights['best_time']
                    draft.save()
                
                from django.utils.formats import date_format
                formatted_time = date_format(scheduled_for, "F j, Y g:i A")
                messages.success(request, f'✅ Post scheduled for {formatted_time}')
                return redirect('social:draft_list')
            
            # Create immediate post
            post = LookbookPost.objects.create(
                user=request.user,
                outfit=outfit,
                caption=caption,
                hashtags=hashtags,
                enhanced_images=enhanced_images,
                enhancement_style=enhancement_style,
                visibility=visibility
            )
            
            messages.success(request, '✅ Post published successfully!')
            return redirect('social:post_detail', post_id=post.id)
    
    # GET: Show form
    outfits = Outfit.objects.filter(user=request.user).order_by('-created_at')
    now = timezone.now()
    now_formatted = now.strftime('%Y-%m-%dT%H:%M')
    
    # Generate initial AI suggestions
    try:
        ai_optimizer = AIEngagementOptimizer(request.user)
        default_hashtags = ai_optimizer.generate_hashtag_suggestions()
        default_captions = ai_optimizer.generate_caption_suggestions()
    except:
        default_hashtags = ['#fashion', '#style', '#ootd', '#outfit', '#look']
        default_captions = [
            "Loving this look for today! ✨",
            "New outfit alert! What do you think? 👀",
            "Feeling good in this outfit! 💕"
        ]
    
    context = {
        'outfits': outfits,
        'default_hashtags': default_hashtags,
        'default_captions': default_captions,
        'now': timezone.now(),
        'now_formatted': now_formatted,
    }
    
    return render(request, 'social/create_post.html', context)


@login_required
def post_detail(request, post_id):
    """View a single post with comments"""
    post = get_object_or_404(
        LookbookPost.objects.select_related('user', 'outfit').annotate(
            is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user)),
            is_saved=Exists(PostSave.objects.filter(post=OuterRef('pk'), user=request.user))
        ),
        id=post_id
    )
    
    # Check visibility permissions
    if post.visibility == 'private' and post.user != request.user:
        messages.error(request, 'This post is private.')
        return redirect('social:feed')
    
    if post.visibility == 'followers':
        is_following = UserFollow.objects.filter(
            follower=request.user,
            following=post.user
        ).exists()
        if not is_following and post.user != request.user:
            messages.error(request, 'This post is only visible to followers.')
            return redirect('social:feed')
    
    # Get comments
    comments = post.comments.select_related('user').filter(parent_comment__isnull=True).order_by('-created_at')
    
    context = {
        'post': post,
        'comments': comments,
        'is_own_post': post.user == request.user,
    }
    
    return render(request, 'social/post_detail.html', context)


@login_required
def delete_post(request, post_id):
    """Delete a post"""
    post = get_object_or_404(LookbookPost, id=post_id, user=request.user)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('social:feed')
    
    return redirect('social:post_detail', post_id=post_id)


@login_required
def edit_post(request, post_id):
    """Edit a lookbook post caption, visibility and hashtags"""
    post = get_object_or_404(LookbookPost, id=post_id, user=request.user)

    if request.method == 'POST':
        caption = request.POST.get('caption', '').strip()
        visibility = request.POST.get('visibility', post.visibility)
        hashtags_raw = request.POST.get('hashtags', '').strip()
        # Normalize hashtags into list
        hashtags = [h if h.startswith('#') else f"#{h}" for h in hashtags_raw.split() if h]

        post.caption = caption
        post.visibility = visibility if visibility in dict(LookbookPost.VISIBILITY_CHOICES) else post.visibility
        post.hashtags = hashtags
        post.save(update_fields=['caption', 'visibility', 'hashtags', 'updated_at'])

        messages.success(request, 'Post updated successfully!')
        return redirect('social:post_detail', post_id=post.id)

    context = {
        'post': post,
    }
    return render(request, 'social/edit_post.html', context)


@login_required
def toggle_like(request, post_id):
    """Like or unlike a post"""
    post = get_object_or_404(LookbookPost, id=post_id)
    
    like, created = PostLike.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        like.delete()
        post.likes_count = max(0, post.likes_count - 1)
        liked = False
    else:
        post.likes_count += 1
        liked = True
    
    post.save(update_fields=['likes_count'])
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'likes_count': post.likes_count})
    
    return redirect('social:post_detail', post_id=post_id)


@login_required
def toggle_save(request, post_id):
    """Save or unsave a post"""
    post = get_object_or_404(LookbookPost, id=post_id)
    
    save, created = PostSave.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        save.delete()
        post.saves_count = max(0, post.saves_count - 1)
        saved = False
    else:
        post.saves_count += 1
        saved = True
    
    post.save(update_fields=['saves_count'])
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'saved': saved, 'saves_count': post.saves_count})
    
    return redirect('social:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    """Add a comment to a post"""
    post = get_object_or_404(LookbookPost, id=post_id)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        
        if content:
            comment = PostComment.objects.create(
                user=request.user,
                post=post,
                content=content,
                parent_comment_id=parent_id if parent_id else None
            )
            post.comments_count += 1
            post.save(update_fields=['comments_count'])
            
            messages.success(request, 'Comment added!')
    
    return redirect('social:post_detail', post_id=post_id)


@login_required
def delete_comment(request, comment_id):
    """Delete a comment"""
    comment = get_object_or_404(PostComment, id=comment_id, user=request.user)
    post = comment.post
    
    if request.method == 'POST':
        comment.delete()
        post.comments_count = max(0, post.comments_count - 1)
        post.save(update_fields=['comments_count'])
        messages.success(request, 'Comment deleted!')
    
    return redirect('social:post_detail', post_id=post.id)


@login_required
def profile_view(request, user_id):
    """View a user's profile and posts"""
    from users.models import User
    profile_user = get_object_or_404(User, id=user_id)
    
    # Check if current user follows this profile
    is_following = UserFollow.objects.filter(
        follower=request.user,
        following=profile_user
    ).exists() if request.user != profile_user else False
    
    # Get user's posts
    if profile_user == request.user:
        posts = LookbookPost.objects.filter(user=profile_user)
    else:
        # Show only public posts or followers-only if following
        visibility_filter = Q(visibility='public')
        if is_following:
            visibility_filter |= Q(visibility='followers')
        posts = LookbookPost.objects.filter(user=profile_user).filter(visibility_filter)
    
    posts = posts.select_related('outfit').annotate(
        is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user))
    ).order_by('-created_at')
    
    # Stats
    followers_count = UserFollow.objects.filter(following=profile_user).count()
    following_count = UserFollow.objects.filter(follower=profile_user).count()
    posts_count = posts.count()
    
    # Extract username from email
    username = profile_user.email.split('@')[0] if '@' in profile_user.email else profile_user.email
    
    context = {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
        'is_own_profile': profile_user == request.user,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
        'username': username,
    }
    
    return render(request, 'social/profile.html', context)


@login_required
def toggle_follow(request, user_id):
    """Follow or unfollow a user"""
    from users.models import User
    user_to_follow = get_object_or_404(User, id=user_id)
    
    if user_to_follow == request.user:
        messages.error(request, 'You cannot follow yourself.')
        return redirect('social:feed')
    
    follow, created = UserFollow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    if not created:
        follow.delete()
        messages.success(request, f'Unfollowed {user_to_follow.get_full_name()}.')
    else:
        messages.success(request, f'Now following {user_to_follow.get_full_name()}!')
    
    return redirect('social:profile', user_id=user_id)


@login_required
def followers_list(request, user_id):
    """List of user's followers"""
    from users.models import User
    profile_user = get_object_or_404(User, id=user_id)
    
    # Get followers and extract the follower user objects
    follower_relationships = UserFollow.objects.filter(following=profile_user).select_related('follower')
    followers = [relationship.follower for relationship in follower_relationships]
    
    # Get IDs of users that current user is following
    following_ids = UserFollow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)
    
    context = {
        'profile_user': profile_user,
        'users': followers,
        'list_type': 'followers',
        'following_ids': list(following_ids),
    }
    
    return render(request, 'social/followers_list.html', context)


@login_required
def following_list(request, user_id):
    """List of users that this user follows"""
    from users.models import User
    profile_user = get_object_or_404(User, id=user_id)
    
    # Get following relationships and extract the followed user objects
    following_relationships = UserFollow.objects.filter(follower=profile_user).select_related('following')
    following_users = [relationship.following for relationship in following_relationships]
    
    # Get IDs of users that current user is following
    following_ids = UserFollow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)
    
    context = {
        'profile_user': profile_user,
        'users': following_users,
        'list_type': 'following',
        'following_ids': list(following_ids),
    }
    
    return render(request, 'social/following_list.html', context)


@login_required
def saved_posts(request):
    """View saved posts"""
    saves = PostSave.objects.filter(user=request.user).select_related(
        'post', 'post__user', 'post__outfit'
    ).order_by('-created_at')
    
    posts = [save.post for save in saves]
    
    context = {
        'posts': posts,
        'is_saved_view': True,
    }
    
    return render(request, 'social/saved_posts.html', context)


@login_required
def challenges_list(request):
    """List all style challenges"""
    challenges = StyleChallenge.objects.all().order_by('status', '-start_date')
    
    context = {
        'challenges': challenges,
    }
    
    return render(request, 'social/challenges_list.html', context)


@login_required
def challenge_detail(request, challenge_id):
    """View a style challenge and its submissions"""
    challenge = get_object_or_404(StyleChallenge, id=challenge_id)
    
    # Get challenge submissions
    submissions = LookbookPost.objects.filter(
        challenge=challenge,
        visibility='public'
    ).select_related('user', 'outfit').annotate(
        is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user))
    ).order_by('-likes_count', '-created_at')
    
    context = {
        'challenge': challenge,
        'submissions': submissions,
    }
    
    return render(request, 'social/challenge_detail.html', context)


@login_required
def ai_preview(request, outfit_id):
    """
    Generate AI-enhanced previews for outfit items.
    For now, this is a mock implementation that returns the original images.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
        
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    
    # Parse JSON body from frontend (sent via fetch with JSON.stringify)
    try:
        data = json.loads(request.body)
        style = data.get('style', 'auto')
    except (json.JSONDecodeError, ValueError):
        # Fallback to POST data if JSON parsing fails
        style = request.POST.get('style', 'auto')
    
    # Mock AI enhancement - in production this would call an AI service
    enhanced_images = {}
    previews = []
    
    for item in outfit.items.all():
        if item.image:
            # For prototype, we just return the original image
            # In a real app, this would return a processed image URL
            original_url = item.image.url
            enhanced_url = item.image.url
            
            # Store relative path for database
            enhanced_images[str(item.id)] = item.image.name
            
            previews.append({
                'item': {'name': item.name},
                'original': original_url,
                'enhanced': enhanced_url
            })
            
    return JsonResponse({
        'status': 'success', 
        'enhanced_images': enhanced_images,
        'previews': previews,
        'style': style
    })


# ==================== Draft & Scheduling Views ====================

@login_required
def draft_list(request):
    """List all drafts and scheduled posts"""
    now = timezone.now()
    
    # Check and publish overdue scheduled posts
    check_time = now + timedelta(seconds=30)
    overdue_drafts = PostDraft.objects.filter(
        user=request.user,
        status='scheduled',
        scheduled_for__isnull=False,
        scheduled_for__lte=check_time
    )
    
    for draft in overdue_drafts:
        try:
            post = LookbookPost.objects.create(
                user=draft.user,
                outfit=draft.outfit,
                caption=draft.caption,
                hashtags=draft.hashtags,
                enhanced_images=draft.enhanced_images,
                visibility=draft.visibility
            )
            draft.status = 'published'
            draft.save()
        except Exception as e:
            pass
    
    # Get active drafts only
    drafts = PostDraft.objects.filter(
        user=request.user,
        status__in=['draft', 'scheduled']
    ).select_related('outfit').order_by('-created_at')
    
    # Separate drafts and scheduled posts
    draft_list = [d for d in drafts if d.status == 'draft']
    scheduled_list = [d for d in drafts if d.status == 'scheduled']
    
    context = {
        'drafts': draft_list,
        'scheduled_posts': scheduled_list,
        'now': now,
    }
    
    return render(request, 'social/draft_list.html', context)


@login_required
def draft_detail(request, draft_id):
    """View and edit a draft"""
    draft = get_object_or_404(PostDraft, id=draft_id, user=request.user)
    
    # If published, redirect to the post
    if draft.status == 'published':
        posts = LookbookPost.objects.filter(
            user=request.user,
            outfit=draft.outfit,
            caption=draft.caption
        ).order_by('-created_at')
        
        if posts.exists():
            return redirect('social:post_detail', post_id=posts.first().id)
        else:
            return redirect('social:draft_list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update':
            draft.caption = request.POST.get('caption', '')
            
            # Process hashtags
            hashtags_raw = request.POST.get('hashtags', '')
            hashtags = []
            for tag in hashtags_raw.split():
                tag = tag.strip()
                if tag and not tag.startswith('#'):
                    tag = f"#{tag}"
                if tag:
                    hashtags.append(tag)
            draft.hashtags = hashtags
            draft.visibility = request.POST.get('visibility', 'public')
            
            # Handle scheduling
            schedule_post = request.POST.get('schedule_post') == 'true'
            scheduled_time = request.POST.get('scheduled_time')
            
            if schedule_post and scheduled_time:
                try:
                    from django.utils.dateparse import parse_datetime
                    scheduled_dt = parse_datetime(scheduled_time)
                    
                    if scheduled_dt:
                        if timezone.is_naive(scheduled_dt):
                            scheduled_dt = timezone.make_aware(scheduled_dt, timezone.get_current_timezone())
                        
                        if scheduled_dt <= timezone.now():
                            messages.warning(request, 'Scheduled time must be in the future. Draft saved but not scheduled.')
                            draft.status = 'draft'
                            draft.scheduled_for = None
                        else:
                            draft.scheduled_for = scheduled_dt
                            draft.status = 'scheduled'
                            messages.success(request, f'Post scheduled for {scheduled_dt.strftime("%Y-%m-%d %H:%M")}')
                    else:
                        draft.status = 'draft'
                        draft.scheduled_for = None
                except Exception as e:
                    draft.status = 'draft'
                    draft.scheduled_for = None
                    messages.error(request, 'Invalid date/time format. Draft saved but not scheduled.')
            else:
                draft.status = 'draft'
                draft.scheduled_for = None
            
            draft.save()
            messages.success(request, 'Draft updated!')
        
        elif action == 'delete':
            draft.delete()
            messages.success(request, 'Draft deleted!')
            return redirect('social:draft_list')
        
        elif action == 'publish':
            post = draft.publish()
            messages.success(request, 'Post published!')
            return redirect('social:post_detail', post_id=post.id)
        
        return redirect('social:draft_detail', draft_id=draft.id)
    
    # GET: Show draft
    ai_optimizer = AIEngagementOptimizer(request.user)
    now = timezone.now()
    
    # Format scheduled time for input
    scheduled_time_formatted = None
    if draft.scheduled_for:
        if timezone.is_naive(draft.scheduled_for):
            scheduled_dt = timezone.make_aware(draft.scheduled_for, timezone.get_current_timezone())
            scheduled_time_formatted = scheduled_dt.strftime('%Y-%m-%dT%H:%M')
        else:
            scheduled_time_formatted = draft.scheduled_for.astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%dT%H:%M')
    
    context = {
        'draft': draft,
        'ai_hashtags': ai_optimizer.generate_hashtag_suggestions(draft.caption),
        'ai_captions': ai_optimizer.generate_caption_suggestions(draft.outfit.name if draft.outfit else ""),
        'best_time': ai_optimizer.analyze_best_time(),
        'suggested_times': [
            (now + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            (now + timedelta(days=1)).replace(hour=9, minute=0, second=0).strftime('%Y-%m-%dT%H:%M'),
            (now + timedelta(days=1)).replace(hour=18, minute=0, second=0).strftime('%Y-%m-%dT%H:%M'),
        ],
        'visibility_choices': LookbookPost.VISIBILITY_CHOICES,
        'now': now,
        'scheduled_time_formatted': scheduled_time_formatted,
        'is_scheduled': draft.status == 'scheduled' and draft.scheduled_for,
    }
    
    return render(request, 'social/draft_detail.html', context)


@login_required
def quick_publish_draft(request, draft_id):
    """Quick publish draft from feed (AJAX)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        draft = get_object_or_404(PostDraft, id=draft_id, user=request.user)
        
        if draft.status == 'scheduled':
            draft.scheduled_for = None
        
        post = draft.publish()
        
        return JsonResponse({
            'status': 'success',
            'post_id': str(post.id),
            'message': 'Post published successfully!'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def toggle_draft_save(request, post_id=None):
    """Save current post as draft from feed or create page"""
    if request.method == 'POST':
        if post_id:
            post = get_object_or_404(LookbookPost, id=post_id, user=request.user)
            draft = PostDraft.objects.create(
                user=request.user,
                outfit=post.outfit,
                caption=post.caption,
                hashtags=post.hashtags,
                enhanced_images=post.enhanced_images,
                visibility=post.visibility,
                status='draft'
            )
            messages.success(request, 'Post saved as draft!')
            return redirect('social:draft_detail', draft_id=draft.id)
        else:
            outfit_id = request.POST.get('outfit')
            caption = request.POST.get('caption', '')
            visibility = request.POST.get('visibility', 'public')
            hashtags_raw = request.POST.get('hashtags', '').split()
            
            hashtags = []
            for tag in hashtags_raw:
                tag = tag.strip()
                if tag and not tag.startswith('#'):
                    tag = f"#{tag}"
                if tag:
                    hashtags.append(tag)
            
            if not outfit_id:
                messages.error(request, 'Please select an outfit to save as draft.')
                return redirect('social:create_post')
            
            outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
            
            enhanced_images_json = request.POST.get('enhanced_images', '{}')
            try:
                enhanced_images = json.loads(enhanced_images_json)
            except:
                enhanced_images = {}
            
            draft = PostDraft.objects.create(
                user=request.user,
                outfit=outfit,
                caption=caption,
                hashtags=hashtags,
                enhanced_images=enhanced_images,
                visibility=visibility,
                status='draft'
            )
            
            messages.success(request, 'Draft saved!')
            return redirect('social:draft_detail', draft_id=draft.id)
    
    return redirect('social:create_post')


@login_required
def ai_get_suggestions(request):
    """AJAX endpoint to get AI suggestions"""
    if request.method == 'POST':
        data = json.loads(request.body)
        caption = data.get('caption', '')
        outfit_id = data.get('outfit_id')
        
        ai_optimizer = AIEngagementOptimizer(request.user)
        
        outfit_name = ""
        if outfit_id:
            try:
                outfit = Outfit.objects.get(id=outfit_id, user=request.user)
                outfit_name = outfit.name
            except:
                pass
        
        hashtags = ai_optimizer.generate_hashtag_suggestions(caption)
        captions = ai_optimizer.generate_caption_suggestions(outfit_name)
        best_time = ai_optimizer.analyze_best_time()
        
        return JsonResponse({
            'hashtags': hashtags,
            'captions': captions,
            'best_time': best_time.isoformat(),
            'best_time_formatted': best_time.strftime('%A, %B %d at %I:%M %p'),
            'confidence_score': ai_optimizer.calculate_confidence_score({
                'caption': caption,
                'hashtags': [],
                'outfit': outfit_name,
                'suggested_time': best_time
            })
        })
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
def post_insights(request, post_id):
    """View AI insights for a post"""
    post = get_object_or_404(LookbookPost, id=post_id, user=request.user)
    
    try:
        insights = AIEngagementData.objects.get(post=post)
    except AIEngagementData.DoesNotExist:
        ai_optimizer = AIEngagementOptimizer(request.user)
        
        insights = AIEngagementData.objects.create(
            post=post,
            optimal_post_time=ai_optimizer.analyze_best_time(),
            hashtag_suggestions=ai_optimizer.generate_hashtag_suggestions(post.caption),
            caption_suggestions=ai_optimizer.generate_caption_suggestions(post.outfit.name),
            predicted_likes=post.likes_count,
            predicted_comments=post.comments_count,
            predicted_saves=post.saves_count,
            confidence_score=0.7
        )
    
    performance_data = {
        'actual_likes': post.likes_count,
        'actual_comments': post.comments_count,
        'actual_saves': post.saves_count,
        'predicted_likes': insights.predicted_likes,
        'predicted_comments': insights.predicted_comments,
        'predicted_saves': insights.predicted_saves,
    }
    
    context = {
        'post': post,
        'insights': insights,
        'performance_data': performance_data,
    }
    
    return render(request, 'social/post_insights.html', context)


@login_required
def check_scheduled_posts_ajax(request):
    """Check and publish scheduled posts (AJAX)"""
    now_utc = timezone.now()
    
    drafts_to_publish = PostDraft.objects.filter(
        user=request.user,
        status='scheduled',
        scheduled_for__isnull=False,
        scheduled_for__lte=now_utc
    ).select_related('outfit')
    
    published = []
    for draft in drafts_to_publish:
        try:
            post = LookbookPost.objects.create(
                user=draft.user,
                outfit=draft.outfit,
                caption=draft.caption,
                hashtags=draft.hashtags,
                enhanced_images=draft.enhanced_images,
                visibility=draft.visibility
            )
            draft.status = 'published'
            draft.save()
            published.append({
                'draft_id': str(draft.id),
                'post_id': str(post.id),
            })
        except Exception as e:
            pass
    
    return JsonResponse({
        'status': 'success',
        'published': published,
        'count': len(published),
        'server_time_utc': now_utc.isoformat(),
    })


@login_required
def manual_check_scheduled(request):
    """Manually check and publish scheduled posts"""
    if request.method == 'POST':
        now = timezone.now()
        scheduled_drafts = PostDraft.objects.filter(
            status='scheduled',
            scheduled_for__lte=now
        ).select_related('user', 'outfit')
        
        published = []
        for draft in scheduled_drafts:
            post = LookbookPost.objects.create(
                user=draft.user,
                outfit=draft.outfit,
                caption=draft.caption,
                hashtags=draft.hashtags,
                enhanced_images=draft.enhanced_images,
                visibility=draft.visibility
            )
            draft.status = 'published'
            draft.save()
            published.append({
                'draft': draft,
                'post': post
            })
        
        context = {
            'published': published,
            'count': len(published),
            'now': now
        }
        return render(request, 'social/manual_check.html', context)
    
    scheduled_drafts = PostDraft.objects.filter(
        status='scheduled'
    ).select_related('user', 'outfit').order_by('scheduled_for')
    
    context = {
        'scheduled_drafts': scheduled_drafts,
        'now': timezone.now()
    }
    return render(request, 'social/manual_check.html', context)


# ==================== REST API Views ====================

from rest_framework import viewsets, status, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .serializers import (
    LookbookPostSerializer,
    PostCommentSerializer,
    UserFollowSerializer,
    StyleChallengeSerializer
)


class SocialPagination(PageNumberPagination):
    """Custom pagination for social items"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class LookbookPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for lookbook posts
    
    Endpoints:
    - GET /api/social/posts/ - List posts
    - POST /api/social/posts/ - Create post
    - GET /api/social/posts/{id}/ - Get post details
    - PUT /api/social/posts/{id}/ - Update post
    - DELETE /api/social/posts/{id}/ - Delete post
    
    Custom actions:
    - GET /api/social/posts/feed/ - Personalized feed
    - GET /api/social/posts/discover/ - Discover trending posts
    - POST /api/social/posts/{id}/like/ - Like/unlike post
    - POST /api/social/posts/{id}/save/ - Save/unsave post
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = LookbookPostSerializer
    pagination_class = SocialPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'visibility', 'challenge']
    search_fields = ['caption', 'hashtags']
    ordering_fields = ['created_at', 'likes_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return appropriate posts based on visibility
        """
        user = self.request.user
        queryset = LookbookPost.objects.select_related('user', 'outfit')
        
        if self.action in ['list', 'retrieve']:
            if user.is_authenticated:
                # Users can see public posts, their own posts, and followers-only posts if they follow the user
                following_ids = UserFollow.objects.filter(follower=user).values_list('following_id', flat=True)
                
                return queryset.filter(
                    Q(visibility='public') |
                    Q(user=user) |
                    Q(visibility='followers', user_id__in=following_ids)
                )
            else:
                return queryset.filter(visibility='public')
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def feed(self, request):
        """
        Get personalized feed for current user
        GET /api/social/posts/feed/
        """
        user = request.user
        following_ids = UserFollow.objects.filter(follower=user).values_list('following_id', flat=True)
        
        # Feed logic: Posts from followed users + own posts
        feed_posts = LookbookPost.objects.filter(
            Q(user_id__in=following_ids) | Q(user=user),
            visibility__in=['public', 'followers']
        ).select_related('user', 'outfit').order_by('-created_at')
        
        page = self.paginate_queryset(feed_posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(feed_posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def discover(self, request):
        """
        Get trending/popular posts
        GET /api/social/posts/discover/
        """
        # Discover logic: Public posts sorted by likes and recency
        discover_posts = LookbookPost.objects.filter(
            visibility='public'
        ).select_related('user', 'outfit').order_by('-likes_count', '-created_at')
        
        page = self.paginate_queryset(discover_posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(discover_posts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        """
        Like or unlike a post
        POST /api/social/posts/{id}/like/
        """
        post = self.get_object()
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            like.delete()
            post.likes_count = max(0, post.likes_count - 1)
            liked = False
        else:
            post.likes_count += 1
            liked = True
            
        post.save(update_fields=['likes_count'])
        
        return Response({
            'status': 'success',
            'liked': liked,
            'likes_count': post.likes_count
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def save(self, request, pk=None):
        """
        Save or unsave a post
        POST /api/social/posts/{id}/save/
        """
        post = self.get_object()
        save, created = PostSave.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            save.delete()
            post.saves_count = max(0, post.saves_count - 1)
            saved = False
        else:
            post.saves_count += 1
            saved = True
            
        post.save(update_fields=['saves_count'])
        
        return Response({
            'status': 'success',
            'saved': saved,
            'saves_count': post.saves_count
        })


class PostCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for post comments
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = PostCommentSerializer
    pagination_class = SocialPagination
    
    def get_queryset(self):
        """Filter comments by post if provided"""
        queryset = PostComment.objects.select_related('user')
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset.order_by('created_at')
    
    def perform_create(self, serializer):
        post_id = self.request.data.get('post_id')
        if not post_id:
            # Try to get from URL kwargs if nested
            # This depends on URL config, assuming standard query param or body for now
            pass 
            
        # In a real nested router, we'd get post_id from kwargs
        # Here we expect it in the body for simplicity or handle it in serializer
        serializer.save(user=self.request.user)


class UserFollowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing follows
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserFollowSerializer
    pagination_class = SocialPagination
    
    def get_queryset(self):
        """
        List who the user is following or who follows them
        """
        user = self.request.user
        mode = self.request.query_params.get('mode', 'following') # following or followers
        
        if mode == 'followers':
            return UserFollow.objects.filter(following=user).select_related('follower')
        return UserFollow.objects.filter(follower=user).select_related('following')
    
    def perform_create(self, serializer):
        serializer.save(follower=self.request.user)


class StyleChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for style challenges (Read Only)
    """
    queryset = StyleChallenge.objects.all().order_by('-start_date')
    serializer_class = StyleChallengeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = SocialPagination

