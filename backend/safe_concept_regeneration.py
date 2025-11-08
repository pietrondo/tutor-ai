#!/usr/bin/env python3
"""
Script sicuro per rigenerare mappe concettuali preservando i contenuti esistenti.
"""

import asyncio
import json
import sys
import requests
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.concept_map_service import ConceptMapService
import structlog

logger = structlog.get_logger()

async def safe_regenerate_all_concept_maps():
    """Rigenera le mappe concettuali in modo sicuro, preservando i contenuti esistenti."""

    # Initialize services
    concept_service = ConceptMapService()

    # Load courses
    try:
        with open("data/courses/courses.json", "r", encoding="utf-8") as f:
            courses = json.load(f)
    except FileNotFoundError:
        logger.error("File corsi non trovato")
        return

    logger.info(f"Found {len(courses)} courses to process")
    results = []

    for course in courses:
        course_id = course["id"]
        course_name = course["name"]

        logger.info(f"Processing course: {course_name} (ID: {course_id})")

        try:
            # Carica la mappa concettuale esistente
            existing_map = concept_service._load_concept_maps()["concept_maps"].get(course_id, {})
            existing_concepts = existing_map.get("concepts", [])

            logger.info(f"Found {len(existing_concepts)} existing concepts for {course_name}")

            # Prova a generare una nuova mappa
            new_map = await concept_service.generate_concept_map(
                course_id=course_id,
                force=True
            )

            new_concepts = new_map.get("concepts", [])

            if len(new_concepts) == 0 and len(existing_concepts) > 0:
                # La nuova generazione ha fallito, mantieni i concetti esistenti ma aggiorna metadata
                logger.warning(f"New generation failed, preserving {len(existing_concepts)} existing concepts")

                enhanced_map = {
                    "course_id": course_id,
                    "generated_at": datetime.now().isoformat(),
                    "source_count": existing_map.get("source_count", 0),
                    "is_fallback": True,
                    "concepts": enhance_existing_concepts(existing_concepts, course_name, course_id)
                }

                # Salva la mappa migliorata
                concept_maps = concept_service._load_concept_maps()
                concept_maps["concept_maps"][course_id] = enhanced_map
                concept_service._save_concept_maps(concept_maps)

                result = {
                    "course_id": course_id,
                    "course_name": course_name,
                    "status": "preserved_and_enhanced",
                    "concepts_count": len(enhanced_map["concepts"]),
                    "generated_at": datetime.now().isoformat(),
                    "note": "Preserved existing concepts due to AI generation failure"
                }

            elif len(new_concepts) > 0:
                # La nuova generazione ha successo
                logger.info(f"✓ Generated {len(new_concepts)} new concepts for {course_name}")
                result = {
                    "course_id": course_id,
                    "course_name": course_name,
                    "status": "regenerated",
                    "concepts_count": len(new_concepts),
                    "generated_at": datetime.now().isoformat()
                }

            else:
                # Non c'erano concetti prima e non sono stati generati
                logger.info(f"No concepts existed before, generating fallback for {course_name}")
                fallback_map = await generate_fallback_concept_map(course_id, course_name, concept_service)

                concept_maps = concept_service._load_concept_maps()
                concept_maps["concept_maps"][course_id] = fallback_map
                concept_service._save_concept_maps(concept_maps)

                result = {
                    "course_id": course_id,
                    "course_name": course_name,
                    "status": "fallback_generated",
                    "concepts_count": len(fallback_map.get("concepts", [])),
                    "generated_at": datetime.now().isoformat()
                }

            results.append(result)

        except Exception as e:
            logger.error(f"✗ Failed to process {course_name}: {str(e)}")
            result = {
                "course_id": course_id,
                "course_name": course_name,
                "status": "error",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
            results.append(result)

    # Save results
    results_file = f"data/safe_concept_regeneration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "regeneration_timestamp": datetime.now().isoformat(),
            "total_courses": len(courses),
            "results": results
        }, f, ensure_ascii=False, indent=2)

    # Print summary
    successful = sum(1 for r in results if r["status"] in ["regenerated", "preserved_and_enhanced", "fallback_generated"])
    failed = len(results) - successful

    print(f"\n{'='*60}")
    print(f"RIEPILOGO RIGENERAZIONE SICURA MAPPE CONCETTUALI")
    print(f"{'='*60}")
    print(f"Corsi totali processati: {len(courses)}")
    print(f"Completati con successo: {successful}")
    print(f"Falliti: {failed}")
    print(f"Risultati salvati in: {results_file}")

    # Status breakdown
    status_counts = {}
    for result in results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"\nBreakdown stati:")
    for status, count in status_counts.items():
        print(f"  - {status}: {count}")

    if failed > 0:
        print(f"\nCorsi con errori:")
        for result in results:
            if result["status"] == "error":
                print(f"  - {result['course_name']}: {result.get('error', 'Unknown error')}")

    print(f"{'='*60}")

def enhance_existing_concepts(existing_concepts, course_name, course_id):
    """Migliora i concetti esistenti con metadata aggiuntivi."""

    # Ottieni i libri del corso per suggerimenti di lettura personalizzati
    try:
        response = requests.get(f"http://localhost:8001/courses/{course_id}/books")
        if response.status_code == 200:
            books_data = response.json()
            books = books_data.get("books", [])
            book_titles = [book.get("title", "") for book in books if book.get("title")]
        else:
            book_titles = []
    except:
        book_titles = []

    enhanced_concepts = []

    for i, concept in enumerate(existing_concepts):
        enhanced_concept = concept.copy()

        # Aggiungi metadata mancanti
        if "recommended_minutes" not in enhanced_concept:
            enhanced_concept["recommended_minutes"] = 30 + (i * 15)  # 30, 45, 60, 75, 90...

        if "suggested_reading" not in enhanced_concept or not enhanced_concept["suggested_reading"]:
            # Assegna libri disponibili in modo round-robin
            if book_titles:
                book_index = i % len(book_titles)
                enhanced_concept["suggested_reading"] = [book_titles[book_index]]
            else:
                enhanced_concept["suggested_reading"] = [f"Materiale per {enhanced_concept.get('name', 'concetto')}"]

        # Aggiungi approfondimenti per geografia
        if "geografia" in course_name.lower():
            if enhanced_concept["id"] == "introduzione":
                enhanced_concept["related_topics"] = ["spazio geografico", "territorio", "paesaggio", "scala geografica"]
                enhanced_concept["learning_objectives"] = [
                    "Comprendere i concetti fondamentali di spazio e territorio",
                    "Distinguere tra i diversi tipi di paesaggi",
                    "Applicare il concetto di scala geografica"
                ]
            elif enhanced_concept["id"] == "concetti-fondamentali":
                enhanced_concept["related_topics"] = ["geografia fisica", "geografia umana", "analisi territoriale", "cartografia"]
                enhanced_concept["learning_objectives"] = [
                    "Distinguere tra geografia fisica e umana",
                    "Applicare metodi di analisi territoriale",
                    "Utilizzare strumenti cartografici base"
                ]

        enhanced_concepts.append(enhanced_concept)

    return enhanced_concepts

async def generate_fallback_concept_map(course_id, course_name, concept_service):
    """Genera una mappa concettuale fallback personalizzata."""

    # Controlla se ci sono libri per suggerimenti
    try:
        response = requests.get(f"http://localhost:8001/courses/{course_id}/books")
        if response.status_code == 200:
            books_data = response.json()
            books = books_data.get("books", [])
            book_titles = [book.get("title", "") for book in books if book.get("title")]
        else:
            book_titles = []
    except:
        book_titles = []

    # Genera concetti base in base al tipo di corso
    if "geografia" in course_name.lower():
        concepts = [
            {
                "id": "concetti-geografici-base",
                "name": "Concetti Geografici Fondamentali",
                "summary": "Introduzione ai principi base della geografia e dell'analisi territoriale",
                "chapter": {"title": "Capitolo 1", "index": 1},
                "related_topics": ["spazio geografico", "territorio", "paesaggio", "ambiente"],
                "learning_objectives": [
                    "Comprendere i concetti fondamentali di spazio e territorio",
                    "Analizzare i diversi tipi di paesaggi",
                    "Applicare il concetto di scala geografica"
                ],
                "suggested_reading": book_titles[:2] if book_titles else ["Manuale di geografia"],
                "recommended_minutes": 45,
                "quiz_outline": [
                    "Definire i concetti di spazio geografico e territorio",
                    "Spiegare la differenza tra i vari tipi di paesaggio",
                    "Applicare la scala geografica a esempi concreti"
                ]
            },
            {
                "id": "metodi-geografici",
                "name": "Metodi e Strumenti della Geografia",
                "summary": "Tecniche di analisi geografica e strumenti per lo studio del territorio",
                "chapter": {"title": "Capitolo 2", "index": 2},
                "related_topics": ["cartografia", "GIS", "analisi territoriale", "rilevamento"],
                "learning_objectives": [
                    "Utilizzare strumenti cartografici base",
                    "Applicare tecniche di analisi territoriale",
                    "Interpretare dati geografici"
                ],
                "suggested_reading": book_titles[2:4] if len(book_titles) > 2 else book_titles[:2],
                "recommended_minutes": 50,
                "quiz_outline": [
                    "Interpretare una carta geografica",
                    "Applicare metodi di analisi territoriale",
                    "Analizzare dati geografici spaziali"
                ]
            }
        ]
    else:
        # Concetti generici per altri tipi di corso
        concepts = [
            {
                "id": "introduzione-materia",
                "name": "Introduzione alla Materia",
                "summary": f"Concetti fondamentali e panoramica di {course_name}",
                "chapter": {"title": "Capitolo 1", "index": 1},
                "related_topics": ["concetti base", "terminologia", "obiettivi del corso"],
                "learning_objectives": [
                    "Comprendere gli obiettivi principali del corso",
                    "Familiarizzare con la terminologia di base",
                    "Identificare le aree tematiche principali"
                ],
                "suggested_reading": book_titles[:2] if book_titles else ["Materiale introduttivo"],
                "recommended_minutes": 30,
                "quiz_outline": [
                    "Definire i concetti fondamentali della materia",
                    "Spiegare gli obiettivi del corso"
                ]
            }
        ]

    return {
        "course_id": course_id,
        "generated_at": datetime.now().isoformat(),
        "source_count": len(book_titles),
        "is_fallback": True,
        "concepts": concepts
    }

if __name__ == "__main__":
    asyncio.run(safe_regenerate_all_concept_maps())