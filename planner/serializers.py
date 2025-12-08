from rest_framework import serializers
from .models import Event, OutfitPlanning, TravelPlan, WearHistory
from outfits.models import Outfit
from outfits.serializers import OutfitSerializer
from wardrobe.models import ClothingItem
from wardrobe.serializers import ClothingItemListSerializer


class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for calendar events
    """
    outfit = OutfitSerializer(read_only=True)
    outfit_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'date', 'time', 'occasion_type',
            'location', 'notes', 'outfit', 'outfit_id',
            'is_completed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_outfit_id(self, value):
        """Validate outfit belongs to user"""
        if value:
            user = self.context['request'].user
            if not Outfit.objects.filter(id=value, user=user).exists():
                raise serializers.ValidationError("Outfit not found or doesn't belong to you")
        return value
    
    def create(self, validated_data):
        """Create event with user"""
        outfit_id = validated_data.pop('outfit_id', None)
        user = self.context['request'].user
        
        event = Event.objects.create(user=user, **validated_data)
        
        if outfit_id:
            event.outfit_id = outfit_id
            event.save()
        
        return event


class OutfitPlanningSerializer(serializers.ModelSerializer):
    """
    Serializer for outfit planning (scheduled outfits for specific dates)
    """
    outfit = OutfitSerializer(read_only=True)
    outfit_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = OutfitPlanning
        fields = [
            'id', 'outfit', 'outfit_id', 'date', 'event_name',
            'event_description', 'location', 'weather_condition',
            'temperature', 'weather_alert', 'notes',
            'reminder_sent', 'was_worn', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'weather_alert', 'reminder_sent', 'created_at', 'updated_at']
    
    def validate_outfit_id(self, value):
        """Validate outfit belongs to user"""
        user = self.context['request'].user
        if not Outfit.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Outfit not found or doesn't belong to you")
        return value
    
    def validate(self, data):
        """Validate unique date per user"""
        user = self.context['request'].user
        date = data.get('date')
        
        # Check if planning already exists for this date (exclude self during update)
        queryset = OutfitPlanning.objects.filter(user=user, date=date)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError(
                f"You already have an outfit planned for {date}. Please update that one instead."
            )
        
        return data
    
    def create(self, validated_data):
        """Create outfit planning with user"""
        user = self.context['request'].user
        return OutfitPlanning.objects.create(user=user, **validated_data)


class TravelPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for travel plans
    """
    outfits = OutfitSerializer(many=True, read_only=True)
    outfit_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    additional_items = ClothingItemListSerializer(many=True, read_only=True)
    additional_item_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = TravelPlan
        fields = [
            'id', 'destination', 'start_date', 'end_date', 'trip_type',
            'expected_weather', 'planned_activities', 'outfits', 'outfit_ids',
            'additional_items', 'additional_item_ids', 'packing_complete',
            'duration', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_duration(self, obj):
        """Get trip duration in days"""
        return obj.duration_days
    
    def validate(self, data):
        """Validate date range"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "Start date cannot be after end date"
            )
        
        return data
    
    def validate_outfit_ids(self, value):
        """Validate outfits belong to user"""
        if value:
            user = self.context['request'].user
            outfits = Outfit.objects.filter(id__in=value, user=user)
            if outfits.count() != len(value):
                raise serializers.ValidationError(
                    "Some outfits don't exist or don't belong to you"
                )
        return value
    
    def validate_additional_item_ids(self, value):
        """Validate items belong to user"""
        if value:
            user = self.context['request'].user
            items = ClothingItem.objects.filter(id__in=value, user=user)
            if items.count() != len(value):
                raise serializers.ValidationError(
                    "Some items don't exist or don't belong to you"
                )
        return value
    
    def create(self, validated_data):
        """Create travel plan with relationships"""
        outfit_ids = validated_data.pop('outfit_ids', [])
        item_ids = validated_data.pop('additional_item_ids', [])
        user = self.context['request'].user
        
        travel_plan = TravelPlan.objects.create(user=user, **validated_data)
        
        # Add outfits
        if outfit_ids:
            outfits = Outfit.objects.filter(id__in=outfit_ids, user=user)
            travel_plan.outfits.set(outfits)
        
        # Add additional items
        if item_ids:
            items = ClothingItem.objects.filter(id__in=item_ids, user=user)
            travel_plan.additional_items.set(items)
        
        return travel_plan
    
    def update(self, instance, validated_data):
        """Update travel plan with relationships"""
        outfit_ids = validated_data.pop('outfit_ids', None)
        item_ids = validated_data.pop('additional_item_ids', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update outfits if provided
        if outfit_ids is not None:
            user = self.context['request'].user
            outfits = Outfit.objects.filter(id__in=outfit_ids, user=user)
            instance.outfits.set(outfits)
        
        # Update additional items if provided
        if item_ids is not None:
            user = self.context['request'].user
            items = ClothingItem.objects.filter(id__in=item_ids, user=user)
            instance.additional_items.set(items)
        
        return instance


class WearHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for wear history tracking
    """
    outfit = OutfitSerializer(read_only=True)
    outfit_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    clothing_items = ClothingItemListSerializer(many=True, read_only=True)
    clothing_item_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = WearHistory
        fields = [
            'id', 'outfit', 'outfit_id', 'clothing_items', 'clothing_item_ids',
            'worn_date', 'rating', 'comfort_rating', 'received_compliments',
            'notes', 'weather_condition', 'temperature', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_outfit_id(self, value):
        """Validate outfit belongs to user"""
        if value:
            user = self.context['request'].user
            if not Outfit.objects.filter(id=value, user=user).exists():
                raise serializers.ValidationError("Outfit not found or doesn't belong to you")
        return value
    
    def validate_clothing_item_ids(self, value):
        """Validate items belong to user"""
        if value:
            user = self.context['request'].user
            items = ClothingItem.objects.filter(id__in=value, user=user)
            if items.count() != len(value):
                raise serializers.ValidationError(
                    "Some items don't exist or don't belong to you"
                )
        return value
    
    def validate(self, data):
        """Validate at least one of outfit or items is provided"""
        outfit_id = data.get('outfit_id')
        item_ids = data.get('clothing_item_ids', [])
        
        if not outfit_id and not item_ids:
            raise serializers.ValidationError(
                "You must provide either an outfit or individual clothing items"
            )
        
        return data
    
    def create(self, validated_data):
        """Create wear history with relationships"""
        item_ids = validated_data.pop('clothing_item_ids', [])
        user = self.context['request'].user
        
        wear_history = WearHistory.objects.create(user=user, **validated_data)
        
        # Add clothing items
        if item_ids:
            items = ClothingItem.objects.filter(id__in=item_ids, user=user)
            wear_history.clothing_items.set(items)
        
        # Update outfit times_worn if outfit is specified
        if wear_history.outfit:
            wear_history.outfit.times_worn += 1
            wear_history.outfit.last_worn = wear_history.worn_date
            wear_history.outfit.save(update_fields=['times_worn', 'last_worn'])
        
        # Update individual item times_worn
        for item in wear_history.clothing_items.all():
            item.times_worn += 1
            item.last_worn = wear_history.worn_date
            item.save(update_fields=['times_worn', 'last_worn'])
        
        return wear_history
