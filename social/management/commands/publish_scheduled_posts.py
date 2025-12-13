from django.core.management.base import BaseCommand
from django.utils import timezone
from social.models import PostDraft, LookbookPost


class Command(BaseCommand):
    help = 'Check and publish scheduled posts that are due'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be published without actually publishing',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options['dry_run']

        self.stdout.write(f'Checking scheduled posts at {now}...')

        # Find all scheduled drafts that are due
        scheduled_drafts = PostDraft.objects.filter(
            status='scheduled',
            scheduled_for__lte=now
        ).select_related('user', 'outfit')

        count = scheduled_drafts.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No scheduled posts are due.'))
            return

        self.stdout.write(f'Found {count} scheduled post(s) to publish...')

        published = 0
        errors = 0

        for draft in scheduled_drafts:
            try:
                if dry_run:
                    self.stdout.write(
                        f'  [DRY RUN] Would publish: "{draft.outfit.name}" by {draft.user.email}'
                    )
                else:
                    # Create the post
                    post = LookbookPost.objects.create(
                        user=draft.user,
                        outfit=draft.outfit,
                        caption=draft.caption,
                        hashtags=draft.hashtags,
                        enhanced_images=draft.enhanced_images,
                        visibility=draft.visibility
                    )

                    # Mark draft as published
                    draft.status = 'published'
                    draft.save()

                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Published: "{draft.outfit.name}" by {draft.user.email}')
                    )

                published += 1

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error publishing draft {draft.id}: {e}')
                )

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n[DRY RUN] Would have published {published} posts.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nDone! Published {published} posts, {errors} errors.'))
