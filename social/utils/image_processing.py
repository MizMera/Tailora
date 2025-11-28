# [file name]: social/utils/image_processing.py
import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid

class ImageProcessor:
    """Classe de base pour le traitement d'images"""
    
    @staticmethod
    def open_image(image_path):
        """Ouvrir une image depuis le chemin Django"""
        if default_storage.exists(image_path):
            with default_storage.open(image_path, 'rb') as f:
                image = Image.open(f)
                return image.convert('RGB')
        return None
    
    @staticmethod
    def save_image(image, directory='enhanced'):
        """Sauvegarder une image dans le storage Django"""
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(directory, filename)
        
        # Convertir en RGB si nécessaire
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Sauvegarder
        buffer = ContentFile(b"")
        image.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        saved_path = default_storage.save(filepath, buffer)
        return saved_path
    
    @staticmethod
    def apply_enhancements(image, enhancements):
        """Appliquer des améliorations à l'image"""
        enhanced_image = image.copy()
        
        # Luminosité
        if enhancements.get('brightness', 1) != 1:
            enhancer = ImageEnhance.Brightness(enhanced_image)
            enhanced_image = enhancer.enhance(enhancements['brightness'])
        
        # Contraste
        if enhancements.get('contrast', 1) != 1:
            enhancer = ImageEnhance.Contrast(enhanced_image)
            enhanced_image = enhancer.enhance(enhancements['contrast'])
        
        # Saturation
        if enhancements.get('saturation', 1) != 1:
            enhancer = ImageEnhance.Color(enhanced_image)
            enhanced_image = enhancer.enhance(enhancements['saturation'])
        
        # Netteté
        if enhancements.get('sharpness', 1) != 1:
            enhancer = ImageEnhance.Sharpness(enhanced_image)
            enhanced_image = enhancer.enhance(enhancements['sharpness'])
        
        return enhanced_image