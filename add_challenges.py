#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tailora_project.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from outfits.models import StyleChallenge
from users.models import User

today = timezone.now().date()
creator = User.objects.filter(is_staff=True).first() or User.objects.first()

# Delete old challenges
print("Deleting old challenges...")
StyleChallenge.objects.all().delete()
print("✓ Cleared\n")

daily_challenges = [
    {'name': 'Monochrome Monday', 'description': 'Create an outfit using only one color palette', 'challenge_type': 'daily', 'duration_days': 1},
    {'name': 'Thrift Tuesday', 'description': 'Style an outfit featuring thrifted pieces', 'challenge_type': 'daily', 'duration_days': 1},
    {'name': 'Texture Wednesday', 'description': 'Mix different textures - denim, silk, leather, knit', 'challenge_type': 'daily', 'duration_days': 1},
    {'name': 'Casual Thursday', 'description': 'Create the perfect casual weekend outfit', 'challenge_type': 'daily', 'duration_days': 1},
    {'name': 'Fancy Friday', 'description': 'Dress up and create your best elevated outfit', 'challenge_type': 'daily', 'duration_days': 1},
]

weekly_challenges = [
    {'name': 'Seasonal Style Week', 'description': 'Create 5 outfits that showcase seasonal trends', 'challenge_type': 'weekly', 'duration_days': 7},
    {'name': 'Color Theory Challenge', 'description': 'Experiment with color combinations. Submit 5 unique outfits', 'challenge_type': 'weekly', 'duration_days': 7},
    {'name': 'Minimalist Week', 'description': 'Create 5 outfits using 10 or fewer pieces total', 'challenge_type': 'weekly', 'duration_days': 7},
    {'name': 'Occasion Styling Sprint', 'description': 'Style outfits for 5 different occasions', 'challenge_type': 'weekly', 'duration_days': 7},
    {'name': 'Wardrobe Remix Challenge', 'description': 'Create 7 different outfits using the same 10 base pieces', 'challenge_type': 'weekly', 'duration_days': 7},
]

count = 0
print("Creating Daily Challenges:")
for data in daily_challenges:
    data['start_date'] = today
    data['end_date'] = today
    data['created_by'] = creator
    data['is_public'] = True
    ch = StyleChallenge.objects.create(**data)
    count += 1
    print(f'  ✓ {data["name"]}')

print("\nCreating Weekly Challenges:")
for data in weekly_challenges:
    data['start_date'] = today
    data['end_date'] = today + timedelta(days=6)
    data['created_by'] = creator
    data['is_public'] = True
    ch = StyleChallenge.objects.create(**data)
    count += 1
    print(f'  ✓ {data["name"]}')

print(f'\nTotal challenges created: {count}')
