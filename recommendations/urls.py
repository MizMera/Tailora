from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    # Daily recommendations
    path('', views.daily_recommendations_view, name='daily'),
    path('daily/', views.daily_recommendations_view, name='daily'),
    
    # Actions
    path('accept/<int:recommendation_id>/', views.accept_recommendation_view, name='accept'),
    path('reject/<int:recommendation_id>/', views.reject_recommendation_view, name='reject'),
    path('rate/<int:recommendation_id>/', views.rate_recommendation_view, name='rate'),
    
    # History
    path('history/', views.recommendation_history_view, name='history'),
    
    # Generate new
    path('generate/', views.generate_new_recommendations_view, name='generate'),
]
