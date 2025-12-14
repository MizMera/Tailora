from django.db import models
from users.models import User
from wardrobe.models import ClothingItem
import uuid


class Outfit(models.Model):
    """
    Module 3: Outfit Creator - Complete outfit combinations
    Represents a full outfit created by user or AI
    """
    OCCASION_CHOICES = [
        ('casual', 'Décontracté'),
        ('work', 'Bureau'),
        ('formal', 'Formel'),
        ('sport', 'Sport'),
        ('evening', 'Soirée'),
        ('weekend', 'Week-end'),
        ('wedding', 'Mariage'),
        ('travel', 'Voyage'),
        ('date', 'Rendez-vous'),
        ('other', 'Autre'),
    ]
    
    SOURCE_CHOICES = [
        ('user', 'Créé par Utilisateur'),
        ('ai', 'Suggestion IA'),
        ('community', 'Inspiré Communauté'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outfits')
    
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Clothing items in the outfit
    items = models.ManyToManyField(ClothingItem, through='OutfitItem', related_name='outfits')
    
    # Occasion and style
    occasion = models.CharField(max_length=20, choices=OCCASION_CHOICES, default='casual')
    style_tags = models.JSONField(default=list, blank=True)  # e.g., ["chic", "coloré", "minimaliste"]
    
    # Source and rating
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='user')
    rating = models.IntegerField(null=True, blank=True)  # User's personal rating 1-5
    
    # Usage tracking
    times_worn = models.IntegerField(default=0)
    last_worn = models.DateField(null=True, blank=True)
    favorite = models.BooleanField(default=False)
    
    # Weather suitability
    min_temperature = models.IntegerField(null=True, blank=True)  # Celsius
    max_temperature = models.IntegerField(null=True, blank=True)  # Celsius
    suitable_weather = models.JSONField(default=list, blank=True)  # ["sunny", "rainy", "snowy"]
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Generated outfit image (composite)
    outfit_image = models.ImageField(upload_to='outfits/', blank=True, null=True)
    
    class Meta:
        db_table = 'outfits'
        ordering = ['-created_at']
        verbose_name = 'Tenue'
        verbose_name_plural = 'Tenues'
        indexes = [
            models.Index(fields=['user', 'occasion']),
            models.Index(fields=['user', 'favorite']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"


class OutfitItem(models.Model):
    """
    Through model for Outfit-ClothingItem relationship
    Allows storing position/layer information for visual composition
    """
    LAYER_CHOICES = [
        ('base', 'Base Layer'),
        ('mid', 'Mid Layer'),
        ('outer', 'Outer Layer'),
        ('accessory', 'Accessory'),
        ('shoes', 'Shoes'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, related_name='outfit_items')
    clothing_item = models.ForeignKey(ClothingItem, on_delete=models.CASCADE, related_name='outfit_memberships')
    
    # Visual composition data
    layer = models.CharField(max_length=20, choices=LAYER_CHOICES, default='base')
    position = models.IntegerField(default=0)  # Order in the outfit
    
    # Canvas position for Mix & Match interface
    x_position = models.FloatField(null=True, blank=True)
    y_position = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'outfit_items'
        ordering = ['position']
        unique_together = [['outfit', 'clothing_item']]
    
    def __str__(self):
        return f"{self.outfit.name} - {self.clothing_item.name}"


class StyleChallenge(models.Model):
    CHALLENGE_TYPES = [
        ('capsule', 'Capsule Wardrobe'),
        ('color', 'Color Theme'),
        ('item', 'Specific Item'),
        ('style', 'Style Exploration'),
        ('sustainability', 'Sustainability'),
        ('daily', 'Daily Style'),
        ('weekly', 'Weekly Theme'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPES, default='capsule')
    duration_days = models.IntegerField(default=7)
    rules = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_challenges')
    is_public = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='challenges/', blank=True, null=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def save(self, *args, **kwargs):
        from django.utils import timezone
        if not self.start_date:
            self.start_date = timezone.now().date()
        if not self.end_date and self.duration_days:
            self.end_date = self.start_date + timezone.timedelta(days=self.duration_days)
        super().save(*args, **kwargs)
    
    def is_active(self):
        from django.utils import timezone
        return self.start_date <= timezone.now().date() <= self.end_date
    
    def participants_count(self):
        return self.participations.filter(completed=False).count()
    
    def __str__(self):
        return self.name


class ChallengeParticipation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_participations')
    challenge = models.ForeignKey(StyleChallenge, on_delete=models.CASCADE, related_name='participations')
    joined_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    streak_days = models.IntegerField(default=0)
    last_activity = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'challenge']
    
    def progress_percentage(self):
        total_outfits = self.challenge.rules.get('required_outfits', self.challenge.duration_days)
        completed_outfits = self.outfits.count()
        return min(100, int((completed_outfits / total_outfits) * 100)) if total_outfits > 0 else 0
    
    def days_remaining(self):
        from django.utils import timezone
        if self.challenge.end_date:
            remaining = (self.challenge.end_date - timezone.now().date()).days
            return max(0, remaining)
        return 0
    
    def outfits_submitted(self):
        return self.outfits.count()
    
    def __str__(self):
        return f"{self.user.email} - {self.challenge.name}"


class ChallengeOutfit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participation = models.ForeignKey(ChallengeParticipation, on_delete=models.CASCADE, related_name='outfits')
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['participation', 'outfit']
    
    def __str__(self):
        return f"{self.participation} - {self.outfit.name}"


class UserBadge(models.Model):
    BADGE_TYPES = [
        ('challenge_complete', 'Challenge Complete'),
        ('streak', 'Streak Master'),
        ('variety', 'Style Explorer'),
        ('sustainability', 'Eco Warrior'),
        ('community', 'Community Star'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outfit_badges')
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    name = models.CharField(max_length=100)
    description = models.TextField()
    earned_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='badges/', blank=True, null=True)
    
    class Meta:
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
