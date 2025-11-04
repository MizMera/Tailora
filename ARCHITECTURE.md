# 🏗️ Architecture Tailora - Vue d'Ensemble

## 📐 Architecture Globale

```
┌─────────────────────────────────────────────────────────────┐
│                    MOBILE APPLICATION                        │
│                   (iOS / Android / Web)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ REST API (JSON)
                       │ JWT Authentication
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   DJANGO REST FRAMEWORK                      │
│                  (API Layer - Port 8000)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────┐              ┌──────────────┐
│  DJANGO ORM  │              │   EXTERNAL   │
│  (Business   │              │     APIs     │
│    Logic)    │              │              │
└──────┬───────┘              └──────┬───────┘
       │                             │
       │                             │
       ▼                             ▼
┌──────────────┐              ┌──────────────┐
│   DATABASE   │              │ OpenWeather  │
│   (SQLite)   │              │     API      │
└──────────────┘              └──────────────┘
```

## 🎯 Modules et Responsabilités

### 📊 Diagramme des Modules

```
                    ┌────────────────────┐
                    │   Module 1: Users  │
                    │   Authentication   │
                    │   Style Profile    │
                    └─────────┬──────────┘
                              │ owns
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Module 2:    │────▶│  Module 3:    │────▶│  Module 4:    │
│  Wardrobe     │     │  Outfits      │     │  Planner      │
│  (Clothing)   │     │  (Mix Match)  │     │  (Calendar)   │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        │                     └──────┬──────────────┘
        │                            │ publishes
        │                            ▼
        │                    ┌───────────────┐
        │                    │  Module 5:    │
        │                    │  Social       │
        │                    │  (Community)  │
        │                    └───────┬───────┘
        │                            │
        └────────────────────────────┼─────────┐
                                     │         │
                                     │ learns  │
                                     ▼         │
                            ┌────────────────┐ │
                            │   Module 6:    │ │
                            │ Recommendations│◀┘
                            │   (AI Engine)  │
                            └────────────────┘
```

## 📁 Structure des Fichiers

```
Tailora/
│
├── 📄 manage.py                    # Django management script
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Environment template
├── 📄 .gitignore                   # Git ignore rules
│
├── 📁 .venv/                       # Virtual environment
├── 📁 media/                       # User uploads (images)
├── 📁 staticfiles/                 # Static files (CSS, JS)
├── 📄 db.sqlite3                   # Database
│
├── 📚 Documentation/
│   ├── README.md                   # Project overview
│   ├── SETUP_GUIDE.md              # Setup instructions
│   ├── API_EXAMPLES.md             # API usage examples
│   ├── PROJECT_SUMMARY.md          # Project summary
│   └── COMMANDS.ps1                # Quick commands
│
├── 📁 tailora_project/             # Main project config
│   ├── settings.py                 # Django settings
│   ├── urls.py                     # Main URL router
│   ├── wsgi.py                     # WSGI config
│   └── asgi.py                     # ASGI config
│
├── 📁 users/                       # Module 1 ✅ COMPLETE
│   ├── models.py                   # User, StyleProfile, Notification
│   ├── serializers.py              # ✅ DRF Serializers
│   ├── views.py                    # ✅ API ViewSets
│   ├── urls.py                     # ✅ URL routes
│   ├── admin.py                    # ✅ Admin interface
│   └── tests.py                    # Unit tests
│
├── 📁 wardrobe/                    # Module 2 📝 TO DO
│   ├── models.py                   # ✅ ClothingCategory, ClothingItem
│   ├── serializers.py              # 📝 To create
│   ├── views.py                    # 📝 To create
│   ├── urls.py                     # 📝 To create
│   ├── admin.py                    # ✅ Configured
│   ├── filters.py                  # 📝 To create (advanced search)
│   └── management/
│       └── commands/
│           └── populate_categories.py  # ✅ Data loader
│
├── 📁 outfits/                     # Module 3 📝 TO DO
│   ├── models.py                   # ✅ Outfit, OutfitItem
│   ├── serializers.py              # 📝 To create
│   ├── views.py                    # 📝 To create
│   ├── urls.py                     # 📝 To create
│   ├── admin.py                    # ✅ Configured
│   └── utils.py                    # 📝 Mix & Match logic
│
├── 📁 planner/                     # Module 4 📝 TO DO
│   ├── models.py                   # ✅ OutfitPlanning, TravelPlan, WearHistory
│   ├── serializers.py              # 📝 To create
│   ├── views.py                    # 📝 To create
│   ├── urls.py                     # 📝 To create
│   ├── admin.py                    # ✅ Configured
│   └── weather_service.py          # 📝 Weather API integration
│
├── 📁 social/                      # Module 5 📝 TO DO
│   ├── models.py                   # ✅ LookbookPost, StyleChallenge, etc.
│   ├── serializers.py              # 📝 To create
│   ├── views.py                    # 📝 To create
│   ├── urls.py                     # 📝 To create
│   ├── admin.py                    # ✅ Configured
│   └── permissions.py              # 📝 Custom permissions
│
└── 📁 recommendations/             # Module 6 📝 TO DO (ALL)
    ├── models.py                   # ✅ DailyRecommendation, UserPreferenceSignal
    ├── serializers.py              # 📝 To create
    ├── views.py                    # 📝 To create
    ├── urls.py                     # 📝 To create
    ├── admin.py                    # ✅ Configured
    ├── engine.py                   # 📝 AI recommendation logic
    ├── ml_utils.py                 # 📝 ML utilities
    └── management/
        └── commands/
            └── populate_style_data.py  # ✅ Style rules loader
```

## 🔄 Flux de Données Principaux

### 1. Inscription & Authentification
```
User Registration
    ↓
POST /api/users/
    ↓
User Created + StyleProfile Created
    ↓
JWT Token Generated
    ↓
User Authenticated
```

### 2. Ajout d'un Vêtement
```
User Uploads Photo
    ↓
POST /api/wardrobe/items/
    ↓
Image Stored in Media
    ↓
ClothingItem Created
    ↓
Categories & Filters Applied
```

### 3. Création de Tenue
```
User Selects Items from Wardrobe
    ↓
POST /api/outfits/
    ↓
Outfit + OutfitItems Created
    ↓
Available for Planning
```

### 4. Planification avec Météo
```
User Selects Date & Outfit
    ↓
POST /api/planner/schedule/
    ↓
Weather API Call
    ↓
OutfitPlanning Created
    ↓
Weather Alert if Mismatch
```

### 5. Recommandation IA
```
Daily Cron Job / User Request
    ↓
GET /api/recommendations/daily/
    ↓
AI Engine Processes:
  - User Style Profile
  - Available Items
  - Weather Data
  - Past Preferences
  - Style Rules
    ↓
3-5 Outfit Suggestions Generated
    ↓
User Feedback Collected
    ↓
ML Model Updated
```

### 6. Interaction Sociale
```
User Creates Outfit
    ↓
POST /api/social/posts/
    ↓
LookbookPost Created
    ↓
Appears in Followers' Feed
    ↓
Likes & Comments
    ↓
Engagement Metrics Updated
```

## 🔐 Sécurité & Permissions

```
┌─────────────────────────────────────────┐
│         PERMISSION LAYERS               │
├─────────────────────────────────────────┤
│  Public:                                │
│    - User Registration                  │
│    - Login                              │
│    - Password Reset                     │
├─────────────────────────────────────────┤
│  Authenticated Users:                   │
│    - Own Profile (CRUD)                 │
│    - Own Wardrobe (CRUD)                │
│    - Own Outfits (CRUD)                 │
│    - Own Planning (CRUD)                │
│    - Social Feed (Read)                 │
│    - Recommendations (Read)             │
├─────────────────────────────────────────┤
│  Social Permissions:                    │
│    - Public Posts: Everyone             │
│    - Followers Only: Followers          │
│    - Private: Owner Only                │
├─────────────────────────────────────────┤
│  Admin:                                 │
│    - All Models (Full Access)           │
│    - User Management                    │
│    - Content Moderation                 │
└─────────────────────────────────────────┘
```

## 🗄️ Base de Données - Relations

```
User ─┬─ 1:1 ──▶ StyleProfile
      │
      ├─ 1:N ──▶ ClothingItem
      │
      ├─ 1:N ──▶ Outfit
      │
      ├─ 1:N ──▶ OutfitPlanning
      │
      ├─ 1:N ──▶ TravelPlan
      │
      ├─ 1:N ──▶ LookbookPost
      │
      ├─ 1:N ──▶ DailyRecommendation
      │
      └─ N:N ──▶ User (UserFollow)

ClothingItem ─┬─ N:N ──▶ Outfit (through OutfitItem)
              │
              └─ N:1 ──▶ ClothingCategory

Outfit ─┬─ 1:N ──▶ LookbookPost
        │
        ├─ 1:N ──▶ OutfitPlanning
        │
        └─ N:N ──▶ TravelPlan

LookbookPost ─┬─ 1:N ──▶ PostLike
              │
              ├─ 1:N ──▶ PostComment
              │
              └─ 1:N ──▶ PostSave

StyleChallenge ─── 1:N ──▶ LookbookPost
```

## 🎨 Technologie Stack

```
┌──────────────────────────────────────────┐
│         FRONTEND (À développer)          │
│                                          │
│   React Native / Flutter / React.js      │
│   + State Management (Redux/MobX)        │
│   + HTTP Client (Axios)                  │
└──────────────────────────────────────────┘
                    ↕
        REST API (JSON + JWT)
                    ↕
┌──────────────────────────────────────────┐
│         BACKEND (✅ Implemented)         │
│                                          │
│   Django 5.0                             │
│   Django REST Framework 3.14             │
│   JWT Authentication                     │
│   Pillow (Image Processing)              │
└──────────────────────────────────────────┘
                    ↕
┌──────────────────────────────────────────┐
│            DATABASE                      │
│                                          │
│   Development: SQLite                    │
│   Production: PostgreSQL (recommended)   │
└──────────────────────────────────────────┘
                    ↕
┌──────────────────────────────────────────┐
│         EXTERNAL SERVICES                │
│                                          │
│   OpenWeatherMap API (Weather)           │
│   AWS S3 (Media Storage - optional)      │
│   Celery + Redis (Async tasks)          │
└──────────────────────────────────────────┘
```

## 📊 Métriques du Projet

| Catégorie | Quantité | Status |
|-----------|----------|--------|
| Modèles Django | 16 | ✅ |
| Applications | 6 | ✅ |
| Endpoints API (Users) | 8+ | ✅ |
| Relations DB | 25+ | ✅ |
| Tables créées | 20+ | ✅ |
| Migrations | Toutes | ✅ |
| Admin configuré | Oui | ✅ |
| Authentification | JWT | ✅ |
| Documentation | 5 docs | ✅ |

## 🚀 Prochaines Étapes

1. **Chaque étudiant:** Implémenter son module (Serializers, Views, URLs)
2. **Étudiant 4:** Intégrer OpenWeatherMap API
3. **Tous:** Développer le moteur IA de recommandations
4. **Tests:** Écrire tests unitaires pour chaque module
5. **Frontend:** Développer l'application mobile/web
6. **Déploiement:** Préparer pour production (Docker, CI/CD)

---

**Architecture conçue pour être:** 
- 📈 Scalable
- 🔧 Maintenable
- 🧩 Modulaire
- 🔒 Sécurisée
- ⚡ Performante
