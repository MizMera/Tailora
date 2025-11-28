#!/usr/bin/env python3
"""
Test script for the new multi-feature clothing detection system.
Tests various clothing items to ensure robust detection regardless of image size.
"""

import os
import sys
import io
import numpy as np
from PIL import Image, ImageDraw

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wardrobe.ai_image_analyzer import FashionImageAnalyzer

class MockFile:
    """Mock file object for testing."""
    def __init__(self, image):
        self.image = image

    def read(self):
        # Convert PIL image to bytes
        buffer = io.BytesIO()
        self.image.save(buffer, format='JPEG')
        return buffer.getvalue()

def create_test_image(width, height, color, shape="rectangle"):
    """Create a simple test image for testing detection."""
    img = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(img)

    if shape == "shirt":
        # Draw a realistic shirt shape
        # Collar (darker area at top)
        collar_color = tuple(max(0, c-40) for c in color)
        draw.rectangle([width//3, 0, 2*width//3, height//6], fill=collar_color)
        # Sleeves (darker sides)
        sleeve_color = tuple(max(0, c-30) for c in color)
        draw.rectangle([0, height//5, width//5, height//2], fill=sleeve_color)
        draw.rectangle([4*width//5, height//5, width, height//2], fill=sleeve_color)
        # Buttons down center (small dark spots)
        button_color = (0, 0, 0)
        for i in range(4, 9):
            y = i * height // 12
            draw.rectangle([width//2-3, y-3, width//2+3, y+3], fill=button_color)

    elif shape == "socks":
        # Draw realistic sock features
        # Ankle opening (lighter top third)
        ankle_color = tuple(min(255, c+50) for c in color)
        draw.rectangle([0, 0, width, height//3], fill=ankle_color)
        # Heel/toe area (darker bottom)
        heel_color = tuple(max(0, c-60) for c in color)
        draw.rectangle([width//4, height//2, 3*width//4, height], fill=heel_color)

    elif shape == "shoes":
        # Draw realistic shoe features
        # Sole (very dark bottom)
        sole_color = (30, 30, 30)
        draw.rectangle([0, 4*height//5, width, height], fill=sole_color)
        # Upper (slightly darker)
        upper_color = tuple(max(0, c-20) for c in color)
        draw.rectangle([width//6, height//3, 5*width//6, 4*height//5], fill=upper_color)

    elif shape == "pants":
        # Draw realistic pants features
        # Waistband (darker top)
        waist_color = tuple(max(0, c-50) for c in color)
        draw.rectangle([0, 0, width, height//8], fill=waist_color)
        # Leg openings (darker bottom)
        leg_color = tuple(max(0, c-40) for c in color)
        draw.rectangle([width//6, 7*height//8, width//2-5, height], fill=leg_color)
        draw.rectangle([width//2+5, 7*height//8, 5*width//6, height], fill=leg_color)

    elif shape == "dress":
        # Draw realistic dress features
        # Bodice (darker top half)
        bodice_color = tuple(max(0, c-30) for c in color)
        draw.rectangle([0, 0, width, height//2], fill=bodice_color)
        # Skirt flares (bottom gets lighter)
        skirt_color = tuple(min(255, c+20) for c in color)
        draw.rectangle([0, height//2, width, height], fill=skirt_color)

    return img

def test_detection():
    """Test the new multi-feature detection system."""
    analyzer = FashionImageAnalyzer()

    test_cases = [
        # (width, height, color, shape, expected_type)
        (300, 400, (100, 150, 200), "shirt", "shirt"),  # Blue shirt
        (200, 600, (150, 150, 150), "socks", "socks"),  # Gray socks
        (400, 200, (80, 80, 80), "shoes", "shoes"),     # Gray shoes
        (250, 500, (120, 80, 60), "pants", "pants"),    # Brown pants
        (300, 600, (200, 100, 150), "dress", "dress"),  # Purple dress
    ]

    print("=== TESTING NEW MULTI-FEATURE DETECTION SYSTEM ===\n")

    for i, (width, height, color, shape, expected) in enumerate(test_cases, 1):
        print(f"Test {i}: {shape} ({width}x{height}) - Expected: {expected}")

        # Create test image
        img = create_test_image(width, height, color, shape)

        # Create mock file object
        mock_file = MockFile(img)

        # Analyze
        result = analyzer.analyze_image(mock_file)

        detected_type = result.get('item_type', 'unknown')
        confidence = result.get('confidence', 0.0)

        status = "✓" if detected_type == expected else "✗"
        print(f"  {status} Detected: {detected_type} ({confidence:.1%})")
        print()

def test_smart_cropping():
    """Test the new smart cropping functionality."""
    analyzer = FashionImageAnalyzer()

    test_cases = [
        # (width, height, color, shape, expected_type)
        (300, 400, (100, 150, 200), "shirt", "shirt"),  # Blue shirt
        (200, 600, (150, 150, 150), "socks", "socks"),  # Gray socks
        (400, 200, (80, 80, 80), "shoes", "shoes"),     # Gray shoes
        (250, 500, (120, 80, 60), "pants", "pants"),    # Brown pants
        (300, 600, (200, 100, 150), "dress", "dress"),  # Purple dress
    ]

    print("=== TESTING SMART CROPPING FUNCTIONALITY ===\n")

    for i, (width, height, color, shape, expected) in enumerate(test_cases, 1):
        print(f"Test {i}: {shape} ({width}x{height}) - Expected: {expected}")

        # Create test image
        img = create_test_image(width, height, color, shape)

        # Test smart cropping
        cropped = analyzer._smart_crop_clothing(img)

        print(f"  Original size: {img.size}")
        print(f"  Cropped size: {cropped.size}")
        print(f"  Standardized to: {cropped.size} (square canvas)")
        print()

if __name__ == "__main__":
    test_smart_cropping()
    test_detection()