<<<<<<< HEAD
from django.urls import path
=======
from django.urls import path, include
from rest_framework.routers import DefaultRouter
>>>>>>> main
from . import views

app_name = 'recommendations'

<<<<<<< HEAD
=======
# REST API router
router = DefaultRouter()
router.register(r'api/daily', views.RecommendationViewSet, basename='recommendation-api')
router.register(r'api/colors', views.ColorCompatibilityViewSet, basename='color-api')
router.register(r'api/rules', views.StyleRuleViewSet, basename='rule-api')

>>>>>>> main
urlpatterns = [
    # Daily recommendations
    path('', views.daily_recommendations_view, name='daily'),
    path('daily/', views.daily_recommendations_view, name='daily'),
    
<<<<<<< HEAD
    # Actions
    path('accept/<int:recommendation_id>/', views.accept_recommendation_view, name='accept'),
    path('reject/<int:recommendation_id>/', views.reject_recommendation_view, name='reject'),
    path('rate/<int:recommendation_id>/', views.rate_recommendation_view, name='rate'),
=======
    # Actions - FIXED: Changed from int to uuid
    path('accept/<uuid:recommendation_id>/', views.accept_recommendation_view, name='accept'),
    path('reject/<uuid:recommendation_id>/', views.reject_recommendation_view, name='reject'),
    path('rate/<uuid:recommendation_id>/', views.rate_recommendation_view, name='rate'),
>>>>>>> main
    
    # History
    path('history/', views.recommendation_history_view, name='history'),
    
    # Generate new
    path('generate/', views.generate_new_recommendations_view, name='generate'),
<<<<<<< HEAD
=======
    
    # REST API routes
    path('', include(router.urls)),
>>>>>>> main
]
