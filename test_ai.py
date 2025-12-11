# test_ai.py - Script de test pour AI Engagement Optimizer
import os
import sys
import django
import random
from datetime import datetime, timedelta

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'votre_projet.settings')  # Remplacez 'votre_projet'
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from social.services import AIEngagementOptimizer  # Importez votre classe
from social.models import LookbookPost, Outfit  # Adaptez selon vos modèles

def setup_test_user():
    """Crée ou récupère un utilisateur de test"""
    try:
        user = User.objects.get(username='test_ai_user')
        print(f"✅ Utilisateur de test trouvé : {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='test_ai_user',
            email='test@example.com',
            password='testpass123'
        )
        print(f"✅ Utilisateur de test créé : {user.username}")
    
    return user

def create_test_outfit(user):
    """Crée un outfit de test"""
    outfit, created = Outfit.objects.get_or_create(
        user=user,
        name="Outfit de Test AI",
        defaults={'description': 'Pour tester les optimisations AI'}
    )
    if created:
        print(f"✅ Outfit de test créé : {outfit.name}")
    else:
        print(f"✅ Outfit de test existant : {outfit.name}")
    
    return outfit

def create_test_posts_with_varied_engagement(user, outfit, num_posts=20):
    """
    Crée des posts de test avec des heures et engagements variés
    pour simuler des données réalistes
    """
    print(f"\n📊 Création de {num_posts} posts de test avec engagement varié...")
    
    # Heures optimales (plus d'engagement)
    optimal_hours = [9, 12, 18, 21]
    
    # Nettoyer les anciens posts de test
    LookbookPost.objects.filter(user=user, caption__contains="[TEST]").delete()
    
    for i in range(num_posts):
        # Choisir une heure : 70% heure optimale, 30% heure aléatoire
        if random.random() < 0.7:
            hour = random.choice(optimal_hours)
            is_optimal = True
        else:
            hour = random.randint(0, 23)
            is_optimal = False
        
        # Date aléatoire dans les 60 derniers jours
        days_ago = random.randint(1, 60)
        post_time = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        post_time = post_time.replace(hour=hour, minute=random.randint(0, 59))
        
        # Générer un engagement basé sur l'heure (plus pour les heures optimales)
        if is_optimal:
            likes = random.randint(15, 50)
            comments = random.randint(3, 15)
        else:
            likes = random.randint(1, 20)
            comments = random.randint(0, 5)
        
        # Créer le post
        post = LookbookPost.objects.create(
            user=user,
            outfit=outfit,
            caption=f"[TEST] Post #{i+1} créé à {hour}h - Engagement test",
            hashtags=['#test', '#ai', '#engagement'],
            created_at=post_time,
            likes_count=likes,
            comments_count=comments,
            is_published=True
        )
        
        print(f"   Post {i+1:2d}: {post_time.strftime('%Y-%m-%d %H:%M')} - {likes}👍 {comments}💬 {'🌟' if is_optimal else ''}")
    
    print(f"✅ {num_posts} posts de test créés avec succès")

def test_ai_analyze_best_time(user):
    """Teste la fonction d'analyse du meilleur moment"""
    print("\n" + "="*60)
    print("🧪 TEST 1: analyze_best_time()")
    print("="*60)
    
    ai_optimizer = AIEngagementOptimizer(user)
    
    print("\n📈 Analyse des habitudes d'engagement...")
    try:
        best_time = ai_optimizer.analyze_best_time()
        print(f"✅ Heure optimale suggérée : {best_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Heure du jour : {best_time.hour}:00")
        
        # Analyse des posts pour comprendre
        posts = LookbookPost.objects.filter(user=user)
        if posts.exists():
            print(f"\n📊 Analyse basée sur {posts.count()} posts :")
            
            # Calculer l'engagement par heure
            hour_engagement = {}
            for post in posts:
                hour = post.created_at.hour
                engagement = post.likes_count + (post.comments_count * 2)
                if hour not in hour_engagement:
                    hour_engagement[hour] = []
                hour_engagement[hour].append(engagement)
            
            # Afficher les top heures
            print("   Engagement moyen par heure :")
            for hour in sorted(hour_engagement.keys()):
                avg = sum(hour_engagement[hour]) / len(hour_engagement[hour])
                count = len(hour_engagement[hour])
                print(f"     {hour:2d}h : {avg:5.1f} points (sur {count} posts)")
        
        return best_time.hour
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return None

def test_ai_hashtag_suggestions(user):
    """Teste la génération de suggestions de hashtags"""
    print("\n" + "="*60)
    print("🧪 TEST 2: generate_hashtag_suggestions()")
    print("="*60)
    
    ai_optimizer = AIEngagementOptimizer(user)
    
    # Test avec différentes captions et catégories
    test_cases = [
        {"caption": "Beautiful casual outfit for summer day", "category": "casual"},
        {"caption": "Elegant dress for formal event tonight", "category": "formal"},
        {"caption": "Perfect work attire for office presentation", "category": "work"},
        {"caption": "", "category": None},  # Cas vide
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔹 Test {i}:")
        print(f"   Caption: '{test_case['caption']}'")
        print(f"   Catégorie: {test_case['category']}")
        
        hashtags = ai_optimizer.generate_hashtag_suggestions(
            caption=test_case['caption'],
            category=test_case['category']
        )
        
        print(f"   Hashtags suggérés ({len(hashtags)}) :")
        for tag in hashtags:
            print(f"     {tag}")
    
    return True

def test_ai_caption_suggestions(user, outfit):
    """Teste la génération de suggestions de captions"""
    print("\n" + "="*60)
    print("🧪 TEST 3: generate_caption_suggestions()")
    print("="*60)
    
    ai_optimizer = AIEngagementOptimizer(user)
    
    # Test avec différentes combinaisons
    test_cases = [
        {"outfit_name": outfit.name, "style": "casual", "mood": "happy"},
        {"outfit_name": "Evening Dress", "style": "elegant", "mood": "confident"},
        {"outfit_name": "Office Suit", "style": "professional", "mood": ""},
        {"outfit_name": "", "style": "", "mood": ""},  # Cas vide
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔹 Test {i}:")
        print(f"   Outfit: {test_case['outfit_name']}")
        print(f"   Style: {test_case['style']}")
        print(f"   Mood: {test_case['mood']}")
        
        captions = ai_optimizer.generate_caption_suggestions(
            outfit_name=test_case['outfit_name'],
            style=test_case['style'],
            mood=test_case['mood']
        )
        
        print(f"   Captions suggérés ({len(captions)}) :")
        for j, caption in enumerate(captions, 1):
            print(f"     {j}. {caption}")
    
    return True

def test_ai_confidence_score(user, best_hour):
    """Teste le calcul du score de confiance"""
    print("\n" + "="*60)
    print("🧪 TEST 4: calculate_confidence_score()")
    print("="*60)
    
    ai_optimizer = AIEngagementOptimizer(user)
    
    # Créer un datetime pour l'heure optimale
    suggested_time = timezone.now().replace(hour=best_hour, minute=0, second=0, microsecond=0)
    
    # Différents scénarios de test
    test_scenarios = [
        {
            "name": "⭐ Scénario OPTIMAL",
            "data": {
                'caption': 'Loving this casual look for today! What do you think? ✨ #fashion',
                'hashtags': ['#fashion', '#style', '#ootd', '#casual', '#summer'],
                'outfit': 'Test Outfit',
                'suggested_time': suggested_time,
                'use_ai': True
            }
        },
        {
            "name": "🆗 Scénario MOYEN",
            "data": {
                'caption': 'Nice outfit',
                'hashtags': ['#fashion', '#style'],
                'outfit': 'Test Outfit',
                'suggested_time': suggested_time.replace(hour=14),  # Heure non optimale
                'use_ai': True
            }
        },
        {
            "name": "⚠️ Scénario FAIBLE",
            "data": {
                'caption': '',
                'hashtags': [],
                'outfit': None,
                'suggested_time': None,
                'use_ai': False
            }
        }
    ]
    
    print("\n📊 Test des scores de confiance :")
    print("   (Basé sur heure optimale = {}h)".format(best_hour))
    
    for scenario in test_scenarios:
        print(f"\n🔹 {scenario['name']}:")
        
        for key, value in scenario['data'].items():
            if value is not None:
                print(f"   {key}: {value}")
        
        try:
            score = ai_optimizer.calculate_confidence_score(scenario['data'])
            percentage = int(score * 100)
            
            # Afficher le score avec barre visuelle
            bar_length = 20
            filled = int(percentage / 100 * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            print(f"   Score de confiance: {percentage}% {bar}")
            
            # Analyse détaillée
            if score >= 0.8:
                print("   📈 Excellent! Haute probabilité d'engagement")
            elif score >= 0.6:
                print("   👍 Bon, bon potentiel d'engagement")
            elif score >= 0.4:
                print("   🤔 Moyen, pourrait être amélioré")
            else:
                print("   ⚠️ Faible, optimisation recommandée")
            
            # Test get_optimization_summary
            summary = ai_optimizer.get_optimization_summary(scenario['data'])
            print(f"   Résumé: {summary['message']}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    return True

def run_comprehensive_test():
    """Exécute tous les tests"""
    print("🚀 DÉMARRAGE DES TESTS DE L'AI ENGAGEMENT OPTIMIZER")
    print("="*60)
    
    try:
        # 1. Initialisation
        user = setup_test_user()
        outfit = create_test_outfit(user)
        
        # 2. Créer des données de test
        create_test_posts_with_varied_engagement(user, outfit, num_posts=15)
        
        # 3. Exécuter les tests
        best_hour = test_ai_analyze_best_time(user)
        
        if best_hour:
            test_ai_hashtag_suggestions(user)
            test_ai_caption_suggestions(user, outfit)
            test_ai_confidence_score(user, best_hour)
        
        # 4. Test d'intégration
        print("\n" + "="*60)
        print("🧪 TEST FINAL: Simulation complète")
        print("="*60)
        
        ai_optimizer = AIEngagementOptimizer(user)
        
        # Simuler la création d'un post
        print("\n🎭 Simulation d'un post optimisé:")
        
        post_data = {
            'caption': 'Feeling amazing in this new outfit! What should I wear next? 👗✨',
            'hashtags': ['#fashion', '#ootd', '#style', '#look', '#outfitoftheday'],
            'outfit': 'Summer Dress',
            'suggested_time': timezone.now().replace(hour=best_hour, minute=0),
            'use_ai': True
        }
        
        # Générer toutes les suggestions
        hashtags = ai_optimizer.generate_hashtag_suggestions(post_data['caption'], 'casual')
        captions = ai_optimizer.generate_caption_suggestions(post_data['outfit'], 'elegant', 'happy')
        confidence = ai_optimizer.calculate_confidence_score(post_data)
        summary = ai_optimizer.get_optimization_summary(post_data)
        
        print(f"📝 Caption suggéré: {captions[0] if captions else 'Aucun'}")
        print(f"🏷️ Hashtags suggérés: {', '.join(hashtags[:5])}...")
        print(f"🎯 Score de confiance: {int(confidence * 100)}%")
        print(f"📊 Résumé: {summary['message']}")
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS TERMINÉS AVEC SUCCÈS !")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        return False

def clean_test_data():
    """Nettoie les données de test (optionnel)"""
    print("\n🧹 Nettoyage des données de test...")
    
    try:
        # Supprimer l'utilisateur de test et toutes ses données
        test_users = User.objects.filter(username='test_ai_user')
        count = test_users.count()
        
        if count > 0:
            test_users.delete()
            print(f"✅ {count} utilisateur(s) de test supprimé(s)")
        else:
            print("✅ Aucune donnée de test à nettoyer")
            
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 TEST AI ENGAGEMENT OPTIMIZER")
    print("="*60)
    
    # Menu simple
    print("\nOptions:")
    print("  1. Exécuter tous les tests")
    print("  2. Nettoyer les données de test")
    print("  3. Quitter")
    
    choice = input("\nVotre choix (1-3): ").strip()
    
    if choice == "1":
        success = run_comprehensive_test()
        
        if success:
            print("\n🎉 L'AI fonctionne correctement!")
            print("   - Les posts de test ont été créés")
            print("   - L'analyse des heures fonctionne")
            print("   - Le calcul du score est opérationnel")
            print("\n📋 Prochaines étapes:")
            print("   1. Testez manuellement la page create_post.html")
            print("   2. Vérifiez que le score change avec les heures")
            print("   3. Ajustez les poids dans calculate_confidence_score() si nécessaire")
        else:
            print("\n⚠️  Des erreurs sont survenues. Vérifiez la configuration.")
            
    elif choice == "2":
        clean_test_data()
        
    elif choice == "3":
        print("Au revoir!")
        
    else:
        print("❌ Choix invalide")