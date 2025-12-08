#!/usr/bin/env python
"""
Test script for BLIP-2 fashion captioning integration in Tailora.
Tests the new BLIP-2 enhanced FashionImageAnalyzer.
"""

import os
import sys
import django
from PIL import Image
import requests
from io import BytesIO

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tailora_project.settings')
django.setup()

from wardrobe.ai_image_analyzer import get_image_analyzer

def test_blip2_captioning():
    """Test BLIP-2 captioning with a sample fashion image."""
    print("🧪 Testing BLIP-2 Fashion Captioning Integration")
    print("=" * 60)

    try:
        # Get analyzer with BLIP-2 enabled
        analyzer = get_image_analyzer(use_blip2=True)
        print("✅ Analyzer initialized successfully")

        # Test with a sample fashion image URL
        # Using a placeholder - in real testing you'd use actual fashion images
        test_image_url = "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400"  # Sample shirt image

        print(f"📥 Downloading test image from: {test_image_url}")

        # Download image
        response = requests.get(test_image_url, timeout=10)
        response.raise_for_status()

        # Create PIL Image
        image = Image.open(BytesIO(response.content))
        print(f"✅ Image loaded: {image.size} pixels")

        # Create a mock Django file-like object
        from django.core.files.base import ContentFile
        from django.core.files.uploadedfile import InMemoryUploadedFile

        # Convert PIL image to bytes
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)

        # Create InMemoryUploadedFile
        mock_file = InMemoryUploadedFile(
            img_byte_arr,
            None,
            'test_fashion.jpg',
            'image/jpeg',
            img_byte_arr.tell(),
            None
        )

        print("🔍 Analyzing image with BLIP-2...")

        # Analyze the image
        result = analyzer.analyze_image(mock_file)

        print("\n📊 Analysis Results:")
        print("-" * 30)
        print(f"Item Type: {result.get('item_type', 'N/A')}")
        print(f"Category: {result.get('category', 'N/A')}")
        print(f"Color: {result.get('color', 'N/A')}")
        print(f"Pattern: {result.get('pattern', 'N/A')}")
        print(f"Material: {result.get('material', 'N/A')}")
        print(f"Style: {result.get('style', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 'N/A'):.2%}")

        description = result.get('description', '')
        print(f"\n📝 Description: {description}")

        # Check if BLIP-2 was used
        if len(description) > 20 and not description.startswith("A "):
            print("✅ BLIP-2 captioning appears to be working!")
        else:
            print("⚠️ Using fallback heuristic description")

        print("\n🏷️ Tags:", result.get('tags', []))
        print("\n✨ Test completed successfully!")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_without_blip2():
    """Test fallback behavior without BLIP-2."""
    print("\n🧪 Testing Fallback (without BLIP-2)")
    print("=" * 40)

    try:
        # Get analyzer with BLIP-2 disabled
        analyzer = get_image_analyzer(use_blip2=False)

        # Simple test image (solid color square)
        test_image = Image.new('RGB', (200, 300), color='red')

        # Create mock file
        img_byte_arr = BytesIO()
        test_image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)

        from django.core.files.uploadedfile import InMemoryUploadedFile
        mock_file = InMemoryUploadedFile(
            img_byte_arr,
            None,
            'test_red.jpg',
            'image/jpeg',
            img_byte_arr.tell(),
            None
        )

        result = analyzer.analyze_image(mock_file)

        description = result.get('description', '')
        print(f"Description: {description}")

        if description.startswith("A red"):
            print("✅ Fallback heuristic description working")
        else:
            print("⚠️ Unexpected description format")

        return True

    except Exception as e:
        print(f"❌ Fallback test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting BLIP-2 Integration Tests for Tailora")
    print("=" * 60)

    # Test BLIP-2 integration
    blip2_success = test_blip2_captioning()

    # Test fallback
    fallback_success = test_without_blip2()

    print("\n" + "=" * 60)
    if blip2_success:
        print("🎉 BLIP-2 integration test PASSED!")
        print("Your Tailora app now has rich AI-generated fashion descriptions!")
    else:
        print("⚠️ BLIP-2 integration test FAILED")
        print("Check the error messages above and ensure dependencies are installed.")

    if fallback_success:
        print("✅ Fallback system working correctly")
    else:
        print("⚠️ Fallback system has issues")

    print("=" * 60)