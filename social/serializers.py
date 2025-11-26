from rest_framework import serializers
from .models import LookbookPost, PostLike, PostComment, PostSave, UserFollow, StyleChallenge
from users.models import User
from outfits.models import Outfit
from outfits.serializers import OutfitSerializer


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for social features"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_image', 'role']
        read_only_fields = fields


class UserFollowSerializer(serializers.ModelSerializer):
    """Serializer for follow relationships"""
    follower = UserBasicSerializer(read_only=True)
    following = UserBasicSerializer(read_only=True)
    following_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = UserFollow
        fields = ['id', 'follower', 'following', 'following_id', 'created_at']
        read_only_fields = ['id', 'follower', 'created_at']
    
    def validate_following_id(self, value):
        """Validate user exists and not self-follow"""
        request_user = self.context['request'].user
        
        if value == request_user.id:
            raise serializers.ValidationError("You cannot follow yourself")
        
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found")
        
        return value
    
    def create(self, validated_data):
        """Create follow relationship"""
        return UserFollow.objects.create(
            follower=self.context['request'].user,
            following_id=validated_data['following_id']
        )


class PostCommentSerializer(serializers.ModelSerializer):
    """Serializer for post comments"""
    user = UserBasicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = PostComment
        fields = ['id', 'user', 'content', 'parent_comment', 'replies', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        """Get replies to this comment"""
        if obj.parent_comment:
            return None  # Don't nest deeper than 1 level
        replies = obj.replies.all()[:5]  # Limit replies
        return PostCommentSerializer(replies, many=True, context=self.context).data


class LookbookPostSerializer(serializers.ModelSerializer):
    """Serializer for lookbook posts"""
    user = UserBasicSerializer(read_only=True)
    outfit = OutfitSerializer(read_only=True)
    outfit_id = serializers.UUIDField(write_only=True)
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    recent_comments = serializers.SerializerMethodField()
    
    class Meta:
        model = LookbookPost
        fields = [
            'id', 'user', 'outfit', 'outfit_id', 'caption', 'hashtags',
            'visibility', 'likes_count', 'comments_count', 'saves_count',
            'challenge', 'is_liked', 'is_saved', 'recent_comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'likes_count', 'comments_count', 'saves_count',
            'created_at', 'updated_at'
        ]
    
    def get_is_liked(self, obj):
        """Check if current user liked this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(user=request.user, post=obj).exists()
        return False
    
    def get_is_saved(self, obj):
        """Check if current user saved this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostSave.objects.filter(user=request.user, post=obj).exists()
        return False
    
    def get_recent_comments(self, obj):
        """Get the 3 most recent comments"""
        comments = obj.comments.filter(parent_comment__isnull=True).order_by('-created_at')[:3]
        return PostCommentSerializer(comments, many=True, context=self.context).data
    
    def validate_outfit_id(self, value):
        """Validate outfit belongs to user"""
        user = self.context['request'].user
        if not Outfit.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Outfit not found or doesn't belong to you")
        return value
    
    def validate_hashtags(self, value):
        """Validate hashtags format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Hashtags must be a list")
        
        # Ensure all start with #
        cleaned = []
        for tag in value:
            tag = str(tag).strip()
            if tag and not tag.startswith('#'):
                tag = f'#{tag}'
            if tag:
                cleaned.append(tag.lower())
        
        return cleaned[:10]  # Limit to 10 hashtags
    
    def create(self, validated_data):
        """Create lookbook post"""
        user = self.context['request'].user
        post = LookbookPost.objects.create(user=user, **validated_data)
        
        # Increment user's posts count
        user.increment_posts_count()
        
        return post


class StyleChallengeSerializer(serializers.ModelSerializer):
    """Serializer for style challenges"""
    submissions_count = serializers.SerializerMethodField()
    user_participated = serializers.SerializerMethodField()
    
    class Meta:
        model = StyleChallenge
        fields = [
            'id', 'title', 'description', 'theme', 'start_date', 'end_date',
            'status', 'rules', 'hashtag', 'banner_image', 'participants_count',
            'submissions_count', 'user_participated', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'participants_count', 'created_at', 'updated_at']
    
    def get_submissions_count(self, obj):
        """Get number of submissions"""
        return obj.submissions.count()
    
    def get_user_participated(self, obj):
        """Check if current user participated"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.submissions.filter(user=request.user).exists()
        return False
