#!/usr/bin/env python3
"""
Script per rigenerare automaticamente le mappe concettuali per tutti i corsi esistenti.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.concept_map_service import ConceptMapService
from services.llm_service import LLMService
import structlog

logger = structlog.get_logger()

async def regenerate_all_concept_maps():
    """Rigenera le mappe concettuali per tutti i corsi esistenti."""

    # Initialize services
    concept_service = ConceptMapService()

    # Load courses
    courses_paths = [
        "data/courses/courses.json",
        "../data/courses/courses.json",
        "/mnt/c/Users/pietr/Documents/progetto/tutor-ai/data/courses/courses.json"
    ]

    courses = []
    for path in courses_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                courses = json.load(f)
                logger.info(f"Caricati corsi da: {path}")
                break
        except FileNotFoundError:
            continue

    if not courses:
        logger.error("File corsi non trovato in nessun percorso")
        return

    logger.info(f"Found {len(courses)} courses to process")

    results = []

    for course in courses:
        course_id = course["id"]
        course_name = course["name"]

        logger.info(f"Processing course: {course_name} (ID: {course_id})")

        try:
            # Generate concept map with force=True to override existing
            concept_map = await concept_service.generate_concept_map(
                course_id=course_id,
                force=True
            )

            result = {
                "course_id": course_id,
                "course_name": course_name,
                "status": "success",
                "concepts_count": len(concept_map.get("concepts", [])),
                "generated_at": datetime.now().isoformat()
            }

            logger.info(f"✓ Generated {result['concepts_count']} concepts for {course_name}")
            results.append(result)

        except Exception as e:
            logger.error(f"✗ Failed to generate concept map for {course_name}: {str(e)}")
            result = {
                "course_id": course_id,
                "course_name": course_name,
                "status": "error",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
            results.append(result)

    # Save results
    results_file = f"data/concept_regeneration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "regeneration_timestamp": datetime.now().isoformat(),
            "total_courses": len(courses),
            "results": results
        }, f, ensure_ascii=False, indent=2)

    # Print summary
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful

    print(f"\n{'='*60}")
    print(f"RIEPILOGO RIGENERAZIONE MAPPE CONCETTUALI")
    print(f"{'='*60}")
    print(f"Corsi totali processati: {len(courses)}")
    print(f"Completati con successo: {successful}")
    print(f"Falliti: {failed}")
    print(f"Risultati salvati in: {results_file}")

    if failed > 0:
        print(f"\nCorsi con errori:")
        for result in results:
            if result["status"] == "error":
                print(f"  - {result['course_name']}: {result.get('error', 'Unknown error')}")

    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(regenerate_all_concept_maps())