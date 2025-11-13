"""
Quick test to verify Qwen API integration is working
Run this to check if OpenRouter Qwen responds correctly
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tailora_project.settings')
django.setup()

from wardrobe.ai_image_analyzer import get_image_analyzer
from PIL import Image
import io

def create_test_image():
    """Create a simple test image (blue rectangle - simulating a shirt)"""
    img = Image.new('RGB', (400, 500), color=(70, 130, 180))  # Steel blue
    return img

def test_qwen_integration():
    print("=" * 60)
    print("Testing Qwen API Integration")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. Checking environment variables:")
    qwen_key = os.getenv('QWEN_API_KEY')
    qwen_base = os.getenv('QWEN_API_BASE')
    qwen_model = os.getenv('QWEN_MODEL')
    
    print(f"   QWEN_API_KEY: {'✓ Set' if qwen_key else '✗ Missing'}")
    print(f"   QWEN_API_BASE: {qwen_base if qwen_base else '✗ Missing'}")
    print(f"   QWEN_MODEL: {qwen_model if qwen_model else '✗ Missing'}")
    
    if not (qwen_key and qwen_base):
        print("\n❌ Qwen environment variables not configured!")
        print("   Expected: QWEN_API_KEY and QWEN_API_BASE in .env file")
        return False
    
    # Get analyzer instance
    print("\n2. Initializing image analyzer...")
    try:
        analyzer = get_image_analyzer()
        analyzer_type = type(analyzer).__name__
        print(f"   Analyzer type: {analyzer_type}")
        
        if analyzer_type == 'QwenImageAnalyzer':
            print("   ✓ QwenImageAnalyzer activated!")
        elif analyzer_type == 'HuggingFaceQwenImageAnalyzer':
            print("   ✓ HuggingFaceQwenImageAnalyzer activated!")
        else:
            print(f"   ⚠ Using fallback: {analyzer_type}")
            print("   (Qwen not activated - check env vars)")
    except Exception as e:
        print(f"   ✗ Error initializing analyzer: {e}")
        return False
    
    # Test with a simple image
    print("\n3. Testing with sample image...")
    try:
        test_img = create_test_image()
        
        # Convert to file-like object
        img_io = io.BytesIO()
        test_img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        print("   Analyzing image (this may take 5-10 seconds)...")
        result = analyzer.analyze_image(img_io)
        
        print("\n4. Analysis Results:")
        print(f"   Item Type: {result.get('item_type', 'N/A')}")
        print(f"   Category: {result.get('category', 'N/A')}")
        print(f"   Color: {result.get('color', 'N/A')}")
        print(f"   Material: {result.get('material', 'N/A')}")
        print(f"   Style: {result.get('style', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 0):.0%}")
        print(f"   Description: {result.get('description', 'N/A')}")
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_qwen_integration()
    sys.exit(0 if success else 1)
