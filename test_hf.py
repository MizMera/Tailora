"""
Test Hugging Face Qwen integration
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tailora_project.settings')
django.setup()

from wardrobe.ai_image_analyzer import get_image_analyzer
from PIL import Image
import io

print("=" * 60)
print("Testing Hugging Face Qwen Integration")
print("=" * 60)

# Check environment
hf_token = os.getenv('HF_API_TOKEN')
hf_model = os.getenv('HF_QWEN_MODEL')

print(f"\nHF_API_TOKEN: {'✓ Set (hf_...)' if hf_token and hf_token.startswith('hf_') else '✗ Missing or Invalid'}")
print(f"HF_QWEN_MODEL: {hf_model or '✗ Missing'}")

if not hf_token or hf_token == 'PASTE_YOUR_HF_TOKEN_HERE':
    print("\n❌ Please update .env file with your Hugging Face token!")
    print("   1. Go to: https://huggingface.co/settings/tokens")
    print("   2. Create a new token (Read access)")
    print("   3. Replace 'PASTE_YOUR_HF_TOKEN_HERE' in .env with your token")
    sys.exit(1)

# Get analyzer
print("\nInitializing analyzer...")
analyzer = get_image_analyzer()
print(f"Analyzer type: {type(analyzer).__name__}")

if type(analyzer).__name__ == 'HuggingFaceQwenImageAnalyzer':
    print("✅ Hugging Face Qwen activated!")
    print("\nℹ️  Note: First request may take 20-30 seconds")
    print("   (HF models 'wake up' from sleep state)")
else:
    print(f"⚠️  Using: {type(analyzer).__name__}")

print("\n" + "=" * 60)
