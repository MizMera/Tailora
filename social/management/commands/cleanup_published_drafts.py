from django.core.management.base import BaseCommand
from social.models import PostDraft

class Command(BaseCommand):
    help = 'Clean up published drafts'
    
    def handle(self, *args, **options):
        # Option 1: Supprimer les drafts publiés
        deleted_count, _ = PostDraft.objects.filter(status='published').delete()
        
        # Option 2: Ou les archiver (changer de table)
        # archived_drafts = PostDraft.objects.filter(status='published')
        # for draft in archived_drafts:
        #     # Créer un enregistrement archivé
        #     ArchivedDraft.objects.create(
        #         original_id=draft.id,
        #         user=draft.user,
        #         # ... autres champs
        #     )
        # deleted_count = archived_drafts.count()
        # archived_drafts.delete()
        
        self.stdout.write(f"✅ Cleaned up {deleted_count} published drafts")