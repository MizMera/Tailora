# 🚀 Guide de Démarrage Rapide - Tailora

## ✅ Installation Rapide

### 1. Activer l'environnement virtuel

**PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**CMD:**
```cmd
.venv\Scripts\activate.bat
```

### 2. Installer les dépendances (déjà fait)
```bash
pip install -r requirements.txt
```

### 3. Les migrations sont déjà effectuées ✓

La base de données SQLite a été créée avec toutes les tables.

### 4. Peupler les données initiales

**Catégories de vêtements:**
```bash
python manage.py populate_categories
```

**Règles de style et couleurs:**
```bash
python manage.py populate_style_data
```

### 5. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

Suivez les instructions et fournissez:
- Email
- Nom d'utilisateur
- Mot de passe

### 6. Lancer le serveur

```bash
python manage.py runserver
```

Accédez à:
- **Application:** http://localhost:8000
- **Admin:** http://localhost:8000/admin

## 📋 Prochaines Étapes par Module

### Pour tous les étudiants:

1. **Créer les Serializers** dans votre module
   - Exemple: `users/serializers.py`
   - Utiliser `ModelSerializer` de DRF

2. **Créer les ViewSets** 
   - Exemple: `users/views.py`
   - Utiliser `ModelViewSet` pour CRUD complet

3. **Configurer les URLs**
   - Exemple: `users/urls.py`
   - Router DRF pour les ViewSets

4. **Tests**
   - Créer `tests.py` pour chaque module
   - Tests CRUD complets

### Module 1 (Étudiant 1) - Users

**Fichiers à créer:**
- `users/serializers.py` - UserSerializer, StyleProfileSerializer, NotificationSerializer
- `users/views.py` - UserViewSet, StyleProfileViewSet, NotificationViewSet
- `users/urls.py` - Routes API
- `users/permissions.py` - Permissions personnalisées

**Endpoints à implémenter:**
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/login/` - Connexion JWT
- `GET/PUT /api/users/profile/` - Profil
- `GET/PUT /api/users/style-profile/` - Profil de style
- `GET /api/users/notifications/` - Liste notifications
- `POST /api/users/onboarding/` - Questionnaire d'accueil

### Module 2 (Étudiant 2) - Wardrobe

**Fichiers à créer:**
- `wardrobe/serializers.py`
- `wardrobe/views.py`
- `wardrobe/urls.py`
- `wardrobe/filters.py` - Filtres de recherche avancés

**Endpoints à implémenter:**
- `GET /api/wardrobe/items/` - Liste (avec filtres)
- `POST /api/wardrobe/items/` - Ajouter vêtement
- `GET /api/wardrobe/items/{id}/` - Détails
- `PUT /api/wardrobe/items/{id}/` - Modifier
- `DELETE /api/wardrobe/items/{id}/` - Supprimer
- `GET /api/wardrobe/categories/` - Catégories
- `POST /api/wardrobe/categories/` - Catégorie custom

### Module 3 (Étudiant 3) - Outfits

**Fichiers à créer:**
- `outfits/serializers.py`
- `outfits/views.py`
- `outfits/urls.py`
- `outfits/utils.py` - Logique Mix & Match

**Endpoints à implémenter:**
- `GET /api/outfits/` - Liste tenues
- `POST /api/outfits/` - Créer tenue
- `GET /api/outfits/{id}/` - Détails
- `PUT /api/outfits/{id}/` - Modifier
- `DELETE /api/outfits/{id}/` - Supprimer
- `POST /api/outfits/{id}/share/` - Partager

### Module 4 (Étudiant 4) - Planner

**Fichiers à créer:**
- `planner/serializers.py`
- `planner/views.py`
- `planner/urls.py`
- `planner/weather_service.py` - Intégration API météo

**Endpoints à implémenter:**
- `GET /api/planner/calendar/` - Calendrier
- `POST /api/planner/schedule/` - Planifier tenue
- `GET /api/planner/schedule/{date}/` - Tenue du jour
- `PUT /api/planner/schedule/{id}/` - Modifier planning
- `DELETE /api/planner/schedule/{id}/` - Supprimer
- `GET /api/planner/weather/{date}/` - Météo
- `POST /api/planner/travel/` - Créer plan voyage
- `GET /api/planner/history/` - Historique

**Configuration Météo:**
1. Obtenir une clé API sur https://openweathermap.org/api
2. Ajouter dans `.env`: `WEATHER_API_KEY=votre_cle`

### Module 5 (Étudiant 5) - Social

**Fichiers à créer:**
- `social/serializers.py`
- `social/views.py`
- `social/urls.py`
- `social/permissions.py` - Permissions de visibilité

**Endpoints à implémenter:**
- `GET /api/social/feed/` - Fil d'actualité
- `POST /api/social/posts/` - Publier
- `GET /api/social/posts/{id}/` - Détails post
- `POST /api/social/posts/{id}/like/` - Liker
- `DELETE /api/social/posts/{id}/like/` - Unliker
- `POST /api/social/posts/{id}/comment/` - Commenter
- `POST /api/social/users/{id}/follow/` - Suivre
- `DELETE /api/social/users/{id}/follow/` - Ne plus suivre
- `GET /api/social/challenges/` - Défis actifs
- `POST /api/social/challenges/{id}/submit/` - Soumettre au défi

### Module 6 (Tous) - Recommendations

**Fichiers à créer:**
- `recommendations/serializers.py`
- `recommendations/views.py`
- `recommendations/urls.py`
- `recommendations/engine.py` - **Logique IA principale**
- `recommendations/ml_utils.py` - Fonctions ML

**Endpoints à implémenter:**
- `GET /api/recommendations/daily/` - Recommandations du jour
- `POST /api/recommendations/{id}/accept/` - Accepter
- `POST /api/recommendations/{id}/reject/` - Rejeter
- `POST /api/recommendations/{id}/rate/` - Noter

**Logique du moteur de recommandation:**
1. Analyser le profil de style utilisateur
2. Vérifier disponibilité des vêtements
3. Récupérer la météo du jour
4. Appliquer les règles de style
5. Calculer les scores de compatibilité
6. Générer 3-5 suggestions
7. Apprendre des feedbacks utilisateurs

## 🔧 Commandes Utiles

### Gestion Base de Données
```bash
# Créer nouvelles migrations
python manage.py makemigrations

# Appliquer migrations
python manage.py migrate

# Shell Django
python manage.py shell

# Réinitialiser la base de données
python manage.py flush
```

### Gestion Serveur
```bash
# Lancer serveur
python manage.py runserver

# Lancer sur un port différent
python manage.py runserver 8080

# Rendre accessible sur le réseau
python manage.py runserver 0.0.0.0:8000
```

### Utilitaires
```bash
# Collecter fichiers statiques
python manage.py collectstatic

# Créer superutilisateur
python manage.py createsuperuser

# Lister toutes les commandes
python manage.py help
```

## 📚 Ressources

- **Django Docs:** https://docs.djangoproject.com/
- **DRF Docs:** https://www.django-rest-framework.org/
- **JWT Auth:** https://django-rest-framework-simplejwt.readthedocs.io/
- **Pillow:** https://pillow.readthedocs.io/

## 🐛 Debugging

### Problème: Module not found
**Solution:** Vérifier que l'environnement virtuel est activé

### Problème: Migration errors
**Solution:** 
```bash
python manage.py makemigrations
python manage.py migrate
```

### Problème: Admin CSS not loading
**Solution:**
```bash
python manage.py collectstatic
```

## 💡 Conseils

1. **Git:** Créer une branche par module
2. **Tests:** Écrire les tests en même temps que le code
3. **Documentation:** Commenter les fonctions complexes
4. **API:** Utiliser Postman ou Insomnia pour tester
5. **Code Review:** Faire des revues de code entre étudiants

## 🎯 Objectifs de Sprint

### Sprint 1 (Semaine 1-2)
- [ ] Tous: Serializers et ViewSets de base
- [ ] Tous: Endpoints CRUD fonctionnels
- [ ] Étudiant 1: Authentification JWT complète

### Sprint 2 (Semaine 3-4)
- [ ] Étudiant 2: Filtres avancés wardrobe
- [ ] Étudiant 3: Interface Mix & Match
- [ ] Étudiant 4: Intégration API météo
- [ ] Étudiant 5: Fil d'actualité et interactions

### Sprint 3 (Semaine 5-6)
- [ ] Tous: Moteur de recommandation IA
- [ ] Tous: Tests unitaires complets
- [ ] Tous: Documentation API

### Sprint 4 (Semaine 7-8)
- [ ] Tous: Optimisations et bugfixes
- [ ] Tous: Déploiement
- [ ] Tous: Présentation finale

Bon courage! 🚀
