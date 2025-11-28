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
    
    # Stats
    path('stats/', views.outfit_stats_view, name='outfit_stats'),
]
