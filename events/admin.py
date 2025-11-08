from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'start_time', 'end_time', 'location', 'organizer', 'capacity', 'price', 'dress_code')
    list_filter = ('date', 'dress_code')
    search_fields = ('name', 'location', 'organizer')
