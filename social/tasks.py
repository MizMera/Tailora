# social/tasks.py
# Background tasks for scheduled post publishing
# Requires django-background-tasks if using @background decorator
from django.utils import timezone
from .models import PostDraft, LookbookPost
import logging

logger = logging.getLogger(__name__)


def publish_scheduled_posts_task():
    """Task to publish scheduled posts"""
    logger.info("Checking for scheduled posts...")

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
            logger.info(f"Published scheduled post: {post.id}")
        except Exception as e:
            logger.error(f"Error publishing draft {draft.id}: {e}")
