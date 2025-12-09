"""
Laundry Scheduler AI for Tailora

Tracks clothing wear/wash cycles and alerts users when:
- Items need washing before planned wear
- Items won't be dry in time for planned wear
- Items are still at dry cleaners when needed
"""

from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from .models import ClothingItem, LaundryAlert
from users.models import User


class LaundrySchedulerAI:
    """
    AI engine for laundry scheduling and alerts
    
    Manages wash thresholds based on clothing type and generates
    proactive alerts for outfit planning conflicts.
    """
    
    # Default wash thresholds by category (lowercase)
    WASH_THRESHOLDS = {
        # Intimates - wash after every wear
        'underwear': 1,
        'socks': 1,
        'briefs': 1,
        'boxers': 1,
        'bra': 2,
        'lingerie': 1,
        
        # Tops - frequent washing
        't-shirt': 2,
        'tee': 2,
        'shirt': 2,
        'blouse': 2,
        'tank top': 1,
        'polo': 2,
        
        # Active wear
        'sportswear': 1,
        'gym': 1,
        'workout': 1,
        'activewear': 1,
        
        # Bottoms - less frequent
        'pants': 4,
        'trousers': 4,
        'jeans': 6,
        'shorts': 3,
        'skirt': 3,
        
        # Dresses
        'dress': 2,
        'gown': 1,
        
        # Outerwear - infrequent
        'jacket': 10,
        'blazer': 8,
        'coat': 15,
        'cardigan': 5,
        'sweater': 4,
        'hoodie': 3,
        'sweatshirt': 3,
        
        # Formal
        'suit': 5,
        'vest': 5,
        'waistcoat': 5,
        
        # Accessories
        'scarf': 10,
        'hat': 15,
        'gloves': 10,
    }
    
    # Default threshold if category not found
    DEFAULT_THRESHOLD = 3
    
    def __init__(self, user: User):
        self.user = user
    
    def get_wash_threshold(self, item: ClothingItem) -> int:
        """
        Get recommended wash threshold for an item based on its category/name.
        Returns user-customized value if set, otherwise AI recommendation.
        """
        # If user has customized, respect their setting
        if item.max_wears_before_wash != 3:  # 3 is the default
            return item.max_wears_before_wash
        
        # Try to match category
        category_name = ''
        if item.category:
            category_name = item.category.name.lower()
        
        item_name = item.name.lower()
        
        # Check both category and item name for matches
        for key, threshold in self.WASH_THRESHOLDS.items():
            if key in category_name or key in item_name:
                return threshold
        
        return self.DEFAULT_THRESHOLD
    
    def auto_set_wash_threshold(self, item: ClothingItem) -> int:
        """
        Automatically set the wash threshold for a new item.
        Updates the item's max_wears_before_wash field.
        """
        threshold = self.get_wash_threshold(item)
        if item.max_wears_before_wash == 3:  # Only if it's still default
            item.max_wears_before_wash = threshold
            item.save(update_fields=['max_wears_before_wash'])
        return threshold
    
    def get_items_needing_wash(self) -> List[ClothingItem]:
        """Get all items that need washing"""
        items = ClothingItem.objects.filter(
            user=self.user,
            status='available'
        )
        return [item for item in items if item.needs_washing()]
    
    def get_items_approaching_wash(self) -> List[ClothingItem]:
        """Get items approaching their wash limit (70%+ of threshold)"""
        items = ClothingItem.objects.filter(
            user=self.user,
            status='available'
        )
        return [item for item in items if item.urgency_level() == 1]
    
    def get_items_at_laundry(self) -> Dict[str, List[ClothingItem]]:
        """Get items currently being washed or at dry cleaners"""
        washing = list(ClothingItem.objects.filter(
            user=self.user,
            status='washing'
        ))
        drying = list(ClothingItem.objects.filter(
            user=self.user,
            status='drying'
        ))
        dry_cleaning = list(ClothingItem.objects.filter(
            user=self.user,
            status='dry_cleaning'
        ))
        
        return {
            'washing': washing,
            'drying': drying,
            'dry_cleaning': dry_cleaning,
        }
    
    def check_outfit_laundry_status(self, outfit) -> Dict:
        """
        Check laundry status for all items in an outfit.
        
        Returns dict with:
        - needs_wash: list of items needing wash
        - approaching: list of items approaching wash limit
        - unavailable: list of items currently being washed/dried
        - is_clear: bool - True if no laundry issues
        """
        result = {
            'needs_wash': [],
            'approaching': [],
            'unavailable': [],
            'is_clear': True,
        }
        
        for item in outfit.items.all():
            urgency = item.urgency_level()
            
            if item.status in ['washing', 'drying', 'dry_cleaning']:
                result['unavailable'].append(item)
                result['is_clear'] = False
            elif urgency >= 2:  # Needs wash or overdue
                result['needs_wash'].append(item)
                result['is_clear'] = False
            elif urgency == 1:  # Approaching
                result['approaching'].append(item)
        
        return result
    
    def check_weekly_plan_conflicts(self, weekly_plan) -> List[Dict]:
        """
        Check all daily slots in a weekly plan for laundry conflicts.
        
        Returns list of conflict dicts per day with issues.
        """
        conflicts = []
        
        for slot in weekly_plan.daily_slots.all():
            if not slot.primary_outfit:
                continue
            
            status = self.check_outfit_laundry_status(slot.primary_outfit)
            
            if not status['is_clear']:
                conflicts.append({
                    'slot': slot,
                    'date': slot.date,
                    'day_name': slot.day_name,
                    'outfit': slot.primary_outfit,
                    'needs_wash': status['needs_wash'],
                    'approaching': status['approaching'],
                    'unavailable': status['unavailable'],
                })
        
        return conflicts
    
    def create_laundry_alerts(self, weekly_plan) -> List[LaundryAlert]:
        """
        Create LaundryAlert objects for all conflicts in a weekly plan.
        Returns list of created alerts.
        """
        from planner.models import DailyPlanSlot
        
        conflicts = self.check_weekly_plan_conflicts(weekly_plan)
        alerts_created = []
        
        for conflict in conflicts:
            slot = conflict['slot']
            planned_date = conflict['date']
            
            # Calculate deadline (day before at 8 PM)
            deadline = datetime.combine(
                planned_date - timedelta(days=1),
                datetime.strptime('20:00', '%H:%M').time()
            )
            deadline = timezone.make_aware(deadline)
            
            # Create alerts for items needing wash
            for item in conflict['needs_wash']:
                # Check if alert already exists
                existing = LaundryAlert.objects.filter(
                    user=self.user,
                    clothing_item=item,
                    planned_date=planned_date,
                    is_resolved=False
                ).exists()
                
                if not existing:
                    alert = LaundryAlert.objects.create(
                        user=self.user,
                        clothing_item=item,
                        planned_date=planned_date,
                        daily_slot=slot,
                        alert_type='needs_washing',
                        priority='high' if item.urgency_level() >= 3 else 'medium',
                        message=f"'{item.name}' needs washing before {slot.day_name}. "
                                f"Worn {item.wears_since_wash}/{item.max_wears_before_wash} times since last wash.",
                        deadline=deadline,
                    )
                    alerts_created.append(alert)
            
            # Create alerts for unavailable items
            for item in conflict['unavailable']:
                existing = LaundryAlert.objects.filter(
                    user=self.user,
                    clothing_item=item,
                    planned_date=planned_date,
                    is_resolved=False
                ).exists()
                
                if not existing:
                    if item.status == 'dry_cleaning':
                        alert_type = 'at_cleaners'
                        msg = f"'{item.name}' is at the dry cleaners. Pick it up before {slot.day_name}."
                    else:
                        alert_type = 'drying_time'
                        msg = f"'{item.name}' is currently {item.get_status_display()}. Make sure it's ready by {slot.day_name}."
                    
                    alert = LaundryAlert.objects.create(
                        user=self.user,
                        clothing_item=item,
                        planned_date=planned_date,
                        daily_slot=slot,
                        alert_type=alert_type,
                        priority='high',
                        message=msg,
                        deadline=deadline,
                    )
                    alerts_created.append(alert)
        
        return alerts_created
    
    def get_active_alerts(self) -> List[LaundryAlert]:
        """Get all unresolved laundry alerts for user"""
        return list(LaundryAlert.objects.filter(
            user=self.user,
            is_resolved=False
        ).select_related('clothing_item', 'daily_slot'))
    
    def resolve_item_alerts(self, item: ClothingItem):
        """Resolve all alerts for an item (when it's washed)"""
        LaundryAlert.objects.filter(
            clothing_item=item,
            is_resolved=False
        ).update(
            is_resolved=True,
            resolved_at=timezone.now()
        )
    
    def mark_item_washed(self, item: ClothingItem) -> ClothingItem:
        """Mark an item as washed and resolve related alerts"""
        item.mark_washed()
        self.resolve_item_alerts(item)
        return item
    
    def mark_item_worn(self, item: ClothingItem) -> ClothingItem:
        """Mark an item as worn (increments wear counter)"""
        item.mark_worn()
        return item
    
    def get_laundry_summary(self) -> Dict:
        """
        Get a complete laundry summary for the user.
        
        Returns dict with counts and lists for dashboard display.
        """
        needs_wash = self.get_items_needing_wash()
        approaching = self.get_items_approaching_wash()
        at_laundry = self.get_items_at_laundry()
        active_alerts = self.get_active_alerts()
        
        # Count urgent alerts (deadline within 24 hours)
        now = timezone.now()
        urgent_count = sum(
            1 for a in active_alerts 
            if a.deadline <= now + timedelta(hours=24)
        )
        
        return {
            'needs_wash_count': len(needs_wash),
            'needs_wash_items': needs_wash,
            'approaching_count': len(approaching),
            'approaching_items': approaching,
            'at_laundry': at_laundry,
            'at_laundry_count': sum(len(v) for v in at_laundry.values()),
            'active_alerts': active_alerts,
            'active_alerts_count': len(active_alerts),
            'urgent_alerts_count': urgent_count,
        }
