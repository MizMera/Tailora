from django.contrib import admin
from .models import Outfit, OutfitItem, StyleChallenge, ChallengeParticipation, ChallengeOutfit, UserBadge

# Your existing admin registrations...
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
