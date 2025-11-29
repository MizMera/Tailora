from rest_framework import serializers
from .models import (
    DailyRecommendation, UserPreferenceSignal,
    ColorCompatibility, StyleRule, ShoppingRecommendation
)
from outfits.serializers import OutfitSerializer


class ColorCompatibilitySerializer(serializers.ModelSerializer):
    """
    Serializer for color compatibility rules
    """
    class Meta:
        model = ColorCompatibility
        fields = ['id', 'color1', 'color2', 'compatibility_score', 'rule_type']


class StyleRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for style rules
    """
    class Meta:
        model = StyleRule
        fields = ['id', 'name', 'description', 'rule_type', 'condition', 'action']


class DailyRecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for daily outfit recommendations
    """
    outfit = OutfitSerializer(read_only=True)
    outfit_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = DailyRecommendation
        fields = [
            'id', 'date', 'outfit', 'outfit_id', 'score',
            'reason', 'is_accepted', 'is_rejected',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        return DailyRecommendation.objects.create(user=user, **validated_data)


class UserPreferenceSignalSerializer(serializers.ModelSerializer):
    """
    Serializer for user feedback signals
    """
    class Meta:
        model = UserPreferenceSignal
        fields = [
            'id', 'signal_type', 'weight', 'context',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ShoppingRecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for AI shopping suggestions
    """
    complements_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ShoppingRecommendation
        fields = [
            'id', 'category', 'suggested_name', 'color', 'description',
            'reason', 'priority', 'versatility_score', 'estimated_price_min',
            'estimated_price_max', 'shopping_keywords', 'complements_count',
            'is_purchased', 'is_dismissed', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_complements_count(self, obj):
        return obj.complements.count()
