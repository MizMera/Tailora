from django.core.management.base import BaseCommand
from social.models import PostDraft

class Command(BaseCommand):
    help = 'Clean up published drafts'

    def handle(self, *args, **options):
        # Delete published drafts
        deleted_count, _ = PostDraft.objects.filter(status='published').delete()

        self.stdout.write(self.style.SUCCESS(f"✅ Cleaned up {deleted_count} published drafts"))
