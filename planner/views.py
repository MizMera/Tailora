from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import calendar as cal
from .models import Event
from outfits.models import Outfit


@login_required
def calendar_view(request):
    """Display calendar with events"""
    # Get current month/year or from query params
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
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
    
    # Upcoming events (next 7 days)
    upcoming_events = Event.objects.filter(
        user=request.user,
        date__gte=today,
        date__lte=today + timedelta(days=7)
    ).select_related('outfit').order_by('date', 'time')[:5]
    
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
