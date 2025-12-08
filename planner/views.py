from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import calendar as cal
from .models import Event
from outfits.models import Outfit
<<<<<<< HEAD
=======
from .weather_service import WeatherService
>>>>>>> main


@login_required
def calendar_view(request):
<<<<<<< HEAD
    """Display calendar with events"""
=======
    """Display calendar with events and weather"""
>>>>>>> main
    # Get current month/year or from query params
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
<<<<<<< HEAD
=======
    # Get location from query params or session
    location = request.GET.get('location', request.session.get('weather_location', 'Tunis'))
    # Save location to session for persistence
    request.session['weather_location'] = location
    
>>>>>>> main
    # Get first and last day of month
    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Get events for the month
    events = Event.objects.filter(
        user=request.user,
        date__gte=first_day,
        date__lte=last_day
    ).select_related('outfit')
    
    # Create calendar data
    month_calendar = cal.monthcalendar(year, month)
    
    # Map events to dates
    events_by_date = {}
    for event in events:
        date_key = event.date.day
        if date_key not in events_by_date:
            events_by_date[date_key] = []
        events_by_date[date_key].append(event)
    
    # Navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
<<<<<<< HEAD
    # Upcoming events (next 7 days)
    upcoming_events = Event.objects.filter(
        user=request.user,
        date__gte=today,
        date__lte=today + timedelta(days=7)
    ).select_related('outfit').order_by('date', 'time')[:5]
    
=======
    # Upcoming events (next 5)
    upcoming_events = Event.objects.filter(
        user=request.user,
        date__gte=today
    ).select_related('outfit').order_by('date', 'time')[:5]
    
    # Get Weather Data
    weather_service = WeatherService()
    
    current_weather = weather_service.get_current_weather(location)
    forecast = weather_service.get_forecast(location)
    
>>>>>>> main
    context = {
        'year': year,
        'month': month,
        'month_name': cal.month_name[month],
        'month_calendar': month_calendar,
        'events_by_date': events_by_date,
        'today': today,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'upcoming_events': upcoming_events,
        'weekday_names': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
<<<<<<< HEAD
=======
        'current_weather': current_weather,
        'weather_forecast': forecast[:5] if forecast else [],  # Next 5 forecast items
        'weather_location': location,
>>>>>>> main
    }
    
    return render(request, 'planner/calendar.html', context)


@login_required
def event_list(request):
    """List all events with filtering"""
    events = Event.objects.filter(user=request.user).select_related('outfit')
    
    # Filtering
    occasion = request.GET.get('occasion', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    if occasion:
        events = events.filter(occasion_type=occasion)
    
    if status == 'upcoming':
        events = events.filter(date__gte=timezone.now().date(), is_completed=False)
    elif status == 'past':
        events = events.filter(date__lt=timezone.now().date())
    elif status == 'completed':
        events = events.filter(is_completed=True)
    elif status == 'no_outfit':
        events = events.filter(outfit__isnull=True, date__gte=timezone.now().date())
    
    if search:
        events = events.filter(
            Q(title__icontains=search) |
            Q(location__icontains=search) |
            Q(notes__icontains=search)
        )
    
    events = events.order_by('date', 'time')
    
    # Statistics for sidebar
    total_events = Event.objects.filter(user=request.user).count()
    upcoming_count = Event.objects.filter(
        user=request.user,
        date__gte=timezone.now().date(),
        is_completed=False
    ).count()
    no_outfit_count = Event.objects.filter(
        user=request.user,
        outfit__isnull=True,
        date__gte=timezone.now().date()
    ).count()
    
    context = {
        'events': events,
        'occasion_choices': Event.OCCASION_CHOICES,
        'selected_occasion': occasion,
        'selected_status': status,
        'search_query': search,
        'total_events': total_events,
        'upcoming_count': upcoming_count,
        'no_outfit_count': no_outfit_count,
    }
    
    return render(request, 'planner/event_list.html', context)


@login_required
def event_create(request):
    """Create a new event"""
    if request.method == 'POST':
        title = request.POST.get('title')
        date = request.POST.get('date')
        time = request.POST.get('time') or None
        occasion_type = request.POST.get('occasion_type')
        location = request.POST.get('location', '')
        notes = request.POST.get('notes', '')
        outfit_id = request.POST.get('outfit')
        
        if not title or not date:
            messages.error(request, 'Title and date are required.')
            return redirect('planner:event_create')
        
        # Create event
        event = Event.objects.create(
            user=request.user,
            title=title,
            date=date,
            time=time if time else None,
            occasion_type=occasion_type,
            location=location,
            notes=notes,
            outfit_id=outfit_id if outfit_id else None
        )
        
        messages.success(request, f'Event "{event.title}" created successfully!')
        return redirect('planner:event_detail', event_id=event.id)
    
    # GET: Show form
    outfits = Outfit.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'occasion_choices': Event.OCCASION_CHOICES,
        'outfits': outfits,
    }
    
    return render(request, 'planner/event_create.html', context)


@login_required
def event_detail(request, event_id):
    """View event details"""
    event = get_object_or_404(Event, id=event_id, user=request.user)
    
    # Suggest outfits based on occasion if no outfit assigned
    suggested_outfits = []
    if not event.outfit:
        suggested_outfits = Outfit.objects.filter(
            user=request.user,
            occasion=event.occasion_type
        ).order_by('-created_at')[:4]
    
    context = {
        'event': event,
        'suggested_outfits': suggested_outfits,
    }
    
    return render(request, 'planner/event_detail.html', context)


@login_required
def event_edit(request, event_id):
    """Edit an event"""
    event = get_object_or_404(Event, id=event_id, user=request.user)
    
    if request.method == 'POST':
        event.title = request.POST.get('title')
        event.date = request.POST.get('date')
        event.time = request.POST.get('time') or None
        event.occasion_type = request.POST.get('occasion_type')
        event.location = request.POST.get('location', '')
        event.notes = request.POST.get('notes', '')
        
        outfit_id = request.POST.get('outfit')
        event.outfit_id = outfit_id if outfit_id else None
        
        event.save()
        messages.success(request, 'Event updated successfully!')
        return redirect('planner:event_detail', event_id=event.id)
    
    # GET: Show form
    outfits = Outfit.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'event': event,
        'occasion_choices': Event.OCCASION_CHOICES,
        'outfits': outfits,
    }
    
    return render(request, 'planner/event_edit.html', context)


@login_required
def event_delete(request, event_id):
    """Delete an event"""
    event = get_object_or_404(Event, id=event_id, user=request.user)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" deleted successfully!')
        return redirect('planner:event_list')
    
    return redirect('planner:event_detail', event_id=event_id)


@login_required
def assign_outfit(request, event_id):
    """Assign outfit to an event"""
    event = get_object_or_404(Event, id=event_id, user=request.user)
    
    if request.method == 'POST':
        outfit_id = request.POST.get('outfit_id')
        if outfit_id:
            outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
            event.outfit = outfit
            event.save()
            messages.success(request, f'Outfit "{outfit.name}" assigned to event!')
        else:
            event.outfit = None
            event.save()
            messages.success(request, 'Outfit removed from event.')
        
        return redirect('planner:event_detail', event_id=event.id)
    
    return redirect('planner:event_detail', event_id=event_id)


@login_required
def toggle_complete(request, event_id):
    """Toggle event completion status"""
    event = get_object_or_404(Event, id=event_id, user=request.user)
    
    if request.method == 'POST':
        event.is_completed = not event.is_completed
        event.save()
        
        status = 'completed' if event.is_completed else 'reopened'
        messages.success(request, f'Event marked as {status}!')
        
        return redirect('planner:event_detail', event_id=event.id)
    
    return redirect('planner:event_detail', event_id=event_id)


@login_required
def event_stats(request):
    """Event statistics and analytics"""
    user_events = Event.objects.filter(user=request.user)
    
    # Basic stats
    total_events = user_events.count()
    upcoming_events = user_events.filter(
        date__gte=timezone.now().date(),
        is_completed=False
    ).count()
    completed_events = user_events.filter(is_completed=True).count()
    events_with_outfits = user_events.filter(outfit__isnull=False).count()
    
    # Events by occasion
    occasion_stats_raw = user_events.values('occasion_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Add display names to occasion stats
    occasion_choices_dict = dict(Event.OCCASION_CHOICES)
    occasion_stats = []
    for stat in occasion_stats_raw:
        stat['occasion_type_display'] = occasion_choices_dict.get(stat['occasion_type'], stat['occasion_type'])
        occasion_stats.append(stat)
    
    # Events by month (last 6 months)
    six_months_ago = timezone.now().date() - timedelta(days=180)
    recent_events = user_events.filter(date__gte=six_months_ago)
    
    monthly_stats = {}
    for event in recent_events:
        month_key = event.date.strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = 0
        monthly_stats[month_key] += 1
    
    # Most used outfits in events
    popular_outfits = Outfit.objects.filter(
        events__user=request.user
    ).annotate(
        event_count=Count('events')
    ).order_by('-event_count')[:5]
    
    # Upcoming events
    next_events = user_events.filter(
        date__gte=timezone.now().date()
    ).order_by('date', 'time')[:5]
    
    context = {
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'completed_events': completed_events,
        'events_with_outfits': events_with_outfits,
        'occasion_stats': occasion_stats,
        'monthly_stats': monthly_stats,
        'popular_outfits': popular_outfits,
        'next_events': next_events,
        'occasion_choices': dict(Event.OCCASION_CHOICES),
    }
    
    return render(request, 'planner/event_stats.html', context)
<<<<<<< HEAD
=======


# ==================== REST API Views ====================

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import OutfitPlanning, TravelPlan, WearHistory
from .serializers import (
    EventSerializer,
    OutfitPlanningSerializer,
    TravelPlanSerializer,
    WearHistorySerializer
)
from .weather_service import weather_service


class PlannerPagination(PageNumberPagination):
    """Custom pagination for planner items"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for calendar events
    
    Endpoints:
    - GET /api/planner/events/ - List events
    - POST /api/planner/events/ - Create event
    - GET /api/planner/events/{id}/ - Get event details
    - PUT /api/planner/events/{id}/ - Update event
    - DELETE /api/planner/events/{id}/ - Delete event
    
    Custom actions:
    - GET /api/planner/events/calendar/ - Calendar view
    - POST /api/planner/events/{id}/toggle_complete/ - Mark complete/incomplete
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EventSerializer
    pagination_class = PlannerPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['occasion_type', 'is_completed']
    search_fields = ['title', 'location', 'notes']
    ordering_fields = ['date', 'created_at']
    ordering = ['date', 'time']
    
    def get_queryset(self):
        """Users can only access their own events"""
        queryset = Event.objects.filter(user=self.request.user).select_related('outfit')
        
        # Additional filters
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """
        Get calendar view for a specific month
        GET /api/planner/events/calendar/?year=2025&month=11
        """
        today = timezone.now().date()
        year = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))
        
        # Get first and last day of month
        from datetime import datetime
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        # Get events for the month
        events = self.get_queryset().filter(
            date__gte=first_day,
            date__lte=last_day
        )
        
        serializer = self.get_serializer(events, many=True)
        
        return Response({
            'year': year,
            'month': month,
            'month_name': first_day.strftime('%B'),
            'events': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def toggle_complete(self, request, pk=None):
        """
        Toggle event completion status
        POST /api/planner/events/{id}/toggle_complete/
        """
        event = self.get_object()
        event.is_completed = not event.is_completed
        event.save(update_fields=['is_completed'])
        
        return Response({
            'status': 'success',
            'is_completed': event.is_completed,
            'message': f'Event marked as {"completed" if event.is_completed else "incomplete"}'
        })


class OutfitPlanningViewSet(viewsets.ModelViewSet):
    """
    ViewSet for outfit planning (scheduled outfits)
    
    Endpoints:
    - GET /api/planner/planning/ - List planned outfits
    - POST /api/planner/planning/ - Schedule outfit
    - GET /api/planner/planning/{id}/ - Get planning details
    - PUT /api/planner/planning/{id}/ - Update planning
    - DELETE /api/planner/planning/{id}/ - Delete planning
    
    Custom actions:
    - POST /api/planner/planning/{id}/mark_worn/ - Mark as worn
    - POST /api/planner/planning/{id}/check_weather/ - Check weather suitability
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OutfitPlanningSerializer
    pagination_class = PlannerPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['was_worn', 'weather_alert']
    ordering_fields = ['date', 'created_at']
    ordering = ['date']
    
    def get_queryset(self):
        """Users can only access their own planning"""
        queryset = OutfitPlanning.objects.filter(
            user=self.request.user
        ).select_related('outfit').prefetch_related('outfit__items')
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_worn(self, request, pk=None):
        """
        Mark outfit as worn
        POST /api/planner/planning/{id}/mark_worn/
        """
        planning = self.get_object()
        planning.was_worn = True
        planning.save(update_fields=['was_worn'])
        
        # Create wear history
        WearHistory.objects.create(
            user=request.user,
            outfit=planning.outfit,
            worn_date=planning.date,
            weather_condition=planning.weather_condition,
            temperature=planning.temperature
        )
        
        # Update outfit wear count
        if planning.outfit:
            planning.outfit.times_worn += 1
            planning.outfit.last_worn = planning.date
            planning.outfit.save(update_fields=['times_worn', 'last_worn'])
        
        return Response({
            'status': 'success',
            'message': 'Outfit marked as worn and added to history'
        })
    
    @action(detail=True, methods=['post'])
    def check_weather(self, request, pk=None):
        """
        Check if planned outfit is suitable for weather
        POST /api/planner/planning/{id}/check_weather/
        Body: {"location": "Paris,FR"} (optional, uses planning location)
        """
        planning = self.get_object()
        location = request.data.get('location', planning.location)
        
        if not location:
            return Response(
                {'error': 'Location is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get weather forecast for the date
        forecast = weather_service.get_forecast(city=location, days=7)
        
        if not forecast:
            return Response(
                {'error': 'Could not fetch weather data'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Find forecast for the planning date
        target_date = planning.date.isoformat()
        day_forecast = next((day for day in forecast if day['date'] == target_date), None)
        
        if not day_forecast:
            return Response({
                'warning': 'Forecast not available for this date'
            })
        
        # Check outfit suitability
        weather_data = {
            'temperature': day_forecast['temp_avg'],
            'condition': day_forecast['condition']
        }
        
        is_suitable, reason = weather_service.is_outfit_suitable(planning.outfit, weather_data)
        
        # Update planning with weather info
        planning.weather_condition = day_forecast['condition']
        planning.temperature = day_forecast['temp_avg']
        planning.weather_alert = not is_suitable
        planning.save(update_fields=['weather_condition', 'temperature', 'weather_alert'])
        
        return Response({
            'is_suitable': is_suitable,
            'reason': reason,
            'forecast': day_forecast
        })


class TravelPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for travel plans
    
    Endpoints:
    - GET /api/planner/travel/ - List travel plans
    - POST /api/planner/travel/ - Create travel plan
    - GET /api/planner/travel/{id}/ - Get plan details
    - PUT /api/planner/travel/{id}/ - Update plan
    - DELETE /api/planner/travel/{id}/ - Delete plan
    
    Custom actions:
    - POST /api/planner/travel/{id}/toggle_packing/ - Mark packing complete/incomplete
    - POST /api/planner/travel/{id}/suggest_outfits/ - Get outfit suggestions
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TravelPlanSerializer
    pagination_class = PlannerPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['packing_complete', 'trip_type']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']
    
    def get_queryset(self):
        """Users can only access their own travel plans"""
        return TravelPlan.objects.filter(
            user=self.request.user
        ).prefetch_related('outfits', 'additional_items')
    
    @action(detail=True, methods=['post'])
    def toggle_packing(self, request, pk=None):
        """
        Toggle packing complete status
        POST /api/planner/travel/{id}/toggle_packing/
        """
        travel_plan = self.get_object()
        travel_plan.packing_complete = not travel_plan.packing_complete
        travel_plan.save(update_fields=['packing_complete'])
        
        return Response({
            'status': 'success',
            'packing_complete': travel_plan.packing_complete,
            'message': f'Packing marked as {"complete" if travel_plan.packing_complete else "incomplete"}'
        })
    
    @action(detail=True, methods=['get'])
    def suggest_outfits(self, request, pk=None):
        """
        Get outfit suggestions based on trip details
        GET /api/planner/travel/{id}/suggest_outfits/
        """
        travel_plan = self.get_object()
        
        # Calculate number of outfits needed (1 per day + a few extra)
        outfits_needed = travel_plan.duration_days + 2
        
        # Get weather forecast if possible
        weather_forecast = None
        if travel_plan.destination:
            weather_forecast = weather_service.get_forecast(
                city=travel_plan.destination,
                days=min(travel_plan.duration_days, 7)
            )
        
        # Get suitable outfits from user's wardrobe
        from outfits.models import Outfit
        from outfits.serializers import OutfitSerializer
        
        suitable_outfits = Outfit.objects.filter(user=request.user)
        
        # Filter by trip type/occasion
        if travel_plan.trip_type:
            occasion_map = {
                'business': 'work',
                'vacation': 'casual',
                'adventure': 'sport'
            }
            occasion = occasion_map.get(travel_plan.trip_type, 'casual')
            suitable_outfits = suitable_outfits.filter(occasion=occasion)
        
        # Limit results
        suitable_outfits = suitable_outfits[:outfits_needed]
        
        serializer = OutfitSerializer(suitable_outfits, many=True)
        
        return Response({
            'trip_duration': travel_plan.duration_days,
            'outfits_needed': outfits_needed,
            'weather_forecast': weather_forecast,
            'suggested_outfits': serializer.data
        })


class WearHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for wear history tracking
    
    Endpoints:
    - GET /api/planner/history/ - List wear history
    - POST /api/planner/history/ - Create history entry
    - GET /api/planner/history/{id}/ - Get history details
    - PUT /api/planner/history/{id}/ - Update history
    - DELETE /api/planner/history/{id}/ - Delete history
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WearHistorySerializer
    pagination_class = PlannerPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['received_compliments']
    ordering_fields = ['worn_date', 'created_at', 'rating']
    ordering = ['-worn_date']
    
    def get_queryset(self):
        """Users can only access their own history"""
        queryset = WearHistory.objects.filter(
            user=self.request.user
        ).select_related('outfit').prefetch_related('clothing_items')
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(worn_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(worn_date__lte=date_to)
        
        return queryset


class WeatherViewSet(viewsets.ViewSet):
    """
    ViewSet for weather data
    
    Endpoints:
    - GET /api/planner/weather/current/ - Current weather
    - GET /api/planner/weather/forecast/ - Weather forecast
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Get current weather
        GET /api/planner/weather/current/?location=Paris,FR
        """
        location = request.query_params.get('location')
        
        if not location:
            return Response(
                {'error': 'location parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        weather_data = weather_service.get_current_weather(city=location)
        
        if not weather_data:
            return Response(
                {'error': 'Could not fetch weather data'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response(weather_data)
    
    @action(detail=False, methods=['get'])
    def forecast(self, request):
        """
        Get weather forecast
        GET /api/planner/weather/forecast/?location=Paris,FR&days=7
        """
        location = request.query_params.get('location')
        days = int(request.query_params.get('days', 7))
        
        if not location:
            return Response(
                {'error': 'location parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        forecast = weather_service.get_forecast(city=location, days=min(days, 7))
        
        if not forecast:
            return Response(
                {'error': 'Could not fetch weather data'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response({
            'location': location,
            'days': len(forecast),
            'forecast': forecast
        })

>>>>>>> main
