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
