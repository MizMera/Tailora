from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import LookbookPostViewSet, PostCommentViewSet, UserFollowViewSet, StyleChallengeViewSet

app_name = 'social'

router = DefaultRouter()
router.register(r'posts', LookbookPostViewSet, basename='post')
router.register(r'comments', PostCommentViewSet, basename='comment')
router.register(r'follows', UserFollowViewSet, basename='follow')
router.register(r'challenges', StyleChallengeViewSet, basename='challenge')

urlpatterns = [
    # Feed
    path('', views.feed_view, name='feed'),
    path('discover/', views.discover_view, name='discover'),
    
    # Posts
    path('post/create/', views.create_post, name='create_post'),
    path('post/<uuid:post_id>/', views.post_detail, name='post_detail'),
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

    # Hashtags
    path('hashtags/trending/', views.trending_hashtags, name='trending_hashtags'),
    path('hashtags/search/<str:hashtag>/', views.hashtag_search, name='hashtag_search'),
    
    #modifier
    path('post/<uuid:post_id>/edit/', views.edit_post, name='edit_post'),

    #api
    # REST API routes
    path('api/', include(router.urls)), 
    path('api/hashtags/trending/', views.trending_hashtags),  # Pour AJAX
    # AI Photo Enhancer
    path('ai-preview/<uuid:outfit_id>/', views.ai_photo_preview, name='ai_photo_preview'),

]
