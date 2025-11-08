#!/usr/bin/env python3
"""
Script migliorato per processare materiali e generare mappe concettuali per tutti i corsi.
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
from services.rag_service import RAGService
from services.llm_service import LLMService
import structlog

logger = structlog.get_logger()

class MaterialProcessor:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.concept_service = ConceptMapService()

    async def process_all_courses(self):
        """Processa tutti i corsi: prima indicizza i materiali, poi genera mappe concettuali."""

        # Carica corsi
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
                # 1. Indicizza materiali esistenti
                await self.index_course_materials(course_id, course_name)

                # 2. Genera mappa concettuale
                concept_map = await self.generate_concept_map_with_content(course_id, course_name)

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
        results_file = f"data/materials_concepts_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({
                "processing_timestamp": datetime.now().isoformat(),
                "total_courses": len(courses),
                "results": results
            }, f, ensure_ascii=False, indent=2)

        # Print summary
        successful = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - successful

        print(f"\n{'='*60}")
        print(f"RIEPILOGO PROCESSAMENTO MATERIALI E MAPPE CONCETTUALI")
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

    async def index_course_materials(self, course_id: str, course_name: str):
        """Indicizza tutti i materiali di un corso nel RAG."""
        logger.info(f"Indexing materials for course: {course_name}")

        try:
            # Chiama l'endpoint di indicizzazione materiale
            response = requests.post(
                f"{self.base_url}/courses/{course_id}/index-materials",
                timeout=300  # 5 minuti per indicizzazione
            )

            if response.status_code == 200:
                result = response.json()
                indexed_count = result.get("indexed_count", 0)
                logger.info(f"✓ Indexed {indexed_count} materials for {course_name}")
            else:
                logger.warning(f"Failed to index materials: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not index materials for {course_name}: {str(e)}")

    async def generate_concept_map_with_content(self, course_id: str, course_name: str):
        """Genera mappa concettuale forzando l'uso dei contenuti indicizzati."""
        logger.info(f"Generating concept map for: {course_name}")

        # Forza la rigenerazione con i contenuti indicizzati
        concept_map = await self.concept_service.generate_concept_map(
            course_id=course_id,
            force=True
        )

        # Se la mappa è vuota, genera una fallback personalizzata
        if not concept_map.get("concepts"):
            logger.warning(f"Empty concept map for {course_name}, generating personalized fallback")
            concept_map = await self.generate_personalized_fallback(course_id, course_name)

        return concept_map

    async def generate_personalized_fallback(self, course_id: str, course_name: str):
        """Genera una mappa concettuale fallback basata sul nome del corso e sui libri."""

        # Ottieni i libri del corso
        try:
            response = requests.get(f"{self.base_url}/courses/{course_id}/books")
            if response.status_code == 200:
                books_data = response.json()
                books = books_data.get("books", [])
                book_titles = [book.get("title", "") for book in books]
            else:
                book_titles = []
        except:
            book_titles = []

        # Genera concetti personalizzati basati sul corso
        if "geografia" in course_name.lower():
            concepts = self.generate_geography_concepts(course_name, book_titles)
        elif "storia" in course_name.lower():
            concepts = self.generate_history_concepts(course_name, book_titles)
        elif "matematica" in course_name.lower():
            concepts = self.generate_math_concepts(course_name, book_titles)
        else:
            concepts = self.generate_generic_concepts(course_name, book_titles)

        return {
            "course_id": course_id,
            "generated_at": datetime.now().isoformat(),
            "source_count": len(book_titles),
            "is_fallback": True,
            "concepts": concepts
        }

    def generate_geography_concepts(self, course_name: str, book_titles: list):
        """Genera concetti per corsi di geografia."""
        return [
            {
                "id": "concetti-geografici-fondamentali",
                "name": "Concetti Geografici Fondamentali",
                "summary": "Introduzione ai principi base della geografia e della geografia storica",
                "chapter": {"title": "Capitolo 1", "index": 1},
                "related_topics": ["spazio geografico", "territorio", "paesaggio", "scala geografica"],
                "learning_objectives": [
                    "Comprendere i concetti fondamentali di spazio e territorio",
                    "Distinguere tra i diversi tipi di paesaggi",
                    "Applicare il concetto di scala geografica"
                ],
                "suggested_reading": book_titles[:2] if book_titles else ["Manuale di geografia"],
                "recommended_minutes": 45,
                "quiz_outline": [
                    "Definire il concetto di spazio geografico",
                    "Spiegare la differenza tra territorio e paesaggio",
                    "Applicare la scala geografica a un caso reale"
                ]
            },
            {
                "id": "geografia-storica-evoluzione",
                "name": "Evoluzione Storica del Territorio",
                "summary": "Analisi dei cambiamenti territoriali nel tempo e le loro cause",
                "chapter": {"title": "Capitolo 2", "index": 2},
                "related_topics": ["cambiamento ambientale", "insediamenti umani", "trasformazioni economiche"],
                "learning_objectives": [
                    "Analizzare l'evoluzione dei paesaggi nel tempo",
                    "Comprendere le cause delle trasformazioni territoriali",
                    "Valutare l'impatto umano sull'ambiente"
                ],
                "suggested_reading": book_titles[2:4] if len(book_titles) > 2 else book_titles[:2],
                "recommended_minutes": 60,
                "quiz_outline": [
                    "Descrivere le principali fasi di evoluzione territoriale",
                    "Analizzare le relazioni tra uomo e ambiente",
                    "Valutare gli impatti delle trasformazioni storiche"
                ]
            },
            {
                "id": "metodi-di-analisi-geografica",
                "name": "Metodi di Analisi Geografica",
                "summary": "Strumenti e tecniche per lo studio del territorio",
                "chapter": {"title": "Capitolo 3", "index": 3},
                "related_topics": ["cartografia", "GIS", "analisi territoriale", "fonti storiche"],
                "learning_objectives": [
                    "Utilizzare strumenti cartografici",
                    "Applicare tecniche di analisi territoriale",
                    "Integrare fonti storiche e geografiche"
                ],
                "suggested_reading": ["Testi di cartografia e analisi territoriale"],
                "recommended_minutes": 50,
                "quiz_outline": [
                    "Interpretare carte geografiche storiche",
                    "Applicare metodi di analisi territoriale",
                    "Integrare diverse fonti informative"
                ]
            }
        ]

    def generate_history_concepts(self, course_name: str, book_titles: list):
        """Genera concetti per corsi di storia."""
        return [
            {
                "id": "metodologia-storica",
                "name": "Metodologia della Ricerca Storica",
                "summary": "Fonti, metodi e strumenti per lo studio del passato",
                "chapter": {"title": "Capitolo 1", "index": 1},
                "related_topics": ["fonti primarie", "fonti secondarie", "critica storica", "periodizzazione"],
                "learning_objectives": [
                    "Distinguere tra tipi di fonti storiche",
                    "Applicare metodi di critica storica",
                    "Comprendere i criteri di periodizzazione"
                ],
                "suggested_reading": book_titles[:2] if book_titles else ["Manuale di metodologia storica"],
                "recommended_minutes": 45,
                "quiz_outline": [
                    "Classificare fonti storiche",
                    "Applicare la critica storica",
                    "Giustificare periodizzazioni storiche"
                ]
            }
        ]

    def generate_math_concepts(self, course_name: str, book_titles: list):
        """Genera concetti per corsi di matematica."""
        return [
            {
                "id": "fondamenti-logici",
                "name": "Fondamenti Logici e Teoria degli Insiemi",
                "summary": "Basi logiche e concetti insiemistici",
                "chapter": {"title": "Capitolo 1", "index": 1},
                "related_topics": ["logica proposizionale", "insiemi", "funzioni", "relazioni"],
                "learning_objectives": [
                    "Applicare regole logiche",
                    "Operare con insiemi",
                    "Comprendere relazioni e funzioni"
                ],
                "suggested_reading": book_titles[:2] if book_titles else ["Manuale di matematica"],
                "recommended_minutes": 60,
                "quiz_outline": [
                    "Risolvere problemi logici",
                    "Operare con insiemi",
                    "Analizzare relazioni matematiche"
                ]
            }
        ]

    def generate_generic_concepts(self, course_name: str, book_titles: list):
        """Genera concetti generici per altri tipi di corsi."""
        return [
            {
                "id": "introduzione-corso",
                "name": "Introduzione al Corso",
                "summary": f"Concetti fondamentali e panoramica di {course_name}",
                "chapter": {"title": "Capitolo 1", "index": 1},
                "related_topics": ["concetti base", "terminologia", "obiettivi"],
                "learning_objectives": [
                    "Comprendere gli obiettivi del corso",
                    "Familiarizzare con la terminologia",
                    "Identificare le aree principali"
                ],
                "suggested_reading": book_titles[:2] if book_titles else ["Materiale introduttivo"],
                "recommended_minutes": 30,
                "quiz_outline": [
                    "Definire i concetti fondamentali",
                    "Spiegare gli obiettivi del corso"
                ]
            }
        ]

async def main():
    processor = MaterialProcessor()
    await processor.process_all_courses()

if __name__ == "__main__":
    asyncio.run(main())