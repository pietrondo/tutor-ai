import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from .rag_service import RAGService
from .llm_service import LLMService

logger = structlog.get_logger()


class ConceptMapService:
    """Generate and track course concept maps, quizzes and study metrics."""

    def __init__(self) -> None:
        self.rag_service = RAGService()
        self.llm_service = LLMService()
        self.concept_store_path = "data/concept_maps.json"
        self.metrics_store_path = "data/concept_metrics.json"
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.concept_store_path):
            with open(self.concept_store_path, "w", encoding="utf-8") as f:
                json.dump({"concept_maps": {}}, f, ensure_ascii=False, indent=2)
        if not os.path.exists(self.metrics_store_path):
            with open(self.metrics_store_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

    def _load_concept_maps(self) -> Dict[str, Any]:
        with open(self.concept_store_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_concept_maps(self, data: Dict[str, Any]) -> None:
        with open(self.concept_store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_metrics(self) -> Dict[str, Any]:
        with open(self.metrics_store_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_metrics(self, data: Dict[str, Any]) -> None:
        with open(self.metrics_store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def get_or_generate_map(
        self,
        course_id: str,
        *,
        book_id: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        concept_maps = self._load_concept_maps()
        existing = concept_maps["concept_maps"].get(course_id)

        if existing and not force:
            return existing

        generated = await self.generate_concept_map(course_id, book_id=book_id, force=force)
        return generated

    async def generate_concept_map(
        self,
        course_id: str,
        *,
        book_id: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        concept_maps = self._load_concept_maps()
        if not force and course_id in concept_maps["concept_maps"]:
            return concept_maps["concept_maps"][course_id]

        logger.info("Generating concept map", course_id=course_id, book_id=book_id)

        documents_result = await self.rag_service.search_documents(course_id)
        documents = documents_result.get("documents", [])
        if not documents:
            logger.warning("No documents found for concept generation, using fallback concepts")
            # Fallback: genera concetti base basati sul corso
            return await self._generate_fallback_concept_map(course_id, book_id)

        # Aggregate context snippets for LLM
        context_snippets: List[str] = []
        for doc in documents[:5]:
            for chunk in doc.get("chunks", [])[:3]:
                excerpt = chunk.get("content") or chunk.get("text") or ""
                if excerpt:
                    context_snippets.append(f"Fonte: {doc.get('source')} -> {excerpt}")

        context_text = "\n\n".join(context_snippets[:20])

        prompt = f"""
Sei un tutor accademico. Analizza i materiali forniti e genera una mappa di concetti principali per il corso.

Requisiti:
- Restituisci SOLO JSON valido (UTF-8), senza testo extra.
- Ogni concetto deve includere riferimenti al capitolo o sezione del materiale.
- Includi per ogni concetto suggerimenti di apprendimento e domande di autovalutazione.
- I concetti devono essere specifici per studenti universitari.

Schema JSON:
{{
  "course_id": "{course_id}",
  "generated_at": "{datetime.now().isoformat()}",
  "source_count": {len(documents)},
  "concepts": [
    {{
      "id": "string - slug unico",
      "name": "titolo concetto",
      "summary": "breve descrizione (max 3 frasi)",
      "chapter": {{
        "title": "titolo capitolo o sezione",
        "index": 0
      }},
      "related_topics": ["topic1", "topic2"],
      "learning_objectives": ["obiettivo1", "obiettivo2"],
      "suggested_reading": ["riferimento 1"],
      "recommended_minutes": 30,
      "quiz_outline": [
        "Domanda guida 1",
        "Domanda guida 2"
      ]
    }}
  ]
}}

Materiali di riferimento (estratti):
{context_text}
""".strip()

        response_text = await self.llm_service.generate_response(
            query=prompt,
            context={"text": context_text, "sources": []},
            course_id=course_id
        )

        concept_map = self._parse_concept_map(response_text, course_id)
        concept_maps["concept_maps"][course_id] = concept_map
        self._save_concept_maps(concept_maps)

        logger.info(
            "Concept map generated",
            course_id=course_id,
            concepts=len(concept_map.get("concepts", []))
        )
        return concept_map

    async def ensure_concept_quizzes(
        self,
        course_id: str,
        *,
        force_refresh: bool = False,
        quiz_profiles: Optional[List[Dict[str, str]]] = None,
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Ensure each concept for the course has at least one diagnostic and mastery quiz.

        Args:
            course_id: Course identifier.
            force_refresh: If True regenerate all quizzes even if already present.
            quiz_profiles: Optional custom quiz configurations. Each item should
                           provide label and difficulty keys.
            num_questions: Number of questions to request for each quiz.

        Returns:
            Updated concept map with quiz payloads attached to every concept.
        """
        concept_maps = self._load_concept_maps()
        concept_map = concept_maps["concept_maps"].get(course_id)

        if not concept_map:
            concept_map = await self.generate_concept_map(course_id)
            concept_maps = self._load_concept_maps()
            concept_map = concept_maps["concept_maps"].get(course_id, concept_map)

        quiz_configs = quiz_profiles or [
            {"label": "diagnostico", "difficulty": "easy"},
            {"label": "approfondimento", "difficulty": "hard"}
        ]

        updated = False

        for concept in concept_map.get("concepts", []):
            quizzes = concept.get("quizzes")
            if not isinstance(quizzes, list) or force_refresh:
                quizzes = [] if force_refresh else (quizzes or [])
            concept_quizzes: List[Dict[str, Any]] = list(quizzes)

            for profile in quiz_configs:
                label = profile.get("label", "valutazione")
                difficulty = profile.get("difficulty", "medium")

                should_generate = force_refresh or not any(
                    q.get("label") == label for q in concept_quizzes
                )

                if not should_generate:
                    continue

                quiz_payload = await self.llm_service.generate_quiz(
                    course_id=course_id,
                    topic=concept["name"],
                    difficulty=difficulty,
                    num_questions=num_questions
                )

                if not quiz_payload.get("questions"):
                    logger.warning(
                        "Quiz generation failed or returned empty questions",
                        course_id=course_id,
                        concept_id=concept.get("id"),
                        concept_name=concept.get("name"),
                        label=label
                    )
                    continue

                quiz_entry = {
                    "id": uuid.uuid4().hex,
                    "label": label,
                    "difficulty": quiz_payload.get("difficulty", difficulty),
                    "title": quiz_payload.get("title") or f"Quiz {label.title()} - {concept['name']}",
                    "generated_at": datetime.now().isoformat(),
                    "questions": quiz_payload.get("questions"),
                    "source": "plan_generation"
                }

                concept_quizzes.append(quiz_entry)

                # Keep only the three most recent quizzes per label to avoid unbounded growth
                same_label = [q for q in concept_quizzes if q.get("label") == label]
                same_label_sorted = sorted(
                    same_label,
                    key=lambda q: q.get("generated_at", ""),
                    reverse=True
                )
                trimmed_same_label = same_label_sorted[:3]
                other_quizzes = [q for q in concept_quizzes if q.get("label") != label]
                concept_quizzes = other_quizzes + trimmed_same_label
                updated = True

            concept["quizzes"] = concept_quizzes

        if updated:
            concept_maps["concept_maps"][course_id] = concept_map
            self._save_concept_maps(concept_maps)

        return concept_map

    def _parse_concept_map(self, raw_text: str, course_id: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        try:
            cleaned = raw_text.strip()
            if "```" in cleaned:
                start = cleaned.find("```")
                end = cleaned.rfind("```")
                if end > start:
                    cleaned = cleaned[start + 3:end]
                    if cleaned.lower().startswith("json"):
                        cleaned = cleaned[4:].strip()
            data = json.loads(cleaned)
        except Exception as exc:
            logger.error("Failed to parse concept map JSON", error=str(exc))
            data = {}

        concepts = data.get("concepts", [])
        normalized_concepts: List[Dict[str, Any]] = []
        used_ids: Dict[str, int] = {}

        def _slug(text: str) -> str:
            import re
            cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", text)
            cleaned = re.sub(r"[\s_-]+", "-", cleaned.strip().lower())
            return cleaned or uuid.uuid4().hex[:8]

        for item in concepts:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("title") or "").strip()
            if not name:
                continue

            base_id = _slug(name)
            dedup_id = base_id
            if base_id in used_ids:
                used_ids[base_id] += 1
                dedup_id = f"{base_id}-{used_ids[base_id]}"
            else:
                used_ids[base_id] = 0

            chapter = item.get("chapter") or {}
            normalized_concepts.append({
                "id": dedup_id,
                "name": name,
                "summary": str(item.get("summary") or "").strip(),
                "chapter": {
                    "title": str(chapter.get("title") or "Capitolo non specificato").strip(),
                    "index": chapter.get("index")
                },
                "related_topics": [
                    str(topic).strip() for topic in item.get("related_topics", []) if str(topic).strip()
                ],
                "learning_objectives": [
                    str(obj).strip() for obj in item.get("learning_objectives", []) if str(obj).strip()
                ],
                "suggested_reading": [
                    str(ref).strip() for ref in item.get("suggested_reading", []) if str(ref).strip()
                ],
                "recommended_minutes": int(item.get("recommended_minutes") or 30),
                "quiz_outline": [
                    str(q).strip() for q in item.get("quiz_outline", []) if str(q).strip()
                ],
                "quizzes": [
                    {
                        "id": str(quiz.get("id") or uuid.uuid4().hex),
                        "label": str(quiz.get("label") or "valutazione").strip(),
                        "difficulty": str(quiz.get("difficulty") or "").strip() or None,
                        "title": str(quiz.get("title") or f"Quiz - {name}").strip(),
                        "generated_at": str(quiz.get("generated_at") or datetime.now().isoformat()),
                        "questions": quiz.get("questions", []),
                        "source": quiz.get("source", "concept_map")
                    }
                    for quiz in (item.get("quizzes") or [])
                    if isinstance(quiz, dict)
                ]
            })

        return {
            "course_id": course_id,
            "generated_at": datetime.now().isoformat(),
            "concepts": normalized_concepts
        }

    def get_concept_map(self, course_id: str, book_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get concept map for a course, optionally filtered by book"""
        try:
            concept_maps = self._load_concept_maps()

            if book_id:
                # Return book-specific concept map
                if course_id in concept_maps["concept_maps"]:
                    course_data = concept_maps["concept_maps"][course_id]
                    if "books" in course_data and book_id in course_data["books"]:
                        book_map = course_data["books"][book_id]

                        # Check if it's already hierarchical, if not, create hierarchical structure
                        if book_map.get("structure_type") != "hierarchical":
                            logger.info(f"Creating hierarchical structure for book {book_id}")
                            from .hierarchical_concept_service import hierarchical_concept_service

                            # Create hierarchical structure
                            hierarchical_structure = hierarchical_concept_service.create_hierarchical_structure(
                                course_id=course_id,
                                course_name=course_data.get("course_name", "Course"),
                                flat_concepts=book_map.get("concepts", []),
                                book_id=book_id
                            )

                            # Save the new hierarchical structure
                            if "books" not in course_data:
                                course_data["books"] = {}
                            course_data["books"][book_id] = hierarchical_structure
                            self._save_concept_maps(concept_maps)

                            return hierarchical_structure
                        else:
                            return book_map

            else:
                # Return course-wide concept map (all books)
                if course_id in concept_maps["concept_maps"]:
                    course_map = concept_maps["concept_maps"][course_id]

                    # Check if it's already hierarchical, if not, create hierarchical structure
                    if course_map.get("structure_type") != "hierarchical":
                        logger.info(f"Creating hierarchical structure for course {course_id}")
                        from .hierarchical_concept_service import hierarchical_concept_service

                        # Create hierarchical structure
                        hierarchical_structure = hierarchical_concept_service.create_hierarchical_structure(
                            course_id=course_id,
                            course_name=course_map.get("course_name", "Course"),
                            flat_concepts=course_map.get("concepts", []),
                            book_id=None
                        )

                        # Save the new hierarchical structure
                        concept_maps["concept_maps"][course_id] = hierarchical_structure
                        self._save_concept_maps(concept_maps)

                        return hierarchical_structure
                    else:
                        return course_map

        except Exception as e:
            logger.error(f"Error getting concept map: {e}")
        return None

    def get_concept_metrics(self, course_id: str) -> Dict[str, Any]:
        metrics = self._load_metrics()
        return metrics.get(course_id, {})

    def record_quiz_attempt(
        self,
        course_id: str,
        concept_id: str,
        concept_name: str,
        chapter_title: Optional[str],
        *,
        score: float,
        time_seconds: float,
        correct_answers: int,
        total_questions: int
    ) -> Dict[str, Any]:
        metrics = self._load_metrics()
        course_metrics = metrics.setdefault(course_id, {})
        concept_metrics = course_metrics.setdefault(concept_id, {
            "concept_name": concept_name,
            "chapter_title": chapter_title,
            "attempts": [],
            "stats": {
                "average_score": 0.0,
                "average_time_seconds": 0.0,
                "attempts_count": 0,
                "best_score": 0.0,
                "latest_score": 0.0,
                "latest_attempt_at": None
            }
        })

        attempt = {
            "timestamp": datetime.now().isoformat(),
            "score": float(score),
            "time_seconds": float(time_seconds),
            "correct_answers": correct_answers,
            "total_questions": total_questions
        }
        concept_metrics["attempts"].append(attempt)

        stats = concept_metrics["stats"]
        attempts_count = len(concept_metrics["attempts"])
        average_score = sum(a["score"] for a in concept_metrics["attempts"]) / attempts_count
        average_time = sum(a["time_seconds"] for a in concept_metrics["attempts"]) / attempts_count
        best_score = max(a["score"] for a in concept_metrics["attempts"])

        stats.update({
            "average_score": round(average_score, 3),
            "average_time_seconds": round(average_time, 2),
            "attempts_count": attempts_count,
            "best_score": round(best_score, 3),
            "latest_score": round(score, 3),
            "latest_attempt_at": attempt["timestamp"]
        })

        self._save_metrics(metrics)
        return concept_metrics


async def _generate_fallback_concept_map(self, course_id: str, book_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate a fallback concept map when no documents are available."""
    logger.info("Generating fallback concept map", course_id=course_id, book_id=book_id)

    # Concetti universali per corsi universitari
    fallback_concepts = [
        {
            "id": "introduzione",
            "name": "Introduzione al Corso",
            "summary": "Concetti fondamentali e panoramica della materia",
            "chapter": {"title": "Capitolo 1", "index": 1},
            "related_topics": ["concetti base", "terminologia", "obiettivi del corso"],
            "learning_objectives": [
                "Comprendere gli obiettivi principali del corso",
                "Familiarizzare con la terminologia di base",
                "Identificare le aree tematiche principali"
            ],
            "suggested_reading": ["Materiale introduttivo del corso"],
            "recommended_minutes": 30,
            "quiz_outline": [
                "Quali sono gli obiettivi principali di questo corso?",
                "Spiegare i concetti fondamentali introdotti"
            ]
        },
        {
            "id": "concetti-fondamentali",
            "name": "Concetti Fondamentali",
            "summary": "Principi teorici e base della disciplina",
            "chapter": {"title": "Capitolo 2", "index": 2},
            "related_topics": ["teoria principale", "principi base", "fondamenti"],
            "learning_objectives": [
                "Comprendere i principi teorici fondamentali",
                "Applicare i concetti base a problemi semplici",
                "Distinguere tra teoria e pratica"
            ],
            "suggested_reading": ["Testi di riferimento principali"],
            "recommended_minutes": 45,
            "quiz_outline": [
                "Definire i concetti fondamentali della materia",
                "Spiegare l'applicazione dei principi base"
            ]
        },
        {
            "id": "applicazioni-pratiche",
            "name": "Applicazioni Pratiche",
            "summary": "Esercizi e applicazioni reali dei concetti studiati",
            "chapter": {"title": "Capitolo 3", "index": 3},
            "related_topics": ["esercizi", "casi studio", "problemi pratici"],
            "learning_objectives": [
                "Applicare la teoria a problemi pratici",
                "Risolvere esercizi tipici della materia",
                "Analizzare casi studio reali"
            ],
            "suggested_reading": ["Eserciziari e casi studio"],
            "recommended_minutes": 60,
            "quiz_outline": [
                "Risolvere un problema pratico applicando i concetti",
                "Analizzare un caso studio specifico"
            ]
        },
        {
            "id": "approfondimenti",
            "name": "Approfondimenti Tematici",
            "summary": "Argomenti avanzati e aree specialistiche della disciplina",
            "chapter": {"title": "Capitolo 4", "index": 4},
            "related_topics": ["argomenti avanzati", "specializzazioni", "tematiche complesse"],
            "learning_objectives": [
                "Esplorare argomenti avanzati della materia",
                "Comprendere le interconnessioni tra diversi concetti",
                "Sviluppare competenze specialistiche"
            ],
            "suggested_reading": ["Articoli scientifici e testi avanzati"],
            "recommended_minutes": 50,
            "quiz_outline": [
                "Spiegare le relazioni tra concetti avanzati",
                "Applicare conoscenze specialistiche a problemi complessi"
            ]
        },
        {
            "id": "valutazione-e-revisione",
            "name": "Valutazione e Revisione",
            "summary": "Verifica dell'apprendimento e preparazione per esami",
            "chapter": {"title": "Capitolo 5", "index": 5},
            "related_topics": ["verifica", "esercizi di revisione", "preparazione esami"],
            "learning_objectives": [
                "Verificare la comprensione dei concetti principali",
                "Identificare aree che richiedono ulteriore studio",
                "Prepararsi efficacemente per le valutazioni"
            ],
            "suggested_reading": ["Materiale di ripasso e esercizi di valutazione"],
            "recommended_minutes": 40,
            "quiz_outline": [
                "Valutare la comprensione generale della materia",
                "Identificare punti di forza e di debolezza"
            ]
        }
    ]

    fallback_map = {
        "course_id": course_id,
        "generated_at": datetime.now().isoformat(),
        "source_count": 0,
        "is_fallback": True,
        "concepts": fallback_concepts
    }

    # Salva la mappa fallback
    concept_maps = self._load_concept_maps()
    concept_maps["concept_maps"][course_id] = fallback_map
    self._save_concept_maps(concept_maps)

    logger.info(
        "Fallback concept map generated",
        course_id=course_id,
        concepts=len(fallback_concepts)
    )

    return fallback_map


concept_map_service = ConceptMapService()
