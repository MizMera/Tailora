# 🎨 Tailora - StyleAI: Votre Coach et Styliste de Garde-Robe Virtuelle

## 📋 Description du Projet

Tailora est une application mobile innovante qui permet aux utilisateurs de numériser leur garde-robe, de recevoir des suggestions de tenues intelligentes propulsées par l'IA, de planifier leurs looks et d'adopter une consommation de mode plus durable.

## 🏗️ Architecture du Projet

Le projet est structuré en 6 modules principaux :

### Module 1 : Gestion des Utilisateurs et Profil de Style (`users`)
**Responsable : Étudiant 1**

Gère l'identité des utilisateurs et leurs préférences de style.

**Fonctionnalités CRUD :**
- ✅ Création de compte sécurisé (email, mot de passe, nom)
- ✅ Affichage du profil utilisateur
- ✅ Modification du profil et du "Profil de Style" (couleurs, styles, marques, morphologie)
- ✅ Suppression du compte et données associées

**Fonctionnalités Avancées :**
- Authentification JWT robuste
- Questionnaire d'accueil (Onboarding)
- Système de notifications

**Models :**
- `User` : Modèle utilisateur étendu
- `StyleProfile` : Préférences de style
- `Notification` : Système de notifications

### Module 2 : Le Dressing Virtuel (`wardrobe`)
**Responsable : Étudiant 2**

Gestion complète de l'inventaire des vêtements.

**Fonctionnalités CRUD :**
- ✅ Ajout d'articles via formulaire (photo, catégorie, couleur, saison, matière, marque)
- ✅ Affichage en galerie avec tri et filtres
- ✅ Modification des détails
- ✅ Suppression d'articles

**Fonctionnalités Avancées :**
- Filtres de recherche avancés
- Catégories personnalisées
- Statuts (au lavage, pressing, prêté)
- Tracking d'utilisation

**Models :**
- `ClothingCategory` : Catégories de vêtements
- `ClothingItem` : Articles individuels

### Module 3 : Le Créateur de Tenues (`outfits`)
**Responsable : Étudiant 3**

Création et gestion d'ensembles vestimentaires complets.

**Fonctionnalités CRUD :**
- ✅ Création manuelle de tenues
- ✅ Galerie de tenues sauvegardées
- ✅ Modification des tenues existantes
- ✅ Suppression de tenues

**Fonctionnalités Avancées :**
- Interface Mix & Match (canvas visuel)
- Association par occasion
- Partage social

**Models :**
- `Outfit` : Tenues complètes
- `OutfitItem` : Relation vêtements-tenues (avec position)

### Module 4 : Le Planificateur et Calendrier de Style (`planner`)
**Responsable : Étudiant 4**

Planification des tenues avec intégration météo.

**Fonctionnalités CRUD :**
- ✅ Attribution de tenues à des dates
- ✅ Visualisation du calendrier
- ✅ Modification des planifications
- ✅ Suppression de tenues planifiées

**Fonctionnalités Avancées :**
- Intégration API Météo
- Assistant de valise pour voyages
- Historique des tenues portées

**Models :**
- `OutfitPlanning` : Planification quotidienne
- `TravelPlan` : Plans de voyage
- `WearHistory` : Historique de port

### Module 5 : Le Hub Social & Inspiration (`social`)
**Responsable : Étudiant 5**

Communauté et partage de style.

**Fonctionnalités CRUD :**
- ✅ Publication de tenues (Lookbook)
- ✅ Fil d'actualité personnalisé
- ✅ Modification de publications
- ✅ Suppression de publications et abonnements

**Fonctionnalités Avancées :**
- Défis de style hebdomadaires
- Recherche par article similaire
- Système d'interactions (likes, commentaires)

**Models :**
- `LookbookPost` : Publications
- `PostLike`, `PostComment`, `PostSave` : Interactions
- `StyleChallenge` : Défis communautaires
- `UserFollow` : Abonnements

### Module 6 : Moteur de Recommandation IA (`recommendations`)
**Cœur de l'Application**

Intelligence artificielle pour suggestions de tenues.

**Fonctionnalités :**
- 3-5 suggestions quotidiennes personnalisées
- Prise en compte du profil de style
- Intégration météo
- Apprentissage par renforcement
- Respect des règles de la mode

**Models :**
- `DailyRecommendation` : Recommandations quotidiennes
- `UserPreferenceSignal` : Signaux d'apprentissage
- `ColorCompatibility` : Théorie des couleurs
- `StyleRule` : Règles de mode

## 🚀 Installation

### Prérequis
- Python 3.10+
- pip
- virtualenv (recommandé)

### Étapes d'installation

1. **Cloner le projet**
```bash
cd d:\app\Tailora
```

2. **L'environnement virtuel est déjà créé (.venv)**
```bash
# Activer l'environnement (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Ou avec CMD
.venv\Scripts\activate.bat
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration de l'environnement**
```bash
# Copier le fichier d'exemple
copy .env.example .env

# Éditer .env avec vos paramètres
```

5. **Effectuer les migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

7. **Lancer le serveur de développement**
```bash
python manage.py runserver
```

L'application sera accessible sur `http://localhost:8000`

## 📁 Structure du Projet

```
Tailora/
├── .venv/                          # Environnement virtuel Python
├── manage.py                       # Commande Django
├── requirements.txt                # Dépendances
├── .env.example                    # Template configuration
├── tailora_project/                # Configuration Django
│   ├── settings.py                 # Paramètres principaux
│   ├── urls.py                     # Routes principales
│   └── wsgi.py                     # Configuration WSGI
├── users/                          # Module 1: Utilisateurs
│   ├── models.py                   # User, StyleProfile, Notification
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── wardrobe/                       # Module 2: Garde-robe
│   ├── models.py                   # ClothingCategory, ClothingItem
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── outfits/                        # Module 3: Tenues
│   ├── models.py                   # Outfit, OutfitItem
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── planner/                        # Module 4: Planificateur
│   ├── models.py                   # OutfitPlanning, TravelPlan, WearHistory
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── social/                         # Module 5: Hub Social
│   ├── models.py                   # LookbookPost, PostLike, StyleChallenge
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
└── recommendations/                # Module 6: IA
    ├── models.py                   # DailyRecommendation, UserPreferenceSignal
    ├── views.py
    ├── serializers.py
    ├── recommendation_engine.py    # Logique IA
    └── urls.py
```

## 🔧 Technologies Utilisées

- **Backend Framework:** Django 5.0
- **API:** Django REST Framework 3.14
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Image Processing:** Pillow
- **Database:** SQLite (dev) / PostgreSQL (production recommandé)
- **AI/ML:** scikit-learn, numpy
- **Weather API:** OpenWeatherMap
- **Async Tasks:** Celery + Redis (optionnel)

## 📊 Diagrammes UML

Le projet comprend plusieurs diagrammes UML fournis :
1. **Diagramme de Classes** : Relations entre les modèles
2. **Diagrammes de Cas d'Usage** : Flux utilisateurs pour chaque module
3. **Diagrammes de Séquence** : Interactions système

## 🔐 Sécurité

- Authentification JWT
- Validation des données entrantes
- Protection CSRF
- Gestion sécurisée des mots de passe
- Variables d'environnement pour données sensibles

## 🌐 API Endpoints (À développer)

### Authentification
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/login/` - Connexion
- `POST /api/auth/refresh/` - Renouveler le token
- `POST /api/auth/logout/` - Déconnexion

### Utilisateurs
- `GET /api/users/profile/` - Profil utilisateur
- `PUT /api/users/profile/` - Modifier profil
- `GET /api/users/style-profile/` - Profil de style
- `PUT /api/users/style-profile/` - Modifier style

### Garde-robe
- `GET /api/wardrobe/items/` - Liste des vêtements
- `POST /api/wardrobe/items/` - Ajouter un vêtement
- `GET /api/wardrobe/items/{id}/` - Détails d'un vêtement
- `PUT /api/wardrobe/items/{id}/` - Modifier un vêtement
- `DELETE /api/wardrobe/items/{id}/` - Supprimer un vêtement

### Tenues
- `GET /api/outfits/` - Liste des tenues
- `POST /api/outfits/` - Créer une tenue
- `GET /api/outfits/{id}/` - Détails d'une tenue
- `PUT /api/outfits/{id}/` - Modifier une tenue
- `DELETE /api/outfits/{id}/` - Supprimer une tenue

### Planificateur
- `GET /api/planner/calendar/` - Calendrier des tenues
- `POST /api/planner/schedule/` - Planifier une tenue
- `GET /api/planner/travel/` - Plans de voyage
- `GET /api/planner/history/` - Historique

### Social
- `GET /api/social/feed/` - Fil d'actualité
- `POST /api/social/posts/` - Publier une tenue
- `POST /api/social/posts/{id}/like/` - Liker
- `POST /api/social/posts/{id}/comment/` - Commenter
- `GET /api/social/challenges/` - Défis actifs

### Recommandations
- `GET /api/recommendations/daily/` - Recommandations du jour
- `POST /api/recommendations/{id}/feedback/` - Feedback sur une recommandation
- `GET /api/recommendations/weather/` - Suggestions selon météo

## 📝 Prochaines Étapes

1. **Créer les Serializers** pour chaque module
2. **Développer les Views et ViewSets** REST
3. **Configurer les URLs** pour l'API
4. **Implémenter le moteur de recommandation IA**
5. **Intégrer l'API Météo**
6. **Créer les tests unitaires**
7. **Développer l'interface admin Django**
8. **Documentation API avec Swagger**

## 👥 Répartition des Responsabilités

- **Étudiant 1** : Module Users + Auth
- **Étudiant 2** : Module Wardrobe
- **Étudiant 3** : Module Outfits
- **Étudiant 4** : Module Planner + API Météo
- **Étudiant 5** : Module Social
- **Tous** : Moteur de Recommandation IA (collaboration)

## 📖 Documentation Complémentaire

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [OpenWeatherMap API](https://openweathermap.org/api)

## 📄 Licence

Ce projet est développé dans un cadre éducatif.

---

**Tailora** - Votre garde-robe intelligente 🎨👗👔
