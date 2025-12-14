"""
BLIP-2 Fashion Image Captioning Integration for Tailora
Generates rich, detailed descriptions of fashion items using pre-trained BLIP-2 model.
"""

import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from PIL import Image
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class BLIP2FashionCaptioner:
    """
    BLIP-2 based fashion image captioning system.
    Generates detailed, fashion-specific descriptions from clothing images.
    """

    def __init__(self, model_name: str = "Salesforce/blip2-opt-2.7b", device: str = "auto"):
        """
        Initialize BLIP-2 fashion captioner.

        Args:
            model_name: HuggingFace model name for BLIP-2
            device: Device to run model on ('auto', 'cpu', 'cuda')
        """
        self.model_name = model_name
        self.device = self._setup_device(device)
        self.processor = None
        self.model = None
        self._load_model()

    def _setup_device(self, device: str) -> str:
        """Setup the appropriate device for model inference."""
        if device == "auto":
            if torch.cuda.is_available():
                # Check GPU memory and prefer GPU if available (reduced requirement for RTX 3050)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
                if gpu_memory >= 3:  # Reduced to 3GB for RTX 3050 with 8-bit quantization
                    logger.info(f"GPU memory: {gpu_memory:.1f} GB, using GPU")
                    return "cuda"
                else:
                    logger.warning(f"GPU memory: {gpu_memory:.1f} GB, insufficient for GPU, using CPU")
                    return "cpu"
            else:
                logger.info("CUDA not available, using CPU")
                return "cpu"
        return device

    def _load_model(self):
        """Load BLIP-2 model and processor with GPU optimizations."""
        try:
            logger.info(f"Loading BLIP-2 model: {self.model_name} on {self.device}")

            # Load processor
            self.processor = Blip2Processor.from_pretrained(self.model_name)

            # GPU-specific loading optimizations
            if self.device == "cuda":
                # Use float16 for memory efficiency and speed
                torch_dtype = torch.float16

                # Force all model parts to GPU for maximum speed
                device_map = {"": "cuda"}  # Force everything to GPU

                # Enable memory optimizations for RTX 3050 (4GB)
                model_kwargs = {
                    "torch_dtype": torch_dtype,
                    "device_map": device_map,
                    "load_in_8bit": True, # QUANTIZATION ENABLED
                    "low_cpu_mem_usage": True,
                }

                logger.info("Loading BLIP-2 with GPU optimizations (8-bit quantization, forced GPU)")

            else:
                # CPU loading
                torch_dtype = torch.float32
                device_map = None

                model_kwargs = {
                    "torch_dtype": torch_dtype,
                    "low_cpu_mem_usage": True,
                }

                logger.info("Loading BLIP-2 for CPU usage")

            # Load the model with optimizations
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                self.model_name,
                **model_kwargs
            )

            # Set to evaluation mode
            self.model.eval()

            # Log memory usage
            if self.device == "cuda":
                memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
                memory_reserved = torch.cuda.memory_reserved() / 1024**3   # GB
                logger.info(f"GPU memory allocated: {memory_allocated:.1f} GB, reserved: {memory_reserved:.1f} GB")
            else:
                logger.info("Model loaded on CPU")

            logger.info(f"✅ BLIP-2 model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"❌ Failed to load BLIP-2 model: {str(e)}")
            raise

    def generate_caption(self, image: Image.Image, max_length: int = 50, num_beams: int = 5) -> str:
        """
        Generate a fashion caption for the given image.

        Args:
            image: PIL Image of clothing item
            max_length: Maximum length of generated caption
            num_beams: Number of beams for beam search

        Returns:
            Generated fashion caption
        """
        try:
            # Prepare image for model
            inputs = self.processor(image, return_tensors="pt").to(self.device)

            # Generate caption
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=True,
                    do_sample=False,  # Use greedy decoding for consistency
                    repetition_penalty=1.2
                )

            # Decode generated text
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

            # Clean up the caption
            cleaned_caption = self._clean_caption(generated_text)

            logger.info(f"Generated caption: {cleaned_caption}")
            return cleaned_caption

        except Exception as e:
            logger.error(f"Error generating caption: {str(e)}")
            return "A clothing item"

    def _clean_caption(self, caption: str) -> str:
        """
        Clean and enhance the generated caption for fashion context.

        Args:
            caption: Raw generated caption

        Returns:
            Cleaned and enhanced caption
        """
        # Remove common artifacts
        caption = caption.strip()

        # Capitalize first letter
        if caption:
            caption = caption[0].upper() + caption[1:]

        # Add period if missing
        if caption and not caption.endswith(('.', '!', '?')):
            caption += '.'

        return caption

    def generate_enhanced_description(self, image: Image.Image, style_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate enhanced fashion description with additional metadata.

        Args:
            image: PIL Image of clothing item
            style_context: Optional context about style preferences

        Returns:
            Dictionary with caption and metadata
        """
        caption = self.generate_caption(image)

        # Extract additional fashion attributes from caption
        attributes = self._extract_fashion_attributes(caption)

        return {
            'caption': caption,
            'attributes': attributes,
            'confidence': 0.85,  # Placeholder - could be improved with confidence scoring
            'model': self.model_name,
            'device': self.device
        }

    def _extract_fashion_attributes(self, caption: str) -> Dict[str, Any]:
        """
        Extract fashion attributes from the generated caption.

        Args:
            caption: Generated caption

        Returns:
            Dictionary of extracted fashion attributes
        """
        # This is a basic implementation - could be enhanced with NLP
        caption_lower = caption.lower()

        attributes = {
            'colors': [],
            'styles': [],
            'materials': [],
            'patterns': []
        }

        # Basic color detection
        colors = ['red', 'blue', 'green', 'yellow', 'black', 'white', 'gray', 'pink', 'purple', 'orange', 'brown', 
                 'beige', 'tan', 'burgundy', 'navy', 'cream', 'gold', 'silver']
        for color in colors:
            if color in caption_lower:
                attributes['colors'].append(color)

        # Basic style detection
        styles = ['casual', 'formal', 'elegant', 'modern', 'vintage', 'classic', 'sporty', 
                 'bohemian', 'boho', 'streetwear', 'minimalist', 'chic', 'retro', 'urban', 'preppy']
        for style in styles:
            if style in caption_lower:
                attributes['styles'].append(style)

        # Basic material detection
        materials = ['cotton', 'wool', 'silk', 'leather', 'denim', 'linen']
        for material in materials:
            if material in caption_lower:
                attributes['materials'].append(material)

        # Basic pattern detection
        patterns = ['striped', 'floral', 'polka dot', 'plaid', 'solid']
        for pattern in patterns:
            if pattern in caption_lower:
                attributes['patterns'].append(pattern)

        return attributes

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'model') and self.model is not None:
            del self.model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Global instance for reuse
_captioner_instance = None

def get_fashion_captioner(model_name: str = "Salesforce/blip2-opt-2.7b") -> BLIP2FashionCaptioner:
    """
    Get or create a global BLIP-2 fashion captioner instance.

    Args:
        model_name: HuggingFace model name

    Returns:
        BLIP2FashionCaptioner instance
    """
    global _captioner_instance

    if _captioner_instance is None or _captioner_instance.model_name != model_name:
        _captioner_instance = BLIP2FashionCaptioner(model_name)

    return _captioner_instance