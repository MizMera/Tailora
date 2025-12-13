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
        BASED ON OPTIMAL POSTING TIME + CONTENT QUALITY
        Returns: Float between 0.0 and 1.0 (0% to 100%)
        """
        score = 0.5  # Base score = 50%

        # 1. POSTING TIME - MOST IMPORTANT FACTOR (max 40%)
        suggested_time = post_data.get('suggested_time')
        if suggested_time:
            hour = suggested_time.hour

            # Different points based on hour (engagement statistics)
            if hour == 18:  # 6 PM = BEST time
                score += 0.40
            elif hour == 9:  # 9 AM = Very good
                score += 0.35
            elif hour == 12:  # 12 PM = Good
                score += 0.30
            elif hour == 21:  # 9 PM = Good
                score += 0.30
            elif 17 <= hour <= 20:  # 5 PM - 8 PM = Decent
                score += 0.25
            elif 8 <= hour <= 11:  # 8 AM - 11 AM = Morning
                score += 0.20
            else:  # Other hours = Less optimal
                score += 0.10
        else:
            # No time selected = immediate posting (less optimal)
            score += 0.05

        # 2. CAPTION QUALITY (max 30%)
        caption = post_data.get('caption', '')
        if caption:
            caption_length = len(caption)

            # Optimal length for engagement: 50-150 characters
            if 50 <= caption_length <= 150:
                score += 0.15
            elif caption_length > 150:
                score += 0.10
            elif caption_length > 20:
                score += 0.08
            else:
                score += 0.05

            # Engagement elements
            if '?' in caption:
                score += 0.05  # Questions increase comments
            if '!' in caption:
                score += 0.03  # Exclamations increase emotional engagement

            # Emojis boost engagement by ~40%
            emojis = ['✨', '🌟', '💫', '💖', '👀', '🔥', '❤️', '😍', '☀️', '🎯', '🍽️', '🌙']
            if any(emoji in caption for emoji in emojis):
                score += 0.05
        else:
            # No caption = penalty
            score -= 0.10

        # 3. HASHTAGS - VISIBILITY (max 15%)
        hashtags = post_data.get('hashtags', [])
        if isinstance(hashtags, str):
            hashtags = [tag.strip() for tag in hashtags.split() if tag.startswith('#')]

        if hashtags:
            hashtag_count = len(hashtags)

            # Optimal number: 5-10 hashtags
            if 5 <= hashtag_count <= 10:
                score += 0.15
            elif 3 <= hashtag_count < 5:
                score += 0.10
            elif hashtag_count > 10:
                score += 0.08  # A bit too many but OK
            elif hashtag_count > 0:
                score += 0.05
        else:
            # No hashtags = small penalty
            score -= 0.05

        # 4. OUTFIT - VISUAL CONTENT (10%)
        if post_data.get('outfit'):
            score += 0.10

        # 5. CATEGORY SPECIFIED (5% bonus)
        if post_data.get('category'):
            score += 0.05

        # 6. STYLE/MOOD SPECIFIED (5% bonus)
        if post_data.get('style') or post_data.get('mood'):
            score += 0.05

        # 7. AI ENABLED (5% bonus)
        if post_data.get('use_ai', True):
            score += 0.05

        # Limit between 0% and 100%
        return max(0.0, min(score, 1.0))

    def get_optimization_summary(self, post_data):
        """
        Get detailed optimization summary with explanations
        """
        score = self.calculate_confidence_score(post_data)

        summary = {
            'confidence_score': score,
            'confidence_percentage': int(score * 100),
            'factors': [],
            'recommendations': []
        }

        # Analyze time factor
        suggested_time = post_data.get('suggested_time')
        if suggested_time:
            hour = suggested_time.hour
            if hour in [18, 9]:
                summary['factors'].append({
                    'type': 'time',
                    'status': 'excellent',
                    'message': f'Perfect posting time ({hour}:00) - Peak engagement hours'
                })
            elif hour in [12, 21]:
                summary['factors'].append({
                    'type': 'time',
                    'status': 'good',
                    'message': f'Good posting time ({hour}:00) - High engagement potential'
                })
            else:
                summary['factors'].append({
                    'type': 'time',
                    'status': 'average',
                    'message': f'Standard posting time ({hour}:00) - Moderate engagement'
                })
        else:
            summary['recommendations'].append('Select a posting time for better engagement')

        # Analyze caption
        caption = post_data.get('caption', '')
        if caption:
            if len(caption) >= 50:
                summary['factors'].append({
                    'type': 'caption',
                    'status': 'good',
                    'message': f'Caption length optimal ({len(caption)} chars)'
                })
            else:
                summary['recommendations'].append('Consider writing a longer caption (50+ chars)')

            if '?' in caption:
                summary['factors'].append({
                    'type': 'engagement',
                    'status': 'good',
                    'message': 'Caption includes engaging question'
                })
        else:
            summary['recommendations'].append('Add a caption to increase engagement')

        # Analyze hashtags
        hashtags = post_data.get('hashtags', [])
        if isinstance(hashtags, str):
            hashtags = [tag.strip() for tag in hashtags.split() if tag.startswith('#')]

        if len(hashtags) >= 5:
            summary['factors'].append({
                'type': 'hashtags',
                'status': 'good',
                'message': f'Good hashtag coverage ({len(hashtags)} hashtags)'
            })
        elif hashtags:
            summary['recommendations'].append(f'Add more hashtags (currently {len(hashtags)})')

        # Determine overall status
        if score >= 0.8:
            summary['status'] = 'excellent'
            summary['message'] = 'High engagement potential! Optimal time and content.'
        elif score >= 0.6:
            summary['status'] = 'good'
            summary['message'] = 'Good engagement potential. Could be improved.'
        else:
            summary['status'] = 'average'
            summary['message'] = 'Moderate engagement potential. Consider optimization.'

        return summary

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
