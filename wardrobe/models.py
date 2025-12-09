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
        ('drying', 'En Séchage'),  # New: drying after wash
    ]
    
    CONDITION_CHOICES = [
        ('new', 'Neuf'),
        ('excellent', 'Excellent'),
        ('good', 'Bon'),
        ('fair', 'Correct'),
        ('worn', 'Usé'),
    ]
    
    CARE_TYPE_CHOICES = [
        ('machine_wash', 'Machine Washable'),
        ('hand_wash', 'Hand Wash'),
        ('dry_clean', 'Dry Clean Only'),
        ('spot_clean', 'Spot Clean'),
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
    
    # ==================== LAUNDRY TRACKING ====================
    wears_since_wash = models.IntegerField(default=0)  # Resets to 0 when washed
    last_washed = models.DateField(null=True, blank=True)
    max_wears_before_wash = models.IntegerField(default=3)  # User customizable
    care_type = models.CharField(max_length=20, choices=CARE_TYPE_CHOICES, default='machine_wash')
    drying_time_hours = models.IntegerField(default=24)  # Hours needed to dry after wash
    
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
    
    def needs_washing(self):
        """Check if item needs to be washed"""
        return self.wears_since_wash >= self.max_wears_before_wash
    
    def urgency_level(self):
        """
        Get laundry urgency level:
        0 = Clean, 1 = Approaching, 2 = Needs wash, 3 = Overdue
        """
        if self.wears_since_wash == 0:
            return 0
        ratio = self.wears_since_wash / max(self.max_wears_before_wash, 1)
        if ratio >= 1.5:
            return 3  # Overdue
        elif ratio >= 1.0:
            return 2  # Needs wash
        elif ratio >= 0.7:
            return 1  # Approaching
        return 0  # Clean
    
    def mark_worn(self):
        """Increment wear counter and update last worn date"""
        from django.utils import timezone
        self.times_worn += 1
        self.wears_since_wash += 1
        self.last_worn = timezone.now().date()
        self.save()
    
    def mark_washed(self):
        """Reset laundry counters after washing"""
        from django.utils import timezone
        self.wears_since_wash = 0
        self.last_washed = timezone.now().date()
        if self.status in ['washing', 'drying']:
            self.status = 'available'
        self.save()


class LaundryAlert(models.Model):
    """
    Proactive laundry notifications
    Created when items in planned outfits need washing
    """
    ALERT_TYPE_CHOICES = [
        ('needs_washing', 'Needs Washing'),
        ('drying_time', 'Needs Time to Dry'),
        ('at_cleaners', 'Still at Dry Cleaners'),
        ('approaching', 'Approaching Wash Limit'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='laundry_alerts')
    clothing_item = models.ForeignKey(ClothingItem, on_delete=models.CASCADE, related_name='laundry_alerts')
    
    # Planning context
    planned_date = models.DateField()  # When item is planned to be worn
    daily_slot = models.ForeignKey(
        'planner.DailyPlanSlot', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='laundry_alerts'
    )
    
    # Alert details
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    message = models.TextField()
    
    # Timing
    deadline = models.DateTimeField()  # By when laundry must be done
    
    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'laundry_alerts'
        ordering = ['deadline', '-priority']
        verbose_name = 'Laundry Alert'
        verbose_name_plural = 'Laundry Alerts'
        indexes = [
            models.Index(fields=['user', 'is_resolved']),
            models.Index(fields=['user', 'planned_date']),
        ]
    
    def __str__(self):
        return f"Laundry alert for {self.clothing_item.name} - {self.planned_date}"
    
    def resolve(self):
        """Mark alert as resolved"""
        from django.utils import timezone
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()

