# 🎨 Tailora - AI-Powered Wardrobe Management System

## 📋 Project Description

Tailora is a comprehensive Django-based web application that revolutionizes wardrobe management through AI-powered features. Users can digitize their wardrobe, receive intelligent outfit suggestions, plan their looks, and embrace sustainable fashion consumption. The app combines computer vision, machine learning, and fashion expertise to provide personalized styling recommendations.

## 🏗️ Architecture Overview

The project follows a modular Django architecture with 6 core modules:

```
┌─────────────────────────────────────────────────────────────┐
│                    WEB APPLICATION                          │
│                   (Django Templates)                        │
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

## 🎯 Core Features

### 🤖 AI-Powered Image Recognition
- **YOLOv8 Integration**: Automatic clothing detection and categorization
- **Color Analysis**: Primary and secondary color extraction with hex codes
- **Material Inference**: Smart material detection based on visual cues
- **Pattern Recognition**: Solid, striped, patterned classification
- **Style Classification**: Casual, formal, business attire recognition
- **Condition Assessment**: Basic wear condition estimation
- **Privacy-Focused**: All processing done locally, no external API calls

### 🎨 Intelligent Recommendations
- **Personalized Suggestions**: Daily outfit recommendations based on user preferences
- **Color Harmony**: Fashion color theory integration
- **Style Learning**: Machine learning from user feedback and behavior
- **Weather Integration**: Season and weather-appropriate suggestions
- **Multi-Factor Scoring**: Comprehensive outfit evaluation algorithm

### 👥 Social Features
- **Lookbook Sharing**: Community-driven outfit sharing
- **Style Challenges**: Weekly fashion challenges
- **Social Interactions**: Likes, comments, and follows
- **Inspiration Feed**: Personalized content discovery

## 📦 Modules Breakdown

### Module 1: User Management (`users`)
**Status: ✅ Fully Implemented**

Handles user authentication, profiles, and style preferences.

**Key Features:**
- JWT-based authentication system
- User registration and login
- Style profile creation (colors, brands, body type, preferences)
- Password reset functionality
- Email verification
- Notification system

**Models:**
- `User`: Extended Django user model
- `StyleProfile`: User's fashion preferences
- `Notification`: System notifications

**API Endpoints:**
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `GET /api/users/profile/` - Get user profile
- `PUT /api/users/profile/` - Update profile
- `GET /api/users/style-profile/` - Get style preferences
- `PUT /api/users/style-profile/` - Update style preferences

### Module 2: Wardrobe Management (`wardrobe`)
**Status: ✅ Models & Admin Complete, API In Progress**

Digital wardrobe inventory management with AI assistance.

**Key Features:**
- Photo upload with AI-powered auto-analysis
- Comprehensive item categorization (24 predefined categories)
- Advanced filtering and search
- Item status tracking (clean, laundry, lent out)
- Usage statistics and analytics
- Bulk operations support

**Models:**
- `ClothingCategory`: Hierarchical clothing categories
- `ClothingItem`: Individual wardrobe items with metadata

**AI Integration:**
- Automatic category suggestion
- Color and pattern detection
- Material and style inference
- Confidence scoring for suggestions

**API Endpoints (Planned):**
- `GET /api/wardrobe/items/` - List wardrobe items
- `POST /api/wardrobe/items/` - Add new item
- `GET /api/wardrobe/items/{id}/` - Item details
- `PUT /api/wardrobe/items/{id}/` - Update item
- `DELETE /api/wardrobe/items/{id}/` - Delete item
- `POST /api/wardrobe/analyze/` - AI image analysis

### Module 3: Outfit Creation (`outfits`)
**Status: ✅ Models & Admin Complete, API In Progress**

Visual outfit creation and management system.

**Key Features:**
- Drag-and-drop outfit builder
- Mix & match interface
- Outfit categorization by occasion
- Save and organize outfits
- Outfit statistics and analytics
- Social sharing capabilities

**Models:**
- `Outfit`: Complete outfit combinations
- `OutfitItem`: Individual items within outfits (with positioning)

**API Endpoints (Planned):**
- `GET /api/outfits/` - List saved outfits
- `POST /api/outfits/` - Create new outfit
- `GET /api/outfits/{id}/` - Outfit details
- `PUT /api/outfits/{id}/` - Update outfit
- `DELETE /api/outfits/{id}/` - Delete outfit

### Module 4: Style Planner (`planner`)
**Status: ✅ Models & Admin Complete, API In Progress**

Calendar-based outfit planning with weather integration.

**Key Features:**
- Calendar view for outfit scheduling
- Weather API integration (OpenWeatherMap)
- Travel planning assistant
- Wear history tracking
- Outfit rotation suggestions
- Seasonal planning

**Models:**
- `OutfitPlanning`: Daily outfit assignments
- `TravelPlan`: Trip planning with outfit suggestions
- `WearHistory`: Tracking of worn outfits

**API Endpoints (Planned):**
- `GET /api/planner/calendar/` - Get calendar view
- `POST /api/planner/schedule/` - Schedule outfit
- `GET /api/planner/weather/` - Weather data
- `GET /api/planner/history/` - Wear history
- `POST /api/planner/travel/` - Create travel plan

### Module 5: Social Community (`social`)
**Status: ✅ Models & Admin Complete, API In Progress**

Social fashion community and inspiration platform.

**Key Features:**
- Lookbook post sharing
- Personalized feed algorithm
- Style challenges and contests
- Social interactions (likes, comments, saves)
- User following system
- Content discovery

**Models:**
- `LookbookPost`: User-generated outfit posts
- `PostLike`, `PostComment`, `PostSave`: Social interactions
- `StyleChallenge`: Community challenges
- `UserFollow`: Social connections

**API Endpoints (Planned):**
- `GET /api/social/feed/` - Personalized feed
- `POST /api/social/posts/` - Create post
- `POST /api/social/posts/{id}/like/` - Like post
- `POST /api/social/posts/{id}/comment/` - Comment on post
- `GET /api/social/challenges/` - Active challenges

### Module 6: AI Recommendations Engine (`recommendations`)
**Status: ✅ Fully Implemented**

Machine learning-powered outfit recommendation system.

**Key Features:**
- Daily personalized recommendations (3-5 outfits)
- Multi-factor scoring algorithm:
  - Color harmony (30% weight)
  - Personal preferences (40% weight)
  - Style consistency (20% weight)
  - Seasonal appropriateness (10% weight)
- Learning from user feedback
- Weather-aware suggestions
- Fashion rule integration

**Models:**
- `DailyRecommendation`: Generated recommendations with scores
- `UserPreferenceSignal`: ML training data from user behavior
- `ColorCompatibility`: Color theory database
- `StyleRule`: Fashion combination rules

**API Endpoints:**
- `GET /api/recommendations/daily/` - Today's recommendations
- `POST /api/recommendations/{id}/accept/` - Accept recommendation
- `POST /api/recommendations/{id}/reject/` - Reject recommendation
- `POST /api/recommendations/{id}/rate/` - Rate recommendation (1-5 stars)
- `GET /api/recommendations/history/` - Recommendation history
- `POST /api/recommendations/generate/` - Generate new recommendations

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- pip package manager
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd Tailora
```

2. **Create virtual environment**
```bash
python -m venv .venv
```

3. **Activate virtual environment**
```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat

# Linux/Mac
source .venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Environment configuration**
```bash
# Copy environment template
copy .env.example .env

# Edit .env with your settings (API keys, database, etc.)
```

6. **Database setup**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Create superuser**
```bash
python manage.py createsuperuser
```

8. **Run development server**
```bash
python manage.py runserver
```

Access the application at `http://localhost:8000`

## 📁 Project Structure

```
Tailora/
├── manage.py                       # Django management script
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment configuration template
├── db.sqlite3                      # SQLite database
├── media/                          # User uploaded files
├── staticfiles/                    # Static assets
├── tailora_project/                # Main Django project
│   ├── settings.py                 # Django settings
│   ├── urls.py                     # Main URL configuration
│   ├── wsgi.py                     # WSGI configuration
│   └── asgi.py                     # ASGI configuration
├── users/                          # User management module
│   ├── models.py                   # User, StyleProfile, Notification
│   ├── views.py                    # API views
│   ├── serializers.py              # DRF serializers
│   ├── urls.py                     # URL patterns
│   ├── admin.py                    # Django admin
│   └── tests.py                    # Unit tests
├── wardrobe/                       # Wardrobe management
│   ├── models.py                   # ClothingCategory, ClothingItem
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── admin.py
│   └── ai_detection.py             # AI image analysis
├── outfits/                        # Outfit creation
│   ├── models.py                   # Outfit, OutfitItem
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
├── planner/                        # Style planning
│   ├── models.py                   # OutfitPlanning, TravelPlan, WearHistory
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
├── social/                         # Social features
│   ├── models.py                   # LookbookPost, interactions, challenges
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
├── recommendations/                # AI recommendations
│   ├── models.py                   # Recommendation models
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── ai_engine.py                # ML recommendation engine
│   └── admin.py
└── templates/                      # HTML templates
    ├── base.html                   # Base template
    ├── dashboard.html              # User dashboard
    ├── wardrobe_*.html             # Wardrobe templates
    ├── outfit_*.html               # Outfit templates
    └── ...
```

## 🔧 Technology Stack

### Backend
- **Framework**: Django 5.0
- **API**: Django REST Framework 3.14
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Image Processing**: Pillow, OpenCV
- **AI/ML**: YOLOv8 (Ultralytics), scikit-learn, NumPy
- **Weather API**: OpenWeatherMap
- **Task Queue**: Celery + Redis (optional)

### Frontend
- **Templates**: Django Templates with Bootstrap
- **Styling**: CSS3 with responsive design
- **JavaScript**: Vanilla JS with jQuery
- **Icons**: Font Awesome

### Development Tools
- **Version Control**: Git
- **Environment**: python-decouple
- **Testing**: Django Test Framework
- **Documentation**: Markdown files
- **Code Quality**: Black, Flake8

## 🔐 Security Features

- JWT token-based authentication
- Password hashing with Django's auth system
- CSRF protection
- Input validation and sanitization
- Secure file upload handling
- Environment variable management for secrets
- CORS configuration for API access

## 📊 Data Models Overview

### Core Relationships
```
User (1) ──── (1) StyleProfile
   │
   ├── (N) ClothingItem
   │      │
   │      └── (1) ClothingCategory
   │
   ├── (N) Outfit
   │      │
   │      └── (N) OutfitItem ──── (1) ClothingItem
   │
   ├── (N) OutfitPlanning
   │
   ├── (N) LookbookPost
   │      │
   │      ├── (N) PostLike
   │      ├── (N) PostComment
   │      └── (N) PostSave
   │
   └── (N) DailyRecommendation
          │
          └── (N) UserPreferenceSignal
```

## 🎯 Development Roadmap

### Phase 1: Core Implementation ✅
- [x] User authentication and profiles
- [x] Wardrobe management with AI analysis
- [x] AI recommendation engine
- [x] Basic outfit creation
- [x] Database models and relationships
- [x] Django admin interfaces

### Phase 2: API Development 🔄
- [ ] Complete REST API for all modules
- [ ] API documentation with Swagger/OpenAPI
- [ ] Comprehensive test coverage
- [ ] Performance optimization

### Phase 3: Advanced Features 📋
- [ ] Weather API integration
- [ ] Social features implementation
- [ ] Mobile app development
- [ ] Advanced AI features (style evolution, trend analysis)
- [ ] Push notifications

### Phase 4: Production Deployment 🚀
- [ ] PostgreSQL migration
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Monitoring and logging
- [ ] Security audit

## � Contributing

### Development Team
- **Users Module**: Authentication, profiles, notifications
- **Wardrobe Module**: AI image analysis, inventory management
- **Outfits Module**: Visual outfit builder, mix & match
- **Planner Module**: Calendar integration, weather API
- **Social Module**: Community features, interactions
- **Recommendations Module**: ML algorithms, personalization

### Code Standards
- Follow Django best practices
- Write comprehensive unit tests
- Use meaningful commit messages
- Document complex algorithms
- Maintain API consistency

## 📖 Documentation

- [Setup Guide](SETUP_GUIDE.md) - Detailed installation instructions
- [API Examples](API_EXAMPLES.md) - API usage examples
- [Architecture](ARCHITECTURE.md) - System architecture details
- [AI Features](AI_IMAGE_RECOGNITION_README.md) - AI capabilities documentation
- [Testing Guide](TESTING_GUIDE.md) - Testing procedures
- [Project Summary](PROJECT_SUMMARY.md) - Current implementation status

## 📄 License

This project is developed for educational purposes.

---

**Tailora** - Your intelligent wardrobe companion 🎨👗👔
