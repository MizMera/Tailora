from django.contrib import admin
from .models import DailyRecommendation, UserPreferenceSignal, ColorCompatibility, StyleRule


@admin.register(DailyRecommendation)
class DailyRecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'recommendation_date', 'outfit', 'status', 'confidence_score', 'user_rating', 'priority']
    list_filter = ['status', 'recommendation_date', 'user_rating']
    search_fields = ['user__email', 'outfit__name', 'reason']
    raw_id_fields = ['user', 'outfit']
    date_hierarchy = 'recommendation_date'
    readonly_fields = ['confidence_score', 'style_match_score']


@admin.register(UserPreferenceSignal)
class UserPreferenceSignalAdmin(admin.ModelAdmin):
    list_display = ['user', 'signal_type', 'signal_value', 'outfit', 'clothing_item', 'created_at']
    list_filter = ['signal_type', 'created_at']
    search_fields = ['user__email']
    raw_id_fields = ['user', 'outfit', 'clothing_item']
    date_hierarchy = 'created_at'


@admin.register(ColorCompatibility)
class ColorCompatibilityAdmin(admin.ModelAdmin):
    list_display = ['color1', 'color2', 'relationship_type', 'compatibility_score']
    list_filter = ['relationship_type']
    search_fields = ['color1', 'color2']


@admin.register(StyleRule)
class StyleRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_name', 'category', 'importance', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['rule_name', 'description']
