# [file name]: social/ai_photo_enhancer.py
from PIL import Image, ImageEnhance, ImageStat
from .utils.image_processing import ImageProcessor

class AIPhotoEnhancer:
    """
    AI pour améliorer automatiquement les photos de mode
    Version simplifiée sans OpenCV
    """
    
    def __init__(self):
        self.processor = ImageProcessor()
        print("✅ AI Photo Enhancer initialisé")
    
    def enhance_fashion_photo(self, image_path, style='auto'):
        """
        Améliorer une photo de mode automatiquement
        Styles: auto, vibrant, elegant, vintage, bright
        """
        print(f"🎨 Début amélioration AI - Style: {style}")
        
        original_image = self.processor.open_image(image_path)
        if not original_image:
            print("❌ Impossible de charger l'image originale")
            return None
        
        print(f"✅ Image chargée: {original_image.size}")
        
        # Analyser l'image
        analysis = self._analyze_image(original_image)
        print(f"📊 Analyse: luminosité={analysis['brightness']:.2f}, contraste={analysis['contrast']:.2f}")
        
        # Obtenir le profil d'amélioration
        enhancements = self._get_enhancement_profile(style, analysis)
        print(f"⚙️  Améliorations: {enhancements}")
        
        # Appliquer les améliorations
        enhanced_image = self.processor.apply_enhancements(original_image, enhancements)
        
        # Recadrage intelligent
        if enhancements.get('auto_crop', False):
            enhanced_image = self._smart_crop(enhanced_image)
            print("✅ Recadrage intelligent appliqué")
        
        print(f"✅ Image améliorée créée: {enhanced_image.size}")
        return enhanced_image
    
    def _analyze_image(self, image):
        """Analyser l'image sans OpenCV"""
        try:
            # Calculer la luminosité moyenne
            stat = ImageStat.Stat(image)
            brightness = sum(stat.mean) / (255 * 3)  # Moyenne RGB normalisée
            
            # Estimation du contraste (écart-type moyen)
            contrast = sum(stat.stddev) / (255 * 3) if stat.stddev else 0.5
            
            return {
                'brightness': brightness,
                'contrast': contrast,
                'saturation': 0.7,  # Valeur par défaut
                'needs_enhancement': brightness < 0.4 or contrast < 0.3
            }
        except Exception as e:
            print(f"❌ Erreur analyse: {e}")
            return {'brightness': 0.5, 'contrast': 0.5, 'saturation': 0.7, 'needs_enhancement': True}
    
    def _get_enhancement_profile(self, style, analysis):
        """Obtenir le profil d'amélioration"""
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
        
        base_enhancements['saturation'] = 1.2  # Toujours augmenter un peu la saturation
        
        # Styles prédéfinis
        style_profiles = {
            'auto': {
                'brightness': 1.2,
                'contrast': 1.3,
                'saturation': 1.2
            },
            'vibrant': {      # 🎨 Très coloré et contrasté
                'brightness': 1.3,
                'contrast': 1.5,
                'saturation': 1.6
            },
            'elegant': {      # ✨ Raffiné et doux
                'brightness': 1.1,
                'contrast': 1.4,
                'saturation': 1.0
            },
            'vintage': {      # 📻 Sépia et sombre
                'brightness': 0.8,
                'contrast': 1.6,
                'saturation': 0.6
            },
            'bright': {       # ☀️ Très lumineux
                'brightness': 1.6,
                'contrast': 1.3,
                'saturation': 1.2
            }
        }
        
        profile = style_profiles.get(style, style_profiles['auto'])
        profile['auto_crop'] = True
        
        return profile
        
    def _smart_crop(self, image):
        """Recadrage intelligent"""
        width, height = image.size
        
        # Ratio pour les posts (4:5)
        target_ratio = 4/5
        current_ratio = width / height
        
        if abs(current_ratio - target_ratio) > 0.1:
            if current_ratio > target_ratio:
                # Trop large
                new_width = int(height * target_ratio)
                left = (width - new_width) // 2
                return image.crop((left, 0, left + new_width, height))
            else:
                # Trop haut
                new_height = int(width / target_ratio)
                top = (height - new_height) // 2
                return image.crop((0, top, width, top + new_height))
        
        return image