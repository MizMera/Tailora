#!/usr/bin/env python
"""
Test script for the open source AI image analyzer
"""
import os
import sys
from PIL import Image, ImageDraw
import io

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wardrobe.ai_image_analyzer import get_image_analyzer

def create_test_image(color='blue', pattern='solid'):
    """Create a simple test image"""
    # Create a 200x200 image
    img = Image.new('RGB', (200, 200), color=color if isinstance(color, tuple) else (0, 0, 255))
    draw = ImageDraw.Draw(img)

    if pattern == 'striped':
        # Add some stripes
        for i in range(0, 200, 20):
            draw.rectangle([0, i, 200, i+10], fill=(255, 255, 255))
    elif pattern == 'dotted':
        # Add some dots
        for x in range(10, 190, 30):
            for y in range(10, 190, 30):
                draw.ellipse([x, y, x+10, y+10], fill=(255, 255, 255))

    return img

def test_image_analysis():
    """Test the image analysis functionality"""
    print("🧪 Testing Open Source AI Image Analyzer")
    print("=" * 50)

    # Get the analyzer
    analyzer = get_image_analyzer()

    # Create test images
    test_images = [
        ('blue_shirt', create_test_image((0, 0, 255), 'solid')),
        ('red_dress', create_test_image((255, 0, 0), 'solid')),
        ('striped_pants', create_test_image((0, 100, 0), 'striped')),
        ('white_accessory', create_test_image((255, 255, 255), 'solid')),
    ]

    for name, image in test_images:
        print(f"\n📸 Testing {name}...")

        # Save to bytes for testing
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        # Create a file-like object
        from django.core.files.uploadedfile import InMemoryUploadedFile
        test_file = InMemoryUploadedFile(
            img_bytes, None, f'{name}.jpg', 'image/jpeg', img_bytes.tell(), None
        )

        try:
            # Analyze the image
            result = analyzer.analyze_image(test_file)

            # Print results
            print(f"  Item Type: {result.get('item_type', 'N/A')}")
            print(f"  Category: {result.get('category', 'N/A')}")
            print(f"  Color: {result.get('color', 'N/A')}")
            print(f"  Pattern: {result.get('pattern', 'N/A')}")
            print(f"  Confidence: {result.get('confidence', 0):.2f}")
            print(f"  Description: {result.get('description', 'N/A')}")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

    print("\n✅ Testing completed!")

if __name__ == "__main__":
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tailora_project.settings')
    import django
    django.setup()

    test_image_analysis()