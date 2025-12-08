from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'recommendations'

# REST API router
router = DefaultRouter()
router.register(r'api/daily', views.RecommendationViewSet, basename='recommendation-api')
router.register(r'api/colors', views.ColorCompatibilityViewSet, basename='color-api')
router.register(r'api/rules', views.StyleRuleViewSet, basename='rule-api')

urlpatterns = [
    # Daily recommendations
    path('', views.daily_recommendations_view, name='daily'),
    path('daily/', views.daily_recommendations_view, name='daily'),
    
    # Actions - FIXED: Changed from int to uuid
    path('accept/<uuid:recommendation_id>/', views.accept_recommendation_view, name='accept'),
    path('reject/<uuid:recommendation_id>/', views.reject_recommendation_view, name='reject'),
    path('rate/<uuid:recommendation_id>/', views.rate_recommendation_view, name='rate'),
    
    # History
    path('history/', views.recommendation_history_view, name='history'),
    
    # Generate new
    path('generate/', views.generate_new_recommendations_view, name='generate'),
    
    # REST API routes
    path('', include(router.urls)),
]
