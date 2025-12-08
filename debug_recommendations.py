import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tailora_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from wardrobe.models import ClothingItem
from recommendations.ai_engine import OutfitRecommendationEngine

User = get_user_model()

def debug_recommendations():
    print("=== DEBUG RECOMMENDATIONS ===")
    
    print(f"Total Users: {User.objects.count()}")
    
    for user in User.objects.all():
        item_count = ClothingItem.objects.filter(user=user).count()
        print(f"User: {user.email} (ID: {user.id}) - Items: {item_count}")
        
        if item_count > 0:
            print("  -> Found items for this user!")
            # Run engine for this user
            engine = OutfitRecommendationEngine(user)
            recs = engine.generate_daily_recommendations(count=3)
            print(f"  -> Generated {len(recs)} recommendations")


if __name__ == "__main__":
    debug_recommendations()
