# [file name]: services.py
import json
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from collections import Counter

class AIEngagementOptimizer:
    """
    Service for AI-powered post optimization
    """
    
    def __init__(self, user):
        self.user = user
    
    def analyze_best_time(self):
        """
        Analyze user's engagement patterns to suggest best posting time
        """
        # Get user's past post performance
        from .models import LookbookPost, PostLike
        
        user_posts = LookbookPost.objects.filter(user=self.user)
        
        if not user_posts.exists():
            # Default best times based on global patterns
            best_hours = [9, 12, 18, 21]  # 9AM, 12PM, 6PM, 9PM
            best_hour = random.choice(best_hours)
        else:
            # Analyze when user gets most engagement
            post_data = []
            for post in user_posts:
                hour = post.created_at.hour
                engagement = post.likes_count + post.comments_count * 2
                post_data.append((hour, engagement))
            
            # Find hour with highest average engagement
            hour_scores = {}
            for hour in range(24):
                hour_engagements = [eng for h, eng in post_data if h == hour]
                if hour_engagements:
                    hour_scores[hour] = sum(hour_engagements) / len(hour_engagements)
            
            best_hour = max(hour_scores.items(), key=lambda x: x[1])[0] if hour_scores else 18
        
        # Schedule for next suitable time
        now = timezone.now()
        suggested_time = now.replace(hour=best_hour, minute=0, second=0, microsecond=0)
        
        # If time has passed today, schedule for tomorrow
        if suggested_time < now:
            suggested_time += timedelta(days=1)
        
        return suggested_time
    
    def generate_hashtag_suggestions(self, caption="", category=None):
        """
        Generate optimized hashtag suggestions
        """
        base_hashtags = ['#fashion', '#style', '#ootd']
        
        # Category-specific hashtags
        category_hashtags = {
            'casual': ['#casualstyle', '#everydayfashion', '#streetstyle'],
            'formal': ['#formalwear', '#dressedup', '#elegantstyle'],
            'work': ['#workwear', '#officeoutfit', '#professionalstyle'],
            'party': ['#partyoutfit', '#nightout', '#goingoutlook'],
            'vintage': ['#vintagefashion', '#retrostyle', '#throwback'],
        }
        
        # Extract keywords from caption for more relevant hashtags
        caption_keywords = self._extract_keywords(caption)
        keyword_hashtags = [f'#{kw}' for kw in caption_keywords[:3] if len(kw) > 3]
        
        # User's best performing hashtags
        user_top_hashtags = self._get_user_top_hashtags()
        
        # Combine all hashtag sources
        all_suggestions = list(set(
            base_hashtags + 
            category_hashtags.get(category, []) + 
            keyword_hashtags + 
            user_top_hashtags[:5]
        ))
        
        # Limit to 15 hashtags maximum
        return all_suggestions[:15]
    
    def generate_caption_suggestions(self, outfit_name="", style="", mood=""):
        """
        Generate engaging caption suggestions
        """
        templates = [
            f"Loving this {style} look for today! ✨",
            f"{outfit_name} has my heart today 💕",
            f"Feeling {mood} in this {style} outfit!",
            f"New {style} outfit alert! What do you think? 👀",
            f"This {style} look is perfect for today's vibes 🌟",
            f"Outfit details: {outfit_name} - styled with love 💖",
            f"{mood} mood, {style} style! How's your day going?",
            f"Just another day in this beautiful {style} outfit ☀️",
        ]
        
        # Add some personalized suggestions based on user history
        personalized = [
            f"Sharing one of my favorite looks! {outfit_name} never fails 💫",
            f"Back at it with another {style} creation! Hope you like it ✨",
        ]
        
        return random.sample(templates + personalized, min(5, len(templates + personalized)))
    
    def calculate_confidence_score(self, post_data):
        """
        Calculate AI confidence score for optimization suggestions
        """
        score = 0.5  # Base score
        
        # Add points for completeness
        if post_data.get('caption'):
            score += 0.1
        if post_data.get('hashtags'):
            score += 0.1
        if post_data.get('outfit'):
            score += 0.1
        
        # Add points for optimal posting time
        optimal_hours = [9, 12, 18, 21]
        suggested_time = post_data.get('suggested_time')
        if suggested_time and suggested_time.hour in optimal_hours:
            score += 0.2
        
        return min(score, 1.0)
    
    def _extract_keywords(self, text):
        """Extract keywords from text"""
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = text.lower().split()
        return [word for word in words if word not in stop_words and len(word) > 3]
    
    def _get_user_top_hashtags(self):
        """Get user's top performing hashtags"""
        from .models import LookbookPost
        
        user_posts = LookbookPost.objects.filter(user=self.user)
        all_hashtags = []
        
        for post in user_posts:
            all_hashtags.extend(post.hashtags)
        
        # Count and return top hashtags
        counter = Counter(all_hashtags)
        return [hashtag for hashtag, _ in counter.most_common(10)]


class PostScheduler:
    """
    Handle scheduled posts
    """
    
    @staticmethod
    def process_scheduled_posts():
        """Check and publish scheduled posts"""
        from .models import PostDraft
        
        now = timezone.now()
        scheduled_posts = PostDraft.objects.filter(
            status='scheduled',
            scheduled_for__lte=now
        )
        
        published_count = 0
        for draft in scheduled_posts:
            draft.publish()
            published_count += 1
        
        return published_count
    
    @staticmethod
    def get_upcoming_schedules(user):
        """Get user's upcoming scheduled posts"""
        from .models import PostDraft
        
        return PostDraft.objects.filter(
            user=user,
            status='scheduled',
            scheduled_for__gt=timezone.now()
        ).order_by('scheduled_for')