from rest_framework import serializers
from .models import ClothingItem, ClothingCategory
from users.models import User


class ClothingCategorySerializer(serializers.ModelSerializer):
    """Serializer for clothing categories"""
    
    class Meta:
        model = ClothingCategory
        fields = ['id', 'name', 'parent_category', 'is_custom', 'icon']
        read_only_fields = ['id']


class ClothingItemListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing wardrobe items
    Used for gallery/grid views
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ClothingItem
        fields = [
            'id', 'name', 'image', 'color', 'color_hex', 
            'category_name', 'brand', 'favorite', 'times_worn',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'times_worn']


class ClothingItemDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for single item details
    Includes all information
    """
    category = ClothingCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ClothingItem
        fields = [
            'id', 'user', 'name', 'description', 'category', 'category_id',
            'image', 'color', 'color_hex', 'pattern', 'material', 'brand',
            'seasons', 'occasions', 'purchase_date', 'purchase_price',
            'purchase_location', 'is_secondhand', 'status', 'condition',
            'times_worn', 'last_worn', 'favorite', 'tags',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'times_worn']
    
    def validate_seasons(self, value):
        """Validate seasons list"""
        valid_seasons = ['spring', 'summer', 'fall', 'winter', 'all_seasons']
        if not isinstance(value, list):
            raise serializers.ValidationError("Seasons must be a list")
        for season in value:
            if season not in valid_seasons:
                raise serializers.ValidationError(f"Invalid season: {season}")
        return value
    
    def validate_occasions(self, value):
        """Validate occasions list"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Occasions must be a list")
        return value
    
    def validate_color_hex(self, value):
        """Validate hex color format"""
        if value and not value.startswith('#'):
            value = f"#{value}"
        if value and len(value) != 7:
            raise serializers.ValidationError("Color hex must be in format #RRGGBB")
        return value


class ClothingItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new wardrobe items
    Handles image upload
    """
    category_id = serializers.UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = ClothingItem
        fields = [
            'name', 'description', 'category_id', 'image', 
            'color', 'color_hex', 'pattern', 'material', 'brand',
            'seasons', 'occasions', 'purchase_date', 'purchase_price',
            'purchase_location', 'is_secondhand', 'condition', 'tags'
        ]
    
    def validate_image(self, value):
        """Validate uploaded image"""
        # Check file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image size should not exceed 5MB")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only JPEG and PNG images are allowed")
        
        return value
    
    def create(self, validated_data):
        """Create item with user from context"""
        user = self.context['request'].user
        
        # Check user's wardrobe limit
        current_count = ClothingItem.objects.filter(user=user).count()
        max_items = user.get_max_wardrobe_items()
        
        if current_count >= max_items:
            raise serializers.ValidationError(
                f"You've reached your wardrobe limit of {max_items} items. Upgrade to Premium to add more!"
            )
        
        # Handle category
        category_id = validated_data.pop('category_id', None)
        if category_id:
            try:
                category = ClothingCategory.objects.get(id=category_id)
                validated_data['category'] = category
            except ClothingCategory.DoesNotExist:
                pass
        
        validated_data['user'] = user
        item = ClothingItem.objects.create(**validated_data)
        
        # Update user's wardrobe count
        user.increment_wardrobe_count()
        
        return item


class WardrobeStatsSerializer(serializers.Serializer):
    """Serializer for wardrobe statistics"""
    total_items = serializers.IntegerField()
    by_category = serializers.DictField()
    by_color = serializers.DictField()
    by_season = serializers.DictField()
    favorite_count = serializers.IntegerField()
    most_worn = serializers.ListField()
    recent_additions = serializers.ListField()
    wardrobe_limit = serializers.IntegerField()
    remaining_slots = serializers.IntegerField()
