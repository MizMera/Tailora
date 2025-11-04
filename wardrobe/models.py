from django.db import models
from users.models import User
import uuid


class ClothingCategory(models.Model):
    """
    Categories for clothing items
    Can be predefined or user-created
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    parent_category = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    is_custom = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='custom_categories')
    icon = models.CharField(max_length=50, blank=True)  # Icon name or emoji
    
    class Meta:
        db_table = 'clothing_categories'
        verbose_name = 'Catégorie de Vêtement'
        verbose_name_plural = 'Catégories de Vêtements'
        unique_together = [['name', 'user']]
    
    def __str__(self):
        return self.name


class ClothingItem(models.Model):
    """
    Module 2: Virtual Wardrobe - Individual clothing items
    Main model for managing user's wardrobe
    """
    SEASON_CHOICES = [
        ('spring', 'Printemps'),
        ('summer', 'Été'),
        ('fall', 'Automne'),
        ('winter', 'Hiver'),
        ('all_seasons', 'Toutes Saisons'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('washing', 'Au Lavage'),
        ('dry_cleaning', 'Au Pressing'),
        ('loaned', 'Prêté'),
        ('repair', 'En Réparation'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'Neuf'),
        ('excellent', 'Excellent'),
        ('good', 'Bon'),
        ('fair', 'Correct'),
        ('worn', 'Usé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wardrobe_items')
    
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ClothingCategory, on_delete=models.SET_NULL, null=True, related_name='items')
    
    # Visual information
    image = models.ImageField(upload_to='wardrobe/')
    color = models.CharField(max_length=50)  # Main color
    color_hex = models.CharField(max_length=7, blank=True)  # Hex code for primary color
    pattern = models.CharField(max_length=50, blank=True)  # e.g., "rayé", "uni", "fleuri"
    
    # Material and brand
    material = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    
    # Season and occasion
    seasons = models.JSONField(default=list)  # List of applicable seasons
    occasions = models.JSONField(default=list)  # e.g., ["casual", "formal", "sport"]
    
    # Purchase information
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purchase_location = models.CharField(max_length=200, blank=True)
    is_secondhand = models.BooleanField(default=False)
    
    # Status and condition
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    
    # Usage tracking
    times_worn = models.IntegerField(default=0)
    last_worn = models.DateField(null=True, blank=True)
    favorite = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tags for better search
    tags = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'clothing_items'
        ordering = ['-created_at']
        verbose_name = 'Vêtement'
        verbose_name_plural = 'Vêtements'
        indexes = [
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'favorite']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"
    
    def is_available(self):
        """Check if item is available to wear"""
        return self.status == 'available'
