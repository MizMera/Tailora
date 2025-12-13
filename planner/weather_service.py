"""
Weather Service for Tailora
Integrates with OpenWeatherMap API to provide weather forecasts
"""

import requests
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Service for fetching weather data from OpenWeatherMap API
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self):
        self.api_key = getattr(settings, 'WEATHER_API_KEY', None)
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
    
    def _make_request(self, endpoint, params):
        """Make HTTP request to OpenWeatherMap API"""
        if not self.api_key:
            return None
        
        params['appid'] = self.api_key
        params['units'] = 'metric'  # Use Celsius
        
        try:
            response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Weather API request failed: {str(e)}")
            return None
    
    def get_current_weather(self, city=None, lat=None, lon=None):
        """
        Get current weather for a location
        
        Args:
            city: City name (e.g., "Paris,FR")
            lat: Latitude
            lon: Longitude
        
        Returns:
            dict: Weather data or None if failed
        """
        # Create cache key
        if city:
            cache_key = f"weather_current_{city}"
            params = {'q': city}
        elif lat and lon:
            cache_key = f"weather_current_{lat}_{lon}"
            params = {'lat': lat, 'lon': lon}
        else:
            logger.error("Either city or coordinates must be provided")
            return None
        
        # Check cache first (cache for 30 minutes)
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Fetch from API
        data = self._make_request('weather', params)
        
        if data:
            # Parse and simplify response
            weather_data = {
                'temperature': round(data['main']['temp']),
                'feels_like': round(data['main']['feels_like']),
                'condition': data['weather'][0]['main'].lower(),
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'wind_speed': round(data['wind']['speed'] * 3.6, 1),  # Convert m/s to km/h
                'icon': data['weather'][0]['icon'],
                'location': data['name'],
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache for 30 minutes
            cache.set(cache_key, weather_data, 60 * 30)
            return weather_data
        
        return None
    
    def get_forecast(self, city=None, lat=None, lon=None, days=7):
        """
        Get weather forecast for upcoming days
        
        Args:
            city: City name
            lat: Latitude
            lon: Longitude
            days: Number of days (max 7 for free tier)
        
        Returns:
            list: Daily forecast data
        """
        # Create cache key
        if city:
            cache_key = f"weather_forecast_{city}_{days}"
            params = {'q': city}
        elif lat and lon:
            cache_key = f"weather_forecast_{lat}_{lon}_{days}"
            params = {'lat': lat, 'lon': lon}
        else:
            return None
        
        # Check cache (cache for 2 hours)
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Fetch 5-day/3-hour forecast
        params['cnt'] = min(days * 8, 40)  # 8 data points per day, max 40
        data = self._make_request('forecast', params)
        
        if not data:
            return None
        
        # Group by day and get daily summary
        daily_forecast = []
        current_date = None
        day_data = []
        
        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            date = dt.date()
            
            if current_date != date:
                # Process previous day
                if day_data:
                    daily_forecast.append(self._process_day_forecast(current_date, day_data))
                
                # Start new day
                current_date = date
                day_data = [item]
            else:
                day_data.append(item)
        
        # Process last day
        if day_data:
            daily_forecast.append(self._process_day_forecast(current_date, day_data))
        
        # Limit to requested days
        daily_forecast = daily_forecast[:days]
        
        # Cache for 2 hours
        cache.set(cache_key, daily_forecast, 60 * 120)
        
        return daily_forecast
    
    def _process_day_forecast(self, date, hourly_data):
        """Process hourly data into daily summary"""
        temps = [item['main']['temp'] for item in hourly_data]
        conditions = [item['weather'][0]['main'].lower() for item in hourly_data]
        
        # Get most common condition
        from collections import Counter
        condition_count = Counter(conditions)
        main_condition = condition_count.most_common(1)[0][0]
        
        return {
            'date': date.isoformat(),
            'day_name': date.strftime('%A'),
            'temp_min': round(min(temps)),
            'temp_max': round(max(temps)),
            'temp_avg': round(sum(temps) / len(temps)),
            'condition': main_condition,
            'description': hourly_data[0]['weather'][0]['description'],
            'icon': hourly_data[0]['weather'][0]['icon'],
            'humidity': round(sum(item['main']['humidity'] for item in hourly_data) / len(hourly_data)),
            'wind_speed': round(sum(item['wind']['speed'] for item in hourly_data) / len(hourly_data) * 3.6, 1)
        }
    
    def is_outfit_suitable(self, outfit, weather_data):
        """
        Check if an outfit is suitable for the weather
        
        Args:
            outfit: Outfit model instance
            weather_data: Weather data dict from get_current_weather
        
        Returns:
            tuple: (is_suitable: bool, reason: str)
        """
        if not weather_data:
            return (True, "Weather data not available")
        
        temp = weather_data['temperature']
        condition = weather_data['condition']
        
        # Check temperature range
        if outfit.min_temperature is not None and temp < outfit.min_temperature:
            return (False, f"Too cold ({temp}°C). Outfit minimum is {outfit.min_temperature}°C")
        
        if outfit.max_temperature is not None and temp > outfit.max_temperature:
            return (False, f"Too hot ({temp}°C). Outfit maximum is {outfit.max_temperature}°C")
        
        # Check weather condition
        if outfit.suitable_weather:
            # Map weather conditions
            condition_map = {
                'clear': 'sunny',
                'clouds': 'cloudy',
                'rain': 'rainy',
                'drizzle': 'rainy',
                'thunderstorm': 'stormy',
                'snow': 'snowy',
                'mist': 'foggy',
                'fog': 'foggy'
            }
            
            mapped_condition = condition_map.get(condition, condition)
            
            if mapped_condition not in outfit.suitable_weather:
                return (False, f"Not suitable for {condition} weather")
        
        return (True, "Outfit is suitable for the weather")
    
    def get_outfit_recommendations_by_weather(self, outfits, weather_data):
        """
        Filter and rank outfits based on weather suitability
        
        Args:
            outfits: QuerySet of outfits
            weather_data: Weather data dict
        
        Returns:
            list: Outfits sorted by suitability
        """
        if not weather_data:
            return outfits
        
        suitable_outfits = []
        
        for outfit in outfits:
            is_suitable, reason = self.is_outfit_suitable(outfit, weather_data)
            if is_suitable:
                suitable_outfits.append(outfit)
        
        return suitable_outfits

    def get_forecast_for_date(self, location: str, target_date) -> Optional[Dict]:
        """
        Get weather forecast for a specific date
        
        Args:
            location: City name
            target_date: Date object or YYYY-MM-DD string
        
        Returns:
            dict: Weather data for that day or None
        """
        if isinstance(target_date, str):
            try:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                logger.error(f"Invalid date string format: {target_date}")
                return None
                
        # Get 7-day forecast
        forecast_list = self.get_forecast(location, days=7)
        
        # Fallback to Tunis if location fails (e.g. detailed address provided)
        if not forecast_list and location != 'Tunis':
            logger.info(f"Location '{location}' failed to return forecast, attempting fallback to 'Tunis'")
            forecast_list = self.get_forecast('Tunis', days=7)
            
        if not forecast_list:
            logger.warning(f"No forecast list returned for location: {location} (or fallback)")
            return None
            
        target_str = target_date.isoformat()
        
        for day_data in forecast_list:
            if day_data['date'] == target_str:
                return day_data
        
        return None


# Global instance (needed by planner.views)
weather_service = WeatherService()
