#!/usr/bin/env python3
"""
Script completo per generare mappe concettuali dettagliate basate sui PDF caricati.
"""

import asyncio
import json
import sys
import os
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.concept_map_service import ConceptMapService
import structlog

logger = structlog.get_logger()

class ComprehensiveConceptGenerator:
    def __init__(self):
        self.concept_service = ConceptMapService()
        self.base_url = "http://localhost:8000"

    async def generate_comprehensive_concepts(self, course_id: str):
        """Genera mappa concettuale completa basata su tutti i materiali del corso."""
        logger.info(f"Generating comprehensive concepts for course: {course_id}")

        # 1. Get course information and books
        course_info = await self.get_course_info(course_id)
        books = course_info.get("books", [])

        # 2. Extract structure from all PDFs
        all_chapters = []
        all_pdf_content = []

        for book in books:
            book_title = book.get("title", "Unknown Book")
            book_id = book.get("id")
            materials = book.get("materials", [])

            logger.info(f"Processing book: {book_title} ({len(materials)} files)")

            for material in materials:
                if material.get("filename", "").endswith(".pdf"):
                    # Extract chapters and content
                    chapters = await self.extract_pdf_chapters(material, book_title, book_id)
                    all_chapters.extend(chapters)

                    # Extract sample content for AI analysis
                    content_sample = await self.extract_pdf_sample(material)
                    if content_sample:
                        all_pdf_content.append({
                            "source": f"{book_title} - {material['filename']}",
                            "content": content_sample
                        })

        # 3. Generate concepts based on extracted content
        concepts = await self.generate_detailed_concepts(course_id, course_info, all_chapters, all_pdf_content)

        # 4. Save comprehensive concept map
        concept_map = {
            "course_id": course_id,
            "course_name": course_info.get("name", "Unknown Course"),
            "generated_at": datetime.now().isoformat(),
            "source_count": len(books),
            "total_chapters_found": len(all_chapters),
            "pdfs_processed": len([m for book in books for m in book.get("materials", []) if m.get("filename", "").endswith(".pdf")]),
            "is_comprehensive": True,
            "concepts": concepts
        }

        await self.save_concept_map(course_id, concept_map)

        return {
            "course_id": course_id,
            "course_name": course_info.get("name"),
            "books_processed": len(books),
            "chapters_found": len(all_chapters),
            "concepts_generated": len(concepts),
            "pdfs_processed": concept_map["pdfs_processed"],
            "generated_at": concept_map["generated_at"]
        }

    async def get_course_info(self, course_id: str) -> Dict[str, Any]:
        """Get detailed course information."""
        try:
            response = requests.get(f"{self.base_url}/courses/{course_id}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get course info: {response.status_code}")
                return {"name": "Unknown Course", "books": []}
        except Exception as e:
            logger.error(f"Error getting course info: {str(e)}")
            return {"name": "Unknown Course", "books": []}

    async def extract_pdf_chapters(self, material: Dict, book_title: str, book_id: str) -> List[Dict]:
        """Extract chapters from PDF material using multiple approaches."""
        try:
            file_path = material.get("file_path")
            if not file_path or not os.path.exists(file_path):
                logger.warning(f"PDF file not found: {file_path}")
                return []

            logger.info(f"Extracting chapters from: {material['filename']}")

            chapters = []

            # Method 1: Try to use RAG service structure analysis
            try:
                from services.rag_service import RAGService
                rag_service = RAGService()
                structure = rag_service.analyze_pdf_structure(file_path)
                rag_chapters = structure.get("chapters", [])

                for chapter in rag_chapters:
                    chapters.append({
                        "source_method": "rag_analysis",
                        "book_title": book_title,
                        "book_id": book_id,
                        "title": chapter.get("title", ""),
                        "page": chapter.get("page", 0),
                        "chapter_number": chapter.get("chapter_number", 0),
                        "estimated_reading_time": chapter.get("estimated_reading_time", 0),
                        "key_topics": chapter.get("key_topics", []),
                        "type": chapter.get("type", "chapter")
                    })

                if chapters:
                    logger.info(f"✅ RAG analysis found {len(chapters)} chapters")
                    return chapters

            except Exception as e:
                logger.warning(f"RAG analysis failed: {str(e)}")

            # Method 2: Manual chapter detection using patterns
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                full_text = ""

                for page_num in range(min(len(doc), 50)):  # Limit to first 50 pages for performance
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    full_text += f"\n--- PAGE {page_num + 1} ---\n{text}\n"

                doc.close()

                # Italian chapter patterns
                chapter_patterns = [
                    r'Capitolo\s+(\d+)\s*[:\-\.]\s*(.+?)(?=\n|$|\nCapitolo|\n\d+\.)',
                    r'CAP\.?\s*(\d+)\s*[:\-\.]\s*(.+?)(?=\n|$|\nCAP\.?|\n\d+\.)',
                    r'(\d+)\.\s*([A-Z][^.\n]{10,50})(?=\n|\n\d+\.)',
                    r'Lezione\s+(\d+)\s*[:\-\.]\s*(.+?)(?=\n|$|\nLezione|\n\d+\.)',
                    r'Modulo\s+(\d+)\s*[:\-\.]\s*(.+?)(?=\n|$|\nModulo|\n\d+\.)',
                    r'Unità\s+(\d+)\s*[:\-\.]\s*(.+?)(?=\n|$|\nUnità|\n\d+\.)',
                    r'PARTE\s+([IVXLCDM]+)\s*[:\-\.]\s*(.+?)(?=\n|$|\nPARTE|\n\d+\.)'
                ]

                import re
                found_chapters = []

                for pattern in chapter_patterns:
                    matches = re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        if len(match.groups()) >= 2:
                            chapter_num = match.group(1)
                            chapter_title = match.group(2).strip()

                            # Find page number
                            chapter_start = match.start()
                            page_match = re.search(r'--- PAGE (\d+) ---', full_text[max(0, chapter_start-200):chapter_start+200])
                            page_num = int(page_match.group(1)) if page_match else 1

                            found_chapters.append({
                                "source_method": "pattern_detection",
                                "book_title": book_title,
                                "book_id": book_id,
                                "title": f"Capitolo {chapter_num}: {chapter_title}",
                                "page": page_num,
                                "chapter_number": int(chapter_num) if chapter_num.isdigit() else 0,
                                "estimated_reading_time": 30,  # Default estimate
                                "key_topics": [],
                                "type": "chapter"
                            })

                # Remove duplicates and sort
                unique_chapters = {}
                for chapter in found_chapters:
                    key = (chapter["page"], chapter["title"])
                    if key not in unique_chapters:
                        unique_chapters[key] = chapter

                chapters = sorted(unique_chapters.values(), key=lambda x: x["page"])

                if chapters:
                    logger.info(f"✅ Pattern detection found {len(chapters)} chapters")
                    return chapters[:20]  # Limit to 20 chapters

            except Exception as e:
                logger.warning(f"Pattern detection failed: {str(e)}")

            # Method 3: Create chapter-like structure from PDF content sections
            try:
                import fitz
                doc = fitz.open(file_path)
                total_pages = len(doc)

                # Create artificial chapters based on page ranges
                pages_per_chapter = max(10, total_pages // 10)  # Max 10 chapters

                for i in range(0, total_pages, pages_per_chapter):
                    start_page = i + 1
                    end_page = min(i + pages_per_chapter, total_pages)

                    # Extract sample text for this section
                    section_text = ""
                    for page_num in range(start_page - 1, min(end_page, total_pages)):
                        page = doc.load_page(page_num)
                        section_text += page.get_text()[:300]  # First 300 chars per page

                    # Extract key terms from section text
                    words = section_text.split()
                    key_terms = [w for w in words if len(w) > 8 and w.isalpha()][:5]

                    chapters.append({
                        "source_method": "section_creation",
                        "book_title": book_title,
                        "book_id": book_id,
                        "title": f"Sezione {i//pages_per_chapter + 1}: Pagine {start_page}-{end_page}",
                        "page": start_page,
                        "chapter_number": i//pages_per_chapter + 1,
                        "estimated_reading_time": pages_per_chapter * 2,  # 2 min per page
                        "key_topics": key_terms,
                        "type": "section"
                    })

                doc.close()
                logger.info(f"✅ Section creation found {len(chapters)} sections")
                return chapters[:15]  # Limit to 15 sections

            except Exception as e:
                logger.warning(f"Section creation failed: {str(e)}")

            logger.warning(f"No chapters found in {material['filename']}")
            return []

        except Exception as e:
            logger.error(f"Error processing PDF {material['filename']}: {str(e)}")
            return []

    async def extract_pdf_sample(self, material: Dict) -> str:
        """Extract a sample of text from PDF for AI analysis."""
        try:
            file_path = material.get("file_path")
            if not file_path or not os.path.exists(file_path):
                return ""

            import fitz
            doc = fitz.open(file_path)
            sample_text = ""

            # Extract from first few pages
            for page_num in range(min(3, len(doc))):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text:
                    sample_text += text[:500] + "\n"  # First 500 chars per page

            doc.close()
            return sample_text[:1000]  # Max 1000 chars total

        except Exception as e:
            logger.warning(f"Failed to extract sample from {material['filename']}: {str(e)}")
            return ""

    async def generate_detailed_concepts(self, course_id: str, course_info: Dict, chapters: List[Dict], pdf_content: List[Dict]) -> List[Dict]:
        """Generate detailed concepts based on course information and extracted content."""
        course_name = course_info.get("name", "").lower()
        concepts = []

        # Generate macro-concepts based on course type
        if "geografia" in course_name:
            macro_concepts = [
                {
                    "id": "spazio-geografico",
                    "name": "Spazio Geografico e Territorio",
                    "summary": "Concetti fondamentali di spazio geografico, territorio e organizzazione spaziale",
                    "chapter": {"title": "Concetti Fondamentali", "index": 1},
                    "related_topics": ["scala geografica", "luogo", "paesaggio", "ambiente", "territorio"],
                    "learning_objectives": [
                        "Comprendere i concetti di spazio e territorio",
                        "Distinguere le diverse scale geografiche",
                        "Analizzare i rapporti tra società e ambiente"
                    ],
                    "suggested_reading": self.get_relevant_books(chapters, ["spazio", "territorio", "concetti"]),
                    "recommended_minutes": 60,
                    "quiz_outline": [
                        "Definire spazio geografico e territorio",
                        "Spiegare le diverse scale di analisi",
                        "Analizzare esempi concreti di organizzazione territoriale"
                    ]
                },
                {
                    "id": "geografia-fisica",
                    "name": "Geografia Fisica e Ambiente",
                    "summary": "Elementi di geografia fisica, processi naturali e interazioni ambientali",
                    "chapter": {"title": "Componenti Naturali", "index": 2},
                    "related_topics": ["clima", "rilievo", "idrografia", "ecosistemi", "risorse naturali"],
                    "learning_objectives": [
                        "Comprendere i processi geomorfologici",
                        "Analizzare i sistemi climatici",
                        "Valutare le interazioni ambientali"
                    ],
                    "suggested_reading": self.get_relevant_books(chapters, ["fisico", "naturale", "ambiente", "clima"]),
                    "recommended_minutes": 75,
                    "quiz_outline": [
                        "Spiegare i principali processi geomorfologici",
                        "Descrivere i fattori climatici",
                        "Analizzare le relazioni tra elementi fisici"
                    ]
                },
                {
                    "id": "geografia-umana",
                    "name": "Geografia Umana e Culturale",
                    "summary": "Popolamento, insediamenti umani, attività economiche e organizzazione sociale",
                    "chapter": {"title": "Organizzazione Umana", "index": 3},
                    "related_topics": ["demografia", "urbanizzazione", "economia", "cultura", "società"],
                    "learning_objectives": [
                        "Analizzare la distribuzione della popolazione",
                        "Comprendere i processi di urbanizzazione",
                        "Valutare le attività economiche territoriali"
                    ],
                    "suggested_reading": self.get_relevant_books(chapters, ["umano", "popolazione", "economia", "cultura"]),
                    "recommended_minutes": 70,
                    "quiz_outline": [
                        "Analizzare i fattori della distribuzione demografica",
                        "Spiegare i processi di urbanizzazione",
                        "Valutare l'impatto delle attività economiche"
                    ]
                },
                {
                    "id": "cartografia-geospaziale",
                    "name": "Cartografia e Analisi Geospaziale",
                    "summary": "Metodi e strumenti per la rappresentazione e analisi dello spazio geografico",
                    "chapter": {"title": "Strumenti di Analisi", "index": 4},
                    "related_topics": ["mappe", "GIS", "coordinate", "rilevamento", "analisi spaziale"],
                    "learning_objectives": [
                        "Utilizzare sistemi di riferimento geografico",
                        "Interpretare carte e mappe tematiche",
                        "Applicare strumenti di analisi spaziale"
                    ],
                    "suggested_reading": self.get_relevant_books(chapters, ["cartografia", "mappa", "GIS", "rilevamento"]),
                    "recommended_minutes": 65,
                    "quiz_outline": [
                        "Spiegare i sistemi di coordinate geografiche",
                        "Interpretare diverse tipologie di carte",
                        "Applicare metodi di analisi spaziale"
                    ]
                },
                {
                    "id": "sviluppo-territoriale",
                    "name": "Sviluppo Territoriale e Globale",
                    "summary": "Processi di sviluppo locale, regionale e globale e loro interazioni",
                    "chapter": {"title": "Sviluppo e Globalizzazione", "index": 5},
                    "related_topics": ["sviluppo sostenibile", "globalizzazione", "reti", "politiche territoriali", "disuguaglianze"],
                    "learning_objectives": [
                        "Comprendere i processi di globalizzazione",
                        "Analizzare le politiche di sviluppo territoriale",
                        "Valutare la sostenibilità ambientale e sociale"
                    ],
                    "suggested_reading": self.get_relevant_books(chapters, ["sviluppo", "globale", "politiche", "sostenibile"]),
                    "recommended_minutes": 80,
                    "quiz_outline": [
                        "Spiegare gli impatti della globalizzazione",
                        "Analizzare le politiche di sviluppo",
                        "Valutare criteri di sostenibilità"
                    ]
                }
            ]
        else:
            # Generic concepts for other courses
            macro_concepts = [
                {
                    "id": "concetti-fondamentali",
                    "name": "Concetti Fondamentali",
                    "summary": "Principi base e concetti introduttivi della materia",
                    "chapter": {"title": "Introduzione", "index": 1},
                    "related_topics": ["base", "fondamenti", "principi", "terminologia"],
                    "learning_objectives": [
                        "Comprendere i concetti base",
                        "Familiarizzare con la terminologia",
                        "Identificare le aree principali"
                    ],
                    "suggested_reading": self.get_relevant_books(chapters, ["introduzione", "concetti", "base"]),
                    "recommended_minutes": 45,
                    "quiz_outline": [
                        "Definire i concetti fondamentali",
                        "Spiegare la terminologia di base"
                    ]
                }
            ]

        # Add chapter-specific concepts from extracted chapters
        chapter_concepts = []
        for i, chapter in enumerate(chapters[:8]):  # Limit to 8 chapters
            chapter_title = chapter.get("title", "")
            if len(chapter_title) > 10:  # Only meaningful titles
                chapter_concepts.append({
                    "id": f"chapter-{i+1}",
                    "name": chapter_title,
                    "summary": f"Analisi dettagliata: {chapter_title}",
                    "chapter": {"title": chapter_title, "index": len(macro_concepts) + i + 1},
                    "related_topics": chapter.get("key_topics", [])[:5],
                    "learning_objectives": [
                        f"Comprendere i contenuti di {chapter_title}",
                        f"Applicare i concetti chiave del capitolo",
                        f"Analizzare le implicazioni del tema trattato"
                    ],
                    "suggested_reading": [chapter.get("book_title", "Materiale del corso")],
                    "recommended_minutes": max(30, chapter.get("estimated_reading_time", 45)),
                    "quiz_outline": [
                        f"Riassumere i punti principali di {chapter_title}",
                        f"Spiegare i concetti chiave trattati",
                        f"Applicare quanto appreso a esempi concreti"
                    ],
                    "is_chapter_based": True,
                    "source_chapter": chapter
                })

        # Combine macro-concepts and chapter concepts
        concepts = macro_concepts + chapter_concepts

        logger.info(f"Generated {len(concepts)} concepts ({len(macro_concepts)} macro + {len(chapter_concepts)} chapters)")
        return concepts

    def get_relevant_books(self, chapters: List[Dict], keywords: List[str]) -> List[str]:
        """Find books/chapters relevant to given keywords."""
        relevant = []
        for chapter in chapters:
            title = chapter.get("title", "").lower()
            book_title = chapter.get("book_title", "")
            if any(keyword.lower() in title for keyword in keywords) and book_title not in relevant:
                relevant.append(book_title)
                if len(relevant) >= 3:  # Limit to 3 books
                    break
        return relevant if relevant else ["Materiale del corso"]

    async def save_concept_map(self, course_id: str, concept_map: Dict[str, Any]):
        """Save the comprehensive concept map."""
        try:
            concept_maps = self.concept_service._load_concept_maps()
            concept_maps["concept_maps"][course_id] = concept_map
            self.concept_service._save_concept_maps(concept_maps)
            logger.info(f"✅ Saved comprehensive concept map with {len(concept_map['concepts'])} concepts")
        except Exception as e:
            logger.error(f"Failed to save concept map: {str(e)}")

async def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python comprehensive_concept_generator.py <course_id>")
        sys.exit(1)

    course_id = sys.argv[1]

    generator = ComprehensiveConceptGenerator()
    result = await generator.generate_comprehensive_concepts(course_id)

    print(f"\n{'='*70}")
    print(f"RIEPILOGO GENERAZIONE COMPREHENSIVE CONCETTI")
    print(f"{'='*70}")
    print(f"Corso: {result['course_name']}")
    print(f"Libri processati: {result['books_processed']}")
    print(f"PDF analizzati: {result['pdfs_processed']}")
    print(f"Capitoli trovati: {result['chapters_found']}")
    print(f"Concetti generati: {result['concepts_generated']}")
    print(f"Generato il: {result['generated_at']}")
    print(f"{'='*70}")

    print(f"\nConcetti principali generati:")
    # Get the saved concept map to show details
    try:
        generator.concept_service._load_concept_maps()
        maps = generator.concept_service._load_concept_maps()
        saved_map = maps["concept_maps"].get(course_id, {})
        concepts = saved_map.get("concepts", [])

        for i, concept in enumerate(concepts[:8]):  # Show first 8 concepts
            print(f"{i+1}. {concept.get('name', 'Unknown')}")
            print(f"   - Obiettivi: {len(concept.get('learning_objectives', []))}")
            print(f"   - Argomenti correlati: {len(concept.get('related_topics', []))}")
            print(f"   - Tempo studio: {concept.get('recommended_minutes', 0)} min")
            print()
    except:
        pass

if __name__ == "__main__":
    asyncio.run(main())