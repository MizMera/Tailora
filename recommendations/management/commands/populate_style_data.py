from django.core.management.base import BaseCommand
from recommendations.models import ColorCompatibility, StyleRule


class Command(BaseCommand):
    help = 'Populate color compatibility and style rules'

    def handle(self, *args, **kwargs):
        # Color compatibility rules
        color_pairs = [
            # Complementary colors
            ('Blue', '#0000FF', 'Orange', '#FFA500', 0.9, 'complementary'),
            ('Red', '#FF0000', 'Green', '#00FF00', 0.85, 'complementary'),
            ('Yellow', '#FFFF00', 'Purple', '#800080', 0.8, 'complementary'),
            
            # Analogous colors
            ('Blue', '#0000FF', 'Green', '#00FF00', 0.85, 'analogous'),
            ('Red', '#FF0000', 'Orange', '#FFA500', 0.9, 'analogous'),
            ('Yellow', '#FFFF00', 'Orange', '#FFA500', 0.95, 'analogous'),
            
            # Neutral combinations
            ('Black', '#000000', 'White', '#FFFFFF', 1.0, 'neutral'),
            ('Black', '#000000', 'Gray', '#808080', 0.95, 'neutral'),
            ('White', '#FFFFFF', 'Gray', '#808080', 0.95, 'neutral'),
            ('Beige', '#F5F5DC', 'Brown', '#8B4513', 0.9, 'neutral'),
            
            # Classic combinations
            ('Navy Blue', '#000080', 'White', '#FFFFFF', 0.95, 'classic'),
            ('Black', '#000000', 'Red', '#FF0000', 0.9, 'classic'),
            ('Gray', '#808080', 'Pink', '#FFC0CB', 0.85, 'classic'),
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
                'name': 'Rule of 3 colors',
                'description': 'Limit an outfit to a maximum of 3 main colors',
                'conditions': {'max_colors': 3},
                'recommendation': 'Choose a maximum of 3 colors for a harmonious look',
                'importance': 0.8
            },
            {
                'category': 'pattern',
                'name': 'Pattern mixing',
                'description': 'Do not mix more than 2 different patterns',
                'conditions': {'max_patterns': 2},
                'recommendation': 'Limit to 2 patterns and vary the scales',
                'importance': 0.7
            },
            {
                'category': 'season',
                'name': 'Seasonal consistency',
                'description': 'Favor clothing suitable for the season',
                'conditions': {'match_season': True},
                'recommendation': 'Check that clothing matches the season',
                'importance': 0.9
            },
            {
                'category': 'proportion',
                'name': 'Top/bottom balance',
                'description': 'Balance volumes between top and bottom',
                'conditions': {'balance_volumes': True},
                'recommendation': 'Loose top with fitted bottom or vice versa',
                'importance': 0.8
            },
            {
                'category': 'style_mix',
                'name': 'Style consistency',
                'description': 'Maintain consistency when mixing styles',
                'conditions': {'style_consistency': 0.7},
                'recommendation': 'Mix max 2 different styles',
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
