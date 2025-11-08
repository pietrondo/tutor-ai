#!/usr/bin/env python3
"""
Script per generare mappe concettuali specifiche per ogni libro.
Ogni libro avrà la sua mappa concettuale basata sui suoi materiali PDF.
"""

import asyncio
import json
import sys
import requests
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.concept_map_service import ConceptMapService
import structlog

logger = structlog.get_logger()

class BookSpecificConceptGenerator:
    def __init__(self):
        self.concept_service = ConceptMapService()
        self.base_url = "http://localhost:8001"

    async def generate_concepts_for_all_books(self, course_id: str):
        """Genera mappe concettuali per tutti i libri di un corso."""
        logger.info(f"Generating book-specific concepts for course: {course_id}")

        # 1. Ottieni tutti i libri del corso
        books = await self.get_course_books(course_id)
        if not books:
            logger.error(f"No books found for course {course_id}")
            return None

        logger.info(f"Found {len(books)} books to process")

        results = []
        total_concepts_generated = 0

        # 2. Genera concetti per ogni libro
        for book in books:
            book_id = book.get("id")
            book_title = book.get("title", "Unknown Book")
            materials = book.get("materials", [])

            logger.info(f"Processing book: {book_title} (ID: {book_id}) - {len(materials)} materials")

            try:
                result = await self.generate_book_concepts(course_id, book_id, book_title, materials)

                results.append({
                    "book_id": book_id,
                    "book_title": book_title,
                    "status": "success",
                    "concepts_count": len(result.get("concepts", [])),
                    "materials_count": len(materials)
                })

                total_concepts_generated += len(result.get("concepts", []))
                logger.info(f"✅ Generated {len(result.get('concepts', []))} concepts for {book_title}")

            except Exception as e:
                logger.error(f"❌ Failed to generate concepts for {book_title}: {str(e)}")
                results.append({
                    "book_id": book_id,
                    "book_title": book_title,
                    "status": "error",
                    "error": str(e),
                    "concepts_count": 0,
                    "materials_count": len(materials)
                })

        # 3. Salva risultati
        summary = {
            "generation_timestamp": datetime.now().isoformat(),
            "course_id": course_id,
            "total_books": len(books),
            "total_concepts": total_concepts_generated,
            "successful_books": sum(1 for r in results if r["status"] == "success"),
            "failed_books": sum(1 for r in results if r["status"] == "error"),
            "results": results
        }

        results_file = f"data/book_concepts_{course_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        self.print_summary(summary, results_file)
        return summary

    async def get_course_books(self, course_id: str) -> List[Dict]:
        """Ottieni tutti i libri di un corso dall'API."""
        try:
            response = requests.get(f"{self.base_url}/courses/{course_id}/books")
            if response.status_code == 200:
                data = response.json()
                return data.get("books", [])
            else:
                logger.error(f"Failed to get books: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting books: {str(e)}")
            return []

    async def get_book_materials_from_course(self, course_id: str, book_id: str) -> List[Dict]:
        """Ottieni i materiali di un libro specifico dai materiali del corso."""
        try:
            # Ottieni tutti i materiali del corso
            response = requests.get(f"{self.base_url}/courses/{course_id}")
            if response.status_code == 200:
                data = response.json()
                course_materials = data.get("course", {}).get("materials", [])

                # Filtra i materiali che appartengono a questo libro
                book_materials = []
                for material in course_materials:
                    # Controlla se il materiale appartiene a questo libro basandosi sul path
                    file_path = material.get("file_path", "")
                    if f"books/{book_id}/" in file_path:
                        book_materials.append(material)

                logger.info(f"Found {len(book_materials)} materials for book {book_id} in course materials")
                return book_materials
            else:
                logger.error(f"Failed to get course materials: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting book materials from course: {str(e)}")
            return []

    async def generate_book_concepts(self, course_id: str, book_id: str, book_title: str, materials: List[Dict]) -> Dict[str, Any]:
        """Genera concetti per un singolo libro basandosi sui suoi materiali."""

        # Se i materiali non sono forniti a livello libro, prendili dal corso
        if not materials:
            materials = await self.get_book_materials_from_course(course_id, book_id)

        pdf_materials = [m for m in materials if m.get("filename", "").endswith(".pdf")]

        logger.info(f"Processing {len(pdf_materials)} PDFs for book: {book_title}")

        # Se non ci sono PDF, genera concetti fallback basati sul titolo
        if not pdf_materials:
            logger.warning(f"No PDF materials found for {book_title}, generating fallback concepts")
            return self.generate_fallback_book_concepts(course_id, book_id, book_title)

        # Analizza i nomi dei file per categorizzare i contenuti
        categorized_materials = self.categorize_materials(pdf_materials)

        # Genera concetti basati sul tipo di libro e materiali
        concepts = self.extract_concepts_from_materials(course_id, book_id, book_title, categorized_materials)

        # Crea mappa concettuale specifica per il libro
        concept_map = {
            "course_id": course_id,
            "book_id": book_id,
            "book_title": book_title,
            "generated_at": datetime.now().isoformat(),
            "source_count": len(pdf_materials),
            "extraction_method": "book_specific_analysis",
            "is_book_specific": True,
            "concepts": concepts
        }

        # Salva la mappa concettuale del libro
        await self.save_book_concept_map(course_id, book_id, concept_map)

        return concept_map

    def categorize_materials(self, pdf_materials: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorizza i materiali PDF per tipo."""
        categorized = {
            "chapters": [],
            "lessons": [],
            "manuals": [],
            "essays": [],
            "other": []
        }

        for material in pdf_materials:
            filename = material.get("filename", "").lower()

            # Rileva capitoli numerati
            if re.search(r'capitolo\s*\d+\.pdf|chapter\s*\d+\.pdf', filename):
                categorized["chapters"].append(material)
            # Rileva lezioni
            elif re.search(r'lezione\s*\d+\.pdf|lesson\s*\d+\.pdf', filename):
                categorized["lessons"].append(material)
            # Rileva manuali
            elif any(keyword in filename for keyword in ['manuale', 'manual', 'guida', 'handbook']):
                categorized["manuals"].append(material)
            # Rileva saggi/tesi
            elif any(keyword in filename for keyword in ['saggio', 'essay', 'tesi', 'dissertazione']):
                categorized["essays"].append(material)
            else:
                categorized["other"].append(material)

        return categorized

    def extract_concepts_from_materials(self, course_id: str, book_id: str, book_title: str, categorized: Dict[str, List[Dict]]) -> List[Dict]:
        """Estrai concetti dai materiali categorizzati."""
        concepts = []
        concept_index = 1

        # Analizza il titolo del libro per determinare il tipo di concetti
        book_type = self.identify_book_type(book_title)

        # 1. Se ci sono capitoli, crea concetti basati sui capitoli
        if categorized["chapters"]:
            concepts.extend(self.generate_chapter_concepts(categorized["chapters"], book_title, concept_index))
            concept_index += len(concepts)

        # 2. Se ci sono lezioni, crea concetti basati sulle lezioni
        if categorized["lessons"]:
            concepts.extend(self.generate_lesson_concepts(categorized["lessons"], book_title, concept_index))
            concept_index += len(concepts) - len(concepts) + 1  # Continue from where we left

        # 3. Aggiungi concetti generali basati sul tipo di libro
        general_concepts = self.generate_general_book_concepts(book_title, book_type, categorized, concept_index)
        concepts.extend(general_concepts)

        # 4. Se ci sono manuali, aggiungi concetti metodologici
        if categorized["manuals"]:
            method_concepts = self.generate_methodological_concepts(categorized["manuals"], book_title, concept_index + len(concepts))
            concepts.extend(method_concepts)

        logger.info(f"Generated {len(concepts)} concepts for {book_title}")
        return concepts

    def identify_book_type(self, book_title: str) -> str:
        """Identifica il tipo di libro dal titolo."""
        title_lower = book_title.lower()

        if any(keyword in title_lower for keyword in ['geografia', 'geographic']):
            return "geography"
        elif any(keyword in title_lower for keyword in ['storia', 'history']):
            return "history"
        elif any(keyword in title_lower for keyword in ['matematica', 'mathematics', 'algebra', 'calcolo']):
            return "mathematics"
        elif any(keyword in title_lower for keyword in ['chimica', 'chemistry']):
            return "chemistry"
        elif any(keyword in title_lower for keyword in ['fisica', 'physics']):
            return "physics"
        elif any(keyword in title_lower for keyword in ['biologia', 'biology']):
            return "biology"
        elif any(keyword in title_lower for keyword in ['economia', 'economics', 'business']):
            return "economics"
        elif any(keyword in title_lower for keyword in ['letteratura', 'literature', 'poesia', 'poetry']):
            return "literature"
        elif any(keyword in title_lower for keyword in ['filosofia', 'philosophy']):
            return "philosophy"
        elif any(keyword in title_lower for keyword in ['psicologia', 'psychology']):
            return "psychology"
        else:
            return "general"

    def generate_chapter_concepts(self, chapters: List[Dict], book_title: str, start_index: int) -> List[Dict]:
        """Genera concetti basati sui capitoli."""
        concepts = []

        # Estrai numeri dei capitoli
        chapter_numbers = []
        for chapter in chapters:
            filename = chapter.get("filename", "")
            match = re.search(r'capitolo\s*(\d+)', filename)
            if match:
                chapter_numbers.append(int(match.group(1)))

        chapter_numbers.sort()
        logger.info(f"Found chapter numbers: {chapter_numbers}")

        # Crea concetti per i capitoli trovati
        for i, chapter_num in enumerate(chapter_numbers[:10]):  # Max 10 chapter concepts
            concepts.append({
                "id": f"chapter-{i+1}",
                "name": f"Capitolo {chapter_num}",
                "summary": f"Analisi del contenuto del capitolo {chapter_num} nel libro {book_title}",
                "chapter": {"title": f"Capitolo {chapter_num}", "index": start_index + i},
                "related_topics": [f"argomenti capitolo {chapter_num}", f"concetti chiave capitolo {chapter_num}"],
                "learning_objectives": [
                    f"Comprendere i contenuti del capitolo {chapter_num}",
                    f"Identificare i concetti principali del capitolo",
                    f"Applicare i concetti a esercizi pratici"
                ],
                "suggested_reading": [f"Materiale del capitolo {chapter_num}"],
                "recommended_minutes": 45,
                "quiz_outline": [
                    f"Riassumere i punti principali del capitolo {chapter_num}",
                    f"Spiegare i concetti chiave trattati",
                    f"Risolvere esercizi sul capitolo {chapter_num}"
                ],
                "source_materials_count": len(chapters),
                "is_chapter_based": True
            })

        return concepts

    def generate_lesson_concepts(self, lessons: List[Dict], book_title: str, start_index: int) -> List[Dict]:
        """Genera concetti basati sulle lezioni."""
        concepts = []

        # Estrai numeri delle lezioni
        lesson_numbers = []
        for lesson in lessons:
            filename = lesson.get("filename", "")
            match = re.search(r'lezione\s*(\d+)', filename)
            if match:
                lesson_numbers.append(int(match.group(1)))

        lesson_numbers.sort()
        logger.info(f"Found lesson numbers: {lesson_numbers}")

        # Crea concetti per lezioni trovate
        for i, lesson_num in enumerate(lesson_numbers[:8]):  # Max 8 lesson concepts
            concepts.append({
                "id": f"lesson-{i+1}",
                "name": f"Lezione {lesson_num}",
                "summary": f"Contenuti e argomenti trattati nella lezione {lesson_num} dal libro {book_title}",
                "chapter": {"title": f"Lezione {lesson_num}", "index": start_index + i},
                "related_topics": [f"temi lezione {lesson_num}", f"esercizi lezione {lesson_num}"],
                "learning_objectives": [
                    f"Comprendere i temi della lezione {lesson_num}",
                    f"Applicare i concetti appresi",
                    f"Completare gli esercizi proposti"
                ],
                "suggested_reading": [f"Materiale della lezione {lesson_num}"],
                "recommended_minutes": 35,
                "quiz_outline": [
                    f"Riassumere i punti principali della lezione {lesson_num}",
                    f"Spiegare i concetti chiave",
                    f"Risolvere gli esercizi della lezione"
                ],
                "source_materials_count": len(lessons),
                "is_lesson_based": True
            })

        return concepts

    def generate_general_book_concepts(self, book_title: str, book_type: str, categorized: Dict[str, List[Dict]], start_index: int) -> List[Dict]:
        """Genera concetti generali basati sul tipo di libro."""
        concepts = []

        if book_type == "geography":
            # Concetti specifici per geografia
            concepts = [
                {
                    "id": f"geo-foundations-{start_index}",
                    "name": "Fondamenti di Geografia",
                    "summary": "Concetti fondamentali di geografia trattati nel libro",
                    "chapter": {"title": "Fondamenti", "index": start_index},
                    "related_topics": ["spazio geografico", "territorio", "paesaggio", "scala"],
                    "learning_objectives": [
                        "Comprendere i concetti di base della geografia",
                        "Analizzare le diverse scale geografiche",
                        "Interpretare i rapporti tra società e ambiente"
                    ],
                    "suggested_reading": self.extract_material_titles(categorized, ["manuals", "other"]),
                    "recommended_minutes": 60,
                    "quiz_outline": [
                        "Definire i concetti geografici fondamentali",
                        "Spiegare le scale di analisi",
                        "Analizzare esempi concreti"
                    ]
                },
                {
                    "id": f"geo-analysis-{start_index+1}",
                    "name": "Metodi di Analisi Geografica",
                    "summary": "Strumenti e metodi per l'analisi territoriale",
                    "chapter": {"title": "Analisi Territoriale", "index": start_index + 1},
                    "related_topics": ["cartografia", "mappe", "GIS", "rilevamento"],
                    "learning_objectives": [
                        "Utilizzare strumenti cartografici",
                        "Interpretare diverse tipologie di carte",
                        "Applicare metodi di analisi spaziale"
                    ],
                    "suggested_reading": self.extract_material_titles(categorized, ["manuals", "chapters"]),
                    "recommended_minutes": 50,
                    "quiz_outline": [
                        "Interpretare carte geografiche",
                        "Utilizzare coordinate geografiche",
                        "Analizzare dati territoriali"
                    ]
                }
            ]
        elif book_type == "history":
            # Concetti per storia
            concepts = [
                {
                    "id": f"history-foundations-{start_index}",
                    "name": "Concetti Storici Fondamentali",
                    "summary": "Principi e metodologia della ricerca storica",
                    "chapter": {"title": "Metodologia Storica", "index": start_index},
                    "related_topics": ["fonti storiche", "periodizzazione", "critica storica"],
                    "learning_objectives": [
                        "Comprendere i metodi della ricerca storica",
                        "Analizzare le fonti storiche",
                        "Applicare la critica storica"
                    ],
                    "suggested_reading": self.extract_material_titles(categorized, ["manuals", "essays"]),
                    "recommended_minutes": 55,
                    "quiz_outline": [
                        "Spiegare i metodi della ricerca",
                        "Analizzare fonti storiche",
                        "Applicare la critica delle fonti"
                    ]
                }
            ]
        else:
            # Concetti generici per altri tipi di libro
            concepts = [
                {
                    "id": f"general-foundations-{start_index}",
                    "name": "Concetti Fondamentali",
                    "summary": f"Principi base e concetti introduttivi del libro {book_title}",
                    "chapter": {"title": "Introduzione", "index": start_index},
                    "related_topics": ["concetti base", "terminologia", "struttura"],
                    "learning_objectives": [
                        "Comprendere i concetti fondamentali",
                        "Familiarizzare con la terminologia",
                        "Identificare la struttura del libro"
                    ],
                    "suggested_reading": ["Introduzione e capitoli iniziali"],
                    "recommended_minutes": 45,
                    "quiz_outline": [
                        "Definire i concetti fondamentali",
                        "Spiegare la terminologia specifica",
                        "Identificare la struttura tematica"
                    ]
                }
            ]

        return concepts

    def generate_methodological_concepts(self, manuals: List[Dict], book_title: str, start_index: int) -> List[Dict]:
        """Genera concetti metodologici basati sui manuali."""
        if not manuals:
            return []

        concepts = []
        manual_titles = [m.get("filename", "").replace(".pdf", "") for m in manuals[:3]]

        concepts.append({
            "id": f"methodology-{start_index}",
            "name": "Metodologia di Studio",
            "summary": "Approcci e metodi per studiare efficacemente il contenuti del libro",
            "chapter": {"title": "Metodologia", "index": start_index},
            "related_topics": ["tecniche di studio", "organizzazione", "approfondimento"],
            "learning_objectives": [
                "Applicare tecniche di studio efficaci",
                "Organizzare il tempo di studio",
                "Utilizzare approfondimenti mirati"
            ],
            "suggested_reading": manual_titles,
            "recommended_minutes": 40,
            "quiz_outline": [
                "Spiegare le migliori tecniche di studio",
                "Organizzare un piano di studio efficace",
                "Utilizzare risorse di approfondimento"
            ],
            "source_materials_count": len(manuals),
            "is_methodological": True
        })

        return concepts

    def generate_fallback_book_concepts(self, course_id: str, book_id: str, book_title: str) -> Dict[str, Any]:
        """Genera concetti fallback quando non ci sono materiali."""
        concepts = [
            {
                "id": "fallback-intro",
                "name": "Introduzione al Libro",
                "summary": f"Panoramica dei contenuti e struttura del libro {book_title}",
                "chapter": {"title": "Introduzione", "index": 1},
                "related_topics": ["struttura del libro", "contenuti principali", "obiettivi"],
                "learning_objectives": [
                    "Comprendere la struttura del libro",
                    "Identificare i temi principali",
                    "Stabilire obiettivi di studio"
                ],
                "suggested_reading": [book_title],
                "recommended_minutes": 30,
                "quiz_outline": [
                    "Descrivere la struttura del libro",
                    "Identificare i temi principali",
                    "Stabilire obiettivi di apprendimento"
                ]
            },
            {
                "id": "fallback-concepts",
                "name": "Concetti Chiave",
                "summary": f"Principali concetti e temi trattati nel libro {book_title}",
                "chapter": {"title": "Concetti Principali", "index": 2},
                "related_topics": ["temi centrali", "concetti fondamentali"],
                "learning_objectives": [
                    "Comprendere i concetti principali",
                    "Identificare i temi centrali",
                    "Collegare i concetti tra loro"
                ],
                "suggested_reading": [book_title],
                "recommended_minutes": 45,
                "quiz_outline": [
                    "Definire i concetti principali",
                    "Spiegare le relazioni tra concetti",
                    "Applicare i concetti a esempi"
                ]
            }
        ]

        return {
            "course_id": course_id,
            "book_id": book_id,
            "book_title": book_title,
            "generated_at": datetime.now().isoformat(),
            "source_count": 0,
            "extraction_method": "fallback_analysis",
            "is_book_specific": True,
            "is_fallback": True,
            "concepts": concepts
        }

    def extract_material_titles(self, categorized: Dict[str, List[Dict]], priority_categories: List[str]) -> List[str]:
        """Estrai titoli dai materiali data le categorie con priorità."""
        titles = []
        for category in priority_categories:
            if category in categorized and categorized[category]:
                for material in categorized[category][:3]:  # Max 3 per categoria
                    filename = material.get("filename", "")
                    title = re.sub(r'\.pdf$', '', filename)
                    title = re.sub(r'[_\-]', ' ', title)
                    if title not in titles:
                        titles.append(title)
        return titles if titles else ["Materiali del libro"]

    async def save_book_concept_map(self, course_id: str, book_id: str, concept_map: Dict[str, Any]):
        """Salva la mappa concettuale del libro usando una struttura gerarchica."""
        try:
            # Carica le mappe esistenti
            concept_maps = self.concept_service._load_concept_maps()

            # Assicura che esista la struttura per course_id
            if "concept_maps" not in concept_maps:
                concept_maps["concept_maps"] = {}

            # Se il corso non esiste, crealo come base
            if course_id not in concept_maps["concept_maps"]:
                concept_maps["concept_maps"][course_id] = {
                    "course_id": course_id,
                    "generated_at": concept_map.get("generated_at", ""),
                    "books": {}
                }

            # Se il corso esiste ma non ha la struttura books, aggiungila preservando i dati esistenti
            if "books" not in concept_maps["concept_maps"][course_id]:
                concept_maps["concept_maps"][course_id]["books"] = {}

            # Salva la mappa del libro specifico
            concept_maps["concept_maps"][course_id]["books"][book_id] = concept_map

            # Salva il tutto
            self.concept_service._save_concept_maps(concept_maps)
            logger.info(f"✅ Saved book concept map for {book_id} with {len(concept_map['concepts'])} concepts")

        except Exception as e:
            logger.error(f"Failed to save book concept map: {str(e)}")

    def print_summary(self, summary: Dict[str, Any], results_file: str):
        """Stampa un riepilogo dettagliato."""
        print(f"\n{'='*80}")
        print(f"RIEPILOGO GENERAZIONE CONCETTI PER LIBRO")
        print(f"{'='*80}")
        print(f"Corso ID: {summary['course_id']}")
        print(f"Libri totali: {summary['total_books']}")
        print(f"Libri processati con successo: {summary['successful_books']}")
        print(f"Libri falliti: {summary['failed_books']}")
        print(f"Concetti totali generati: {summary['total_concepts']}")
        print(f"Risultati salvati in: {results_file}")
        print(f"{'='*80}")

        if summary['successful_books'] > 0:
            print(f"\nLibri processati con successo:")
            for result in summary['results']:
                if result['status'] == 'success':
                    print(f"  ✅ {result['book_title']}")
                    print(f"     - Concetti: {result['concepts_count']}")
                    print(f"     - Materiali: {result['materials_count']}")

        if summary['failed_books'] > 0:
            print(f"\nLibri con errori:")
            for result in summary['results']:
                if result['status'] == 'error':
                    print(f"  ❌ {result['book_title']}: {result.get('error', 'Unknown error')}")

        print(f"\n📊 Statistiche:")
        print(f"  - Media concetti per libro: {summary['total_concepts'] / max(1, summary['successful_books']):.1f}")
        print(f"  - Copertura libri: {summary['successful_books'] / summary['total_books'] * 100:.1f}%")
        print(f"{'='*80}")

async def main():
    """Funzione principale."""
    if len(sys.argv) != 2:
        print("Usage: python book_specific_concept_generator.py <course_id>")
        sys.exit(1)

    course_id = sys.argv[1]

    generator = BookSpecificConceptGenerator()
    result = await generator.generate_concepts_for_all_books(course_id)

    if result and result['total_books'] > 0:
        print(f"\n✅ Generazione completata!")
        print(f"Ora ogni libro ha la sua mappa concettuale specifica basata sui suoi materiali PDF.")
        print(f"Puoi testare le mappe concettuali nell'interfaccia web:")
        print(f"http://localhost:3000/courses/{course_id}/books")
    else:
        print("❌ Nessun libro trovato o errore durante la generazione")

if __name__ == "__main__":
    asyncio.run(main())