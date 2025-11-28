# [file name]: serializers.py
# SUPPRIMER tout le code après PostSaveSerializer !

# Garder SEULEMENT les serializers, supprimer les ViewSets
# [file content begin]
from rest_framework import serializers
from users.models import User
from outfits.models import Outfit
from .models import LookbookPost, PostComment, PostLike, PostSave, UserFollow, StyleChallenge

class MiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_picture']

class OutfitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outfit
        fields = ['id', 'name', 'image', 'description']

class StyleChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StyleChallenge
        fields = ['id', 'title', 'description', 'theme', 'status', 'start_date', 'end_date', 'participants_count', 'hashtag', 'banner_image']

class LookbookPostSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer(read_only=True)
    outfit = OutfitSerializer(read_only=True)
    challenge = StyleChallengeSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    saves_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = LookbookPost
        fields = [
            'id', 'user', 'outfit', 'challenge', 'caption', 'hashtags',
            'visibility', 'likes_count', 'comments_count', 'saves_count',
            'created_at', 'updated_at'
        ]

class PostCommentSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ['id', 'user', 'post', 'content', 'parent_comment', 'replies', 'created_at', 'updated_at']

    def get_replies(self, obj):
        if obj.replies.exists():
            return PostCommentSerializer(obj.replies.all(), many=True).data
        return []

class UserFollowSerializer(serializers.ModelSerializer):
    follower = MiniUserSerializer(read_only=True)
    following = MiniUserSerializer(read_only=True)

    class Meta:
        model = UserFollow
        fields = ['id', 'follower', 'following', 'created_at']

class PostLikeSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer(read_only=True)

    class Meta:
        model = PostLike
        fields = ['id', 'user', 'post', 'created_at']

class PostSaveSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer(read_only=True)

    class Meta:
        model = PostSave
        fields = ['id', 'user', 'post', 'created_at']
# [file content end]