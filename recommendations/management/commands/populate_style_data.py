from django.core.management.base import BaseCommand
from recommendations.models import ColorCompatibility, StyleRule


class Command(BaseCommand):
    help = 'Populate color compatibility and style rules'

    def handle(self, *args, **kwargs):
        # Color compatibility rules
        color_pairs = [
            # Complementary colors
            ('Bleu', '#0000FF', 'Orange', '#FFA500', 0.9, 'complementary'),
            ('Rouge', '#FF0000', 'Vert', '#00FF00', 0.85, 'complementary'),
            ('Jaune', '#FFFF00', 'Violet', '#800080', 0.8, 'complementary'),
            
            # Analogous colors
            ('Bleu', '#0000FF', 'Vert', '#00FF00', 0.85, 'analogous'),
            ('Rouge', '#FF0000', 'Orange', '#FFA500', 0.9, 'analogous'),
            ('Jaune', '#FFFF00', 'Orange', '#FFA500', 0.95, 'analogous'),
            
            # Neutral combinations
            ('Noir', '#000000', 'Blanc', '#FFFFFF', 1.0, 'neutral'),
            ('Noir', '#000000', 'Gris', '#808080', 0.95, 'neutral'),
            ('Blanc', '#FFFFFF', 'Gris', '#808080', 0.95, 'neutral'),
            ('Beige', '#F5F5DC', 'Marron', '#8B4513', 0.9, 'neutral'),
            
            # Classic combinations
            ('Bleu Marine', '#000080', 'Blanc', '#FFFFFF', 0.95, 'classic'),
            ('Noir', '#000000', 'Rouge', '#FF0000', 0.9, 'classic'),
            ('Gris', '#808080', 'Rose', '#FFC0CB', 0.85, 'classic'),
        ]
        
        created_count = 0
        for color1, hex1, color2, hex2, score, rel_type in color_pairs:
            _, created = ColorCompatibility.objects.get_or_create(
                color1=color1,
                color1_hex=hex1,
                color2=color2,
                color2_hex=hex2,
                defaults={
                    'compatibility_score': score,
                    'relationship_type': rel_type
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created color pair: {color1} + {color2}')
                )
        
        # Style rules
        style_rules = [
            {
                'category': 'color',
                'name': 'Règle des 3 couleurs',
                'description': 'Limiter une tenue à 3 couleurs principales maximum',
                'conditions': {'max_colors': 3},
                'recommendation': 'Choisir 3 couleurs au maximum pour un look harmonieux',
                'importance': 0.8
            },
            {
                'category': 'pattern',
                'name': 'Mélange de motifs',
                'description': 'Ne pas mélanger plus de 2 motifs différents',
                'conditions': {'max_patterns': 2},
                'recommendation': 'Limiter à 2 motifs et varier les échelles',
                'importance': 0.7
            },
            {
                'category': 'season',
                'name': 'Cohérence saisonnière',
                'description': 'Privilégier les vêtements adaptés à la saison',
                'conditions': {'match_season': True},
                'recommendation': 'Vérifier que les vêtements correspondent à la saison',
                'importance': 0.9
            },
            {
                'category': 'proportion',
                'name': 'Équilibre haut/bas',
                'description': 'Équilibrer les volumes entre le haut et le bas',
                'conditions': {'balance_volumes': True},
                'recommendation': 'Haut ample avec bas ajusté ou inversement',
                'importance': 0.8
            },
            {
                'category': 'style_mix',
                'name': 'Cohérence de style',
                'description': 'Maintenir une cohérence dans le mélange de styles',
                'conditions': {'style_consistency': 0.7},
                'recommendation': 'Mélanger max 2 styles différents',
                'importance': 0.75
            },
        ]
        
        rules_created = 0
        for rule_data in style_rules:
            _, created = StyleRule.objects.get_or_create(
                category=rule_data['category'],
                rule_name=rule_data['name'],
                defaults={
                    'description': rule_data['description'],
                    'conditions': rule_data['conditions'],
                    'recommendation': rule_data['recommendation'],
                    'importance': rule_data['importance'],
                    'is_active': True
                }
            )
            if created:
                rules_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created rule: {rule_data["name"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} color pairs and {rules_created} style rules'
            )
        )
