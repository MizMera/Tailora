from django.urls import path
from . import views


urlpatterns = [
    path('', views.wardrobe_gallery_view, name='wardrobe_gallery'),
    path('upload/', views.wardrobe_upload_view, name='wardrobe_upload'),
    path('item/<uuid:item_id>/', views.wardrobe_detail_view, name='wardrobe_detail'),
    path('item/<uuid:item_id>/edit/', views.wardrobe_edit_view, name='wardrobe_edit'),
    path('item/<uuid:item_id>/delete/', views.wardrobe_delete_view, name='wardrobe_delete'),
    path('item/<uuid:item_id>/favorite/', views.wardrobe_toggle_favorite_view, name='wardrobe_toggle_favorite'),
    path('stats/', views.wardrobe_stats_view, name='wardrobe_stats'),
    
    # API endpoints
    path('api/items/', views.api_wardrobe_list, name='api_wardrobe_list'),
    path('api/items/create/', views.api_wardrobe_create, name='api_wardrobe_create'),
    path('api/items/<uuid:item_id>/', views.api_wardrobe_detail, name='api_wardrobe_detail'),
    path('api/items/<uuid:item_id>/update/', views.api_wardrobe_update, name='api_wardrobe_update'),
    path('api/items/<uuid:item_id>/delete/', views.api_wardrobe_delete, name='api_wardrobe_delete'),
    path('api/stats/', views.api_wardrobe_stats, name='api_wardrobe_stats'),
    path('api/analyze-image/', views.api_analyze_image, name='api_analyze_image'),
]