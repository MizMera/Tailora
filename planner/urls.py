from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'planner'

# REST API router
router = DefaultRouter()
router.register(r'api/events', views.EventViewSet, basename='event-api')
router.register(r'api/planning', views.OutfitPlanningViewSet, basename='planning-api')
router.register(r'api/travel', views.TravelPlanViewSet, basename='travel-api')
router.register(r'api/history', views.WearHistoryViewSet, basename='history-api')
router.register(r'api/weather', views.WeatherViewSet, basename='weather-api')

urlpatterns = [
    # Template-based calendar views
    path('', views.calendar_view, name='calendar'),
    path('events/', views.event_list, name='event_list'),
    
    # Event CRUD
    path('events/create/', views.event_create, name='event_create'),
    path('events/<uuid:event_id>/', views.event_detail, name='event_detail'),
    path('events/<uuid:event_id>/edit/', views.event_edit, name='event_edit'),
    path('events/<uuid:event_id>/delete/', views.event_delete, name='event_delete'),
    
    # Outfit assignment
    path('events/<uuid:event_id>/assign-outfit/', views.assign_outfit, name='assign_outfit'),
    path('events/<uuid:event_id>/toggle-complete/', views.toggle_complete, name='toggle_complete'),
    
    # Statistics
    path('stats/', views.event_stats, name='event_stats'),
    
    # REST API routes
    path('', include(router.urls)),
]
