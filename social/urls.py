from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
app_name = 'social'

# REST API router
router = DefaultRouter()
router.register(r'api/posts', views.LookbookPostViewSet, basename='post-api')
router.register(r'api/comments', views.PostCommentViewSet, basename='comment-api')
router.register(r'api/follows', views.UserFollowViewSet, basename='follow-api')
router.register(r'api/challenges', views.StyleChallengeViewSet, basename='challenge-api')

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
    
    # AI Feature
    path('ai-preview/<uuid:outfit_id>/', views.ai_preview, name='ai_preview'),
    
    # REST API routes
    path('', include(router.urls)),

        # Drafts
    path('drafts/', views.draft_list, name='draft_list'),
    path('draft/<uuid:draft_id>/', views.draft_detail, name='draft_detail'),
    path('draft/save/', views.toggle_draft_save, name='save_draft'),
    path('draft/save/<uuid:post_id>/', views.toggle_draft_save, name='save_post_as_draft'),
    
    # AI Endpoints
    path('ai/suggestions/', views.ai_get_suggestions, name='ai_get_suggestions'),
    
    # Post Insights
    path('post/<uuid:post_id>/insights/', views.post_insights, name='post_insights'),
    path('draft/<uuid:draft_id>/publish-quick/', views.quick_publish_draft, name='quick_publish_draft'),

    path('check-scheduled/', views.manual_check_scheduled, name='manual_check_scheduled'),
    path('check-scheduled-ajax/', views.check_scheduled_posts_ajax, name='check_scheduled_ajax'),    
    
    path('force-publish-scheduled/', views.force_publish_all_scheduled, name='force_publish_scheduled'),

    
]
