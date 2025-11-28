from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, StyleProfile, Notification

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 
                  'phone', 'profile_image', 'is_verified', 'onboarding_completed', 'date_joined']
        read_only_fields = ['id', 'email', 'is_verified', 'date_joined']


class StyleProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user style profile
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = StyleProfile
        fields = ['id', 'user', 'user_email', 'favorite_colors', 'preferred_styles', 
                  'favorite_brands', 'body_type', 'height', 'budget_min', 'budget_max',
                  'prefers_sustainable', 'prefers_secondhand', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'user_email', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications
    """
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 
                  'created_at', 'related_object_type', 'related_object_id']
        read_only_fields = ['id', 'created_at']
