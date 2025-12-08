"""
Populate simplified clothing categories with AI detection mapping
Run: python manage.py populate_simple_categories
"""
from django.core.management.base import BaseCommand
from wardrobe.models import ClothingCategory


class Command(BaseCommand):
    help = 'Populates simplified clothing categories for AI'

    def handle(self, *args, **options):
        # Delete old verbose categories
        ClothingCategory.objects.filter(is_custom=False).delete()
        
        # SIMPLIFIED categories - short & clear
        categories = [
            # Essential (AI needs these)
            {'name': 'Top', 'icon': '', 'ai_keywords': ['shirt', 'blouse', 't-shirt', 'top', 'sweater', 'hoodie']},
            {'name': 'Bottom', 'icon': '', 'ai_keywords': ['pants', 'jeans', 'skirt', 'shorts', 'trousers']},
            {'name': 'Dress', 'icon': '', 'ai_keywords': ['dress', 'gown', 'robe']},
            
            # Outerwear
            {'name': 'Jacket', 'icon': '', 'ai_keywords': ['jacket', 'coat', 'blazer', 'cardigan']},
            
            # Footwear
            {'name': 'Shoe', 'icon': '', 'ai_keywords': ['shoe', 'sneaker', 'boot', 'sandal', 'heel']},
            
            # Accessories
            {'name': 'Bag', 'icon': '', 'ai_keywords': ['bag', 'purse', 'backpack', 'handbag']},
            {'name': 'Hat', 'icon': '', 'ai_keywords': ['hat', 'cap', 'beanie']},
            {'name': 'Scarf', 'icon': '', 'ai_keywords': ['scarf', 'shawl']},
            {'name': 'Belt', 'icon': '', 'ai_keywords': ['belt']},
            
            # Active
            {'name': 'Sport', 'icon': '', 'ai_keywords': ['sport', 'athletic', 'gym', 'yoga']},
        ]

        for cat_data in categories:
            category = ClothingCategory.objects.create(
                name=cat_data['name'],
                icon=cat_data.get('icon', ''),
                is_custom=False,
                user=None  # Global
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Created: {category.name}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nCreated {len(categories)} simple categories!')
        )
        
        # Show AI mapping
        self.stdout.write('\nAI Detection Keywords:')
        for cat in categories:
            keywords = ', '.join(cat['ai_keywords'][:3])
            self.stdout.write(f'  {cat["name"]}: {keywords}...')
