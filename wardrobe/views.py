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
from django.conf import settings
import sys

from .models import ClothingItem, ClothingCategory
from .serializers import (
    ClothingItemListSerializer, 
    ClothingItemDetailSerializer,
    ClothingItemCreateSerializer,
    ClothingCategorySerializer,
    WardrobeStatsSerializer
)
from .ai_image_analyzer import get_image_analyzer


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
    season_filter = request.GET.get('seasons')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    show_favorites = request.GET.get('favorites') == 'true'

    # DEBUG: Print what we're filtering for
    print(f"DEBUG: Season filter value: '{season_filter}'")
    print(f"DEBUG: Initial items count: {items.count()}")
    
    # Apply filters
    if color_filter:
        items = items.filter(color__icontains=color_filter)
        print(f"DEBUG: After color filter '{color_filter}': {items.count()} items")

    if status_filter:
        items = items.filter(status=status_filter)
        print(f"DEBUG: After status filter '{status_filter}': {items.count()} items")
    
    if show_favorites:
        items = items.filter(favorite=True)
        print(f"DEBUG: After favorites filter: {items.count()} items")
    
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query) 
        )
        print(f"DEBUG: After search filter: {items.count()} items")
    
    # Apply season filter - FIXED: Initialize matching_ids outside the if block
    matching_ids = None  # Initialize as None
    
    if season_filter:
        # Get ALL items for this user first (to avoid filtering issues)
        all_user_items = ClothingItem.objects.filter(user=user)
        
        # Find items that match the season
        matching_ids = []  # Now this is defined
        for item in all_user_items:
            # DEBUG: Check what's in each item's seasons
            print(f"DEBUG: Item '{item.name}' has seasons: {item.seasons} (type: {type(item.seasons)})")
            
            if item.seasons and season_filter in item.seasons:
                matching_ids.append(item.id)
                print(f"DEBUG: Item '{item.name}' matches season '{season_filter}'")
        
        print(f"DEBUG: Found {len(matching_ids)} items matching season '{season_filter}'")

        # Apply the season filter to our current queryset
        if matching_ids:
            items = items.filter(id__in=matching_ids)
        else:
            items = items.none()  # No matches found
        
        print(f"DEBUG: After season filter: {items.count()} items")

    # Get filter options for dropdowns
    categories = ClothingCategory.objects.filter(
        Q(is_custom=False) | Q(user=user)
    )
    colors = items.values_list('color', flat=True).distinct()

    # Get available seasons for dropdown
    seasons = get_available_seasons(user)
    print(f"DEBUG: Available seasons: {seasons}")

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
        'seasons': seasons,  # Add seasons to context
        'total_items': total_items,
        'max_items': max_items,
        'remaining_slots': remaining_slots,
        'is_premium': user.is_premium_user(),
        'selected_category': category_filter,
        'selected_color': color_filter,
        'selected_seasons': season_filter,
        'selected_status': status_filter,
        'search_query': search_query,
        'show_favorites': show_favorites,
    }
    
    return render(request, 'wardrobe_gallery.html', context)

def get_available_seasons(user):
    """Get unique seasons from user's wardrobe items"""
    items = ClothingItem.objects.filter(user=user)
    all_seasons = []
    
    for item in items:
        if item.seasons:  # Check if seasons list is not empty
            all_seasons.extend(item.seasons)
            print(f"DEBUG: Item '{item.name}' contributes seasons: {item.seasons}")
    
    unique_seasons = sorted(set(all_seasons))
    print(f"DEBUG: Unique seasons found: {unique_seasons}")
    return unique_seasons


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
            f"You've reached your wardrobe limit of {max_items} items. Upgrade to Premium to add more!"
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
        
        # Debug logging
        print(f"DEBUG: Received POST data:")
        print(f"  - name: {name}")
        print(f"  - image: {image}")
        print(f"  - color: {color}")
        print(f"  - category_id: {category_id}")
        
        # Validation
        if not name or not image or not color:
            error_msg = f"Name, image, and color are required. (Received: name={name}, image={image}, color={color})"
            messages.error(request, error_msg)
            print(f"DEBUG: Validation failed - {error_msg}")
            return render(request, 'wardrobe_upload.html', {'categories': get_categories(user)})
        
        # Validate image
        if image.size > 5 * 1024 * 1024:  # 5MB
            messages.error(request, "Image size must not exceed 5 MB.")
            return render(request, 'wardrobe_upload.html', {'categories': get_categories(user)})
        
        # Process and optimize image
        try:
            processed_image = optimize_image(image)
        except Exception as e:
            messages.error(request, f"Error processing image: {str(e)}")
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
            
            messages.success(request, f"{name} has been added to your wardrobe!")
            return redirect('wardrobe_detail', item_id=item.id)
        
        except Exception as e:
            messages.error(request, f"Error adding item: {str(e)}")
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
                messages.error(request, f"Error processing image: {str(e)}")
                return render(request, 'wardrobe_edit.html', {
                    'item': item,
                    'categories': get_categories(request.user)
                })
        
        item.save()
        messages.success(request, f"{item.name} has been updated!")
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
        
        messages.success(request, f"{item_name} has been removed from your wardrobe.")
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
    
    # Recent additions with absolute URLs - GARDEZ SEULEMENT CETTE VERSION
    recent_items = items.order_by('-created_at')[:5]
    
    # Debug: print image URLs
    for item in recent_items:
        print(f"Item: {item.name}, Image URL: {item.image.url}")
        print(f"Absolute URL: {request.build_absolute_uri(item.image.url)}")

    stats['recent_additions'] = [
        {
            'name': item.name,
            'image_url': request.build_absolute_uri(item.image.url),  # URL absolue
            'color': item.color,
            'created_at': item.created_at
        }
        for item in recent_items
    ]
    
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
    
    season = request.query_params.get('seasons')
    if season:
        items = items.filter(seasons__contains=season)
    
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_analyze_image(request):
    """
    API: Analyze uploaded image using AI to extract clothing metadata
    """
    try:
        from .category_mapper import CategoryMapper
        
        image_file = request.FILES.get('image')

        if not image_file:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate image size (max 10MB for analysis)
        if image_file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'Image size must not exceed 10 MB'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Analyze image
        analyzer = get_image_analyzer()
        analysis = analyzer.analyze_image(image_file)

        # Get suggested category based on AI detection
        suggested_category = CategoryMapper.get_category_for_ai_detection(
            ai_category=analysis.get('category'),
            item_type=analysis.get('item_type'),
            user=request.user
        )
        
        # Get list of category name suggestions
        category_suggestions = CategoryMapper.get_suggested_categories(
            ai_category=analysis.get('category'),
            item_type=analysis.get('item_type')
        )

        response_data = {
            'analysis': analysis,
            'suggested_category_id': str(suggested_category.id) if suggested_category else None,
            'suggested_category_name': suggested_category.name if suggested_category else None,
            'category_suggestions': category_suggestions,
            'success': True
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"AI analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {
                'error': 'Failed to analyze image',
                'details': str(e) if settings.DEBUG else 'Internal server error'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

