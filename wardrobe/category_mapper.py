"""
Category Mapper - Maps AI-detected item types to database categories
"""
from .models import ClothingCategory


class CategoryMapper:
    """
    Maps AI-detected item types and categories to database ClothingCategory objects
    """
    
    # Mapping from AI category names to database category names (English/French)
    AI_TO_DB_MAPPING = {
        # Tops
        'tops': ['Hauts', 'Tops', 'T-shirts', 'Chemises', 'Pulls'],
        'shirt': ['Chemises', 'Hauts'],
        'top': ['Tops', 'Hauts'],
        't-shirt': ['T-shirts', 'Hauts'],
        'blouse': ['Chemises', 'Tops', 'Hauts'],
        'sweater': ['Pulls', 'Hauts'],
        'sweatshirt': ['Pulls', 'Hauts'],
        
        # Bottoms
        'bottoms': ['Bas', 'Pantalons', 'Jeans'],
        'pants': ['Pantalons', 'Bas'],
        'jeans': ['Jeans', 'Pantalons', 'Bas'],
        'shorts': ['Shorts', 'Bas'],
        'skirt': ['Jupes', 'Bas'],
        
        # Dresses
        'dresses': ['Robes'],
        'dress': ['Robes'],
        
        # Outerwear
        'outerwear': ['Vestes & Manteaux', 'Vestes', 'Manteaux'],
        'jacket': ['Vestes', 'Vestes & Manteaux'],
        'coat': ['Manteaux', 'Vestes & Manteaux'],
        
        # Shoes
        'shoes': ['Chaussures'],
        'sneakers': ['Chaussures'],
        'boots': ['Chaussures'],
        'sandals': ['Chaussures'],
        
        # Accessories
        'accessories': ['Accessoires'],
        'accessory': ['Accessoires'],
        'socks': ['Accessoires', 'Sous-vêtements'],
        'hat': ['Accessoires'],
        'bag': ['Accessoires'],
        'scarf': ['Accessoires'],
    }
    
    # Item type to category suggestions (for more specific matching)
    ITEM_TYPE_TO_CATEGORY = {
        'shirt': 'Chemises',
        'blouse': 'Chemises',
        't-shirt': 'T-shirts',
        'sweater': 'Pulls',
        'cardigan': 'Gilets',
        'pants': 'Pantalons',
        'jeans': 'Jeans',
        'shorts': 'Shorts',
        'skirt': 'Jupes',
        'dress': 'Robes',
        'jacket': 'Vestes',
        'coat': 'Manteaux',
        'shoes': 'Chaussures',
        'sneakers': 'Chaussures',
        'boots': 'Chaussures',
        'socks': 'Accessoires',
        'bag': 'Accessoires',
        'hat': 'Accessoires',
        'scarf': 'Accessoires',
    }
    
    @classmethod
    def get_category_for_ai_detection(cls, ai_category, item_type=None, user=None):
        """
        Get database category object based on AI detection
        
        Args:
            ai_category: Category from AI (e.g., 'tops', 'bottoms')
            item_type: Specific item type from AI (e.g., 'shirt', 'pants')
            user: User object (for custom categories)
        
        Returns:
            ClothingCategory object or None
        """
        # Try item type first (more specific)
        if item_type:
            item_type_lower = item_type.lower().strip()
            if item_type_lower in cls.ITEM_TYPE_TO_CATEGORY:
                category_name = cls.ITEM_TYPE_TO_CATEGORY[item_type_lower]
                category = cls._find_category(category_name, user)
                if category:
                    return category
        
        # Fall back to AI category
        if ai_category:
            ai_category_lower = ai_category.lower().strip()
            if ai_category_lower in cls.AI_TO_DB_MAPPING:
                possible_names = cls.AI_TO_DB_MAPPING[ai_category_lower]
                for name in possible_names:
                    category = cls._find_category(name, user)
                    if category:
                        return category
        
        return None
    
    @classmethod
    def _find_category(cls, name, user=None):
        """
        Find category by name (checks global and user custom categories)
        
        Args:
            name: Category name to search for
            user: User object
        
        Returns:
            ClothingCategory object or None
        """
        # Try exact match first
        try:
            # Try global category first
            return ClothingCategory.objects.get(name=name, is_custom=False, user=None)
        except ClothingCategory.DoesNotExist:
            pass
        
        # Try user custom category
        if user:
            try:
                return ClothingCategory.objects.get(name=name, user=user, is_custom=True)
            except ClothingCategory.DoesNotExist:
                pass
        
        # Try case-insensitive match
        try:
            return ClothingCategory.objects.filter(
                name__iexact=name,
                is_custom=False,
                user=None
            ).first()
        except:
            pass
        
        return None
    
    @classmethod
    def get_suggested_categories(cls, ai_category, item_type=None):
        """
        Get list of suggested category names based on AI detection
        
        Returns:
            List of category names (strings)
        """
        suggestions = []
        
        # Add item type suggestions
        if item_type:
            item_type_lower = item_type.lower().strip()
            if item_type_lower in cls.ITEM_TYPE_TO_CATEGORY:
                suggestions.append(cls.ITEM_TYPE_TO_CATEGORY[item_type_lower])
        
        # Add AI category suggestions
        if ai_category:
            ai_category_lower = ai_category.lower().strip()
            if ai_category_lower in cls.AI_TO_DB_MAPPING:
                for name in cls.AI_TO_DB_MAPPING[ai_category_lower]:
                    if name not in suggestions:
                        suggestions.append(name)
        
        return suggestions
