# 📡 Exemples d'Appels API - Tailora

Ce document contient des exemples concrets d'utilisation de l'API Tailora.

## 🔐 Authentification

### Inscription d'un nouvel utilisateur
```http
POST /api/users/
Content-Type: application/json

{
    "email": "marie@example.com",
    "username": "marie_style",
    "first_name": "Marie",
    "last_name": "Dupont",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
}
```

**Réponse (201 Created):**
```json
{
    "id": "uuid-here",
    "email": "marie@example.com",
    "username": "marie_style",
    "first_name": "Marie",
    "last_name": "Dupont",
    "phone": null,
    "profile_image": null,
    "is_verified": false,
    "onboarding_completed": false,
    "date_joined": "2024-11-04T10:30:00Z"
}
```

### Connexion (Login)
```http
POST /api/users/login/
Content-Type: application/json

{
    "email": "marie@example.com",
    "password": "SecurePass123!"
}
```

**Réponse (200 OK):**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": "uuid-here",
        "email": "marie@example.com",
        "username": "marie_style",
        "first_name": "Marie",
        "last_name": "Dupont"
    }
}
```

### Rafraîchir le token
```http
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## 👤 Profil Utilisateur

### Obtenir son profil
```http
GET /api/users/me/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Modifier son profil
```http
PUT /api/users/me/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
    "first_name": "Marie-Claire",
    "phone": "+33612345678"
}
```

## 🎨 Profil de Style

### Créer/Modifier son profil de style
```http
POST /api/style-profiles/me/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
    "favorite_colors": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
    "preferred_styles": ["chic", "casual", "minimaliste"],
    "favorite_brands": ["Zara", "H&M", "Mango"],
    "body_type": "sablier",
    "height": 165,
    "budget_min": 50.00,
    "budget_max": 200.00,
    "prefers_sustainable": true,
    "prefers_secondhand": true
}
```

## 👗 Garde-robe (Module 2 - À implémenter)

### Ajouter un vêtement
```http
POST /api/wardrobe/items/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: multipart/form-data

{
    "name": "Robe d'été fleurie",
    "description": "Belle robe légère pour l'été",
    "category": "uuid-categorie-robes",
    "image": [file],
    "color": "Bleu",
    "color_hex": "#4ECDC4",
    "pattern": "Fleuri",
    "material": "Coton",
    "brand": "Zara",
    "seasons": ["spring", "summer"],
    "occasions": ["casual", "weekend"],
    "purchase_date": "2024-06-15",
    "purchase_price": 45.99,
    "status": "available"
}
```

### Lister les vêtements avec filtres
```http
GET /api/wardrobe/items/?color=Bleu&status=available&category=robes
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Modifier un vêtement
```http
PUT /api/wardrobe/items/{id}/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
    "status": "washing",
    "favorite": true
}
```

## 👔 Tenues (Module 3 - À implémenter)

### Créer une tenue
```http
POST /api/outfits/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
    "name": "Look décontracté du samedi",
    "description": "Tenue confortable pour le weekend",
    "occasion": "weekend",
    "items": [
        {
            "clothing_item": "uuid-item-1",
            "layer": "base",
            "position": 1
        },
        {
            "clothing_item": "uuid-item-2",
            "layer": "outer",
            "position": 2
        },
        {
            "clothing_item": "uuid-item-3",
            "layer": "shoes",
            "position": 3
        }
    ],
    "style_tags": ["casual", "comfortable"],
    "min_temperature": 15,
    "max_temperature": 25
}
```

### Lister mes tenues
```http
GET /api/outfits/?occasion=work&favorite=true
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## 📅 Planification (Module 4 - À implémenter)

### Planifier une tenue pour une date
```http
POST /api/planner/schedule/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
    "outfit": "uuid-outfit",
    "date": "2024-11-15",
    "event_name": "Réunion importante",
    "location": "Bureau Paris"
}
```

### Voir le calendrier
```http
GET /api/planner/calendar/?start_date=2024-11-01&end_date=2024-11-30
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Créer un plan de voyage
```http
POST /api/planner/travel/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
    "destination": "Nice",
    "start_date": "2024-12-20",
    "end_date": "2024-12-27",
    "trip_type": "vacation",
    "planned_activities": ["plage", "restaurants", "randonnée"],
    "outfits": ["uuid-outfit-1", "uuid-outfit-2", "uuid-outfit-3"]
}
```

## 🌐 Social (Module 5 - À implémenter)

### Publier une tenue
```http
POST /api/social/posts/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
    "outfit": "uuid-outfit",
    "caption": "Mon look préféré pour les soirées d'été! 🌺",
    "hashtags": ["lookdujour", "summervibes", "chicstyle"],
    "visibility": "public"
}
```

### Liker une publication
```http
POST /api/social/posts/{post_id}/like/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Commenter une publication
```http
POST /api/social/posts/{post_id}/comment/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
    "content": "Superbe tenue! J'adore les couleurs 😍"
}
```

### Suivre un utilisateur
```http
POST /api/social/users/{user_id}/follow/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Voir le fil d'actualité
```http
GET /api/social/feed/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Participer à un défi
```http
POST /api/social/challenges/{challenge_id}/submit/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
    "outfit": "uuid-outfit",
    "caption": "Mon interprétation du look monochrome!"
}
```

## 🤖 Recommandations IA (Module 6 - À implémenter)

### Obtenir les recommandations du jour
```http
GET /api/recommendations/daily/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Réponse:**
```json
{
    "date": "2024-11-04",
    "recommendations": [
        {
            "id": "uuid-rec-1",
            "outfit": {
                "id": "uuid-outfit",
                "name": "Look professionnel",
                "items": [...]
            },
            "reason": "Cette tenue convient parfaitement pour le temps pluvieux prévu aujourd'hui et correspond à votre style chic.",
            "confidence_score": 0.92,
            "weather_factor": {
                "condition": "rainy",
                "temperature": 15,
                "humidity": 80
            },
            "style_match_score": 0.95
        },
        {
            "id": "uuid-rec-2",
            "outfit": {...},
            "reason": "...",
            "confidence_score": 0.88
        }
    ]
}
```

### Accepter une recommandation
```http
POST /api/recommendations/{rec_id}/accept/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Noter une recommandation
```http
POST /api/recommendations/{rec_id}/rate/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
    "user_rating": 5,
    "user_feedback": "Excellente suggestion! J'ai reçu beaucoup de compliments."
}
```

## 🔔 Notifications

### Lister les notifications
```http
GET /api/notifications/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Marquer comme lue
```http
POST /api/notifications/{notification_id}/mark_read/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Marquer toutes comme lues
```http
POST /api/notifications/mark_all_read/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## 📝 Notes d'Implémentation

### Headers requis pour toutes les requêtes authentifiées:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

### Codes de statut HTTP:
- `200 OK` - Succès
- `201 Created` - Ressource créée
- `204 No Content` - Succès sans contenu de retour
- `400 Bad Request` - Données invalides
- `401 Unauthorized` - Non authentifié
- `403 Forbidden` - Non autorisé
- `404 Not Found` - Ressource non trouvée
- `500 Internal Server Error` - Erreur serveur

### Pagination:
```http
GET /api/wardrobe/items/?page=2&page_size=20
```

**Réponse:**
```json
{
    "count": 150,
    "next": "http://localhost:8000/api/wardrobe/items/?page=3",
    "previous": "http://localhost:8000/api/wardrobe/items/?page=1",
    "results": [...]
}
```

### Filtres et recherche:
```http
# Recherche textuelle
GET /api/wardrobe/items/?search=chemise

# Filtres multiples
GET /api/wardrobe/items/?color=Bleu&brand=Zara&status=available

# Tri
GET /api/wardrobe/items/?ordering=-created_at
GET /api/wardrobe/items/?ordering=name
```

## 🧪 Test avec cURL

### Exemple d'inscription:
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!"
  }'
```

### Exemple avec authentification:
```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

## 🔧 Outils Recommandés

- **Postman** - https://www.postman.com/
- **Insomnia** - https://insomnia.rest/
- **Thunder Client** (VS Code extension)
- **HTTPie** - https://httpie.io/

---

**Bonne chance pour l'implémentation! 🚀**
