"""
Test script to verify language extraction works correctly
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from utils import extract_advice_from_docx

# Test with different languages
print("=" * 60)
print("Testing Language Extraction")
print("=" * 60)

for lang in ['en', 'gu', 'hi']:
    print(f"\n\n{'='*60}")
    print(f"Testing Language: {lang.upper()}")
    print('='*60)
    
    # Test with OCD symptom
    result = extract_advice_from_docx('uploads', 'ocd', lang=lang)
    
    if result:
        for title, sections in result.items():
            print(f"\n>> {title}")
            for section in sections:
                print(f"  -- {section.get('subtitle', 'No subtitle')}")
                content_items = section.get('content', [])
                for i, item in enumerate(content_items[:3]):  # Show first 3 items
                    print(f"     * {item[:80]}...")
                if len(content_items) > 3:
                    print(f"     ... and {len(content_items) - 3} more items")
    else:
        print("  XX No data extracted")

print("\n" + "="*60)
print("Test Complete!")
print("="*60)
