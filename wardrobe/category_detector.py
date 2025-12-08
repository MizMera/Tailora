"""
AI Category Detector - Maps AI detection results to simplified categories
"""
from wardrobe.models import ClothingCategory


class CategoryDetector:
    """Auto-detect category from AI image analysis"""
    
    # AI detection keywords mapped to our simplified categories
    CATEGORY_MAP = {
        'Top': ['shirt', 'blouse', 't-shirt', 'top', 'sweater', 'hoodie', 'polo', 'tank'],
        'Bottom': ['pants', 'jeans', 'skirt', 'shorts', 'trousers', 'leggings'],
        'Dress': ['dress', 'gown', 'robe', 'sundress'],
        'Jacket': ['jacket', 'coat', 'blazer', 'cardigan', 'outerwear'],
        'Shoe': ['shoe', 'sneaker', 'boot', 'sandal', 'heel', 'footwear'],
        'Bag': ['bag', 'purse', 'backpack', 'handbag', 'tote'],
        'Hat': ['hat', 'cap', 'beanie', 'headwear'],
        'Scarf': ['scarf', 'shawl'],
        'Belt': ['belt'],
        'Sport': ['sport', 'athletic', 'gym', 'yoga', 'fitness'],
    }
    
    @classmethod
    def detect_category(cls, ai_result_text, user=None):
        """
        Detect category from AI analysis result
        
        Args:
            ai_result_text: String from AI (e.g., "blue shirt", "denim jeans")
            user: Optional user to get custom categories
            
        Returns:
            ClothingCategory object or None
        """
        if not ai_result_text:
            return None
        
        text_lower = ai_result_text.lower()
        
        # Check each category's keywords
        for category_name, keywords in cls.CATEGORY_MAP.items():
            if any(keyword in text_lower for keyword in keywords):
                # Get or create the category
                category = ClothingCategory.objects.filter(
                    name=category_name,
                    is_custom=False
                ).first()
                
                if category:
                    return category
        
        return None
    
    @classmethod
    def get_suggested_category_name(cls, ai_result_text):
        """
        Get suggested category name without database query
        
        Returns:
            String category name or None
        """
        if not ai_result_text:
            return None
        
        text_lower = ai_result_text.lower()
        
        for category_name, keywords in cls.CATEGORY_MAP.items():
            if any(keyword in text_lower for keyword in keywords):
                return category_name
        
        return None
