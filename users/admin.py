from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StyleProfile, Notification, FashionIQ, StyleCritiqueSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'email', 'username', 'role', 'status', 'is_verified', 
        'wardrobe_items_count', 'outfits_created_count', 'date_joined'
    ]
    list_filter = [
        'role', 'status', 'is_verified', 'onboarding_completed', 
        'is_staff', 'is_active', 'date_joined'
    ]
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    readonly_fields = [
        'date_joined', 'last_active', 'wardrobe_items_count', 
        'outfits_created_count', 'posts_count', 'followers_count', 'following_count'
    ]
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Tailora Info', {
            'fields': ('phone', 'profile_image', 'is_verified', 'onboarding_completed')
        }),
        ('Role & Status', {
            'fields': ('role', 'status', 'premium_until')
        }),
        ('Statistics', {
            'fields': (
                'wardrobe_items_count', 'outfits_created_count', 'posts_count',
                'followers_count', 'following_count', 'last_active'
            )
        }),
    )
    
    actions = ['make_premium', 'make_stylist', 'make_influencer', 'activate_users', 'suspend_users']
    
    def make_premium(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        queryset.update(role='premium', premium_until=timezone.now() + timedelta(days=365))
        self.message_user(request, f"{queryset.count()} utilisateurs sont maintenant Premium.")
    make_premium.short_description = "Rendre Premium (1 an)"
    
    def make_stylist(self, request, queryset):
        queryset.update(role='stylist')
        self.message_user(request, f"{queryset.count()} utilisateurs sont maintenant Stylistes.")
    make_stylist.short_description = "Rendre Styliste"
    
    def make_influencer(self, request, queryset):
        queryset.update(role='influencer')
        self.message_user(request, f"{queryset.count()} utilisateurs sont maintenant Influenceurs.")
    make_influencer.short_description = "Rendre Influenceur"
    
    def activate_users(self, request, queryset):
        queryset.update(status='active', is_active=True)
        self.message_user(request, f"{queryset.count()} utilisateurs activés.")
    activate_users.short_description = "Activer les comptes"
    
    def suspend_users(self, request, queryset):
        queryset.update(status='suspended', is_active=False)
        self.message_user(request, f"{queryset.count()} utilisateurs suspendus.")
    suspend_users.short_description = "Suspendre les comptes"


@admin.register(StyleProfile)
class StyleProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'body_type', 'height', 'prefers_sustainable', 'created_at']
    list_filter = ['body_type', 'prefers_sustainable', 'prefers_secondhand']
    search_fields = ['user__email', 'user__username']
    raw_id_fields = ['user']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'


@admin.register(FashionIQ)
class FashionIQAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_level', 'total_xp', 'color_score', 'lessons_completed']
    list_filter = ['current_level']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['total_xp', 'lessons_completed']


@admin.register(StyleCritiqueSession)
class StyleCritiqueSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'concept_taught', 'is_accepted', 'is_helpful', 'created_at']
    list_filter = ['is_accepted', 'is_helpful', 'created_at']
    search_fields = ['user__email', 'critique_text', 'suggestion_text']
    raw_id_fields = ['user']
