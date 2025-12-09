# social/management/commands/publish_scheduled_posts.py
import os
import sys
import django
from datetime import datetime
from django.utils import timezone

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tailora_project.settings')
django.setup()

from social.models import PostDraft, LookbookPost
from django.contrib.auth import get_user_model

def publish_scheduled_posts():
    """Publier les posts programmés dont l'heure est passée"""
    now = timezone.now()
    print(f"Checking scheduled posts at {now}")
    
    # Récupérer les drafts programmés dont l'heure est passée
    scheduled_drafts = PostDraft.objects.filter(
        status='scheduled',
        scheduled_for__lte=now
    ).select_related('user', 'outfit')
    
    published_count = 0
    for draft in scheduled_drafts:
        try:
            print(f"Publishing draft: {draft.id} - {draft.outfit.name}")
            
            # Créer le post
            post = LookbookPost.objects.create(
                user=draft.user,
                outfit=draft.outfit,
                caption=draft.caption,
                hashtags=draft.hashtags,
                enhanced_images=draft.enhanced_images,
                visibility=draft.visibility
            )
            
            # Mettre à jour le statut du draft
            draft.status = 'published'
            draft.save()
            
            published_count += 1
            print(f"✓ Published: {post.id}")
            
        except Exception as e:
            print(f"✗ Error publishing draft {draft.id}: {e}")
    
    return published_count

if __name__ == "__main__":
    count = publish_scheduled_posts()
    print(f"Published {count} posts")