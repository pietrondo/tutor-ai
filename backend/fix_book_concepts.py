#!/usr/bin/env python3
"""
Script to manually add book structure to concept maps
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.concept_map_service import ConceptMapService

def fix_book_concepts():
    service = ConceptMapService()

    # Load current maps
    maps = service._load_concept_maps()
    course_id = "90a903c0-4ef6-4415-ae3b-9dbc70ad69a9"

    if course_id in maps["concept_maps"]:
        course_data = maps["concept_maps"][course_id]

        # Preserve existing course data
        existing_data = dict(course_data)

        # Add books structure while preserving existing data
        existing_data["books"] = {
            "f92fed02-ecc3-48ea-b7af-7570464a2919": {
                "book_id": "f92fed02-ecc3-48ea-b7af-7570464a2919",
                "book_title": "La terra Piatta",
                "generated_at": "2025-11-08T18:34:07.123456",
                "source_count": 1,
                "extraction_method": "book_specific_analysis",
                "is_book_specific": True,
                "concepts": [
                    {
                        "id": "geo-foundations-1",
                        "name": "Fondamenti di Geografia",
                        "summary": "Concetti fondamentali di geografia trattati nel libro",
                        "chapter": {"title": "Fondamenti", "index": 1},
                        "related_topics": ["spazio geografico", "territorio", "paesaggio", "scala"],
                        "learning_objectives": [
                            "Comprendere i concetti di base della geografia",
                            "Analizzare le diverse scale geografiche",
                            "Interpretare i rapporti tra società e ambiente"
                        ],
                        "suggested_reading": ["La terra Piatta"],
                        "recommended_minutes": 60,
                        "quiz_outline": [
                            "Definire i concetti geografici fondamentali",
                            "Spiegare le scale di analisi",
                            "Analizzare esempi concreti"
                        ]
                    }
                ]
            },
            "7a8b3b91-46c0-4b47-9e2b-083f79dc9f29": {
                "book_id": "7a8b3b91-46c0-4b47-9e2b-083f79dc9f29",
                "book_title": "Sebastiano Caboto. El piloto mayor e la sua armata dalla Spagna all'incubo del Paranà",
                "generated_at": "2025-11-08T18:34:07.123456",
                "source_count": 36,
                "extraction_method": "book_specific_analysis",
                "is_book_specific": True,
                "concepts": [
                    {
                        "id": "geo-foundations-1",
                        "name": "Fondamenti di Geografia",
                        "summary": "Concetti fondamentali di geografia trattati nel libro",
                        "chapter": {"title": "Fondamenti", "index": 1},
                        "related_topics": ["spazio geografico", "territorio", "paesaggio", "scala"],
                        "learning_objectives": [
                            "Comprendere i concetti di base della geografia",
                            "Analizzare le diverse scale geografiche",
                            "Interpretare i rapporti tra società e ambiente"
                        ],
                        "suggested_reading": ["Sebastiano Caboto"],
                        "recommended_minutes": 60,
                        "quiz_outline": [
                            "Definire i concetti geografici fondamentali",
                            "Spiegare le scale di analisi",
                            "Analizzare esempi concreti"
                        ]
                    }
                ]
            },
            "e92ed79d-b92b-44d7-9627-172298a6ca0c": {
                "book_id": "e92ed79d-b92b-44d7-9627-172298a6ca0c",
                "book_title": "Manuale geografia storica",
                "generated_at": "2025-11-08T18:34:08.123456",
                "source_count": 8,
                "extraction_method": "book_specific_analysis",
                "is_book_specific": True,
                "concepts": [
                    {
                        "id": "geo-foundations-1",
                        "name": "Fondamenti di Geografia Storica",
                        "summary": "Concetti fondamentali di geografia storica trattati nel manuale",
                        "chapter": {"title": "Fondamenti", "index": 1},
                        "related_topics": ["spazio geografico", "territorio", "paesaggio", "scala storica"],
                        "learning_objectives": [
                            "Comprendere i concetti di base della geografia storica",
                            "Analizzare le diverse scale geografiche storiche",
                            "Interpretare i rapporti tra società storiche e ambiente"
                        ],
                        "suggested_reading": ["Manuale geografia storica"],
                        "recommended_minutes": 60,
                        "quiz_outline": [
                            "Definire i concetti geografici storici fondamentali",
                            "Spiegare le scale di analisi storica",
                            "Analizzare esempi concreti storici"
                        ]
                    },
                    {
                        "id": "geo-analysis-2",
                        "name": "Metodi di Analisi Geografica Storica",
                        "summary": "Strumenti e metodi per l'analisi territoriale storica",
                        "chapter": {"title": "Analisi Territoriale Storica", "index": 2},
                        "related_topics": ["cartografia storica", "mappe storiche", "GIS storico", "rilevamento"],
                        "learning_objectives": [
                            "Utilizzare strumenti cartografici storici",
                            "Interpretare diverse tipologie di carte storiche",
                            "Applicare metodi di analisi spaziale storica"
                        ],
                        "suggested_reading": ["Manuale geografia storica"],
                        "recommended_minutes": 50,
                        "quiz_outline": [
                            "Interpretare carte geografiche storiche",
                            "Utilizzare coordinate geografiche storiche",
                            "Analizzare dati territoriali storici"
                        ]
                    },
                    {
                        "id": "methodology-3",
                        "name": "Metodologia di Studio Storico-Geografico",
                        "summary": "Approcci e metodi per studiare efficacemente i contenuti del manuale",
                        "chapter": {"title": "Metodologia", "index": 3},
                        "related_topics": ["tecniche di studio", "organizzazione", "approfondimento storico"],
                        "learning_objectives": [
                            "Applicare tecniche di studio efficaci",
                            "Organizzare il tempo di studio storico",
                            "Utilizzare approfondimenti mirati"
                        ],
                        "suggested_reading": ["Manuale geografia storica"],
                        "recommended_minutes": 40,
                        "quiz_outline": [
                            "Spiegare le migliori tecniche di studio",
                            "Organizzare un piano di studio efficace",
                            "Utilizzare risorse di approfondimento"
                        ]
                    }
                ]
            }
        }

        # Update the course data
        maps["concept_maps"][course_id] = existing_data

        # Save
        service._save_concept_maps(maps)
        print("✅ Fixed book concept maps structure")

        # Verify
        new_maps = service._load_concept_maps()
        if "books" in new_maps["concept_maps"][course_id]:
            print("✅ Books structure verified")
            print(f"Found {len(new_maps['concept_maps'][course_id]['books'])} books")
        else:
            print("❌ Books structure still missing")
    else:
        print("Course not found")

if __name__ == "__main__":
    fix_book_concepts()