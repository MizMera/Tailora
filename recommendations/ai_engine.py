"""
AI Recommendation Engine for Tailora
Generates intelligent outfit recommendations based on:
- User style preferences
- Weather conditions
- Occasion
- Color theory
- Past behavior
- Wardrobe items
"""

from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import random
from typing import List, Dict, Tuple
from collections import defaultdict

from wardrobe.models import ClothingItem
from outfits.models import Outfit, OutfitItem
from users.models import StyleProfile
from .models import (
    DailyRecommendation,
    UserPreferenceSignal,
    ColorCompatibility,
    StyleRule
)


class OutfitRecommendationEngine:
    """
    Core AI engine for generating outfit recommendations
    """
    
    def __init__(self, user):
        self.user = user
        self.style_profile = getattr(user, 'style_profile', None)
        self.wardrobe_items = ClothingItem.objects.filter(
            user=user,
            status='available'
        ).select_related('category')
        
    def generate_daily_recommendations(self, date=None, count=3):
        """
        Generate N outfit recommendations for a specific date
        
        Args:
            date: The date to generate recommendations for (default: today)
            count: Number of recommendations to generate
            
        Returns:
            List of DailyRecommendation objects
        """
        if date is None:
            date = timezone.now().date()
            
        # Get user preferences
        preferences = self._analyze_user_preferences()
        
        # Get available wardrobe items
        if not self.wardrobe_items.exists():
            return []
            
        # Generate multiple outfit combinations
        candidate_outfits = self._generate_outfit_combinations(count * 3)
        
        # Score each outfit
        scored_outfits = []
        for outfit_items in candidate_outfits:
            score_data = self._score_outfit(outfit_items, preferences)
            scored_outfits.append((outfit_items, score_data))
        
        # Sort by total score
        scored_outfits.sort(key=lambda x: x[1]['total_score'], reverse=True)
        
        # Create recommendations for top N
        recommendations = []
        for i, (outfit_items, score_data) in enumerate(scored_outfits[:count]):
            # Create or get outfit
            outfit = self._create_outfit_from_items(outfit_items, f"Recommended Outfit {date}")
            
            # Create recommendation
            recommendation = DailyRecommendation.objects.create(
                user=self.user,
                outfit=outfit,
                recommendation_date=date,
                priority=i,
                reason=score_data['reason'],
                confidence_score=score_data['total_score'],
                style_match_score=score_data['style_score'],
                occasion_match=score_data.get('occasion', '')
            )
            recommendations.append(recommendation)
            
        return recommendations
    
    def _analyze_user_preferences(self):
        """
        Analyze user's past behavior to understand preferences
        
        Returns:
            Dict of preference scores
        """
        preferences = {
            'favorite_colors': [],
            'favorite_categories': [],
            'preferred_occasions': [],
            'style_preferences': {},
            'color_weights': defaultdict(float),
            'category_weights': defaultdict(float),
        }
        
        # Analyze favorite items
        favorite_items = self.wardrobe_items.filter(favorite=True)
        for item in favorite_items:
            if item.color:
                preferences['color_weights'][item.color.lower()] += 2.0
            if item.category:
                preferences['category_weights'][item.category.name] += 1.5
        
        # Analyze worn outfits
        worn_outfits = Outfit.objects.filter(
            user=self.user,
            times_worn__gt=0
        ).prefetch_related('items')
        
        for outfit in worn_outfits:
            weight = min(outfit.times_worn * 0.5, 3.0)  # Cap at 3
            for item in outfit.items.all():
                if item.color:
                    preferences['color_weights'][item.color.lower()] += weight
                if item.category:
                    preferences['category_weights'][item.category.name] += weight * 0.5
        
        # Get top preferences
        if preferences['color_weights']:
            preferences['favorite_colors'] = sorted(
                preferences['color_weights'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        
        if preferences['category_weights']:
            preferences['favorite_categories'] = sorted(
                preferences['category_weights'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        
        # Add style profile preferences
        if self.style_profile:
            preferences['style_preferences'] = {
                'preferred_styles': self.style_profile.preferred_styles if hasattr(self.style_profile, 'preferred_styles') else [],
                'body_type': self.style_profile.body_type if hasattr(self.style_profile, 'body_type') else None,
                'color_palette': self.style_profile.color_palette if hasattr(self.style_profile, 'color_palette') else None,
            }
        
        return preferences
    
    def _generate_outfit_combinations(self, count=10):
        """
        Generate random outfit combinations from wardrobe
        
        Returns:
            List of item combinations
        """
        combinations = []
        items_by_category = defaultdict(list)
        
        # Group items by category
        for item in self.wardrobe_items:
            if item.category:
                items_by_category[item.category.name].append(item)
        
        # Essential categories for a complete outfit
        essential_categories = ['Tops', 'Bottoms']
        optional_categories = ['Shoes', 'Outerwear', 'Accessories']
        
        # Generate combinations
        attempts = 0
        max_attempts = count * 5
        
        while len(combinations) < count and attempts < max_attempts:
            attempts += 1
            outfit_items = []
            
            # Pick essential items
            for cat in essential_categories:
                if cat in items_by_category and items_by_category[cat]:
                    item = random.choice(items_by_category[cat])
                    outfit_items.append(item)
            
            # Skip if missing essentials
            if len(outfit_items) < len(essential_categories):
                continue
            
            # Add some optional items (30% chance for each)
            for cat in optional_categories:
                if cat in items_by_category and items_by_category[cat]:
                    if random.random() < 0.3:
                        item = random.choice(items_by_category[cat])
                        outfit_items.append(item)
            
            # Avoid duplicates
            item_ids = tuple(sorted([item.id for item in outfit_items]))
            if item_ids not in [tuple(sorted([i.id for i in combo])) for combo in combinations]:
                combinations.append(outfit_items)
        
        return combinations
    
    def _score_outfit(self, items: List[ClothingItem], preferences: Dict) -> Dict:
        """
        Score an outfit combination based on multiple factors
        
        Returns:
            Dict with scores and reasoning
        """
        scores = {
            'color_harmony': 0.0,
            'style_consistency': 0.0,
            'personal_preference': 0.0,
            'season_match': 0.0,
            'total_score': 0.0,
            'reason': '',
            'style_score': 0.0,
            'occasion': ''
        }
        
        # 1. Color Harmony Score (30% weight)
        colors = [item.color.lower() for item in items if item.color]
        if len(colors) >= 2:
            color_score = self._calculate_color_harmony(colors)
            scores['color_harmony'] = color_score * 0.3
        
        # 2. Personal Preference Score (40% weight)
        pref_score = 0.0
        for item in items:
            # Favorite item bonus
            if item.favorite:
                pref_score += 0.5
            
            # Preferred color bonus
            if item.color and item.color.lower() in preferences['color_weights']:
                pref_score += preferences['color_weights'][item.color.lower()] * 0.1
            
            # Preferred category bonus
            if item.category and item.category.name in preferences['category_weights']:
                pref_score += preferences['category_weights'][item.category.name] * 0.1
        
        # Normalize preference score
        scores['personal_preference'] = min(pref_score / len(items), 1.0) * 0.4
        
        # 3. Style Consistency Score (20% weight)
        if self.style_profile and hasattr(self.style_profile, 'preferred_styles') and self.style_profile.preferred_styles:
            # Simple heuristic: items with tags matching any preferred style
            matching_items = sum(1 for item in items if item.style_tags and 
                               any(style.lower() in [t.lower() for t in item.style_tags] 
                                   for style in self.style_profile.preferred_styles))
            scores['style_consistency'] = (matching_items / len(items)) * 0.2
        
        # 4. Season Match Score (10% weight)
        current_season = self._get_current_season()
        season_matches = sum(1 for item in items if item.seasons and current_season in item.seasons)
        scores['season_match'] = (season_matches / len(items)) * 0.1
        
        # Calculate total
        scores['total_score'] = sum([
            scores['color_harmony'],
            scores['style_consistency'],
            scores['personal_preference'],
            scores['season_match']
        ])
        
        scores['style_score'] = scores['total_score']
        
        # Generate reason
        reasons = []
        if scores['color_harmony'] > 0.2:
            reasons.append("harmonious colors")
        if scores['personal_preference'] > 0.25:
            reasons.append("matches your style")
        if scores['season_match'] > 0.05:
            reasons.append(f"perfect for {current_season}")
        
        if reasons:
            scores['reason'] = f"Recommended because it has {', '.join(reasons)}."
        else:
            scores['reason'] = "A fresh combination from your wardrobe."
        
        return scores
    
    def _calculate_color_harmony(self, colors: List[str]) -> float:
        """
        Calculate how well colors work together
        Uses color compatibility database
        
        Returns:
            Harmony score 0-1
        """
        if len(colors) < 2:
            return 0.5
        
        # Get all color pairs
        total_score = 0.0
        pair_count = 0
        
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                color1 = colors[i]
                color2 = colors[j]
                
                # Check compatibility database
                compat = ColorCompatibility.objects.filter(
                    Q(color1__iexact=color1, color2__iexact=color2) |
                    Q(color1__iexact=color2, color2__iexact=color1)
                ).first()
                
                if compat:
                    total_score += compat.compatibility_score
                else:
                    # Default neutral score for unknown pairs
                    total_score += 0.5
                
                pair_count += 1
        
        return total_score / pair_count if pair_count > 0 else 0.5
    
    def _get_current_season(self) -> str:
        """
        Determine current season based on date
        """
        month = timezone.now().month
        
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
    
    def _create_outfit_from_items(self, items: List[ClothingItem], name: str) -> Outfit:
        """
        Create an Outfit object from a list of items
        """
        # Check if this exact combination exists
        item_ids = set(item.id for item in items)
        
        existing_outfits = Outfit.objects.filter(user=self.user).prefetch_related('items')
        for outfit in existing_outfits:
            if set(outfit.items.values_list('id', flat=True)) == item_ids:
                return outfit
        
        # Create new outfit
        outfit = Outfit.objects.create(
            user=self.user,
            name=name,
            source='ai_recommended',
            occasion='casual'
        )
        
        # Add items
        for idx, item in enumerate(items):
            OutfitItem.objects.create(
                outfit=outfit,
                clothing_item=item,
                position=idx
            )
        
        return outfit
    
    def record_feedback(self, recommendation, status, rating=None, feedback_text=''):
        """
        Record user feedback on a recommendation
        Creates preference signals for learning
        """
        # Update recommendation
        recommendation.status = status
        if rating:
            recommendation.user_rating = rating
        if feedback_text:
            recommendation.user_feedback = feedback_text
        recommendation.save()
        
        # Create preference signal
        signal_type = f'recommendation_{status}'
        signal_value = {
            'accepted': 1.0,
            'rejected': -0.5,
            'worn': 2.0,
        }.get(status, 0.0)
        
        if rating:
            signal_value += (rating - 3) * 0.5  # -1 to +1 based on 1-5 rating
        
        UserPreferenceSignal.objects.create(
            user=self.user,
            signal_type=signal_type,
            signal_value=signal_value,
            outfit=recommendation.outfit,
            context={
                'recommendation_id': str(recommendation.id),
                'confidence_score': recommendation.confidence_score,
                'reason': recommendation.reason,
            }
        )
