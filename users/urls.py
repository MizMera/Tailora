from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, StyleProfileViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'style-profiles', StyleProfileViewSet, basename='style-profile')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
