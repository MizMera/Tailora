"""
Django Management Command: Send Outfit Reminders

Sends email reminders to users about their planned outfits.

Usage:
    # Send evening reminders (tomorrow's outfit)
    python manage.py send_outfit_reminders --time evening
    
    # Send morning reminders (today's outfit)
    python manage.py send_outfit_reminders --time morning
    
    # Send to specific user
    python manage.py send_outfit_reminders --time evening --email user@example.com
    
    # Dry run (don't actually send)
    python manage.py send_outfit_reminders --time evening --dry-run

Schedule with cron (Linux) or Task Scheduler (Windows):
    # Evening at 8 PM: 0 20 * * * cd /path/to/tailora && python manage.py send_outfit_reminders --time evening
    # Morning at 7 AM: 0 7 * * * cd /path/to/tailora && python manage.py send_outfit_reminders --time morning
"""

from django.core.management.base import BaseCommand, CommandError
from planner.notification_scheduler import OutfitNotificationScheduler
from users.models import User


class Command(BaseCommand):
    help = 'Send outfit reminder emails to users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--time',
            type=str,
            choices=['morning', 'evening'],
            default='evening',
            help='Time of day for reminders (morning=today, evening=tomorrow)'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Send to a specific user email only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending'
        )

    def handle(self, *args, **options):
        reminder_time = options['time']
        email_filter = options.get('email')
        dry_run = options.get('dry_run', False)
        
        scheduler = OutfitNotificationScheduler()
        
        self.stdout.write(
            self.style.NOTICE(f"Running {reminder_time} outfit reminders...")
        )
        
        if email_filter:
            # Send to specific user
            try:
                user = User.objects.get(email=email_filter)
            except User.DoesNotExist:
                raise CommandError(f"User with email '{email_filter}' not found")
            
            if dry_run:
                slot = scheduler.get_tomorrow_outfit(user) if reminder_time == 'evening' else scheduler.get_today_outfit(user)
                if slot and slot.primary_outfit:
                    self.stdout.write(
                        f"Would send to {user.email}: {slot.primary_outfit.name} for {slot.day_name}"
                    )
                else:
                    self.stdout.write(f"No outfit found for {user.email}")
            else:
                if reminder_time == 'evening':
                    success = scheduler.send_evening_reminder(user)
                else:
                    success = scheduler.send_morning_reminder(user)
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"Sent reminder to {user.email}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"No outfit to send for {user.email}")
                    )
        else:
            # Send to all eligible users
            if dry_run:
                users = scheduler.get_users_for_notification(reminder_time)
                self.stdout.write(f"Would send to {len(users)} users:")
                for user in users[:10]:  # Show first 10
                    slot = scheduler.get_tomorrow_outfit(user) if reminder_time == 'evening' else scheduler.get_today_outfit(user)
                    if slot and slot.primary_outfit:
                        self.stdout.write(f"  - {user.email}: {slot.primary_outfit.name}")
                    else:
                        self.stdout.write(f"  - {user.email}: (no outfit)")
                if len(users) > 10:
                    self.stdout.write(f"  ... and {len(users) - 10} more")
            else:
                results = scheduler.run_reminders(reminder_time)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Done! Sent: {results['sent']}, Skipped: {results['skipped']}, Failed: {results['failed']}"
                    )
                )
