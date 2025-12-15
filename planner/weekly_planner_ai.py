"""
AI Weekly Planner Engine for Tailora

Generates intelligent weekly outfit plans based on:
- Calendar events and occasion types
- Weather forecasts (7-day)
- Wear history (avoid repetition)
- User style preferences
- Color harmony and style rules
"""

from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import random

from wardrobe.models import ClothingItem
from outfits.models import Outfit, OutfitItem
from users.models import StyleProfile, User
from .models import Event, WeeklyPlan, DailyPlanSlot, WearHistory
from .weather_service import WeatherService


class WeeklyPlannerAI:
    """
    AI engine for generating weekly outfit plans
    
    Scoring weights:
    - Weather appropriateness: 28%
    - Event/occasion match: 23%
    - Recency penalty (avoid recently worn): 18%
    - User preference (ML learned): 15%
    - Style profile match: 10%
    - Color harmony: 6%
    """
    
    WEATHER_WEIGHT = 0.28
    OCCASION_WEIGHT = 0.23
    RECENCY_WEIGHT = 0.18
    PREFERENCE_WEIGHT = 0.15  # ML learned preferences
    STYLE_WEIGHT = 0.10
    COLOR_WEIGHT = 0.06
    RANDOMNESS_FACTOR = 0.15  # Up to 15% random variation for variety
    
    def __init__(self, user: User):
        self.user = user
        self.style_profile = getattr(user, 'style_profile', None)
        self.weather_service = WeatherService()
        self._ml_engine = None
    
    @property
    def ml_engine(self):
        """Lazy load ML engine"""
        if self._ml_engine is None:
            try:
                from recommendations.ml_pattern_engine import MLPatternEngine
                self._ml_engine = MLPatternEngine(self.user)
            except Exception:
                self._ml_engine = None
        return self._ml_engine
        
    def generate_weekly_plan(
        self, 
        week_start: Optional[datetime] = None,
        location: str = 'Tunis'
    ) -> WeeklyPlan:
        """
        Generate a complete weekly outfit plan
        
        Args:
            week_start: Monday of the week to plan (default: current week)
            location: City for weather forecast
            
        Returns:
            WeeklyPlan object with 7 DailyPlanSlot entries
        """
        # Normalize to Monday of the week
        if week_start is None:
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
        elif hasattr(week_start, 'date'):
            week_start = week_start.date()
            week_start = week_start - timedelta(days=week_start.weekday())
        else:
            week_start = week_start - timedelta(days=week_start.weekday())
        
        # Check for existing plan for this week
        existing_plan = WeeklyPlan.objects.filter(
            user=self.user,
            week_start=week_start
        ).first()
        
        if existing_plan:
            # Delete old plan and create fresh one
            existing_plan.delete()
        
        # Fetch required data
        weather_data = self._fetch_week_weather(week_start, location)
        week_events = self._get_week_events(week_start)
        available_outfits = self._get_available_outfits()
        wear_history = self._get_recent_wear_history(days=21)
        
        # Create the weekly plan
        weekly_plan = WeeklyPlan.objects.create(
            user=self.user,
            week_start=week_start,
            weather_data=weather_data,
            events_considered=[{
                'id': str(e.id),
                'title': e.title,
                'date': str(e.date),
                'occasion': e.occasion_type
            } for e in week_events],
            location=location,
            generation_reasoning=self._generate_plan_reasoning(week_events, weather_data),
            status='active'
        )
        
        # Generate outfit for each day
        used_outfits = set()  # Track used outfits to ensure variety
        
        for day_offset in range(7):
            day_date = week_start + timedelta(days=day_offset)
            day_weather = self._get_day_weather(weather_data, day_offset)
            day_events = [e for e in week_events if e.date == day_date]
            
            # Calculate scores for all outfits
            scored_outfits = []
            for outfit in available_outfits:
                if outfit.id in used_outfits:
                    continue  # Skip already used outfits
                    
                scores = self._calculate_outfit_scores(
                    outfit, 
                    day_weather, 
                    day_events,
                    wear_history,
                    day_date
                )
                scored_outfits.append((outfit, scores))
            
            # Sort by total score
            scored_outfits.sort(key=lambda x: x[1]['total'], reverse=True)
            
            # Select primary outfit and alternatives
            primary_outfit = None
            alternatives = []
            selection_reason = "No suitable outfit found for this day."
            scores_dict = {'weather': 0, 'occasion': 0, 'recency': 0, 'style': 0}
            
            if scored_outfits:
                # Use weighted random selection from top candidates for variety
                primary_outfit, scores_dict = self._weighted_random_select(scored_outfits[:7])
                used_outfits.add(primary_outfit.id)
                selection_reason = self._generate_selection_reason(
                    primary_outfit, scores_dict, day_weather, day_events
                )
                
                # Get up to 3 alternatives (excluding selected primary)
                for alt_outfit, _ in scored_outfits:
                    if alt_outfit.id != primary_outfit.id and len(alternatives) < 3:
                        alternatives.append(alt_outfit)
            
            # Create the daily slot
            daily_slot = DailyPlanSlot.objects.create(
                weekly_plan=weekly_plan,
                date=day_date,
                day_of_week=day_offset,
                primary_outfit=primary_outfit,
                weather_condition=day_weather.get('condition', ''),
                temperature=day_weather.get('temperature'),
                humidity=day_weather.get('humidity'),
                weather_icon=day_weather.get('icon', ''),
                selection_reason=selection_reason,
                confidence=scores_dict.get('total', 0.5),
                weather_score=scores_dict.get('weather', 0),
                occasion_score=scores_dict.get('occasion', 0),
                recency_score=scores_dict.get('recency', 0),
                style_score=scores_dict.get('style', 0),
                status='suggested'
            )
            
            # Add alternatives
            if alternatives:
                daily_slot.alternatives.set(alternatives)
            
            # Link events
            if day_events:
                daily_slot.events.set(day_events)
        
        return weekly_plan
    
    def _fetch_week_weather(self, week_start, location: str) -> Dict:
        """
        Fetch 7-day weather forecast
        
        Returns dict with daily forecasts keyed by day offset (0-6)
        """
        weather_data = {}
        
        try:
            # Try to get forecast from weather service
            forecast = self.weather_service.get_forecast(location, days=7)
            
            if forecast and 'daily' in forecast:
                for i, day_forecast in enumerate(forecast['daily'][:7]):
                    weather_data[i] = {
                        'temperature': day_forecast.get('temp', {}).get('day', 20),
                        'condition': day_forecast.get('weather', [{}])[0].get('main', 'Clear'),
                        'humidity': day_forecast.get('humidity', 50),
                        'icon': day_forecast.get('weather', [{}])[0].get('icon', '01d'),
                        'feels_like': day_forecast.get('feels_like', {}).get('day', 20),
                    }
        except Exception as e:
            print(f"Weather fetch error: {e}")
        
        # Fill in missing days with defaults
        for i in range(7):
            if i not in weather_data:
                weather_data[i] = {
                    'temperature': 20,
                    'condition': 'Clear',
                    'humidity': 50,
                    'icon': '01d',
                    'feels_like': 20,
                }
        
        return weather_data
    
    def _get_day_weather(self, weather_data: Dict, day_offset: int) -> Dict:
        """Get weather for a specific day offset"""
        return weather_data.get(day_offset, {
            'temperature': 20,
            'condition': 'Clear',
            'humidity': 50,
            'icon': '01d',
        })
    
    def _get_week_events(self, week_start) -> List[Event]:
        """Get all events for the week"""
        week_end = week_start + timedelta(days=6)
        return list(Event.objects.filter(
            user=self.user,
            date__gte=week_start,
            date__lte=week_end
        ).order_by('date', 'time'))
    
    def _get_available_outfits(self) -> List[Outfit]:
        """Get all user outfits that are available"""
        outfits = list(Outfit.objects.filter(
            user=self.user
        ).prefetch_related('items').order_by('-created_at')[:50])
        # Shuffle to add initial randomness
        random.shuffle(outfits)
        return outfits
    
    def _weighted_random_select(self, scored_outfits: List[Tuple[Outfit, Dict]]) -> Tuple[Outfit, Dict]:
        """
        Select an outfit using weighted random selection.
        Higher scoring outfits are more likely to be selected, but not guaranteed.
        This ensures regeneration produces different results.
        """
        if not scored_outfits:
            return None, {}
        
        if len(scored_outfits) == 1:
            return scored_outfits[0]
        
        # Convert scores to weights (ensure minimum weight)
        weights = []
        for outfit, scores in scored_outfits:
            # Use exponential weighting to favor higher scores while allowing variation
            weight = max(0.1, scores['total']) ** 2  # Square to favor higher scores
            weights.append(weight)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            # Equal probability if all weights are 0
            return random.choice(scored_outfits)
        
        # Weighted random selection
        r = random.uniform(0, total_weight)
        cumulative = 0
        for i, (outfit, scores) in enumerate(scored_outfits):
            cumulative += weights[i]
            if r <= cumulative:
                return outfit, scores
        
        # Fallback to last item
        return scored_outfits[-1]
    
    def _get_recent_wear_history(self, days: int = 21) -> Dict:
        """
        Get wear history for the past N days
        
        Returns dict: outfit_id -> last_worn_date
        """
        cutoff = timezone.now().date() - timedelta(days=days)
        history = WearHistory.objects.filter(
            user=self.user,
            worn_date__gte=cutoff
        ).select_related('outfit')
        
        wear_dict = {}
        for entry in history:
            if entry.outfit:
                wear_dict[entry.outfit.id] = entry.worn_date
        
        return wear_dict
    
    def _calculate_outfit_scores(
        self,
        outfit: Outfit,
        day_weather: Dict,
        day_events: List[Event],
        wear_history: Dict,
        target_date
    ) -> Dict:
        """
        Calculate comprehensive scores for an outfit
        
        Returns dict with individual scores and total
        """
        scores = {
            'weather': 0.0,
            'occasion': 0.0,
            'recency': 0.0,
            'preference': 0.0,  # ML learned preferences
            'style': 0.0,
            'color': 0.0,
            'total': 0.0,
        }
        
        # 1. Weather Score (28%)
        scores['weather'] = self._score_weather_match(outfit, day_weather)
        
        # 2. Occasion Score (23%)
        scores['occasion'] = self._score_occasion_match(outfit, day_events)
        
        # 3. Recency Score (18%) - Higher score for less recently worn
        scores['recency'] = self._score_recency(outfit, wear_history, target_date)
        
        # 4. Preference Score (15%) - ML learned from accept/reject patterns
        if self.ml_engine:
            try:
                # Get preference boost from -1 to 1, normalize to 0-1 range
                boost = self.ml_engine.calculate_preference_boost(outfit)
                scores['preference'] = (boost + 1) / 2  # Convert [-1,1] to [0,1]
            except Exception:
                scores['preference'] = 0.5  # Neutral if ML fails
        else:
            scores['preference'] = 0.5  # Neutral if no ML engine
        
        # 5. Style Score (10%)
        scores['style'] = self._score_style_match(outfit)
        
        # 6. Color Score (6%)
        scores['color'] = self._score_color_harmony(outfit)
        
        # Calculate weighted total
        base_score = (
            scores['weather'] * self.WEATHER_WEIGHT +
            scores['occasion'] * self.OCCASION_WEIGHT +
            scores['recency'] * self.RECENCY_WEIGHT +
            scores['preference'] * self.PREFERENCE_WEIGHT +
            scores['style'] * self.STYLE_WEIGHT +
            scores['color'] * self.COLOR_WEIGHT
        )
        
        # Add randomness factor for variety (regeneration produces different results)
        random_factor = random.uniform(-self.RANDOMNESS_FACTOR, self.RANDOMNESS_FACTOR)
        scores['total'] = max(0.0, min(1.0, base_score + random_factor))
        
        return scores
    
    def _score_weather_match(self, outfit: Outfit, weather: Dict) -> float:
        """Score outfit suitability for weather conditions"""
        score = 0.5  # Base score
        
        # Handle None or empty weather data
        if not weather:
            return score  # Return neutral score if no weather data
            
        temp = weather.get('temperature', 20)
        condition = weather.get('condition', '').lower()
        
        # Check outfit temperature range
        if outfit.min_temperature and outfit.max_temperature:
            if outfit.min_temperature <= temp <= outfit.max_temperature:
                score = 1.0
            elif abs(temp - outfit.min_temperature) <= 5 or abs(temp - outfit.max_temperature) <= 5:
                score = 0.7
            else:
                score = 0.3
        else:
            # No temperature data - use item analysis
            items = outfit.items.all()
            warm_items = 0
            light_items = 0
            
            for item in items:
                item_name = (item.name or '').lower()
                category = (item.category.name if item.category else '').lower()
                
                # Check for warm items
                if any(w in item_name or w in category for w in 
                       ['jacket', 'coat', 'sweater', 'hoodie', 'cardigan', 'wool']):
                    warm_items += 1
                
                # Check for light items
                if any(l in item_name or l in category for l in 
                       ['t-shirt', 'shorts', 'tank', 'sandal', 'linen']):
                    light_items += 1
            
            # Score based on temperature appropriateness
            if temp < 15:  # Cold
                score = min(1.0, 0.5 + warm_items * 0.2)
            elif temp > 28:  # Hot
                score = min(1.0, 0.5 + light_items * 0.2)
            else:  # Moderate
                score = 0.7
        
        # Weather condition adjustments
        if 'rain' in condition:
            # Check for rain-appropriate items
            suitable_weather = outfit.suitable_weather or []
            if 'rainy' in suitable_weather or 'rain' in suitable_weather:
                score = min(1.0, score + 0.2)
            else:
                score = max(0.2, score - 0.2)
        
        return score
    
    def _score_occasion_match(self, outfit: Outfit, events: List[Event]) -> float:
        """Score outfit match with day's events"""
        if not events:
            # No events - casual day
            if outfit.occasion in ['casual', 'weekend']:
                return 0.9
            elif outfit.occasion == 'work':
                return 0.7  # Work outfits are fine for regular days
            else:
                return 0.5
        
        # Match with event occasions
        best_match = 0.0
        occasion_map = {
            'work': ['work'],
            'casual': ['casual'],
            'formal': ['formal', 'evening'],
            'party': ['evening', 'date'],
            'date': ['date', 'evening'],
            'sports': ['sport'],
            'travel': ['travel', 'casual'],
        }
        
        for event in events:
            event_occasion = event.occasion_type
            outfit_occasion = outfit.occasion
            
            if event_occasion == outfit_occasion:
                best_match = max(best_match, 1.0)
            elif outfit_occasion in occasion_map.get(event_occasion, []):
                best_match = max(best_match, 0.8)
            elif outfit_occasion in ['casual', 'work']:
                best_match = max(best_match, 0.5)
        
        return best_match if best_match > 0 else 0.4
    
    def _score_recency(self, outfit: Outfit, wear_history: Dict, target_date) -> float:
        """Score based on how recently the outfit was worn"""
        last_worn = wear_history.get(outfit.id)
        
        if not last_worn:
            return 1.0  # Never worn or not in recent history - great!
        
        days_since = (target_date - last_worn).days
        
        if days_since <= 3:
            return 0.2  # Too recent
        elif days_since <= 7:
            return 0.5
        elif days_since <= 14:
            return 0.8
        else:
            return 1.0
    
    def _score_style_match(self, outfit: Outfit) -> float:
        """Score match with user's style profile"""
        if not self.style_profile:
            return 0.6  # Default neutral score
        
        score = 0.5
        
        # Check preferred styles
        preferred_styles = getattr(self.style_profile, 'preferred_styles', []) or []
        outfit_tags = outfit.style_tags or []
        
        if preferred_styles and outfit_tags:
            matching = sum(1 for style in preferred_styles 
                          if style.lower() in [t.lower() for t in outfit_tags])
            if matching > 0:
                score += min(0.4, matching * 0.15)
        
        # Favorite bonus
        if outfit.favorite:
            score += 0.2
        
        # Rating bonus
        if outfit.rating:
            score += (outfit.rating - 3) * 0.1  # -0.2 to +0.2
        
        return min(1.0, max(0.0, score))
    
    def _score_color_harmony(self, outfit: Outfit) -> float:
        """Score the color harmony of outfit items"""
        items = outfit.items.all()
        colors = [item.color.lower() for item in items if item.color]
        
        if len(colors) < 2:
            return 0.7  # Single color or no color data
        
        # Neutral colors that go with everything
        neutrals = {'black', 'white', 'gray', 'grey', 'beige', 'cream', 'navy', 'tan', 'brown'}
        
        neutral_count = sum(1 for c in colors if c in neutrals)
        color_count = len(colors) - neutral_count
        
        # Good ratio: mostly neutrals with 1-2 accent colors
        if color_count <= 2 and neutral_count >= 1:
            return 0.9
        elif color_count <= 3:
            return 0.7
        else:
            return 0.5  # Too many colors
    
    def _generate_selection_reason(
        self, 
        outfit: Outfit, 
        scores: Dict, 
        weather: Dict, 
        events: List[Event]
    ) -> str:
        """Generate human-readable reason for outfit selection"""
        reasons = []
        
        # Handle None weather
        if not weather:
            weather = {}
        
        # Weather reason
        temp = weather.get('temperature', 20)
        if scores.get('weather', 0) >= 0.8:
            if temp < 15:
                reasons.append("perfect for the cool weather")
            elif temp > 28:
                reasons.append("great for the warm day")
            else:
                reasons.append("ideal for the temperature")
        
        # Occasion reason
        if events and scores.get('occasion', 0) >= 0.7:
            event_titles = [e.title for e in events[:2]]
            reasons.append(f"matches your {', '.join(event_titles)}")
        elif not events:
            reasons.append("perfect for a casual day")
        
        # Style reason
        if scores.get('style', 0) >= 0.7:
            reasons.append("fits your style preferences")
        
        # Favorite reason
        if outfit.favorite:
            reasons.append("one of your favorites")
        
        # Recency reason
        if scores.get('recency', 0) >= 0.9:
            reasons.append("hasn't been worn recently")
        
        if not reasons:
            reasons.append("a great combination from your wardrobe")
        
        return f"Recommended because it's {', '.join(reasons)}."
    
    def _generate_plan_reasoning(self, events: List[Event], weather_data: Dict) -> str:
        """Generate overall reasoning for the weekly plan"""
        event_count = len(events)
        
        # Analyze weather trend
        temps = [w.get('temperature', 20) for w in weather_data.values()]
        avg_temp = sum(temps) / len(temps) if temps else 20
        
        if avg_temp < 15:
            weather_summary = "cool temperatures expected this week"
        elif avg_temp > 28:
            weather_summary = "warm weather ahead"
        else:
            weather_summary = "moderate temperatures throughout the week"
        
        # Format event summary
        if event_count == 0:
            event_summary = "no scheduled events"
        elif event_count == 1:
            event_summary = f"1 event ({events[0].title})"
        else:
            event_summary = f"{event_count} events planned"
        
        return (
            f"This week's plan considers {weather_summary} and {event_summary}. "
            f"Outfits were selected to ensure variety while maintaining style consistency."
        )
    
    def regenerate_day(self, daily_slot: DailyPlanSlot) -> DailyPlanSlot:
        """
        Regenerate outfit suggestion for a specific day
        
        Args:
            daily_slot: The DailyPlanSlot to regenerate
            
        Returns:
            Updated DailyPlanSlot
        """
        weekly_plan = daily_slot.weekly_plan
        weather_data = weekly_plan.weather_data
        day_offset = daily_slot.day_of_week
        
        # Get available outfits, excluding currently assigned one
        available_outfits = self._get_available_outfits()
        current_outfit = daily_slot.primary_outfit
        
        if current_outfit:
            available_outfits = [o for o in available_outfits if o.id != current_outfit.id]
        
        # Get day context
        day_weather = self._get_day_weather(weather_data, day_offset)
        day_events = list(daily_slot.events.all())
        wear_history = self._get_recent_wear_history()
        
        # Score outfits
        scored_outfits = []
        for outfit in available_outfits:
            scores = self._calculate_outfit_scores(
                outfit, day_weather, day_events, wear_history, daily_slot.date
            )
            scored_outfits.append((outfit, scores))
        
        scored_outfits.sort(key=lambda x: x[1]['total'], reverse=True)
        
        if scored_outfits:
            # Use weighted random selection for variety
            new_outfit, scores = self._weighted_random_select(scored_outfits[:5])
            daily_slot.primary_outfit = new_outfit
            daily_slot.selection_reason = self._generate_selection_reason(
                new_outfit, scores, day_weather, day_events
            )
            daily_slot.confidence = scores['total']
            daily_slot.weather_score = scores['weather']
            daily_slot.occasion_score = scores['occasion']
            daily_slot.recency_score = scores['recency']
            daily_slot.style_score = scores['style']
            daily_slot.status = 'suggested'
            
            # Update alternatives
            alternatives = [o for o, _ in scored_outfits[1:4]]
            daily_slot.alternatives.set(alternatives)
            
            daily_slot.save()
        
        return daily_slot
    
    def accept_outfit(self, daily_slot: DailyPlanSlot) -> DailyPlanSlot:
        """Mark an outfit as accepted by user"""
        daily_slot.status = 'accepted'
        daily_slot.save()
        return daily_slot
    
    def swap_to_alternative(
        self, 
        daily_slot: DailyPlanSlot, 
        alternative_outfit: Outfit
    ) -> DailyPlanSlot:
        """Swap primary outfit with an alternative"""
        old_primary = daily_slot.primary_outfit
        
        # Set new primary
        daily_slot.primary_outfit = alternative_outfit
        daily_slot.status = 'modified'
        
        # Move old primary to alternatives
        alternatives = list(daily_slot.alternatives.all())
        if old_primary and old_primary not in alternatives:
            alternatives.append(old_primary)
        
        # Remove new primary from alternatives
        alternatives = [a for a in alternatives if a.id != alternative_outfit.id]
        
        daily_slot.alternatives.set(alternatives[:3])
        daily_slot.save()
        
        return daily_slot
    
    def record_outfit_used(
        self,
        outfit: Outfit,
        worn_date,
        weather_condition: str = '',
        temperature: int = None
    ):
        """
        Record that an outfit was used, updating wear history and laundry stats.
        Reusable for both Weekly Planner and Events.
        """
        # Create wear history entry
        wear_entry = WearHistory.objects.create(
            user=self.user,
            outfit=outfit,
            worn_date=worn_date,
            weather_condition=weather_condition,
            temperature=temperature
        )
        
        # Add individual items to wear history
        items = outfit.items.all()
        wear_entry.clothing_items.set(items)
        
        # Update outfit wear count
        outfit.times_worn += 1
        outfit.last_worn = worn_date
        outfit.save()
        
        # Update each item's wear count and laundry tracking
        for item in items:
            item.times_worn += 1
            item.wears_since_wash += 1  # Track laundry needs
            item.last_worn = worn_date
            item.save()
            
        return wear_entry

    def mark_as_worn(self, daily_slot: DailyPlanSlot) -> DailyPlanSlot:
        """Mark outfit as worn and record in wear history"""
        daily_slot.status = 'worn'
        daily_slot.save()
        
        if daily_slot.primary_outfit:
            self.record_outfit_used(
                outfit=daily_slot.primary_outfit,
                worn_date=daily_slot.date,
                weather_condition=daily_slot.weather_condition,
                temperature=daily_slot.temperature
            )
        
        return daily_slot
