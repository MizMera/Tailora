"""
Outfit Notification Scheduler

Sends email reminders about tomorrow's outfit from the weekly planner.
Can be run via cron or Windows Task Scheduler.

Usage:
    # Evening reminders (run at 8 PM)
    python manage.py send_outfit_reminders --time evening
    
    # Morning reminders (run at 7 AM)
    python manage.py send_outfit_reminders --time morning
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from typing import Optional, List

from users.models import User, Notification
from planner.models import WeeklyPlan, DailyPlanSlot


class OutfitNotificationScheduler:
    """
    Scheduler for sending outfit reminder emails
    """
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
    
    def get_users_for_notification(self, reminder_time: str) -> List[User]:
        """
        Get users who should receive notifications at this time
        
        Args:
            reminder_time: 'morning' or 'evening'
        """
        users = []
        for user in User.objects.filter(is_active=True, status='active'):
            try:
                profile = user.style_profile
                prefs = profile.get_notification_prefs()
                
                if not prefs.get('outfit_reminder', True):
                    continue
                if not prefs.get('email_notifications', True):
                    continue
                
                user_time = prefs.get('reminder_time', 'evening')
                if user_time == 'both' or user_time == reminder_time:
                    users.append(user)
            except Exception:
                # User without style profile - use defaults (evening)
                if reminder_time == 'evening':
                    users.append(user)
        
        return users
    
    def get_tomorrow_outfit(self, user: User) -> Optional[DailyPlanSlot]:
        """Get the outfit planned for tomorrow"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        week_start = tomorrow - timedelta(days=tomorrow.weekday())
        
        try:
            weekly_plan = WeeklyPlan.objects.filter(
                user=user,
                week_start=week_start
            ).first()
            
            if weekly_plan:
                return weekly_plan.daily_slots.filter(date=tomorrow).first()
        except Exception:
            pass
        
        return None
    
    def get_today_outfit(self, user: User) -> Optional[DailyPlanSlot]:
        """Get the outfit planned for today (morning reminder)"""
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        try:
            weekly_plan = WeeklyPlan.objects.filter(
                user=user,
                week_start=week_start
            ).first()
            
            if weekly_plan:
                return weekly_plan.daily_slots.filter(date=today).first()
        except Exception:
            pass
        
        return None
    
    def send_evening_reminder(self, user: User) -> bool:
        """Send evening reminder about tomorrow's outfit"""
        slot = self.get_tomorrow_outfit(user)
        
        if not slot or not slot.primary_outfit:
            return False
        
        return self._send_outfit_email(
            user=user,
            slot=slot,
            subject=f"👔 Your outfit for tomorrow ({slot.day_name})",
            template='email/outfit_reminder_evening.html',
            context_extra={'is_evening': True}
        )
    
    def send_morning_reminder(self, user: User) -> bool:
        """Send morning reminder about today's outfit"""
        slot = self.get_today_outfit(user)
        
        if not slot or not slot.primary_outfit:
            return False
        
        return self._send_outfit_email(
            user=user,
            slot=slot,
            subject=f"☀️ Time to get dressed! Today's outfit ready",
            template='email/outfit_reminder_morning.html',
            context_extra={'is_morning': True}
        )
    
    def _send_outfit_email(
        self, 
        user: User, 
        slot: DailyPlanSlot,
        subject: str,
        template: str,
        context_extra: dict = None
    ) -> bool:
        """Send outfit reminder email"""
        try:
            outfit = slot.primary_outfit
            items = list(outfit.items.all()[:6])
            
            context = {
                'user': user,
                'slot': slot,
                'outfit': outfit,
                'items': items,
                'weather': {
                    'temperature': slot.temperature,
                    'condition': slot.weather_condition,
                },
                'day_name': slot.day_name,
                'date': slot.date,
                'selection_reason': slot.selection_reason,
                'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
                **(context_extra or {})
            }
            
            html_message = render_to_string(template, context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=self.from_email,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Create in-app notification too
            Notification.objects.create(
                user=user,
                notification_type='outfit_ready',
                title=subject,
                message=f"Your outfit '{outfit.name}' is ready for {slot.day_name}",
                related_object_type='DailyPlanSlot',
                related_object_id=slot.id
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to send reminder to {user.email}: {e}")
            return False
    
    def run_reminders(self, reminder_time: str) -> dict:
        """
        Run reminders for all eligible users
        
        Args:
            reminder_time: 'morning' or 'evening'
            
        Returns:
            dict with counts of sent/failed
        """
        users = self.get_users_for_notification(reminder_time)
        results = {'sent': 0, 'failed': 0, 'skipped': 0}
        
        for user in users:
            if reminder_time == 'evening':
                success = self.send_evening_reminder(user)
            else:
                success = self.send_morning_reminder(user)
            
            if success:
                results['sent'] += 1
            elif success is False:
                results['skipped'] += 1  # No outfit to remind about
            else:
                results['failed'] += 1
        
        return results
