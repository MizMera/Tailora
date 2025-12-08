import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from outfits.models import StyleChallenge


class Command(BaseCommand):
    help = "Create daily and weekly public challenges if they don't already exist for the current period."

    def add_arguments(self, parser):
        parser.add_argument(
            "--owner-email",
            help="Email of the user who should own the auto-created challenges. Defaults to first superuser, else first user.",
        )

    def handle(self, *args, **options):
        owner = self._pick_owner(options.get("owner_email"))
        if not owner:
            self.stdout.write(self.style.ERROR("No users available to own challenges. Create a user first."))
            return

        today = timezone.now().date()
        created = []

        # Create daily challenges for past 3 days and today
        for days_ago in [3, 2, 1, 0]:
            target_date = today - timedelta(days=days_ago)
            daily = self._ensure_daily_challenge(owner, target_date)
            if daily:
                created.append(daily)

        # Create weekly challenges for past 2 weeks
        for weeks_ago in [1, 0]:
            target_date = today - timedelta(weeks=weeks_ago)
            weekly = self._ensure_weekly_challenge(owner, target_date)
            if weekly:
                created.append(weekly)

        if created:
            for ch in created:
                self.stdout.write(self.style.SUCCESS(f"Created challenge: {ch.name}"))
        else:
            self.stdout.write(self.style.WARNING("All challenges already exist for these periods."))

    def _pick_owner(self, email_hint):
        User = get_user_model()
        if email_hint:
            return User.objects.filter(email=email_hint).first()
        owner = User.objects.filter(is_superuser=True).order_by("id").first()
        if owner:
            return owner
        return User.objects.order_by("id").first()

    def _ensure_daily_challenge(self, owner, today):
        # One daily challenge per calendar day
        existing = StyleChallenge.objects.filter(
            challenge_type="daily",
            start_date=today,
        ).first()
        if existing:
            return None

        theme = random.choice([
            "Monochrome Monday",
            "Texture Tuesday",
            "Warm Tones",
            "Cool Contrast",
            "Minimalist Day",
            "Bold Accent",
            "Pattern Play",
        ])

        challenge = StyleChallenge.objects.create(
            name=f"Daily Challenge {today.isoformat()}",
            description=f"Style prompt: {theme} — build an outfit that fits today's theme.",
            challenge_type="daily",
            duration_days=1,
            rules={"theme": theme, "required_outfits": 1},
            created_by=owner,
            is_public=True,
            start_date=today,
            end_date=today,
        )
        return challenge

    def _ensure_weekly_challenge(self, owner, today):
        # Week starts on Monday
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        existing = StyleChallenge.objects.filter(
            challenge_type="weekly",
            start_date=monday,
        ).first()
        if existing:
            return None

        theme = random.choice([
            "Denim Week",
            "Earth Tones",
            "Sporty Street",
            "Office Chic",
            "Weekend Getaway",
            "Layering Lab",
            "Color Splash",
        ])

        challenge = StyleChallenge.objects.create(
            name=f"Weekly Challenge {monday.isoformat()} - {sunday.isoformat()}",
            description=f"Weekly theme: {theme}. Create outfits that match throughout the week.",
            challenge_type="weekly",
            duration_days=7,
            rules={"theme": theme, "required_outfits": 3},
            created_by=owner,
            is_public=True,
            start_date=monday,
            end_date=sunday,
        )
        return challenge
