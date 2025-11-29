from django.db.models import Count, Max
from social.models import *

class BadgeChecker:
    def __init__(self, user):
        self.user = user
    
    def check_all_badges(self):
        """Vérifie tous les badges pour un utilisateur"""
        badges_earned = []
        
        # Récupérer les stats de l'utilisateur
        user_stats = self._get_user_stats()
        
        # Vérifier chaque badge
        all_badges = Badge.objects.all()
        for badge in all_badges:
            if self._qualifies_for_badge(badge, user_stats):
                user_badge, created = UserBadge.objects.get_or_create(
                    user=self.user,
                    badge=badge
                )
                if created:
                    badges_earned.append(badge)
        
        return badges_earned
    
    def _get_user_stats(self):
        """Récupère les statistiques de l'utilisateur"""
        posts_count = LookbookPost.objects.filter(user=self.user).count()
        
        # Likes max sur un post
        max_likes_post = LookbookPost.objects.filter(user=self.user).aggregate(
            max_likes=Max('likes_count')
        )['max_likes'] or 0
        
        # Followers count
        followers_count = UserFollow.objects.filter(following=self.user).count()
        
        # Posts avec plus de 20 likes
        quality_posts_count = LookbookPost.objects.filter(
            user=self.user, 
            likes_count__gte=20
        ).count()
        
        # Comments count
        from social.models import PostComment
        comments_count = PostComment.objects.filter(user=self.user).count()
        
        # Saves count (posts sauvegardés par l'utilisateur)
        from social.models import PostSave
        saves_count = PostSave.objects.filter(user=self.user).count()
        
        return {
            'posts_count': posts_count,
            'max_likes_on_post': max_likes_post,
            'followers_count': followers_count,
            'quality_posts_count': quality_posts_count,
            'comments_count': comments_count,
            'saves_count': saves_count,
        }
    
    def _qualifies_for_badge(self, badge, user_stats):
        """Vérifie si l'utilisateur remplit les critères du badge"""
        criteria = badge.criteria
        
        for condition, required_value in criteria.items():
            user_value = user_stats.get(condition, 0)
            
            if condition == 'posts_count' and user_value < required_value:
                return False
            elif condition == 'max_likes_on_post' and user_value < required_value:
                return False
            elif condition == 'followers_count' and user_value < required_value:
                return False
            elif condition == 'quality_posts_count' and user_value < required_value:
                return False
            elif condition == 'comments_count' and user_value < required_value:
                return False
            elif condition == 'saves_count' and user_value < required_value:
                return False
        
        return True