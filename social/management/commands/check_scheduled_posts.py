from django.core.management.base import BaseCommand
from django.utils import timezone
from social.models import PostDraft, LookbookPost

class Command(BaseCommand):
    help = 'Check and publish scheduled posts'
    
    def handle(self, *args, **options):
        scheduled_posts = PostDraft.objects.filter(
            status='scheduled',
            scheduled_for__lte=timezone.now()
        )
        
        count = 0
        for draft in scheduled_posts:
            # Publish the draft
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
            count += 1
            
            self.stdout.write(f'Published: {post.id}')
        
        self.stdout.write(f'Published {count} scheduled posts')