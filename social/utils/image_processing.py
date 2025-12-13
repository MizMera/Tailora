# [file name]: social/utils/image_processing.py
import os
from PIL import Image, ImageEnhance
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid

class ImageProcessor:
    """Classe de base pour le traitement d'images"""

    @staticmethod
    def open_image(image_path):
        """Ouvrir une image depuis le chemin Django"""
        try:
            if default_storage.exists(image_path):
                with default_storage.open(image_path, 'rb') as f:
                    image = Image.open(f)
                    return image.convert('RGB')
            return None
        except Exception as e:
            print(f"❌ Erreur ouverture image {image_path}: {e}")
            return None

    @staticmethod
    def save_image(image, directory='enhanced'):
        """Sauvegarder une image dans le storage Django"""
        try:
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
            print(f"✅ Image sauvegardée: {saved_path}")
            return saved_path
        except Exception as e:
            print(f"❌ Erreur sauvegarde image: {e}")
            return None

    @staticmethod
    def apply_enhancements(image, enhancements):
        """Appliquer des améliorations à l'image"""
        try:
            enhanced_image = image.copy()

            # Luminosité
            if enhancements.get('brightness', 1) != 1:
                enhancer = ImageEnhance.Brightness(enhanced_image)
                enhanced_image = enhancer.enhance(enhancements['brightness'])
                print(f"✅ Luminosité: {enhancements['brightness']}")

            # Contraste
            if enhancements.get('contrast', 1) != 1:
                enhancer = ImageEnhance.Contrast(enhanced_image)
                enhanced_image = enhancer.enhance(enhancements['contrast'])
                print(f"✅ Contraste: {enhancements['contrast']}")

            # Saturation
            if enhancements.get('saturation', 1) != 1:
                enhancer = ImageEnhance.Color(enhanced_image)
                enhanced_image = enhancer.enhance(enhancements['saturation'])
                print(f"✅ Saturation: {enhancements['saturation']}")

            return enhanced_image
        except Exception as e:
            print(f"❌ Erreur améliorations: {e}")
            return image
