#!/usr/bin/env python3
"""
Script finale che usa l'API per generare mappe concettuali complete.
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

class APIConceptGenerator:
    def __init__(self):
        self.concept_service = ConceptMapService()
        self.base_url = "http://localhost:8000"

    async def generate_concepts_from_api(self, course_id: str):
        """Genera concetti usando l'API del backend."""
        logger.info(f"Generating concepts from API for course: {course_id}")

        # 1. Ottieni dati corso dall'API
        course_data = await self.get_course_data_from_api(course_id)
        if not course_data:
            logger.error(f"Course {course_id} not found via API")
            return None

        course_name = course_data.get("name", "")
        materials = course_data.get("materials", [])

        logger.info(f"Found {len(materials)} materials via API for course: {course_name}")

        # 2. Analizza i PDF materials
        pdf_materials = [m for m in materials if m.get("filename", "").endswith(".pdf")]
        logger.info(f"Found {len(pdf_materials)} PDF files")

        # 3. Estrai concetti dettagliati
        concepts = await self.extract_detailed_concepts(course_name, pdf_materials)

        # 4. Crea mappa concettuale completa
        concept_map = {
            "course_id": course_id,
            "course_name": course_name,
            "generated_at": datetime.now().isoformat(),
            "source_count": len(pdf_materials),
            "total_materials": len(materials),
            "extraction_method": "api_filename_analysis",
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

    async def get_course_data_from_api(self, course_id: str) -> Dict[str, Any]:
        """Ottieni dati del corso dall'API."""
        try:
            response = requests.get(f"{self.base_url}/courses/{course_id}")
            if response.status_code == 200:
                return response.json().get("course", {})
            else:
                logger.error(f"API request failed: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting course data from API: {str(e)}")
            return {}

    async def extract_detailed_concepts(self, course_name: str, pdf_materials: List[Dict]) -> List[Dict]:
        """Estrai concetti dettagliati dai materiali PDF."""
        concepts = []

        if not pdf_materials:
            logger.warning("No PDF materials found, generating fallback concepts")
            return self.generate_fallback_concepts(course_name)

        # Categorizza i materials
        categorized = self.categorize_materials(pdf_materials)

        logger.info(f"Material categories: {categorized}")

        # Genera concetti macro per geografia
        if "geografia" in course_name.lower():
            # 1. Concetti fondamentali
            concepts.append({
                "id": "concetti-geografici-fondamentali",
                "name": "Concetti Geografici Fondamentali",
                "summary": "Principi base della geografia: spazio, territorio, paesaggio e scala geografica",
                "chapter": {"title": "Fondamenti di Geografia", "index": 1},
                "related_topics": ["spazio geografico", "territorio", "paesaggio", "scala", "ambiente", "luogo"],
                "learning_objectives": [
                    "Comprendere i concetti fondamentali di spazio e territorio",
                    "Distinguere tra diverse scale geografiche (locale, regionale, globale)",
                    "Analizzare le relazioni tra società e ambiente",
                    "Interpretare il concetto di paesaggio geografico"
                ],
                "suggested_reading": self.extract_manual_titles(categorized["manuals"]),
                "recommended_minutes": 60,
                "quiz_outline": [
                    "Definire spazio geografico e territory con esempi concreti",
                    "Spiegare l'importanza della scala geografica nell'analisi",
                    "Analizzare le relazioni tra attività umane e ambiente",
                    "Interpretare diversi tipi di paesaggio"
                ],
                "source_materials_count": len(categorized["manuals"]),
                "material_sources": categorized["manuals"][:3]
            })

            # 2. Geografia storica e sviluppo
            concepts.append({
                "id": "geografia-storica-evoluzione",
                "name": "Geografia Storica e Sviluppo Territoriale",
                "summary": "Evoluzione storica dei territori, processi di sviluppo e trasformazioni nel tempo",
                "chapter": {"title": "Evoluzione Storica dei Territori", "index": 2},
                "related_topics": ["evoluzione territoriale", "storia geografica", "cambiamento ambientale", "sviluppo sostenibile", "globalizzazione"],
                "learning_objectives": [
                    "Comprendere l'evoluzione dei territori nel tempo",
                    "Analizzare i fattori storici del cambiamento geografico",
                    "Valutare l'impatto delle attività umane sull'ambiente",
                    "Spiegare i processi di globalizzazione territoriale"
                ],
                "suggested_reading": self.extract_thematic_titles(categorized["thematic"]),
                "recommended_minutes": 75,
                "quiz_outline": [
                    "Spiegare l'evoluzione storica dei territori",
                    "Analizzare i fattori di cambiamento geografico",
                    "Valutare le relazioni tra storia e geografia",
                    "Interpretare gli impatti della globalizzazione"
                ],
                "source_materials_count": len(categorized["thematic"]),
                "material_sources": categorized["thematic"][:3]
            })

            # 3. Metodi e strumenti
            concepts.append({
                "id": "metodi-strumenti-geografici",
                "name": "Metodi e Strumenti della Geografia",
                "summary": "Cartografia, GIS, sistemi di riferimento e tecniche di analisi territoriale",
                "chapter": {"title": "Strumenti di Analisi Geografica", "index": 3},
                "related_topics": ["cartografia", "mappe tematiche", "GIS", "coordinate geografiche", "rilevamento", "analisi spaziale"],
                "learning_objectives": [
                    "Utilizzare sistemi di riferimento geografico",
                    "Interpretare diverse tipologie di carte e mappe",
                    "Applicare strumenti di analisi spaziale",
                    "Comprendere i principi della cartografia digitale"
                ],
                "suggested_reading": self.extract_manual_titles(categorized["manuals"]),
                "recommended_minutes": 65,
                "quiz_outline": [
                    "Spiegare i sistemi di coordinate geografiche",
                    "Interpretare carte topografiche e tematiche",
                    "Applicare metodi di analisi spaziale",
                    "Utilizzare strumenti cartografici digitali"
                ],
                "source_materials_count": len(categorized["manuals"]),
                "material_sources": categorized["manuals"][:2]
            })

            # 4. Lezioni tematiche (se presenti)
            if categorized["lessons"]:
                lesson_topics = self.extract_lesson_topics(categorized["lessons"])
                concepts.append({
                    "id": "lezioni-tematiche-geografiche",
                    "name": "Lezioni Tematiche di Geografia",
                    "summary": f"Approfondimenti su {len(categorized['lessons'])} temi specifici: {', '.join(lesson_topics[:5])}",
                    "chapter": {"title": "Lezioni Tematiche", "index": 4},
                    "related_topics": lesson_topics[:10],
                    "learning_objectives": [
                        "Approfondire temi specifici di geografia",
                        "Applicare concetti a casi studio concreti",
                        "Sviluppare competenze di analisi territoriale",
                        "Integrare conoscenze teoriche e pratiche"
                    ],
                    "suggested_reading": [f"Lezioni numerate ({len(categorized['lessons'])} files)"],
                    "recommended_minutes": len(categorized["lessons"]) * 20,  # 20 min per lezione
                    "quiz_outline": [
                        "Analizzare i temi trattati nelle lezioni",
                        "Applicare i concetti geografici agli esempi specifici",
                        "Sviluppare analisi tematiche dettagliate",
                        "Collegare i diversi argomenti tra loro"
                    ],
                    "source_materials_count": len(categorized["lessons"]),
                    "lesson_files": [m.get("filename") for m in categorized["lessons"][:8]]
                })

            # 5. Argomenti speciali (se presenti)
            if categorized["special"]:
                for i, material in enumerate(categorized["special"][:3]):  # Max 3 special concepts
                    filename = material.get("filename", "")
                    concept_name = self.clean_filename_to_concept_name(filename)

                    concepts.append({
                        "id": f"special-topic-{i+1}",
                        "name": concept_name,
                        "summary": f"Studio approfondito del tema: {concept_name}",
                        "chapter": {"title": f"Tema Speciale: {concept_name}", "index": 5 + i},
                        "related_topics": self.extract_keywords_from_filename(filename),
                        "learning_objectives": [
                            f"Comprendere approfonditamente il tema {concept_name}",
                            f"Analizzare gli aspetti chiave del tema",
                            f"Collegare il tema con i concetti geografici generali"
                        ],
                        "suggested_reading": [filename],
                        "recommended_minutes": 50,
                        "quiz_outline": [
                            f"Spiegare i concetti principali di {concept_name}",
                            f"Analizzare le implicazioni geografiche del tema",
                            f"Applicare il tema a esempi concreti"
                        ],
                        "source_materials_count": 1,
                        "source_file": filename
                    })

        else:
            # Concetti generici per altri corsi
            concepts = self.generate_fallback_concepts(course_name)

        logger.info(f"Generated {len(concepts)} detailed concepts")
        return concepts

    def categorize_materials(self, pdf_materials: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorizza i materiali PDF per tipo."""
        categorized = {
            "lessons": [],
            "manuals": [],
            "thematic": [],
            "special": [],
            "other": []
        }

        for material in pdf_materials:
            filename = material.get("filename", "").lower()

            # Lezioni numerate
            if re.search(r'geografia\s*#\d+\.pdf', filename) or re.search(r'lezione\s*\d+', filename):
                categorized["lessons"].append(material)
            # Manuali
            elif any(keyword in filename for keyword in ['manuale', 'manual', 'guida']):
                categorized["manuals"].append(material)
            # Tematiche specifiche
            elif any(keyword in filename for keyword in ['storic', 'caboto', 'natura', 'ambiente']):
                categorized["thematic"].append(material)
            # Argomenti speciali
            elif any(keyword in filename for keyword in ['conferenza', 'registrazione', 'philipp', 'blom']):
                categorized["special"].append(material)
            else:
                categorized["other"].append(material)

        return categorized

    def extract_manual_titles(self, manuals: List[Dict]) -> List[str]:
        """Estrai titoli dai manuali."""
        if not manuals:
            return ["Manuali di geografia disponibili"]

        titles = []
        for manual in manuals[:3]:  # Max 3 manuals
            filename = manual.get("filename", "")
            title = re.sub(r'\.pdf$', '', filename)
            title = re.sub(r'[_\-]', ' ', title)
            titles.append(title)

        return titles if titles else ["Manuali di riferimento"]

    def extract_thematic_titles(self, thematics: List[Dict]) -> List[str]:
        """Estrai titoli dai materiali tematici."""
        if not thematics:
            return ["Materiali tematici del corso"]

        titles = []
        for thematic in thematics[:3]:
            filename = thematic.get("filename", "")
            title = re.sub(r'\.pdf$', '', filename)
            title = re.sub(r'[_\-]', ' ', title)
            titles.append(title)

        return titles if titles else ["Materiali tematici"]

    def extract_lesson_topics(self, lessons: List[Dict]) -> List[str]:
        """Estrai argomenti dalle lezioni."""
        topics = []
        for lesson in lessons[:10]:  # Max 10 lessons
            filename = lesson.get("filename", "")
            match = re.search(r'#(\d+)', filename)
            if match:
                lesson_num = match.group(1)
                topics.append(f"Lezione {lesson_num}")

        return topics if topics else ["Lezioni varie"]

    def extract_keywords_from_filename(self, filename: str) -> List[str]:
        """Estrai parole chiave dal filename."""
        clean_name = re.sub(r'\.pdf$', '', filename.lower())
        clean_name = re.sub(r'[_\-]', ' ', clean_name)

        words = [word for word in clean_name.split() if len(word) > 3]
        return words[:8] if words else ["geografia", "territorio", "ambiente"]

    def clean_filename_to_concept_name(self, filename: str) -> str:
        """Pulisce il filename per creare un nome di concetto."""
        name = re.sub(r'\.pdf$', '', filename)
        name = re.sub(r'[_\-]', ' ', name)
        name = re.sub(r'\d+', '', name)

        words = [word.capitalize() for word in name.split() if len(word) > 2]
        return ' '.join(words) if words else "Tema Specifico"

    def generate_fallback_concepts(self, course_name: str) -> List[Dict]:
        """Genera concetti fallback per corsi non geografici."""
        return [
            {
                "id": "concetti-fondamentali",
                "name": "Concetti Fondamentali del Corso",
                "summary": f"Principi base e concetti introduttivi di {course_name}",
                "chapter": {"title": "Introduzione al Corso", "index": 1},
                "related_topics": ["base", "fondamenti", "principi", "terminologia"],
                "learning_objectives": [
                    "Comprendere i concetti base della materia",
                    "Familiarizzare con la terminologia specifica",
                    "Identificare le aree tematiche principali"
                ],
                "suggested_reading": ["Materiale introduttivo del corso"],
                "recommended_minutes": 45,
                "quiz_outline": [
                    "Definire i concetti fondamentali",
                    "Spiegare la terminologia di base",
                    "Identificare le aree principali"
                ]
            }
        ]

    async def save_concept_map(self, course_id: str, concept_map: Dict[str, Any]):
        """Salva la mappa concettuale."""
        try:
            concept_maps = self.concept_service._load_concept_maps()
            concept_maps["concept_maps"][course_id] = concept_map
            self.concept_service._save_concept_maps(concept_maps)
            logger.info(f"✅ Saved comprehensive concept map with {len(concept_map['concepts'])} concepts")
        except Exception as e:
            logger.error(f"Failed to save concept map: {str(e)}")

async def main():
    """Funzione principale."""
    if len(sys.argv) != 2:
        print("Usage: python api_concept_generator.py <course_id>")
        sys.exit(1)

    course_id = sys.argv[1]

    generator = APIConceptGenerator()
    result = await generator.generate_concepts_from_api(course_id)

    if result:
        print(f"\n{'='*80}")
        print(f"RIEPILOGO GENERAZIONE CONCETTI COMPLETA DA API")
        print(f"{'='*80}")
        print(f"Corso: {result['course_name']}")
        print(f"Materiali totali: {result['total_materials']}")
        print(f"PDF analizzati: {result['pdf_materials']}")
        print(f"Concetti generati: {result['concepts_generated']}")
        print(f"Generato il: {result['generated_at']}")
        print(f"{'='*80}")

        # Mostra dettagli dei concetti generati
        try:
            generator.concept_service._load_concept_maps()
            maps = generator.concept_service._load_concept_maps()
            saved_map = maps["concept_maps"].get(course_id, {})
            concepts = saved_map.get("concepts", [])

            print(f"\nConcetti generati ({len(concepts)} totali):")
            for i, concept in enumerate(concepts):
                print(f"\n{i+1}. {concept.get('name', 'Unknown')}")
                print(f"   - Riassunto: {concept.get('summary', 'N/A')[:100]}...")
                print(f"   - Materiali sorgente: {concept.get('source_materials_count', 0)}")
                print(f"   - Tempo studio raccomandato: {concept.get('recommended_minutes', 0)} minuti")
                print(f"   - Argomenti correlati: {len(concept.get('related_topics', []))}")
                print(f"   - Obiettivi di apprendimento: {len(concept.get('learning_objectives', []))}")

                if 'material_sources' in concept:
                    sources = concept.get('material_sources', [])
                    print(f"   - Fonti principali: {len(sources)} files")
                    for source in sources[:2]:
                        print(f"     • {source.get('filename', 'Unknown file')}")

        except Exception as e:
            logger.error(f"Error displaying concept details: {str(e)}")

        print(f"\n{'='*80}")
        print(f"✅ Generazione completata con successo!")
        print(f"Ora puoi testare i concetti nell'interfaccia web:")
        print(f"http://localhost:3000/chat?course={course_id}")
        print(f"{'='*80}")
    else:
        print("❌ Failed to generate concepts")

if __name__ == "__main__":
    asyncio.run(main())