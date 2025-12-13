from django.db.models import Count, Max
from social.models import Badge, UserBadge, LookbookPost, UserFollow, PostComment, PostSave


class BadgeChecker:
    """
    Check and award badges to users based on their activity
    """
    
    def __init__(self, user):
        self.user = user

    def check_all_badges(self):
        """Check all badges for a user and award any that are earned"""
        badges_earned = []

        # Get user statistics
        user_stats = self._get_user_stats()

        # Check each badge
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
        """Get user statistics for badge checking"""
        posts_count = LookbookPost.objects.filter(user=self.user).count()

        # Max likes on a single post
        max_likes_post = LookbookPost.objects.filter(user=self.user).aggregate(
            max_likes=Max('likes_count')
        )['max_likes'] or 0

        # Followers count
        followers_count = UserFollow.objects.filter(following=self.user).count()

        # Quality posts count (posts with 20+ likes)
        quality_posts_count = LookbookPost.objects.filter(
            user=self.user,
            likes_count__gte=20
        ).count()

        # Comments count
        comments_count = PostComment.objects.filter(user=self.user).count()

        # Saves count (posts saved by this user)
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
        """Check if user qualifies for a specific badge"""
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


def check_user_badges(user):
    """Utility function to check badges for a user"""
    checker = BadgeChecker(user)
    return checker.check_all_badges()
