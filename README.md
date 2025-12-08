#  Tailora: AI-Powered Wardrobe Management System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django)
![License](https://img.shields.io/badge/License-Educational-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active_Development-green?style=for-the-badge)

**Tailora** is a cutting-edge, intelligent wardrobe management platform designed to digitize your closet, optimize your style, and promote sustainable fashion. By leveraging computer vision and machine learning, Tailora offers personalized outfit recommendations, smart inventory tracking, and a vibrant social community for fashion enthusiasts.

---

## 🚀 Key Features

### 🤖 AI & Computer Vision
*   **Smart Detection**: Automatically detects clothing type, color, pattern, and material using YOLOv8.
*   **Style Analysis**: Classifies items into styles (Casual, Formal, Business) and assesses wear condition.
*   **Privacy First**: All AI processing runs locally on your machine—no data leaves your device.

###  Wardrobe Management
*   **Digital Closet**: Organize your entire wardrobe with detailed metadata.
*   **Smart Filtering**: Search by color, season, occasion, or usage status (clean/laundry).
*   **Analytics**: Track cost-per-wear and most/least worn items.

###  Intelligent Styling
*   **Daily Recommendations**: Get 3-5 outfit suggestions every morning based on weather and style preferences.
*   **Outfit Builder**: Drag-and-drop interface to create and save custom looks.
*   **Travel Planner**: Generate packing lists based on destination weather and trip duration.

###  Social Community
*   **Lookbooks**: Share your best outfits and get inspired by others.
*   **Challenges**: Participate in weekly style challenges.
*   **Interaction**: Follow trendsetters, like posts, and save favorite looks.

---

##  System Architecture

Tailora is built on a modular Django architecture, ensuring scalability and maintainability.

```mermaid
graph TD
    Client[Web Client] -->|HTTP/JSON| API[Django REST API]
    API -->|ORM| DB[(SQLite/Postgres)]
    API -->|Internal| AI[AI Engine (YOLOv8)]
    API -->|External| Weather[OpenWeather API]
    
    subgraph "Core Modules"
        Users[User Management]
        Wardrobe[Wardrobe Inventory]
        Outfits[Outfit Builder]
        Planner[Style Planner]
        Social[Social Platform]
        Recs[Recommendations]
    end
    
    API --- Users
    API --- Wardrobe
    API --- Outfits
    API --- Planner
    API --- Social
    API --- Recs
```

---

##  Getting Started

Follow these steps to set up the project locally for development.

### Prerequisites
*   **Python 3.10+**
*   **Git**
*   **Virtualenv** (recommended)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/Tailora.git
    cd Tailora
    ```

2.  **Set Up Virtual Environment**
    ```bash
    python -m venv .venv
    
    # Windows
    .\.venv\Scripts\Activate.ps1
    
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Create a `.env` file in the root directory (copy from `.env.example`):
    ```bash
    copy .env.example .env
    ```
    *Update `.env` with your secret keys and API tokens.*

5.  **Initialize Database**
    ```bash
    python manage.py migrate
    python manage.py createsuperuser
    ```

6.  **Run the Server**
    ```bash
    python manage.py runserver
    ```
    Visit `http://localhost:8000` to see the app in action!

---

##  How to Contribute

We welcome contributions from the team and the community! Here is how you can help improve Tailora.

### Development Workflow

1.  **Pick a Task**: Check the `TODO.md` or project board for open tasks.
2.  **Create a Branch**: Always work on a new branch for your feature or fix.
    ```bash
    git checkout -b feature/name-of-feature
    # or
    git checkout -b fix/description-of-bug
    ```
3.  **Develop**: Write clean, documented code.
    *   **Backend**: Follow PEP 8 standards. Use `Black` for formatting.
    *   **Frontend**: Keep styles modular and JS clean.
4.  **Test**: Ensure your changes don't break existing functionality.
    ```bash
    python manage.py test
    ```
5.  **Commit**: Use clear, descriptive commit messages.
    ```bash
    git commit -m "Add: AI detection for denim textures"
    ```
6.  **Pull Request**: Push your branch and open a PR against `main`. Describe your changes and link any relevant issues.

### Project Structure Overview

Understanding the folder structure will help you navigate the codebase:

*   `tailora_project/`: Main Django settings and configuration.
*   `users/`: Authentication, profiles, and preferences.
*   `wardrobe/`: Core inventory logic and AI image processing (`ai_detection.py`).
*   `outfits/`: Outfit composition and management.
*   `planner/`: Calendar, travel planning, and weather integration.
*   `social/`: Community features (feeds, likes, comments).
*   `recommendations/`: The ML engine (`ai_engine.py`) for outfit suggestions.
*   `templates/`: Django HTML templates for the frontend.
*   `static/` & `media/`: Static assets (CSS/JS) and user-uploaded content.

---

##  License

This project is developed for educational purposes.

---

**Tailora Team** - *Innovating Fashion Tech* 
