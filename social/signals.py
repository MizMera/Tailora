from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LookbookPost
from .utils.post_badges import PostBadgeSystem

@receiver(post_save, sender=LookbookPost)
def update_post_badge_on_save(sender, instance, **kwargs):
    """Update badge when a post is saved"""
    PostBadgeSystem.update_post_badge(instance)
