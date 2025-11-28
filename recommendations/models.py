from django.db import models
from users.models import User
from outfits.models import Outfit
from wardrobe.models import ClothingItem
import uuid


class DailyRecommendation(models.Model):
    """
    AI-powered daily outfit recommendations
    Core of the recommendation engine
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('viewed', 'Viewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('worn', 'Worn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_recommendations')
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, related_name='recommendations')
    
    # Recommendation details
    recommendation_date = models.DateField()
    priority = models.IntegerField(default=0)  # For ordering multiple recommendations
    
    # AI reasoning
    reason = models.TextField(blank=True)  # Why this outfit was recommended
    confidence_score = models.FloatField(default=0.0)  # AI confidence 0-1
    
    # Context factors used
    weather_factor = models.JSONField(default=dict, blank=True)  # Weather data considered
    style_match_score = models.FloatField(default=0.0)  # Match with user's style profile
    occasion_match = models.CharField(max_length=50, blank=True)
    
    # User feedback
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user_rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    user_feedback = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_recommendations'
        ordering = ['recommendation_date', 'priority']
        unique_together = [['user', 'recommendation_date', 'outfit']]
        verbose_name = 'Daily Recommendation'
        verbose_name_plural = 'Daily Recommendations'
        indexes = [
            models.Index(fields=['user', 'recommendation_date']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Recommendation for {self.user.email} on {self.recommendation_date}"


class UserPreferenceSignal(models.Model):
    """
    Tracks user interactions for machine learning
    Used to improve recommendations over time
    """
    SIGNAL_TYPES = [
        ('outfit_created', 'Outfit Created'),
        ('outfit_liked', 'Outfit Liked'),
        ('outfit_worn', 'Outfit Worn'),
        ('outfit_rated', 'Outfit Rated'),
        ('item_favorited', 'Item Favorited'),
        ('recommendation_accepted', 'Recommendation Accepted'),
        ('recommendation_rejected', 'Recommendation Rejected'),
        ('post_liked', 'Post Liked'),
        ('style_updated', 'Style Updated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preference_signals')
    
    # Signal information
    signal_type = models.CharField(max_length=50, choices=SIGNAL_TYPES)
    signal_value = models.FloatField()  # Positive or negative weight
    
    # Related objects
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, null=True, blank=True, related_name='preference_signals')
    clothing_item = models.ForeignKey(ClothingItem, on_delete=models.CASCADE, null=True, blank=True, related_name='preference_signals')
    
    # Context
    context = models.JSONField(default=dict, blank=True)  # Additional context data
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_preference_signals'
        ordering = ['-created_at']
        verbose_name = 'Preference Signal'
        verbose_name_plural = 'Preference Signals'
        indexes = [
            models.Index(fields=['user', 'signal_type']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.signal_type} - {self.signal_value}"


class ColorCompatibility(models.Model):
    """
    Color theory rules for outfit matching
    Pre-populated with fashion color theory rules
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    color1 = models.CharField(max_length=50)
    color1_hex = models.CharField(max_length=7)
    color2 = models.CharField(max_length=50)
    color2_hex = models.CharField(max_length=7)
    
    compatibility_score = models.FloatField()  # 0-1, higher is better
    relationship_type = models.CharField(max_length=50)  # "complementary", "analogous", "triadic", etc.
    
    class Meta:
        db_table = 'color_compatibility'
        unique_together = [['color1', 'color2']]
        verbose_name = 'Color Compatibility'
        verbose_name_plural = 'Color Compatibilities'
    
    def __str__(self):
        return f"{self.color1} + {self.color2} = {self.compatibility_score}"


class StyleRule(models.Model):
    """
    Fashion rules and guidelines for outfit creation
    Used by AI to create appropriate combinations
    """
    RULE_CATEGORIES = [
        ('color', 'Color'),
        ('pattern', 'Pattern'),
        ('season', 'Season'),
        ('occasion', 'Occasion'),
        ('proportion', 'Proportion'),
        ('style_mix', 'Style Mix'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=50, choices=RULE_CATEGORIES)
    rule_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Rule logic (can be JSON for complex rules)
    conditions = models.JSONField(default=dict)
    recommendation = models.TextField()
    
    # Weight in decision making
    importance = models.FloatField(default=1.0)  # 0-1
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'style_rules'
        verbose_name = 'Style Rule'
        verbose_name_plural = 'Style Rules'
    
    def __str__(self):
        return f"{self.category} - {self.rule_name}"
