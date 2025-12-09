from django.utils import timezone
from django.core.cache import cache
from .models import PostDraft, LookbookPost
import threading

class ScheduledPostsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.lock = threading.Lock()
        
    def __call__(self, request):
        # Vérifier les posts programmés (max une fois par minute)
        if request.user.is_authenticated:
            with self.lock:
                last_check = cache.get('last_scheduled_check')
                
                if not last_check or (timezone.now() - last_check).seconds > 60:
                    self._publish_scheduled_posts()
                    cache.set('last_scheduled_check', timezone.now(), 60)
        
        response = self.get_response(request)
        return response
    
    def _publish_scheduled_posts(self):
        """Publier les posts programmés"""
        from django.utils import timezone
        
        scheduled_drafts = PostDraft.objects.filter(
            status='scheduled',
            scheduled_for__lte=timezone.now()
        ).select_related('user', 'outfit')
        
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
                print(f"[Scheduled] Published post {post.id} from draft {draft.id}")
            except Exception as e:
                print(f"[Scheduled] Error publishing draft {draft.id}: {e}")