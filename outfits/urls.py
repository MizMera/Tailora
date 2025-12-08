from django.urls import path
from . import views

app_name = 'outfits'

urlpatterns = [
    # Outfit management
    path('', views.outfit_gallery_view, name='outfit_gallery'),
    path('create/', views.outfit_create_view, name='outfit_create'),
    path('<uuid:outfit_id>/', views.outfit_detail_view, name='outfit_detail'),
    path('<uuid:outfit_id>/edit/', views.outfit_edit_view, name='outfit_edit'),
    path('<uuid:outfit_id>/delete/', views.outfit_delete_view, name='outfit_delete'),
    path('<uuid:outfit_id>/toggle-favorite/', views.outfit_toggle_favorite_view, name='outfit_toggle_favorite'),
    path('<uuid:outfit_id>/wear/', views.outfit_wear_view, name='outfit_wear'),
    
    # Stats
    path('stats/', views.outfit_stats_view, name='outfit_stats'),
    
    # Advanced Search
    path('advanced-search/', views.advanced_search_view, name='outfit_advanced_search'),
    
    # Challenges
    path('challenges/', views.challenges_list_view, name='challenges_list'),
    path('challenges/create/', views.create_challenge_view, name='create_challenge'),
    path('challenges/<uuid:challenge_id>/', views.challenge_detail_view, name='challenge_detail'),
    path('challenges/<uuid:challenge_id>/join/', views.join_challenge_view, name='join_challenge'),
    path('challenges/<uuid:challenge_id>/submit/', views.submit_challenge_outfit_view, name='submit_challenge_outfit'),
    path('badges/', views.badges_view, name='badges'),
]