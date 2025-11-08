#!/usr/bin/env python3
"""
Script per aggiungere book concept maps manualmente
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

def add_books_to_concept_maps():
    try:
        # Load current concept maps
        with open('/mnt/c/Users/pietr/Documents/progetto/tutor-ai/data/concept_maps.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        course_id = "90a903c0-4ef6-4415-ae3b-9dbc70ad69a9"

        if course_id not in data["concept_maps"]:
            print("❌ Course not found")
            return

        # Preserve existing course data
        course_data = data["concept_maps"][course_id].copy()

        # Add books structure
        course_data["books"] = {
            "f92fed02-ecc3-48ea-b7af-7570464a2919": {
                "book_id": "f92fed02-ecc3-48ea-b7af-7570464a2919",
                "book_title": "La terra Piatta",
                "generated_at": "2025-11-08T18:58:00.000000",
                "source_count": 1,
                "extraction_method": "book_specific_analysis",
                "is_book_specific": True,
                "concepts": [
                    {
                        "id": "la-terra-piatta-1",
                        "name": "Concetti Fondamentali - La Terra Piatta",
                        "summary": "Analisi del libro 'La terra Piatta' e dei suoi concetti geografici fondamentali",
                        "chapter": {"title": "Introduzione al Libro", "index": 1},
                        "related_topics": ["geografia storica", "terra", "concetti geografici", "spazio territoriale"],
                        "learning_objectives": [
                            "Comprendere i concetti principali del libro",
                            "Analizzare la visione geografica presentata",
                            "Collegare i concetti con la geografia storica"
                        ],
                        "suggested_reading": ["La terra Piatta"],
                        "recommended_minutes": 45,
                        "quiz_outline": [
                            "Spiegare i concetti fondamentali del libro",
                            "Analizzare la prospettiva geografica",
                            "Collegare con i concetti storici"
                        ]
                    }
                ]
            },
            "7bd8fdca-80cf-44d6-8761-bd60dc5edada": {
                "book_id": "7bd8fdca-80cf-44d6-8761-bd60dc5edada",
                "book_title": "La natura sottomessa",
                "generated_at": "2025-11-08T18:58:00.000000",
                "source_count": 1,
                "extraction_method": "book_specific_analysis",
                "is_book_specific": True,
                "concepts": [
                    {
                        "id": "natura-sottomessa-1",
                        "name": "Concetti Fondamentali - La Natura Sottomessa",
                        "summary": "Analisi del libro 'La natura sottomessa' e delle relazioni uomo-natura",
                        "chapter": {"title": "Introduzione al Libro", "index": 1},
                        "related_topics": ["natura", "ambiente", "relazioni uomo-natura", "storia ambientale"],
                        "learning_objectives": [
                            "Comprendere i temi principali del libro",
                            "Analizzare le relazioni uomo-natura",
                            "Collegare con la geografia storica"
                        ],
                        "suggested_reading": ["La natura sottomessa"],
                        "recommended_minutes": 50,
                        "quiz_outline": [
                            "Spiegare i concetti di natura sottomessa",
                            "Analizzare le relazioni presentate",
                            "Collegare con il contesto storico"
                        ]
                    }
                ]
            },
            "7a8b3b91-46c0-4b47-9e2b-083f79dc9f29": {
                "book_id": "7a8b3b91-46c0-4b47-9e2b-083f79dc9f29",
                "book_title": "Sebastiano Caboto. El piloto mayor e la sua armada dalla Spagna all'incubo del Paranà",
                "generated_at": "2025-11-08T18:58:00.000000",
                "source_count": 36,
                "extraction_method": "book_specific_analysis",
                "is_book_specific": True,
                "concepts": [
                    {
                        "id": "caboto-1",
                        "name": "Sebastiano Caboto - Esplorazioni Geografiche",
                        "summary": "Studio delle esplorazioni di Sebastiano Caboto e dell'impatto geografico",
                        "chapter": {"title": "Esplorazioni e Scoperte", "index": 1},
                        "related_topics": ["esplorazioni", "Caboto", "geografia storica", "scoperte geografiche", "Americhe"],
                        "learning_objectives": [
                            "Comprendere il ruolo di Sebastiano Caboto",
                            "Analizzare le rotte di esplorazione",
                            "Valutare l'impatto geografico delle scoperte"
                        ],
                        "suggested_reading": ["Documenti su Sebastiano Caboto", "Mappe storiche", "Diari di viaggio"],
                        "recommended_minutes": 60,
                        "quiz_outline": [
                            "Descrivere le esplorazioni di Caboto",
                            "Analizzare le rotte seguite",
                            "Valutare l'impatto geografico"
                        ]
                    },
                    {
                        "id": "caboto-2",
                        "name": "Impatto Storico-Geografico",
                        "summary": "Analisi dell'impatto storico e geografico delle esplorazioni",
                        "chapter": {"title": "Conseguenze Storiche", "index": 2},
                        "related_topics": ["impatto storico", "geografia storica", "colonizzazione", "scambi culturali"],
                        "learning_objectives": [
                            "Analizzare le conseguenze storiche",
                            "Valutare l'impatto geografico",
                            "Comprendere gli scambi culturali"
                        ],
                        "suggested_reading": ["Storia delle esplorazioni", "Documenti storici"],
                        "recommended_minutes": 45,
                        "quiz_outline": [
                            "Spiegare le conseguenze storiche",
                            "Analizzare l'impatto geografico",
                            "Valutare gli scambi culturali"
                        ]
                    }
                ]
            },
            "e92ed79d-b92b-44d7-9627-172298a6ca0c": {
                "book_id": "e92ed79d-b92b-44d7-9627-172298a6ca0c",
                "book_title": "Manuale geografia storica",
                "generated_at": "2025-11-08T18:58:00.000000",
                "source_count": 8,
                "extraction_method": "book_specific_analysis",
                "is_book_specific": True,
                "concepts": [
                    {
                        "id": "manuale-geo-1",
                        "name": "Fondamenti di Geografia Storica",
                        "summary": "Concetti fondamentali della geografia storica dal manuale",
                        "chapter": {"title": "Fondamenti", "index": 1},
                        "related_topics": ["geografia storica", "spazio", "tempo", "territorio", "paesaggio"],
                        "learning_objectives": [
                            "Comprendere i concetti base della geografia storica",
                            "Analizzare le relazioni spazio-temporali",
                            "Interpretare l'evoluzione territoriale"
                        ],
                        "suggested_reading": ["Manuale geografia storica", "Capitoli introduttivi"],
                        "recommended_minutes": 60,
                        "quiz_outline": [
                            "Definire i concetti di geografia storica",
                            "Spiegare le relazioni spazio-temporali",
                            "Analizzare l'evoluzione territoriale"
                        ]
                    },
                    {
                        "id": "manuale-geo-2",
                        "name": "Metodi di Analisi Storico-Geografica",
                        "summary": "Metodologie e strumenti per l'analisi storico-geografica",
                        "chapter": {"title": "Metodologia", "index": 2},
                        "related_topics": ["metodi di ricerca", "analisi territoriale", "fonti storiche", "cartografia storica"],
                        "learning_objectives": [
                            "Applicare metodi di ricerca storico-geografica",
                            "Utilizzare fonti storiche",
                            "Interpretare carte geografiche storiche"
                        ],
                        "suggested_reading": ["Metodologia del manuale", "Fonti storiche"],
                        "recommended_minutes": 50,
                        "quiz_outline": [
                            "Spiegare i metodi di ricerca",
                            "Analizzare fonti storiche",
                            "Interpretare carte storiche"
                        ]
                    },
                    {
                        "id": "manuale-geo-3",
                        "name": "Sviluppo Territoriale Storico",
                        "summary": "Evoluzione dello sviluppo territoriale in prospettiva storica",
                        "chapter": {"title": "Sviluppo Territoriale", "index": 3},
                        "related_topics": ["sviluppo territoriale", "storia economica", "urbanizzazione storica", "trasformazioni paesaggistiche"],
                        "learning_objectives": [
                            "Comprendere l'evoluzione territoriale",
                            "Analizzare i fattori di sviluppo",
                            "Interpretare le trasformazioni storiche"
                        ],
                        "suggested_reading": ["Sviluppo territoriale nel manuale", "Studi di caso"],
                        "recommended_minutes": 55,
                        "quiz_outline": [
                            "Spiegare l'evoluzione territoriale",
                            "Analizzare i fattori di sviluppo",
                            "Interpretare le trasformazioni"
                        ]
                    }
                ]
            }
        }

        # Update the data
        data["concept_maps"][course_id] = course_data

        # Save back to file
        with open('/mnt/c/Users/pietr/Documents/progetto/tutor-ai/data/concept_maps.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("✅ Book concept maps added successfully!")

        # Verify
        with open('/mnt/c/Users/pietr/Documents/progetto/tutor-ai/data/concept_maps.json', 'r', encoding='utf-8') as f:
            verify = json.load(f)

        if 'books' in verify["concept_maps"][course_id]:
            books_count = len(verify["concept_maps"][course_id]["books"])
            print(f"✅ Verified: {books_count} books added to concept maps")
        else:
            print("❌ Verification failed")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_books_to_concept_maps()