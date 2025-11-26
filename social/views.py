from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Exists, OuterRef
from django.http import JsonResponse
from .models import LookbookPost, PostLike, PostComment, PostSave, UserFollow, StyleChallenge
from outfits.models import Outfit


@login_required
def feed_view(request):
    """Main social feed showing posts from followed users"""
    # Get users the current user follows
    following_ids = UserFollow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)
    
    # Get posts from followed users + own posts
    posts = LookbookPost.objects.filter(
        Q(user_id__in=following_ids) | Q(user=request.user),
        visibility__in=['public', 'followers']
    ).select_related('user', 'outfit').prefetch_related('likes', 'comments').annotate(
        is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=request.user)),
        is_saved=Exists(PostSave.objects.filter(post=OuterRef('pk'), user=request.user))
    ).order_by('-created_at')[:20]
    
    # Get active challenges
    active_challenges = StyleChallenge.objects.filter(status='active')[:3]
    
    # User stats
    followers_count = UserFollow.objects.filter(following=request.user).count()
    following_count = UserFollow.objects.filter(follower=request.user).count()
    posts_count = LookbookPost.objects.filter(user=request.user).count()
    
    context = {
        'posts': posts,
        'active_challenges': active_challenges,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
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
    """Create a new lookbook post"""
    if request.method == 'POST':
        outfit_id = request.POST.get('outfit')
        caption = request.POST.get('caption', '')
        visibility = request.POST.get('visibility', 'public')
        hashtags = request.POST.get('hashtags', '').split()
        
        if not outfit_id:
            messages.error(request, 'Please select an outfit.')
            return redirect('social:create_post')
        
        outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
        
        post = LookbookPost.objects.create(
            user=request.user,
            outfit=outfit,
            caption=caption,
            visibility=visibility,
            hashtags=hashtags
        )
        
        messages.success(request, 'Post created successfully!')
        return redirect('social:post_detail', post_id=post.id)
    
    # GET: Show form
    outfits = Outfit.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'outfits': outfits,
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
    
    context = {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
        'is_own_profile': profile_user == request.user,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
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
    user = get_object_or_404(User, id=user_id)
    
    followers = UserFollow.objects.filter(following=user).select_related('follower')
    
    context = {
        'user': user,
        'followers': followers,
    }
    
    return render(request, 'social/followers_list.html', context)


@login_required
def following_list(request, user_id):
    """List of users that this user follows"""
    from users.models import User
    user = get_object_or_404(User, id=user_id)
    
    following = UserFollow.objects.filter(follower=user).select_related('following')
    
    context = {
        'user': user,
        'following': following,
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
