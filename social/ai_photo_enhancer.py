# [file name]: social/ai_photo_enhancer.py
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from .utils.image_processing import ImageProcessor

class AIPhotoEnhancer:
    """
    AI pour améliorer automatiquement les photos de mode
    """
    
    def __init__(self):
        self.processor = ImageProcessor()
    
    def enhance_fashion_photo(self, image_path, style='auto'):
        """
        Améliorer une photo de mode automatiquement
        Styles: auto, vibrant, elegant, vintage, bright
        """
        original_image = self.processor.open_image(image_path)
        if not original_image:
            return None
        
        # Analyser l'image pour déterminer les améliorations nécessaires
        analysis = self._analyze_image(original_image)
        
        # Appliquer les améliorations basées sur le style et l'analyse
        enhancements = self._get_enhancement_profile(style, analysis)
        enhanced_image = self.processor.apply_enhancements(original_image, enhancements)
        
        # Recadrage intelligent si nécessaire
        if enhancements.get('auto_crop', False):
            enhanced_image = self._smart_crop(enhanced_image)
        
        # Application de filtre de style
        if enhancements.get('filter'):
            enhanced_image = self._apply_style_filter(enhanced_image, enhancements['filter'])
        
        return enhanced_image
    
    def _analyze_image(self, image):
        """Analyser l'image pour déterminer les améliorations nécessaires"""
        # Convertir en array numpy pour l'analyse
        img_array = np.array(image)
        
        # Calculer la luminosité moyenne
        brightness = np.mean(img_array) / 255.0
        
        # Calculer le contraste (écart-type)
        contrast = np.std(img_array) / 255.0
        
        # Détection de dominantes de couleur
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        saturation = np.mean(hsv[:, :, 1]) / 255.0
        
        return {
            'brightness': brightness,
            'contrast': contrast,
            'saturation': saturation,
            'needs_enhancement': brightness < 0.4 or contrast < 0.3 or saturation < 0.3
        }
    
    def _get_enhancement_profile(self, style, analysis):
        """Obtenir le profil d'amélioration basé sur le style et l'analyse"""
        base_enhancements = {}
        
        # Ajustements basés sur l'analyse
        if analysis['brightness'] < 0.4:
            base_enhancements['brightness'] = 1.3
        elif analysis['brightness'] > 0.7:
            base_enhancements['brightness'] = 0.9
        
        if analysis['contrast'] < 0.3:
            base_enhancements['contrast'] = 1.4
        elif analysis['contrast'] > 0.6:
            base_enhancements['contrast'] = 0.9
        
        if analysis['saturation'] < 0.3:
            base_enhancements['saturation'] = 1.3
        
        # Appliquer le style choisi
        style_profiles = {
            'auto': {'sharpness': 1.1},
            'vibrant': {
                'saturation': base_enhancements.get('saturation', 1) * 1.2,
                'contrast': base_enhancements.get('contrast', 1) * 1.1,
                'brightness': base_enhancements.get('brightness', 1) * 1.05
            },
            'elegant': {
                'brightness': base_enhancements.get('brightness', 1) * 0.95,
                'contrast': base_enhancements.get('contrast', 1) * 1.1,
                'saturation': base_enhancements.get('saturation', 1) * 0.9,
                'filter': 'warm'
            },
            'vintage': {
                'brightness': base_enhancements.get('brightness', 1) * 0.9,
                'contrast': base_enhancements.get('contrast', 1) * 1.2,
                'saturation': base_enhancements.get('saturation', 1) * 0.8,
                'filter': 'vintage'
            },
            'bright': {
                'brightness': 1.4,
                'contrast': 1.2,
                'saturation': 1.1,
                'filter': 'cool'
            }
        }
        
        profile = style_profiles.get(style, style_profiles['auto'])
        profile.update(base_enhancements)
        profile['auto_crop'] = True
        
        return profile
    
    def _smart_crop(self, image):
        """Recadrage intelligent pour mettre en valeur l'outfit"""
        width, height = image.size
        
        # Ratio idéal pour les posts Instagram (4:5)
        target_ratio = 4/5
        current_ratio = width / height
        
        if abs(current_ratio - target_ratio) > 0.1:
            # Calculer les nouvelles dimensions
            if current_ratio > target_ratio:
                # Trop large - recadrer les côtés
                new_width = int(height * target_ratio)
                left = (width - new_width) // 2
                return image.crop((left, 0, left + new_width, height))
            else:
                # Trop haut - recadrer le haut/bas
                new_height = int(width / target_ratio)
                top = (height - new_height) // 2
                return image.crop((0, top, width, top + new_height))
        
        return image
    
    def _apply_style_filter(self, image, filter_name):
        """Appliquer un filtre de style"""
        if filter_name == 'warm':
            # Ajouter une teinte chaude
            enhancer = ImageEnhance.Color(image)
            return enhancer.enhance(1.1)
        
        elif filter_name == 'cool':
            # Teinte froide (bleutée)
            array = np.array(image)
            array[:, :, 2] = np.clip(array[:, :, 2] * 0.9, 0, 255)  # Réduire le rouge
            return Image.fromarray(array)
        
        elif filter_name == 'vintage':
            # Effet vintage sépia
            array = np.array(image)
            # Conversion sépia
            r, g, b = array[:, :, 0], array[:, :, 1], array[:, :, 2]
            array[:, :, 0] = np.clip(r * 0.393 + g * 0.769 + b * 0.189, 0, 255)
            array[:, :, 1] = np.clip(r * 0.349 + g * 0.686 + b * 0.168, 0, 255)
            array[:, :, 2] = np.clip(r * 0.272 + g * 0.534 + b * 0.131, 0, 255)
            return Image.fromarray(array)
        
        return image
    
    def compare_images(self, original_path, enhanced_path):
        """Créer une comparaison côte à côte"""
        original = self.processor.open_image(original_path)
        enhanced = self.processor.open_image(enhanced_path)
        
        if not original or not enhanced:
            return None
        
        # Redimensionner à la même taille si nécessaire
        width = max(original.width, enhanced.width)
        height = max(original.height, enhanced.height)
        
        original = original.resize((width, height))
        enhanced = enhanced.resize((width, height))
        
        # Créer l'image de comparaison
        comparison = Image.new('RGB', (width * 2, height))
        comparison.paste(original, (0, 0))
        comparison.paste(enhanced, (width, 0))
        
        return comparison