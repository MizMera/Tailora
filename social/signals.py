from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LookbookPost
from .utils.post_badges import PostBadgeSystem

@receiver(post_save, sender=LookbookPost)
def update_post_badge_on_save(sender, instance, **kwargs):
    """Met à jour le badge quand un post est sauvegardé"""
    PostBadgeSystem.update_post_badge(instance)