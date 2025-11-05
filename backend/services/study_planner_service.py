import json
import math
import re
import unicodedata
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import structlog
from pydantic import BaseModel, Field

from .background_task_service import background_task_service, TaskType, TaskStatus
from .book_service import BookService
from .concept_map_service import concept_map_service
from .llm_service import LLMService
from .rag_service import RAGService

logger = structlog.get_logger()

class StudySession(BaseModel):
    id: str
    title: str
    description: str
    duration_minutes: int
    topics: List[str]
    materials: List[str]
    difficulty: str
    objectives: List[str]
    prerequisites: List[str]
    completion_date: Optional[datetime] = None
    completed: bool = False
    order_index: int
    book_id: Optional[str] = None
    book_title: Optional[str] = None
    chapter_title: Optional[str] = None
    chapter_index: Optional[int] = None
    chapter_summary: Optional[str] = None
    concepts: List[Dict[str, Any]] = Field(default_factory=list)
    quizzes: List[Dict[str, Any]] = Field(default_factory=list)


class MissionTask(BaseModel):
    id: str
    label: str
    type: str
    target_id: Optional[str] = None
    related_session_id: Optional[str] = None
    related_concept_id: Optional[str] = None
    related_quiz_id: Optional[str] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    badge: Optional[str] = None


class StudyMission(BaseModel):
    id: str
    title: str
    description: str
    week_index: int
    start_date: datetime
    end_date: datetime
    progress: float = 0.0
    badge: Optional[str] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    tasks: List[MissionTask] = Field(default_factory=list)

class StudyPlan(BaseModel):
    id: str
    course_id: str
    title: str
    description: str
    total_sessions: int
    estimated_hours: int
    difficulty_progression: str
    created_at: datetime
    updated_at: datetime
    sessions: List[StudySession]
    missions: List[StudyMission] = Field(default_factory=list)
    current_session_index: int = 0
    is_active: bool = True

class StudyPlannerService:
    def __init__(self):
        self.rag_service = RAGService()
        self.llm_service = LLMService()
        self.book_service = BookService()
        self.plans_data_file = "data/study_plans.json"
        self._ensure_data_directory()
        logger.info("Study Planner Service initialized")

    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        import os
        os.makedirs("data", exist_ok=True)

    def _load_plans(self) -> Dict[str, Any]:
        """Load existing study plans from file"""
        try:
            with open(self.plans_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"plans": {}}
        except Exception as e:
            logger.error(f"Error loading study plans: {e}")
            return {"plans": {}}

    def _save_plans(self, plans_data: Dict[str, Any]):
        """Save study plans to file"""
        try:
            with open(self.plans_data_file, 'w', encoding='utf-8') as f:
                json.dump(plans_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving study plans: {e}")
            raise e

    async def generate_study_plan(self, course_id: str, preferences: Dict[str, Any]) -> StudyPlan:
        """Generate a comprehensive study plan that covers all course chapters and concepts."""
        try:
            documents_result = await self.rag_service.search_documents(course_id)
            documents = documents_result.get('documents', [])

            if not documents:
                raise ValueError("No documents found for this course")

            materials_summary: List[Dict[str, Any]] = []
            rag_chapters: List[Dict[str, Any]] = []
            collected_topics: List[str] = []

            for doc in documents:
                materials_summary.append({
                    'source': doc['source'],
                    'chunks_count': doc['total_chunks']
                })

                if doc['source'].lower().endswith('.pdf'):
                    try:
                        structure_analysis = await self._analyze_pdf_chapter_structure(doc['source'], course_id)
                        if structure_analysis['chapters']:
                            for chapter in structure_analysis['chapters']:
                                enriched_chapter = dict(chapter)
                                enriched_chapter['document_source'] = doc['source']
                                rag_chapters.append(enriched_chapter)
                                collected_topics.extend(chapter.get('topics', []))
                                logger.info(
                                    "Chapter topics discovered",
                                    source=doc['source'],
                                    chapter=chapter.get('title'),
                                    topics=len(chapter.get('topics', []))
                                )
                        else:
                            chunk_topics = await self._extract_topics_from_chunks(doc, course_id)
                            collected_topics.extend(chunk_topics)
                    except Exception as exc:
                        logger.error(
                            "Error analyzing chapter structure",
                            source=doc['source'],
                            error=str(exc)
                        )
                        chunk_topics = await self._extract_topics_from_chunks(doc, course_id)
                        collected_topics.extend(chunk_topics)
                else:
                    chunk_topics = await self._extract_topics_from_chunks(doc, course_id)
                    collected_topics.extend(chunk_topics)

            unique_topics = self._unique_preserve_order(collected_topics)[:30]
            book_chapters = self._collect_course_chapters(course_id)

            logger.info(
                "Study plan sources prepared",
                documents=len(documents),
                rag_chapters=len(rag_chapters),
                declared_chapters=len(book_chapters),
                extracted_topics=len(unique_topics)
            )

            refresh_quizzes = preferences.get('refresh_concept_quizzes', True)
            concept_map = await concept_map_service.ensure_concept_quizzes(
                course_id,
                force_refresh=bool(refresh_quizzes)
            )

            sessions = await self._generate_study_sessions(
                course_id=course_id,
                topics=unique_topics,
                materials=materials_summary,
                preferences=preferences,
                concept_map=concept_map,
                book_chapters=book_chapters,
                rag_chapters=rag_chapters
            )

            missions = self._generate_weekly_missions(
                sessions=sessions,
                concept_map=concept_map,
                preferences=preferences
            )

            missions = self._generate_weekly_missions(
                sessions=sessions,
                concept_map=concept_map,
                preferences=preferences
            )

            total_minutes = sum(s.duration_minutes for s in sessions)
            estimated_hours = math.ceil(total_minutes / 60) if total_minutes else 0

            plan = StudyPlan(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title=f"Piano di Studio - {preferences.get('title', 'Generale')}",
                description=f"Piano personalizzato basato su {len(documents)} documenti",
                total_sessions=len(sessions),
                estimated_hours=estimated_hours,
                difficulty_progression=preferences.get('difficulty_progression', 'graduale'),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                sessions=sessions,
                missions=missions
            )

            await self.save_study_plan(plan)

            logger.info(
                "Study plan generated",
                course_id=course_id,
                sessions=len(sessions),
                estimated_hours=estimated_hours
            )
            return plan

        except Exception as e:
            logger.error(f"Error generating study plan: {e}")
            raise e

    async def _generate_study_sessions(
        self,
        course_id: str,
        topics: List[str],
        materials: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        concept_map: Optional[Dict[str, Any]],
        book_chapters: List[Dict[str, Any]],
        rag_chapters: List[Dict[str, Any]]
    ) -> List[StudySession]:
        """Generate individual study sessions using chapter coverage when available."""
        try:
            if book_chapters or rag_chapters:
                return await self._generate_chapter_sessions(
                    course_id=course_id,
                    materials=materials,
                    preferences=preferences,
                    concept_map=concept_map,
                    book_chapters=book_chapters,
                    rag_chapters=rag_chapters
                )

            return await self._generate_topic_sessions(
                course_id=course_id,
                topics=topics,
                materials=materials,
                preferences=preferences,
                concept_map=concept_map
            )

        except Exception as e:
            logger.error(f"Error generating study sessions: {e}")
            raise e

    async def _generate_chapter_sessions(
        self,
        course_id: str,
        materials: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        concept_map: Optional[Dict[str, Any]],
        book_chapters: List[Dict[str, Any]],
        rag_chapters: List[Dict[str, Any]]
    ) -> List[StudySession]:
        difficulty_level = preferences.get('difficulty_level', 'intermediate')
        base_duration = max(int(preferences.get('session_duration', 45)), 30)

        concept_items = concept_map.get("concepts", []) if concept_map else []
        assigned_concepts: set = set()

        rag_by_title: Dict[str, List[Dict[str, Any]]] = {}
        rag_by_number: Dict[int, List[Dict[str, Any]]] = {}
        for chapter in rag_chapters:
            title_key = self._normalize_for_matching(chapter.get("title"))
            if title_key:
                rag_by_title.setdefault(title_key, []).append(chapter)
            number = chapter.get("chapter_number")
            try:
                if number is not None:
                    rag_by_number.setdefault(int(number), []).append(chapter)
            except (TypeError, ValueError):
                continue

        session_specs: List[Dict[str, Any]] = []
        for entry in book_chapters:
            normalized_title = self._normalize_for_matching(entry.get("chapter_title"))
            rag_candidates = rag_by_title.get(normalized_title, [])
            if not rag_candidates and entry.get("chapter_index") is not None:
                rag_candidates = rag_by_number.get(entry["chapter_index"] + 1, [])

            topics = list(entry.get("topics", []))
            estimated_minutes = entry.get("estimated_minutes")
            chapter_summary = entry.get("chapter_summary")

            if rag_candidates:
                rag_best = rag_candidates[0]
                topics.extend(rag_best.get("topics", []))
                if not estimated_minutes:
                    estimated_minutes = rag_best.get("estimated_reading_time")
                if not chapter_summary:
                    chapter_summary = (rag_best.get("content") or "")[:400]

            related_concepts: List[Dict[str, Any]] = []
            for concept in concept_items:
                concept_id = concept.get("id")
                if not concept_id or concept_id in assigned_concepts:
                    continue

                if self._concept_matches_chapter(concept, entry, normalized_title):
                    related_concepts.append(concept)
                    assigned_concepts.add(concept_id)

            session_specs.append({
                "book_id": entry.get("book_id"),
                "book_title": entry.get("book_title"),
                "chapter_title": entry.get("chapter_title"),
                "chapter_index": entry.get("chapter_index"),
                "topics": self._unique_preserve_order(topics),
                "estimated_minutes": estimated_minutes,
                "chapter_summary": chapter_summary,
                "concepts": related_concepts
            })

        leftover_concepts = [
            concept for concept in concept_items
            if concept.get("id") not in assigned_concepts
        ]

        for concept in leftover_concepts:
            session_specs.append({
                "book_id": None,
                "book_title": concept.get("chapter", {}).get("title"),
                "chapter_title": concept.get("name"),
                "chapter_index": None,
                "topics": self._unique_preserve_order(concept.get("related_topics", [])),
                "estimated_minutes": concept.get("recommended_minutes"),
                "chapter_summary": concept.get("summary"),
                "concepts": [concept]
            })

        sessions: List[StudySession] = []
        for index, spec in enumerate(session_specs):
            session = await self._create_session_from_spec(
                course_id=course_id,
                spec=spec,
                materials=materials,
                difficulty_level=difficulty_level,
                base_duration=base_duration,
                order_index=index
            )
            sessions.append(session)

        return sessions

    async def _generate_topic_sessions(
        self,
        course_id: str,
        topics: List[str],
        materials: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        concept_map: Optional[Dict[str, Any]]
    ) -> List[StudySession]:
        sessions_per_week = max(int(preferences.get('sessions_per_week', 3)), 1)
        base_duration = max(int(preferences.get('session_duration', 45)), 30)
        difficulty_level = preferences.get('difficulty_level', 'intermediate')

        ordered_topics = self._unique_preserve_order(topics) or ["Ripasso generale del corso"]
        topics_per_session = max(1, len(ordered_topics) // (sessions_per_week * 4))

        concept_lookup = self._build_concept_lookup(concept_map)

        sessions: List[StudySession] = []
        for index in range(0, len(ordered_topics), topics_per_session):
            session_topics = ordered_topics[index:index + topics_per_session]
            matched_concepts = self._match_topics_to_concepts(session_topics, concept_lookup)

            spec = {
                "book_id": None,
                "book_title": None,
                "chapter_title": session_topics[0] if session_topics else "Sessione di studio",
                "chapter_index": None,
                "topics": session_topics,
                "estimated_minutes": None,
                "chapter_summary": None,
                "concepts": matched_concepts
            }

            session = await self._create_session_from_spec(
                course_id=course_id,
                spec=spec,
                materials=materials,
                difficulty_level=difficulty_level,
                base_duration=base_duration,
                order_index=len(sessions)
            )
            sessions.append(session)

        return sessions

    def _generate_weekly_missions(
        self,
        sessions: List[StudySession],
        concept_map: Optional[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[StudyMission]:
        if not sessions:
            return []

        sessions_per_week = max(1, int(preferences.get('sessions_per_week', 3)))
        total_weeks = max(1, math.ceil(len(sessions) / sessions_per_week))
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        badges = [
            "Kickoff",
            "Momentum",
            "Focus",
            "Mastery"
        ]

        concept_lookup: Dict[str, Dict[str, Any]] = {}
        if concept_map and concept_map.get("concepts"):
            for concept in concept_map["concepts"]:
                if isinstance(concept, dict) and concept.get("id"):
                    concept_lookup[str(concept["id"])] = concept

        missions: List[StudyMission] = []
        for week_index in range(total_weeks):
            week_sessions = sessions[week_index * sessions_per_week:(week_index + 1) * sessions_per_week]
            if not week_sessions:
                continue

            mission_tasks: List[MissionTask] = []
            for session in week_sessions:
                task_id = uuid.uuid4().hex
                mission_tasks.append(MissionTask(
                    id=task_id,
                    label=f"Completa la sessione: {session.title}",
                    type="session",
                    target_id=session.id,
                    related_session_id=session.id
                ))

                for quiz in session.quizzes or []:
                    if not isinstance(quiz, dict):
                        continue
                    quiz_id = quiz.get("quiz_id") or quiz.get("id")
                    label = quiz.get("title") or quiz.get("label") or "Quiz di verifica"
                    related_concept = quiz.get("concept_id") or quiz.get("concept_name")
                    mission_tasks.append(MissionTask(
                        id=uuid.uuid4().hex,
                        label=f"Completa il quiz: {label}",
                        type="quiz",
                        target_id=str(quiz_id) if quiz_id else None,
                        related_session_id=session.id,
                        related_quiz_id=str(quiz_id) if quiz_id else None,
                        related_concept_id=str(related_concept) if related_concept else None
                    ))

                for concept in session.concepts or []:
                    if not isinstance(concept, dict):
                        continue
                    raw_concept_id = concept.get("id") or concept.get("name")
                    if not raw_concept_id:
                        continue
                    concept_id = str(raw_concept_id)
                    details = concept_lookup.get(concept_id)
                    label = (details.get("name") if isinstance(details, dict) else concept.get("name")) or "Concetto chiave"
                    mission_tasks.append(MissionTask(
                        id=uuid.uuid4().hex,
                        label=f"Rivedi il concetto: {label}",
                        type="concept_review",
                        target_id=concept_id,
                        related_session_id=session.id,
                        related_concept_id=concept_id
                    ))

            if not mission_tasks:
                continue

            badge = badges[week_index % len(badges)]
            mission = StudyMission(
                id=uuid.uuid4().hex,
                title=f"Missione Settimana {week_index + 1}",
                description="Completa le attività previste per consolidare i contenuti della settimana.",
                week_index=week_index,
                start_date=start_date + timedelta(weeks=week_index),
                end_date=start_date + timedelta(weeks=week_index, days=6, hours=23, minutes=59),
                badge=badge,
                tasks=mission_tasks
            )
            mission = self._recalculate_mission_progress_model(mission)
            missions.append(mission)

        return missions

    def _recalculate_mission_progress_model(self, mission: StudyMission) -> StudyMission:
        tasks = mission.tasks or []
        total = len(tasks)
        completed = sum(1 for task in tasks if task.completed)
        mission.progress = round((completed / total) if total else 0.0, 3)
        if total > 0 and completed == total:
            mission.completed = True
            if not mission.completed_at:
                mission.completed_at = datetime.now()
        else:
            mission.completed = False
            mission.completed_at = None
        return mission

    def _recalculate_mission_progress_dict(self, mission: Dict[str, Any]):
        tasks = mission.get("tasks") or []
        valid_tasks = [task for task in tasks if isinstance(task, dict)]
        total = len(valid_tasks)
        completed = sum(1 for task in valid_tasks if task.get("completed"))
        progress = (completed / total) if total else 0.0
        mission["progress"] = round(progress, 3)
        if total > 0 and completed == total:
            mission["completed"] = True
            mission.setdefault("completed_at", datetime.now().isoformat())
        else:
            mission["completed"] = False
            mission["completed_at"] = None

    async def _create_session_from_spec(
        self,
        course_id: str,
        spec: Dict[str, Any],
        materials: List[Dict[str, Any]],
        difficulty_level: str,
        base_duration: int,
        order_index: int
    ) -> StudySession:
        concept_payloads = [self._build_concept_payload(concept) for concept in spec.get("concepts", [])]
        concept_names = [c["name"] for c in concept_payloads if c.get("name")]

        topics = self._unique_preserve_order(
            spec.get("topics", []) + concept_names + ([spec.get("chapter_title")] if spec.get("chapter_title") else [])
        )

        aggregated_objectives = self._unique_preserve_order([
            obj for concept in concept_payloads for obj in concept.get("learning_objectives", [])
        ])[:5]

        duration_from_concepts = sum(
            int(concept.get("recommended_minutes") or 0) for concept in concept_payloads
        )
        estimated_minutes = spec.get("estimated_minutes") or 0
        duration_minutes = max(base_duration, duration_from_concepts, estimated_minutes)
        duration_minutes = min(duration_minutes if duration_minutes else base_duration, base_duration * 2)
        if duration_minutes <= 0:
            duration_minutes = base_duration

        materials_list = []
        if spec.get("book_title") or spec.get("chapter_title"):
            book_descriptor_parts = []
            if spec.get("book_title"):
                book_descriptor_parts.append(spec["book_title"])
            if spec.get("chapter_title"):
                book_descriptor_parts.append(spec["chapter_title"])
            materials_list.append(" - ".join(book_descriptor_parts))
        materials_list.extend([m['source'] for m in materials])
        materials_list = self._unique_preserve_order(materials_list)

        session_prompt = f"""
        Sei un tutor accademico universitario. Progetta una sessione di studio per il capitolo "{spec.get('chapter_title') or 'Modulo del corso'}".
        Libro o materiale principale: "{spec.get('book_title') or 'Materiali aggregati del corso'}".
        Concetti chiave: {', '.join(concept_names) if concept_names else 'nessun concetto mappato'}.
        Temi del capitolo: {', '.join(topics)}.
        Obiettivi di apprendimento suggeriti: {', '.join(aggregated_objectives) if aggregated_objectives else 'non specificati'}.
        Durata disponibile: {duration_minutes} minuti.
        Livello di difficoltà richiesto: {difficulty_level}.

        Restituisci esclusivamente JSON valido con la struttura:
        {{
            "title": "Titolo coinvolgente",
            "description": "Descrizione (2-3 frasi) che motivi lo studio",
            "objectives": ["Obiettivo 1", "Obiettivo 2", "Obiettivo 3"],
            "prerequisites": ["Prerequisito 1", "Prerequisito 2"]
        }}
        Limita gli obiettivi a massimo 3 elementi e i prerequisiti a massimo 3 elementi. Usa l'italiano.
        """.strip()

        response = await self.llm_service.generate_response(session_prompt, {}, course_id)

        try:
            session_data = json.loads(response)
        except Exception:
            session_data = {
                "title": spec.get("chapter_title") or "Sessione di studio",
                "description": f"Sessione dedicata a {', '.join(topics)}",
                "objectives": aggregated_objectives[:3] or [
                    "Comprendere i concetti fondamentali",
                    "Applicare la teoria a problemi pratici"
                ],
                "prerequisites": []
            }

        session_quizzes: List[Dict[str, Any]] = []
        for concept in concept_payloads:
            for quiz in concept.get("quizzes", []):
                session_quizzes.append({
                    "concept_id": concept.get("id"),
                    "concept_name": concept.get("name"),
                    "quiz_id": quiz.get("id"),
                    "label": quiz.get("label"),
                    "difficulty": quiz.get("difficulty"),
                    "title": quiz.get("title"),
                    "generated_at": quiz.get("generated_at"),
                    "questions": quiz.get("questions", [])
                })

        return StudySession(
            id=str(uuid.uuid4()),
            title=session_data.get('title', spec.get("chapter_title") or f"Sessione {order_index + 1}"),
            description=session_data.get('description', f"Sessione di studio su {', '.join(topics)}"),
            duration_minutes=duration_minutes,
            topics=topics,
            materials=materials_list,
            difficulty=difficulty_level,
            objectives=session_data.get('objectives', []),
            prerequisites=session_data.get('prerequisites', []),
            order_index=order_index,
            book_id=spec.get("book_id"),
            book_title=spec.get("book_title"),
            chapter_title=spec.get("chapter_title"),
            chapter_index=spec.get("chapter_index"),
            chapter_summary=spec.get("chapter_summary"),
            concepts=concept_payloads,
            quizzes=session_quizzes
        )

    def _build_concept_payload(self, concept: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": concept.get("id"),
            "name": concept.get("name"),
            "summary": concept.get("summary"),
            "chapter": concept.get("chapter"),
            "related_topics": concept.get("related_topics", []),
            "learning_objectives": concept.get("learning_objectives", []),
            "suggested_reading": concept.get("suggested_reading", []),
            "recommended_minutes": concept.get("recommended_minutes"),
            "quiz_outline": concept.get("quiz_outline", []),
            "quizzes": concept.get("quizzes", [])
        }

    def _unique_preserve_order(self, values: List[str]) -> List[str]:
        seen = set()
        ordered: List[str] = []
        for value in values:
            clean = str(value).strip()
            if not clean:
                continue
            key = clean.lower()
            if key not in seen:
                seen.add(key)
                ordered.append(clean)
        return ordered

    def _normalize_for_matching(self, text: Optional[str]) -> str:
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKD", str(text))
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = normalized.lower()
        normalized = re.sub(r'\b(capitolo|chapter|modulo|lezione|unita|unit[aà])\b', ' ', normalized)
        normalized = re.sub(r'[^a-z0-9]+', ' ', normalized)
        return normalized.strip()

    def _collect_course_chapters(self, course_id: str) -> List[Dict[str, Any]]:
        try:
            books = self.book_service.get_books_by_course(course_id)
        except Exception as exc:
            logger.error("Unable to load books for course", course_id=course_id, error=str(exc))
            return []

        chapters: List[Dict[str, Any]] = []
        for book in books:
            chapter_list = book.get("chapters") or []
            for index, raw_chapter in enumerate(chapter_list):
                if isinstance(raw_chapter, dict):
                    title = str(raw_chapter.get("title") or raw_chapter.get("name") or "").strip()
                    summary = str(raw_chapter.get("summary") or "")
                    estimated_minutes = raw_chapter.get("estimated_minutes")
                    topics = raw_chapter.get("topics", [])
                else:
                    title = str(raw_chapter).strip()
                    summary = ""
                    estimated_minutes = None
                    topics = []

                if not title:
                    continue

                chapters.append({
                    "book_id": book.get("id"),
                    "book_title": book.get("title"),
                    "chapter_title": title,
                    "chapter_index": index,
                    "chapter_summary": summary,
                    "estimated_minutes": estimated_minutes,
                    "topics": topics
                })

        return chapters

    def _concept_matches_chapter(
        self,
        concept: Dict[str, Any],
        chapter_entry: Dict[str, Any],
        normalized_chapter_title: str
    ) -> bool:
        chapter_info = concept.get("chapter") or {}

        concept_chapter_title = self._normalize_for_matching(chapter_info.get("title"))
        if concept_chapter_title and normalized_chapter_title:
            if concept_chapter_title == normalized_chapter_title:
                return True

        concept_index = chapter_info.get("index")
        if concept_index is not None and chapter_entry.get("chapter_index") is not None:
            try:
                concept_index_int = int(concept_index)
                if concept_index_int in (chapter_entry["chapter_index"], chapter_entry["chapter_index"] + 1):
                    return True
            except (TypeError, ValueError):
                pass

        concept_name_norm = self._normalize_for_matching(concept.get("name"))
        if concept_name_norm and normalized_chapter_title:
            if concept_name_norm in normalized_chapter_title or normalized_chapter_title in concept_name_norm:
                return True

        return False

    def _build_concept_lookup(self, concept_map: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        lookup: Dict[str, Dict[str, Any]] = {}
        if not concept_map:
            return lookup

        for concept in concept_map.get("concepts", []):
            variants = [
                concept.get("name"),
                concept.get("chapter", {}).get("title"),
            ]
            for variant in variants:
                key = self._normalize_for_matching(variant)
                if key:
                    lookup[key] = concept

        return lookup

    def _match_topics_to_concepts(
        self,
        session_topics: List[str],
        concept_lookup: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        matched: List[Dict[str, Any]] = []
        used_ids: set = set()

        for topic in session_topics:
            normalized_topic = self._normalize_for_matching(topic)
            concept = concept_lookup.get(normalized_topic)
            if not concept:
                concept = next(
                    (candidate for key, candidate in concept_lookup.items()
                     if normalized_topic and (normalized_topic in key or key in normalized_topic)),
                    None
                )

            concept_id = concept.get("id") if concept else None
            if concept and concept_id not in used_ids:
                matched.append(concept)
                used_ids.add(concept_id)

        return matched

    async def refresh_course_plans_with_books(self, course_id: str):
        """Synchronize stored study plans with latest book chapter metadata."""
        try:
            books = self.book_service.get_books_by_course(course_id)
        except Exception as exc:
            logger.error("Unable to load books for plan refresh", course_id=course_id, error=str(exc))
            return

        if not books:
            return

        plans_data = self._load_plans()
        if not plans_data.get("plans"):
            return

        chapter_lookup: Dict[tuple, Dict[str, Any]] = {}
        chapter_only_lookup: Dict[str, Dict[str, Any]] = {}

        for book in books:
            book_title = book.get("title")
            normalized_book = self._normalize_for_matching(book_title)
            chapters = book.get("chapters") or []

            for index, chapter in enumerate(chapters):
                if not isinstance(chapter, dict):
                    continue

                chapter_title = chapter.get("title")
                normalized_chapter = self._normalize_for_matching(chapter_title)
                if not normalized_chapter:
                    continue

                summary = chapter.get("summary") or ""
                estimated = chapter.get("estimated_minutes")
                try:
                    estimated_minutes = int(estimated) if estimated is not None else None
                    if estimated_minutes is not None and estimated_minutes < 0:
                        estimated_minutes = None
                except (TypeError, ValueError):
                    estimated_minutes = None

                info = {
                    "book_title": book_title,
                    "chapter_title": chapter_title,
                    "chapter_summary": summary,
                    "chapter_index": index,
                    "estimated_minutes": estimated_minutes
                }

                chapter_lookup[(normalized_book, normalized_chapter)] = info
                chapter_only_lookup.setdefault(normalized_chapter, info)

        changed = False
        now = datetime.now().isoformat()

        for plan_id, plan_data in plans_data.get("plans", {}).items():
            if plan_data.get("course_id") != course_id:
                continue

            sessions = plan_data.get("sessions") or []
            missions = plan_data.get("missions") or []
            plan_changed = False

            for session in sessions:
                normalized_book = self._normalize_for_matching(session.get("book_title"))
                normalized_chapter = self._normalize_for_matching(session.get("chapter_title"))

                chapter_info = chapter_lookup.get((normalized_book, normalized_chapter))
                if not chapter_info and normalized_chapter:
                    chapter_info = chapter_only_lookup.get(normalized_chapter)

                if not chapter_info:
                    continue

                summary = chapter_info.get("chapter_summary") or ""
                if summary and session.get("chapter_summary") != summary:
                    session["chapter_summary"] = summary
                    plan_changed = True

                if chapter_info.get("book_title") and session.get("book_title") != chapter_info["book_title"]:
                    session["book_title"] = chapter_info["book_title"]
                    plan_changed = True

                if chapter_info.get("chapter_title") and session.get("chapter_title") != chapter_info["chapter_title"]:
                    session["chapter_title"] = chapter_info["chapter_title"]
                    plan_changed = True

                if session.get("chapter_index") != chapter_info.get("chapter_index"):
                    session["chapter_index"] = chapter_info.get("chapter_index")
                    plan_changed = True

                estimated_minutes = chapter_info.get("estimated_minutes")
                if isinstance(estimated_minutes, int) and estimated_minutes > 0:
                    current_duration = int(session.get("duration_minutes") or 0)
                    if current_duration != estimated_minutes:
                        session["duration_minutes"] = estimated_minutes
                        plan_changed = True

                descriptor_parts = []
                if chapter_info.get("book_title"):
                    descriptor_parts.append(chapter_info["book_title"])
                if chapter_info.get("chapter_title"):
                    descriptor_parts.append(chapter_info["chapter_title"])
                if descriptor_parts:
                    descriptor = " - ".join(descriptor_parts)
                    materials = session.get("materials") or []
                    if materials:
                        if materials[0] != descriptor:
                            materials[0] = descriptor
                            session["materials"] = materials
                            plan_changed = True
                    else:
                        session["materials"] = [descriptor]
                        plan_changed = True

                concepts = session.get("concepts") or []
                for concept in concepts:
                    if not isinstance(concept, dict):
                        continue
                    concept_chapter = concept.get("chapter") or {}
                    normalized_concept_chapter = self._normalize_for_matching(
                        concept_chapter.get("title") or concept.get("name")
                    )
                    if normalized_chapter and normalized_concept_chapter == normalized_chapter:
                        if summary and not concept.get("summary"):
                            concept["summary"] = summary
                            plan_changed = True
                        if isinstance(estimated_minutes, int) and estimated_minutes > 0:
                            if concept.get("recommended_minutes") != estimated_minutes:
                                concept["recommended_minutes"] = estimated_minutes
                                plan_changed = True
                        concept.setdefault("chapter", {})["title"] = chapter_info.get("chapter_title")
                        concept["chapter"]["index"] = chapter_info.get("chapter_index")

                session_quizzes = session.get("quizzes") or []
                for quiz in session_quizzes:
                    if not isinstance(quiz, dict):
                        continue
                    if summary and not quiz.get("summary"):
                        quiz["summary"] = summary
                        plan_changed = True

                session_id = session.get("id")
                if session_id and missions:
                    for mission in missions:
                        tasks = mission.get("tasks") or []
                        for task in tasks:
                            if task.get("related_session_id") != session_id:
                                continue
                            if task.get("type") == "session":
                                desired_label = f"Completa la sessione: {session.get('title')}"
                                if task.get("label") != desired_label:
                                    task["label"] = desired_label
                                    plan_changed = True
                            elif task.get("type") == "quiz":
                                related_quiz_id = task.get("related_quiz_id")
                                if related_quiz_id:
                                    for quiz in session_quizzes:
                                        quiz_id = str(quiz.get("quiz_id") or quiz.get("id") or "")
                                        if quiz_id and quiz_id == related_quiz_id:
                                            desired_label = f"Completa il quiz: {quiz.get('title') or quiz.get('label') or 'Quiz di verifica'}"
                                            if task.get("label") != desired_label:
                                                task["label"] = desired_label
                                                plan_changed = True

            if missions:
                for mission in missions:
                    if isinstance(mission, dict):
                        self._recalculate_mission_progress_dict(mission)
                plan_data["missions"] = missions

            if plan_changed:
                durations_sum = sum(int(session.get("duration_minutes") or 0) for session in sessions)
                plan_data["estimated_hours"] = math.ceil(durations_sum / 60) if durations_sum else 0
                plan_data["updated_at"] = now
                changed = True

        if changed:
            self._save_plans(plans_data)

    async def save_study_plan(self, plan: StudyPlan):
        """Save a study plan"""
        try:
            plans_data = self._load_plans()
            plans_data['plans'][plan.id] = plan.dict()
            self._save_plans(plans_data)
            logger.info(f"Saved study plan {plan.id}")
        except Exception as e:
            logger.error(f"Error saving study plan: {e}")
            raise e

    async def get_plan_missions(self, plan_id: str) -> List[StudyMission]:
        plan = await self.get_study_plan(plan_id)
        if not plan:
            raise ValueError("Study plan not found")
        return plan.missions

    async def update_mission_task(
        self,
        plan_id: str,
        mission_id: str,
        task_id: str,
        completed: bool
    ) -> StudyMission:
        plans_data = self._load_plans()
        plan_data = plans_data['plans'].get(plan_id)
        if not plan_data:
            raise ValueError("Study plan not found")

        missions = plan_data.get('missions') or []
        mission_data = next((mission for mission in missions if mission.get('id') == mission_id), None)
        if not mission_data:
            raise ValueError("Mission not found")

        tasks = mission_data.get('tasks') or []
        task_data = next((task for task in tasks if task.get('id') == task_id), None)
        if not task_data:
            raise ValueError("Task not found")

        task_data['completed'] = completed
        task_data['completed_at'] = datetime.now().isoformat() if completed else None

        self._recalculate_mission_progress_dict(mission_data)

        plan_data['missions'] = missions
        plan_data['updated_at'] = datetime.now().isoformat()
        plans_data['plans'][plan_id] = plan_data
        self._save_plans(plans_data)

        return StudyMission(**mission_data)

    async def get_study_plan(self, plan_id: str) -> Optional[StudyPlan]:
        """Get a specific study plan"""
        try:
            plans_data = self._load_plans()
            plan_data = plans_data['plans'].get(plan_id)
            if plan_data:
                return StudyPlan(**plan_data)
            return None
        except Exception as e:
            logger.error(f"Error getting study plan {plan_id}: {e}")
            return None

    async def get_course_study_plans(self, course_id: str) -> List[StudyPlan]:
        """Get all study plans for a course"""
        try:
            plans_data = self._load_plans()
            course_plans = []

            for plan_data in plans_data['plans'].values():
                if plan_data.get('course_id') == course_id:
                    course_plans.append(StudyPlan(**plan_data))

            return sorted(course_plans, key=lambda p: p.created_at, reverse=True)
        except Exception as e:
            logger.error(f"Error getting study plans for course {course_id}: {e}")
            return []

    async def update_session_progress(self, plan_id: str, session_id: str, completed: bool):
        """Update session completion status"""
        try:
            plans_data = self._load_plans()
            plan_data = plans_data['plans'].get(plan_id)

            if not plan_data:
                raise ValueError(f"Study plan {plan_id} not found")

            # Find and update the session
            for session in plan_data['sessions']:
                if session['id'] == session_id:
                    session['completed'] = completed
                    if completed:
                        session['completion_date'] = datetime.now().isoformat()
                    break

            # Update current session index
            if completed:
                for i, session in enumerate(plan_data['sessions']):
                    if not session.get('completed'):
                        plan_data['current_session_index'] = i
                        break
                else:
                    plan_data['current_session_index'] = len(plan_data['sessions']) - 1

            missions = plan_data.get('missions') or []
            if missions:
                for mission in missions:
                    tasks = mission.get('tasks') or []
                    for task in tasks:
                        if task.get('related_session_id') == session_id:
                            task['completed'] = completed
                            task['completed_at'] = datetime.now().isoformat() if completed else None
                    self._recalculate_mission_progress_dict(mission)

            plan_data['missions'] = missions
            plan_data['updated_at'] = datetime.now().isoformat()
            self._save_plans(plans_data)

            logger.info(f"Updated session {session_id} progress for plan {plan_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating session progress: {e}")
            return False

    async def delete_study_plan(self, plan_id: str) -> bool:
        """Delete a study plan"""
        try:
            plans_data = self._load_plans()
            if plan_id in plans_data['plans']:
                del plans_data['plans'][plan_id]
                self._save_plans(plans_data)
                logger.info(f"Deleted study plan {plan_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting study plan {plan_id}: {e}")
            return False

    async def regenerate_plan(self, plan_id: str, preferences: Dict[str, Any]) -> StudyPlan:
        """Regenerate an existing study plan with new preferences"""
        try:
            # Get existing plan
            existing_plan = await self.get_study_plan(plan_id)
            if not existing_plan:
                raise ValueError(f"Study plan {plan_id} not found")

            # Delete old plan
            await self.delete_study_plan(plan_id)

            # Generate new plan
            new_plan = await self.generate_study_plan(existing_plan.course_id, preferences)

            logger.info(f"Regenerated study plan {plan_id} as {new_plan.id}")
            return new_plan

        except Exception as e:
            logger.error(f"Error regenerating study plan: {e}")
            raise e

    async def _analyze_pdf_chapter_structure(self, pdf_path: str, course_id: str) -> Dict[str, Any]:
        """Analyze PDF chapter structure using RAG service"""
        try:
            # Use RAG service to analyze PDF structure
            structure_analysis = self.rag_service.analyze_pdf_structure(pdf_path)
            logger.info(f"Analyzed PDF structure for {pdf_path}: {structure_analysis['total_chapters']} chapters found")
            return structure_analysis
        except Exception as e:
            logger.error(f"Error analyzing PDF chapter structure for {pdf_path}: {e}")
            return {"chapters": [], "total_chapters": 0, "has_toc": False, "structure_detected": False}

    async def _extract_topics_from_chunks(self, doc: Dict[str, Any], course_id: str) -> List[str]:
        """Extract topics from document chunks using LLM analysis"""
        try:
            # Get a sample of chunks to analyze
            chunks_sample = []
            if doc.get('total_chunks', 0) > 0:
                # Get first few chunks for analysis
                for i in range(min(5, doc['total_chunks'])):
                    chunks_sample.append(f"Chunk {i+1}: [Content from {doc['source']}]")

            if not chunks_sample:
                return []

            # Use LLM to extract topics from chunks
            topics_prompt = f"""
            Analyze the following document chunks and extract the main topics and concepts.

            Document: {doc['source']}
            Chunks: {len(chunks_sample)} samples available

            Please provide a list of the main topics covered in this document.
            Focus on:
            1. Key concepts and themes
            2. Technical terms or subject-specific vocabulary
            3. Main subject areas
            4. Important topics that would be studied

            Format as a JSON array of topic strings:
            ["topic1", "topic2", "topic3", ...]

            Limit to 8-10 most important topics.
            """

            response = await self.llm_service.generate_response(topics_prompt, {}, course_id)

            try:
                topics = json.loads(response)
                if isinstance(topics, list):
                    return [str(topic).strip() for topic in topics if str(topic).strip()]
                else:
                    logger.warning(f"LLM response for topics is not a list: {topics}")
                    return []
            except json.JSONDecodeError:
                # Fallback: extract topics using simple text analysis
                logger.warning(f"Failed to parse LLM topics response, using fallback extraction")
                return self._extract_topics_fallback(doc.get('source', ''))

        except Exception as e:
            logger.error(f"Error extracting topics from chunks for {doc['source']}: {e}")
            return []

    def _extract_topics_fallback(self, filename: str) -> List[str]:
        """Fallback topic extraction based on filename"""
        try:
            import re

            # Extract potential topics from filename
            topics = []

            # Common academic subject patterns in Italian
            subject_patterns = [
                r'(matematica|algebra|geometria|calcolo|statistica)',
                r'(fisica|chimica|biologia|scienza)',
                r'(storia|geografia|letteratura|filosofia)',
                r'(informatica|programmazione|computer|algoritmo)',
                r'(economia|finanza|marketing|gestione)',
                r'(diritto|legge|giurisprudenza)',
                r'(psicologia|sociologia|pedagogia)',
                r'(inglese|italiano|lingua|grammatica)'
            ]

            filename_lower = filename.lower()
            for pattern in subject_patterns:
                matches = re.findall(pattern, filename_lower)
                topics.extend(matches)

            # Remove duplicates and capitalize
            unique_topics = list(set(topics))
            return [topic.capitalize() for topic in unique_topics[:5]]  # Max 5 topics

        except Exception as e:
            logger.error(f"Error in fallback topic extraction: {e}")
            return []

    async def generate_study_plan_background(self, course_id: str, preferences: Dict[str, Any],
                                           user_id: Optional[str] = None) -> str:
        """Generate a study plan in background and return task ID"""
        # Create background task
        task_id = background_task_service.create_task(
            task_type=TaskType.STUDY_PLAN_GENERATION,
            course_id=course_id,
            user_id=user_id,
            metadata={
                'preferences': preferences,
                'course_id': course_id
            }
        )

        # Submit the background task
        coro = self._generate_study_plan_with_progress(task_id, course_id, preferences)
        background_task_service.submit_task(task_id, coro)

        logger.info(f"Submitted background study plan generation task {task_id} for course {course_id}")
        return task_id

    async def _generate_study_plan_with_progress(self, task_id: str, course_id: str, preferences: Dict[str, Any]):
        """Generate study plan with progress updates"""
        try:
            # Step 1: Get course documents (20%)
            background_task_service.update_task_status(
                task_id, TaskStatus.RUNNING, progress=10.0,
                message="Recupero documenti del corso..."
            )

            documents_result = await self.rag_service.search_documents(course_id)

            if not documents_result.get('documents'):
                raise ValueError("No documents found for this course")

            background_task_service.update_task_status(
                task_id, TaskStatus.RUNNING, progress=20.0,
                message=f"Trovati {len(documents_result['documents'])} documenti"
            )

            # Step 2: Extract topics and content (40%)
            background_task_service.update_task_status(
                task_id, TaskStatus.RUNNING, progress=25.0,
                message="Analisi struttura PDF ed estrazione argomenti..."
            )

            collected_topics: List[str] = []
            materials_summary: List[Dict[str, Any]] = []
            rag_chapters: List[Dict[str, Any]] = []

            total_docs = len(documents_result['documents'])
            for i, doc in enumerate(documents_result['documents']):
                # Update progress for each document
                doc_progress = 25.0 + (15.0 * (i + 1) / total_docs)

                materials_summary.append({
                    'source': doc['source'],
                    'chunks_count': doc['total_chunks']
                })

                background_task_service.update_task_status(
                    task_id, TaskStatus.RUNNING, progress=doc_progress,
                    message=f"Analisi documento {i+1}/{total_docs}: {doc['source']}"
                )

                # Analyze PDF structure if it's a PDF file
                if doc['source'].lower().endswith('.pdf'):
                    try:
                        structure_analysis = await self._analyze_pdf_chapter_structure(doc['source'], course_id)
                        if structure_analysis['chapters']:
                            for chapter in structure_analysis['chapters']:
                                enriched_chapter = dict(chapter)
                                enriched_chapter['document_source'] = doc['source']
                                rag_chapters.append(enriched_chapter)
                                collected_topics.extend(chapter.get('topics', []))
                                logger.info(
                                    "Background: chapter topics discovered",
                                    source=doc['source'],
                                    chapter=chapter.get('title'),
                                    topics=len(chapter.get('topics', []))
                                )
                        else:
                            chunk_topics = await self._extract_topics_from_chunks(doc, course_id)
                            collected_topics.extend(chunk_topics)
                    except Exception as e:
                        logger.error(f"Error analyzing chapter structure for {doc['source']}: {e}")
                        chunk_topics = await self._extract_topics_from_chunks(doc, course_id)
                        collected_topics.extend(chunk_topics)
                else:
                    chunk_topics = await self._extract_topics_from_chunks(doc, course_id)
                    collected_topics.extend(chunk_topics)

            unique_topics = self._unique_preserve_order(collected_topics)[:30]
            book_chapters = self._collect_course_chapters(course_id)

            background_task_service.update_task_status(
                task_id, TaskStatus.RUNNING, progress=45.0,
                message=f"Estratti {len(unique_topics)} argomenti unici"
            )

            # Step 3: Check if we have chapter data (50%)
            if rag_chapters or book_chapters:
                logger.info(
                    "Background: chapter structure detected",
                    rag_chapters=len(rag_chapters),
                    declared_chapters=len(book_chapters)
                )
                background_task_service.update_task_status(
                    task_id, TaskStatus.RUNNING, progress=50.0,
                    message=f"Rilevati {len(book_chapters) or len(rag_chapters)} capitoli da coprire"
                )
            else:
                logger.info("No chapter structure detected, using topic-based approach")
                background_task_service.update_task_status(
                    task_id, TaskStatus.RUNNING, progress=50.0,
                    message="Nessuna struttura capitoli rilevata, uso approccio basato su argomenti"
                )

            refresh_quizzes = preferences.get('refresh_concept_quizzes', True)
            concept_map = await concept_map_service.ensure_concept_quizzes(
                course_id,
                force_refresh=bool(refresh_quizzes)
            )

            # Step 4: Generate study sessions (80%)
            background_task_service.update_task_status(
                task_id, TaskStatus.RUNNING, progress=55.0,
                message="Generazione sessioni di studio con AI..."
            )

            sessions = await self._generate_study_sessions(
                course_id=course_id,
                topics=unique_topics,
                materials=materials_summary,
                preferences=preferences,
                concept_map=concept_map,
                book_chapters=book_chapters,
                rag_chapters=rag_chapters
            )

            background_task_service.update_task_status(
                task_id, TaskStatus.RUNNING, progress=80.0,
                message=f"Generate {len(sessions)} sessioni di studio"
            )

            # Step 5: Create and save study plan (90%)
            background_task_service.update_task_status(
                task_id, TaskStatus.RUNNING, progress=85.0,
                message="Creazione e salvataggio piano di studio..."
            )

            total_minutes = sum(s.duration_minutes for s in sessions)
            estimated_hours = math.ceil(total_minutes / 60) if total_minutes else 0

            plan = StudyPlan(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title=f"Piano di Studio - {preferences.get('title', 'Generale')}",
                description=f"Piano personalizzato basato su {len(documents_result['documents'])} documenti",
                total_sessions=len(sessions),
                estimated_hours=estimated_hours,
                difficulty_progression=preferences.get('difficulty_progression', 'graduale'),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                sessions=sessions,
                missions=missions
            )

            # Save plan
            await self.save_study_plan(plan)

            background_task_service.update_task_status(
                task_id, TaskStatus.RUNNING, progress=95.0,
                message="Piano di studio salvato con successo"
            )

            # Step 6: Return result (100%)
            result = {
                'study_plan': plan.dict(),
                'sessions_count': len(sessions),
                'estimated_hours': plan.estimated_hours,
                'chapters_detected': len(book_chapters) or len(rag_chapters),
                'rag_chapters_detected': len(rag_chapters),
                'topics_extracted': len(unique_topics),
                'missions_generated': len(missions)
            }

            background_task_service.update_task_status(
                task_id, TaskStatus.COMPLETED, progress=100.0,
                message=f"Piano di studio completato! {len(sessions)} sessioni generate",
                result=result
            )

            logger.info(f"Background study plan generation completed for course {course_id} with {len(sessions)} sessions")
            return result

        except Exception as e:
            logger.error(f"Error in background study plan generation: {e}")
            background_task_service.update_task_status(
                task_id, TaskStatus.FAILED,
                message=f"Errore nella generazione del piano di studio: {str(e)}",
                error=str(e)
            )
            raise e

    def get_background_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a background task"""
        task = background_task_service.get_task(task_id)
        if not task:
            return None

        return {
            'id': task.id,
            'status': task.status,
            'progress': task.progress,
            'message': task.message,
            'result': task.result,
            'error': task.error,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'course_id': task.course_id,
            'task_type': task.task_type
        }

    def get_course_background_tasks(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all background tasks for a course"""
        tasks = background_task_service.get_tasks_by_course(course_id)
        return [
            {
                'id': task.id,
                'status': task.status,
                'progress': task.progress,
                'message': task.message,
                'created_at': task.created_at.isoformat(),
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'task_type': task.task_type
            }
            for task in tasks
        ]
