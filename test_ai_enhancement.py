"""
Test the enhanced AI recommendation system
Run: python test_ai_enhancement.py
"""
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tailora_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from recommendations.ai_engine import OutfitRecommendationEngine

User = get_user_model()

def test_enhanced_ai():
    print("="*60)
    print("TESTING ENHANCED AI RECOMMENDATION SYSTEM")
    print("="*60)
    
    # Find user with items
    for user in User.objects.all():
        from wardrobe.models import ClothingItem
        item_count = ClothingItem.objects.filter(user=user).count()
        
        if item_count > 0:
            print(f"\nTesting with user: {user.email} ({item_count} items)")
            engine = OutfitRecommendationEngine(user)
            
            # Test 1: Weather Recommendations
            print("\n--- TEST 1: Weather-Aware Recommendations ---")
            try:
                recs = engine.generate_weather_recommendations(location="Tunis,TN", count=2)
                print(f"✅ Generated {len(recs)} weather-aware recommendations")
                for rec in recs:
                    print(f"   - {rec.outfit.name}: {rec.reason}")
                    print(f"     Weather: {rec.weather_factor}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            # Test 2: Shopping Suggestions
            print("\n--- TEST 2: Shopping Suggestions ---")
            try:
                suggestions = engine.suggest_shopping_items(max_suggestions=3)
                print(f"✅ Generated {len(suggestions)} shopping suggestions")
                for sug in suggestions:
                    print(f"   - {sug.suggested_name} ({sug.category})")
                    print(f"     Priority: {sug.priority}, Reason: {sug.reason}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            # Done
            break
    else:
        print("❌ No users with wardrobe items found")
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_enhanced_ai()
