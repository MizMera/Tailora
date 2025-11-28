#!/usr/bin/env python3
"""
Quick test script for category-aware color detection enhancement.
Tests the improved color analysis with real fashion dataset insights.
"""

import io

class MockFile:
    """Mock file object for testing."""
    def __init__(self, image):
        self.image = image

    def read(self):
        # Convert PIL image to bytes
        buffer = io.BytesIO()
        self.image.save(buffer, format='JPEG')
        buffer.seek(0)
        return buffer.getvalue()

import os
import sys
import io
from PIL import Image, ImageDraw

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wardrobe.ai_image_analyzer import FashionImageAnalyzer

def create_test_clothing_image(color, category="shirt"):
    """Create a test image with specific color and category."""
    width, height = 300, 400

    # Create base image
    img = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(img)

    # Add some variation to make it more realistic
    for i in range(10):
        x = i * 30
        y = i * 40
        variation_color = tuple(min(255, c + i*5) for c in color)
        draw.rectangle([x, y, x+20, y+20], fill=variation_color)

    return img

def test_category_color_detection():
    """Test the enhanced category-aware color detection."""
    analyzer = FashionImageAnalyzer()

    # Test different categories with their typical colors
    test_cases = [
        ("shirt", (100, 150, 200), "tops"),      # Blue shirt
        ("pants", (50, 50, 150), "bottoms"),     # Navy pants
        ("dress", (200, 100, 150), "dresses"),   # Pink dress
        ("shoes", (50, 50, 50), "shoes"),        # Black shoes
    ]

    print("🧪 TESTING CATEGORY-AWARE COLOR DETECTION")
    print("=" * 50)

    for item_type, color, expected_category in test_cases:
        print(f"\n📸 Testing {item_type.upper()} ({expected_category})")
        print(f"   Color: RGB{color}")

        # Create test image
        test_image = create_test_clothing_image(color, item_type)

        # Create mock file object
        mock_file = MockFile(test_image)

        # Analyze the image
        try:
            result = analyzer.analyze_image(mock_file)

            print("   ✅ Detection Results:")
            print(f"      Item Type: {result.get('item_type', 'unknown')}")
            print(f"      Category: {result.get('category', 'unknown')}")
            print(f"      Primary Color: {result.get('color', 'unknown')}")
            print(f"      Secondary Colors: {result.get('secondary_colors', [])}")
            print(f"      Pattern: {result.get('pattern', 'unknown')}")
            print(f"      Confidence: {result.get('confidence', 0):.1%}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

    print("\n" + "=" * 50)
    print("🎉 Category-aware color detection test complete!")

if __name__ == "__main__":
    test_category_color_detection()