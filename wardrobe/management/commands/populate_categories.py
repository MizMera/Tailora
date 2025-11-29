"""
Populate predefined clothing categories for better AI recommendations
Run: python manage.py populate_categories
"""
from django.core.management.base import BaseCommand
from wardrobe.models import ClothingCategory


class Command(BaseCommand):
    help = 'Populates predefined clothing categories for AI recommendations'

    def handle(self, *args, **options):
        # Standard categories that AI engine recognizes
        categories = [
            # Essential Categories (AI needs these)
            {'name': 'Top', 'icon': ''},
            {'name': 'Bottom', 'icon': ''},
            {'name': 'Dress', 'icon': ''},
            
            # Outerwear
            {'name': 'Jacket', 'icon': ''},
            {'name': 'Coat', 'icon': ''},
            {'name': 'Blazer', 'icon': ''},
            
            # Footwear
            {'name': 'Shoe', 'icon': ''},
            {'name': 'Boot', 'icon': ''},
            {'name': 'Sandal', 'icon': ''},
            
            # Accessories
            {'name': 'Bag', 'icon': ''},
            {'name': 'Hat', 'icon': ''},
            {'name': 'Scarf', 'icon': ''},
            {'name': 'Belt', 'icon': ''},
            {'name': 'Jewelry', 'icon': ''},
            
            # Activewear
            {'name': 'Sport', 'icon': ''},
            {'name': 'Swim', 'icon': ''},
        ]

        created_count = 0
        for cat_data in categories:
            category, created = ClothingCategory.objects.get_or_create(
                name=cat_data['name'],
                is_custom=False,
                defaults={
                    'icon': cat_data['icon'],
                    'user': None  # Global categories
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(f'  Category already exists: {category.name}')

        self.stdout.write(
            self.style.SUCCESS(f'\nCompleted! Created {created_count} new categories.')
        )
        self.stdout.write(
            self.style.WARNING(f'Total categories: {ClothingCategory.objects.filter(is_custom=False).count()}')
        )
