from django.core.management.base import BaseCommand
from wardrobe.models import ClothingCategory


class Command(BaseCommand):
    help = 'Create default clothing categories'

    def handle(self, *args, **kwargs):
        categories = [
            {'name': 'Tops', 'icon': '👕'},
            {'name': 'Bottoms', 'icon': '👖'},
            {'name': 'Dresses', 'icon': '👗'},
            {'name': 'Outerwear', 'icon': '🧥'},
            {'name': 'Shoes', 'icon': '👞'},
            {'name': 'Accessories', 'icon': '👜'},
            {'name': 'Sportswear', 'icon': '🏃'},
            {'name': 'Underwear', 'icon': '🩱'},
            {'name': 'Sleepwear', 'icon': '😴'},
            {'name': 'Bags', 'icon': '🎒'},
            {'name': 'Jewelry', 'icon': '💍'},
            {'name': 'Hats', 'icon': '🎩'},
            {'name': 'Scarves', 'icon': '🧣'},
            {'name': 'Belts', 'icon': '🔗'},
            {'name': 'Socks', 'icon': '🧦'},
        ]

        created_count = 0
        for cat_data in categories:
            category, created = ClothingCategory.objects.get_or_create(
                name=cat_data['name'],
                is_custom=False,
                defaults={'icon': cat_data['icon']}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                self.stdout.write(f'Category already exists: {category.name}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal categories created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total categories in database: {ClothingCategory.objects.filter(is_custom=False).count()}'))
