#!/usr/bin/env python3
"""
Test script to verify improved jeans/pants detection.
Tests the fixes for false detection issues.
"""

import os
import sys
import io
from PIL import Image, ImageDraw

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wardrobe.ai_image_analyzer import FashionImageAnalyzer

class MockFile:
    """Mock file object for testing."""
    def __init__(self, image):
        self.image = image

    def read(self):
        buffer = io.BytesIO()
        self.image.save(buffer, format='JPEG')
        buffer.seek(0)
        return buffer.getvalue()

def create_jeans_image(width=300, height=500):
    """Create a realistic jeans/pants test image."""
    # Blue denim color
    denim_blue = (70, 100, 150)
    
    img = Image.new('RGB', (width, height), denim_blue)
    draw = ImageDraw.Draw(img)
    
    # Waistband (darker at top)
    waistband_color = (50, 70, 110)
    draw.rectangle([0, 0, width, height//10], fill=waistband_color)
    
    # Add some texture variation (realistic denim)
    for i in range(20):
        x = (i * width) // 20
        variation = (i % 3) * 10
        varied_color = tuple(min(255, c + variation) for c in denim_blue)
        draw.rectangle([x, height//5, x + width//20, height], fill=varied_color)
    
    # Leg separation (vertical seam)
    seam_color = (50, 80, 120)
    draw.line([width//2, height//3, width//2, height], fill=seam_color, width=2)
    
    return img

def test_jeans_detection():
    """Test the improved jeans detection."""
    print("\n" + "="*60)
    print("🧪 TESTING IMPROVED JEANS/PANTS DETECTION")
    print("="*60 + "\n")
    
    analyzer = FashionImageAnalyzer()
    
    # Test cases with different aspect ratios
    test_cases = [
        ("Standard Jeans", 300, 500, 1.67),
        ("Cropped Jeans", 300, 450, 1.50),
        ("Wide Leg Jeans", 350, 550, 1.57),
        ("Tall Jeans", 280, 600, 2.14),
    ]
    
    for name, width, height, expected_ar in test_cases:
        print(f"\n📸 Testing: {name}")
        print(f"   Size: {width}x{height} (aspect ratio: {expected_ar:.2f})")
        
        # Create test image
        jeans_img = create_jeans_image(width, height)
        mock_file = MockFile(jeans_img)
        
        # Analyze
        try:
            result = analyzer.analyze_image(mock_file)
            
            detected_type = result.get('item_type', 'unknown')
            detected_category = result.get('category', 'unknown')
            confidence = result.get('confidence', 0)
            color = result.get('color', 'unknown')
            
            # Check if correct
            is_correct = detected_type == 'pants' or detected_category == 'bottoms'
            status = "✅ CORRECT" if is_correct else "❌ WRONG"
            
            print(f"   {status}")
            print(f"   Detected: {detected_type} ({detected_category})")
            print(f"   Confidence: {confidence:.1%}")
            print(f"   Color: {color}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_jeans_detection()
