from rest_framework import serializers
from .models import (
    LookbookPost, PostComment, UserFollow, 
    PostLike, PostSave, StyleChallenge
)
from outfits.serializers import OutfitSerializer
from users.serializers import UserSerializer


class UserFollowSerializer(serializers.ModelSerializer):
    """
    Serializer for user following relationships
    """
    follower = serializers.StringRelatedField(read_only=True)
    following = UserSerializer(read_only=True)
    following_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserFollow
        fields = ['id', 'follower', 'following', 'following_id', 'created_at']
        read_only_fields = ['id', 'follower', 'created_at']
    
    def create(self, validated_data):
        follower = self.context['request'].user
        following_id = validated_data.pop('following_id')
        
        # Prevent self-follow
        if follower.id == following_id:
            raise serializers.ValidationError("You cannot follow yourself.")
            
        # Check if already following
        if UserFollow.objects.filter(follower=follower, following_id=following_id).exists():
            raise serializers.ValidationError("You are already following this user.")
            
        return UserFollow.objects.create(follower=follower, following_id=following_id)


class PostCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for comments on posts
    """
    user = serializers.StringRelatedField(read_only=True)
    user_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = PostComment
        fields = ['id', 'user', 'user_avatar', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_user_avatar(self, obj):
        if hasattr(obj.user, 'profile') and obj.user.profile.avatar:
            return obj.user.profile.avatar.url
        return None
    
    def create(self, validated_data):
        user = self.context['request'].user
        post_id = self.context['view'].kwargs.get('post_pk')
        return PostComment.objects.create(user=user, post_id=post_id, **validated_data)


class LookbookPostSerializer(serializers.ModelSerializer):
    """
    Serializer for social feed posts
    """
    user = UserSerializer(read_only=True)
    outfit = OutfitSerializer(read_only=True)
    outfit_id = serializers.UUIDField(write_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = LookbookPost
        fields = [
            'id', 'user', 'outfit', 'outfit_id', 'caption', 'image',
            'likes_count', 'comments_count', 'is_liked', 'is_saved',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'likes_count', 'comments_count', 'created_at', 'updated_at']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=user).exists()
        return False

    def get_is_saved(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return PostSave.objects.filter(post=obj, user=user).exists()
        return False
    
    def create(self, validated_data):
        user = self.context['request'].user
        return LookbookPost.objects.create(user=user, **validated_data)


class StyleChallengeSerializer(serializers.ModelSerializer):
    """
    Serializer for style challenges
    """
    participants_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = StyleChallenge
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'rules', 'prize', 'participants_count', 'is_active',
            'created_at'
        ]
    
    def get_participants_count(self, obj):
        # Assuming there's a related name or we count posts linked to this challenge
        # For now, placeholder logic or if there's a ManyToMany field
        return 0 
    
    def get_is_active(self, obj):
        from django.utils import timezone
        now = timezone.now().date()
        return obj.start_date <= now <= obj.end_date
