from rest_framework import serializers
from .models import Outfit, OutfitItem
from wardrobe.models import ClothingItem
from wardrobe.serializers import ClothingItemListSerializer


class OutfitItemSerializer(serializers.ModelSerializer):
    """
    Serializer for items within an outfit
    Includes positioning data for visual composition
    """
    clothing_item = ClothingItemListSerializer(read_only=True)
    clothing_item_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = OutfitItem
        fields = [
            'id', 'clothing_item', 'clothing_item_id', 
            'layer', 'position', 'x_position', 'y_position'
        ]
        read_only_fields = ['id']


class OutfitSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing outfits
    Used in gallery/grid views
    """
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Outfit
        fields = [
            'id', 'name', 'occasion', 'favorite', 
            'times_worn', 'outfit_image', 'created_at',
            'items_count'
        ]
        read_only_fields = ['id', 'created_at', 'times_worn']
    
    def get_items_count(self, obj):
        """Get number of items in outfit"""
        return obj.items.count()


class OutfitDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for single outfit details
    Includes all information and nested items
    """
    outfit_items = OutfitItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Outfit
        fields = [
            'id', 'user', 'name', 'description', 'occasion',
            'style_tags', 'source', 'rating', 'times_worn',
            'last_worn', 'favorite', 'min_temperature',
            'max_temperature', 'suitable_weather', 'outfit_image',
            'created_at', 'updated_at', 'outfit_items', 'items_count'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'times_worn']
    
    def get_items_count(self, obj):
        """Get number of items in outfit"""
        return obj.items.count()


class OutfitCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new outfits
    Handles item selection and validation
    """
    item_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    outfit_items_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Outfit
        fields = [
            'name', 'description', 'occasion', 'style_tags',
            'min_temperature', 'max_temperature', 'suitable_weather',
            'item_ids', 'outfit_items_data'
        ]
    
    def validate_item_ids(self, value):
        """Validate that items exist and belong to user"""
        if not value:
            return value
        
        user = self.context['request'].user
        
        # Check all items exist and belong to user
        items = ClothingItem.objects.filter(id__in=value, user=user)
        if items.count() != len(value):
            raise serializers.ValidationError(
                "Some items don't exist or don't belong to you"
            )
        
        return value
    
    def validate(self, data):
        """Validate outfit data"""
        # Check user's outfit limit
        user = self.context['request'].user
        current_count = Outfit.objects.filter(user=user).count()
        max_outfits = user.get_max_outfits()
        
        if current_count >= max_outfits:
            raise serializers.ValidationError(
                f"You've reached your outfit limit of {max_outfits}. "
                f"Upgrade to Premium to create more!"
            )
        
        # Validate temperature range
        min_temp = data.get('min_temperature')
        max_temp = data.get('max_temperature')
        
        if min_temp is not None and max_temp is not None:
            if min_temp > max_temp:
                raise serializers.ValidationError(
                    "Minimum temperature cannot be higher than maximum temperature"
                )
        
        return data
    
    def create(self, validated_data):
        """Create outfit with items"""
        item_ids = validated_data.pop('item_ids', [])
        outfit_items_data = validated_data.pop('outfit_items_data', [])
        user = self.context['request'].user
        
        # Create outfit
        validated_data['user'] = user
        validated_data['source'] = 'user'
        outfit = Outfit.objects.create(**validated_data)
        
        # Add items to outfit
        if outfit_items_data:
            # If detailed item data provided
            for item_data in outfit_items_data:
                OutfitItem.objects.create(
                    outfit=outfit,
                    clothing_item_id=item_data['clothing_item_id'],
                    layer=item_data.get('layer', 'base'),
                    position=item_data.get('position', 0),
                    x_position=item_data.get('x_position'),
                    y_position=item_data.get('y_position')
                )
        elif item_ids:
            # If just item IDs provided, create with defaults
            for idx, item_id in enumerate(item_ids):
                OutfitItem.objects.create(
                    outfit=outfit,
                    clothing_item_id=item_id,
                    position=idx
                )
        
        # Update user's outfit count
        user.increment_outfits_count()
        
        return outfit


class OutfitUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing outfits
    """
    class Meta:
        model = Outfit
        fields = [
            'name', 'description', 'occasion', 'style_tags',
            'rating', 'favorite', 'min_temperature',
            'max_temperature', 'suitable_weather'
        ]
    
    def validate(self, data):
        """Validate outfit data"""
        # Validate temperature range
        instance = self.instance
        min_temp = data.get('min_temperature', instance.min_temperature)
        max_temp = data.get('max_temperature', instance.max_temperature)
        
        if min_temp is not None and max_temp is not None:
            if min_temp > max_temp:
                raise serializers.ValidationError(
                    "Minimum temperature cannot be higher than maximum temperature"
                )
        
        return data
