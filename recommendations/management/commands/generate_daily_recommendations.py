"""
Management command to generate daily outfit recommendations for all users
Run this daily via cron/scheduler to create new recommendations
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from recommendations.ai_engine import OutfitRecommendationEngine

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate daily outfit recommendations for all active users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            nargs='+',
            help='Specific user IDs to generate recommendations for',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of recommendations to generate per user (default: 3)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if recommendations already exist for today',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        count = options['count']
        force = options['force']
        
        # Determine which users to process
        if options['users']:
            users = User.objects.filter(id__in=options['users'], is_active=True)
            self.stdout.write(f'Processing {len(options["users"])} specific user(s)...')
        else:
            users = User.objects.filter(is_active=True)
            self.stdout.write(f'Processing all {users.count()} active users...')
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for user in users:
            try:
                # Check if recommendations already exist
                from recommendations.models import DailyRecommendation
                existing = DailyRecommendation.objects.filter(
                    user=user,
                    recommendation_date=today
                ).count()
                
                if existing > 0 and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⏭️  User {user.email}: Already has {existing} recommendations for today (use --force to regenerate)'
                        )
                    )
                    skipped_count += 1
                    continue
                
                # Delete existing if forcing regeneration
                if existing > 0 and force:
                    DailyRecommendation.objects.filter(
                        user=user,
                        recommendation_date=today
                    ).delete()
                    self.stdout.write(f'🗑️  Deleted {existing} existing recommendations for {user.email}')
                
                # Generate recommendations
                engine = OutfitRecommendationEngine(user)
                recommendations = engine.generate_daily_recommendations(date=today, count=count)
                
                if recommendations:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ User {user.email}: Generated {len(recommendations)} recommendations'
                        )
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  User {user.email}: No recommendations generated (insufficient wardrobe?)'
                        )
                    )
                    skipped_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ User {user.email}: Error - {str(e)}'
                    )
                )
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully processed: {success_count}'))
        self.stdout.write(self.style.WARNING(f'⏭️  Skipped: {skipped_count}'))
        self.stdout.write(self.style.ERROR(f'❌ Errors: {error_count}'))
        self.stdout.write('='*60 + '\n')
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'🎉 Daily recommendations generated successfully for {today}!'
                )
            )
