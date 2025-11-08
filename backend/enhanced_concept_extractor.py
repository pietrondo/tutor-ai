#!/usr/bin/env python3
"""
Script avanzato per estrarre macroconcetti e capitoli dai PDF dei corsi.
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

from services.rag_service import RAGService
from services.llm_service import LLMService
from services.concept_map_service import ConceptMapService
import structlog

logger = structlog.get_logger()

class EnhancedConceptExtractor:
    def __init__(self):
        self.rag_service = RAGService()
        self.llm_service = LLMService()
        self.concept_service = ConceptMapService()

    async def extract_concepts_from_all_pdfs(self, course_id: str):
        """Estrae concetti da tutti i PDF di un corso."""

        logger.info(f"Starting enhanced concept extraction for course: {course_id}")

        # 1. Indicizza tutti i PDF nel RAG
        await self.index_all_pdfs(course_id)

        # 2. Estrai macroconcetti usando AI
        macro_concepts = await self.extract_macro_concepts_with_ai(course_id)

        # 3. Estrai struttura dei capitoli
        chapters = await self.extract_chapter_structure(course_id)

        # 4. Genera mappa concettuale completa
        complete_concept_map = await self.generate_complete_concept_map(course_id, macro_concepts, chapters)

        # 5. Salva la mappa concettuale
        await self.save_concept_map(course_id, complete_concept_map)

        return {
            "course_id": course_id,
            "macro_concepts": len(macro_concepts),
            "chapters": len(chapters),
            "total_concepts": len(complete_concept_map.get("concepts", [])),
            "generated_at": datetime.now().isoformat()
        }

    async def index_all_pdfs(self, course_id: str):
        """Indicizza tutti i PDF del corso."""
        logger.info(f"Indexing all PDFs for course {course_id}")

        try:
            # Get course materials
            response = requests.get(f"http://localhost:8001/courses/{course_id}/books")
            if response.status_code != 200:
                logger.error(f"Failed to get course books: {response.status_code}")
                return

            books_data = response.json()
            books = books_data.get("books", [])

            total_pdfs = 0
            indexed_pdfs = 0

            for book in books:
                materials = book.get("materials", [])
                book_id = book.get("id")
                book_title = book.get("title", "Unknown Book")

                logger.info(f"Processing book: {book_title}")

                for material in materials:
                    if material.get("filename", "").endswith(".pdf"):
                        total_pdfs += 1
                        file_path = material.get("file_path")

                        try:
                            # Index PDF with RAG
                            await self.rag_service.index_pdf(file_path, course_id, book_id)
                            indexed_pdfs += 1
                            logger.info(f"✅ Indexed: {material['filename']}")

                        except Exception as e:
                            logger.error(f"❌ Failed to index {material['filename']}: {str(e)}")

            logger.info(f"Indexing complete: {indexed_pdfs}/{total_pdfs} PDFs indexed")

        except Exception as e:
            logger.error(f"Error during PDF indexing: {str(e)}")

    async def extract_macro_concepts_with_ai(self, course_id: str) -> List[Dict[str, Any]]:
        """Estrae macroconcetti usando l'AI analizzando il contenuto dei PDF indicizzati."""
        logger.info("Extracting macro concepts with AI")

        try:
            # Get indexed documents
            documents_result = await self.rag_service.search_documents(course_id)
            documents = documents_result.get("documents", [])

            if not documents:
                logger.warning("No indexed documents found, generating fallback concepts")
                return await self.generate_fallback_macro_concepts(course_id)

            # Aggregate content from multiple sources
            content_samples = []
            for doc in documents[:10]:  # Prendi i primi 10 documenti
                for chunk in doc.get("chunks", [])[:2]:  # Prendi i primi 2 chunk per documento
                    text = chunk.get("content", "") or chunk.get("text", "")
                    if text and len(text) > 100:
                        content_samples.append({
                            "source": doc.get("source", "Unknown"),
                            "content": text[:500]  # Primi 500 caratteri
                        })

            if not content_samples:
                return await self.generate_fallback_macro_concepts(course_id)

            # Create prompt for macro concepts extraction
            content_text = "\n\n".join([f"Fonte: {sample['source']}\n{sample['content']}" for sample in content_samples[:5]])

            prompt = f"""
Sei un esperto di analisi dei contenuti accademici. Analizza i seguenti materiali di un corso universitario e estrai i macroconcetti fondamentali.

MATERIALI:
{content_text}

TASK:
Estrai i 10-15 macroconcetti più importanti che rappresentano le idee principali del corso.
Per ogni concetto fornisci:
1. nome: Nome chiaro e conciso del concetto
2. descrizione: Breve spiegazione (1-2 frasi)
3. parole_chiave: 5-10 parole chiave importanti
4. importanza: Alto/Medio/Basso (quanto è fondamentale per il corso)
5. argomenti_correlati: 3-5 argomenti correlati

Formato JSON:
{{
  "macro_concetti": [
    {{
      "nome": "Nome del concetto",
      "descrione": "Breve descrizione",
      "parole_chiave": ["parola1", "parola2", ...],
      "importanza": "Alto",
      "argomenti_correlati": ["argomento1", "argomento2", ...]
    }}
  ]
}}

Concentrati sui concetti veramente importanti e fondamentali per la comprensione della materia.
"""

            # Call LLM
            response = await self.llm_service.generate_response(prompt, temperature=0.3)

            # Parse response
            try:
                # Try to extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    json_text = json_match.group(0)
                    data = json.loads(json_text)
                    concepts = data.get("macro_concetti", [])
                else:
                    concepts = []

                logger.info(f"✅ Extracted {len(concepts)} macro concepts with AI")
                return concepts[:15]  # Limit to 15 concepts

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {str(e)}")
                return await self.generate_fallback_macro_concepts(course_id)

        except Exception as e:
            logger.error(f"Error in AI macro concept extraction: {str(e)}")
            return await self.generate_fallback_macro_concepts(course_id)

    async def generate_fallback_macro_concepts(self, course_id: str) -> List[Dict[str, Any]]:
        """Genera macroconcetti fallback basati sul tipo di corso."""

        # Get course info
        try:
            response = requests.get(f"http://localhost:8001/courses/{course_id}")
            if response.status_code == 200:
                course_data = response.json()
                course_name = course_data.get("name", "").lower()
            else:
                course_name = ""
        except:
            course_name = ""

        if "geografia" in course_name:
            return [
                {
                    "nome": "Spazio Geografico",
                    "descrzione": "Il concetto fondamentale di spazio come costruzione sociale e naturale",
                    "parole_chiave": ["territorio", "paesaggio", "luogo", "ambiente", "scala geografica"],
                    "importanza": "Alto",
                    "argomenti_correlati": ["geografia fisica", "geografia umana", "analisi territoriale"]
                },
                {
                    "nome": "Territorio e Ambiente",
                    "descrzione": "Relazioni tra attività umane e ambiente naturale",
                    "parole_chiave": ["ecosistema", "sostenibilità", "impatto ambientale", "risorse naturali"],
                    "importanza": "Alto",
                    "argomenti_correlati": ["geografia ambientale", "gestione risorse", "sviluppo sostenibile"]
                },
                {
                    "nome": "Cartografia e Rappresentazione",
                    "descrzione": "Metodi e strumenti per rappresentare lo spazio geografico",
                    "parole_chiave": ["mappe", "GIS", "coordinate", "proiezioni", "visualizzazione dati"],
                    "importanza": "Alto",
                    "argomenti_correlati": ["cartografia tematica", "sistemi informativi geografici", "analisi spaziale"]
                },
                {
                    "nome": "Globalizzazione e Sistemi Territoriali",
                    "descrzione": "Processi di globalizzazione e loro impatto sui territori",
                    "parole_chiave": ["globalizzazione", "reti", "flussi", "connettività", "economia globale"],
                    "importanza": "Medio",
                    "argomenti_correlati": ["geografia economica", "reti globali", "località globale"]
                },
                {
                    "nome": "Sviluppo Regionale e Locale",
                    "descrzione": "Processi di sviluppo a diverse scale territoriali",
                    "parole_chiave": ["sviluppo locale", "politiche regionali", "disuguaglianze territoriali"],
                    "importanza": "Medio",
                    "argomenti_correlati": ["pianificazione territoriale", "politiche di sviluppo", "economia locale"]
                }
            ]
        else:
            # Concetti generici per altri corsi
            return [
                {
                    "nome": "Concetti Fondamentali",
                    "descrzione": "Principi base della disciplina",
                    "parole_chiave": ["base", "fondamenti", "principi", "concetti introduttivi"],
                    "importanza": "Alto",
                    "argomenti_correlati": ["teoria", "metodologia", "applicazioni"]
                }
            ]

    async def extract_chapter_structure(self, course_id: str) -> List[Dict[str, Any]]:
        """Estrae la struttura dei capitoli dai PDF."""
        logger.info("Extracting chapter structure from PDFs")

        try:
            # Get course books
            response = requests.get(f"http://localhost:8001/courses/{course_id}/books")
            if response.status_code != 200:
                return []

            books_data = response.json()
            books = books_data.get("books", [])
            all_chapters = []

            for book in books:
                materials = book.get("materials", [])
                book_title = book.get("title", "Unknown Book")

                for material in materials:
                    if material.get("filename", "").endswith(".pdf"):
                        file_path = material.get("file_path")
                        try:
                            # Use RAG service to analyze PDF structure
                            structure = self.rag_service.analyze_pdf_structure(file_path)
                            chapters = structure.get("chapters", [])

                            # Add book information
                            for chapter in chapters:
                                chapter["book_title"] = book_title
                                chapter["book_id"] = book.get("id")
                                all_chapters.append(chapter)

                        except Exception as e:
                            logger.warning(f"Failed to extract chapters from {material['filename']}: {str(e)}")

            # Sort chapters by page number
            all_chapters.sort(key=lambda x: x.get("page", 0))

            logger.info(f"✅ Extracted {len(all_chapters)} chapters from all PDFs")
            return all_chapters

        except Exception as e:
            logger.error(f"Error extracting chapter structure: {str(e)}")
            return []

    async def generate_complete_concept_map(self, course_id: str, macro_concepts: List[Dict], chapters: List[Dict]) -> Dict[str, Any]:
        """Genera una mappa concettuale completa combinando macroconcetti e capitoli."""
        logger.info("Generating complete concept map")

        concepts = []

        # Add macro concepts as main concepts
        for i, concept in enumerate(macro_concepts):
            concept_id = f"macro-{i+1}"

            # Find related chapters
            related_chapters = []
            for chapter in chapters:
                chapter_title = chapter.get("title", "").lower()
                concept_keywords = [kw.lower() for kw in concept.get("parole_chiave", [])]
                concept_name = concept.get("nome", "").lower()

                # Check if chapter relates to this concept
                if any(keyword in chapter_title for keyword in concept_keywords) or \
                   any(word in chapter_title for word in concept_name.split() if len(word) > 3):
                    related_chapters.append(chapter.get("title", ""))

            concepts.append({
                "id": concept_id,
                "name": concept.get("nome", "Concept"),
                "summary": concept.get("descrizione", ""),
                "chapter": {
                    "title": f"Concetto {i+1}: {concept.get('nome', 'Concept')}",
                    "index": i + 1
                },
                "related_topics": concept.get("argomenti_correlati", [])[:5],
                "related_chapters": related_chapters[:3],  # Top 3 related chapters
                "learning_objectives": [
                    f"Comprendere {concept.get('nome', 'il concetto')}",
                    f"Applicare i principi di {concept.get('nome', 'il concetto')}",
                    f"Analizzare le relazioni con {', '.join(concept.get('argomenti_correlati', [])[:2])}"
                ],
                "suggested_reading": [f"Materiali su {concept.get('nome', 'il concetto')}"],
                "recommended_minutes": 30 + (i * 10),  # 30, 40, 50, 60...
                "keywords": concept.get("parole_chiave", []),
                "importance": concept.get("importanza", "Medio"),
                "quiz_outline": [
                    f"Definire e spiegare {concept.get('nome', 'il concetto')}",
                    f"Applicare {concept.get('nome', 'il concetto')} a esempi concreti",
                    f"Analizzare le relazioni con concetti correlati"
                ]
            })

        # Add chapters as additional concepts if they don't overlap too much
        chapter_concepts_added = 0
        for chapter in chapters[:10]:  # Limit to 10 chapters to avoid overwhelming
            chapter_title = chapter.get("title", "")

            # Check if this chapter is already well covered by macro concepts
            is_covered = False
            for concept in concepts:
                related_chapters = concept.get("related_chapters", [])
                if chapter_title in related_chapters:
                    is_covered = True
                    break

            if not is_covered and chapter_concepts_added < 5:  # Add max 5 unique chapters
                concepts.append({
                    "id": f"chapter-{chapter_concepts_added + 1}",
                    "name": chapter_title,
                    "summary": f"Approfondimento del capitolo: {chapter_title}",
                    "chapter": {
                        "title": chapter_title,
                        "index": len(concepts) + 1
                    },
                    "related_topics": [],
                    "learning_objectives": [
                        f"Comprendere i contenuti del capitolo {chapter_title}",
                        f"Applicare i concetti chiave del capitolo"
                    ],
                    "suggested_reading": [chapter.get("book_title", "Corso materials")],
                    "recommended_minutes": 45,
                    "is_chapter_specific": True,
                    "quiz_outline": [
                        f"Riassumere i punti principali del capitolo",
                        f"Spiegare i concetti chiave trattati"
                    ]
                })
                chapter_concepts_added += 1

        return {
            "course_id": course_id,
            "generated_at": datetime.now().isoformat(),
            "source_count": len(chapters),
            "macro_concepts_count": len(macro_concepts),
            "chapters_count": len(chapters),
            "is_enhanced": True,
            "concepts": concepts
        }

    async def save_concept_map(self, course_id: str, concept_map: Dict[str, Any]):
        """Salva la mappa concettuale."""
        try:
            concept_maps = self.concept_service._load_concept_maps()
            concept_maps["concept_maps"][course_id] = concept_map
            self.concept_service._save_concept_maps(concept_maps)
            logger.info(f"✅ Saved concept map with {len(concept_map['concepts'])} concepts")
        except Exception as e:
            logger.error(f"Failed to save concept map: {str(e)}")

async def main():
    """Funzione principale."""
    if len(sys.argv) != 2:
        print("Usage: python enhanced_concept_extractor.py <course_id>")
        sys.exit(1)

    course_id = sys.argv[1]

    extractor = EnhancedConceptExtractor()
    result = await extractor.extract_concepts_from_all_pdfs(course_id)

    print(f"\n{'='*60}")
    print(f"RIEPILOGO ESTRAZIONE CONCETTI AVANZATA")
    print(f"{'='*60}")
    print(f"Course ID: {result['course_id']}")
    print(f"Macro concetti: {result['macro_concepts']}")
    print(f"Capitoli: {result['chapters']}")
    print(f"Concetti totali: {result['total_concepts']}")
    print(f"Generated at: {result['generated_at']}")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())