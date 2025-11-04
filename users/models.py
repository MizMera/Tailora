from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class User(AbstractUser):
    """
    Extended User model for Tailora application
    Module 1: User Management and Style Profile
    """
    
    # Role choices
    ROLE_CHOICES = [
        ('user', 'Utilisateur Standard'),
        ('premium', 'Utilisateur Premium'),
        ('stylist', 'Styliste'),
        ('influencer', 'Influenceur'),
        ('admin', 'Administrateur'),
    ]
    
    # Account status choices
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('suspended', 'Suspendu'),
        ('banned', 'Banni'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    # Role and Status
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Premium features
    premium_until = models.DateTimeField(null=True, blank=True)
    
    # Onboarding status
    onboarding_completed = models.BooleanField(default=False)
    
    # User statistics
    wardrobe_items_count = models.IntegerField(default=0)
    outfits_created_count = models.IntegerField(default=0)
    posts_count = models.IntegerField(default=0)
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    
    # Last activity
    last_active = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['status']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return self.email
    
    # Role checking methods
    def is_premium_user(self):
        """Check if user has premium access"""
        from django.utils import timezone
        return (
            self.role in ['premium', 'stylist', 'influencer', 'admin'] or
            (self.premium_until and self.premium_until > timezone.now())
        )
    
    def is_stylist(self):
        """Check if user is a stylist"""
        return self.role in ['stylist', 'admin']
    
    def is_influencer(self):
        """Check if user is an influencer"""
        return self.role in ['influencer', 'admin']
    
    def is_admin_user(self):
        """Check if user is an admin"""
        return self.role == 'admin' or self.is_superuser
    
    def can_create_unlimited_outfits(self):
        """Check if user can create unlimited outfits"""
        return self.is_premium_user()
    
    def can_access_ai_recommendations(self):
        """Check if user can access AI recommendations"""
        return self.is_premium_user()
    
    def can_upload_unlimited_items(self):
        """Check if user can upload unlimited wardrobe items"""
        return self.is_premium_user()
    
    def can_create_challenges(self):
        """Check if user can create style challenges"""
        return self.role in ['stylist', 'influencer', 'admin']
    
    def get_max_wardrobe_items(self):
        """Get maximum wardrobe items allowed"""
        if self.is_premium_user():
            return 1000  # Unlimited practically
        return 50  # Free tier limit
    
    def get_max_outfits(self):
        """Get maximum outfits allowed"""
        if self.is_premium_user():
            return 500
        return 20  # Free tier limit
    
    def get_role_display_badge(self):
        """Get display badge for user role"""
        badges = {
            'premium': '⭐ Premium',
            'stylist': '👔 Styliste',
            'influencer': '🌟 Influenceur',
            'admin': '🛡️ Admin',
        }
        return badges.get(self.role, '')
    
    def is_account_active(self):
        """Check if account is active and not suspended/banned"""
        return self.status == 'active' and self.is_active
    
    def increment_wardrobe_count(self):
        """Increment wardrobe items count"""
        self.wardrobe_items_count += 1
        self.save(update_fields=['wardrobe_items_count'])
    
    def increment_outfits_count(self):
        """Increment outfits created count"""
        self.outfits_created_count += 1
        self.save(update_fields=['outfits_created_count'])
    
    def increment_posts_count(self):
        """Increment posts count"""
        self.posts_count += 1
        self.save(update_fields=['posts_count'])


class StyleProfile(models.Model):
    """
    User's style preferences and profile
    Stores information about favorite colors, styles, brands, and body type
    """
    STYLE_CHOICES = [
        ('casual', 'Casual'),
        ('chic', 'Chic'),
        ('boheme', 'Bohème'),
        ('sportif', 'Sportif'),
        ('elegant', 'Élégant'),
        ('classique', 'Classique'),
        ('streetwear', 'Streetwear'),
        ('vintage', 'Vintage'),
        ('minimaliste', 'Minimaliste'),
    ]
    
    BODY_TYPE_CHOICES = [
        ('rectangle', 'Rectangle'),
        ('triangle', 'Triangle'),
        ('triangle_inverse', 'Triangle Inversé'),
        ('sablier', 'Sablier'),
        ('ovale', 'Ovale'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='style_profile')
    
    # Style preferences
    favorite_colors = models.JSONField(default=list, blank=True)  # List of color hex codes
    preferred_styles = models.JSONField(default=list, blank=True)  # List of style choices
    favorite_brands = models.JSONField(default=list, blank=True)  # List of brand names
    
    # Body information
    body_type = models.CharField(max_length=20, choices=BODY_TYPE_CHOICES, blank=True)
    height = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(100), MaxValueValidator(250)])  # in cm
    
    # Budget preferences
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Sustainability preferences
    prefers_sustainable = models.BooleanField(default=False)
    prefers_secondhand = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'style_profiles'
        verbose_name = 'Profil de Style'
        verbose_name_plural = 'Profils de Style'
    
    def __str__(self):
        return f"Style Profile - {self.user.email}"


class Notification(models.Model):
    """
    User notifications system
    """
    NOTIFICATION_TYPES = [
        ('outfit_ready', 'Tenue Prête'),
        ('weather_alert', 'Alerte Météo'),
        ('social_like', 'J\'aime Social'),
        ('social_comment', 'Commentaire Social'),
        ('challenge', 'Défi de Style'),
        ('recommendation', 'Recommandation'),
        ('system', 'Système'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional reference to related objects
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.UUIDField(blank=True, null=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
