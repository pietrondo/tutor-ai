#!/usr/bin/env python3
"""
Test script per verificare la generazione di slide con ZAI
"""

import requests
import json

def test_zai_slides():
    """Test the ZAI slides generation endpoint"""
    url = "http://localhost:8000/generate-slides/zai-agent"

    payload = {
        "course_id": "test_course",
        "topic": "Introduzione alla geografia storica",
        "num_slides": 3,
        "slide_style": "modern",
        "audience": "university"
    }

    try:
        print("🚀 Testing ZAI slides generation...")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )

        print(f"\n📊 Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success!")
            print(f"Response keys: {list(result.keys())}")

            if 'slides_data' in result:
                slides_data = result['slides_data']
                print(f"Title: {slides_data.get('title', 'N/A')}")
                print(f"Number of slides: {len(slides_data.get('slides', []))}")

                for i, slide in enumerate(slides_data.get('slides', [])):
                    print(f"\n  Slide {i+1}:")
                    print(f"    Title: {slide.get('title', 'N/A')}")
                    print(f"    Type: {slide.get('type', 'N/A')}")
                    print(f"    Content length: {len(str(slide.get('content', [])))}")
                    if slide.get('content'):
                        print(f"    Content preview: {str(slide['content'])[:100]}...")

            if 'metadata' in result:
                metadata = result['metadata']
                print(f"\n📋 Metadata:")
                for key, value in metadata.items():
                    print(f"  {key}: {value}")
        else:
            print(f"\n❌ Error!")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("\n⏰ Request timed out (60s)")
    except requests.exceptions.ConnectionError:
        print("\n🔌 Connection error - is the backend running?")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

if __name__ == "__main__":
    test_zai_slides()