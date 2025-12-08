"""
URL configuration for tailora_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.auth_views import (
    login_view, register_view, logout_view, dashboard_view,
    password_reset_request_view, password_reset_confirm_view,
    verify_email_view, resend_verification_email_view,
    profile_settings_view, change_password_view, verify_password_change_view,
    request_account_deletion_view, confirm_account_deletion_view,
    upgrade_account_view, cancel_subscription_view, ai_style_analyze_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication pages
    path('', login_view, name='login'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Password Reset
    path('password-reset/', password_reset_request_view, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', password_reset_confirm_view, name='password_reset_confirm'),
    
    # Email Verification
    path('verify-email/<uidb64>/<token>/', verify_email_view, name='verify_email'),
    path('resend-verification/', resend_verification_email_view, name='resend_verification'),
    
    # Profile & Account Management
    path('profile/settings/', profile_settings_view, name='profile_settings'),
    path('profile/change-password/', change_password_view, name='change_password'),
    path('profile/verify-password-change/', verify_password_change_view, name='verify_password_change'),
    path('profile/request-account-deletion/', request_account_deletion_view, name='request_account_deletion'),
    path('profile/confirm-account-deletion/', confirm_account_deletion_view, name='confirm_account_deletion'),
    path('profile/upgrade/', upgrade_account_view, name='upgrade_account'),
    path('profile/cancel-subscription/', cancel_subscription_view, name='cancel_subscription'),
    path('profile/analyze-style/', ai_style_analyze_view, name='ai_style_analyze'),
    
    # JWT Authentication (API)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Module URLs
    path('wardrobe/', include('wardrobe.urls')),  # Module 2: Wardrobe Management
    path('outfits/', include('outfits.urls')),  # Module 3: Outfit Management
    path('planner/', include('planner.urls')),  # Module 4: Calendar & Events
    path('social/', include('social.urls')),  # Module 5: Social Features
    path('recommendations/', include('recommendations.urls')),  # Module 6: AI Recommendations
    
    # API endpoints
    path('api/', include('users.urls')),
    # path('api/outfits/', include('outfits.urls')),   # To be created by Student 3
    # path('api/planner/', include('planner.urls')),   # To be created by Student 4
    # path('api/social/', include('social.urls')),    # To be created by Student 5
    # path('api/recommendations/', include('recommendations.urls')),  # To be created by Student 6
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
