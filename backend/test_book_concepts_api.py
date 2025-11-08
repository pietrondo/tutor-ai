#!/usr/bin/env python3
"""
Script per testare le book concept maps API
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.concept_map_service import ConceptMapService

def test_book_concepts_api():
    try:
        service = ConceptMapService()

        # Load concept maps
        maps = service._load_concept_maps()
        course_id = "90a903c0-4ef6-4415-ae3b-9dbc70ad69a9"

        if course_id in maps["concept_maps"]:
            course_data = maps["concept_maps"][course_id]

            print("🔍 Testing book concept maps structure...")
            print(f"✅ Course: {course_data.get('course_name', 'N/A')}")

            if "books" in course_data:
                print(f"📚 Books found: {len(course_data['books'])}")

                for book_id, book_data in course_data["books"].items():
                    title = book_data.get('book_title', 'Unknown')
                    concepts = book_data.get('concepts', [])

                    print(f"\n📖 Book: {title}")
                    print(f"   Book ID: {book_id}")
                    print(f"   Concepts: {len(concepts)}")

                    for i, concept in enumerate(concepts):
                        print(f"   {i+1}. {concept.get('name', 'N/A')}")
                        print(f"      Summary: {concept.get('summary', 'N/A')[:100]}...")
                        print(f"      Learning objectives: {len(concept.get('learning_objectives', []))}")

                print(f"\n✅ All book concept maps loaded successfully!")
                print(f"📊 Total books with concepts: {len(course_data['books'])}")

                # Test data structure for frontend
                print(f"\n🔧 Testing frontend data format...")

                # Simulate what frontend would receive
                frontend_data = {
                    "success": True,
                    "book_concepts": course_data["books"]
                }

                print(f"✅ Frontend can receive {len(frontend_data['book_concepts'])} books")
                return True

            else:
                print("❌ No books structure found in concept maps")
                return False
        else:
            print("❌ Course not found")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_book_concepts_api()
    if success:
        print("\n🎯 Ready for frontend integration!")
    else:
        print("\n❌ Need to fix concept maps structure")