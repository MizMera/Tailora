from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Outfit, OutfitItem
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
<<<<<<< HEAD
            Q(style_tags__contains=[search_query])
=======
            Q(style_tags__icontains=search_query)
>>>>>>> main
        )
    
    # Pagination
    paginator = Paginator(outfits, 12)  # 12 outfits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get stats
    total_outfits = outfits.count()
    favorite_count = outfits.filter(favorite=True).count()
    
    context = {
        'outfits': page_obj,
        'total_outfits': total_outfits,
        'favorite_count': favorite_count,
        'selected_occasion': occasion_filter,
        'search_query': search_query,
        'show_favorites': show_favorites,
        'occasions': Outfit.OCCASION_CHOICES,
    }
    
    return render(request, 'outfit_gallery.html', context)


@login_required
def outfit_create_view(request):
    """
    Create a new outfit by selecting wardrobe items
    """
    user = request.user
    
<<<<<<< HEAD
=======
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

>>>>>>> main
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
            
<<<<<<< HEAD
=======
            # Update user's outfit count
            user.increment_outfits_count()
            
>>>>>>> main
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
<<<<<<< HEAD
=======
        
        # Update user's outfit count
        user = request.user
        if user.outfits_created_count > 0:
            user.outfits_created_count -= 1
            user.save(update_fields=['outfits_created_count'])
        
>>>>>>> main
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
<<<<<<< HEAD
=======


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
>>>>>>> main
