# test_profile_badges.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tailora_project.settings')
django.setup()

from social.models import LookbookPost
from users.models import User

def test_profile_badges():
    print("🎪 TEST BADGES SUR LES POSTS DU PROFIL...")
    
    try:
        user = User.objects.get(id="da3b4de0-b7e5-4515-a71f-b3cc098097d6")
        posts = LookbookPost.objects.filter(user=user)
        
        if not posts.exists():
            print("❌ Aucun post trouvé pour cet utilisateur")
            return
        
        print(f"👤 Utilisateur: {user.get_full_name()}")
        print(f"📊 Posts trouvés: {posts.count()}")
        
        # Configuration des badges avec différents niveaux
        test_configs = [
            (posts[0], 10, "🔹 Niveau bas (pas de badge)"),
            (posts[1], 25, "❤️ Apprécié (25+ likes)"),   
            (posts[2], 60, "🔥 Viral (50+ likes)"),  
            (posts[3], 120, "🌟 Star (100+ likes)"),
        ]
        
        # Si vous avez plus de posts, ajoutez le badge Iconique
        if posts.count() >= 5:
            test_configs.append((posts[4], 250, "💎 Iconique (200+ likes)"))
        
        print("\n📝 CONFIGURATION DES POSTS:")
        for i, (post, likes, description) in enumerate(test_configs, 1):
            post.likes_count = likes
            post.save()
            
            # Détermination du badge
            if likes >= 200:
                badge = "💎 Iconique"
                badge_style = "gold"
            elif likes >= 100:
                badge = "🌟 Star" 
                badge_style = "silver"
            elif likes >= 50:
                badge = "🔥 Viral"
                badge_style = "orange"
            elif likes >= 25:
                badge = "❤️ Apprécié"
                badge_style = "pink"
            else:
                badge = "Aucun badge"
                badge_style = "gray"
            
            print(f"   {i}. '{post.outfit.name}'")
            print(f"      Likes: {likes} → {badge}")
            print(f"      Description: {description}")
            print(f"      Style: {badge_style}")
        
        # Résumé des badges configurés
        print(f"\n🎯 RÉSUMÉ DES BADGES:")
        badge_counts = {
            "💎 Iconique": 0,
            "🌟 Star": 0, 
            "🔥 Viral": 0,
            "❤️ Apprécié": 0,
            "Aucun badge": 0
        }
        
        for post in posts:
            if post.likes_count >= 200:
                badge_counts["💎 Iconique"] += 1
            elif post.likes_count >= 100:
                badge_counts["🌟 Star"] += 1
            elif post.likes_count >= 50:
                badge_counts["🔥 Viral"] += 1
            elif post.likes_count >= 25:
                badge_counts["❤️ Apprécié"] += 1
            else:
                badge_counts["Aucun badge"] += 1
        
        for badge, count in badge_counts.items():
            if count > 0:
                print(f"   {badge}: {count} post(s)")
        
        print(f"\n✅ Configuration terminée!")
        print("🌐 Allez voir votre profil: http://127.0.0.1:8000/social/profile/da3b4de0-b7e5-4515-a71f-b3cc098097d6/")
        
    except User.DoesNotExist:
        print("❌ Utilisateur non trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_profile_badges()