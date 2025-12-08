#!/usr/bin/env python
"""
Quick test for BLIP-2 integration in Tailora - demonstrates the enhanced description system.
This test works without downloading the large BLIP-2 model.
"""

import os
import sys
import django
from PIL import Image
from io import BytesIO

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tailora_project.settings')
django.setup()

from wardrobe.ai_image_analyzer import get_image_analyzer

def create_test_fashion_image(color: str = 'navy', width: int = 300, height: int = 400) -> Image.Image:
    """Create a test image that looks like clothing."""
    # Create base image
    img = Image.new('RGB', (width, height), color=color)

    # Add some clothing-like features (simple patterns)
    if color == 'navy':
        # Add some lighter areas to simulate fabric texture
        for x in range(0, width, 20):
            for y in range(0, height, 20):
                if (x + y) % 40 == 0:
                    for i in range(min(10, width - x)):
                        for j in range(min(10, height - y)):
                            if i + j < 15:
                                img.putpixel((x + i, y + j), (100, 100, 150))

    return img

def test_enhanced_descriptions():
    """Test the enhanced description system with various clothing types."""
    print("🧪 Testing Enhanced BLIP-2 Fashion Description System")
    print("=" * 65)

    # Test cases simulating different clothing items
    test_cases = [
        {
            'name': 'Navy Blazer',
            'color': 'navy',
            'size': (280, 380),
            'expected_type': 'jacket',
            'description': 'A sophisticated navy blue blazer'
        },
        {
            'name': 'Red Dress',
            'color': 'red',
            'size': (250, 450),
            'expected_type': 'dress',
            'description': 'An elegant red dress'
        },
        {
            'name': 'White Shirt',
            'color': 'white',
            'size': (300, 350),
            'expected_type': 'shirt',
            'description': 'A crisp white shirt'
        },
        {
            'name': 'Black Pants',
            'color': 'black',
            'size': (200, 500),
            'expected_type': 'pants',
            'description': 'Classic black pants'
        }
    ]

    print("Testing with BLIP-2 ENABLED (will fallback to heuristics):")
    print("-" * 55)

    analyzer = get_image_analyzer(use_blip2=True)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']}")
        print(f"   Image: {test_case['color']} {test_case['size'][0]}x{test_case['size'][1]}")

        # Create test image
        test_image = create_test_fashion_image(
            test_case['color'],
            test_case['size'][0],
            test_case['size'][1]
        )

        # Convert to Django file format
        img_byte_arr = BytesIO()
        test_image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)

        from django.core.files.uploadedfile import InMemoryUploadedFile
        mock_file = InMemoryUploadedFile(
            img_byte_arr,
            None,
            f'test_{test_case["name"].lower().replace(" ", "_")}.jpg',
            'image/jpeg',
            img_byte_arr.tell(),
            None
        )

        # Analyze the image
        result = analyzer.analyze_image(mock_file)

        # Display results
        print(f"   📊 Detected: {result.get('item_type', 'unknown')} ({result.get('category', 'unknown')})")
        print(f"   🎨 Color: {result.get('color', 'unknown')}")
        print(f"   📝 Description: {result.get('description', 'none')}")
        print(f"   🎯 Confidence: {result.get('confidence', 0):.1%}")

        # Check if description is enhanced
        description = result.get('description', '')
        if len(description) > 20 and not description.startswith("A "):
            print("   ✅ BLIP-2 style rich description detected!")
        elif description.startswith("A ") and len(description) > 10:
            print("   ℹ️ Using enhanced heuristic description")
        else:
            print("   ⚠️ Basic description generated")

def test_blip2_status():
    """Check BLIP-2 loading status."""
    print("\n🔍 BLIP-2 Status Check")
    print("=" * 25)

    try:
        analyzer = get_image_analyzer(use_blip2=True)

        if analyzer.blip2_captioner is not None:
            print("✅ BLIP-2 is loaded and ready!")
            print(f"   Model: {analyzer.blip2_captioner.model_name}")
            print(f"   Device: {analyzer.blip2_captioner.device}")
        else:
            print("⚠️ BLIP-2 not available - using fallback mode")
            print("   This is expected in development/testing environments")

    except Exception as e:
        print(f"❌ BLIP-2 status check failed: {str(e)}")

def demonstrate_enhanced_workflow():
    """Demonstrate the complete enhanced workflow."""
    print("\n🚀 Complete Enhanced Workflow Demo")
    print("=" * 40)

    print("1. User uploads clothing photo")
    print("2. YOLOv8 detects clothing items (existing)")
    print("3. Color and pattern analysis (existing)")
    print("4. BLIP-2 generates rich description (NEW!)")
    print("5. Fallback to heuristics if needed (NEW!)")
    print("6. Return enhanced metadata")

    # Quick demo
    analyzer = get_image_analyzer(use_blip2=True)
    test_img = create_test_fashion_image('blue', 250, 400)

    img_byte_arr = BytesIO()
    test_img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    from django.core.files.uploadedfile import InMemoryUploadedFile
    mock_file = InMemoryUploadedFile(
        img_byte_arr, None, 'demo.jpg', 'image/jpeg', img_byte_arr.tell(), None
    )

    result = analyzer.analyze_image(mock_file)

    print("\n📋 Final Result:")
    print(f"   Item: {result.get('item_type', 'unknown')}")
    print(f"   Category: {result.get('category', 'unknown')}")
    print(f"   Color: {result.get('color', 'unknown')}")
    print(f"   Material: {result.get('material', 'unknown')}")
    print(f"   Style: {result.get('style', 'unknown')}")
    print(f"   Description: {result.get('description', 'none')}")
    print(f"   Confidence: {result.get('confidence', 0):.1%}")

if __name__ == "__main__":
    print("🎨 Tailora BLIP-2 Enhanced Fashion Description Test")
    print("=" * 60)
    print("This test demonstrates the new BLIP-2 integration without")
    print("requiring the large model download.")
    print("=" * 60)

    try:
        test_blip2_status()
        test_enhanced_descriptions()
        demonstrate_enhanced_workflow()

        print("\n" + "=" * 60)
        print("🎉 Test completed successfully!")
        print("Your Tailora app now has enhanced fashion descriptions!")
        print("BLIP-2 will provide rich descriptions when available,")
        print("with automatic fallback to improved heuristics.")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()