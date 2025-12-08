from django.core.management.base import BaseCommand
from recommendations.models import ColorCompatibility

class Command(BaseCommand):
    help = 'Populates the database with basic color compatibility rules'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating color compatibility rules...')
        
        # Basic color rules (Color 1, Color 2, Score 0-100, Type)
        # Hex codes are approximate for reference
        colors_hex = {
            'black': '#000000', 'white': '#FFFFFF', 'red': '#FF0000', 
            'blue': '#0000FF', 'beige': '#F5F5DC', 'grey': '#808080',
            'navy': '#000080', 'brown': '#A52A2A', 'pink': '#FFC0CB',
            'orange': '#FFA500', 'purple': '#800080', 'yellow': '#FFFF00',
            'green': '#008000', 'olive': '#808000', 'cream': '#FFFDD0',
            'burgundy': '#800020', 'camel': '#C19A6B'
        }

        rules = [
            # Neutrals go with everything
            ('black', 'white', 100, 'complementary'),
            ('black', 'red', 90, 'contrast'),
            ('black', 'blue', 85, 'contrast'),
            ('white', 'blue', 95, 'fresh'),
            ('white', 'beige', 90, 'neutral'),
            ('grey', 'navy', 85, 'professional'),
            
            # Monochromatic
            ('navy', 'blue', 90, 'monochromatic'),
            ('beige', 'brown', 85, 'monochromatic'),
            ('pink', 'red', 80, 'monochromatic'),
            
            # Complementary
            ('blue', 'orange', 85, 'complementary'),
            ('purple', 'yellow', 80, 'complementary'),
            ('red', 'green', 70, 'complementary'),  # Tricky but classic
            
            # Analogous
            ('blue', 'green', 85, 'analogous'),
            ('red', 'orange', 85, 'analogous'),
            ('yellow', 'orange', 85, 'analogous'),
            
            # Classic Combos
            ('navy', 'white', 100, 'nautical'),
            ('olive', 'cream', 90, 'earth_tone'),
            ('burgundy', 'grey', 90, 'sophisticated'),
            ('camel', 'black', 95, 'chic'),
        ]
        
        count = 0
        for c1, c2, score, rule_type in rules:
            hex1 = colors_hex.get(c1, '#000000')
            hex2 = colors_hex.get(c2, '#000000')
            
            # Create both directions
            obj1, created1 = ColorCompatibility.objects.get_or_create(
                color1=c1, color2=c2,
                defaults={
                    'compatibility_score': score, 
                    'relationship_type': rule_type,
                    'color1_hex': hex1,
                    'color2_hex': hex2
                }
            )
            
            obj2, created2 = ColorCompatibility.objects.get_or_create(
                color1=c2, color2=c1,
                defaults={
                    'compatibility_score': score, 
                    'relationship_type': rule_type,
                    'color1_hex': hex2,
                    'color2_hex': hex1
                }
            )
            
            if created1: count += 1
            if created2: count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully added {count} color rules'))
