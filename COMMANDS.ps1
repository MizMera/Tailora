# Tailora Django Project - Quick Start Commands

# This file contains useful commands for the Tailora project
# Copy and paste these commands in your PowerShell terminal

# ============================================
# INITIAL SETUP (One-time only)
# ============================================

# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Create superuser for admin access
python manage.py createsuperuser
# Follow prompts: email, username, password

# ============================================
# DAILY DEVELOPMENT
# ============================================

# Activate environment (every new terminal session)
.\.venv\Scripts\Activate.ps1

# Start development server
python manage.py runserver

# Start server on different port
python manage.py runserver 8080

# ============================================
# DATABASE MANAGEMENT
# ============================================

# Create new migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Open Django shell
python manage.py shell

# Reset database (CAUTION: deletes all data)
python manage.py flush

# ============================================
# DATA POPULATION
# ============================================

# Populate clothing categories
python manage.py populate_categories

# Populate style rules and colors
python manage.py populate_style_data

# ============================================
# TESTING & VALIDATION
# ============================================

# Run system checks
python manage.py check

# Run deployment checks
python manage.py check --deploy

# Run tests (when created)
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test wardrobe

# ============================================
# UTILITIES
# ============================================

# Collect static files
python manage.py collectstatic

# Show all available commands
python manage.py help

# Show installed apps
python manage.py showmigrations

# ============================================
# ACCESS POINTS
# ============================================

# Main application: http://localhost:8000
# Admin interface: http://localhost:8000/admin
# API endpoints: http://localhost:8000/api/

# ============================================
# API TESTING EXAMPLES
# ============================================

# Using curl (in PowerShell):

# Register new user
curl -X POST http://localhost:8000/api/users/ `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"test@example.com\",\"username\":\"testuser\",\"first_name\":\"Test\",\"last_name\":\"User\",\"password\":\"TestPass123!\",\"password_confirm\":\"TestPass123!\"}'

# Login
curl -X POST http://localhost:8000/api/users/login/ `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"test@example.com\",\"password\":\"TestPass123!\"}'

# Get user profile (replace TOKEN with your access token)
curl -X GET http://localhost:8000/api/users/me/ `
  -H "Authorization: Bearer TOKEN"

# ============================================
# TROUBLESHOOTING
# ============================================

# If port 8000 is busy:
# Find process: netstat -ano | findstr :8000
# Kill process: taskkill /PID <PID> /F

# If migrations fail:
# 1. Delete db.sqlite3
# 2. Delete all migration files in each app/migrations/ (except __init__.py)
# 3. Run: python manage.py makemigrations
# 4. Run: python manage.py migrate

# If modules not found:
# Make sure virtual environment is activated:
# .\.venv\Scripts\Activate.ps1

# ============================================
# GIT WORKFLOW (Recommended)
# ============================================

# Initialize git repository
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial Tailora project setup"

# Create branch for your module
git checkout -b feature/module-users
git checkout -b feature/module-wardrobe
git checkout -b feature/module-outfits
git checkout -b feature/module-planner
git checkout -b feature/module-social

# ============================================
# PACKAGE MANAGEMENT
# ============================================

# Install new package
pip install package-name

# Save to requirements
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt

# ============================================
# NOTES
# ============================================

# - Always activate virtual environment before working
# - Run migrations after changing models
# - Test your endpoints using Postman or Insomnia
# - Commit your changes regularly
# - Document your code
# - Write tests for your features

# For more details, see:
# - README.md - Project overview
# - SETUP_GUIDE.md - Detailed setup instructions
# - API_EXAMPLES.md - API usage examples
# - PROJECT_SUMMARY.md - Complete project summary
