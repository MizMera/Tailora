from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from outfits.models import StyleChallenge
from users.models import User


class Command(BaseCommand):
    help = 'Add sample challenges (daily, weekly, and regular) to the database'

    def handle(self, *args, **options):
        # Get or create a default creator (admin user)
        try:
            creator = User.objects.filter(is_staff=True).first()
            if not creator:
                creator = User.objects.first()
        except:
            self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
            return

        today = timezone.now().date()
        
        # Daily Challenges
        daily_challenges = [
            {
                'name': 'Monochrome Monday',
                'description': 'Create an outfit using only one color palette. Show your creativity with different shades!',
                'challenge_type': 'daily',
                'duration_days': 1,
                'is_public': True,
            },
            {
                'name': 'Thrift Tuesday',
                'description': 'Style an outfit featuring your favorite thrifted or vintage pieces.',
                'challenge_type': 'daily',
                'duration_days': 1,
                'is_public': True,
            },
            {
                'name': 'Texture Wednesday',
                'description': 'Mix and match different textures - denim, silk, leather, knit. Create an interesting contrast!',
                'challenge_type': 'daily',
                'duration_days': 1,
                'is_public': True,
            },
            {
                'name': 'Casual Thursday',
                'description': 'Create the perfect casual weekend outfit that\'s comfortable yet stylish.',
                'challenge_type': 'daily',
                'duration_days': 1,
                'is_public': True,
            },
            {
                'name': 'Fancy Friday',
                'description': 'Dress up! Create your best elevated or formal outfit for a special night out.',
                'challenge_type': 'daily',
                'duration_days': 1,
                'is_public': True,
            },
        ]

        # Weekly Challenges
        weekly_challenges = [
            {
                'name': 'Seasonal Style Week',
                'description': 'Create 5 outfits that showcase how you\'re styling current seasonal trends.',
                'challenge_type': 'weekly',
                'duration_days': 7,
                'is_public': True,
            },
            {
                'name': 'Color Theory Challenge',
                'description': 'Experiment with color combinations - complementary, analogous, or triadic. Submit 5 unique color-coordinated outfits.',
                'challenge_type': 'weekly',
                'duration_days': 7,
                'is_public': True,
            },
            {
                'name': 'Minimalist Week',
                'description': 'Create 5 outfits using 10 or fewer pieces total (per outfit). Less is more!',
                'challenge_type': 'weekly',
                'duration_days': 7,
                'is_public': True,
            },
            {
                'name': 'Occasion Styling Sprint',
                'description': 'Style outfits for 5 different occasions - work, casual, formal, gym, and date night.',
                'challenge_type': 'weekly',
                'duration_days': 7,
                'is_public': True,
            },
            {
                'name': 'Wardrobe Remix Challenge',
                'description': 'Create 7 different outfits using the same 10 base pieces. Show your outfit versatility!',
                'challenge_type': 'weekly',
                'duration_days': 7,
                'is_public': True,
            },
        ]

        # Regular Challenges (longer duration)
        regular_challenges = [
            {
                'name': 'Spring Refresh Challenge',
                'description': 'Update your wardrobe with spring pieces. Create 10 outfits featuring seasonal colors and fabrics.',
                'challenge_type': 'regular',
                'duration_days': 14,
                'is_public': True,
            },
            {
                'name': 'Sustainable Style Month',
                'description': 'Complete this month-long challenge by creating outfits using only thrifted, vintage, or ethically-made pieces. Submit 20 outfits.',
                'challenge_type': 'regular',
                'duration_days': 30,
                'is_public': True,
            },
            {
                'name': 'Personal Brand Challenge',
                'description': 'Develop your signature style! Create 15 outfits that showcase your unique aesthetic and personality.',
                'challenge_type': 'regular',
                'duration_days': 21,
                'is_public': True,
            },
            {
                'name': 'Capsule Wardrobe Challenge',
                'description': 'Build a capsule wardrobe with 20-30 essential pieces and create 12 different outfits from them.',
                'challenge_type': 'regular',
                'duration_days': 14,
                'is_public': True,
            },
        ]

        created_count = 0

        # Create daily challenges
        for challenge_data in daily_challenges:
            challenge_data['start_date'] = today
            challenge_data['end_date'] = today
            challenge_data['created_by'] = creator
            
            challenge, created = StyleChallenge.objects.get_or_create(
                name=challenge_data['name'],
                defaults=challenge_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created daily challenge: {challenge.name}')
                )
            else:
                self.stdout.write(f'⊘ Challenge already exists: {challenge.name}')

        # Create weekly challenges
        for challenge_data in weekly_challenges:
            challenge_data['start_date'] = today
            challenge_data['end_date'] = today + timedelta(days=6)
            challenge_data['created_by'] = creator
            
            challenge, created = StyleChallenge.objects.get_or_create(
                name=challenge_data['name'],
                defaults=challenge_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created weekly challenge: {challenge.name}')
                )
            else:
                self.stdout.write(f'⊘ Challenge already exists: {challenge.name}')

        # Create regular challenges
        for challenge_data in regular_challenges:
            challenge_data['start_date'] = today
            challenge_data['end_date'] = today + timedelta(days=challenge_data['duration_days'] - 1)
            challenge_data['created_by'] = creator
            
            challenge, created = StyleChallenge.objects.get_or_create(
                name=challenge_data['name'],
                defaults=challenge_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created regular challenge: {challenge.name}')
                )
            else:
                self.stdout.write(f'⊘ Challenge already exists: {challenge.name}')

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Total challenges created: {created_count}')
        )
