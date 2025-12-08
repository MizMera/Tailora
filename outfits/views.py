from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Max
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Outfit, OutfitItem, StyleChallenge, ChallengeParticipation, ChallengeOutfit, UserBadge
from wardrobe.models import ClothingItem
import uuid


@login_required
def outfit_gallery_view(request):
    """
    Display all user's outfits with filtering options
    """
    user = request.user
    outfits = Outfit.objects.filter(user=user).prefetch_related('items')
    
    # Apply filters
    occasion_filter = request.GET.get('occasion')
    search_query = request.GET.get('search', '').strip()
    show_favorites = request.GET.get('favorites') == 'true'
    
    if occasion_filter:
        outfits = outfits.filter(occasion=occasion_filter)
    
    if show_favorites:
        outfits = outfits.filter(favorite=True)
    
    if search_query:
        # Fixed search logic for SQLite compatibility
        outfits = outfits.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        # Remove style_tags from search since SQLite doesn't support JSONField contains
    
    # Pagination
    paginator = Paginator(outfits, 12)  # 12 outfits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get stats
    total_outfits = outfits.count()
    favorite_count = outfits.filter(favorite=True).count()

    # Daily challenge highlight (show latest active daily challenge)
    daily_challenge = (
        StyleChallenge.objects.filter(
            challenge_type='daily',
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date(),
            is_public=True,
        )
        .order_by('-start_date')
        .first()
    )
    daily_participation = None
    if daily_challenge:
        daily_participation = ChallengeParticipation.objects.filter(
            user=user, challenge=daily_challenge
        ).first()
    
    context = {
        'outfits': page_obj,
        'total_outfits': total_outfits,
        'favorite_count': favorite_count,
        'selected_occasion': occasion_filter,
        'search_query': search_query,
        'show_favorites': show_favorites,
        'occasions': Outfit.OCCASION_CHOICES,
        'daily_challenge': daily_challenge,
        'daily_participation': daily_participation,
    }
    
    return render(request, 'outfit_gallery.html', context)


@login_required
def outfit_create_view(request):
    """
    Create a new outfit by selecting wardrobe items
    """
    user = request.user
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        occasion = request.POST.get('occasion', 'casual')
        item_ids = request.POST.getlist('items')  # List of clothing item IDs
        
        # Validation
        if not name:
            messages.error(request, 'Outfit name is required.')
            return redirect('outfits:outfit_create')
        
        if not item_ids or len(item_ids) < 2:
            messages.error(request, 'Please select at least 2 items to create an outfit.')
            return redirect('outfits:outfit_create')
        
        # Create outfit
        try:
            outfit = Outfit.objects.create(
                user=user,
                name=name,
                description=description,
                occasion=occasion,
                source='user'
            )
            
            # Add items to outfit
            for idx, item_id in enumerate(item_ids):
                try:
                    clothing_item = ClothingItem.objects.get(id=item_id, user=user)
                    OutfitItem.objects.create(
                        outfit=outfit,
                        clothing_item=clothing_item,
                        position=idx
                    )
                except ClothingItem.DoesNotExist:
                    pass
            
            messages.success(request, f'{name} has been created successfully!')
            return redirect('outfits:outfit_detail', outfit_id=outfit.id)
        
        except Exception as e:
            messages.error(request, f'Error creating outfit: {str(e)}')
            return redirect('outfits:outfit_create')
    
    # GET request - show wardrobe items to select from
    wardrobe_items = ClothingItem.objects.filter(user=user, status='available')
    
    # Group by category for easier selection (include uncategorized)
    items_by_category = {}
    for item in wardrobe_items:
        cat_name = item.category.name if item.category else 'Uncategorized'
        if cat_name not in items_by_category:
            items_by_category[cat_name] = []
        items_by_category[cat_name].append(item)
    
    context = {
        'items_by_category': items_by_category,
        'occasions': Outfit.OCCASION_CHOICES,
    }
    
    return render(request, 'outfit_create.html', context)


@login_required
def outfit_detail_view(request, outfit_id):
    """
    Display single outfit details
    """
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    outfit_items = outfit.outfit_items.select_related('clothing_item').order_by('position')
    
    context = {
        'outfit': outfit,
        'outfit_items': outfit_items,
    }
    
    return render(request, 'outfit_detail.html', context)


@login_required
def outfit_edit_view(request, outfit_id):
    """
    Edit existing outfit
    """
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    
    if request.method == 'POST':
        # Update fields
        outfit.name = request.POST.get('name', outfit.name)
        outfit.description = request.POST.get('description', outfit.description)
        outfit.occasion = request.POST.get('occasion', outfit.occasion)
        outfit.favorite = request.POST.get('favorite') == 'on'
        
        # Update items if changed
        item_ids = request.POST.getlist('items')
        if item_ids:
            # Remove old items
            outfit.outfit_items.all().delete()
            
            # Add new items
            for idx, item_id in enumerate(item_ids):
                try:
                    clothing_item = ClothingItem.objects.get(id=item_id, user=request.user)
                    OutfitItem.objects.create(
                        outfit=outfit,
                        clothing_item=clothing_item,
                        position=idx
                    )
                except ClothingItem.DoesNotExist:
                    pass
        
        outfit.save()
        messages.success(request, f'{outfit.name} has been updated!')
        return redirect('outfits:outfit_detail', outfit_id=outfit.id)
    
    # GET request
    current_items = outfit.items.all()
    wardrobe_items = ClothingItem.objects.filter(user=request.user, status='available')
    
    # Group by category (include uncategorized)
    items_by_category = {}
    for item in wardrobe_items:
        cat_name = item.category.name if item.category else 'Uncategorized'
        if cat_name not in items_by_category:
            items_by_category[cat_name] = []
        items_by_category[cat_name].append(item)
    
    context = {
        'outfit': outfit,
        'current_items': current_items,
        'items_by_category': items_by_category,
        'occasions': Outfit.OCCASION_CHOICES,
    }
    
    return render(request, 'outfit_edit.html', context)


@login_required
def outfit_delete_view(request, outfit_id):
    """
    Delete an outfit
    """
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    
    if request.method == 'POST':
        outfit_name = outfit.name
        outfit.delete()
        messages.success(request, f'{outfit_name} has been deleted.')
        return redirect('outfits:outfit_gallery')
    
    return redirect('outfits:outfit_detail', outfit_id=outfit.id)


@login_required
def outfit_toggle_favorite_view(request, outfit_id):
    """
    Toggle favorite status of an outfit
    """
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    outfit.favorite = not outfit.favorite
    outfit.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'outfits:outfit_gallery'))


@login_required
def outfit_wear_view(request, outfit_id):
    """
    Mark an outfit as worn
    """
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    
    # Mark the outfit as worn
    outfit.mark_as_worn()
    
    messages.success(request, f'You wore "{outfit.name}" today!')
    
    return redirect(request.META.get('HTTP_REFERER', 'outfits:outfit_gallery'))


@login_required
def outfit_stats_view(request):
    """
    Display outfit statistics and insights
    """
    user = request.user
    outfits = Outfit.objects.filter(user=user).prefetch_related('items')
    
    # Calculate statistics
    stats = {
        'total_outfits': outfits.count(),
        'by_occasion': {},
        'favorite_count': outfits.filter(favorite=True).count(),
        'most_worn': [],
        'recent_outfits': [],
    }
    
    # Group by occasion
    occasion_counts = outfits.values('occasion').annotate(count=Count('id'))
    for item in occasion_counts:
        occasion_name = dict(Outfit.OCCASION_CHOICES).get(item['occasion'], item['occasion'])
        stats['by_occasion'][occasion_name] = item['count']
    
    # Most worn outfits - use complete objects with prefetched items
    stats['most_worn'] = outfits.filter(times_worn__gt=0).order_by('-times_worn')[:5]
    
    # Recent outfits - use complete objects with prefetched items
    stats['recent_outfits'] = outfits.order_by('-created_at')[:5]
    
    # Calculate additional stats for the template
    total_items = 0
    total_wears = 0
    
    for outfit in outfits:
        total_items += outfit.items.count()
        total_wears += outfit.times_worn
    
    stats['total_wears'] = total_wears
    stats['avg_items_per_outfit'] = total_items / stats['total_outfits'] if stats['total_outfits'] > 0 else 0
    stats['favorite_outfits'] = stats['favorite_count']
    
    context = {
        'stats': stats,
    }
    
    return render(request, 'outfit_stats.html', context)


@login_required
def advanced_search_view(request):
    """
    Advanced outfit search with multiple filtering options
    """
    user = request.user
    outfits = Outfit.objects.filter(user=user).prefetch_related('items')
    
    # Get all filter parameters with proper handling
    contains_ids = request.GET.get('contains', '')
    excludes_ids = request.GET.get('excludes', '')
    color_palette = request.GET.get('colors', '')
    item_categories = request.GET.getlist('categories')
    last_worn_filter = request.GET.get('last_worn', '')
    wear_count_filter = request.GET.get('wear_count', '')
    min_rating = request.GET.get('min_rating')
    occasion_filter = request.GET.get('occasion', '')
    favorite_only = request.GET.get('favorites') == 'true'
    
    # Apply filters with proper UUID handling
    if contains_ids:
        try:
            # Filter out empty strings and validate UUIDs
            contains_uuid_list = []
            for item_id in contains_ids.split(','):
                if item_id.strip():  # Only process non-empty strings
                    try:
                        contains_uuid_list.append(uuid.UUID(item_id.strip()))
                    except ValueError:
                        # Skip invalid UUIDs
                        continue
            
            if contains_uuid_list:
                # Outfits that contain ALL of the specified items
                for item_id in contains_uuid_list:
                    outfits = outfits.filter(items__id=item_id)
        except (ValueError, AttributeError):
            # If there's any error in processing, ignore this filter
            pass
    
    if excludes_ids:
        try:
            # Filter out empty strings and validate UUIDs
            excludes_uuid_list = []
            for item_id in excludes_ids.split(','):
                if item_id.strip():  # Only process non-empty strings
                    try:
                        excludes_uuid_list.append(uuid.UUID(item_id.strip()))
                    except ValueError:
                        # Skip invalid UUIDs
                        continue
            
            if excludes_uuid_list:
                # Outfits that don't contain ANY of the excluded items
                for item_id in excludes_uuid_list:
                    outfits = outfits.exclude(items__id=item_id)
        except (ValueError, AttributeError):
            # If there's any error in processing, ignore this filter
            pass
    
    if color_palette:
        colors = color_palette.split(',')
        # This is a simplified approach - for production you might want a better color matching
        for color in colors:
            outfits = outfits.filter(items__color__icontains=color)
    
    if item_categories:
        outfits = outfits.filter(items__category__name__in=item_categories)
    
    if last_worn_filter:
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        
        if last_worn_filter == 'today':
            outfits = outfits.filter(last_worn=today)
        elif last_worn_filter == 'week':
            week_ago = today - timedelta(days=7)
            outfits = outfits.filter(last_worn__gte=week_ago)
        elif last_worn_filter == 'month':
            month_ago = today - timedelta(days=30)
            outfits = outfits.filter(last_worn__gte=month_ago)
        elif last_worn_filter == 'never':
            outfits = outfits.filter(last_worn__isnull=True)
        elif last_worn_filter == 'long_ago':
            month_ago = today - timedelta(days=30)
            outfits = outfits.filter(last_worn__lt=month_ago)
    
    if wear_count_filter:
        if wear_count_filter == 'most_worn':
            outfits = outfits.filter(times_worn__gt=0).order_by('-times_worn')
        elif wear_count_filter == 'least_worn':
            outfits = outfits.order_by('times_worn')
        elif wear_count_filter == 'never_worn':
            outfits = outfits.filter(times_worn=0)
    
    if min_rating:
        outfits = outfits.filter(rating__gte=int(min_rating))
    
    if occasion_filter:
        outfits = outfits.filter(occasion=occasion_filter)
    
    if favorite_only:
        outfits = outfits.filter(favorite=True)
    
    # Remove duplicates from multiple filters
    outfits = outfits.distinct()
    
    # Get available filter options for the template
    wardrobe_items = ClothingItem.objects.filter(user=user, status='available')
    available_categories = set()
    available_colors = set()
    
    for item in wardrobe_items:
        if item.category:
            available_categories.add(item.category.name)
        if item.color:
            available_colors.add(item.color)
    
    # Last worn choices for template
    last_worn_choices = [
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('never', 'Never Worn'),
        ('long_ago', 'Long Ago')
    ]
    
    # Prepare filter parameters for template (handle empty values)
    filter_params = {
        'contains': contains_ids.split(',') if contains_ids else [],
        'excludes': excludes_ids.split(',') if excludes_ids else [],
        'colors': color_palette,
        'categories': item_categories,
        'last_worn': last_worn_filter,
        'wear_count': wear_count_filter,
        'min_rating': min_rating,
        'occasion': occasion_filter,
        'favorites': favorite_only,
    }
    
    # Pagination
    paginator = Paginator(outfits, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'outfits': page_obj,
        'wardrobe_items': wardrobe_items,
        'available_categories': sorted(available_categories),
        'available_colors': sorted(available_colors),
        'occasions': Outfit.OCCASION_CHOICES,
        'last_worn_choices': last_worn_choices,
        'filter_params': filter_params
    }
    
    return render(request, 'outfit_advanced_search.html', context)


# Challenge Views
@login_required
def challenges_list_view(request):
    """
    List all available challenges
    """
    user = request.user
    all_challenges = StyleChallenge.objects.filter(
        Q(is_public=True) | Q(created_by=user)
    ).prefetch_related('participations')
    
    # Get user's participations
    user_participations = {
        p.challenge_id: p for p in ChallengeParticipation.objects.filter(user=user)
    }
    
    # Separate challenges into categories
    active_challenges = []
    available_challenges = []
    completed_challenges = []
    
    for challenge in all_challenges:
        participation = user_participations.get(challenge.id)
        
        if participation:
            if participation.completed:
                completed_challenges.append((challenge, participation))
            else:
                active_challenges.append((challenge, participation))
        else:
            available_challenges.append(challenge)
    
    context = {
        'active_challenges': active_challenges,
        'available_challenges': available_challenges,
        'completed_challenges': completed_challenges,
    }
    
    return render(request, 'challenges_list.html', context)


@login_required
def challenge_detail_view(request, challenge_id):
    """
    View challenge details and participate
    """
    from django.utils import timezone
    
    challenge = get_object_or_404(StyleChallenge, id=challenge_id)
    user = request.user
    
    # Check if user is participating
    participation = ChallengeParticipation.objects.filter(
        user=user, challenge=challenge
    ).first()
    
    # Get submitted outfits for this challenge
    submitted_outfits = []
    if participation:
        submitted_outfits = ChallengeOutfit.objects.filter(
            participation=participation
        ).select_related('outfit')
    
    # Check if user can join
    can_join = not participation and challenge.is_active()
    
    # Check if challenge is locked (passed)
    is_locked = not participation and challenge.end_date and timezone.now().date() > challenge.end_date
    
    context = {
        'challenge': challenge,
        'participation': participation,
        'submitted_outfits': submitted_outfits,
        'can_join': can_join,
        'is_locked': is_locked,
        'progress': participation.progress_percentage() if participation else 0,
    }
    
    return render(request, 'challenge_detail.html', context)


@login_required
def join_challenge_view(request, challenge_id):
    """
    Join a style challenge
    """
    challenge = get_object_or_404(StyleChallenge, id=challenge_id)
    user = request.user
    
    # Check if already participating
    if ChallengeParticipation.objects.filter(user=user, challenge=challenge).exists():
        messages.warning(request, 'You are already participating in this challenge!')
        return redirect('outfits:challenge_detail', challenge_id=challenge_id)
    
    # Check if challenge is active
    if not challenge.is_active():
        messages.error(request, 'This challenge is no longer active.')
        return redirect('outfits:challenges_list')
    
    # Create participation
    participation = ChallengeParticipation.objects.create(
        user=user,
        challenge=challenge
    )
    
    messages.success(request, f'You have joined the "{challenge.name}" challenge!')
    return redirect('outfits:challenge_detail', challenge_id=challenge_id)


@login_required
def submit_challenge_outfit_view(request, challenge_id):
    """
    Submit an outfit for a challenge
    """
    challenge = get_object_or_404(StyleChallenge, id=challenge_id)
    user = request.user
    
    participation = get_object_or_404(
        ChallengeParticipation, 
        user=user, 
        challenge=challenge,
        completed=False
    )
    
    if request.method == 'POST':
        outfit_id = request.POST.get('outfit')
        notes = request.POST.get('notes', '')
        
        if not outfit_id:
            messages.error(request, 'Please select an outfit.')
            return redirect('outfits:challenge_detail', challenge_id=challenge_id)
        
        try:
            outfit = Outfit.objects.get(id=outfit_id, user=user)
            
            # Check if outfit already submitted
            if ChallengeOutfit.objects.filter(participation=participation, outfit=outfit).exists():
                messages.warning(request, 'This outfit has already been submitted for the challenge.')
                return redirect('outfits:challenge_detail', challenge_id=challenge_id)
            
            # Create challenge outfit submission
            ChallengeOutfit.objects.create(
                participation=participation,
                outfit=outfit,
                notes=notes
            )
            
            # Update streak and last activity
            from django.utils import timezone
            participation.last_activity = timezone.now().date()
            
            # Check if challenge is completed
            required_outfits = challenge.rules.get('required_outfits', challenge.duration_days)
            submitted_count = ChallengeOutfit.objects.filter(participation=participation).count()
            
            if submitted_count >= required_outfits:
                participation.completed = True
                participation.completed_at = timezone.now()
                messages.success(request, f'Congratulations! You completed the "{challenge.name}" challenge!')
                
                # Award badge
                UserBadge.objects.create(
                    user=user,
                    badge_type='challenge_complete',
                    name=f'{challenge.name} Champion',
                    description=f'Completed the {challenge.name} challenge'
                )
            else:
                messages.success(request, f'Outfit submitted! {required_outfits - submitted_count} more to go.')
            
            participation.save()
            
        except Outfit.DoesNotExist:
            messages.error(request, 'Invalid outfit selected.')
        
        return redirect('outfits:challenge_detail', challenge_id=challenge_id)
    
    # GET request - show outfit selection
    user_outfits = Outfit.objects.filter(user=user)
    already_submitted = ChallengeOutfit.objects.filter(
        participation=participation
    ).values_list('outfit_id', flat=True)
    
    available_outfits = user_outfits.exclude(id__in=already_submitted)
    
    context = {
        'challenge': challenge,
        'participation': participation,
        'available_outfits': available_outfits,
    }
    
    return render(request, 'submit_challenge_outfit.html', context)


@login_required
def create_challenge_view(request):
    """
    Create a new style challenge
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        challenge_type = request.POST.get('challenge_type', 'capsule')
        duration_days = int(request.POST.get('duration_days', 7))
        rules_text = request.POST.get('rules', '')
        
        if not name:
            messages.error(request, 'Challenge name is required.')
            return redirect('outfits:create_challenge')
        
        # Parse rules (simplified - in production you'd want a better rules system)
        rules = {}
        if rules_text:
            rules = {'custom_rules': rules_text}
        
        # Create challenge
        challenge = StyleChallenge.objects.create(
            name=name,
            description=description,
            challenge_type=challenge_type,
            duration_days=duration_days,
            rules=rules,
            created_by=request.user,
            is_public=request.POST.get('is_public') == 'on'
        )
        
        messages.success(request, f'Challenge "{name}" created successfully!')
        return redirect('outfits:challenge_detail', challenge_id=challenge.id)
    
    context = {
        'challenge_types': StyleChallenge.CHALLENGE_TYPES,
    }
    return render(request, 'create_challenge.html', context)


@login_required
def badges_view(request):
    """
    View user's earned badges
    """
    user = request.user
    badges = UserBadge.objects.filter(user=user)
    
    # Calculate some stats
    total_challenges = ChallengeParticipation.objects.filter(user=user, completed=True).count()
    longest_streak = ChallengeParticipation.objects.filter(user=user).aggregate(
        max_streak=Max('streak_days')
    )['max_streak'] or 0
    
    context = {
        'badges': badges,
        'total_challenges': total_challenges,
        'longest_streak': longest_streak,
    }
    
    return render(request, 'badges.html', context)