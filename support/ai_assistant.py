"""
Smart Support Assistant for Tailora
Uses advanced pattern matching, synonyms, and a comprehensive knowledge base.
No external API required - all intelligence is built-in.
"""
import re
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher


class TailoraSupportAssistant:
    """
    AI-like support assistant using intelligent pattern matching and knowledge base.
    Provides helpful, contextual responses about Tailora features.
    """
    
    def __init__(self):
        self.synonyms = self._build_synonyms()
        self.intent_keywords = self._build_intent_keywords()
        self.knowledge_base = self._build_knowledge_base()
        self.conversation_history = []
    
    def get_response(self, user_message: str) -> Dict:
        """
        Get a response for the user's message.
        
        Returns:
            Dict with 'response', 'category', and 'suggestions'
        """
        original_message = user_message
        message_lower = user_message.lower().strip()
        
        # Normalize message with synonyms
        normalized = self._normalize_message(message_lower)
        
        # Store in history
        self.conversation_history.append({'role': 'user', 'content': user_message})
        
        # Check for greetings
        if self._is_greeting(message_lower):
            response = self._get_greeting_response()
            return {
                'response': response,
                'category': 'greeting',
                'suggestions': self._get_popular_topics()
            }
        
        # Check for thanks/goodbye
        if self._is_closing(message_lower):
            return {
                'response': "You're welcome! 😊 Feel free to come back anytime you have questions. Happy styling!",
                'category': 'closing',
                'suggestions': []
            }
        
        # Detect intent for smarter routing
        intent = self._detect_intent(normalized)
        
        # Find best matching answer from knowledge base
        best_match = self._find_best_match(normalized, intent)
        
        if best_match:
            answer, category, confidence = best_match
            suggestions = self._get_related_topics(category)
            
            return {
                'response': answer,
                'category': category,
                'suggestions': suggestions,
                'confidence': confidence
            }
        
        # Partial match - try to be helpful with context clues
        partial = self._try_partial_match(normalized)
        if partial:
            return partial
        
        # Fallback response
        return {
            'response': self._get_fallback_response(original_message),
            'category': 'unknown',
            'suggestions': self._get_popular_topics()
        }
    
    def _build_synonyms(self) -> Dict[str, List[str]]:
        """Build synonym mappings for better understanding."""
        return {
            'clothes': ['clothing', 'items', 'garments', 'pieces', 'apparel', 'wear', 'garment', 'things'],
            'wardrobe': ['closet', 'collection', 'inventory', 'clothes'],
            'outfit': ['look', 'ensemble', 'combination', 'style', 'attire'],
            'create': ['make', 'build', 'add', 'generate', 'new'],
            'delete': ['remove', 'erase', 'get rid of', 'discard', 'trash'],
            'edit': ['change', 'modify', 'update', 'adjust', 'fix'],
            'help': ['assist', 'support', 'guide', 'how to', 'how do i', 'how can i'],
            'show': ['display', 'see', 'view', 'find', 'look at', 'check'],
            'upload': ['add', 'import', 'put', 'send'],
            'photo': ['image', 'picture', 'pic', 'snapshot'],
            'favorite': ['favourite', 'love', 'like', 'star', 'heart'],
            'account': ['profile', 'user', 'settings'],
            'premium': ['pro', 'paid', 'subscription', 'upgrade'],
            'problem': ['issue', 'error', 'bug', 'broken', 'not working', 'doesn\'t work'],
        }
    
    def _build_intent_keywords(self) -> Dict[str, List[str]]:
        """Build intent detection keywords."""
        return {
            'how_to': ['how', 'how to', 'how do i', 'how can i', 'steps', 'guide', 'tutorial'],
            'what_is': ['what is', 'what are', 'what\'s', 'explain', 'tell me about', 'define'],
            'troubleshoot': ['not working', 'doesn\'t work', 'broken', 'error', 'problem', 'issue', 'help', 'can\'t', 'cannot', 'won\'t'],
            'where_is': ['where', 'where is', 'find', 'locate', 'look for'],
            'why': ['why', 'reason', 'because'],
            'action': ['want to', 'need to', 'trying to', 'can i', 'should i'],
        }
    
    def _normalize_message(self, message: str) -> str:
        """Normalize message by expanding with synonyms."""
        words = message.split()
        normalized_words = []
        
        for word in words:
            # Keep the original word
            normalized_words.append(word)
            
            # Add any canonical forms
            for canonical, synonyms in self.synonyms.items():
                if word in synonyms:
                    normalized_words.append(canonical)
        
        return ' '.join(normalized_words)
    
    def _detect_intent(self, message: str) -> str:
        """Detect the user's intent."""
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return intent
        return 'general'
    
    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting."""
        greetings = ['hi', 'hello', 'hey', 'bonjour', 'salut', 'good morning', 
                     'good afternoon', 'good evening', "what's up", 'sup', 'yo',
                     'hola', 'ciao', 'howdy', 'greetings']
        # Must start with or be just the greeting
        for g in greetings:
            if message == g or message.startswith(g + ' ') or message.startswith(g + ','):
                return len(message.split()) <= 6
        return False
    
    def _is_closing(self, message: str) -> bool:
        """Check if message is a closing/thanks."""
        closings = ['thank', 'thanks', 'merci', 'bye', 'goodbye', 'au revoir', 
                    'got it', 'understood', 'perfect', 'great', 'awesome', 
                    'that helps', 'helpful', 'solved', 'works now', 'all good',
                    'thx', 'ty', 'appreciate', 'cheers']
        return any(c in message for c in closings)
    
    def _get_greeting_response(self) -> str:
        return """👋 **Hello! I'm Tailora's Support Assistant.**

I'm here to help you with:
• 👕 **Wardrobe** - Adding, organizing, and managing your clothes
• 👔 **Outfits** - Creating and styling outfit combinations
• 🎯 **Challenges** - Joining and completing fashion challenges
• 🤖 **AI Features** - Style Coach, recommendations, and more
• 📊 **Statistics** - Understanding your wardrobe data
• 👤 **Account** - Profile, settings, and premium features
• 🔧 **Troubleshooting** - Fixing common issues

**What can I help you with today?** 

Just type your question or click one of the suggestions below!"""
    
    def _get_fallback_response(self, original_message: str) -> str:
        # Try to give a helpful fallback based on detected words
        if any(word in original_message.lower() for word in ['outfit', 'look', 'wear']):
            hint = "It sounds like you're asking about outfits. Try: **How do I create an outfit?**"
        elif any(word in original_message.lower() for word in ['clothes', 'wardrobe', 'item']):
            hint = "It sounds like you're asking about your wardrobe. Try: **How do I add clothes?**"
        elif any(word in original_message.lower() for word in ['error', 'problem', 'broken', 'not']):
            hint = "It sounds like you're having an issue. Try: **Image upload not working** or tell me more specifically what's wrong."
        else:
            hint = "Could you rephrase your question or try one of these topics?"
        
        return f"""I'm not quite sure I understand that question. 🤔

{hint}

**Popular topics:**
• "How do I add clothes to my wardrobe?"
• "How do I create an outfit?"
• "What are style challenges?"
• "What's the difference between free and premium?"
• "My upload isn't working"

You can also type **"contact support"** to reach a human."""
    
    def _get_popular_topics(self) -> List[str]:
        return [
            "How do I add clothes?",
            "How do I create an outfit?",
            "What is Premium?",
            "How do challenges work?",
            "AI Style Coach"
        ]
    
    def _get_related_topics(self, category: str) -> List[str]:
        """Get related topics for follow-up suggestions."""
        related = {
            'wardrobe': [
                "How do I edit clothing items?",
                "How do I mark favorites?",
                "What's my wardrobe limit?"
            ],
            'outfits': [
                "AI Style Coach feedback",
                "Can I duplicate outfits?",
                "Advanced outfit search"
            ],
            'challenges': [
                "How do I submit an outfit?",
                "What are badges?",
                "Create my own challenge"
            ],
            'account': [
                "Change my password",
                "Premium benefits",
                "Delete my account"
            ],
            'troubleshooting': [
                "Image upload issues",
                "Page not loading",
                "Contact human support"
            ],
            'features': [
                "AI recommendations",
                "Wardrobe statistics",
                "Weather-based suggestions"
            ],
            'social': [
                "Share my outfits",
                "Follow other users",
                "Lookbook posts"
            ],
            'planner': [
                "Plan outfits ahead",
                "Link to calendar events",
                "Set reminders"
            ]
        }
        return related.get(category, self._get_popular_topics())
    
    def _try_partial_match(self, message: str) -> Optional[Dict]:
        """Try to find a partial match and offer guidance."""
        # Check for category mentions
        category_hints = {
            'wardrobe': ['wardrobe', 'clothes', 'clothing', 'item', 'garment'],
            'outfits': ['outfit', 'look', 'combination', 'style', 'wear'],
            'challenges': ['challenge', 'badge', 'compete', 'daily', 'weekly'],
            'account': ['account', 'profile', 'password', 'email', 'setting'],
            'social': ['social', 'share', 'follow', 'post', 'lookbook', 'feed'],
            'planner': ['calendar', 'event', 'plan', 'schedule', 'reminder'],
        }
        
        for category, hints in category_hints.items():
            if any(hint in message for hint in hints):
                return {
                    'response': f"""I see you're asking about **{category}**. 

Here are some common questions I can help with:

{chr(10).join('• ' + topic for topic in self._get_related_topics(category))}

Click one of these or tell me more specifically what you need!""",
                    'category': category,
                    'suggestions': self._get_related_topics(category),
                    'confidence': 0.5
                }
        return None
    
    def _find_best_match(self, message: str, intent: str) -> Optional[Tuple[str, str, float]]:
        """Find the best matching answer from knowledge base."""
        best_score = 0
        best_answer = None
        best_category = None
        
        for category, qa_pairs in self.knowledge_base.items():
            for question_patterns, answer in qa_pairs:
                score = self._calculate_match_score(message, question_patterns, intent)
                if score > best_score:
                    best_score = score
                    best_answer = answer
                    best_category = category
        
        # Return if confidence is high enough
        if best_score >= 0.35:  # Lowered threshold for better matching
            return (best_answer, best_category, best_score)
        return None
    
    def _calculate_match_score(self, message: str, patterns: List[str], intent: str) -> float:
        """Calculate how well a message matches the patterns."""
        max_score = 0
        
        for pattern in patterns:
            pattern_lower = pattern.lower()
            
            # Exact phrase match - highest score
            if pattern_lower in message:
                return 1.0
            
            # Check if message contains pattern
            if message in pattern_lower:
                return 0.95
            
            # Keyword matching
            pattern_words = set(pattern_lower.split())
            message_words = set(message.split())
            
            # Remove common stop words for better matching
            stop_words = {'a', 'an', 'the', 'is', 'are', 'do', 'does', 'to', 'i', 'my', 'me', 'can'}
            pattern_words = pattern_words - stop_words
            message_words = message_words - stop_words
            
            # Word overlap score
            common = pattern_words.intersection(message_words)
            if pattern_words:
                word_score = len(common) / len(pattern_words)
            else:
                word_score = 0
            
            # Boost for matching important keywords
            important_keywords = ['add', 'create', 'delete', 'edit', 'upload', 'change', 
                                'outfit', 'clothes', 'wardrobe', 'challenge', 'premium',
                                'password', 'account', 'help', 'error', 'not working']
            keyword_bonus = sum(0.1 for kw in important_keywords if kw in pattern_lower and kw in message)
            
            # Sequence similarity (fuzzy matching)
            seq_score = SequenceMatcher(None, pattern_lower, message).ratio()
            
            # N-gram matching for partial phrases
            ngram_score = self._ngram_similarity(pattern_lower, message, n=2)
            
            # Combined score with weights
            score = (word_score * 0.4) + (seq_score * 0.25) + (ngram_score * 0.25) + keyword_bonus
            
            # Intent bonus - boost if intent matches expected pattern
            if intent == 'how_to' and ('how' in pattern_lower or 'add' in pattern_lower or 'create' in pattern_lower):
                score += 0.1
            elif intent == 'troubleshoot' and any(w in pattern_lower for w in ['error', 'not', 'issue', 'problem']):
                score += 0.1
            
            max_score = max(max_score, score)
        
        return min(1.0, max_score)  # Cap at 1.0
    
    def _ngram_similarity(self, s1: str, s2: str, n: int = 2) -> float:
        """Calculate n-gram similarity between two strings."""
        def get_ngrams(s: str, n: int) -> set:
            s = s.replace(' ', '_')
            return set(s[i:i+n] for i in range(len(s) - n + 1))
        
        if len(s1) < n or len(s2) < n:
            return 0.0
        
        ngrams1 = get_ngrams(s1, n)
        ngrams2 = get_ngrams(s2, n)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0
    
    def _build_knowledge_base(self) -> Dict[str, List[Tuple[List[str], str]]]:
        """Build the comprehensive knowledge base."""
        return {
            'wardrobe': [
                (
                    ['add clothes', 'add items', 'upload clothes', 'add to wardrobe', 
                     'how to add', 'upload items', 'new clothes', 'add clothing',
                     'put clothes', 'import clothes', 'add garments', 'add more items'],
                    """📸 **Adding Clothes to Your Wardrobe**

1. Go to **My Wardrobe** from the navigation menu
2. Click the **"+ Add Item"** button
3. Upload a photo of your clothing item
4. Our AI will automatically detect:
   • Color and pattern
   • Category (shirt, pants, etc.)
   • Style attributes
5. Review and edit the details if needed
6. Click **Save** to add it to your wardrobe!

💡 **Pro Tips:**
• Use a plain background for best AI detection
• Good lighting helps identify colors accurately
• You can take photos or upload existing images"""
                ),
                (
                    ['edit clothes', 'change item', 'update clothing', 'modify item',
                     'edit wardrobe item', 'change details', 'fix item', 'wrong info',
                     'correct color', 'change category'],
                    """✏️ **Editing Clothing Items**

1. Go to **My Wardrobe**
2. Click on the item you want to edit
3. Click the **Edit** button (pencil icon)
4. Update any details:
   • Name, color, category
   • Season suitability
   • Purchase info (price, brand, date)
   • Status (available, washing, loaned)
5. Click **Save** to confirm changes

💡 Editing items also updates them in any outfits they're part of!"""
                ),
                (
                    ['delete clothes', 'remove item', 'delete from wardrobe', 'get rid of',
                     'discard item', 'trash clothes'],
                    """🗑️ **Removing Clothing Items**

1. Go to **My Wardrobe**
2. Click on the item you want to remove
3. Click the **Delete** button (trash icon)
4. Confirm the deletion

⚠️ **Important Notes:**
• This action cannot be undone
• The item will be removed from any outfits it's part of
• Your outfit count won't change, but those outfits may be incomplete"""
                ),
                (
                    ['favorite', 'mark favorite', 'add to favorites', 'favourite',
                     'love item', 'star item', 'heart item', 'like clothes'],
                    """❤️ **Marking Favorites**

To mark an item as a favorite:
1. Go to **My Wardrobe**
2. Find the item you love
3. Click the **heart icon** on the item card

**Filtering favorites:**
• Use the sidebar filter → "Favorites Only"
• Or click the ❤️ filter button

Favorites appear first in outfit creation for easy access!"""
                ),
                (
                    ['wardrobe limit', 'how many items', 'maximum items', 'storage limit',
                     'item limit', 'can\'t add more', 'full wardrobe', 'limit reached'],
                    """📦 **Wardrobe Limits**

• **Free Account:** Up to 50 items
• **Premium Account:** Up to 500 items

**Check your usage:**
• Look at the header in My Wardrobe
• Or visit **Wardrobe Stats** for details

**Reached your limit?**
• Delete items you no longer own
• Or upgrade to Premium for 10x more space! 🌟"""
                ),
                (
                    ['categories', 'organize', 'sort clothes', 'filter wardrobe',
                     'find clothes', 'search wardrobe', 'organize wardrobe'],
                    """🏷️ **Organizing Your Wardrobe**

**Sidebar Filters:**
• **Category** - Tops, Bottoms, Dresses, Shoes, Accessories
• **Season** - Spring, Summer, Fall, Winter
• **Color** - Filter by specific colors
• **Status** - Available, Washing, Loaned, Donated

**Search Bar:**
• Find items by name, brand, or color
• Type keywords like "blue shirt" or "Nike"

**View Options:**
• Grid view for visual browsing
• List view for more details"""
                ),
                (
                    ['wardrobe stats', 'statistics', 'insights', 'wardrobe analytics',
                     'most worn', 'least worn', 'wardrobe data'],
                    """📊 **Wardrobe Statistics**

Access **View Stats** from My Wardrobe to see:

**Item Breakdown:**
• Total items count
• Items by category (pie chart)
• Items by color distribution
• Items by season

**Wear Insights:**
• Most worn items
• Least worn (maybe donate?)
• Items never worn
• Average cost per wear

Great for closet cleanouts and shopping decisions!"""
                ),
            ],
            'outfits': [
                (
                    ['create outfit', 'make outfit', 'new outfit', 'build outfit',
                     'how to create outfit', 'combine clothes', 'put together outfit',
                     'make new look', 'style outfit', 'create look'],
                    """👔 **Creating an Outfit**

1. Go to **My Outfits** from the navigation
2. Click **"+ Create Outfit"**
3. Select items from your wardrobe:
   • Choose at least 2 items
   • Mix tops, bottoms, shoes, accessories
4. Give your outfit a name
5. Select the occasion:
   • Casual, Work, Formal, Sport, Evening, etc.
6. Click **Create**!

✨ **Bonus:** Our AI Style Coach will instantly analyze your outfit and give feedback on color harmony, style coherence, and tips for improvement!"""
                ),
                (
                    ['edit outfit', 'change outfit', 'modify outfit', 'update outfit',
                     'add item to outfit', 'remove item from outfit', 'swap items'],
                    """✏️ **Editing an Outfit**

1. Go to **My Outfits**
2. Click on the outfit you want to edit
3. Click the **Edit** button
4. Make your changes:
   • Add or remove items
   • Change the outfit name
   • Update the occasion
   • Edit the description
5. Click **Save**

🎨 The AI Style Coach will re-analyze your updated outfit and give new feedback!"""
                ),
                (
                    ['delete outfit', 'remove outfit', 'trash outfit', 'get rid of outfit'],
                    """🗑️ **Deleting an Outfit**

1. Go to **My Outfits**
2. Click on the outfit
3. Click the **Delete** button
4. Confirm deletion

⚠️ **Note:** This removes the outfit combination only. Your clothing items stay safely in your wardrobe."""
                ),
                (
                    ['outfit suggestions', 'ai recommendations', 'what should i wear',
                     'recommend outfit', 'daily recommendation', 'suggest outfit',
                     'what to wear', 'outfit ideas', 'style suggestions'],
                    """🤖 **AI Outfit Recommendations**

Get personalized outfit suggestions!

1. Go to **AI Recommendations** (Daily page)
2. View suggestions based on:
   • Today's weather in your location
   • Your style preferences
   • Items you haven't worn recently
   • Special occasions/events
3. **Like** outfits to save them
4. **Confirm** to add to your collection
5. **Dismiss** to see alternatives

💎 Premium users get smarter, more personalized recommendations!"""
                ),
                (
                    ['style coach', 'ai feedback', 'outfit feedback', 'outfit score',
                     'color harmony', 'pattern matching', 'style analysis',
                     'fashion score', 'xp', 'fashion iq'],
                    """🎨 **AI Style Coach**

Every outfit gets analyzed by our AI Style Coach!

**What it checks:**
• **Color Harmony** - Do the colors complement each other?
• **Pattern Mixing** - Are patterns balanced and not clashing?
• **Style Coherence** - Does the outfit make sense together?
• **Occasion Match** - Is it appropriate for the selected occasion?

**Earn Fashion XP:**
• Great outfits = More XP points
• Level up your Fashion IQ
• Unlock style badges

Look for the Style Coach popup after creating outfits!"""
                ),
                (
                    ['duplicate outfit', 'copy outfit', 'clone outfit', 'same outfit again'],
                    """📋 **Duplicating an Outfit**

1. Go to **My Outfits**
2. Click on the outfit you want to copy
3. Click the **...** menu or **Duplicate** button
4. A new outfit is created with "(Copy)" in the name
5. Edit the copy to make variations!

Great for creating seasonal variations or slight modifications of your favorite looks."""
                ),
                (
                    ['advanced search', 'find outfits', 'search outfits', 'filter outfits',
                     'outfit search', 'find specific outfit'],
                    """🔍 **Advanced Outfit Search**

Find exactly what you're looking for!

1. Go to **My Outfits**
2. Click **"Advanced Search"**
3. Filter by:
   • **Must contain** - Specific items
   • **Must NOT contain** - Exclude items
   • **Colors** - Color palette
   • **Categories** - Item types
   • **Last worn** - Today, this week, month, never
   • **Wear count** - Most worn, least worn
   • **Occasion** - Casual, formal, etc.
   • **Favorites** - Only favorites

Perfect for finding forgotten gems! 💎"""
                ),
            ],
            'challenges': [
                (
                    ['challenge', 'style challenge', 'fashion challenge', 'how do challenges work',
                     'join challenge', 'participate challenge', 'what is challenge',
                     'challenge rules', 'challenge types'],
                    """🎯 **Style Challenges**

Challenges are fun ways to push your style creativity!

**How they work:**
1. Go to **My Outfits → Challenges**
2. Browse available challenges
3. Click **"Join Challenge"**
4. Submit outfits that match the theme
5. Earn badges and XP!

**Challenge Types:**
• 🌅 **Daily** - Quick one-day challenges
• 📅 **Weekly** - Week-long themed challenges  
• 🎨 **Color Theme** - Use specific colors
• 👔 **Item Focus** - Feature a specific item type
• ♻️ **Sustainability** - Rewear and remix outfits
• 💼 **Capsule Wardrobe** - Limited item challenges"""
                ),
                (
                    ['submit outfit challenge', 'complete challenge', 'challenge submission',
                     'how to submit', 'send outfit to challenge'],
                    """📤 **Submitting to a Challenge**

1. **Join** the challenge first
2. Create an outfit that matches the theme
3. Go to the challenge detail page
4. Click **"Submit Outfit"**
5. Select an existing outfit OR create a new one
6. Add optional notes explaining your choices
7. Click **Submit**!

**Tips:**
• Read the challenge rules carefully
• Be creative within the theme
• Check your progress on the challenge page"""
                ),
                (
                    ['badges', 'earn badges', 'rewards', 'achievements', 'what are badges',
                     'how to get badges', 'badge types'],
                    """🏆 **Badges & Achievements**

Earn badges by styling well and staying active!

**How to earn:**
• ✅ **Challenge Complete** - Finish challenges
• 🔥 **Streak Master** - Consecutive daily outfits
• 🌈 **Style Explorer** - Try different styles
• ♻️ **Eco Warrior** - Sustainability challenges
• ⭐ **Community Star** - Social engagement

**Where to view:**
Go to **My Outfits → Badges**

Each badge gives you bonus XP and profile flair!"""
                ),
                (
                    ['create challenge', 'make challenge', 'my own challenge',
                     'start challenge', 'host challenge'],
                    """🎨 **Creating Your Own Challenge**

1. Go to **My Outfits → Challenges**
2. Click **"Create Challenge"**
3. Fill in the details:
   • Challenge name
   • Theme/description
   • Duration (daily, weekly, or custom)
   • Rules and requirements
4. Set visibility (public or private)
5. Launch it!

Others can join your public challenges and compete!"""
                ),
            ],
            'account': [
                (
                    ['premium', 'upgrade', 'subscription', 'paid plan', 'pro account',
                     'free vs premium', 'premium benefits', 'what is premium',
                     'premium features', 'upgrade account', 'go premium'],
                    """🌟 **Premium Membership**

**Free Account includes:**
• 50 wardrobe items
• Basic outfit creation
• Join public challenges
• Standard AI features

**Premium unlocks:**
• ✨ 500 wardrobe items (10x more!)
• 🤖 Advanced AI recommendations
• 📧 Priority support
• 🎯 Exclusive challenges
• 📊 Detailed analytics & insights
• 🚫 Ad-free experience
• 🏆 Premium badges

**How to upgrade:**
Go to **Settings → Upgrade Account** or click your profile!"""
                ),
                (
                    ['change password', 'reset password', 'forgot password', 'update password',
                     'new password', 'password not working'],
                    """🔐 **Changing Your Password**

**If you're logged in:**
1. Go to **Settings**
2. Click **"Change Password"**
3. Enter your current password
4. Enter your new password (twice)
5. Click **Save**

**If you forgot your password:**
1. Go to the login page
2. Click **"Forgot Password?"**
3. Enter your email
4. Check your inbox for reset link
5. Create a new password

🔒 Use a strong password with letters, numbers, and symbols!"""
                ),
                (
                    ['delete account', 'remove account', 'close account', 'deactivate',
                     'erase data', 'delete my data', 'gdpr'],
                    """⚠️ **Deleting Your Account**

1. Go to **Settings**
2. Scroll to **"Delete Account"**
3. Read the warning carefully
4. Enter your password to confirm
5. Click **Delete**

**What gets deleted:**
• All wardrobe items and photos
• All outfits and combinations
• Challenge history and badges
• Profile and preferences

⛔ **This action is permanent and cannot be undone!**"""
                ),
                (
                    ['profile', 'edit profile', 'update profile', 'change name',
                     'profile picture', 'my name', 'personal info'],
                    """👤 **Editing Your Profile**

1. Go to **Settings** (or click User in navbar)
2. Click **"Profile"** tab
3. Update your info:
   • First and last name
   • Profile photo
   • Location (for weather recommendations)
   • Style preferences
   • Bio/description
4. Click **Save**

Your profile shows up in social features and challenges!"""
                ),
                (
                    ['notification', 'emails', 'alerts', 'stop emails', 'email preferences',
                     'notifications settings'],
                    """🔔 **Notification Settings**

Control what notifications you receive:

1. Go to **Settings → Notifications**
2. Toggle preferences:
   • Email notifications
   • Challenge updates
   • Outfit reminders
   • Weekly digests
   • Marketing emails

You can unsubscribe from individual email types anytime!"""
                ),
            ],
            'troubleshooting': [
                (
                    ['image upload', 'photo not uploading', 'upload error', 'image error',
                     'upload not working', "can't upload", 'picture won\'t upload',
                     'image fails', 'upload stuck'],
                    """📸 **Image Upload Issues**

**Common fixes:**

1. **File size** - Images must be under 5MB
2. **Format** - Use JPG, PNG, or WEBP
3. **Browser** - Try clearing cache (Ctrl+Shift+Delete)
4. **Connection** - Check your internet
5. **Try another browser** - Chrome, Firefox, Edge

**Still not working?**
• Resize the image (under 2000px width)
• Take a fresh photo
• Try from a different device
• Clear app data and retry

📧 Persistent issues? Email support@tailora.com"""
                ),
                (
                    ['page not loading', 'slow loading', 'error page', 'site down',
                     'not working', 'broken', 'won\'t load', 'blank page',
                     'spinning', 'loading forever'],
                    """🔧 **Page Loading Issues**

**Quick fixes:**
1. **Refresh** - Press F5 or Ctrl+R
2. **Hard refresh** - Ctrl+Shift+R
3. **Clear cache** - Settings → Clear browsing data
4. **Check internet** - Can you load other sites?
5. **Incognito mode** - Test in private browsing
6. **Different browser** - Chrome, Firefox, Edge, Safari

**On mobile?**
• Force close the browser
• Check for app updates
• Toggle WiFi/cellular data

**Server down?**
If the issue persists, we're probably already fixing it. Try again in 10-15 minutes."""
                ),
                (
                    ['contact support', 'email support', 'get help', 'human help',
                     'talk to someone', 'real person', 'customer service',
                     'speak to human', 'live support'],
                    """📧 **Contact Human Support**

If you need more help:

**Email:** support@tailora.com
**Response time:** Usually within 24-48 hours

**What to include:**
• Your account email
• Device and browser info
• Clear description of the issue
• Screenshots if applicable
• Steps to reproduce

**For urgent issues:**
Include "[URGENT]" in your email subject.

We're here to help! 💪"""
                ),
                (
                    ['login problem', 'can\'t login', 'login error', 'wrong password',
                     'account locked', 'access denied'],
                    """🔑 **Login Issues**

**Can't remember password?**
1. Click "Forgot Password" on login page
2. Check your email for reset link
3. Create a new password

**Email not found?**
• Check for typos
• Try alternative emails you might have used
• Contact support if still stuck

**Account locked?**
Multiple failed attempts trigger temporary locks. Wait 15-30 minutes and try again.

**Still can't get in?**
Email support@tailora.com with your account email."""
                ),
            ],
            'features': [
                (
                    ['what is tailora', 'about tailora', 'how does tailora work',
                     'what can tailora do', 'tell me about tailora', 'tailora features'],
                    """👗 **What is Tailora?**

Tailora is your **AI-powered digital wardrobe assistant**!

**Core Features:**
• 📸 **Digital Wardrobe** - Catalog all your clothes with AI
• 👔 **Outfit Creator** - Mix and match to create looks
• 🤖 **AI Style Coach** - Get instant outfit feedback
• 🎯 **Style Challenges** - Fun fashion games & competitions
• 📊 **Wardrobe Analytics** - Understand your style habits
• 🌤️ **Weather Recommendations** - Dress for the day
• 📱 **Outfit Planner** - Plan looks for upcoming events
• 🌐 **Social Features** - Share and get inspired

**Getting started:**
1. Add your clothes to the wardrobe
2. Create outfit combinations
3. Get AI feedback and earn XP!"""
                ),
                (
                    ['weather', 'weather recommendations', 'weather based', 'dress for weather',
                     'temperature', 'rain', 'sunny', 'cold weather'],
                    """🌤️ **Weather-Based Recommendations**

Tailora considers weather when suggesting outfits!

**How it works:**
• Set your location in **Settings → Profile**
• Get recommendations based on:
  - Current temperature
  - Rain/snow forecast
  - UV index
  - Humidity levels

**Smart suggestions:**
• ☀️ Hot: Light fabrics, short sleeves
• 🌧️ Rain: Waterproof layers
• ❄️ Cold: Layering combinations
• 🌡️ Variable: Versatile pieces

Check the **Daily** page for weather-smart outfit ideas!"""
                ),
                (
                    ['social', 'share outfit', 'lookbook', 'post outfit',
                     'follow users', 'community', 'feed', 'social features'],
                    """🌐 **Social Features**

Connect with the Tailora community!

**Share Your Style:**
• Post outfits to your lookbook
• Add captions and hashtags
• Get likes and comments

**Discover & Follow:**
• Browse the community feed
• Follow stylish users
• Get inspired by others' looks

**Engagement:**
• Like and comment on posts
• Save looks for inspiration
• Build your follower community

Access via **Social Features** in the navigation!"""
                ),
                (
                    ['planner', 'calendar', 'plan outfits', 'schedule',
                     'upcoming event', 'outfit for event', 'plan ahead'],
                    """📅 **Outfit Planner**

Plan your wardrobe ahead of time!

**Features:**
• View calendar with outfit assignments
• Link outfits to events
• Plan for trips or special occasions
• Get reminders for upcoming events

**How to use:**
1. Go to **Calendar & Events**
2. Click on a date to add an event
3. Assign an outfit to the event
4. Get notified when the day comes

Never stress about what to wear again!"""
                ),
            ],
            'social': [
                (
                    ['share outfit', 'post outfit', 'lookbook post', 'share my look',
                     'publish outfit', 'show my style'],
                    """📤 **Sharing Outfits**

Share your looks with the community!

1. Go to **Social Features**
2. Click **"Create Post"**
3. Select an outfit from your collection
4. Add a caption and hashtags
5. Choose visibility (public/friends)
6. Post it!

**Tips for engagement:**
• Use popular hashtags
• Post during active hours
• Respond to comments
• Follow others and engage

Your best looks deserve to be seen! ✨"""
                ),
                (
                    ['follow', 'followers', 'following', 'unfollow',
                     'find users', 'discover people'],
                    """👥 **Following & Followers**

Build your style community!

**To follow someone:**
1. Visit their profile
2. Click the **Follow** button
3. Their posts appear in your feed

**Your followers:**
• See your follower count in your profile
• Followers see your posts in their feed
• Get notifications when you gain followers

**Discover users:**
• Browse the explore/discover section
• See popular stylists
• Find users with similar style"""
                ),
            ],
        }


# Singleton instance
_assistant_instance = None

def get_support_assistant() -> TailoraSupportAssistant:
    """Get or create the support assistant instance."""
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = TailoraSupportAssistant()
    return _assistant_instance
