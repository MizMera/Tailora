from django.contrib import admin
from .models import UserFollow, LookbookPost, PostLike, PostComment, PostSave, StyleChallenge


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    search_fields = ['follower__email', 'following__email']
    raw_id_fields = ['follower', 'following']
    date_hierarchy = 'created_at'


@admin.register(LookbookPost)
class LookbookPostAdmin(admin.ModelAdmin):
    list_display = ['user', 'outfit', 'visibility', 'likes_count', 'comments_count', 'saves_count', 'created_at']
    list_filter = ['visibility', 'created_at', 'challenge']
    search_fields = ['user__email', 'caption', 'outfit__name']
    raw_id_fields = ['user', 'outfit', 'challenge']
    date_hierarchy = 'created_at'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    search_fields = ['user__email']
    raw_id_fields = ['user', 'post']
    date_hierarchy = 'created_at'


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content', 'parent_comment', 'created_at']
    search_fields = ['user__email', 'content']
    raw_id_fields = ['user', 'post', 'parent_comment']
    date_hierarchy = 'created_at'


@admin.register(PostSave)
class PostSaveAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    search_fields = ['user__email']
    raw_id_fields = ['user', 'post']
    date_hierarchy = 'created_at'


@admin.register(StyleChallenge)
class StyleChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'theme', 'hashtag', 'start_date', 'end_date', 'status', 'participants_count']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['title', 'theme', 'hashtag']
    date_hierarchy = 'start_date'
