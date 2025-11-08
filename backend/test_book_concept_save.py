#!/usr/bin/env python3
"""
Test script to check book concept map saving
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.concept_map_service import ConceptMapService

def test_book_concept_storage():
    service = ConceptMapService()

    # Load current maps
    maps = service._load_concept_maps()
    print("Current structure:")
    print(json.dumps(maps, indent=2, ensure_ascii=False)[:500] + "...")

    # Check if course exists
    course_id = "90a903c0-4ef6-4415-ae3b-9dbc70ad69a9"
    if course_id in maps["concept_maps"]:
        course_data = maps["concept_maps"][course_id]
        print(f"\nCourse data keys: {list(course_data.keys())}")

        # Check if books structure exists
        if "books" not in course_data:
            print("Creating books structure...")
            course_data["books"] = {}

        # Add a test book concept
        book_id = "test-book-id"
        test_concept = {
            "test": "book concept map",
            "concepts": [{"id": "test", "name": "Test Concept"}]
        }

        course_data["books"][book_id] = test_concept

        # Save
        service._save_concept_maps(maps)
        print("✅ Test book concept saved")

        # Reload and verify
        new_maps = service._load_concept_maps()
        if "books" in new_maps["concept_maps"][course_id]:
            print("✅ Books structure found after save")
            print(f"Book keys: {list(new_maps['concept_maps'][course_id]['books'].keys())}")
        else:
            print("❌ Books structure still missing")
    else:
        print("Course not found")

if __name__ == "__main__":
    test_book_concept_storage()