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


class WeeklyPlan(models.Model):
    """
    AI-generated weekly outfit plan
    Stores a full week's worth of outfit recommendations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_plans')
    
    # Week information
    week_start = models.DateField()  # Monday of the planned week
    
    # AI generation context
    generated_at = models.DateTimeField(auto_now_add=True)
    weather_data = models.JSONField(default=dict, blank=True)  # 7-day forecast snapshot
    events_considered = models.JSONField(default=list, blank=True)  # Events during this week
    generation_reasoning = models.TextField(blank=True)  # Why these outfits were chosen
    location = models.CharField(max_length=100, default='Tunis')  # Weather location
    
    # User feedback for ML improvement
    overall_rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    feedback = models.TextField(blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        db_table = 'weekly_plans'
        ordering = ['-week_start']
        unique_together = [['user', 'week_start']]
        verbose_name = 'Weekly Plan'
        verbose_name_plural = 'Weekly Plans'
        indexes = [
            models.Index(fields=['user', 'week_start']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Week of {self.week_start} for {self.user.email}"
    
    @property
    def week_end(self):
        """Get the Sunday of this week"""
        from datetime import timedelta
        return self.week_start + timedelta(days=6)
    
    @property
    def is_current_week(self):
        """Check if this plan is for the current week"""
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        # Get Monday of current week
        current_monday = today - timedelta(days=today.weekday())
        return self.week_start == current_monday


class DailyPlanSlot(models.Model):
    """
    Individual day slot within a weekly plan
    Contains the recommended outfit for a specific day
    """
    STATUS_CHOICES = [
        ('suggested', 'AI Suggested'),
        ('accepted', 'User Accepted'),
        ('modified', 'User Modified'),
        ('skipped', 'Skipped'),
        ('worn', 'Worn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    weekly_plan = models.ForeignKey(WeeklyPlan, on_delete=models.CASCADE, related_name='daily_slots')
    
    # Day information
    date = models.DateField()
    day_of_week = models.IntegerField()  # 0=Monday, 6=Sunday
    
    # Primary outfit recommendation
    primary_outfit = models.ForeignKey(
        Outfit, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='primary_daily_slots'
    )
    
    # Alternative outfit options
    alternatives = models.ManyToManyField(
        Outfit, 
        blank=True, 
        related_name='alternative_daily_slots'
    )
    
    # For AI suggestions before outfit creation (stores item IDs)
    suggested_items = models.JSONField(default=list, blank=True)  # List of clothing item IDs
    suggested_name = models.CharField(max_length=200, blank=True)  # Suggested outfit name
    
    # Weather context for this day
    weather_condition = models.CharField(max_length=50, blank=True)  # sunny, rainy, cloudy
    temperature = models.IntegerField(null=True, blank=True)  # Celsius
    humidity = models.IntegerField(null=True, blank=True)  # Percentage
    weather_icon = models.CharField(max_length=20, blank=True)  # Icon code
    
    # Events for this day
    events = models.ManyToManyField(Event, blank=True, related_name='daily_plan_slots')
    
    # AI reasoning
    selection_reason = models.TextField(blank=True)  # Why this outfit was chosen
    confidence = models.FloatField(default=0.5)  # AI confidence 0-1
    
    # Scoring breakdown
    weather_score = models.FloatField(default=0.0)
    occasion_score = models.FloatField(default=0.0)
    recency_score = models.FloatField(default=0.0)
    style_score = models.FloatField(default=0.0)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='suggested')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_plan_slots'
        ordering = ['date']
        unique_together = [['weekly_plan', 'date']]
        verbose_name = 'Daily Plan Slot'
        verbose_name_plural = 'Daily Plan Slots'
        indexes = [
            models.Index(fields=['weekly_plan', 'date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][self.day_of_week]
        outfit_name = self.primary_outfit.name if self.primary_outfit else self.suggested_name or 'No outfit'
        return f"{day_name} ({self.date}) - {outfit_name}"
    
    @property
    def day_name(self):
        """Get the name of the day"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[self.day_of_week] if 0 <= self.day_of_week <= 6 else 'Unknown'
    
    @property
    def has_events(self):
        """Check if this day has any events"""
        return self.events.exists()
    
    @property
    def is_today(self):
        """Check if this slot is for today"""
        from django.utils import timezone
        return self.date == timezone.now().date()
    
    @property
    def is_past(self):
        """Check if this day has passed"""
        from django.utils import timezone
        return self.date < timezone.now().date()
