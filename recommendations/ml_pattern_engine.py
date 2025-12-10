"""
ML Pattern Engine for Learning User Preferences

This engine tracks user interactions with outfit recommendations
and learns patterns to improve future suggestions.

Learning Signals:
- Accept outfit: +1.0 weight
- Reject/Swap: -0.5 weight  
- Mark as worn: +1.5 weight
- Regenerate day: -0.3 weight
"""

from django.db.models import Avg, Count, Sum, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import json

from users.models import User
from outfits.models import Outfit
from wardrobe.models import ClothingItem
from .models import UserPreferenceSignal


class MLPatternEngine:
    """
    Machine learning engine for personalizing outfit recommendations
    based on user acceptance/rejection patterns.
    """
    
    # Signal weights
    SIGNAL_WEIGHTS = {
        'recommendation_accepted': 1.0,
        'recommendation_rejected': -0.5,
        'outfit_worn': 1.5,
        'outfit_regenerated': -0.3,
        'outfit_rated': 0.5,  # Additional weight for ratings
    }
    
    # Time decay factor (signals lose relevance over time)
    DECAY_HALF_LIFE_DAYS = 30  # Signals half as important after 30 days
    
    def __init__(self, user: User):
        self.user = user
        self._cached_preferences = None
    
    # ==================== Signal Recording ====================
    
    def record_outfit_accepted(self, outfit: Outfit, slot=None, context: dict = None):
        """Record when user accepts an AI-suggested outfit"""
        context = context or {}
        context['slot_id'] = str(slot.id) if slot else None
        context['slot_date'] = str(slot.date) if slot else None
        
        # Record outfit-level signal
        UserPreferenceSignal.objects.create(
            user=self.user,
            signal_type='recommendation_accepted',
            signal_value=self.SIGNAL_WEIGHTS['recommendation_accepted'],
            outfit=outfit,
            context=context
        )
        
        # Record item-level signals (each item in the outfit gets positive signal)
        for item in outfit.items.all():
            self._record_item_signal(
                item, 
                'recommendation_accepted', 
                self.SIGNAL_WEIGHTS['recommendation_accepted'] * 0.5,
                context
            )
    
    def record_outfit_rejected(self, outfit: Outfit, slot=None, context: dict = None):
        """Record when user rejects/swaps away from an outfit"""
        context = context or {}
        context['slot_id'] = str(slot.id) if slot else None
        context['rejection_reason'] = context.get('reason', 'swapped')
        
        UserPreferenceSignal.objects.create(
            user=self.user,
            signal_type='recommendation_rejected',
            signal_value=self.SIGNAL_WEIGHTS['recommendation_rejected'],
            outfit=outfit,
            context=context
        )
        
        # Record item-level negative signals
        for item in outfit.items.all():
            self._record_item_signal(
                item,
                'recommendation_rejected',
                self.SIGNAL_WEIGHTS['recommendation_rejected'] * 0.3,
                context
            )
    
    def record_outfit_worn(self, outfit: Outfit, context: dict = None):
        """Record when user actually wears an outfit (strongest positive signal)"""
        context = context or {}
        
        UserPreferenceSignal.objects.create(
            user=self.user,
            signal_type='outfit_worn',
            signal_value=self.SIGNAL_WEIGHTS['outfit_worn'],
            outfit=outfit,
            context=context
        )
        
        # Strong positive signal for each item worn
        for item in outfit.items.all():
            self._record_item_signal(
                item,
                'outfit_worn',
                self.SIGNAL_WEIGHTS['outfit_worn'] * 0.7,
                context
            )
    
    def record_regeneration(self, slot=None, context: dict = None):
        """Record when user regenerates a day's outfit suggestion"""
        context = context or {}
        context['slot_id'] = str(slot.id) if slot else None
        
        UserPreferenceSignal.objects.create(
            user=self.user,
            signal_type='outfit_regenerated',
            signal_value=self.SIGNAL_WEIGHTS['outfit_regenerated'],
            outfit=slot.primary_outfit if slot else None,
            context=context
        )
    
    def _record_item_signal(self, item: ClothingItem, signal_type: str, 
                           value: float, context: dict):
        """Record a signal for an individual clothing item"""
        item_context = context.copy() if context else {}
        item_context['item_category'] = item.category.name if item.category else None
        item_context['item_color'] = item.color
        item_context['item_occasions'] = item.occasions
        
        UserPreferenceSignal.objects.create(
            user=self.user,
            signal_type=signal_type,
            signal_value=value,
            clothing_item=item,
            context=item_context
        )
    
    # ==================== Pattern Analysis ====================
    
    def analyze_color_preferences(self) -> dict:
        """Analyze which colors the user prefers based on accept/reject patterns"""
        # Get signals with color context
        signals = UserPreferenceSignal.objects.filter(
            user=self.user,
            clothing_item__isnull=False
        ).select_related('clothing_item').order_by('-created_at')[:500]
        
        color_scores = defaultdict(float)
        color_counts = defaultdict(int)
        
        for signal in signals:
            if signal.clothing_item and signal.clothing_item.color:
                color = signal.clothing_item.color.lower()
                decay = self._calculate_time_decay(signal.created_at)
                color_scores[color] += signal.signal_value * decay
                color_counts[color] += 1
        
        # Normalize scores
        preferences = {}
        for color, score in color_scores.items():
            if color_counts[color] >= 2:  # Minimum signals for reliability
                preferences[color] = {
                    'score': round(score / color_counts[color], 3),
                    'count': color_counts[color],
                    'affinity': 'positive' if score > 0 else 'negative'
                }
        
        return dict(sorted(preferences.items(), key=lambda x: x[1]['score'], reverse=True))
    
    def analyze_style_preferences(self) -> dict:
        """Analyze preferred outfit styles/occasions"""
        signals = UserPreferenceSignal.objects.filter(
            user=self.user,
            outfit__isnull=False
        ).select_related('outfit').order_by('-created_at')[:300]
        
        occasion_scores = defaultdict(float)
        occasion_counts = defaultdict(int)
        
        for signal in signals:
            if signal.outfit and signal.outfit.occasion:
                occasion = signal.outfit.occasion
                decay = self._calculate_time_decay(signal.created_at)
                occasion_scores[occasion] += signal.signal_value * decay
                occasion_counts[occasion] += 1
        
        preferences = {}
        for occasion, score in occasion_scores.items():
            if occasion_counts[occasion] >= 2:
                avg_score = score / occasion_counts[occasion]
                preferences[occasion] = {
                    'score': round(avg_score, 3),
                    'count': occasion_counts[occasion],
                    'affinity': 'strong' if avg_score > 0.5 else 'moderate' if avg_score > 0 else 'weak'
                }
        
        return dict(sorted(preferences.items(), key=lambda x: x[1]['score'], reverse=True))
    
    def analyze_weather_preferences(self) -> dict:
        """Analyze preferences based on weather conditions at acceptance time"""
        signals = UserPreferenceSignal.objects.filter(
            user=self.user,
            signal_type__in=['recommendation_accepted', 'outfit_worn']
        ).order_by('-created_at')[:200]
        
        weather_prefs = defaultdict(lambda: {'accepts': 0, 'total': 0})
        
        for signal in signals:
            context = signal.context or {}
            temp = context.get('temperature')
            condition = context.get('weather_condition')
            
            if temp is not None:
                temp_range = self._get_temp_range(temp)
                weather_prefs[temp_range]['total'] += 1
                if signal.signal_value > 0:
                    weather_prefs[temp_range]['accepts'] += 1
        
        return {
            k: {
                'acceptance_rate': round(v['accepts'] / v['total'], 2) if v['total'] > 0 else 0,
                'sample_size': v['total']
            }
            for k, v in weather_prefs.items()
        }
    
    def _get_temp_range(self, temp: float) -> str:
        """Categorize temperature into ranges"""
        if temp < 10:
            return 'cold (<10°C)'
        elif temp < 18:
            return 'cool (10-18°C)'
        elif temp < 25:
            return 'warm (18-25°C)'
        else:
            return 'hot (>25°C)'
    
    # ==================== Scoring & Weights ====================
    
    def get_personalized_weights(self) -> dict:
        """Get personalized scoring weights based on user history"""
        total_signals = UserPreferenceSignal.objects.filter(
            user=self.user
        ).count()
        
        if total_signals < 10:
            # Not enough data, use defaults
            return {
                'weather': 0.30,
                'occasion': 0.25,
                'recency': 0.20,
                'style': 0.15,
                'preference': 0.10,
            }
        
        # Analyze patterns to adjust weights
        acceptance_rate = self._calculate_acceptance_rate()
        
        # Users who accept more might value variety, users who reject more
        # might have stronger preferences
        if acceptance_rate > 0.7:
            # High acceptor - variety is good
            return {
                'weather': 0.30,
                'occasion': 0.25,
                'recency': 0.25,  # More recency weight = more variety
                'style': 0.10,
                'preference': 0.10,
            }
        elif acceptance_rate < 0.4:
            # Picky user - lean into their preferences
            return {
                'weather': 0.25,
                'occasion': 0.20,
                'recency': 0.15,
                'style': 0.15,
                'preference': 0.25,  # More preference weight
            }
        else:
            # Balanced user
            return {
                'weather': 0.28,
                'occasion': 0.23,
                'recency': 0.18,
                'style': 0.13,
                'preference': 0.18,
            }
    
    def calculate_preference_boost(self, outfit: Outfit) -> float:
        """
        Calculate a personalized boost for an outfit based on learned preferences.
        Returns a value between -1.0 and 1.0
        """
        if not outfit:
            return 0.0
        
        signals = self._get_outfit_signals(outfit)
        color_prefs = self.analyze_color_preferences()
        style_prefs = self.analyze_style_preferences()
        
        boost = 0.0
        factors = 0
        
        # Outfit occasion preference
        if outfit.occasion in style_prefs:
            boost += style_prefs[outfit.occasion]['score'] * 0.4
            factors += 1
        
        # Item color preferences
        for item in outfit.items.all():
            if item.color and item.color.lower() in color_prefs:
                boost += color_prefs[item.color.lower()]['score'] * 0.2
                factors += 1
        
        # Historical outfit performance
        outfit_signals = signals.filter(outfit=outfit)
        if outfit_signals.exists():
            avg_signal = outfit_signals.aggregate(avg=Avg('signal_value'))['avg']
            boost += (avg_signal or 0) * 0.4
            factors += 1
        
        # Normalize
        if factors > 0:
            boost /= factors
        
        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, boost))
    
    def get_item_affinity_scores(self) -> dict:
        """Get affinity scores for individual items based on usage patterns"""
        item_signals = UserPreferenceSignal.objects.filter(
            user=self.user,
            clothing_item__isnull=False
        ).values('clothing_item').annotate(
            total_score=Sum('signal_value'),
            signal_count=Count('id')
        ).order_by('-total_score')
        
        return {
            str(item['clothing_item']): {
                'score': round(item['total_score'], 2),
                'interactions': item['signal_count']
            }
            for item in item_signals
        }
    
    # ==================== User Insights ====================
    
    def get_user_profile_insights(self) -> dict:
        """Generate insights about user's style patterns for dashboard display"""
        total_signals = UserPreferenceSignal.objects.filter(user=self.user).count()
        
        if total_signals < 5:
            return {
                'has_data': False,
                'message': "Keep using the weekly planner to help me learn your style!"
            }
        
        color_prefs = self.analyze_color_preferences()
        style_prefs = self.analyze_style_preferences()
        acceptance_rate = self._calculate_acceptance_rate()
        
        # Top colors
        top_colors = [c for c, v in list(color_prefs.items())[:3] if v['score'] > 0]
        
        # Top occasions
        top_occasions = [o for o, v in list(style_prefs.items())[:3] if v['score'] > 0]
        
        # Determine user type
        if acceptance_rate > 0.75:
            user_type = "Adventurous - You love trying new combinations!"
        elif acceptance_rate > 0.5:
            user_type = "Balanced - You know what you like but stay open"
        else:
            user_type = "Selective - You have refined taste"
        
        return {
            'has_data': True,
            'total_interactions': total_signals,
            'acceptance_rate': round(acceptance_rate * 100),
            'favorite_colors': top_colors,
            'favorite_occasions': top_occasions,
            'user_type': user_type,
            'personalized_weights': self.get_personalized_weights(),
        }
    
    # ==================== Helper Methods ====================
    
    def _calculate_time_decay(self, created_at) -> float:
        """Calculate time decay factor for a signal"""
        days_ago = (timezone.now() - created_at).days
        half_life = self.DECAY_HALF_LIFE_DAYS
        return 0.5 ** (days_ago / half_life)
    
    def _calculate_acceptance_rate(self) -> float:
        """Calculate overall acceptance rate"""
        accepted = UserPreferenceSignal.objects.filter(
            user=self.user,
            signal_type='recommendation_accepted'
        ).count()
        
        rejected = UserPreferenceSignal.objects.filter(
            user=self.user,
            signal_type='recommendation_rejected'
        ).count()
        
        total = accepted + rejected
        if total == 0:
            return 0.5  # Default to 50%
        
        return accepted / total
    
    def _get_outfit_signals(self, outfit: Outfit = None):
        """Get signals, optionally filtered by outfit"""
        qs = UserPreferenceSignal.objects.filter(user=self.user)
        if outfit:
            qs = qs.filter(outfit=outfit)
        return qs
