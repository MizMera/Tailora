from django.db.models import Q, Count, Exists, OuterRef
from django.core.cache import cache
from datetime import timedelta
from django.utils import timezone
from .models import LookbookPost, UserFollow, PostLike, PostSave


class FeedAlgorithm:
    """
    Personalized feed algorithm for the social hub
    """
    
    def get_personalized_feed(self, user, limit=20):
        """Get personalized feed - posts from followed users and own posts"""
        cache_key = f'feed_{user.id}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Get IDs of users being followed
        following_ids = UserFollow.objects.filter(
            follower=user
        ).values_list('following_id', flat=True)

        # Get posts from followed users and own posts
        posts = LookbookPost.objects.filter(
            Q(user_id__in=following_ids) | Q(user=user),
            visibility__in=['public', 'followers']
        ).select_related('user', 'outfit').prefetch_related('likes', 'comments').annotate(
            is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=user)),
            is_saved=Exists(PostSave.objects.filter(post=OuterRef('pk'), user=user))
        ).order_by('-created_at')[:limit]

        # Cache for 5 minutes
        cache.set(cache_key, posts, 300)
        return posts


class HashtagSystem:
    """
    Hashtag extraction and trending hashtag system
    """
    
    @staticmethod
    def extract_hashtags(text):
        """Extract hashtags from text"""
        import re
        return re.findall(r'#\w+', text.lower())

    @staticmethod
    def get_trending_hashtags(limit=10):
        """Get trending hashtags from recent posts"""
        from collections import Counter
        
        recent_posts = LookbookPost.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).values_list('hashtags', flat=True)

        all_hashtags = []
        for tags in recent_posts:
            if tags:
                all_hashtags.extend(tags)

        return Counter(all_hashtags).most_common(limit)
