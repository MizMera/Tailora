from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Max
from django.core.paginator import Paginator
from .models import Outfit, OutfitItem, StyleChallenge, ChallengeParticipation, ChallengeOutfit, UserBadge
from .models import Outfit, OutfitItem
from users.models import StyleCritiqueSession
from wardrobe.models import ClothingItem


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
        outfits = outfits.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(style_tags__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(outfits, 12)  # 12 outfits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get stats
    total_outfits = outfits.count()
    favorite_count = outfits.filter(favorite=True).count()
    
    # Get today's daily and weekly challenges
    from django.utils import timezone
    from datetime import timedelta
    today = timezone.now().date()
    
    # Daily challenge (today only)
    daily_challenge = StyleChallenge.objects.filter(
        start_date=today,
        end_date=today,
        challenge_type='daily',
        is_public=True
    ).first()
    
    # Weekly challenge (active this week)
    weekly_challenge = StyleChallenge.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        challenge_type='weekly',
        is_public=True
    ).first()
    
    # Get user's participation
    daily_participation = None
    weekly_participation = None
    if daily_challenge:
        daily_participation = ChallengeParticipation.objects.filter(
            user=user, 
            challenge=daily_challenge
        ).first()
    if weekly_challenge:
        weekly_participation = ChallengeParticipation.objects.filter(
            user=user,
            challenge=weekly_challenge
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
        'weekly_challenge': weekly_challenge,
        'weekly_participation': weekly_participation,
    }
    
    return render(request, 'outfit_gallery.html', context)


@login_required
def outfit_advanced_search_view(request):
    """
    Advanced search for outfits with multiple filters
    """
    user = request.user
    outfits = Outfit.objects.filter(user=user).prefetch_related('items')
    
    # Get all filter parameters
    search_query = request.GET.get('search', '').strip()
    occasion_filter = request.GET.get('occasion', '')
    colors = request.GET.getlist('colors')
    styles = request.GET.getlist('styles')
    item_count_min = request.GET.get('item_count_min', '')
    item_count_max = request.GET.get('item_count_max', '')
    show_favorites = request.GET.get('favorites') == 'true'
    
    # Apply search query
    if search_query:
        outfits = outfits.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(style_tags__icontains=search_query)
        )
    
    # Apply occasion filter
    if occasion_filter:
        outfits = outfits.filter(occasion=occasion_filter)
    
    # Apply color filters
    if colors:
        color_query = Q()
        for color in colors:
            color_query |= Q(items__color__icontains=color)
        outfits = outfits.filter(color_query).distinct()
    
    # Apply style filters
    if styles:
        style_query = Q()
        for style in styles:
            style_query |= Q(style_tags__icontains=style)
        outfits = outfits.filter(style_query).distinct()
    
    # Apply item count filters
    if item_count_min:
        try:
            min_count = int(item_count_min)
            outfits = outfits.annotate(item_count=Count('items')).filter(item_count__gte=min_count)
        except (ValueError, TypeError):
            pass
    
    if item_count_max:
        try:
            max_count = int(item_count_max)
            if not item_count_min:
                outfits = outfits.annotate(item_count=Count('items'))
            outfits = outfits.filter(item_count__lte=max_count)
        except (ValueError, TypeError):
            pass
    
    # Apply favorites filter
    if show_favorites:
        outfits = outfits.filter(favorite=True)
    
    # Pagination
    paginator = Paginator(outfits, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all unique colors and styles from user's wardrobe for filter options
    user_colors = set()
    user_styles = set()
    
    for outfit in Outfit.objects.filter(user=user):
        for item in outfit.items.all():
            if hasattr(item, 'color') and item.color:
                user_colors.add(item.color)
        if outfit.style_tags:
            tags = outfit.style_tags.split(',')
            for tag in tags:
                user_styles.add(tag.strip())
    
    # Get wardrobe items for must contain/exclude filters
    wardrobe_items = ClothingItem.objects.filter(user=user, status='available')
    
    context = {
        'outfits': page_obj,
        'total_outfits': outfits.count(),
        'occasions': Outfit.OCCASION_CHOICES,
        'colors': sorted(list(user_colors)),
        'styles': sorted(list(user_styles)),
        'selected_colors': colors,
        'selected_styles': styles,
        'selected_occasion': occasion_filter,
        'search_query': search_query,
        'item_count_min': item_count_min,
        'item_count_max': item_count_max,
        'show_favorites': show_favorites,
        'wardrobe_items': wardrobe_items,
    }
    
    return render(request, 'outfit_advanced_search.html', context)


@login_required
def outfit_create_view(request):
    """
    Create a new outfit by selecting wardrobe items
    """
    user = request.user
    
    # Check outfit limit
    outfit_count = Outfit.objects.filter(user=user).count()
    max_outfits = user.get_max_outfits()
    if outfit_count >= max_outfits:
        messages.warning(
            request, 
            f"You have reached your limit of {max_outfits} outfits. "
            f"Upgrade to Premium to create more."
        )
        return redirect('outfits:outfit_gallery')

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
            
            # Update user's outfit count
            user.increment_outfits_count()
            
            # Run AI Style Coach audit AFTER items are added
            try:
                from recommendations.ai_engine import StyleCoach
                coach = StyleCoach(user)
                coach.audit_outfit(outfit)
            except Exception as e:
                print(f"Style Coach error: {e}")
            
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
    
    # Get latest critique
    critique = StyleCritiqueSession.objects.filter(
        related_outfit=outfit
    ).order_by('-created_at').first()
    
    context = {
        'outfit': outfit,
        'outfit_items': outfit_items,
        'critique': critique,
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
        
        # Re-run AI Style Coach audit after edit
        if item_ids:  # Only re-audit if items were changed
            try:
                from recommendations.ai_engine import StyleCoach
                coach = StyleCoach(request.user)
                coach.audit_outfit(outfit)
            except Exception as e:
                print(f"Style Coach error on edit: {e}")
        
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
        
        # Update user's outfit count
        user = request.user
        if user.outfits_created_count > 0:
            user.outfits_created_count -= 1
            user.save(update_fields=['outfits_created_count'])
        
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
def outfit_stats_view(request):
    """
    Display outfit statistics and insights
    """
    user = request.user
    outfits = Outfit.objects.filter(user=user)
    
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
    
    # Most worn outfits
    stats['most_worn'] = list(
        outfits.filter(times_worn__gt=0)
        .order_by('-times_worn')[:5]
        .values('name', 'times_worn', 'outfit_image', 'id')
    )
    
    # Recent outfits
    stats['recent_outfits'] = list(
        outfits.order_by('-created_at')[:5]
        .values('name', 'created_at', 'outfit_image', 'id')
    )
    
    context = {
        'stats': stats,
    }
    
    return render(request, 'outfit_stats.html', context)


# ==================== REST API Views ====================

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .serializers import (
    OutfitSerializer,
    OutfitDetailSerializer,
    OutfitCreateSerializer,
    OutfitUpdateSerializer,
    OutfitItemSerializer
)
from rest_framework.exceptions import ValidationError


class OutfitPagination(PageNumberPagination):
    """Custom pagination for outfits"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class OutfitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for outfit management
    Provides CRUD operations for outfits
    
    Endpoints:
    - GET /api/outfits/ - List all user's outfits
    - POST /api/outfits/ - Create new outfit
    - GET /api/outfits/{id}/ - Get outfit details
    - PUT /api/outfits/{id}/ - Update outfit
    - DELETE /api/outfits/{id}/ - Delete outfit
    
    Custom actions:
    - POST /api/outfits/{id}/toggle_favorite/ - Toggle favorite status
    - POST /api/outfits/{id}/add_item/ - Add item to outfit
    - POST /api/outfits/{id}/remove_item/ - Remove item from outfit
    - POST /api/outfits/{id}/duplicate/ - Duplicate outfit
    - GET /api/outfits/stats/ - Get outfit statistics
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OutfitPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['occasion', 'favorite', 'source']
    search_fields = ['name', 'description', 'style_tags']
    ordering_fields = ['created_at', 'times_worn', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Users can only access their own outfits"""
        return Outfit.objects.filter(user=self.request.user).prefetch_related(
            'outfit_items',
            'outfit_items__clothing_item',
            'items'
        )
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return OutfitSerializer
        elif self.action == 'create':
            return OutfitCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OutfitUpdateSerializer
        return OutfitDetailSerializer
    
    def perform_create(self, serializer):
        """Automatically associate outfit with current user and check limits"""
        user = self.request.user
        outfit_count = Outfit.objects.filter(user=user).count()
        max_outfits = user.get_max_outfits()
        if outfit_count >= max_outfits:
            raise ValidationError(
                f"You have reached your limit of {max_outfits} outfits. "
                f"Upgrade to Premium to create more."
            )
        serializer.save()
    
    def perform_destroy(self, instance):
        """Decrement user's outfit count on delete"""
        user = self.request.user
        instance.delete()
        # Update count
        user.outfits_created_count = max(0, user.outfits_created_count - 1)
        user.save(update_fields=['outfits_created_count'])
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """
        Toggle favorite status of an outfit
        POST /api/outfits/{id}/toggle_favorite/
        """
        outfit = self.get_object()
        outfit.favorite = not outfit.favorite
        outfit.save(update_fields=['favorite'])
        
        return Response({
            'status': 'success',
            'favorite': outfit.favorite,
            'message': f'Outfit {"added to" if outfit.favorite else "removed from"} favorites'
        })
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """
        Add item to outfit
        POST /api/outfits/{id}/add_item/
        Body: {
            "clothing_item_id": "uuid",
            "layer": "base|mid|outer|accessory|shoes",
            "position": 0
        }
        """
        outfit = self.get_object()
        clothing_item_id = request.data.get('clothing_item_id')
        
        if not clothing_item_id:
            return Response(
                {'error': 'clothing_item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify item exists and belongs to user
        try:
            clothing_item = ClothingItem.objects.get(
                id=clothing_item_id,
                user=request.user
            )
        except ClothingItem.DoesNotExist:
            return Response(
                {'error': 'Clothing item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if item already in outfit
        if OutfitItem.objects.filter(outfit=outfit, clothing_item=clothing_item).exists():
            return Response(
                {'error': 'Item already in outfit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create outfit item
        outfit_item = OutfitItem.objects.create(
            outfit=outfit,
            clothing_item=clothing_item,
            layer=request.data.get('layer', 'base'),
            position=request.data.get('position', 0),
            x_position=request.data.get('x_position'),
            y_position=request.data.get('y_position')
        )
        
        serializer = OutfitItemSerializer(outfit_item)
        return Response({
            'status': 'success',
            'message': 'Item added to outfit',
            'outfit_item': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """
        Remove item from outfit
        POST /api/outfits/{id}/remove_item/
        Body: {"clothing_item_id": "uuid"}
        """
        outfit = self.get_object()
        clothing_item_id = request.data.get('clothing_item_id')
        
        if not clothing_item_id:
            return Response(
                {'error': 'clothing_item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            outfit_item = OutfitItem.objects.get(
                outfit=outfit,
                clothing_item_id=clothing_item_id
            )
            outfit_item.delete()
            
            return Response({
                'status': 'success',
                'message': 'Item removed from outfit'
            })
        except OutfitItem.DoesNotExist:
            return Response(
                {'error': 'Item not in outfit'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate an outfit
        POST /api/outfits/{id}/duplicate/
        """
        original_outfit = self.get_object()
        
        # Create duplicate
        duplicate_outfit = Outfit.objects.create(
            user=request.user,
            name=f"{original_outfit.name} (Copy)",
            description=original_outfit.description,
            occasion=original_outfit.occasion,
            style_tags=original_outfit.style_tags,
            source='user',
            min_temperature=original_outfit.min_temperature,
            max_temperature=original_outfit.max_temperature,
            suitable_weather=original_outfit.suitable_weather
        )
        
        # Copy outfit items
        for outfit_item in original_outfit.outfit_items.all():
            OutfitItem.objects.create(
                outfit=duplicate_outfit,
                clothing_item=outfit_item.clothing_item,
                layer=outfit_item.layer,
                position=outfit_item.position,
                x_position=outfit_item.x_position,
                y_position=outfit_item.y_position
            )
        
        # Update user count
        request.user.increment_outfits_count()
        
        serializer = OutfitDetailSerializer(duplicate_outfit)
        return Response({
            'status': 'success',
            'message': 'Outfit duplicated successfully',
            'outfit': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get outfit statistics
        GET /api/outfits/stats/
        """
        user = request.user
        outfits = self.get_queryset()
        
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
        
        # Most worn outfits
        most_worn = outfits.filter(times_worn__gt=0).order_by('-times_worn')[:5]
        stats['most_worn'] = OutfitSerializer(most_worn, many=True).data
        
        # Recent outfits
        recent = outfits.order_by('-created_at')[:5]
        stats['recent_outfits'] = OutfitSerializer(recent, many=True).data
        
        # Outfit limit info
        stats['max_outfits'] = user.get_max_outfits()
        stats['remaining_slots'] = max(0, stats['max_outfits'] - stats['total_outfits'])
        
        return Response(stats)

# Challenge Views
@login_required
def challenges_list_view(request):
    """
    List all available challenges (daily, weekly, and regular)
    """
    user = request.user
    from django.utils import timezone
    
    all_challenges = StyleChallenge.objects.filter(
        Q(is_public=True) | Q(created_by=user)
    ).prefetch_related('participations')
    
    # Get user's participations
    user_participations = {
        p.challenge_id: p for p in ChallengeParticipation.objects.filter(user=user)
    }
    
    # Separate challenges into categories
    daily_challenges = []
    weekly_challenges = []
    active_challenges = []
    available_challenges = []
    completed_challenges = []
    
    today = timezone.now().date()
    
    for challenge in all_challenges:
        participation = user_participations.get(challenge.id)
        
        # Check if challenge is active (current date is between start and end)
        is_active = challenge.start_date <= today <= challenge.end_date if challenge.end_date else challenge.start_date <= today
        
        # Categorize by challenge type - always append as (challenge, participation) tuple for consistency
        if challenge.challenge_type == 'daily' and is_active:
            if participation:
                if participation.completed:
                    completed_challenges.append((challenge, participation))
                else:
                    daily_challenges.append((challenge, participation))
            else:
                daily_challenges.append((challenge, None))
        elif challenge.challenge_type == 'weekly' and is_active:
            if participation:
                if participation.completed:
                    completed_challenges.append((challenge, participation))
                else:
                    weekly_challenges.append((challenge, participation))
            else:
                weekly_challenges.append((challenge, None))
        else:
            # Regular challenges
            if participation:
                if participation.completed:
                    completed_challenges.append((challenge, participation))
                else:
                    active_challenges.append((challenge, participation))
            else:
                if is_active:
                    available_challenges.append((challenge, None))
    
    context = {
        'daily_challenges': daily_challenges,
        'weekly_challenges': weekly_challenges,
        'active_challenges': active_challenges,
        'available_challenges': available_challenges,
        'completed_challenges': completed_challenges,
        'today': today,
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


