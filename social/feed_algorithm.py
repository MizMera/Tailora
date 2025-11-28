# [file name]: feed_algorithm.py
# [file content begin]
from django.db.models import Q, Count, Exists, OuterRef
from django.core.cache import cache
from datetime import timedelta
from django.utils import timezone
from .models import LookbookPost, UserFollow, PostLike, PostSave

# [file name]: feed_algorithm.py
class FeedAlgorithm:
    def get_personalized_feed(self, user, limit=20):
        """Version corrigée - même logique que l'ancien algorithme"""
        cache_key = f'feed_{user.id}'
        cached = cache.get(cache_key)
        if cached: 
            return cached
        
        # Même logique que l'ancien algorithme qui fonctionnait
        following_ids = UserFollow.objects.filter(
            follower=user
        ).values_list('following_id', flat=True)
        
        posts = LookbookPost.objects.filter(
            Q(user_id__in=following_ids) | Q(user=user),
            visibility__in=['public', 'followers']
        ).select_related('user', 'outfit').prefetch_related('likes', 'comments').annotate(
            is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=user)),
            is_saved=Exists(PostSave.objects.filter(post=OuterRef('pk'), user=user))
        ).order_by('-created_at')[:limit]
        
        cache.set(cache_key, posts, 300)
        return posts
class HashtagSystem:
    @staticmethod
    def extract_hashtags(text):
        import re
        return re.findall(r'#\w+', text.lower())
    
    @staticmethod  
    def get_trending_hashtags(limit=10):
        from collections import Counter
        recent_posts = LookbookPost.objects.filter(
            created_at__gte=timezone.now()-timedelta(days=7)
        ).values_list('hashtags', flat=True)
        
        all_hashtags = []
        for tags in recent_posts: 
            all_hashtags.extend(tags)
        
        return Counter(all_hashtags).most_common(limit)
# [file content end]