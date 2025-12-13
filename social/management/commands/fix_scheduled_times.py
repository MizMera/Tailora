from django.core.management.base import BaseCommand
from django.utils import timezone
from social.models import PostDraft

class Command(BaseCommand):
    help = 'Fix scheduled times timezone issues'

    def handle(self, *args, **options):
        drafts = PostDraft.objects.filter(
            status='scheduled',
            scheduled_for__isnull=False
        )

        fixed = 0
        published = 0

        for draft in drafts:
            # Fix timezone
            if timezone.is_naive(draft.scheduled_for):
                draft.scheduled_for = timezone.make_aware(draft.scheduled_for, timezone.get_current_timezone())
                draft.save()
                fixed += 1
                self.stdout.write(f"✓ Fixed timezone for draft {draft.id}")

            # Publish if overdue
            if draft.scheduled_for <= timezone.now():
                from social.models import LookbookPost
                post = LookbookPost.objects.create(
                    user=draft.user,
                    outfit=draft.outfit,
                    caption=draft.caption,
                    hashtags=draft.hashtags,
                    enhanced_images=draft.enhanced_images,
                    visibility=draft.visibility
                )
                draft.status = 'published'
                draft.save()
                published += 1
                self.stdout.write(f"✓ Published overdue draft {draft.id} as post {post.id}")

        self.stdout.write(self.style.SUCCESS(f"Fixed {fixed} timezone issues, published {published} overdue posts"))
