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
            Q(style_tags__contains=[search_query])
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
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        occasion = request.POST.get('occasion', 'casual')
        item_ids = request.POST.getlist('items')  # List of clothing item IDs
        
        # Validation
        if not name:
            messages.error(request, 'Le nom de la tenue est requis.')
            return redirect('outfits:outfit_create')
        
        if not item_ids or len(item_ids) < 2:
            messages.error(request, 'Veuillez sélectionner au moins 2 articles pour créer une tenue.')
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
            
            messages.success(request, f'{name} a été créé avec succès!')
            return redirect('outfits:outfit_detail', outfit_id=outfit.id)
        
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {str(e)}')
            return redirect('outfits:outfit_create')
    
    # GET request - show wardrobe items to select from
    wardrobe_items = ClothingItem.objects.filter(user=user, status='available')
    
    # Group by category for easier selection
    items_by_category = {}
    for item in wardrobe_items:
        if item.category:
            cat_name = item.category.name
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
        messages.success(request, f'{outfit.name} a été mis à jour!')
        return redirect('outfits:outfit_detail', outfit_id=outfit.id)
    
    # GET request
    current_items = outfit.items.all()
    wardrobe_items = ClothingItem.objects.filter(user=request.user, status='available')
    
    # Group by category
    items_by_category = {}
    for item in wardrobe_items:
        if item.category:
            cat_name = item.category.name
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
        messages.success(request, f'{outfit_name} a été supprimé.')
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
