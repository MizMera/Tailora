from django.contrib import admin
from .models import ClothingCategory, ClothingItem


@admin.register(ClothingCategory)
class ClothingCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_category', 'is_custom', 'user']
    list_filter = ['is_custom']
    search_fields = ['name']
    raw_id_fields = ['user', 'parent_category']


@admin.register(ClothingItem)
class ClothingItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'category', 'color', 'brand', 'status', 'favorite', 'times_worn', 'created_at']
    list_filter = ['status', 'condition', 'favorite', 'is_secondhand', 'category']
    search_fields = ['name', 'brand', 'user__email', 'color']
    raw_id_fields = ['user', 'category']
    date_hierarchy = 'created_at'
    readonly_fields = ['times_worn', 'last_worn']
