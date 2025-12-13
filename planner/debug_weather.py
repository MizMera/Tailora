
import os
import sys
import django
from datetime import date

# Setup Django environment
sys.path.append('d:\\app\\Tailora')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tailora.settings')
django.setup()

from planner.weather_service import WeatherService

def test_weather():
    service = WeatherService()
    today = date(2025, 12, 13) # Using the date from context/screenshot
    
    cities_to_test = [
        "Tunis",
        "Rue de Palestine, Lafayette, Les Jardins", # The address from screenshot
        "Paris",
    ]

    print(f"Testing weather for date: {today}")

    for location in cities_to_test:
        print(f"\n--- Testing location: '{location}' ---")
        
        # Test 1: Forecast for date
        forecast = service.get_forecast_for_date(location, today)
        if forecast:
            print(f"✅ Success! Found forecast: {forecast['temperature']}°C, {forecast['condition']}")
        else:
            print(f"❌ Failed to get forecast for date.")

        # Test 2: General Forecast (list) to see if API returns anything at all
        full_forecast = service.get_forecast(location)
        if full_forecast:
            print(f"   (API returned {len(full_forecast)} daily usage items)")
        else:
            print(f"   (API returned NO data for this location)")

if __name__ == "__main__":
    test_weather()
