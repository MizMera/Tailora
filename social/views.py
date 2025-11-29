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

