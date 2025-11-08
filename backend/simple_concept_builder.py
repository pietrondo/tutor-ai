#!/usr/bin/env python3
"""
Script semplice per creare mappe concettuali basate sui materiali PDF esistenti.
"""

import asyncio
import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.concept_map_service import ConceptMapService
import structlog

logger = structlog.get_logger()

class SimpleConceptBuilder:
    def __init__(self):
        self.concept_service = ConceptMapService()

    async def build_concepts_from_materials(self, course_id: str):
        """Costruisci concetti analizzando direttamente i file materials del corso."""
        logger.info(f"Building concepts from materials for course: {course_id}")

        # 1. Carica dati corso da file JSON
        course_data = self.load_course_from_file(course_id)
        if not course_data:
            logger.error(f"Course {course_id} not found")
            return None

        course_name = course_data.get("name", "")
        materials = course_data.get("materials", [])
        # Se non ci sono materials a livello corso, prendili dai libri
        if not materials:
            books = course_data.get("books", [])
            for book in books:
                book_materials = book.get("materials", [])
                materials.extend(book_materials)
                logger.info(f"Added {len(book_materials)} materials from book: {book.get('title', 'Unknown')}")

        logger.info(f"Found {len(materials)} materials for course: {course_name}")

        # 2. Analizza i nomi dei file per estrarre concetti
        pdf_materials = [m for m in materials if m.get("filename", "").endswith(".pdf")]
        logger.info(f"Found {len(pdf_materials)} PDF files")

        # 3. Estrai concetti dai nomi dei file e dal contenuto
        concepts = await self.extract_concepts_from_filenames(course_name, pdf_materials)

        # 4. Crea mappa concettuale completa
        concept_map = {
            "course_id": course_id,
            "course_name": course_name,
            "generated_at": datetime.now().isoformat(),
            "source_count": len(pdf_materials),
            "total_materials": len(materials),
            "extraction_method": "filename_analysis",
            "is_comprehensive": True,
            "concepts": concepts
        }

        # 5. Salva la mappa concettuale
        await self.save_concept_map(course_id, concept_map)

        return {
            "course_id": course_id,
            "course_name": course_name,
            "total_materials": len(materials),
            "pdf_materials": len(pdf_materials),
            "concepts_generated": len(concepts),
            "generated_at": concept_map["generated_at"]
        }

    def load_course_from_file(self, course_id: str) -> Dict[str, Any]:
        """Carica dati del corso dal file JSON."""
        try:
            # Try multiple possible paths
            paths = [
                f"data/courses/courses.json",
                "/app/data/courses/courses.json"
            ]

            courses = []
            for path in paths:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        courses = json.load(f)
                    break

            for course in courses:
                if course.get("id") == course_id:
                    return course

            return None

        except Exception as e:
            logger.error(f"Error loading course data: {str(e)}")
            return None

    async def extract_concepts_from_filenames(self, course_name: str, pdf_materials: List[Dict]) -> List[Dict]:
        """Estrai concetti analizzando i nomi dei file PDF."""
        concepts = []

        # Analizza i pattern nei nomi dei file
        numbered_lessons = []
        thematic_materials = []
        manual_materials = []
        other_materials = []

        for material in pdf_materials:
            filename = material.get("filename", "")

            # Pattern: Geografia #X.pdf o Lezione X.pdf
            if re.search(r'Geografia\s*#\d+\.pdf', filename) or re.search(r'Lezione\s*\d+', filename):
                numbered_lessons.append(material)
            # Pattern: manuali
            elif any(keyword in filename.lower() for keyword in ['manuale', 'manual']):
                manual_materials.append(material)
            # Pattern: tematici specifici
            elif any(keyword in filename.lower() for keyword in ['caboto', 'natura', 'storic', 'finael']):
                thematic_materials.append(material)
            else:
                other_materials.append(material)

        logger.info(f"Categorized materials: {len(numbered_lessons)} lessons, {len(thematic_materials)} thematic, {len(manual_materials)} manuals, {len(other_materials)} other")

        # Genera concetti macro basati sul corso
        if "geografia" in course_name.lower():
            macro_concepts = [
                {
                    "id": "concetti-fondamentali-geografia",
                    "name": "Concetti Fondamentali di Geografia",
                    "summary": "Principi base della geografia, concetti di spazio, territorio e scala geografica",
                    "chapter": {"title": "Fondamenti di Geografia", "index": 1},
                    "related_topics": ["spazio geografico", "territorio", "paesaggio", "scala", "ambiente"],
                    "learning_objectives": [
                        "Comprendere i concetti fondamentali di spazio e territorio",
                        "Distinguere tra diverse scale geografiche",
                        "Analizzare le relazioni tra società e ambiente"
                    ],
                    "suggested_reading": self.extract_manual_titles(manual_materials),
                    "recommended_minutes": 60,
                    "quiz_outline": [
                        "Definire i concetti di spazio geografico e territorio",
                        "Spiegare l'importanza della scala geografica",
                        "Analizzare esempi concreti di organizzazione territoriale"
                    ],
                    "source_materials_count": len(manual_materials)
                },
                {
                    "id": "geografia-storica-sviluppo",
                    "name": "Geografia Storica e Sviluppo Territoriale",
                    "summary": "Evoluzione storica dei territori e processi di sviluppo geografico nel tempo",
                    "chapter": {"title": "Sviluppo Storico", "index": 2},
                    "related_topics": ["evoluzione territoriale", "storia geografica", "cambiamento ambientale", "sviluppo sostenibile"],
                    "learning_objectives": [
                        "Comprendere l'evoluzione dei territori nel tempo",
                        "Analizzare i fattori storici del cambiamento geografico",
                        "Valutare l'impatto umano sull'ambiente storico"
                    ],
                    "suggested_reading": self.extract_thematic_titles(thematic_materials),
                    "recommended_minutes": 75,
                    "quiz_outline": [
                        "Spiegare l'evoluzione storica dei territori",
                        "Analizzare i fattori di cambiamento geografico",
                        "Valutare le relazioni tra storia e geografia"
                    ],
                    "source_materials_count": len(thematic_materials)
                },
                {
                    "id": "metodi-cartografia",
                    "name": "Metodi Cartografici e Analisi Territoriale",
                    "summary": "Strumenti e tecniche per la rappresentazione e analisi dello spazio geografico",
                    "chapter": {"title": "Strumenti di Analisi", "index": 3},
                    "related_topics": ["cartografia", "mappe", "GIS", "coordinate", "rilevamento", "analisi spaziale"],
                    "learning_objectives": [
                        "Utilizzare sistemi di riferimento geografico",
                        "Interpretare diverse tipologie di carte",
                        "Applicare strumenti di analisi territoriale"
                    ],
                    "suggested_reading": self.extract_manual_titles(manual_materials),
                    "recommended_minutes": 65,
                    "quiz_outline": [
                        "Spiegare i sistemi di coordinate geografiche",
                        "Interpretare carte tematiche e topografiche",
                        "Applicare metodi di analisi spaziale"
                    ],
                    "source_materials_count": len(manual_materials)
                }
            ]

            concepts.extend(macro_concepts)

            # Aggiungi concetti basati sulle lezioni numerate
            if numbered_lessons:
                lesson_concept = {
                    "id": "lezioni-tematiche",
                    "name": "Lezioni Tematiche di Geografia",
                    "summary": f"Approfondimenti su {len(numbered_lessons)} temi specifici di geografia",
                    "chapter": {"title": "Lezioni Tematiche", "index": len(macro_concepts) + 1},
                    "related_topics": self.extract_lesson_topics(numbered_lessons),
                    "learning_objectives": [
                        "Approfondire temi specifici di geografia",
                        "Applicare concetti a casi studio concreti",
                        "Sviluppare competenze specialistiche"
                    ],
                    "suggested_reading": [f"Lezioni numerate ({len(numbered_lessons)} files)"],
                    "recommended_minutes": len(numbered_lessons) * 15,  # 15 min per lezione
                    "quiz_outline": [
                        "Analizzare i temi trattati nelle lezioni",
                        "Applicare i concetti geografici a esempi specifici",
                        "Sviluppare analisi tematiche dettagliate"
                    ],
                    "source_materials_count": len(numbered_lessons),
                    "lesson_files": [m.get("filename") for m in numbered_lessons[:10]]  # Show first 10
                }
                concepts.append(lesson_concept)

        # Aggiungi concetti basati su materiali tematici specifici
        if thematic_materials:
            for i, material in enumerate(thematic_materials[:3]):  # Max 3 thematic concepts
                filename = material.get("filename", "")
                concept_name = self.extract_concept_name_from_filename(filename)

                concepts.append({
                    "id": f"tematic-{i+1}",
                    "name": concept_name,
                    "summary": f"Analisi approfondita del tema: {concept_name}",
                    "chapter": {"title": f"Tema Speciale: {concept_name}", "index": len(concepts) + 1},
                    "related_topics": self.extract_keywords_from_filename(filename),
                    "learning_objectives": [
                        f"Comprendere il tema {concept_name}",
                        f"Analizzare gli aspetti chiave del tema",
                        f"Applicare i concetti geografici al tema specifico"
                    ],
                    "suggested_reading": [filename],
                    "recommended_minutes": 45,
                    "quiz_outline": [
                        f"Spiegare i concetti principali di {concept_name}",
                        f"Analizzare le implicazioni geografiche del tema",
                        f"Applicare quanto studiato a esempi concreti"
                    ],
                    "source_materials_count": 1,
                    "source_file": filename
                })

        logger.info(f"Generated {len(concepts)} concepts from materials")
        return concepts

    def extract_manual_titles(self, manual_materials: List[Dict]) -> List[str]:
        """Estrai titoli dai materiali di tipo manuale."""
        titles = []
        for material in manual_materials:
            filename = material.get("filename", "")
            # Pulisci il nome del file
            title = re.sub(r'\.pdf$', '', filename)
            title = re.sub(r'[_\-]', ' ', title)
            titles.append(title)
        return titles[:3] if titles else ["Manuali di geografia"]

    def extract_thematic_titles(self, thematic_materials: List[Dict]) -> List[str]:
        """Estrai titoli dai materiali tematici."""
        titles = []
        for material in thematic_materials:
            filename = material.get("filename", "")
            title = re.sub(r'\.pdf$', '', filename)
            title = re.sub(r'[_\-]', ' ', title)
            titles.append(title)
        return titles[:3] if titles else ["Materiali tematici"]

    def extract_lesson_topics(self, lesson_materials: List[Dict]) -> List[str]:
        """Estrai argomenti dalle lezioni numerate."""
        topics = []
        for material in lesson_materials:
            filename = material.get("filename", "")
            # Estrai numero della lezione
            match = re.search(r'#(\d+)', filename)
            if match:
                lesson_num = match.group(1)
                topics.append(f"Lezione {lesson_num}")
        return topics[:10] if topics else ["Lezioni varie"]

    def extract_concept_name_from_filename(self, filename: str) -> str:
        """Estrai nome del concetto dal filename."""
        # Rimuovi estensione e caratteri speciali
        name = re.sub(r'\.pdf$', '', filename)
        name = re.sub(r'[_\-]', ' ', name)
        name = re.sub(r'\d+', '', name)

        # Capitalizza parole importanti
        words = name.split()
        if words:
            return ' '.join([word.capitalize() for word in words if len(word) > 2])
        return "Tema Specifico"

    def extract_keywords_from_filename(self, filename: str) -> List[str]:
        """Estrai parole chiave dal filename."""
        # Converti in minuscolo e pulisci
        clean_name = re.sub(r'\.pdf$', '', filename.lower())
        clean_name = re.sub(r'[_\-]', ' ', clean_name)

        # Dividi in parole e filtra
        words = [word for word in clean_name.split() if len(word) > 3]
        return words[:5] if words else ["geografia", "territorio"]

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
        print("Usage: python simple_concept_builder.py <course_id>")
        sys.exit(1)

    course_id = sys.argv[1]

    builder = SimpleConceptBuilder()
    result = await builder.build_concepts_from_materials(course_id)

    if result:
        print(f"\n{'='*70}")
        print(f"RIEPILOGO COSTRUZIONE CONCETTI SEMPLICE")
        print(f"{'='*70}")
        print(f"Corso: {result['course_name']}")
        print(f"Materiali totali: {result['total_materials']}")
        print(f"PDF analizzati: {result['pdf_materials']}")
        print(f"Concetti generati: {result['concepts_generated']}")
        print(f"Generato il: {result['generated_at']}")
        print(f"{'='*70}")

        # Mostra dettagli dei concetti
        try:
            builder.concept_service._load_concept_maps()
            maps = builder.concept_service._load_concept_maps()
            saved_map = maps["concept_maps"].get(course_id, {})
            concepts = saved_map.get("concepts", [])

            print(f"\nConcetti principali:")
            for i, concept in enumerate(concepts):
                print(f"{i+1}. {concept.get('name', 'Unknown')}")
                print(f"   - Materiali sorgente: {concept.get('source_materials_count', 0)}")
                print(f"   - Tempo studio: {concept.get('recommended_minutes', 0)} min")
                print(f"   - Argomenti correlati: {len(concept.get('related_topics', []))}")
                print()
        except:
            pass
    else:
        print("❌ Failed to generate concepts")

if __name__ == "__main__":
    asyncio.run(main())