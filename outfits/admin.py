from django.contrib import admin
from .models import Outfit, OutfitItem, StyleChallenge, ChallengeParticipation, ChallengeOutfit, UserBadge


class OutfitItemInline(admin.TabularInline):
    model = OutfitItem
    extra = 1
    raw_id_fields = ['clothing_item']


@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'occasion', 'source', 'favorite', 'times_worn', 'rating', 'created_at']
    list_filter = ['occasion', 'source', 'favorite', 'created_at']
    search_fields = ['name', 'user__email', 'description']
    raw_id_fields = ['user']
    inlines = [OutfitItemInline]
    date_hierarchy = 'created_at'


@admin.register(OutfitItem)
class OutfitItemAdmin(admin.ModelAdmin):
    list_display = ['outfit', 'clothing_item', 'layer', 'position']
    list_filter = ['layer']
    raw_id_fields = ['outfit', 'clothing_item']


@admin.register(StyleChallenge)
class StyleChallengeAdmin(admin.ModelAdmin):
    list_display = ['name', 'challenge_type', 'created_by', 'is_public', 'start_date', 'end_date']
    list_filter = ['challenge_type', 'is_public', 'start_date']
    search_fields = ['name', 'description']
    raw_id_fields = ['created_by']


@admin.register(ChallengeParticipation)
class ChallengeParticipationAdmin(admin.ModelAdmin):
    list_display = ['user', 'challenge', 'joined_at', 'completed', 'completed_at']
    list_filter = ['completed', 'joined_at']
    raw_id_fields = ['user', 'challenge']


@admin.register(ChallengeOutfit)
class ChallengeOutfitAdmin(admin.ModelAdmin):
    list_display = ['participation', 'outfit', 'submitted_at']
    raw_id_fields = ['participation', 'outfit']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'badge_type', 'earned_at']
    list_filter = ['badge_type', 'earned_at']
    raw_id_fields = ['user']
