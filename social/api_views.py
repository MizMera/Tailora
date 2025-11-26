
# ==================== REST API Views ====================

from rest_framework import viewsets, status, permissions
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
    """Custom pagination for social content"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


class LookbookPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for lookbook posts
    
    Endpoints:
    - GET /api/social/posts/ - List posts (feed)
    - POST /api/social/posts/ - Create post
    - GET /api/social/posts/{id}/ - Get post details
    - PUT /api/social/posts/{id}/ - Update post
    - DELETE /api/social/posts/{id}/ - Delete post
    
    Custom actions:
    - POST /api/social/posts/{id}/like/ - Toggle like
    - POST /api/social/posts/{id}/save/ - Toggle save
    - GET /api/social/posts/feed/ - Personalized feed
    - GET /api/social/posts/discover/ - Discover trending
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LookbookPostSerializer
    pagination_class = SocialPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['visibility']
    search_fields = ['caption', 'hashtags']
    ordering_fields = ['created_at', 'likes_count', 'comments_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get posts based on user's permissions"""
        user = self.request.user
        
        # Base: public posts + own posts
        queryset = LookbookPost.objects.filter(
            Q(visibility='public') | Q(user=user)
        ).select_related('user', 'outfit').prefetch_related('outfit__items')
        
        # Add followers-only posts from people user follows
        following_ids = UserFollow.objects.filter(follower=user).values_list('following_id', flat=True)
        followers_posts = Q(user_id__in=following_ids, visibility='followers')
		
        queryset = queryset.filter(Q(visibility='public') | Q(user=user) | followers_posts)
        
        return queryset.distinct()
    
    @action(detail=False, methods=['get'])
    def feed(self, request):
        """
        Personalized feed from followed users
        GET /api/social/posts/feed/
        """
        following_ids = UserFollow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)
        
        posts = LookbookPost.objects.filter(
            Q(user_id__in=following_ids) | Q(user=request.user)
        ).select_related('user', 'outfit').order_by('-created_at')
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def discover(self, request):
        """
        Discover trending posts
        GET /api/social/posts/discover/
        """
        posts = LookbookPost.objects.filter(
            visibility='public'
        ).select_related('user', 'outfit').order_by('-likes_count', '-created_at')
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Toggle like on a post
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
    
    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        """
        Toggle save on a post
        POST /api/social/posts/{id}/save/
        """
        post = self.get_object()
        
        save_obj, created = PostSave.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            save_obj.delete()
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
    
    Endpoints:
    - GET /api/social/comments/ - List comments for a post
    - POST /api/social/comments/ - Add comment
    - DELETE /api/social/comments/{id}/ - Delete comment
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostCommentSerializer
    pagination_class = SocialPagination
    
    def get_queryset(self):
        """Get comments, optionally filtered by post"""
        queryset = PostComment.objects.select_related('user', 'post').prefetch_related('replies')
        
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = queryset.filter(post_id=post_id, parent_comment__isnull=True)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create comment and update post count"""
        comment = serializer.save(user=self.request.user)
        
        # Update comments count
        post = comment.post
        post.comments_count += 1
        post.save(update_fields=['comments_count'])
    
    def perform_destroy(self, instance):
        """Delete comment and update post count"""
        post = instance.post
        instance.delete()
        
        post.comments_count = max(0, post.comments_count - 1)
        post.save(update_fields=['comments_count'])


class UserFollowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user follow relationships
    
    Endpoints:
    - GET /api/social/follows/ - List follows
    - POST /api/social/follows/ - Follow user
    - DELETE /api/social/follows/{id}/ - Unfollow
    
    Custom actions:
    - GET /api/social/follows/followers/ - Get followers
    - GET /api/social/follows/following/ - Get following list
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserFollowSerializer
    pagination_class = SocialPagination
    
    def get_queryset(self):
        """Get user's follow relationships"""
        return UserFollow.objects.filter(
            Q(follower=self.request.user) | Q(following=self.request.user)
        ).select_related('follower', 'following')
    
    @action(detail=False, methods=['get'])
    def followers(self, request):
        """
        Get list of followers
        GET /api/social/follows/followers/
        """
        follows = UserFollow.objects.filter(following=request.user).select_related('follower')
        
        page = self.paginate_queryset(follows)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(follows, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def following(self, request):
        """
        Get list of users you're following
        GET /api/social/follows/following/
        """
        follows = UserFollow.objects.filter(follower=request.user).select_related('following')
        
        page = self.paginate_queryset(follows)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(follows, many=True)
        return Response(serializer.data)


class StyleChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for style challenges (Read-only for users)
    
    Endpoints:
    - GET /api/social/challenges/ - List challenges
    - GET /api/social/challenges/{id}/ - Get challenge details
    
    Custom actions:
    - GET /api/social/challenges/active/ - Get active challenges
    - GET /api/social/challenges/{id}/submissions/ - Get challenge submissions
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StyleChallengeSerializer
    pagination_class = SocialPagination
    queryset = StyleChallenge.objects.all().order_by('-start_date')
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['start_date', 'participants_count']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get active challenges
        GET /api/social/challenges/active/
        """
        challenges = self.queryset.filter(status='active')
        serializer = self.get_serializer(challenges, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """
        Get submissions for a challenge
        GET /api/social/challenges/{id}/submissions/
        """
        challenge = self.get_object()
        posts = LookbookPost.objects.filter(
            challenge=challenge,
            visibility='public'
        ).select_related('user', 'outfit').order_by('-likes_count', '-created_at')
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = LookbookPostSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)
        
        serializer = LookbookPostSerializer(posts, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
