#!/usr/bin/env python3
"""
Hook automatico per generare mappe concettuali quando vengono aggiunti materiali.
Da integrare nell'endpoint di upload materiale.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from services.concept_map_service import ConceptMapService
import structlog

logger = structlog.get_logger()

async def generate_concepts_on_material_upload(course_id: str, course_name: str = None):
    """
    Genera automaticamente mappe concettuali quando vengono caricati nuovi materiali.

    Args:
        course_id: ID del corso
        course_name: Nome opzionale del corso (per fallback personalizzati)
    """

    concept_service = ConceptMapService()

    try:
        # Carica la mappa concettuale esistente
        existing_maps = concept_service._load_concept_maps()
        existing_map = existing_maps["concept_maps"].get(course_id, {})
        existing_concepts = existing_map.get("concepts", [])

        logger.info(f"Auto-generating concepts for course {course_id}")
        logger.info(f"Found {len(existing_concepts)} existing concepts")

        # Se non ci sono concetti esistenti, genera una mappa base
        if len(existing_concepts) == 0:
            logger.info("No existing concepts found, generating base map")

            # Prova a generare con AI
            try:
                new_map = await concept_service.generate_concept_map(
                    course_id=course_id,
                    force=True
                )

                new_concepts = new_map.get("concepts", [])

                if len(new_concepts) > 0:
                    logger.info(f"✓ Generated {len(new_concepts)} concepts with AI")
                    return {"status": "generated", "concepts_count": len(new_concepts)}

            except Exception as e:
                logger.warning(f"AI generation failed: {str(e)}")

            # Fallback: genera concetti base personalizzati
            fallback_map = await generate_base_fallback_map(course_id, course_name or "Course")

            # Salva la mappa fallback
            concept_maps = concept_service._load_concept_maps()
            concept_maps["concept_maps"][course_id] = fallback_map
            concept_service._save_concept_maps(concept_maps)

            logger.info(f"✓ Generated {len(fallback_map['concepts'])} fallback concepts")
            return {"status": "fallback_generated", "concepts_count": len(fallback_map["concepts"])}

        else:
            logger.info(f"Course already has {len(existing_concepts)} concepts, skipping generation")
            return {"status": "existing_found", "concepts_count": len(existing_concepts)}

    except Exception as e:
        logger.error(f"Failed to auto-generate concepts: {str(e)}")
        return {"status": "error", "error": str(e)}

async def generate_base_fallback_map(course_id: str, course_name: str):
    """Genera una mappa concettuale base fallback."""

    # Logica per generare concetti base in base al tipo di corso
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
                "suggested_reading": ["Materiale del corso"],
                "recommended_minutes": 45,
                "quiz_outline": [
                    "Definire i concetti di spazio geografico e territorio",
                    "Spiegare la differenza tra i vari tipi di paesaggio",
                    "Applicare la scala geografica a esempi concreti"
                ]
            }
        ]
    else:
        concepts = [
            {
                "id": "introduzione-corso",
                "name": "Introduzione al Corso",
                "summary": f"Concetti fondamentali e panoramica di {course_name}",
                "chapter": {"title": "Capitolo 1", "index": 1},
                "related_topics": ["concetti base", "terminologia", "obiettivi"],
                "learning_objectives": [
                    "Comprendere gli obiettivi del corso",
                    "Familiarizzare con la terminologia",
                    "Identificare le aree tematiche principali"
                ],
                "suggested_reading": ["Materiale introduttivo"],
                "recommended_minutes": 30,
                "quiz_outline": [
                    "Definire i concetti fondamentali",
                    "Spiegare gli obiettivi del corso"
                ]
            }
        ]

    return {
        "course_id": course_id,
        "generated_at": datetime.now().isoformat(),
        "source_count": 0,
        "is_fallback": True,
        "concepts": concepts
    }

# Funzione da chiamare negli endpoint di upload materiale
async def on_material_uploaded(course_id: str, course_name: str = None):
    """Hook da chiamare dopo l'upload di materiale."""
    result = await generate_concepts_on_material_upload(course_id, course_name)
    logger.info(f"Concept generation hook result: {result}")
    return result

if __name__ == "__main__":
    # Test mode
    if len(sys.argv) > 1:
        course_id = sys.argv[1]
        course_name = sys.argv[2] if len(sys.argv) > 2 else "Test Course"
        asyncio.run(on_material_uploaded(course_id, course_name))
    else:
        print("Usage: python auto_generate_concepts_hook.py <course_id> [course_name]")