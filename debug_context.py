from datetime import date
from planner.weather_service import WeatherService

service = WeatherService()
today = date(2025, 12, 13)
print(f"Testing weather for date: {today}")

locations = ["Tunis", "Rue de Palestine, Lafayette, Les Jardins", "Paris"]

for loc in locations:
    print(f"\nLocation: '{loc}'")
    try:
        data = service.get_forecast_for_date(loc, today)
        print(f"Result: {data}")
    except Exception as e:
        print(f"Error: {e}")
