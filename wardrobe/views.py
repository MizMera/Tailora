from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

from .models import ClothingItem, ClothingCategory
from .serializers import (
    ClothingItemListSerializer, 
    ClothingItemDetailSerializer,
    ClothingItemCreateSerializer,
    ClothingCategorySerializer,
    WardrobeStatsSerializer
)


# ==================== Template Views ====================

@login_required
def wardrobe_gallery_view(request):
    """
    Display user's wardrobe in gallery view
    Supports filtering and search
    """
    user = request.user
    items = ClothingItem.objects.filter(user=user)
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    color_filter = request.GET.get('color')
    season_filter = request.GET.get('season')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    show_favorites = request.GET.get('favorites') == 'true'
    
    # Apply filters
    if category_filter:
        items = items.filter(category__name=category_filter)
    
    if color_filter:
        items = items.filter(color__icontains=color_filter)
    
    if season_filter:
        items = items.filter(seasons__contains=[season_filter])
    
    if status_filter:
        items = items.filter(status=status_filter)
    
    if show_favorites:
        items = items.filter(favorite=True)
    
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__contains=[search_query])
        )
    
    # Get filter options for dropdowns
    categories = ClothingCategory.objects.filter(
        Q(is_custom=False) | Q(user=user)
    )
    colors = items.values_list('color', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(items, 24)  # 24 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get wardrobe stats
    total_items = items.count()
    max_items = user.get_max_wardrobe_items()
    remaining_slots = max_items - total_items
    
    context = {
        'items': page_obj,
        'categories': categories,
        'colors': colors,
        'total_items': total_items,
        'max_items': max_items,
        'remaining_slots': remaining_slots,
        'is_premium': user.is_premium_user(),
        'selected_category': category_filter,
        'selected_color': color_filter,
        'selected_season': season_filter,
        'selected_status': status_filter,
        'search_query': search_query,
        'show_favorites': show_favorites,
    }
    
    return render(request, 'wardrobe_gallery.html', context)


@login_required
def wardrobe_upload_view(request):
    """
    Upload new clothing item to wardrobe
    """
    user = request.user
    
    # Check wardrobe limit
    current_count = ClothingItem.objects.filter(user=user).count()
    max_items = user.get_max_wardrobe_items()
    
    if current_count >= max_items:
        messages.error(
            request, 
            f'Vous avez atteint la limite de {max_items} vêtements. '
            f'Passez à Premium pour ajouter plus d\'articles!'
        )
        return redirect('wardrobe_gallery')
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        color = request.POST.get('color')
        color_hex = request.POST.get('color_hex', '')
        pattern = request.POST.get('pattern', '')
        material = request.POST.get('material', '')
        brand = request.POST.get('brand', '')
        seasons = request.POST.getlist('seasons')
        occasions = request.POST.getlist('occasions')
        purchase_date = request.POST.get('purchase_date') or None
        purchase_price = request.POST.get('purchase_price') or None
        purchase_location = request.POST.get('purchase_location', '')
        is_secondhand = request.POST.get('is_secondhand') == 'on'
        condition = request.POST.get('condition', 'good')
        tags = request.POST.get('tags', '').split(',')
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        # Validation
        if not name or not image or not color:
            messages.error(request, 'Nom, image et couleur sont requis.')
            return render(request, 'wardrobe_upload.html', {'categories': get_categories(user)})
        
        # Validate image
        if image.size > 5 * 1024 * 1024:  # 5MB
            messages.error(request, 'La taille de l\'image ne doit pas dépasser 5 MB.')
            return render(request, 'wardrobe_upload.html', {'categories': get_categories(user)})
        
        # Process and optimize image
        try:
            processed_image = optimize_image(image)
        except Exception as e:
            messages.error(request, f'Erreur lors du traitement de l\'image: {str(e)}')
            return render(request, 'wardrobe_upload.html', {'categories': get_categories(user)})
        
        # Get category
        category = None
        if category_id:
            try:
                category = ClothingCategory.objects.get(id=category_id)
            except ClothingCategory.DoesNotExist:
                pass
        
        # Create item
        try:
            item = ClothingItem.objects.create(
                user=user,
                name=name,
                description=description,
                category=category,
                image=processed_image,
                color=color,
                color_hex=color_hex,
                pattern=pattern,
                material=material,
                brand=brand,
                seasons=seasons,
                occasions=occasions,
                purchase_date=purchase_date,
                purchase_price=purchase_price,
                purchase_location=purchase_location,
                is_secondhand=is_secondhand,
                condition=condition,
                tags=tags
            )
            
            # Update user's wardrobe count
            user.increment_wardrobe_count()
            
            messages.success(request, f'{name} a été ajouté à votre garde-robe!')
            return redirect('wardrobe_detail', item_id=item.id)
        
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout: {str(e)}')
            return render(request, 'wardrobe_upload.html', {'categories': get_categories(user)})
    
    # GET request
    categories = get_categories(user)
    context = {
        'categories': categories,
        'remaining_slots': max_items - current_count,
        'max_items': max_items,
    }
    
    return render(request, 'wardrobe_upload.html', context)


@login_required
def wardrobe_detail_view(request, item_id):
    """
    Display single wardrobe item details
    """
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
    context = {
        'item': item,
    }
    
    return render(request, 'wardrobe_detail.html', context)


@login_required
def wardrobe_edit_view(request, item_id):
    """
    Edit existing wardrobe item
    """
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
    if request.method == 'POST':
        # Update fields
        item.name = request.POST.get('name', item.name)
        item.description = request.POST.get('description', item.description)
        item.color = request.POST.get('color', item.color)
        item.color_hex = request.POST.get('color_hex', item.color_hex)
        item.pattern = request.POST.get('pattern', item.pattern)
        item.material = request.POST.get('material', item.material)
        item.brand = request.POST.get('brand', item.brand)
        item.seasons = request.POST.getlist('seasons')
        item.occasions = request.POST.getlist('occasions')
        item.purchase_date = request.POST.get('purchase_date') or None
        item.purchase_price = request.POST.get('purchase_price') or None
        item.purchase_location = request.POST.get('purchase_location', item.purchase_location)
        item.is_secondhand = request.POST.get('is_secondhand') == 'on'
        item.condition = request.POST.get('condition', item.condition)
        item.status = request.POST.get('status', item.status)
        item.favorite = request.POST.get('favorite') == 'on'
        
        tags = request.POST.get('tags', '').split(',')
        item.tags = [tag.strip() for tag in tags if tag.strip()]
        
        # Update category if provided
        category_id = request.POST.get('category')
        if category_id:
            try:
                item.category = ClothingCategory.objects.get(id=category_id)
            except ClothingCategory.DoesNotExist:
                pass
        
        # Update image if provided
        new_image = request.FILES.get('image')
        if new_image:
            try:
                item.image = optimize_image(new_image)
            except Exception as e:
                messages.error(request, f'Erreur lors du traitement de l\'image: {str(e)}')
                return render(request, 'wardrobe_edit.html', {
                    'item': item,
                    'categories': get_categories(request.user)
                })
        
        item.save()
        messages.success(request, f'{item.name} a été mis à jour!')
        return redirect('wardrobe_detail', item_id=item.id)
    
    # GET request
    categories = get_categories(request.user)
    context = {
        'item': item,
        'categories': categories,
    }
    
    return render(request, 'wardrobe_edit.html', context)


@login_required
def wardrobe_delete_view(request, item_id):
    """
    Delete wardrobe item
    """
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
    if request.method == 'POST':
        item_name = item.name
        item.delete()
        
        # Update user's wardrobe count
        user = request.user
        if user.wardrobe_items_count > 0:
            user.wardrobe_items_count -= 1
            user.save()
        
        messages.success(request, f'{item_name} a été supprimé de votre garde-robe.')
        return redirect('wardrobe_gallery')
    
    context = {
        'item': item,
    }
    
    return render(request, 'wardrobe_delete.html', context)


@login_required
def wardrobe_toggle_favorite_view(request, item_id):
    """
    Toggle favorite status of an item
    """
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    item.favorite = not item.favorite
    item.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'wardrobe_gallery'))


@login_required
def wardrobe_stats_view(request):
    """
    Display wardrobe statistics and insights
    """
    user = request.user
    items = ClothingItem.objects.filter(user=user)
    
    # Calculate statistics
    stats = {
        'total_items': items.count(),
        'by_category': {},
        'by_color': {},
        'by_season': {},
        'favorite_count': items.filter(favorite=True).count(),
        'most_worn': [],
        'recent_additions': [],
        'wardrobe_limit': user.get_max_wardrobe_items(),
    }
    
    # Group by category
    category_counts = items.values('category__name').annotate(count=Count('id'))
    for item in category_counts:
        if item['category__name']:
            stats['by_category'][item['category__name']] = item['count']
    
    # Group by color
    color_counts = items.values('color').annotate(count=Count('id'))
    for item in color_counts:
        stats['by_color'][item['color']] = item['count']
    
    # Most worn items
    stats['most_worn'] = list(
        items.filter(times_worn__gt=0)
        .order_by('-times_worn')[:5]
        .values('name', 'times_worn', 'image')
    )
    
    # Recent additions
    stats['recent_additions'] = list(
        items.order_by('-created_at')[:5]
        .values('name', 'created_at', 'image')
    )
    
    stats['remaining_slots'] = stats['wardrobe_limit'] - stats['total_items']
    
    context = {
        'stats': stats,
        'is_premium': user.is_premium_user(),
    }
    
    return render(request, 'wardrobe_stats.html', context)


# ==================== Helper Functions ====================

def get_categories(user):
    """Get categories available to user"""
    return ClothingCategory.objects.filter(
        Q(is_custom=False) | Q(user=user)
    )


def optimize_image(image_file):
    """
    Optimize uploaded image: resize and compress
    Returns optimized InMemoryUploadedFile
    """
    # Open image
    img = Image.open(image_file)
    
    # Convert RGBA to RGB if necessary
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # Resize if too large (max 1920x1920)
    max_size = (1920, 1920)
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save to BytesIO
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)
    
    # Create InMemoryUploadedFile
    return InMemoryUploadedFile(
        output,
        'ImageField',
        f"{image_file.name.split('.')[0]}.jpg",
        'image/jpeg',
        sys.getsizeof(output),
        None
    )


# ==================== API Views (for REST API) ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_wardrobe_list(request):
    """API: Get user's wardrobe items"""
    items = ClothingItem.objects.filter(user=request.user)
    
    # Apply filters
    category = request.query_params.get('category')
    if category:
        items = items.filter(category__name=category)
    
    color = request.query_params.get('color')
    if color:
        items = items.filter(color__icontains=color)
    
    season = request.query_params.get('season')
    if season:
        items = items.filter(seasons__contains=[season])
    
    serializer = ClothingItemListSerializer(items, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_wardrobe_create(request):
    """API: Create new wardrobe item"""
    serializer = ClothingItemCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        item = serializer.save()
        detail_serializer = ClothingItemDetailSerializer(item)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_wardrobe_detail(request, item_id):
    """API: Get single item details"""
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    serializer = ClothingItemDetailSerializer(item)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def api_wardrobe_update(request, item_id):
    """API: Update wardrobe item"""
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    serializer = ClothingItemDetailSerializer(item, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_wardrobe_delete(request, item_id):
    """API: Delete wardrobe item"""
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    item.delete()
    
    # Update user's wardrobe count
    user = request.user
    if user.wardrobe_items_count > 0:
        user.wardrobe_items_count -= 1
        user.save()
    
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_wardrobe_stats(request):
    """API: Get wardrobe statistics"""
    user = request.user
    items = ClothingItem.objects.filter(user=user)
    
    stats = {
        'total_items': items.count(),
        'by_category': {},
        'by_color': {},
        'by_season': {},
        'favorite_count': items.filter(favorite=True).count(),
        'most_worn': list(items.order_by('-times_worn')[:5].values('id', 'name', 'times_worn')),
        'recent_additions': list(items.order_by('-created_at')[:5].values('id', 'name', 'created_at')),
        'wardrobe_limit': user.get_max_wardrobe_items(),
        'remaining_slots': user.get_max_wardrobe_items() - items.count(),
    }
    
    # Group by category
    for item in items.values('category__name').annotate(count=Count('id')):
        if item['category__name']:
            stats['by_category'][item['category__name']] = item['count']
    
    # Group by color
    for item in items.values('color').annotate(count=Count('id')):
        stats['by_color'][item['color']] = item['count']
    
    serializer = WardrobeStatsSerializer(stats)
    return Response(serializer.data)
