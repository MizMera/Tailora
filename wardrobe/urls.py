from django.urls import path
from . import views

app_name = 'wardrobe'

urlpatterns = [
    # Template views
    path('', views.wardrobe_gallery_view, name='wardrobe_gallery'),
    path('upload/', views.wardrobe_upload_view, name='wardrobe_upload'),
    path('<uuid:item_id>/', views.wardrobe_detail_view, name='wardrobe_detail'),
    path('<uuid:item_id>/edit/', views.wardrobe_edit_view, name='wardrobe_edit'),
    path('<uuid:item_id>/delete/', views.wardrobe_delete_view, name='wardrobe_delete'),
    path('<uuid:item_id>/favorite/', views.wardrobe_toggle_favorite_view, name='wardrobe_toggle_favorite'),
    path('stats/', views.wardrobe_stats_view, name='wardrobe_stats'),
    
    # Laundry Scheduling
    path('laundry/', views.laundry_dashboard, name='laundry_dashboard'),
    path('laundry/<uuid:item_id>/washed/', views.mark_item_washed, name='mark_item_washed'),
    path('laundry/<uuid:item_id>/settings/', views.update_item_laundry_settings, name='update_item_laundry_settings'),
    path('laundry/<uuid:item_id>/status/', views.change_item_status, name='change_item_status'),
    path('laundry/alert/<uuid:alert_id>/resolve/', views.resolve_laundry_alert, name='resolve_laundry_alert'),
    path('laundry/auto-thresholds/', views.auto_set_all_thresholds, name='auto_set_all_thresholds'),
    
    # API endpoints
    path('api/items/', views.api_wardrobe_list, name='api_wardrobe_list'),
    path('api/items/create/', views.api_wardrobe_create, name='api_wardrobe_create'),
    path('api/items/<uuid:item_id>/', views.api_wardrobe_detail, name='api_wardrobe_detail'),
    path('api/items/<uuid:item_id>/update/', views.api_wardrobe_update, name='api_wardrobe_update'),
    path('api/items/<uuid:item_id>/delete/', views.api_wardrobe_delete, name='api_wardrobe_delete'),
    path('api/stats/', views.api_wardrobe_stats, name='api_wardrobe_stats'),
    path('api/analyze-image/', views.api_analyze_image, name='api_analyze_image'),
]

