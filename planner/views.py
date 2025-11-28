from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import calendar as cal
from .models import Event
from outfits.models import Outfit
from django.db.models import Count, Avg, Q
from wardrobe.models import ClothingItem
from .models import WearHistory  # AJOUTEZ CET IMPORT

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
        
        # AJOUT: Récupérer latitude et longitude
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        
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
            outfit_id=outfit_id if outfit_id else None,
            # AJOUT: Sauvegarder les coordonnées
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None
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
        
        # AJOUT: Mettre à jour latitude et longitude
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        event.latitude = float(latitude) if latitude else None
        event.longitude = float(longitude) if longitude else None
        
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
def get_coordinates_for_city(city_name):
    """Fallback coordinates for major cities - FOCUS ON TUNISIA"""
    city_coordinates = {
        # Villes Tunisiennes
        'tunis': (36.8065, 10.1815),
        'sousse': (35.8254, 10.6360),
        'sfax': (34.7406, 10.7603),
        'kairouan': (35.6781, 10.0963),
        'bizerte': (37.2747, 9.8739),
        'gabès': (33.8815, 10.0982),
        'ariana': (36.8601, 10.1934),
        'gafsa': (34.4250, 8.7842),
        'monastir': (35.7833, 10.8333),
        'kasserine': (35.1676, 8.8365),
        'ben arous': (36.7533, 10.2189),
        'medenine': (33.3549, 10.5055),
        'nabeul': (36.4561, 10.7376),
        'tataouine': (32.9297, 10.4518),
        'beja': (36.7256, 9.1817),
        'jendouba': (36.5012, 8.7804),
        'kef': (36.1822, 8.7148),
        'mahdia': (35.5047, 11.0622),
        'manouba': (36.8081, 10.0972),
        'sidibouzid': (35.0383, 9.4840),
        'siliana': (36.0847, 9.3708),
        'tozeur': (33.9197, 8.1334),
        'zaghouan': (36.4029, 10.1429),
        'kelibia': (36.8476, 11.0939),
        'hammamet': (36.4000, 10.6167),
        'djerba': (33.8750, 10.8575),
        'sidi bou said': (36.8687, 10.3416),
        'carthage': (36.8545, 10.3307),
        'la marsa': (36.8760, 10.3244),
        
        # Villes internationales (pour backup)
        'paris': (48.8566, 2.3522),
        'london': (51.5074, -0.1278),
        'new york': (40.7128, -74.0060),
    }
    
    city_lower = city_name.lower().strip()
    
    # Recherche exacte d'abord
    if city_lower in city_coordinates:
        return city_coordinates[city_lower]
    
    # Recherche partielle
    for city, coords in city_coordinates.items():
        if city in city_lower:
            return coords
    
    return None
import requests
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def geocode_location(request):
    """Geocode location name to coordinates - TUNISIA FOCUS"""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        location_name = request.GET.get('location', '')
        
        if not location_name:
            return JsonResponse({'success': False, 'error': 'Veuillez entrer un nom de lieu'})
        
        try:
            # Essayer d'abord avec les coordonnées prédéfinies pour la Tunisie
            fallback_coords = get_coordinates_for_city(location_name)
            if fallback_coords:
                return JsonResponse({
                    'success': True,
                    'latitude': fallback_coords[0],
                    'longitude': fallback_coords[1],
                    'display_name': f"{location_name.title()}, Tunisie",
                    'source': 'predefined'
                })
            
            # Sinon utiliser l'API Nominatim
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': f"{location_name}, Tunisie",
                'format': 'json',
                'limit': 1,
                'countrycodes': 'tn'  # Focus sur la Tunisie
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    result = data[0]
                    return JsonResponse({
                        'success': True,
                        'latitude': float(result['lat']),
                        'longitude': float(result['lon']),
                        'display_name': result['display_name'],
                        'source': 'api'
                    })
                else:
                    return JsonResponse({'success': False, 'error': 'Lieu non trouvé. Essayez avec un nom de ville tunisienne.'})
            else:
                return JsonResponse({'success': False, 'error': 'Erreur du service de géocodage'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Erreur: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Requête invalide'})
# AJOUTEZ CES VUES POUR L'HISTORIQUE DES VÊTEMENTS À LA FIN DU FICHIER :

@login_required
def add_wear_history_from_event(request, event_id):
    """Add wear history from an event with assigned outfit"""
    event = get_object_or_404(Event, id=event_id, user=request.user)
    
    if not event.outfit:
        messages.error(request, 'This event has no outfit assigned.')
        return redirect('planner:event_detail', event_id=event.id)
    
    if request.method == 'POST':
        # Check if wear history already exists for this event
        existing_entry = WearHistory.objects.filter(
            user=request.user,
            worn_date=event.date,  # Changé de wear_date à worn_date
            outfit=event.outfit
        ).first()
        
        if existing_entry:
            messages.info(request, 'Wear history already exists for this event.')
            return redirect('planner:wear_history_list')
        
        # Create wear history entry from event
        wear_entry = WearHistory.objects.create(
            user=request.user,
            worn_date=event.date,  # Changé de wear_date à worn_date
            outfit=event.outfit,
            notes=f"Worn for event: {event.title}" + (f" - {event.notes}" if event.notes else "")
        )
        
        # Add all clothing items from the outfit
        wear_entry.clothing_items.set(event.outfit.items.all())
        
        messages.success(request, f'Wear history added for {event.date}!')
        return redirect('planner:wear_history_list')
    
    # GET: Show confirmation page
    context = {
        'event': event,
    }
    return render(request, 'planner/add_wear_history_from_event.html', context)
@login_required
def wear_history_list(request):
    """
    View to display wear history for the current user
    """
    wear_history = WearHistory.objects.filter(user=request.user).order_by('-worn_date')  # Changé de wear_date à worn_date
    
    context = {
        'wear_history': wear_history,
    }
    return render(request, 'planner/wear_history_list.html', context)
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

def mark_worn_and_back(request, event_id):
    """
    Marque l'outfit comme porté et redirige vers la liste des événements
    """
    event = get_object_or_404(Event, id=event_id, user=request.user)
    
    if event.outfit and not event.is_completed:
        try:
            # Créer l'entrée dans l'historique des portés
            WearHistory.objects.create(
                user=request.user,
                outfit=event.outfit,
                event=event,
                worn_date=event.date
            )
            
            # Marquer l'événement comme complété
            event.is_completed = True
            event.save()
            
            messages.success(request, f"Outfit '{event.outfit.name}' marked as worn and event completed!")
        except Exception as e:
            messages.error(request, f"Error marking as worn: {str(e)}")
    else:
        if not event.outfit:
            messages.warning(request, "Cannot mark as worn - no outfit assigned to this event.")
        elif event.is_completed:
            messages.warning(request, "Event is already completed.")
    
    # Rediriger vers la liste des événements
    return HttpResponseRedirect(reverse('planner:event_list'))


def delete_wear_history(request, entry_id):
    """
    Supprime une entrée de l'historique des portés
    """
    entry = get_object_or_404(WearHistory, id=entry_id, user=request.user)
    
    if request.method == 'POST':
        entry.delete()
        messages.success(request, "Wear history entry deleted successfully!")
    
    return redirect('planner:wear_history_list')