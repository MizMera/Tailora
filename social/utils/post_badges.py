# social/utils/post_badges.py
class PostBadgeSystem:
    @staticmethod
    def get_badge_for_likes(likes_count):
        """Retourne le badge approprié pour un nombre de likes"""
        if likes_count >= 200:
            return {'icon': '💎', 'name': 'Iconique', 'color': '#00BCD4'}
        elif likes_count >= 100:
            return {'icon': '🌟', 'name': 'Star', 'color': '#FFD700'}
        elif likes_count >= 50:
            return {'icon': '🔥', 'name': 'Viral', 'color': '#FF5722'}
        elif likes_count >= 25:
            return {'icon': '❤️', 'name': 'Apprécié', 'color': '#E91E63'}
        else:
            return None
    
    @staticmethod
    def update_post_badge(post):
        """Met à jour le badge d'un post basé sur ses likes"""
        badge_info = PostBadgeSystem.get_badge_for_likes(post.likes_count)
        if badge_info:
            post.current_badge = f"{badge_info['icon']} {badge_info['name']}"
        else:
            post.current_badge = None
        post.save()