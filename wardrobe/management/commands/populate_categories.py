from django.core.management.base import BaseCommand
from wardrobe.models import ClothingCategory


class Command(BaseCommand):
    help = 'Populate default clothing categories'

    def handle(self, *args, **kwargs):
        categories = [
            # Main categories
            {'name': 'Hauts', 'icon': '👕'},
            {'name': 'Bas', 'icon': '👖'},
            {'name': 'Robes', 'icon': '👗'},
            {'name': 'Vestes & Manteaux', 'icon': '🧥'},
            {'name': 'Chaussures', 'icon': '👞'},
            {'name': 'Accessoires', 'icon': '👜'},
            {'name': 'Sous-vêtements', 'icon': '🩱'},
            {'name': 'Sport', 'icon': '🏃'},
        ]
        
        created_count = 0
        for cat_data in categories:
            category, created = ClothingCategory.objects.get_or_create(
                name=cat_data['name'],
                is_custom=False,
                user=None,
                defaults={'icon': cat_data['icon']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
        
        # Create subcategories for Hauts
        hauts = ClothingCategory.objects.get(name='Hauts', is_custom=False, user=None)
        subcategories_hauts = ['T-shirts', 'Chemises', 'Pulls', 'Gilets', 'Tops', 'Débardeurs']
        
        for subcat_name in subcategories_hauts:
            subcat, created = ClothingCategory.objects.get_or_create(
                name=subcat_name,
                parent_category=hauts,
                is_custom=False,
                user=None
            )
            if created:
                created_count += 1
        
        # Create subcategories for Bas
        bas = ClothingCategory.objects.get(name='Bas', is_custom=False, user=None)
        subcategories_bas = ['Jeans', 'Pantalons', 'Shorts', 'Jupes', 'Leggings']
        
        for subcat_name in subcategories_bas:
            subcat, created = ClothingCategory.objects.get_or_create(
                name=subcat_name,
                parent_category=bas,
                is_custom=False,
                user=None
            )
            if created:
                created_count += 1
        
        # Create subcategories for Chaussures
        chaussures = ClothingCategory.objects.get(name='Chaussures', is_custom=False, user=None)
        subcategories_chaussures = ['Baskets', 'Bottes', 'Sandales', 'Talons', 'Mocassins']
        
        for subcat_name in subcategories_chaussures:
            subcat, created = ClothingCategory.objects.get_or_create(
                name=subcat_name,
                parent_category=chaussures,
                is_custom=False,
                user=None
            )
            if created:
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} categories')
        )
