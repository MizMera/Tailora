from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
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
        # SQLite doesn't support JSON contains, so we filter in Python if needed
        # or use icontains on the JSON field as a string workaround
        items = items.filter(seasons__icontains=season_filter)
    
    if status_filter:
        items = items.filter(status=status_filter)
    
    if show_favorites:
        items = items.filter(favorite=True)
    
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(color__icontains=search_query) |
            Q(category__name__icontains=search_query)
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
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'wardrobe/wardrobe_list_partial.html', context)
    
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
            f"You've reached your wardrobe limit of {max_items} items. Upgrade to Premium to add more!"
        )
        return redirect('wardrobe:wardrobe_gallery')
    
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
            return render(request, 'wardrobe_upload.html', {'categories': get_categories(user), 'remaining_slots': max_items - current_count, 'max_items': max_items})
        
        # Validate image
        if image.size > 5 * 1024 * 1024:  # 5MB
            messages.error(request, "Image size must not exceed 5 MB.")
            return render(request, 'wardrobe_upload.html', {'categories': get_categories(user), 'remaining_slots': max_items - current_count, 'max_items': max_items})
        
        # Process and optimize image
        try:
            processed_image = optimize_image(image)
        except Exception as e:
            messages.error(request, f"Error processing image: {str(e)}")
            return render(request, 'wardrobe_upload.html', {'categories': get_categories(user), 'remaining_slots': max_items - current_count, 'max_items': max_items})
        
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
            return redirect('wardrobe:wardrobe_detail', item_id=item.id)
        
        except Exception as e:
            messages.error(request, f"Error adding item: {str(e)}")
            return render(request, 'wardrobe_upload.html', {'categories': get_categories(user), 'remaining_slots': max_items - current_count, 'max_items': max_items})
    
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
        return redirect('wardrobe:wardrobe_detail', item_id=item.id)
    
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
        return redirect('wardrobe:wardrobe_gallery')
    
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
    
    return redirect(request.META.get('HTTP_REFERER', 'wardrobe:wardrobe_gallery'))


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
        'underutilized_items': [],
        'total_value': 0,
        'secondhand_percentage': 0,
    }
    
    # Group by category
    category_counts = items.values('category__name').annotate(count=Count('id'))
    for item in category_counts:
        if item['category__name']:
            stats['by_category'][item['category__name']] = item['count']
    
    # Group by color
    color_counts = items.values('color').annotate(count=Count('id')).order_by('-count')[:10]
    for item in color_counts:
        stats['by_color'][item['color']] = item['count']
    
    # Calculate total value and second-hand percentage
    items_with_prices = items.exclude(purchase_price__isnull=True)
    if items_with_prices.exists():
        stats['total_value'] = items_with_prices.aggregate(total=Sum('purchase_price'))['total'] or 0
    
    secondhand_count = items.filter(is_secondhand=True).count()
    if stats['total_items'] > 0:
        stats['secondhand_percentage'] = round((secondhand_count / stats['total_items']) * 100, 1)
    # Most worn items with cost per wear
    most_worn_items = items.filter(times_worn__gt=0).order_by('-times_worn')[:5]
    stats['most_worn'] = []
    for item in most_worn_items:
        cost_per_wear = None
        if item.purchase_price and item.times_worn > 0:
            cost_per_wear = round(float(item.purchase_price) / item.times_worn, 2)
        stats['most_worn'].append({
            'name': item.name,
            'times_worn': item.times_worn,
            'image': item.image.url if item.image else None,
            'cost_per_wear': cost_per_wear,
        })
    
    # Underutilized items (low wear count, purchased more than 30 days ago)
    from django.utils import timezone
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)
    underutilized = items.filter(
        times_worn__lte=2,
        created_at__lte=thirty_days_ago
    ).order_by('times_worn', '-created_at')[:5]
    stats['underutilized_items'] = []
    for item in underutilized:
        stats['underutilized_items'].append({
            'name': item.name,
            'times_worn': item.times_worn,
            'image': item.image.url if item.image else None,
            'days_owned': (timezone.now().date() - item.created_at.date()).days,
        })
    
    # Recent additions - need image URLs not just paths
    recent_items = items.order_by('-created_at')[:5]
    stats['recent_additions'] = []
    for item in recent_items:
        stats['recent_additions'].append({
            'id': str(item.id),
            'name': item.name,
            'created_at': item.created_at,
            'image': item.image.url if item.image else None,
        })
    
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
    user = request.user
    current_count = ClothingItem.objects.filter(user=user).count()
    max_items = user.get_max_wardrobe_items()

    if current_count >= max_items:
        return Response(
            {'error': f"You've reached your wardrobe limit of {max_items} items. Upgrade to Premium to add more!"},
            status=status.HTTP_403_FORBIDDEN
        )

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

        # AUTO-DETECT category using new detector
        from .category_detector import CategoryDetector
        
        # Try to detect from item_type or category
        ai_text = analysis.get('item_type', '') + ' ' + analysis.get('category', '')
        detected_category = CategoryDetector.detect_category(ai_text, user=request.user)
        
        response_data = {
            'analysis': analysis,
            'suggested_category_id': str(detected_category.id) if detected_category else None,
            'suggested_category_name': detected_category.name if detected_category else None,
            'auto_detected': detected_category is not None,
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


# ==================== Laundry Scheduling Views ====================

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .laundry_scheduler import LaundrySchedulerAI
import json


@login_required
def laundry_dashboard(request):
    """
    Display laundry management dashboard
    Shows items needing wash, items at laundry, and upcoming conflicts
    """
    scheduler = LaundrySchedulerAI(request.user)
    summary = scheduler.get_laundry_summary()
    
    # Get items grouped by urgency
    needs_wash = summary['needs_wash_items']
    approaching = summary['approaching_items']
    at_laundry = summary['at_laundry']
    
    # Separate needs_wash into overdue and regular
    overdue = [item for item in needs_wash if item.urgency_level() >= 3]
    needs_wash_now = [item for item in needs_wash if item.urgency_level() == 2]
    
    context = {
        'overdue_items': overdue,
        'needs_wash_items': needs_wash_now,
        'approaching_items': approaching,
        'washing_items': at_laundry.get('washing', []),
        'drying_items': at_laundry.get('drying', []),
        'dry_cleaning_items': at_laundry.get('dry_cleaning', []),
        'active_alerts': summary['active_alerts'],
        'stats': {
            'overdue_count': len(overdue),
            'needs_wash_count': len(needs_wash_now),
            'approaching_count': summary['approaching_count'],
            'at_laundry_count': summary['at_laundry_count'],
            'urgent_alerts': summary['urgent_alerts_count'],
        },
    }
    
    return render(request, 'wardrobe/laundry_dashboard.html', context)


@login_required
@require_POST
def mark_item_washed(request, item_id):
    """Mark a clothing item as washed"""
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
    scheduler = LaundrySchedulerAI(request.user)
    scheduler.mark_item_washed(item)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'"{item.name}" marked as washed!',
            'wears_since_wash': item.wears_since_wash,
        })
    
    messages.success(request, f'"{item.name}" marked as washed!')
    return redirect(request.META.get('HTTP_REFERER', 'wardrobe:laundry_dashboard'))


@login_required
@require_POST
def update_item_laundry_settings(request, item_id):
    """Update laundry settings for a specific item"""
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = request.POST.dict()
    
    # Update max wears before wash
    if 'max_wears' in data:
        try:
            max_wears = int(data['max_wears'])
            if 1 <= max_wears <= 50:
                item.max_wears_before_wash = max_wears
        except (ValueError, TypeError):
            pass
    
    # Update care type
    if 'care_type' in data:
        if data['care_type'] in dict(ClothingItem.CARE_TYPE_CHOICES):
            item.care_type = data['care_type']
    
    # Update drying time
    if 'drying_time' in data:
        try:
            drying_time = int(data['drying_time'])
            if 1 <= drying_time <= 168:  # 1 hour to 1 week
                item.drying_time_hours = drying_time
        except (ValueError, TypeError):
            pass
    
    item.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Laundry settings updated!',
            'max_wears_before_wash': item.max_wears_before_wash,
            'care_type': item.care_type,
            'drying_time_hours': item.drying_time_hours,
        })
    
    messages.success(request, 'Laundry settings updated!')
    return redirect('wardrobe:wardrobe_detail', item_id=item.id)


@login_required
@require_POST
def change_item_status(request, item_id):
    """Change item status (available, washing, drying, etc.)"""
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = request.POST.dict()
    
    new_status = data.get('status')
    
    if new_status in dict(ClothingItem.STATUS_CHOICES):
        item.status = new_status
        item.save()
        
        status_display = dict(ClothingItem.STATUS_CHOICES).get(new_status, new_status)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Status changed to "{status_display}"',
                'status': new_status,
                'status_display': status_display,
            })
        
        messages.success(request, f'Status changed to "{status_display}"')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Invalid status',
            }, status=400)
        messages.error(request, 'Invalid status')
    
    return redirect(request.META.get('HTTP_REFERER', 'wardrobe:laundry_dashboard'))


@login_required
def resolve_laundry_alert(request, alert_id):
    """Resolve a laundry alert"""
    from .models import LaundryAlert
    
    alert = get_object_or_404(LaundryAlert, id=alert_id, user=request.user)
    alert.resolve()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Alert resolved!',
        })
    
    messages.success(request, 'Alert resolved!')
    return redirect(request.META.get('HTTP_REFERER', 'wardrobe:laundry_dashboard'))


@login_required
def auto_set_all_thresholds(request):
    """Auto-set wash thresholds for all items based on AI recommendations"""
    scheduler = LaundrySchedulerAI(request.user)
    items = ClothingItem.objects.filter(user=request.user)
    
    updated_count = 0
    for item in items:
        if item.max_wears_before_wash == 3:  # Only update defaults
            scheduler.auto_set_wash_threshold(item)
            updated_count += 1
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Updated thresholds for {updated_count} items!',
            'updated_count': updated_count,
        })
    
    messages.success(request, f'Updated laundry thresholds for {updated_count} items!')
    return redirect('wardrobe:laundry_dashboard')
