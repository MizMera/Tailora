from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    # Feed
    path('', views.feed_view, name='feed'),
    path('discover/', views.discover_view, name='discover'),
    
    # Posts
    path('post/create/', views.create_post, name='create_post'),
    path('post/<uuid:post_id>/', views.post_detail, name='post_detail'),
    path('post/<uuid:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<uuid:post_id>/delete/', views.delete_post, name='delete_post'),
    
    # Interactions
    path('post/<uuid:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('post/<uuid:post_id>/save/', views.toggle_save, name='toggle_save'),
    path('post/<uuid:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<uuid:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    # User profiles
    path('profile/<uuid:user_id>/', views.profile_view, name='profile'),
    path('profile/<uuid:user_id>/followers/', views.followers_list, name='followers_list'),
    path('profile/<uuid:user_id>/following/', views.following_list, name='following_list'),
    path('profile/<uuid:user_id>/follow/', views.toggle_follow, name='toggle_follow'),
    
    # Saved posts
    path('saved/', views.saved_posts, name='saved_posts'),
    
    # Style challenges
    path('challenges/', views.challenges_list, name='challenges_list'),
    path('challenge/<uuid:challenge_id>/', views.challenge_detail, name='challenge_detail'),
]
