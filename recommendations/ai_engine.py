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
from users.models import FashionIQ, StyleCritiqueSession


class OutfitRecommendationEngine:
    """
    Core AI engine for generating outfit recommendations
    """
    
    def __init__(self, user):
        self.user = user
        self.style_profile = getattr(user, 'style_profile', None)
        
        # Filter wardrobe items: only 'available' AND not needing washing
        from django.db.models import F
        self.wardrobe_items = ClothingItem.objects.filter(
            user=user,
            status='available'
        ).exclude(
            # Exclude items that need washing (wears_since_wash >= max_wears_before_wash)
            wears_since_wash__gte=F('max_wears_before_wash')
        ).select_related('category')
        
    def generate_daily_recommendations(self, date=None, count=5):
        """
        Generate N outfit recommendations for a specific date
        Does NOT create actual outfits - just stores suggestions for user to confirm
        
        Args:
            date: The date to generate recommendations for (default: today)
            count: Number of recommendations to generate (default: 5)
            
        Returns:
            List of DailyRecommendation objects
        """
        if date is None:
            date = timezone.now().date()
            
        # Get user preferences
        preferences = self._analyze_user_preferences()
        
        # Get available wardrobe items (excluding items that need washing)
        if not self.wardrobe_items.exists():
            return []
            
        # Generate more outfit combinations for variety
        candidate_outfits = self._generate_outfit_combinations(count * 5)
        
        # Score each outfit
        scored_outfits = []
        for outfit_items in candidate_outfits:
            score_data = self._score_outfit(outfit_items, preferences)
            scored_outfits.append((outfit_items, score_data))
        
        # Sort by total score
        scored_outfits.sort(key=lambda x: x[1]['total_score'], reverse=True)
        
        # Ensure variety - don't pick too similar outfits
        selected_outfits = self._select_diverse_outfits(scored_outfits, count)
        
        # Create recommendations for selected outfits
        recommendations = []
        for i, (outfit_items, score_data) in enumerate(selected_outfits):
            # Store outfit items as JSON - NOT creating an actual outfit yet
            items_data = [{
                'id': str(item.id),
                'name': item.name,
                'category': item.category.name if item.category else 'Uncategorized',
                'color': item.color or '',
                'image_url': item.image.url if item.image else None,
            } for item in outfit_items]
            
            # Generate a creative name suggestion
            suggested_name = self._generate_creative_outfit_name(outfit_items)
            
            # Create recommendation without creating an outfit
            recommendation = DailyRecommendation.objects.create(
                user=self.user,
                outfit=None,  # No outfit created yet - user must confirm
                recommendation_date=date,
                priority=i,
                reason=score_data['reason'],
                confidence_score=score_data['total_score'],
                style_match_score=score_data['style_score'],
                occasion_match=score_data.get('occasion', 'casual'),
                weather_factor={
                    'suggested_items': items_data,
                    'suggested_name': suggested_name,
                    'item_ids': [str(item.id) for item in outfit_items],
                }
            )
            recommendations.append(recommendation)
            
        return recommendations
    
    def _select_diverse_outfits(self, scored_outfits, count):
        """
        Select diverse outfits to avoid showing too similar combinations
        """
        if len(scored_outfits) <= count:
            return scored_outfits
        
        selected = []
        used_item_sets = []
        
        for outfit_items, score_data in scored_outfits:
            if len(selected) >= count:
                break
            
            # Check overlap with already selected outfits
            current_ids = set(item.id for item in outfit_items)
            
            is_diverse = True
            for used_set in used_item_sets:
                overlap = len(current_ids.intersection(used_set))
                # If more than 50% overlap, skip this outfit
                if overlap > len(current_ids) * 0.5:
                    is_diverse = False
                    break
            
            if is_diverse:
                selected.append((outfit_items, score_data))
                used_item_sets.append(current_ids)
        
        # If we couldn't get enough diverse outfits, fill with top remaining
        if len(selected) < count:
            for outfit_items, score_data in scored_outfits:
                if len(selected) >= count:
                    break
                if (outfit_items, score_data) not in selected:
                    selected.append((outfit_items, score_data))
        
        return selected
    
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
        Generate smart outfit combinations from wardrobe.
        Ensures proper outfit structure: 1 top, 1 bottom, optionally 1 outerwear, 1 shoes, 1-2 accessories.
        Never picks multiple items from the same category group (e.g., 2 shirts).
        
        Returns:
            List of item combinations
        """
        combinations = []
        items_by_role = {
            'top': [],
            'bottom': [],
            'outerwear': [],
            'shoes': [],
            'accessory': [],
            'dress': [],  # Full-body items
        }
        
        # Map items to outfit roles based on category AND item name (for uncategorized items)
        top_patterns = ['top', 'shirt', 'blouse', 't-shirt', 'polo', 'sweater', 'hoodie', 'tank', 'tee', 'pullover']
        bottom_patterns = ['bottom', 'pants', 'jeans', 'skirt', 'shorts', 'trousers', 'chinos', 'leggings']
        outerwear_patterns = ['outerwear', 'jacket', 'coat', 'blazer', 'cardigan', 'vest', 'parka', 'bomber']
        shoes_patterns = ['shoes', 'shoe', 'footwear', 'sneakers', 'boots', 'sandals', 'heels', 'loafers']
        accessory_patterns = ['accessory', 'accessories', 'bag', 'hat', 'scarf', 'belt', 'watch', 'jewelry', 'sunglasses', 'tie']
        dress_patterns = ['dress', 'jumpsuit', 'romper', 'suit']
        
        for item in self.wardrobe_items:
            # Build search text from both category and item name
            cat_text = item.category.name.lower() if item.category else ''
            item_name = item.name.lower() if item.name else ''
            search_text = f"{cat_text} {item_name}"
            
            # Assign to role based on category/name patterns
            role_assigned = False
            
            if any(p in search_text for p in dress_patterns):
                items_by_role['dress'].append(item)
                role_assigned = True
            elif any(p in search_text for p in outerwear_patterns):
                items_by_role['outerwear'].append(item)
                role_assigned = True
            elif any(p in search_text for p in bottom_patterns):
                items_by_role['bottom'].append(item)
                role_assigned = True
            elif any(p in search_text for p in top_patterns):
                items_by_role['top'].append(item)
                role_assigned = True
            elif any(p in search_text for p in shoes_patterns):
                items_by_role['shoes'].append(item)
                role_assigned = True
            elif any(p in search_text for p in accessory_patterns):
                items_by_role['accessory'].append(item)
                role_assigned = True
            
            # If still not assigned, try to guess from common keywords
            if not role_assigned:
                # Default uncategorized items to tops (most common)
                items_by_role['top'].append(item)
        
        print(f"DEBUG: Items by role - tops: {len(items_by_role['top'])}, bottoms: {len(items_by_role['bottom'])}, outerwear: {len(items_by_role['outerwear'])}, shoes: {len(items_by_role['shoes'])}, accessories: {len(items_by_role['accessory'])}, dresses: {len(items_by_role['dress'])}")
        
        # Check if we have enough items to create outfits
        has_basics = (len(items_by_role['top']) > 0 and len(items_by_role['bottom']) > 0) or len(items_by_role['dress']) > 0
        
        if not has_basics:
            print("WARNING: Not enough items to create proper outfits")
            # Fallback: return whatever we have
            all_items = list(self.wardrobe_items)
            if len(all_items) >= 2:
                random.shuffle(all_items)
                combinations.append(all_items[:min(3, len(all_items))])
            return combinations
        
        # Generate combinations
        used_combos = set()
        attempts = 0
        max_attempts = count * 10
        
        while len(combinations) < count and attempts < max_attempts:
            attempts += 1
            outfit_items = []
            
            # Decide: dress outfit or top+bottom outfit
            use_dress = len(items_by_role['dress']) > 0 and random.random() < 0.3
            
            if use_dress:
                # Dress-based outfit
                dress = random.choice(items_by_role['dress'])
                outfit_items.append(dress)
            else:
                # Top + Bottom outfit (MUST have exactly 1 of each)
                if items_by_role['top'] and items_by_role['bottom']:
                    outfit_items.append(random.choice(items_by_role['top']))
                    outfit_items.append(random.choice(items_by_role['bottom']))
                else:
                    continue  # Skip if we can't form a basic outfit
            
            # Add optional outerwear (40% chance)
            if items_by_role['outerwear'] and random.random() < 0.4:
                outfit_items.append(random.choice(items_by_role['outerwear']))
            
            # Add shoes (60% chance)
            if items_by_role['shoes'] and random.random() < 0.6:
                outfit_items.append(random.choice(items_by_role['shoes']))
            
            # Add 0-1 accessories (30% chance)
            if items_by_role['accessory'] and random.random() < 0.3:
                outfit_items.append(random.choice(items_by_role['accessory']))
            
            # Check for duplicates using item IDs
            item_ids = tuple(sorted([item.id for item in outfit_items]))
            if item_ids in used_combos:
                continue
            
            used_combos.add(item_ids)
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
        
        # Base score - start with a reasonable minimum
        base_score = 0.35
        
        # 1. Color Harmony Score (25% weight)
        colors = [item.color.lower() for item in items if item.color]
        if len(colors) >= 2:
            color_score = self._calculate_color_harmony(colors)
            scores['color_harmony'] = color_score * 0.25
        elif len(colors) == 1:
            # Single color is always harmonious
            scores['color_harmony'] = 0.20
        
        # 2. Personal Preference Score (30% weight)
        pref_score = 0.0
        for item in items:
            # Favorite item bonus
            if item.favorite:
                pref_score += 0.4
            
            # Preferred color bonus
            if item.color and item.color.lower() in preferences['color_weights']:
                pref_score += min(preferences['color_weights'][item.color.lower()] * 0.15, 0.3)
            
            # Preferred category bonus
            if item.category and item.category.name in preferences['category_weights']:
                pref_score += min(preferences['category_weights'][item.category.name] * 0.15, 0.3)
            
            # Recently added items get a small boost
            pref_score += 0.1
        
        # Normalize preference score
        scores['personal_preference'] = min(pref_score / max(len(items), 1), 1.0) * 0.30
        
        # 3. Style Consistency Score (25% weight)
        style_score = 0.15  # Base consistency score
        if self.style_profile and hasattr(self.style_profile, 'preferred_styles') and self.style_profile.preferred_styles:
            matching_items = sum(1 for item in items if item.tags and 
                               any(style.lower() in [t.lower() for t in item.tags] 
                                   for style in self.style_profile.preferred_styles))
            style_score += (matching_items / max(len(items), 1)) * 0.10
        scores['style_consistency'] = style_score
        
        # 4. Season Match Score (20% weight)
        current_season = self._get_current_season()
        season_matches = 0
        for item in items:
            if item.seasons:
                if current_season in item.seasons or 'all_seasons' in item.seasons:
                    season_matches += 1
            else:
                # Items without season info are neutral
                season_matches += 0.5
        scores['season_match'] = (season_matches / max(len(items), 1)) * 0.20
        
        # Calculate total with base score
        scores['total_score'] = base_score + sum([
            scores['color_harmony'],
            scores['style_consistency'],
            scores['personal_preference'],
            scores['season_match']
        ])
        
        # Clamp to 0-1 range
        scores['total_score'] = min(max(scores['total_score'], 0.0), 1.0)
        scores['style_score'] = scores['total_score']
        
        # Generate reason with improved thresholds
        reasons = []
        if scores['color_harmony'] >= 0.15:
            reasons.append("harmonious colors")
        if scores['personal_preference'] >= 0.15:
            reasons.append("matches your style")
        if scores['season_match'] >= 0.10:
            reasons.append(f"perfect for {current_season}")
        if any(item.favorite for item in items):
            reasons.append("includes your favorites")
        
        # Always provide a reason
        if not reasons:
            reasons.append("a fresh combination from your wardrobe")
        
        scores['reason'] = f"Recommended for {', '.join(reasons)}."
        
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
        Create an Outfit object from a list of items with a creative name
        """
        # Check if this exact combination exists
        item_ids = set(item.id for item in items)
        
        existing_outfits = Outfit.objects.filter(user=self.user).prefetch_related('items')
        for outfit in existing_outfits:
            if set(outfit.items.values_list('id', flat=True)) == item_ids:
                return outfit
        
        # Generate a creative name based on the items
        creative_name = self._generate_creative_outfit_name(items)
        
        # Create new outfit
        outfit = Outfit.objects.create(
            user=self.user,
            name=creative_name,
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
        
        try:
            return outfit
        except Exception as e:
            print(f"Error creating outfit: {e}")
            return None
    
    def _generate_creative_outfit_name(self, items: List[ClothingItem]) -> str:
        """
        Generate a creative, descriptive name for an outfit based on its items
        
        Returns a creative name like "Urban Chic", "Coastal Breeze", etc.
        """
        # Collect item attributes
        colors = [item.color.lower() for item in items if item.color]
        categories = [item.category.name.lower() if item.category else '' for item in items]
        tags = []
        for item in items:
            if item.tags:
                tags.extend([t.lower() for t in item.tags])
        
        # Determine primary color theme
        color_themes = {
            'neutral': ['black', 'white', 'gray', 'grey', 'beige', 'cream', 'ivory', 'tan', 'brown'],
            'warm': ['red', 'orange', 'yellow', 'coral', 'peach', 'burgundy', 'maroon', 'terracotta'],
            'cool': ['blue', 'navy', 'green', 'teal', 'turquoise', 'aqua', 'mint', 'cyan'],
            'earthy': ['olive', 'khaki', 'brown', 'rust', 'camel', 'sand', 'taupe'],
            'pastel': ['pink', 'lavender', 'lilac', 'baby blue', 'mint', 'peach', 'blush'],
            'bold': ['red', 'royal blue', 'emerald', 'purple', 'magenta', 'fuchsia']
        }
        
        primary_theme = 'classic'
        for theme, theme_colors in color_themes.items():
            if any(color in theme_colors for color in colors):
                primary_theme = theme
                break
        
        # Style descriptors based on items
        style_words = []
        
        # Check for formal vs casual
        formal_indicators = ['blazer', 'suit', 'dress shirt', 'heels', 'formal', 'elegant']
        casual_indicators = ['jeans', 't-shirt', 'sneakers', 'casual', 'hoodie', 'sweatshirt']
        sporty_indicators = ['athletic', 'sport', 'sneakers', 'joggers', 'workout', 'active']
        
        all_text = ' '.join(categories + tags)
        
        if any(ind in all_text for ind in formal_indicators):
            style_words.extend(['Elegant', 'Refined', 'Sophisticated', 'Polished'])
        elif any(ind in all_text for ind in sporty_indicators):
            style_words.extend(['Active', 'Dynamic', 'Athletic', 'Energetic'])
        elif any(ind in all_text for ind in casual_indicators):
            style_words.extend(['Casual', 'Relaxed', 'Easy', 'Effortless'])
        else:
            style_words.extend(['Chic', 'Modern', 'Fresh', 'Classic'])
        
        # Mood/vibe descriptors based on color theme
        mood_words = {
            'neutral': ['Minimalist', 'Sleek', 'Urban', 'Timeless', 'Sophisticated'],
            'warm': ['Sunset', 'Autumn', 'Warm', 'Golden', 'Cozy'],
            'cool': ['Ocean', 'Breezy', 'Cool', 'Serene', 'Fresh'],
            'earthy': ['Nature', 'Organic', 'Grounded', 'Forest', 'Natural'],
            'pastel': ['Soft', 'Dreamy', 'Sweet', 'Delicate', 'Spring'],
            'bold': ['Bold', 'Vibrant', 'Statement', 'Power', 'Dynamic'],
            'classic': ['Classic', 'Everyday', 'Versatile', 'Smart', 'Polished']
        }
        
        # Seasonal additions
        season = self._get_current_season()
        seasonal_words = {
            'winter': ['Winter', 'Cozy', 'Warm', 'Frost'],
            'spring': ['Spring', 'Fresh', 'Bloom', 'Renewal'],
            'summer': ['Summer', 'Sunny', 'Breezy', 'Radiant'],
            'fall': ['Autumn', 'Harvest', 'Rustic', 'Cozy']
        }
        
        # Build the name
        mood = random.choice(mood_words.get(primary_theme, mood_words['classic']))
        style = random.choice(style_words)
        
        # Different name patterns
        name_patterns = [
            f"{mood} {style}",
            f"The {mood} Look",
            f"{style} {mood}",
            f"{mood} Vibes",
            f"{style} Moment",
            f"{mood} Edit",
        ]
        
        # Add seasonal flavor sometimes (20% chance)
        if random.random() < 0.2:
            seasonal = random.choice(seasonal_words.get(season, ['']))
            name_patterns.extend([
                f"{seasonal} {mood}",
                f"{mood} {seasonal}",
            ])
        
        return random.choice(name_patterns)
    
    def confirm_recommendation(self, recommendation):
        """
        User confirms they want to wear this outfit - creates the actual outfit
        
        Args:
            recommendation: DailyRecommendation object with suggested items
            
        Returns:
            The created Outfit object, or None if failed
        """
        if recommendation.outfit:
            # Already confirmed
            return recommendation.outfit
        
        # Get the suggested items from the weather_factor JSON
        suggested_data = recommendation.weather_factor or {}
        item_ids = suggested_data.get('item_ids', [])
        suggested_name = suggested_data.get('suggested_name', 'My Outfit')
        
        if not item_ids:
            return None
        
        # Get the actual clothing items
        items = ClothingItem.objects.filter(id__in=item_ids, user=self.user)
        
        if not items.exists():
            return None
        
        # Create the outfit
        outfit = self._create_outfit_from_items(list(items), suggested_name)
        
        if outfit:
            # Link the recommendation to the new outfit
            recommendation.outfit = outfit
            recommendation.status = 'accepted'
            recommendation.save()
            
            # Record positive feedback
            UserPreferenceSignal.objects.create(
                user=self.user,
                signal_type='recommendation_accepted',
                signal_value=1.5,
                outfit=outfit,
                context={
                    'recommendation_id': str(recommendation.id),
                    'confidence_score': recommendation.confidence_score,
                }
            )
        
        return outfit
    
    def generate_weather_recommendations(self, date=None, location=None, count=5):
        """
        Generate weather-aware outfit recommendations
        
        Args:
            date: Date for weather forecast (default: today)
            location: Location string (e.g., "Tunis,TN")
            count: Number of recommendations (default: 5)
            
        Returns:
            List of DailyRecommendation objects
        """
        if date is None:
            date = timezone.now().date()
        
        # For now, just call the regular daily recommendations
        # TODO: Integrate actual weather API data for weather-aware suggestions
        recommendations = self.generate_daily_recommendations(date=date, count=count)
        
        return recommendations
    
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

    def get_unavailable_items(self):
        """
        Get items that are currently unavailable (washing, loaned, etc.)
        """
        unavailable = ClothingItem.objects.filter(
            user=self.user
        ).exclude(status='available')
        
        # Also check for items that are 'available' but 'dirty' (wears_since_wash >= max)
        dirty = ClothingItem.objects.filter(
            user=self.user,
            status='available',
            wears_since_wash__gte=models.F('max_wears_before_wash')
        )
        
        return list(unavailable) + list(dirty)

    # ---------------------------------------------------------
    # VIRTUAL OUTFIT GENERATION (New Feature)
    # ---------------------------------------------------------
    def _generate_virtual_outfits(self, count=10):
        """
        Generate outfits using virtual items based on style archetypes
        """
        archetypes = [
            {
                'name': 'Parisian Chic',
                'style': 'Classic',
                'items': [
                    {'name': 'Breton Stripe Tee', 'category': 'Tops', 'color': 'Navy/White', 'image_url': 'https://placehold.co/400x500/navy/white?text=Breton+Stripe'},
                    {'name': 'Straight Leg Jeans', 'category': 'Bottoms', 'color': 'Medium Wash', 'image_url': 'https://placehold.co/400x500/3b82f6/white?text=Jeans'},
                    {'name': 'Trench Coat', 'category': 'Outerwear', 'color': 'Beige', 'image_url': 'https://placehold.co/400x500/d2b48c/white?text=Trench'},
                    {'name': 'Leather Loafers', 'category': 'Shoes', 'color': 'Black', 'image_url': 'https://placehold.co/400x500/000000/white?text=Loafers'}
                ]
            },
            {
                'name': 'Modern Minimalist',
                'style': 'Minimalist',
                'items': [
                    {'name': 'Oversized White Shirt', 'category': 'Tops', 'color': 'White', 'image_url': 'https://placehold.co/400x500/ffffff/000000?text=White+Shirt'},
                    {'name': 'Wide Leg Trousers', 'category': 'Bottoms', 'color': 'Black', 'image_url': 'https://placehold.co/400x500/000000/white?text=Trousers'},
                    {'name': 'Minimalist Sneakers', 'category': 'Shoes', 'color': 'White', 'image_url': 'https://placehold.co/400x500/ffffff/000000?text=Sneakers'}
                ]
            },
            {
                'name': 'Weekend Casual',
                'style': 'Casual',
                'items': [
                    {'name': 'Grey Hoodie', 'category': 'Tops', 'color': 'Grey', 'image_url': 'https://placehold.co/400x500/808080/white?text=Hoodie'},
                    {'name': 'Jogger Pants', 'category': 'Bottoms', 'color': 'Black', 'image_url': 'https://placehold.co/400x500/000000/white?text=Joggers'},
                    {'name': 'Running Shoes', 'category': 'Shoes', 'color': 'White', 'image_url': 'https://placehold.co/400x500/ffffff/000000?text=Runners'},
                    {'name': 'Baseball Cap', 'category': 'Accessories', 'color': 'Navy', 'image_url': 'https://placehold.co/400x500/000080/white?text=Cap'}
                ]
            },
            {
                'name': 'Smart Business',
                'style': 'Formal',
                'items': [
                    {'name': 'Satin Blouse', 'category': 'Tops', 'color': 'Cream', 'image_url': 'https://placehold.co/400x500/fffdd0/000000?text=Satin+Blouse'},
                    {'name': 'Pencil Skirt', 'category': 'Bottoms', 'color': 'Navy', 'image_url': 'https://placehold.co/400x500/000080/white?text=Skirt'},
                    {'name': 'Classic Blazer', 'category': 'Outerwear', 'color': 'Navy', 'image_url': 'https://placehold.co/400x500/000080/white?text=Blazer'},
                    {'name': 'Pointed Heels', 'category': 'Shoes', 'color': 'Nude', 'image_url': 'https://placehold.co/400x500/eebbbb/000000?text=Heels'}
                ]
            },
            {
                'name': 'Summer Breeze',
                'style': 'Boho',
                'items': [
                    {'name': 'Floral Midi Dress', 'category': 'Dresses', 'color': 'Sage Green', 'image_url': 'https://placehold.co/400x500/9dc183/white?text=Floral+Dress'},
                    {'name': 'Denim Jacket', 'category': 'Outerwear', 'color': 'Light Wash', 'image_url': 'https://placehold.co/400x500/add8e6/000000?text=Denim+Jacket'},
                    {'name': 'Strappy Sandals', 'category': 'Shoes', 'color': 'Tan', 'image_url': 'https://placehold.co/400x500/d2b48c/white?text=Sandals'}
                ]
            },
            {
                'name': 'City Slicker',
                'style': 'Urban',
                'items': [
                    {'name': 'Leather Jacket', 'category': 'Outerwear', 'color': 'Black', 'image_url': 'https://placehold.co/400x500/000000/white?text=Leather+Jacket'},
                    {'name': 'Graphic Tee', 'category': 'Tops', 'color': 'Black', 'image_url': 'https://placehold.co/400x500/000000/white?text=Graphic+Tee'},
                    {'name': 'Distressed Jeans', 'category': 'Bottoms', 'color': 'Grey', 'image_url': 'https://placehold.co/400x500/808080/white?text=Jeans'},
                    {'name': 'Combat Boots', 'category': 'Shoes', 'color': 'Black', 'image_url': 'https://placehold.co/400x500/000000/white?text=Boots'}
                ]
            }
        ]
        
        # Generate variations from archetypes
        virtual_outfits = []
        
        for _ in range(count):
            archetype = random.choice(archetypes)
            # Create a copy to randomize slightly if needed later
            outfit = {
                'name': archetype['name'],
                'style': archetype['style'],
                'items': archetype['items']
            }
            virtual_outfits.append(outfit)
            
        return virtual_outfits


class StyleCoach:
    """
    AI Style Coach Logic
    Audits outfits for style rules and updates Fashion IQ.
    """
    
    def __init__(self, user):
        self.user = user
        
    def audit_outfit(self, outfit) -> StyleCritiqueSession:
        """
        Analyze an outfit and define if it's a 'Lesson' or a 'Win'.
        Updates Fashion IQ.
        """
        # 1. Analyze Logic
        items = list(outfit.items.all())
        colors = [item.color.lower() for item in items if item.color]
        
        # Check Color Harmony
        harmony_score, harmony_reason = self._check_color_harmony(colors)
        
        # Check Pattern Mixing (Simple rule: > 2 patterned items is risky)
        pattern_issues = self._check_patterns(items)
        
        # 2. Determine Feedback
        critique = ""
        suggestion = ""
        concept = ""
        is_positive = True
        xp_gain = 10  # Base XP for creating an outfit
        
        if harmony_score < 0.4:
            critique = f"Contrast Warning: {harmony_reason}" if harmony_reason else "These colors have problematic contrast."
            suggestion = "Try replacing one item with a solid neutral (White or Black)."
            concept = "Color Theory: Rule of Harmony"
            is_positive = False
            xp_gain += 5  # Learning opportunity
        elif pattern_issues:
            critique = f"You are mixing {len(pattern_issues)} patterns."
            suggestion = "Stick to 1 mixed pattern per outfit for a cohesive look."
            concept = "Pattern Mixing 101"
            is_positive = False
            xp_gain += 5
        else:
            critique = "Great coordination!"
            suggestion = "This looks balanced."
            concept = "Good Style"
            xp_gain += 15  # Bonus for good style
            
        # 3. Create Session Record
        session = StyleCritiqueSession.objects.create(
            user=self.user,
            related_outfit=outfit,
            critique_text=critique,
            suggestion_text=suggestion,
            concept_taught=concept,
            xp_gained=xp_gain,
            is_helpful=True
        )
        
        # 4. Update Fashion IQ
        self._update_fashion_iq(xp_gain, harmony_score)
        
        
        return session

    def _check_color_harmony(self, colors: List[str]) -> Tuple[float, str]:
        """
        Check color harmony using color theory rules.
        Returns: (score, reason)
        """
        if len(colors) < 2:
            return 1.0, ""  # Monochromatic/Single item is safe
            
        # Normalize to base colors
        colors = [self._get_base_color(c) for c in colors]
        unique_colors = set(colors)
        
        # Define color relationships
        NEUTRALS = {'black', 'white', 'grey', 'beige', 'navy'}
        
        # Good combinations (Analogous, Classic, Safe)
        GOOD_COMBOS = [
            {'navy', 'white'},        # Classic
            {'black', 'white'},       # Timeless
            {'navy', 'beige'},        # Nautical
            {'grey', 'pink'},         # Soft contrast
            {'blue', 'white'},        # Fresh
            {'brown', 'beige'},       # Earth tones
            {'green', 'brown'},       # Natural
            {'blue', 'grey'},         # Cool tones
        ]
        
        # Risky combinations (Complementary/Clashing)
        CLASH_COMBOS = [
            ({'black', 'brown'}, "Mixing Black and Brown is difficult to pull off."),
            ({'black', 'navy'}, "Black and Navy can look mismatched."),
            ({'red', 'pink'}, "Red and Pink are risky together."),
            ({'red', 'green'}, "Red and Green can look too festive."),
            ({'purple', 'orange'}, "Purple and Orange clash."),
            ({'red', 'orange'}, "Red and Orange compete for attention."),
            ({'blue', 'green'}, "Blue and Green require careful balance."),
        ]
        
        # 1. Check for GOOD combinations first
        non_neutrals = unique_colors - NEUTRALS
        if len(non_neutrals) <= 1:
            # Neutral + 1 accent = Usually good
            return 0.9, ""
            
        for good_combo in GOOD_COMBOS:
            if good_combo.issubset(unique_colors):
                return 0.95, ""  # Known good combo
        
        # 2. Check for "Busy" (Too many colors)
        if len(unique_colors) > 3:
            return 0.35, "This outfit looks busy. Try reducing the number of colors."
            
        # 3. Check for CLASHES
        for clash_set, warning in CLASH_COMBOS:
            if clash_set.issubset(unique_colors):
                return 0.3, warning
                
        # 4. Check for "Neutral Chaos" (Black + Brown + Grey)
        dark_neutrals = unique_colors & {'black', 'brown', 'grey', 'navy'}
        if len(dark_neutrals) >= 3:
            return 0.35, "Too many dark neutrals competing."

        # Default: Acceptable but not exceptional
        return 0.7, ""

    def _get_base_color(self, color_name: str) -> str:
        """
        Extract base color from description (e.g., 'Dark Gray' -> 'gray')
        """
        color = color_name.lower().strip()
        
        # Specific mappings
        if 'navy' in color: return 'navy'
        if 'brown' in color or 'beige' in color or 'tan' in color or 'camel' in color: return 'brown'
        if 'gray' in color or 'grey' in color or 'silver' in color or 'charcoal' in color: return 'grey'
        if 'white' in color or 'cream' in color or 'ivory' in color: return 'white'
        if 'black' in color: return 'black'
        if 'red' in color or 'burgundy' in color or 'maroon' in color: return 'red'
        if 'pink' in color or 'rose' in color: return 'pink'
        if 'green' in color or 'olive' in color: return 'green'
        if 'blue' in color: return 'blue'
        if 'orange' in color: return 'orange'
        if 'yellow' in color or 'gold' in color: return 'yellow'
        if 'purple' in color or 'violet' in color or 'lavender' in color: return 'purple'
        
        return color

    def _check_patterns(self, items) -> List[str]:
        """
        Detect patterns and return list of patterned items.
        """
        PATTERN_KEYWORDS = [
            'stripe', 'striped', 'pinstripe', 'breton',
            'floral', 'flower', 'botanical',
            'plaid', 'tartan', 'check', 'checked', 'gingham',
            'polka', 'dot', 'spotted', 'dotted',
            'leopard', 'zebra', 'snake', 'animal', 'tiger',
            'geometric', 'abstract', 'graphic',
            'paisley', 'print', 'pattern',
        ]
        
        patterned_items = []
        for item in items:
            text = (item.name + " " + " ".join(item.tags or [])).lower()
            if any(kw in text for kw in PATTERN_KEYWORDS):
                patterned_items.append(item.name)
        
        return patterned_items if len(patterned_items) > 2 else []

    def _update_fashion_iq(self, xp, style_score):
        """
        Add XP, check for level up, and update streak
        """
        from datetime import date, timedelta
        
        iq, created = FashionIQ.objects.get_or_create(user=self.user)
        iq.total_xp += xp
        iq.lessons_completed += 1
        
        # Streak Logic: If good outfit (score >= 0.7), update streak
        today = date.today()
        if style_score >= 0.7:
            if iq.last_good_outfit_date:
                days_since = (today - iq.last_good_outfit_date).days
                if days_since == 1:
                    # Consecutive day - extend streak
                    iq.current_streak += 1
                elif days_since == 0:
                    # Same day - don't change streak
                    pass
                else:
                    # Streak broken - restart
                    iq.current_streak = 1
            else:
                # First good outfit ever
                iq.current_streak = 1
            
            iq.last_good_outfit_date = today
            iq.longest_streak = max(iq.longest_streak, iq.current_streak)
        
        # Level Logic
        if iq.total_xp > 5000:
            iq.current_level = 'expert'
        elif iq.total_xp > 2000:
            iq.current_level = 'advanced'
        elif iq.total_xp > 500:
            iq.current_level = 'intermediate'
        
        iq.save()
