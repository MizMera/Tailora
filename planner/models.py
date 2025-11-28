from django.db import models
from users.models import User
from outfits.models import Outfit
from wardrobe.models import ClothingItem
import uuid


class Event(models.Model):
    """
    Simple event/occasion model for calendar planning
    """
    OCCASION_CHOICES = [
        ('work', 'Work/Professional'),
        ('casual', 'Casual Outing'),
        ('formal', 'Formal Event'),
        ('party', 'Party/Celebration'),
        ('date', 'Date/Romance'),
        ('sports', 'Sports/Fitness'),
        ('travel', 'Travel'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    
    # Basic information
    title = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    occasion_type = models.CharField(max_length=50, choices=OCCASION_CHOICES, default='casual')
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    # Outfit planning
    outfit = models.ForeignKey(Outfit, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    
    # Status
    is_completed = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'events'
        ordering = ['date', 'time']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.date}"


class OutfitPlanning(models.Model):
    """
    Module 4: Style Planner & Calendar
    Assigns outfits to specific dates
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outfit_plannings')
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, related_name='plannings')
    
    # Date and event information
    date = models.DateField()
    event_name = models.CharField(max_length=200, blank=True)
    event_description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Weather information (fetched from API)
    weather_condition = models.CharField(max_length=50, blank=True)  # "sunny", "rainy", etc.
    temperature = models.IntegerField(null=True, blank=True)  # Celsius
    weather_alert = models.BooleanField(default=False)  # If outfit not suitable for weather
    
    # Notes and reminders
    notes = models.TextField(blank=True)
    reminder_sent = models.BooleanField(default=False)
    
    # Status
    was_worn = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'outfit_plannings'
        ordering = ['date']
        unique_together = [['user', 'date']]
        verbose_name = 'Planification de Tenue'
        verbose_name_plural = 'Planifications de Tenues'
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.outfit.name}"


class TravelPlan(models.Model):
    """
    Travel planning and packing assistant
    Helps users plan outfits for trips
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_plans')
    
    # Trip information
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    trip_type = models.CharField(max_length=50, blank=True)  # "business", "vacation", "adventure"
    
    # Climate and activities
    expected_weather = models.JSONField(default=dict, blank=True)  # Weather forecast data
    planned_activities = models.JSONField(default=list, blank=True)  # List of activities
    
    # Packing list
    outfits = models.ManyToManyField(Outfit, related_name='travel_plans', blank=True)
    additional_items = models.ManyToManyField(ClothingItem, related_name='travel_plans', blank=True)
    
    # Status
    packing_complete = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'travel_plans'
        ordering = ['-start_date']
        verbose_name = 'Plan de Voyage'
        verbose_name_plural = 'Plans de Voyage'
    
    def __str__(self):
        return f"{self.destination} - {self.start_date} to {self.end_date}"
    
    @property
    def duration_days(self):
        """Calculate trip duration in days"""
        return (self.end_date - self.start_date).days + 1


class WearHistory(models.Model):
    """
    Historical record of what was worn when
    Helps avoid repetition and track actual usage
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wear_history')
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, related_name='wear_history', null=True, blank=True)
    clothing_items = models.ManyToManyField(ClothingItem, related_name='wear_history')
    
    # When it was worn
    worn_date = models.DateField()
    
    # Optional feedback
    rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    comfort_rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    received_compliments = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    # Weather that day
    weather_condition = models.CharField(max_length=50, blank=True)
    temperature = models.IntegerField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'wear_history'
        ordering = ['-worn_date']
        verbose_name = 'Historique de Port'
        verbose_name_plural = 'Historiques de Port'
        indexes = [
            models.Index(fields=['user', 'worn_date']),
        ]
    
    def __str__(self):
        outfit_name = self.outfit.name if self.outfit else "Custom combination"
        return f"{self.user.email} - {self.worn_date} - {outfit_name}"
