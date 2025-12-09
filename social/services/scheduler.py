# social/services/scheduler.py
from django.utils import timezone
from ..models import PostDraft, LookbookPost

class PostScheduler:
    @staticmethod
    def publish_scheduled_posts():
        """Publier tous les posts programmés en retard"""
        now = timezone.now()
        scheduled_drafts = PostDraft.objects.filter(
            status='scheduled',
            scheduled_for__isnull=False,
            scheduled_for__lte=now
        )
        
        published = []
        for draft in scheduled_drafts:
            try:
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
                published.append(post)
                print(f"[Scheduler] Published post {post.id} from draft {draft.id}")
            except Exception as e:
                print(f"[Scheduler] Error: {e}")
        
        return published