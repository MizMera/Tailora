from django.urls import path
from . import views

app_name = 'planner'

urlpatterns = [
    # Calendar views
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
    
    # Geolocation
    path('geocode/', views.geocode_location, name='geocode_location'),
    
    path('wear-history/', views.wear_history_list, name='wear_history_list'),
    path('event/<uuid:event_id>/mark-worn-and-back/', views.mark_worn_and_back, name='mark_worn_and_back'),
    path('event/<uuid:event_id>/add-wear-history/', views.add_wear_history_from_event, name='add_wear_history_from_event'),
    path('wear-history/<uuid:entry_id>/delete/', views.delete_wear_history, name='delete_wear_history'),

    
]
