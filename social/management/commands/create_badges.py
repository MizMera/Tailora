# social/management/commands/create_badges.py
from django.core.management.base import BaseCommand
from social.models import Badge

class Command(BaseCommand):
    help = 'Create fashion popularity badges'

    def handle(self, *args, **options):
        POPULARITY_BADGES = [
            {
                'name': '❤️ Look Apprécié',
                'badge_type': 'popularity',
                'description': 'Une tenue a reçu 25 likes',
                'icon': '❤️',
                'color': '#E91E63',
                'criteria': {'max_likes_on_post': 25}
            },
            {
                'name': '🔥 Look Viral', 
                'badge_type': 'popularity',
                'description': 'Une tenue a reçu 50 likes',
                'icon': '🔥',
                'color': '#FF5722',
                'criteria': {'max_likes_on_post': 50}
            },
            {
                'name': '🌟 Look Star',
                'badge_type': 'popularity',
                'description': 'Une tenue a reçu 100 likes',
                'icon': '🌟',
                'color': '#FFD700',
                'criteria': {'max_likes_on_post': 100}
            },
            {
                'name': '💎 Look Iconique',
                'badge_type': 'popularity',
                'description': 'Une tenue a reçu 200 likes',
                'icon': '💎',
                'color': '#00BCD4',
                'criteria': {'max_likes_on_post': 200}
            }
        ]

        created_count = 0
        for badge_data in POPULARITY_BADGES:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Badge créé: {badge.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'🎉 {created_count} badges de popularité créés!')
        )