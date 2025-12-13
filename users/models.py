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
        ('user', 'Standard User'),
        ('premium', 'Premium User'),
        ('stylist', 'Stylist'),
        ('influencer', 'Influencer'),
        ('admin', 'Administrator'),
    ]
    
    # Account status choices
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('banned', 'Banned'),
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
    
    # Deletion
    deletion_code = models.CharField(max_length=6, blank=True, null=True)
    deletion_code_expires_at = models.DateTimeField(blank=True, null=True)
    
    # Password change verification
    password_change_code = models.CharField(max_length=6, blank=True, null=True)
    password_change_code_expires_at = models.DateTimeField(blank=True, null=True)
    pending_new_password = models.CharField(max_length=128, blank=True, null=True)  # Temporarily store hashed new password
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['status']),
            models.Index(fields=['is_verified']),
        ]
        
    def generate_deletion_code(self):
        """
        Generate a 6-digit deletion code and set an expiration time (15 minutes).
        """
        from django.utils import timezone
        import random
        self.deletion_code = str(random.randint(100000, 999999))
        self.deletion_code_expires_at = timezone.now() + timezone.timedelta(minutes=15)
        self.save()
    
    def generate_password_change_code(self, new_password_hash):
        """
        Generate a 6-digit password change verification code and set an expiration time (15 minutes).
        Also stores the pending new password hash temporarily.
        """
        from django.utils import timezone
        import random
        self.password_change_code = str(random.randint(100000, 999999))
        self.password_change_code_expires_at = timezone.now() + timezone.timedelta(minutes=15)
        self.pending_new_password = new_password_hash
        self.save()
    
    def clear_password_change_code(self):
        """
        Clear the password change verification code and pending password.
        """
        self.password_change_code = None
        self.password_change_code_expires_at = None
        self.pending_new_password = None
        self.save()
    
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
        ('boheme', 'Bohemian'),
        ('sportif', 'Sporty'),
        ('elegant', 'Elegant'),
        ('classique', 'Classic'),
        ('streetwear', 'Streetwear'),
        ('vintage', 'Vintage'),
        ('minimaliste', 'Minimalist'),
    ]
    
    BODY_TYPE_CHOICES = [
        ('rectangle', 'Rectangle'),
        ('triangle', 'Triangle'),
        ('triangle_inverse', 'Inverted Triangle'),
        ('sablier', 'Hourglass'),
        ('ovale', 'Oval'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='style_profile')
    
    # Style preferences
    favorite_colors = models.JSONField(default=list, blank=True)  # List of color hex codes
    preferred_styles = models.JSONField(default=list, blank=True)  # List of style choices
    favorite_colors = models.JSONField(default=list, blank=True)  # List of color hex codes
    preferred_styles = models.JSONField(default=list, blank=True)  # List of style choices
    favorite_brands = models.JSONField(default=list, blank=True)  # List of brand names
    
    # AI Analysis Data
    ai_palette = models.JSONField(default=list, blank=True)  # List of {name, hex} from AI extraction
    
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
    
    # Coaching preferences
    COACH_MODE_CHOICES = [
        ('gentle', 'Gentle Guide'),
        ('strict', 'Strict Stylist'),
        ('educational', 'Professor of Style'),
    ]
    coach_mode = models.CharField(max_length=20, choices=COACH_MODE_CHOICES, default='gentle')
    learning_focus = models.JSONField(default=list, blank=True)  # e.g. ["Color Theory", "Proportions"]
    
    # Notification preferences
    notification_preferences = models.JSONField(default=dict, blank=True)
    # Structure:
    # {
    #   "outfit_reminder": True,
    #   "reminder_time": "evening",  # "morning" | "evening" | "both"
    #   "email_notifications": True,
    #   "weekly_digest": False
    # }
    
    def get_notification_prefs(self):
        """Get notification preferences with defaults"""
        defaults = {
            'outfit_reminder': True,
            'reminder_time': 'evening',
            'email_notifications': True,
            'weekly_digest': False,
        }
        prefs = self.notification_preferences or {}
        return {**defaults, **prefs}
    
    class Meta:
        db_table = 'style_profiles'
        verbose_name = 'Style Profile'
        verbose_name_plural = 'Style Profiles'
    
    def __str__(self):
        return f"Style Profile - {self.user.email}"



class FashionIQ(models.Model):
    """
    Tracks the user's fashion competence and learning progress.
    Gamifies the style improvement process.
    """
    LEVEL_CHOICES = [
        ('novice', 'Fashion Novice'),
        ('intermediate', 'Style Enthusiast'),
        ('advanced', 'Taste Maker'),
        ('expert', 'Style Icon'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fashion_iq')
    
    current_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='novice')
    total_xp = models.IntegerField(default=0)
    
    # Skill Scores (0-100)
    color_score = models.IntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(100)])
    pattern_score = models.IntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(100)])
    silhouette_score = models.IntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(100)])
    versatility_score = models.IntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Learning Stats
    lessons_completed = models.IntegerField(default=0)
    strengths = models.JSONField(default=list, blank=True)
    areas_for_improvement = models.JSONField(default=list, blank=True)
    
    # Streak Tracking
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_good_outfit_date = models.DateField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fashion_iq'
        verbose_name = 'Fashion IQ'
        verbose_name_plural = 'Fashion IQs'

    def __str__(self):
        return f"{self.user.email} - {self.get_current_level_display()}"


class StyleCritiqueSession(models.Model):
    """
    A feedback session where the AI critiques an outfit or choice.
    Acts as a 'Lesson' for the user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='critique_sessions')
    
    # The subject of critique
    outfit_image = models.ImageField(upload_to='critiques/', blank=True, null=True)
    # We use string reference to avoid circular imports if outfits app imports User
    related_outfit = models.ForeignKey('outfits.Outfit', on_delete=models.SET_NULL, null=True, blank=True, related_name='critiques')
    
    # AI Feedback
    critique_text = models.TextField()  # "The red clashes with the pink..."
    suggestion_text = models.TextField()  # "Try a white shirt instead."
    
    # Educational Context
    concept_taught = models.CharField(max_length=100, blank=True)  # e.g. "Color Theory: Analogous Colors"
    xp_gained = models.IntegerField(default=0)
    
    # User Reaction
    is_accepted = models.BooleanField(default=False)  # Did they take the advice?
    is_helpful = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'style_critiques'
        ordering = ['-created_at']
        verbose_name = 'Style Critique'
        verbose_name_plural = 'Style Critiques'
    
    def __str__(self):
        return f"Critique for {self.user.email} - {self.concept_taught}"


class Notification(models.Model):
    """
    User notifications system
    """
    NOTIFICATION_TYPES = [
        ('outfit_ready', 'Outfit Ready'),
        ('weather_alert', 'Weather Alert'),
        ('social_like', 'Social Like'),
        ('social_comment', 'Social Comment'),
        ('challenge', 'Style Challenge'),
        ('recommendation', 'Recommendation'),
        ('system', 'System'),
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


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_related_models(sender, instance, created, **kwargs):
    """
    Ensure related models are created when a User is created.
    """
    if created:
        FashionIQ.objects.get_or_create(user=instance)
        StyleProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_related_models(sender, instance, **kwargs):
    """
    Ensure related models are saved when User is saved.
    """
    if hasattr(instance, 'fashion_iq'):
        instance.fashion_iq.save()
    if hasattr(instance, 'style_profile'):
        instance.style_profile.save()

