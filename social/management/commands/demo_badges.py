from django.core.management.base import BaseCommand
from social.models import LookbookPost


class Command(BaseCommand):
    help = 'Update post likes for demo badges'

    def handle(self, *args, **options):
        posts = list(LookbookPost.objects.all())
        badge_counts = [250, 150, 75, 45, 30]
        
        for i, post in enumerate(posts):
            likes = badge_counts[i % len(badge_counts)]
            post.likes_count = likes
            post.save()
            badge = 'Iconic' if likes >= 200 else 'Star' if likes >= 100 else 'Viral' if likes >= 50 else 'None'
            self.stdout.write(f'{post.outfit.name}: {likes} likes ({badge})')
        
        self.stdout.write(self.style.SUCCESS(f'Updated {len(posts)} posts!'))
