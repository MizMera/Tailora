from django.contrib import admin
from .models import OutfitPlanning, TravelPlan, WearHistory


@admin.register(OutfitPlanning)
class OutfitPlanningAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'outfit', 'event_name', 'temperature', 'weather_alert', 'was_worn']
    list_filter = ['date', 'weather_alert', 'was_worn', 'reminder_sent']
    search_fields = ['user__email', 'event_name', 'outfit__name']
    raw_id_fields = ['user', 'outfit']
    date_hierarchy = 'date'


@admin.register(TravelPlan)
class TravelPlanAdmin(admin.ModelAdmin):
    list_display = ['destination', 'user', 'start_date', 'end_date', 'duration_days', 'packing_complete']
    list_filter = ['start_date', 'packing_complete', 'trip_type']
    search_fields = ['destination', 'user__email']
    raw_id_fields = ['user']
    filter_horizontal = ['outfits', 'additional_items']
    date_hierarchy = 'start_date'


@admin.register(WearHistory)
class WearHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'worn_date', 'outfit', 'rating', 'comfort_rating', 'received_compliments']
    list_filter = ['worn_date', 'rating', 'comfort_rating', 'received_compliments']
    search_fields = ['user__email', 'outfit__name', 'notes']
    raw_id_fields = ['user', 'outfit']
    filter_horizontal = ['clothing_items']
    date_hierarchy = 'worn_date'
