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
from wardrobe.models import ClothingItem


@login_required
def daily_recommendations_view(request):
    """
    Display comprehensive AI recommendations including weather-aware outfits,
    shopping suggestions, and wardrobe analysis
    """
    user = request.user
    today = timezone.now().date()
    
    # Get today's recommendations (weather-aware)
    recommendations = DailyRecommendation.objects.filter(
        user=user,
        recommendation_date=today
    ).select_related('outfit').prefetch_related('outfit__items__category')
    
    # If no recommendations exist, generate weather-aware ones
    if not recommendations.exists():
        try:
            engine = OutfitRecommendationEngine(user)
            recommendations = engine.generate_weather_recommendations(
                date=today,
                location="Tunis,TN",
                count=3
            )
            if recommendations:
                messages.success(request, f'Generated {len(recommendations)} weather-aware recommendations!')
        except Exception as e:
            messages.error(request, f'Could not generate recommendations: {str(e)}')
            recommendations = []
    
    # Get shopping suggestions
    shopping_suggestions = []
    try:
        from recommendations.models import ShoppingRecommendation
        shopping_suggestions = ShoppingRecommendation.objects.filter(
            user=user,
            is_purchased=False,
            is_dismissed=False
        ).order_by('-priority', '-versatility_score')[:5]
        
        # Generate if none exist
        if not shopping_suggestions.exists():
            engine = OutfitRecommendationEngine(user)
            shopping_suggestions = engine.suggest_shopping_items(max_suggestions=5)
    except Exception as e:
        print(f"Error fetching shopping suggestions: {str(e)}")
    
    # Get wardrobe analysis
    wardrobe_analysis = {
        'total_items': 0,
        'versatility_score': 0,
        'category_distribution': {},
        'color_distribution': {},
        'underutilized_items': [],
        'wardrobe_health': 'Loading...'
    }
    
    try:
        from collections import defaultdict
        items = ClothingItem.objects.filter(user=user, status='available')
        
        category_counts = defaultdict(int)
        color_counts = defaultdict(int)
        underutilized = []
        
        for item in items:
            if item.category:
                category_counts[item.category.name] += 1
            if item.color:
                color_counts[item.color] += 1
            if item.times_worn == 0:
                underutilized.append(item)
        
        total_items = items.count()
        versatility_score = min(total_items / 20.0, 1.0) * 100
        
        wardrobe_analysis = {
            'total_items': total_items,
            'versatility_score': int(versatility_score),
            'category_distribution': dict(category_counts),
            'color_distribution': dict(color_counts),
            'underutilized_items': underutilized[:5],
            'wardrobe_health': 'Excellent' if versatility_score > 80 else 
                              'Good' if versatility_score > 50 else 'Needs Expansion'
        }
    except Exception as e:
        print(f"Error analyzing wardrobe: {str(e)}")
    
    # Get weather info
    from planner.weather_service import WeatherService
    weather_service = WeatherService()
    current_weather = weather_service.get_current_weather("Tunis,TN")
    
    # Get past recommendations for history
    past_recommendations = DailyRecommendation.objects.filter(
        user=user,
        recommendation_date__lt=today,
        status__in=['accepted', 'worn']
    ).select_related('outfit').order_by('-recommendation_date')[:10]
    
    context = {
        'recommendations': recommendations,
        'past_recommendations': past_recommendations,
        'shopping_suggestions': shopping_suggestions,
        'wardrobe_analysis': wardrobe_analysis,
        'current_weather': current_weather,
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


# ==================== REST API Views ====================

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import DailyRecommendation, ColorCompatibility, StyleRule
from .serializers import (
    DailyRecommendationSerializer,
    ColorCompatibilitySerializer,
    StyleRuleSerializer
)
from .ai_engine import OutfitRecommendationEngine


class RecommendationPagination(PageNumberPagination):
    """Custom pagination for recommendations"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class RecommendationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for daily outfit recommendations
    
    Endpoints:
    - GET /api/recommendations/ - List recommendations
    - GET /api/recommendations/{id}/ - Get details
    
    Custom actions:
    - POST /api/recommendations/generate/ - Generate new recommendations
    - POST /api/recommendations/{id}/accept/ - Accept recommendation
    - POST /api/recommendations/{id}/reject/ - Reject recommendation
    - POST /api/recommendations/{id}/rate/ - Rate recommendation
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DailyRecommendationSerializer
    pagination_class = RecommendationPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_accepted', 'is_rejected', 'recommendation_date']
    ordering_fields = ['recommendation_date', 'score']
    ordering = ['-recommendation_date', '-score']
    
    def get_queryset(self):
        """Users can only access their own recommendations"""
        return DailyRecommendation.objects.filter(
            user=self.request.user
        ).select_related('outfit')
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate new recommendations for today
        POST /api/recommendations/generate/
        """
        user = request.user
        today = timezone.now().date()
        
        # Check if recommendations already exist
        existing = DailyRecommendation.objects.filter(
            user=user,
            recommendation_date=today
        )
        
        if existing.exists() and not request.data.get('force', False):
            serializer = self.get_serializer(existing, many=True)
            return Response({
                'message': 'Recommendations already exist for today',
                'recommendations': serializer.data
            })
        
        # Delete existing if force=True
        if existing.exists():
            existing.delete()
        
        try:
            engine = OutfitRecommendationEngine(user)
            recommendations = engine.generate_daily_recommendations(date=today, count=3)
            serializer = self.get_serializer(recommendations, many=True)
            return Response({
                'message': f'Generated {len(recommendations)} recommendations',
                'recommendations': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Error generating recommendations: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept a recommendation
        POST /api/recommendations/{id}/accept/
        """
        recommendation = self.get_object()
        
        engine = OutfitRecommendationEngine(request.user)
        engine.record_feedback(recommendation, 'accepted')
        
        return Response({
            'status': 'success',
            'message': 'Recommendation accepted'
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a recommendation
        POST /api/recommendations/{id}/reject/
        """
        recommendation = self.get_object()
        
        engine = OutfitRecommendationEngine(request.user)
        engine.record_feedback(recommendation, 'rejected')
        
        return Response({
            'status': 'success',
            'message': 'Recommendation rejected'
        })
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """
        Rate a recommendation
        POST /api/recommendations/{id}/rate/
        Body: {"rating": 5, "feedback": "Great match!"}
        """
        recommendation = self.get_object()
        rating = request.data.get('rating')
        feedback = request.data.get('feedback', '')
        
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
            
            return Response({
                'status': 'success',
                'message': 'Rating saved'
            })
            
        except (ValueError, TypeError) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def weather_recommendations(self, request):
        """
        Generate weather-aware recommendations
        POST /api/recommendations/weather_recommendations/
        Body: {"date": "2025-11-27", "location": "Tunis,TN", "count": 3}
        """
        user = request.user
        date_str = request.data.get('date')
        location = request.data.get('location', 'Tunis,TN')
        count = int(request.data.get('count', 3))
        
        # Parse date
        if date_str:
            from datetime import datetime
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            date = timezone.now().date()
        
        try:
            engine = OutfitRecommendationEngine(user)
            recommendations = engine.generate_weather_recommendations(date, location, count)
            serializer = self.get_serializer(recommendations, many=True)
            return Response({
                'message': f'Generated {len(recommendations)} weather-aware recommendations',
                'location': location,
                'date': date.isoformat(),
                'recommendations': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Error generating recommendations: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def shopping_suggestions(self, request):
        """
        Get AI shopping suggestions
        GET /api/recommendations/shopping_suggestions/?max=5
        """
        user = request.user
        max_suggestions = int(request.query_params.get('max', 5))
        
        try:
            engine = OutfitRecommendationEngine(user)
            suggestions = engine.suggest_shopping_items(max_suggestions)
            
            # Serialize suggestions
            from recommendations.serializers import ShoppingRecommendationSerializer
            serializer = ShoppingRecommendationSerializer(suggestions, many=True)
            
            return Response({
                'message': f'Found {len(suggestions)} shopping suggestions',
                'suggestions': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Error generating suggestions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def wardrobe_analysis(self, request):
        """
        Analyze wardrobe for gaps and insights
        GET /api/recommendations/wardrobe_analysis/
        """
        user = request.user
        from collections import defaultdict
        
        # Get wardrobe items
        items = ClothingItem.objects.filter(user=user, status='available')
        
        # Analyze categories
        category_counts = defaultdict(int)
        color_counts = defaultdict(int)
        underutilized = []
        
        for item in items:
            if item.category:
                category_counts[item.category.name] += 1
            if item.color:
                color_counts[item.color] += 1
            if item.times_worn == 0:
                underutilized.append({
                    'id': str(item.id),
                    'name': item.name,
                    'category': item.category.name if item.category else None
                })
        
        # Calculate versatility score
        total_items = items.count()
        versatility_score = min(total_items / 20.0, 1.0)  # Scale: 20 items = 100%
        
        return Response({
            'total_items': total_items,
            'versatility_score': round(versatility_score * 100),
            'category_distribution': dict(category_counts),
            'color_distribution': dict(color_counts),
            'underutilized_items': underutilized[:10],
            'wardrobe_health': 'Excellent' if versatility_score > 0.8 else 
                              'Good' if versatility_score > 0.5 else 'Needs Expansion'
        })


class ColorCompatibilityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for color compatibility rules (Read Only)
    """
    queryset = ColorCompatibility.objects.all()
    serializer_class = ColorCompatibilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = RecommendationPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['color1', 'color2']


class StyleRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for style rules (Read Only)
    """
    queryset = StyleRule.objects.all()
    serializer_class = StyleRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = RecommendationPagination


