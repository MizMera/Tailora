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
    
    # ==================== Weekly Planner Routes ====================
    path('weekly/', views.weekly_planner_view, name='weekly_planner'),
    path('weekly/generate/', views.generate_weekly_plan, name='generate_weekly_plan'),
    path('weekly/slot/<uuid:slot_id>/accept/', views.accept_daily_outfit, name='accept_daily_outfit'),
    path('weekly/slot/<uuid:slot_id>/swap/', views.swap_daily_outfit, name='swap_daily_outfit'),
    path('weekly/slot/<uuid:slot_id>/worn/', views.mark_outfit_worn, name='mark_outfit_worn'),
    path('weekly/slot/<uuid:slot_id>/regenerate/', views.regenerate_daily_slot, name='regenerate_daily_slot'),
    
    # REST API routes
    path('', include(router.urls)),
]
