"""
Open Source AI-powered image analysis service for wardrobe items
Rewritten to use an external OpenVisionAPI-style REST endpoint for clothing detection/classification
instead of local Hugging Face transformers. Retains color + pattern analysis locally.
Configure via environment variables or Django settings:
    OPEN_VISION_API_URL, OPEN_VISION_API_TASK (detect|classify), OPEN_VISION_API_KEY (optional), OPEN_VISION_API_TIMEOUT.
"""
import os
import json
import base64
from typing import Dict, List, Optional, Tuple
from collections import Counter
from PIL import Image, ImageStat
import numpy as np
import io
import requests
from django.conf import settings


class OpenSourceClothingImageAnalyzer:
    """Analyzer that delegates clothing recognition to a REST API (OpenVisionAPI compatible)."""

    def __init__(self):
        # Remote API configuration
        self.api_base_url = getattr(settings, 'OPEN_VISION_API_URL', os.environ.get('OPEN_VISION_API_URL', '')).rstrip('/')
        self.api_task = getattr(settings, 'OPEN_VISION_API_TASK', os.environ.get('OPEN_VISION_API_TASK', 'detect'))
        self.api_timeout = int(getattr(settings, 'OPEN_VISION_API_TIMEOUT', os.environ.get('OPEN_VISION_API_TIMEOUT', '15')))
        self.api_key = getattr(settings, 'OPEN_VISION_API_KEY', os.environ.get('OPEN_VISION_API_KEY', None))
        if not self.api_base_url:
            print("[AI] OPEN_VISION_API_URL not set. Analyzer will return fallback results.")

        # Color name mappings
        self._initialize_color_mappings()

    def _initialize_models(self):  # Backward compatibility (unused now)
        pass

    def _initialize_color_mappings(self):
        """Initialize color name mappings"""
        self.color_names = {
            # Basic colors
            (255, 255, 255): "white",
            (0, 0, 0): "black",
            (128, 128, 128): "gray",
            (255, 0, 0): "red",
            (0, 255, 0): "green",
            (0, 0, 255): "blue",
            (255, 255, 0): "yellow",
            (255, 0, 255): "magenta",
            (0, 255, 255): "cyan",

            # Extended colors
            (255, 165, 0): "orange",
            (128, 0, 128): "purple",
            (165, 42, 42): "brown",
            (255, 192, 203): "pink",
            (255, 215, 0): "gold",
            (192, 192, 192): "silver",
            (139, 69, 19): "saddle brown",
            (0, 128, 0): "dark green",
            (0, 0, 128): "navy blue",
            (0, 128, 128): "teal",
            (128, 128, 0): "olive",
        }

    def analyze_image(self, image_file) -> Dict:
        """
        Analyze a clothing image and extract metadata using open source AI

        Args:
            image_file: Django FileField or uploaded file

        Returns:
            Dict containing analysis results
        """
        try:
            # Open and process image
            image = self._load_image(image_file)
            # Auto-crop to foreground to reduce background bias
            image_cropped = self._auto_crop_foreground(image)

            # Extract basic image features
            basic_features = self._extract_basic_features(image_cropped)

            # AI-powered classification via remote API
            ai_analysis = self._infer_with_api(image_cropped)

            # Color analysis
            color_analysis = self._analyze_colors(image_cropped)

            # Combine results
            analysis = self._combine_analyses(basic_features, ai_analysis, color_analysis)

            return analysis

        except Exception as e:
            print(f"Error analyzing image: {str(e)}")
            return self._get_fallback_analysis()

    def _auto_crop_foreground(self, image: Image.Image) -> Image.Image:
        """Simple foreground crop by removing near-white borders/background.
        Works well for product photos on white backgrounds without OpenCV.
        """
        try:
            arr = np.asarray(image.convert('RGB'))
            h, w, _ = arr.shape

            # Mask non-background: keep pixels that are not very bright (near-white)
            # and not very close to white grey.
            thresh = 235
            mask = ~((arr[:, :, 0] > thresh) & (arr[:, :, 1] > thresh) & (arr[:, :, 2] > thresh))

            # If mask too sparse, lower threshold once
            if mask.sum() < 0.02 * (h * w):
                thresh = 245
                mask = ~((arr[:, :, 0] > thresh) & (arr[:, :, 1] > thresh) & (arr[:, :, 2] > thresh))

            # If still sparse, return original
            if mask.sum() < 0.01 * (h * w):
                return image

            ys, xs = np.where(mask)
            y1, y2 = int(ys.min()), int(ys.max())
            x1, x2 = int(xs.min()), int(xs.max())

            # Add margin
            margin_y = int(0.05 * (y2 - y1 + 1))
            margin_x = int(0.05 * (x2 - x1 + 1))
            y1 = max(0, y1 - margin_y)
            y2 = min(h, y2 + margin_y)
            x1 = max(0, x1 - margin_x)
            x2 = min(w, x2 + margin_x)

            cropped = image.crop((x1, y1, x2, y2))
            # Avoid extreme narrow crops
            if cropped.size[0] < 40 or cropped.size[1] < 40:
                return image
            return cropped
        except Exception:
            return image

    def _load_image(self, image_file) -> Image.Image:
        """Load image from file"""
        if hasattr(image_file, 'read'):
            # Django file field
            image_data = image_file.read()
            image = Image.open(io.BytesIO(image_data))
        else:
            # File path
            image = Image.open(image_file)

        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        return image

    def _extract_basic_features(self, image: Image.Image) -> Dict:
        """Extract basic features from image"""
        width, height = image.size
        aspect_ratio = width / height if height > 0 else 1

        # Estimate if it's a single item or group
        is_single_item = aspect_ratio < 2.5  # Most clothing items aren't extremely wide

        return {
            'width': width,
            'height': height,
            'aspect_ratio': aspect_ratio,
            'estimated_single_item': is_single_item,
        }

    def _infer_with_api(self, image: Image.Image) -> Dict:
        """Send image to OpenVisionAPI-style endpoint and parse response."""
        if not self.api_base_url:
            return {'item_type': 'clothing item', 'category': 'tops', 'confidence': 0.0}
        try:
            buf = io.BytesIO()
            image.save(buf, format='JPEG', quality=90)
            buf.seek(0)
            files = {'image': ('image.jpg', buf, 'image/jpeg')}
            data = {'task': self.api_task}
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            resp = requests.post(f"{self.api_base_url}/predict", files=files, data=data, headers=headers, timeout=self.api_timeout)
            resp.raise_for_status()
            payload = resp.json()
            predictions = payload.get('predictions') or payload.get('results') or payload.get('detections') or []
            if isinstance(predictions, dict):
                predictions = predictions.get('detections') or predictions.get('items') or []
            best = None
            best_score = -1.0
            clothing_keywords = ['shirt','t-shirt','dress','jacket','coat','blazer','hoodie','sweater','cardigan','pants','trousers','jeans','shorts','skirt','leggings','waistcoat','vest','gilet']
            for p in predictions:
                label = (p.get('label') or p.get('class') or p.get('name') or '').lower()
                score = float(p.get('confidence') or p.get('score') or p.get('prob') or 0.0)
                if not label:
                    continue
                boost = 0.15 if any(k in label for k in clothing_keywords) else 0.0
                ranked = score + boost
                if ranked > best_score:
                    best = {'label': label, 'score': score}
                    best_score = ranked
            if best:
                item_type, category = self._canonicalize_label(best['label'])
                return {
                    'item_type': item_type,
                    'category': category,
                    'confidence': float(best['score']),
                    'raw_results': predictions[:3] if isinstance(predictions, list) else [],
                }
        except Exception as e:
            print(f"[AI] Remote inference failed: {e}")
        return {'item_type': 'clothing item', 'category': 'tops', 'confidence': 0.0}

    def _canonicalize_label(self, label: str) -> tuple[str, str]:
        """Map label/synonym to canonical item_type and category"""
        label = label.lower().strip()
        # Normalize French -> English where helpful
        mapping = {
            # Shirts
            'chemise': ('shirt', 'tops'),
            'chemise noire': ('black shirt', 'tops'),
            'chemise blanche': ('white shirt', 'tops'),
            'dress shirt': ('dress shirt', 'tops'),
            'button-up shirt': ('shirt', 'tops'),
            'long-sleeve shirt': ('long-sleeve shirt', 'tops'),
            'short-sleeve shirt': ('short-sleeve shirt', 'tops'),
            'shirt': ('shirt', 'tops'),
            't-shirt': ('t-shirt', 'tops'),
            'polo shirt': ('polo shirt', 'tops'),
            'blouse': ('blouse', 'tops'),
            # Outerwear
            'jacket': ('jacket', 'outerwear'),
            'coat': ('coat', 'outerwear'),
            'blazer': ('blazer', 'outerwear'),
            'cardigan': ('cardigan', 'outerwear'),
            'hoodie': ('hoodie', 'tops'),
            'sweater': ('sweater', 'tops'),
            'pull': ('sweater', 'tops'),
            'gilet': ('cardigan', 'outerwear'),
            # Bottoms
            'jeans': ('jeans', 'bottoms'),
            'pants': ('pants', 'bottoms'),
            'trousers': ('pants', 'bottoms'),
            'shorts': ('shorts', 'bottoms'),
            'skirt': ('skirt', 'bottoms'),
            'leggings': ('leggings', 'bottoms'),
            # One piece
            'dress': ('dress', 'dresses'),
            'robe': ('dress', 'dresses'),
            # Vests (avoid tactical assumptions)
            'waistcoat': ('waistcoat', 'outerwear'),
            'vest': ('vest', 'outerwear'),
            'gilet sans manches': ('vest', 'outerwear'),
        }
        if label in mapping:
            return mapping[label]
        # Default heuristic
        if 'shirt' in label or 'chemise' in label:
            return ('shirt', 'tops')
        if any(k in label for k in ['jacket', 'coat', 'blazer', 'cardigan']):
            return (label, 'outerwear')
        if any(k in label for k in ['jeans', 'pants', 'trousers', 'shorts', 'skirt', 'leggings']):
            cat = 'bottoms'
            base = 'pants' if 'pants' in label or 'trousers' in label else label
            return (base, cat)
        if any(k in label for k in ['dress', 'robe']):
            return ('dress', 'dresses')
        return ('clothing item', 'tops')

    def _map_to_fashion_categories(self, classification_results: List[Dict]) -> Dict:
        """Map general classification results to fashion categories"""
        # Define fashion-related keywords
        fashion_keywords = {
            'tops': ['shirt', 't-shirt', 'blouse', 'sweater', 'jacket', 'coat', 'cardigan', 'hoodie', 'polo'],
            'bottoms': ['pants', 'trousers', 'jeans', 'shorts', 'skirt', 'leggings'],
            'dresses': ['dress', 'gown', 'robe'],
            'outerwear': ['jacket', 'coat', 'blazer', 'vest'],
            'shoes': ['shoe', 'sneaker', 'boot', 'sandal', 'heel'],
            'accessories': ['hat', 'cap', 'bag', 'purse', 'belt', 'scarf', 'jewelry', 'watch', 'glove'],
        }

        # Reverse mapping for quick lookup
        keyword_to_category = {}
        for category, keywords in fashion_keywords.items():
            for keyword in keywords:
                keyword_to_category[keyword] = category

        # Analyze results
        best_match = None
        best_score = 0.0
        best_category = 'tops'  # default

        for result in classification_results:
            label = result['label'].lower()
            score = result['score']

            # Check for fashion keywords
            for keyword, category in keyword_to_category.items():
                if keyword in label:
                    if score > best_score:
                        best_score = score
                        best_match = label
                        best_category = category
                    break

        # If no fashion match found, try to infer from general categories
        if not best_match:
            for result in classification_results:
                label = result['label'].lower()
                score = result['score']

                # Look for clothing-related terms
                if any(term in label for term in ['clothing', 'garment', 'apparel', 'wear']):
                    best_match = label
                    best_score = score
                    break

        return {
            'item_type': best_match or 'clothing item',
            'category': best_category,
            'confidence': best_score,
            'raw_results': classification_results[:3]  # Keep top 3 for debugging
        }

    def _analyze_colors(self, image: Image.Image) -> Dict:
        """Analyze colors in the image with simple background filtering (ignore near-white)."""
        try:
            # Resize for faster processing
            image_small = image.resize((160, 160), Image.Resampling.LANCZOS)

            # Convert to numpy array
            arr = np.array(image_small)
            # Flatten to (N, 3)
            pixels = arr.reshape(-1, 3)

            # Create mask to ignore near-white/very bright pixels (common background)
            # Threshold: all channels > 230 considered background
            mask = ~((pixels[:, 0] > 230) & (pixels[:, 1] > 230) & (pixels[:, 2] > 230))
            fg_pixels = pixels[mask]

            # If too few foreground pixels, fallback to all pixels
            if fg_pixels.size < 100:
                fg_pixels = pixels

            # Count colors on reduced set by rounding to reduce noise
            reduced = (fg_pixels // 8) * 8  # bucketize to 32 levels per channel
            tuples = list(map(tuple, reduced.tolist()))
            color_counts = Counter(tuples)
            most_common_colors = color_counts.most_common(5)

            # Convert RGB to color names
            primary_rgb = most_common_colors[0][0]
            primary_color = self._rgb_to_color_name(primary_rgb)
            secondary_colors = [self._rgb_to_color_name(c[0]) for c in most_common_colors[1:3]]

            # Get hex codes
            primary_hex = self._rgb_to_hex(primary_rgb)

            # Determine if it's patterned
            # Use fg_pixels for variance-based pattern detection
            pattern_score = self._detect_pattern([tuple(x) for x in fg_pixels[:10000]])
            pattern_type = self._classify_pattern(pattern_score)

            return {
                'primary_color': primary_color,
                'primary_hex': primary_hex,
                'secondary_colors': secondary_colors,
                'pattern': pattern_type,
                'color_distribution': len(color_counts),
            }

        except Exception as e:
            print(f"Color analysis error: {str(e)}")
            return {
                'primary_color': '',
                'primary_hex': '',
                'secondary_colors': [],
                'pattern': 'solid',
                'color_distribution': 0,
            }

    def _rgb_to_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to color name"""
        # Find closest color
        min_distance = float('inf')
        closest_color = "unknown"

        for color_rgb, color_name in self.color_names.items():
            distance = sum((a - b) ** 2 for a, b in zip(rgb, color_rgb))
            if distance < min_distance:
                min_distance = distance
                closest_color = color_name

        return closest_color

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _detect_pattern(self, pixels: List[Tuple[int, int, int]]) -> float:
        """Detect if image has a pattern (rough heuristic)"""
        if not pixels:
            return 0.0

        # Calculate color variance
        r_values = [p[0] for p in pixels]
        g_values = [p[1] for p in pixels]
        b_values = [p[2] for p in pixels]

        r_var = np.var(r_values)
        g_var = np.var(g_values)
        b_var = np.var(b_values)

        avg_variance = (r_var + g_var + b_var) / 3

        # Normalize to 0-1 scale (rough heuristic)
        pattern_score = min(avg_variance / 1000, 1.0)

        return pattern_score

    def _classify_pattern(self, pattern_score: float) -> str:
        """Classify pattern type based on score"""
        if pattern_score < 0.3:
            return "solid"
        elif pattern_score < 0.6:
            return "subtle pattern"
        else:
            return "patterned"

    def _combine_analyses(self, basic: Dict, ai: Dict, colors: Dict) -> Dict:
        """Combine all analysis results into final output"""
        # Map categories to more specific types
        category_to_types = {
            'tops': ['t-shirt', 'shirt', 'blouse', 'sweater', 'hoodie'],
            'bottoms': ['pants', 'jeans', 'shorts', 'skirt'],
            'dresses': ['dress'],
            'outerwear': ['jacket', 'coat'],
            'shoes': ['shoes', 'sneakers', 'boots'],
            'accessories': ['hat', 'bag', 'belt', 'scarf'],
        }

        category = ai.get('category', 'tops')
        possible_types = category_to_types.get(category, ['clothing item'])

        # Generate description
        description = self._generate_description(ai, colors, basic)

        # Determine material (rough heuristic)
        material = self._infer_material(colors, ai)

        # Determine style and occasions
        style_info = self._infer_style_and_occasions(ai, colors)

        return {
            'item_type': ai.get('item_type', 'clothing item'),
            'category': category,
            'color': colors.get('primary_color', ''),
            'color_hex': colors.get('primary_hex', ''),
            'secondary_colors': colors.get('secondary_colors', []),
            'pattern': colors.get('pattern', 'solid'),
            'material': material,
            'style': style_info['style'],
            'occasions': style_info['occasions'],
            'seasons': self._infer_seasons(colors.get('primary_color', '')),
            'gender': 'unisex',  # Default assumption
            'brand_guess': None,  # Would need brand detection model
            'condition': 'good',  # Default assumption
            'description': description,
            'tags': self._generate_tags(ai, colors, basic),
            'confidence': ai.get('confidence', 0.5),
            'features': self._extract_features(basic, ai),
        }

    def _generate_description(self, ai: Dict, colors: Dict, basic: Dict) -> str:
        """Generate a human-readable description"""
        item_type = ai.get('item_type', 'clothing item')
        color = colors.get('primary_color', 'colored')
        pattern = colors.get('pattern', 'solid')

        if pattern != 'solid':
            desc = f"A {color} {item_type} with {pattern}"
        else:
            desc = f"A {color} {item_type}"

        return desc

    def _infer_material(self, colors: Dict, ai: Dict) -> str:
        """Infer material based on colors and item type"""
        # Very basic heuristics
        item_type = ai.get('item_type', '').lower()

        if 'jean' in item_type or 'denim' in item_type:
            return 'denim'
        elif 'leather' in item_type or 'suede' in item_type:
            return 'leather'
        elif 'wool' in item_type or 'knit' in item_type:
            return 'wool'
        elif 'cotton' in item_type:
            return 'cotton'
        else:
            # Default based on color brightness
            primary_color = colors.get('primary_color', '')
            if primary_color in ['white', 'pastel']:
                return 'cotton'
            else:
                return 'polyester'  # Common synthetic

    def _infer_style_and_occasions(self, ai: Dict, colors: Dict) -> Dict:
        """Infer style and suitable occasions"""
        item_type = ai.get('item_type', '').lower()
        color = colors.get('primary_color', '')

        # Basic style inference
        if any(word in item_type for word in ['jean', 'sneaker', 't-shirt']):
            style = 'casual'
            occasions = ['casual', 'everyday']
        elif any(word in item_type for word in ['dress', 'blouse', 'heel']):
            style = 'formal'
            occasions = ['work', 'formal', 'party']
        elif any(word in item_type for word in ['jacket', 'coat']):
            style = 'business'
            occasions = ['work', 'business']
        else:
            style = 'casual'
            occasions = ['casual']

        return {'style': style, 'occasions': occasions}

    def _infer_seasons(self, color: str) -> List[str]:
        """Infer suitable seasons based on color"""
        # Very basic heuristics
        if color in ['white', 'pastel', 'bright']:
            return ['spring', 'summer']
        elif color in ['dark', 'navy', 'black']:
            return ['fall', 'winter']
        else:
            return ['spring', 'summer', 'fall']  # Most colors work in multiple seasons

    def _generate_tags(self, ai: Dict, colors: Dict, basic: Dict) -> List[str]:
        """Generate relevant tags"""
        tags = []

        # Add item type related tags
        item_type = ai.get('item_type', '').lower()
        if 'shirt' in item_type:
            tags.extend(['top', 'shirt'])
        elif 'pants' in item_type or 'jean' in item_type:
            tags.extend(['bottom', 'pants'])
        elif 'dress' in item_type:
            tags.extend(['dress', 'one-piece'])

        # Add color tags
        color = colors.get('primary_color', '')
        if color:
            tags.append(color)

        # Add pattern tags
        pattern = colors.get('pattern', '')
        if pattern and pattern != 'solid':
            tags.append(pattern)

        return tags[:5]  # Limit to 5 tags

    def _extract_features(self, basic: Dict, ai: Dict) -> Dict:
        """Extract item features"""
        return {
            'aspect_ratio': basic.get('aspect_ratio', 1.0),
            'estimated_single_item': basic.get('estimated_single_item', True),
        }

    def _get_fallback_analysis(self) -> Dict:
        """Return fallback analysis when AI fails"""
        return {
            'item_type': 'clothing item',
            'category': 'tops',
            'color': '',
            'color_hex': '',
            'secondary_colors': [],
            'pattern': 'solid',
            'material': 'cotton',
            'style': 'casual',
            'occasions': ['casual'],
            'seasons': ['all'],
            'gender': 'unisex',
            'brand_guess': None,
            'condition': 'good',
            'description': 'A clothing item',
            'tags': [],
            'confidence': 0.0,
            'features': {},
        }

    def get_category_suggestions(self, analysis: Dict) -> List[Dict]:
        """Get category suggestions based on analysis"""
        category = analysis.get('category', 'tops')

        suggestions = [
            {'name': 'Tops', 'confidence': 0.8 if category == 'tops' else 0.4},
            {'name': 'Bottoms', 'confidence': 0.8 if category == 'bottoms' else 0.4},
            {'name': 'Dresses', 'confidence': 0.8 if category == 'dresses' else 0.4},
            {'name': 'Outerwear', 'confidence': 0.8 if category == 'outerwear' else 0.4},
            {'name': 'Shoes', 'confidence': 0.8 if category == 'shoes' else 0.4},
            {'name': 'Accessories', 'confidence': 0.8 if category == 'accessories' else 0.4},
        ]

        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)

        return suggestions[:3]


# Singleton instance for reuse
_analyzer_instance = None

def get_image_analyzer() -> OpenSourceClothingImageAnalyzer:
    """
    Get singleton instance of the open source image analyzer
    """
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = OpenSourceClothingImageAnalyzer()
    return _analyzer_instance
