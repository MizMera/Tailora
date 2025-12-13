from django.core.management.base import BaseCommand
from social.models import Badge


class Command(BaseCommand):
    help = 'Create default badges for the social module'

    def handle(self, *args, **options):
        badges = [
            {
                'name': 'First Post',
                'badge_type': 'starter',
                'description': 'Created your first lookbook post',
                'icon': '🌟',
                'color': '#FFD700',
                'criteria': {'posts_count': 1}
            },
            {
                'name': 'Style Starter',
                'badge_type': 'starter',
                'description': 'Created 5 lookbook posts',
                'icon': '✨',
                'color': '#87CEEB',
                'criteria': {'posts_count': 5}
            },
            {
                'name': 'Fashion Creator',
                'badge_type': 'creator',
                'description': 'Created 10 lookbook posts',
                'icon': '🎨',
                'color': '#9370DB',
                'criteria': {'posts_count': 10}
            },
            {
                'name': 'Style Icon',
                'badge_type': 'creator',
                'description': 'Created 25 lookbook posts',
                'icon': '👑',
                'color': '#FFD700',
                'criteria': {'posts_count': 25}
            },
            {
                'name': 'Rising Star',
                'badge_type': 'popular',
                'description': 'Got 10 likes on a single post',
                'icon': '⭐',
                'color': '#FF6B6B',
                'criteria': {'max_likes_on_post': 10}
            },
            {
                'name': 'Trendsetter',
                'badge_type': 'trendsetter',
                'description': 'Got 50 likes on a single post',
                'icon': '🔥',
                'color': '#FF4500',
                'criteria': {'max_likes_on_post': 50}
            },
            {
                'name': 'Viral Sensation',
                'badge_type': 'trendsetter',
                'description': 'Got 100 likes on a single post',
                'icon': '💫',
                'color': '#9400D3',
                'criteria': {'max_likes_on_post': 100}
            },
            {
                'name': 'Social Butterfly',
                'badge_type': 'social',
                'description': 'Gained 10 followers',
                'icon': '🦋',
                'color': '#FF69B4',
                'criteria': {'followers_count': 10}
            },
            {
                'name': 'Influencer',
                'badge_type': 'influencer',
                'description': 'Gained 50 followers',
                'icon': '💎',
                'color': '#00CED1',
                'criteria': {'followers_count': 50}
            },
            {
                'name': 'Fashion Legend',
                'badge_type': 'influencer',
                'description': 'Gained 100 followers',
                'icon': '🏆',
                'color': '#FFD700',
                'criteria': {'followers_count': 100}
            },
            {
                'name': 'Community Member',
                'badge_type': 'social',
                'description': 'Left 10 comments on posts',
                'icon': '💬',
                'color': '#32CD32',
                'criteria': {'comments_count': 10}
            },
            {
                'name': 'Quality Curator',
                'badge_type': 'champion',
                'description': 'Had 3 posts with 20+ likes',
                'icon': '🎯',
                'color': '#FF8C00',
                'criteria': {'quality_posts_count': 3}
            },
        ]

        created_count = 0
        updated_count = 0

        for badge_data in badges:
            badge, created = Badge.objects.update_or_create(
                name=badge_data['name'],
                defaults={
                    'badge_type': badge_data['badge_type'],
                    'description': badge_data['description'],
                    'icon': badge_data['icon'],
                    'color': badge_data['color'],
                    'criteria': badge_data['criteria'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created badge: {badge.icon} {badge.name}'))
            else:
                updated_count += 1
                self.stdout.write(f'Updated badge: {badge.icon} {badge.name}')

        self.stdout.write(self.style.SUCCESS(f'\nDone! Created {created_count}, updated {updated_count} badges.'))
