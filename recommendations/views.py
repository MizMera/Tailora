from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg
from datetime import datetime, timedelta

from .models import DailyRecommendation, UserPreferenceSignal
from .ai_engine import OutfitRecommendationEngine


@login_required
def daily_recommendations_view(request):
    """
    Display daily outfit recommendations for the user
    """
    user = request.user
    today = timezone.now().date()
    
    # Get today's recommendations
    recommendations = DailyRecommendation.objects.filter(
        user=user,
        recommendation_date=today
    ).select_related('outfit').prefetch_related('outfit__items__category')
    
    # If no recommendations exist, generate them
    if not recommendations.exists():
        try:
            engine = OutfitRecommendationEngine(user)
            recommendations = engine.generate_daily_recommendations(date=today, count=3)
            messages.success(request, f'Generated {len(recommendations)} new recommendations for you!')
        except Exception as e:
            messages.error(request, f'Could not generate recommendations: {str(e)}')
            recommendations = []
    
    # Get past recommendations for history
    past_recommendations = DailyRecommendation.objects.filter(
        user=user,
        recommendation_date__lt=today,
        status__in=['accepted', 'worn']
    ).select_related('outfit').order_by('-recommendation_date')[:10]
    
    context = {
        'recommendations': recommendations,
        'past_recommendations': past_recommendations,
        'today': today,
    }
    
    return render(request, 'recommendations/daily.html', context)


@login_required
@require_POST
def accept_recommendation_view(request, recommendation_id):
    """
    User accepts a recommendation
    """
    recommendation = get_object_or_404(
        DailyRecommendation,
        id=recommendation_id,
        user=request.user
    )
    
    engine = OutfitRecommendationEngine(request.user)
    engine.record_feedback(recommendation, 'accepted')
    
    messages.success(request, f'Great choice! "{recommendation.outfit.name}" added to your outfits.')
    
    # Check if request is AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Recommendation accepted'
        })
    
    return redirect('recommendations:daily')


@login_required
@require_POST
def reject_recommendation_view(request, recommendation_id):
    """
    User rejects a recommendation
    """
    recommendation = get_object_or_404(
        DailyRecommendation,
        id=recommendation_id,
        user=request.user
    )
    
    engine = OutfitRecommendationEngine(request.user)
    engine.record_feedback(recommendation, 'rejected')
    
    messages.info(request, 'Recommendation dismissed. We\'ll learn from your preferences!')
    
    # Check if request is AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Recommendation rejected'
        })
    
    return redirect('recommendations:daily')


@login_required
@require_POST
def rate_recommendation_view(request, recommendation_id):
    """
    User rates a recommendation
    """
    recommendation = get_object_or_404(
        DailyRecommendation,
        id=recommendation_id,
        user=request.user
    )
    
    rating = request.POST.get('rating')
    feedback = request.POST.get('feedback', '')
    
    try:
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        
        engine = OutfitRecommendationEngine(request.user)
        engine.record_feedback(
            recommendation,
            status='viewed',
            rating=rating,
            feedback_text=feedback
        )
        
        messages.success(request, 'Thank you for your feedback!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Rating saved'
            })
        
    except (ValueError, TypeError) as e:
        messages.error(request, f'Invalid rating: {str(e)}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return redirect('recommendations:daily')


@login_required
def recommendation_history_view(request):
    """
    View all past recommendations
    """
    recommendations = DailyRecommendation.objects.filter(
        user=request.user
    ).select_related('outfit').order_by('-recommendation_date', 'priority')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        recommendations = recommendations.filter(status=status_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            recommendations = recommendations.filter(recommendation_date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            recommendations = recommendations.filter(recommendation_date__lte=date_to)
        except ValueError:
            pass
    
    # Stats
    stats = {
        'total': recommendations.count(),
        'accepted': recommendations.filter(status='accepted').count(),
        'rejected': recommendations.filter(status='rejected').count(),
        'worn': recommendations.filter(status='worn').count(),
        'avg_confidence': recommendations.aggregate(avg=Avg('confidence_score'))['avg'] or 0,
    }
    
    context = {
        'recommendations': recommendations[:50],  # Limit to 50
        'stats': stats,
        'status_choices': DailyRecommendation.STATUS_CHOICES,
        'selected_status': status_filter,
    }
    
    return render(request, 'recommendations/history.html', context)


@login_required
@require_POST
def generate_new_recommendations_view(request):
    """
    Manually trigger generation of new recommendations
    """
    user = request.user
    today = timezone.now().date()
    
    # Check if recommendations already exist
    existing = DailyRecommendation.objects.filter(
        user=user,
        recommendation_date=today
    )
    
    if existing.exists():
        existing.delete()
    
    try:
        engine = OutfitRecommendationEngine(user)
        recommendations = engine.generate_daily_recommendations(date=today, count=3)
        messages.success(request, f'Generated {len(recommendations)} fresh recommendations!')
    except Exception as e:
        messages.error(request, f'Error generating recommendations: {str(e)}')
    
    return redirect('recommendations:daily')

