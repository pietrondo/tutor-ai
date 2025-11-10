"""
Knowledge Area Service
Automatically extracts knowledge areas from uploaded materials and generates adaptive quizzes
Integrates with chat to provide contextual assessments
"""

import json
import uuid
import asyncio
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import structlog
from services.rag_service import RAGService
from services.active_recall_service import ActiveRecallEngine, QuestionGenerationRequest
from services.llm_service import LLMService

logger = structlog.get_logger()

@dataclass
class Concept:
    """Represents a single concept with learning progress"""
    id: str
    name: str
    description: str
    keywords: List[str]
    difficulty_level: float  # 0.0-1.0
    mastery_level: float  # User's mastery level 0.0-1.0
    confidence_level: float  # User's confidence 0.0-1.0
    last_studied: Optional[datetime]
    study_count: int
    quiz_count: int
    material_sources: List[str]
    parent_concept_id: Optional[str] = None  # For hierarchical structure
    sub_concept_ids: List[str] = None  # Child concepts
    position_x: float = 0.0  # For visualization
    position_y: float = 0.0  # For visualization

    def __post_init__(self):
        if self.sub_concept_ids is None:
            self.sub_concept_ids = []

@dataclass
class KnowledgeArea:
    """Represents a knowledge area with main concepts and sub-concepts"""
    id: str
    name: str
    description: str
    main_concepts: List[str]  # IDs of main concepts
    all_concepts: Dict[str, Concept]  # All concepts by ID
    difficulty_level: float  # 0.0-1.0
    coverage_score: float  # How much material covers this area
    mastery_level: float  # Overall mastery level 0.0-1.0
    last_updated: Optional[datetime]
    material_sources: List[str]  # PDF files, documents

    def get_main_concepts(self) -> List[Concept]:
        """Get main concepts (no parent)"""
        return [self.all_concepts[concept_id] for concept_id in self.main_concepts
                if concept_id in self.all_concepts]

    def get_sub_concepts(self, parent_id: str) -> List[Concept]:
        """Get sub-concepts of a specific concept"""
        parent = self.all_concepts.get(parent_id)
        if not parent:
            return []
        return [self.all_concepts[sub_id] for sub_id in parent.sub_concept_ids
                if sub_id in self.all_concepts]

    def add_concept(self, concept: Concept, is_main: bool = False):
        """Add a new concept to the knowledge area"""
        self.all_concepts[concept.id] = concept
        if is_main and concept.id not in self.main_concepts:
            self.main_concepts.append(concept.id)
        elif concept.parent_concept_id:
            # Add to parent's sub-concepts
            parent = self.all_concepts.get(concept.parent_concept_id)
            if parent and concept.id not in parent.sub_concept_ids:
                parent.sub_concept_ids.append(concept.id)

    def calculate_overall_mastery(self):
        """Calculate overall mastery based on all concepts"""
        if not self.all_concepts:
            self.mastery_level = 0.0
            return

        total_mastery = sum(concept.mastery_level for concept in self.all_concepts.values())
        self.mastery_level = total_mastery / len(self.all_concepts)

@dataclass
class LearningProgress:
    """Tracks learning progress across knowledge areas"""
    user_id: str
    course_id: str
    area_id: str
    mastery_level: float
    confidence_level: float
    correct_answers: int
    total_answers: int
    last_activity: datetime
    improvement_trend: float  # Positive if improving
    recommended_difficulty: float

@dataclass
class QuizRecommendation:
    """Recommended quiz for a specific knowledge area"""
    area_id: str
    area_name: str
    quiz_type: str  # assessment, practice, challenge
    difficulty: float
    num_questions: int
    rationale: str
    time_estimate_minutes: int

@dataclass
class ConceptVisualization:
    """Data for concept visualization"""
    concept_id: str
    name: str
    x: float
    y: float
    size: float  # Node size based on importance
    color: str  # Color based on mastery level
    mastery_level: float
    has_sub_concepts: bool
    parent_id: Optional[str]

@dataclass
class ConnectionVisualization:
    """Data for connections between concepts"""
    from_concept_id: str
    to_concept_id: str
    strength: float  # Connection strength
    relationship_type: str  # "prerequisite", "related", "hierarchy"

class KnowledgeAreaService:
    """Service for managing knowledge areas and adaptive assessments"""

    def __init__(self, rag_service: RAGService, llm_service: LLMService, active_recall_engine: ActiveRecallEngine):
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.active_recall_engine = active_recall_engine

        # Persistent storage for knowledge areas
        self.data_dir = self._resolve_data_dir()
        self.knowledge_areas_dir = os.path.join(self.data_dir, "knowledge_areas")
        os.makedirs(self.knowledge_areas_dir, exist_ok=True)
        self.knowledge_areas_file = os.path.join(self.knowledge_areas_dir, "knowledge_areas.json")

        # Storage for knowledge areas and progress
        self.knowledge_areas: Dict[str, Dict[str, KnowledgeArea]] = {}  # course_id -> area_id -> area
        self.learning_progress: Dict[str, List[LearningProgress]] = {}  # user_id -> progress

        # Configuration
        self.max_areas_per_course = 15
        self.min_material_coverage = 0.1  # Minimum coverage to consider an area valid

        # Load existing data
        self.load_knowledge_areas()

        logger.info("Knowledge Area Service initialized")

    def _resolve_data_dir(self) -> str:
        """
        Determine a writable data directory.
        Prefers DATA_DIR env var, falls back to repo-relative backend/data.
        """
        default_dir = Path(__file__).resolve().parent.parent / "data"
        env_dir = os.environ.get("DATA_DIR")
        candidate_dirs = []

        if env_dir:
            candidate_dirs.append(Path(env_dir).expanduser())
        candidate_dirs.append(default_dir)

        for directory in candidate_dirs:
            resolved_dir = directory if directory.is_absolute() else (Path.cwd() / directory)
            try:
                resolved_dir.mkdir(parents=True, exist_ok=True)
                return str(resolved_dir)
            except PermissionError:
                logger.warning(f"Permission denied for data directory '{resolved_dir}'. Trying fallback.")

        raise PermissionError("Unable to access any writable data directory for KnowledgeAreaService.")

    async def extract_main_concepts_fast(self, course_id: str, book_id: Optional[str] = None) -> KnowledgeArea:
        """Extract main concepts quickly from course materials"""
        try:
            logger.info(f"Fast extracting main concepts for course {course_id}")

            # Quick content sampling
            content_prompt = """
            Identifica SOLO i 5-7 concetti principali più importanti di questo corso.

            Restituisci JSON semplice:
            {
                "course_name": "Nome del corso",
                "main_concepts": [
                    {
                        "name": "Nome concetto",
                        "description": "Breve descrizione (max 50 parole)",
                        "keywords": ["keyword1", "keyword2"],
                        "difficulty": 0.5
                    }
                ]
            }
            """

            rag_response = await self.rag_service.retrieve_context(
                content_prompt,
                course_id=course_id,
                book_id=book_id,
                k=8  # Smaller sample for speed
            )

            if not rag_response.get("text"):
                logger.warning(f"No content found for course {course_id}")
                return self._create_fallback_knowledge_area(course_id, rag_response.get("sources", []))

            # Fast LLM extraction
            extraction_prompt = f"""
            Analizza rapidamente questo materiale ed estrai SOLO i concetti principali.

            MATERIALE:
            {rag_response["text"][:2000]}  # Limit for speed

            FONTI:
            {[source.get("source", "Unknown") for source in rag_response.get("sources", [])[:5]]}

            {content_prompt}
            """

            llm_response = await self.llm_service.generate_response(
                query=extraction_prompt,
                context={"text": rag_response["text"][:2000]},
                course_id=course_id
            )

            logger.info(f"Fast LLM response: {llm_response[:200]}...")

            # Parse and create knowledge area with main concepts
            try:
                if not llm_response or llm_response.strip() == "":
                    logger.error("Empty LLM response for fast extraction")
                    return self._create_fallback_knowledge_area(course_id, rag_response.get("sources", []))

                llm_data = json.loads(llm_response)

                # Create knowledge area
                knowledge_area = KnowledgeArea(
                    id=f"{course_id}_main",
                    name=llm_data.get("course_name", "Area di Conoscenza Principale"),
                    description="Concetti principali del corso con sotto-concetti dinamici",
                    main_concepts=[],
                    all_concepts={},
                    difficulty_level=0.5,
                    coverage_score=0.8,
                    mastery_level=0.0,
                    last_updated=datetime.now(),
                    material_sources=[source.get("source", "Unknown") for source in rag_response.get("sources", [])]
                )

                # Add main concepts with automatic positioning
                main_concepts = llm_data.get("main_concepts", [])
                for i, concept_data in enumerate(main_concepts[:7]):  # Max 7 main concepts
                    angle = (2 * 3.14159 * i) / len(main_concepts)
                    radius = 200

                    concept = Concept(
                        id=f"{course_id}_concept_{i}",
                        name=concept_data["name"],
                        description=concept_data["description"],
                        keywords=concept_data.get("keywords", []),
                        difficulty_level=concept_data.get("difficulty", 0.5),
                        mastery_level=0.0,
                        confidence_level=0.0,
                        last_studied=None,
                        study_count=0,
                        quiz_count=0,
                        material_sources=[source.get("source", "Unknown") for source in rag_response.get("sources", [])],
                        parent_concept_id=None,
                        sub_concept_ids=[],
                        position_x=radius * 0.8 * (1 if angle == 0 else 0.7),  # Center with slight spread
                        position_y=radius * 0.6 * (0 if i % 2 == 0 else 0.5)  # Alternating height
                    )

                    knowledge_area.add_concept(concept, is_main=True)

                # Store the knowledge area
                if course_id not in self.knowledge_areas:
                    self.knowledge_areas[course_id] = {}

                self.knowledge_areas[course_id][knowledge_area.id] = knowledge_area
                self.save_knowledge_areas()

                logger.info(f"Extracted {len(main_concepts)} main concepts for course {course_id}")
                return knowledge_area

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response: {e}")
                return self._create_fallback_knowledge_area(course_id, rag_response.get("sources", []))

        except Exception as e:
            logger.error(f"Error in fast concept extraction: {e}")
            return self._create_fallback_knowledge_area(course_id, [])

    def load_knowledge_areas(self):
        """Load knowledge areas from persistent storage"""
        try:
            if os.path.exists(self.knowledge_areas_file):
                with open(self.knowledge_areas_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert dictionaries back to KnowledgeArea objects
                    for course_id, areas_dict in data.get("knowledge_areas", {}).items():
                        self.knowledge_areas[course_id] = {}
                        for area_id, area_data in areas_dict.items():
                            # Handle new hierarchical format
                            if "main_concepts" in area_data and "all_concepts" in area_data:
                                # New format - convert concepts back to Concept objects
                                all_concepts = {}
                                for concept_id, concept_data in area_data["all_concepts"].items():
                                    # Convert datetime strings back
                                    if concept_data.get("last_studied"):
                                        concept_data["last_studied"] = datetime.fromisoformat(concept_data["last_studied"])

                                    # Ensure required fields exist
                                    if "sub_concept_ids" not in concept_data:
                                        concept_data["sub_concept_ids"] = []
                                    if "parent_concept_id" not in concept_data:
                                        concept_data["parent_concept_id"] = None

                                    all_concepts[concept_id] = Concept(**concept_data)

                                # Convert last_updated
                                if area_data.get("last_updated"):
                                    area_data["last_updated"] = datetime.fromisoformat(area_data["last_updated"])

                                knowledge_area = KnowledgeArea(
                                    id=area_data["id"],
                                    name=area_data["name"],
                                    description=area_data["description"],
                                    main_concepts=area_data["main_concepts"],
                                    all_concepts=all_concepts,
                                    difficulty_level=area_data["difficulty_level"],
                                    coverage_score=area_data["coverage_score"],
                                    mastery_level=area_data["mastery_level"],
                                    last_updated=area_data.get("last_updated"),
                                    material_sources=area_data["material_sources"]
                                )

                                self.knowledge_areas[course_id][area_id] = knowledge_area
                            else:
                                # Old format - convert to new format for compatibility
                                logger.warning(f"Loading old format knowledge area {area_id}, converting to new format")
                                if area_data.get("last_assessed"):
                                    area_data["last_assessed"] = datetime.fromisoformat(area_data["last_assessed"])

                                # Create minimal knowledge area from old format
                                knowledge_area = KnowledgeArea(
                                    id=area_data["id"],
                                    name=area_data["name"],
                                    description=area_data["description"],
                                    main_concepts=[],
                                    all_concepts={},
                                    difficulty_level=area_data.get("difficulty_level", 0.5),
                                    coverage_score=area_data.get("coverage_score", 0.5),
                                    mastery_level=area_data.get("mastery_level", 0.0),
                                    last_updated=None,
                                    material_sources=area_data.get("material_sources", [])
                                )

                                self.knowledge_areas[course_id][area_id] = knowledge_area

                    # Load learning progress
                    for user_id, progress_list in data.get("learning_progress", {}).items():
                        self.learning_progress[user_id] = []
                        for progress_data in progress_list:
                            if progress_data.get("last_activity"):
                                progress_data["last_activity"] = datetime.fromisoformat(progress_data["last_activity"])
                            self.learning_progress[user_id].append(LearningProgress(**progress_data))

                    logger.info(f"Loaded knowledge areas for {len(self.knowledge_areas)} courses")
            else:
                logger.info("No existing knowledge areas file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading knowledge areas: {e}")
            # Continue with empty knowledge areas

    def save_knowledge_areas(self):
        """Save knowledge areas to persistent storage"""
        try:
            data = {
                "knowledge_areas": {},
                "learning_progress": {},
                "last_updated": datetime.now().isoformat()
            }

            # Convert knowledge areas to dictionaries
            for course_id, areas_dict in self.knowledge_areas.items():
                data["knowledge_areas"][course_id] = {}
                for area_id, area in areas_dict.items():
                    area_dict = asdict(area)
                    # Convert datetime to ISO string for new format
                    if area_dict.get("last_updated"):
                        area_dict["last_updated"] = area.last_updated.isoformat()

                    # Convert concept datetime fields
                    if "all_concepts" in area_dict:
                        for concept_id, concept_dict in area_dict["all_concepts"].items():
                            if concept_dict.get("last_studied"):
                                concept_dict["last_studied"] = concept_dict["last_studied"].isoformat()

                    data["knowledge_areas"][course_id][area_id] = area_dict

            # Convert learning progress to dictionaries
            for user_id, progress_list in self.learning_progress.items():
                data["learning_progress"][user_id] = []
                for progress in progress_list:
                    progress_dict = asdict(progress)
                    if progress_dict.get("last_activity"):
                        progress_dict["last_activity"] = progress.last_activity.isoformat()
                    data["learning_progress"][user_id].append(progress_dict)

            # Write to file
            with open(self.knowledge_areas_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("Knowledge areas saved successfully")
        except Exception as e:
            logger.error(f"Error saving knowledge areas: {e}")

    async def extract_knowledge_areas_from_course(self, course_id: str, book_id: Optional[str] = None) -> List[KnowledgeArea]:
        """Extract knowledge areas from course materials using RAG and AI analysis"""
        try:
            logger.info(f"Extracting knowledge areas for course {course_id}, book {book_id}")

            # Step 1: Get comprehensive content from RAG
            content_prompt = """
            Analizza i materiali di questo corso e identifica le aree di conoscenza principali.
            Fornisci un elenco strutturato di argomenti, concetti e temi che dovrebbero essere studiati.

            Concentrati su:
            1. Argomenti principali e temi centrali
            2. Concetti chiave e terminologia importante
            3. Abilità e competenze da sviluppare
            4. Relazioni tra diversi argomenti
            5. Livelli di difficoltà progressivi

            Formato risposta come JSON valido:
            {
                "areas": [
                    {
                        "name": "Nome area",
                        "description": "Descrizione dettagliata",
                        "keywords": ["keyword1", "keyword2"],
                        "difficulty": 0.5,
                        "concepts": ["concetto1", "concetto2"]
                    }
                ]
            }
            """

            rag_response = await self.rag_service.retrieve_context(
                content_prompt,
                course_id=course_id,
                book_id=book_id,
                k=15  # Get comprehensive content
            )

            if not rag_response.get("text"):
                logger.warning(f"No content found for course {course_id}")
                return []

            # Step 2: Use LLM to extract structured knowledge areas
            extraction_prompt = f"""
            Sei un esperto in didattica e analisi dei contenuti. Analizza il seguente materiale didattico
            ed estrai le aree di conoscenza principali per questo corso.

            MATERIALE:
            {rag_response["text"]}

            FONTI:
            {rag_response.get("sources", [])}

            Estrai esattamente 8-12 aree di conoscenza principali che coprono il contenuto del corso.
            Per ogni area fornisci:
            - Nome chiaro e specifico
            - Descrizione dettagliata
            - Parole chiave rilevanti
            - Livello di difficoltà (0.1 facile, 0.9 molto difficile)
            - Concetti chiave da imparare

            Rispondi SOLO con JSON valido:
            {{
                "areas": [
                    {{
                        "name": "Nome area",
                        "description": "Descrizione",
                        "keywords": ["keyword1", "keyword2"],
                        "difficulty": 0.5,
                        "concepts": ["concetto1", "concetto2"]
                    }}
                ]
            }}
            """

            llm_response = await self.llm_service.generate_response(
                query=extraction_prompt,
                context={"text": rag_response["text"]},
                course_id=course_id
            )

            logger.info(f"LLM response received: {llm_response[:200]}...")

            # Step 3: Parse and create knowledge areas
            try:
                if not llm_response or llm_response.strip() == "":
                    logger.error("Empty LLM response received")
                    # Create fallback knowledge areas based on content analysis
                    areas = self._create_fallback_knowledge_areas(course_id, rag_response["text"], rag_response.get("sources", []))
                else:
                    llm_data = json.loads(llm_response)
                    areas = []

                    for i, area_data in enumerate(llm_data.get("areas", [])):
                        area = KnowledgeArea(
                        id=f"{course_id}_area_{i}",
                        name=area_data["name"],
                        description=area_data["description"],
                        keywords=area_data.get("keywords", []),
                        difficulty_level=area_data.get("difficulty", 0.5),
                        prerequisite_areas=[],
                        related_areas=[],
                        material_sources=[source["source"] for source in rag_response.get("sources", [])],
                        coverage_score=self._calculate_coverage_score(area_data, rag_response["text"]),
                        mastery_level=0.0,  # Start with no mastery
                        last_assessed=None,
                        assessment_count=0,
                        quiz_questions_available=0,
                        concepts=area_data.get("concepts", [])
                    )
                    areas.append(area)

                # Step 4: Establish relationships between areas
                self._establish_area_relationships(areas)

                # Step 5: Store areas
                if course_id not in self.knowledge_areas:
                    self.knowledge_areas[course_id] = {}

                for area in areas:
                    self.knowledge_areas[course_id][area.id] = area

                # Step 6: Save to persistent storage
                self.save_knowledge_areas()

                logger.info(f"Extracted {len(areas)} knowledge areas for course {course_id}")
                return areas

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response: {e}")
                logger.error(f"LLM response: {llm_response}")
                return []

        except Exception as e:
            logger.error(f"Error extracting knowledge areas: {e}")
            return []

    def _calculate_coverage_score(self, area_data: Dict[str, Any], content_text: str) -> float:
        """Calculate how well the content covers this knowledge area"""
        try:
            area_keywords = area_data.get("keywords", [])
            area_concepts = area_data.get("concepts", [])
            all_terms = area_keywords + area_concepts

            if not all_terms:
                return 0.5  # Default coverage

            content_lower = content_text.lower()
            matches = sum(1 for term in all_terms if term.lower() in content_lower)
            coverage = min(matches / len(all_terms), 1.0)

            return max(coverage, self.min_material_coverage)
        except Exception:
            return 0.5

    def _establish_area_relationships(self, areas: List[KnowledgeArea]):
        """Establish prerequisite and related area relationships"""
        for i, area in enumerate(areas):
            # Simple heuristic: areas with similar keywords are related
            for j, other_area in enumerate(areas):
                if i != j:
                    keyword_overlap = len(set(area.keywords) & set(other_area.keywords))
                    total_keywords = len(set(area.keywords) | set(other_area.keywords))

                    if keyword_overlap > 0:
                        similarity = keyword_overlap / total_keywords
                        if similarity > 0.3:  # 30% overlap or more
                            if other_area.id not in area.related_areas:
                                area.related_areas.append(other_area.id)

                            # Establish prerequisite based on difficulty
                            if area.difficulty_level < other_area.difficulty_level and similarity > 0.5:
                                if other_area.id not in area.prerequisite_areas:
                                    area.prerequisite_areas.append(other_area.id)

    async def generate_quiz_for_area(self, course_id: str, area_id: str, user_id: str,
                                    num_questions: int = 5, difficulty_override: Optional[float] = None) -> QuizRecommendation:
        """Generate a quiz recommendation for a specific knowledge area"""
        try:
            if course_id not in self.knowledge_areas or area_id not in self.knowledge_areas[course_id]:
                raise ValueError(f"Knowledge area {area_id} not found for course {course_id}")

            area = self.knowledge_areas[course_id][area_id]

            # Get user's current progress for this area
            user_progress = self._get_user_progress(user_id, area_id)

            # Calculate adaptive difficulty
            if difficulty_override:
                difficulty = difficulty_override
            else:
                difficulty = self._calculate_adaptive_difficulty(area, user_progress)

            # Determine quiz type based on mastery
            quiz_type = self._determine_quiz_type(user_progress)

            # Generate contextual quiz using Active Recall Engine
            content_for_quiz = self._prepare_content_for_quiz(course_id, area)

            quiz_request = QuestionGenerationRequest(
                course_id=course_id,
                content=content_for_quiz,
                concept_id=area_id,
                difficulty_target=difficulty,
                num_questions=num_questions,
                bloom_levels=self._select_bloom_levels(user_progress.mastery_level),
                context_tags=area.keywords
            )

            # Generate quiz questions
            quiz_response = await self.active_recall_engine.generate_questions(quiz_request)

            # Update area with available questions
            area.quiz_questions_available = len(quiz_response.get("questions", []))
            area.last_assessed = datetime.now()
            area.assessment_count += 1

            return QuizRecommendation(
                area_id=area_id,
                area_name=area.name,
                quiz_type=quiz_type,
                difficulty=difficulty,
                num_questions=num_questions,
                rationale=self._generate_quiz_rationale(area, user_progress),
                time_estimate_minutes=num_questions * 2  # 2 minutes per question average
            )

        except Exception as e:
            logger.error(f"Error generating quiz for area {area_id}: {e}")
            raise

    def _get_user_progress(self, user_id: str, area_id: str) -> LearningProgress:
        """Get user's progress for a specific knowledge area"""
        if user_id not in self.learning_progress:
            return LearningProgress(
                user_id=user_id,
                course_id="",
                area_id=area_id,
                mastery_level=0.0,
                confidence_level=0.0,
                correct_answers=0,
                total_answers=0,
                last_activity=datetime.now(),
                improvement_trend=0.0,
                recommended_difficulty=0.3
            )

        progress_list = self.learning_progress[user_id]
        for progress in progress_list:
            if progress.area_id == area_id:
                return progress

        # Create new progress entry
        new_progress = LearningProgress(
            user_id=user_id,
            course_id="",
            area_id=area_id,
            mastery_level=0.0,
            confidence_level=0.0,
            correct_answers=0,
            total_answers=0,
            last_activity=datetime.now(),
            improvement_trend=0.0,
            recommended_difficulty=0.3
        )
        progress_list.append(new_progress)
        return new_progress

    def _calculate_adaptive_difficulty(self, area: KnowledgeArea, progress: LearningProgress) -> float:
        """Calculate adaptive difficulty based on area and user progress"""
        base_difficulty = area.difficulty_level

        # Adjust based on mastery level
        mastery_adjustment = progress.mastery_level * 0.3  # 30% adjustment based on mastery

        # Adjust based on confidence vs mastery mismatch
        confidence_mastery_gap = progress.confidence_level - progress.mastery_level
        adjustment = abs(confidence_mastery_gap) * 0.2  # 20% adjustment for over/under confidence

        # If user is overconfident, increase difficulty
        if confidence_mastery_gap > 0.2:  # Overconfident
            adjustment *= 1.5
        # If user is underconfident, decrease difficulty slightly
        elif confidence_mastery_gap < -0.2:  # Underconfident
            adjustment *= -0.5

        final_difficulty = base_difficulty + mastery_adjustment + adjustment
        return max(0.1, min(1.0, final_difficulty))

    def _determine_quiz_type(self, progress: LearningProgress) -> str:
        """Determine quiz type based on user progress"""
        if progress.mastery_level < 0.3:
            return "assessment"  # Initial assessment
        elif progress.mastery_level < 0.7:
            return "practice"    # Practice and reinforcement
        else:
            return "challenge"   # Challenge and mastery testing

    def _prepare_content_for_quiz(self, course_id: str, area: KnowledgeArea) -> str:
        """Prepare targeted content for quiz generation"""
        content_prompt = f"""
        Area di conoscenza: {area.name}
        Descrizione: {area.description}
        Concetti chiave: {', '.join(area.concepts)}
        Parole chiave: {', '.join(area.keywords)}

        Genera domande specifiche per questa area di conoscenza.
        """
        return content_prompt

    def _select_bloom_levels(self, mastery_level: float) -> List[str]:
        """Select appropriate Bloom's taxonomy levels based on mastery"""
        if mastery_level < 0.3:
            return ["remember", "understand"]  # Focus on basic recall
        elif mastery_level < 0.7:
            return ["understand", "apply", "analyze"]  # Application and analysis
        else:
            return ["analyze", "evaluate", "create"]  # Higher-order thinking

    def _generate_quiz_rationale(self, area: KnowledgeArea, progress: LearningProgress) -> str:
        """Generate rationale for why this quiz is recommended"""
        if progress.total_answers == 0:
            return f"Valutazione iniziale per '{area.name}' per stabilire il tuo livello di partenza."

        if progress.mastery_level < 0.5:
            return f"Pratica su '{area.name}' - il tuo livello attuale è {progress.mastery_level:.0%}, serve più esercizio."
        elif progress.mastery_level < 0.8:
            return f"Reinforzo su '{area.name}' - buon progresso, consolidiamo la conoscenza."
        else:
            return f"Sfida su '{area.name}' - eccellente padronanza, testiamo competenze avanzate."

    async def get_recommended_quizzes(self, user_id: str, course_id: str, max_quizzes: int = 5) -> List[QuizRecommendation]:
        """Get recommended quizzes for a user based on their learning progress"""
        try:
            if course_id not in self.knowledge_areas:
                logger.warning(f"No knowledge areas found for course {course_id}")
                return []

            areas = list(self.knowledge_areas[course_id].values())
            recommendations = []

            # Sort areas by priority (low mastery, high coverage)
            prioritized_areas = sorted(areas, key=lambda a: self._calculate_area_priority(a, user_id))

            for area in prioritized_areas[:max_quizzes]:
                try:
                    recommendation = await self.generate_quiz_for_area(course_id, area.id, user_id)
                    recommendations.append(recommendation)
                except Exception as e:
                    logger.error(f"Error generating recommendation for area {area.id}: {e}")
                    continue

            return recommendations

        except Exception as e:
            logger.error(f"Error getting recommended quizzes: {e}")
            return []

    def _calculate_area_priority(self, area: KnowledgeArea, user_id: str) -> float:
        """Calculate priority score for a knowledge area (lower = higher priority)"""
        progress = self._get_user_progress(user_id, area.id)

        # Factors for priority calculation
        mastery_priority = (1.0 - progress.mastery_level) * 0.4  # Lower mastery = higher priority
        coverage_priority = area.coverage_score * 0.3  # Higher coverage = higher priority
        recency_priority = 0.2 if progress.last_activity else 0.0  # Recently assessed = lower priority
        assessment_count_priority = max(0, 5 - progress.assessment_count) * 0.1  # Few assessments = higher priority

        return mastery_priority + coverage_priority + recency_priority + assessment_count_priority

    def update_progress(self, user_id: str, course_id: str, area_id: str,
                        correct: bool, confidence: float, response_time: float):
        """Update user progress after answering a quiz question"""
        try:
            progress = self._get_user_progress(user_id, area_id)

            # Update basic metrics
            progress.total_answers += 1
            if correct:
                progress.correct_answers += 1

            # Calculate new mastery level using exponential moving average
            alpha = 0.3  # Learning rate
            new_performance = 1.0 if correct else 0.0
            progress.mastery_level = alpha * new_performance + (1 - alpha) * progress.mastery_level

            # Update confidence level
            progress.confidence_level = alpha * confidence + (1 - alpha) * progress.confidence_level

            # Calculate improvement trend
            if progress.total_answers > 1:
                recent_performance = progress.correct_answers / progress.total_answers
                progress.improvement_trend = recent_performance - 0.5  # Positive if above 50%

            # Update recommended difficulty
            progress.recommended_difficulty = self._calculate_adaptive_difficulty(
                self.knowledge_areas.get(course_id, {}).get(area_id),
                progress
            )

            progress.last_activity = datetime.now()

            # Save to persistent storage
            self.save_knowledge_areas()

            logger.info(f"Updated progress for user {user_id}, area {area_id}: "
                       f"mastery={progress.mastery_level:.2f}, confidence={progress.confidence_level:.2f}")

        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    def get_knowledge_areas(self, course_id: str) -> List[KnowledgeArea]:
        """Get all knowledge areas for a course"""
        return list(self.knowledge_areas.get(course_id, {}).values())

    def get_user_progress_summary(self, user_id: str, course_id: str) -> Dict[str, Any]:
        """Get comprehensive progress summary for a user"""
        try:
            areas = self.get_knowledge_areas(course_id)
            if not areas:
                return {"message": "No knowledge areas found for this course"}

            progress_summary = {
                "course_id": course_id,
                "total_areas": len(areas),
                "mastered_areas": 0,
                "in_progress_areas": 0,
                "not_started_areas": 0,
                "overall_mastery": 0.0,
                "areas_detail": []
            }

            total_mastery = 0.0
            master_threshold = 0.8
            start_threshold = 0.1

            for area in areas:
                progress = self._get_user_progress(user_id, area.id)

                area_detail = {
                    "area_id": area.id,
                    "area_name": area.name,
                    "mastery_level": progress.mastery_level,
                    "confidence_level": progress.confidence_level,
                    "assessment_count": progress.assessment_count,
                    "last_activity": progress.last_activity.isoformat() if progress.last_activity else None,
                    "difficulty_level": area.difficulty_level,
                    "quiz_available": area.quiz_questions_available > 0
                }
                progress_summary["areas_detail"].append(area_detail)
                total_mastery += progress.mastery_level

                # Categorize progress
                if progress.mastery_level >= master_threshold:
                    progress_summary["mastered_areas"] += 1
                elif progress.mastery_level >= start_threshold:
                    progress_summary["in_progress_areas"] += 1
                else:
                    progress_summary["not_started_areas"] += 1

            progress_summary["overall_mastery"] = total_mastery / len(areas) if areas else 0.0

            return progress_summary

        except Exception as e:
            logger.error(f"Error getting progress summary: {e}")
            return {"error": str(e)}

    def _create_fallback_knowledge_areas(self, course_id: str, content_text: str, sources: List[Dict]) -> List[KnowledgeArea]:
        """Create fallback knowledge areas when LLM fails to respond"""
        try:
            logger.info("Creating fallback knowledge areas based on content analysis")

            # Simple keyword-based area extraction
            areas = []

            # Common academic subject areas
            area_templates = [
                {
                    "name": "Concetti Fondamentali",
                    "description": "Concetti di base e terminologia principale del corso",
                    "keywords": ["concetto", "definizione", "base", "fondamentale", "terminologia"],
                    "difficulty": 0.3
                },
                {
                    "name": "Storia e Sviluppo",
                    "description": "Evoluzione storica e sviluppo cronologico degli argomenti",
                    "keywords": ["storia", "sviluppo", "evoluzione", "cronologia", "periodo"],
                    "difficulty": 0.5
                },
                {
                    "name": "Teoria e Principi",
                    "description": "Principi teorici e quadri concettuali",
                    "keywords": ["teoria", "principio", "modello", "quadro", "concettuale"],
                    "difficulty": 0.7
                },
                {
                    "name": "Applicazioni Pratiche",
                    "description": "Applicazioni pratiche ed esempi concreti",
                    "keywords": ["applicazione", "pratica", "esempio", "concreto", "reale"],
                    "difficulty": 0.6
                },
                {
                    "name": "Metodologia",
                    "description": "Metodi e procedure di analisi e studio",
                    "keywords": ["metodo", "metodologia", "procedura", "analisi", "approccio"],
                    "difficulty": 0.6
                }
            ]

            content_lower = content_text.lower()

            # Create areas based on template matches
            for i, template in enumerate(area_templates):
                # Count keyword matches in content
                matches = sum(1 for keyword in template["keywords"] if keyword in content_lower)

                if matches > 0:  # Only create area if keywords are found
                    area = KnowledgeArea(
                        id=f"{course_id}_area_{i}",
                        name=template["name"],
                        description=template["description"],
                        keywords=template["keywords"],
                        difficulty_level=template["difficulty"],
                        prerequisite_areas=[],
                        related_areas=[],
                        material_sources=[source.get("source", "Unknown") for source in sources],
                        coverage_score=min(matches / len(template["keywords"]), 1.0),
                        mastery_level=0.0,
                        last_assessed=None,
                        assessment_count=0,
                        quiz_questions_available=5,
                        concepts=template["keywords"][:3]  # Use first few keywords as concepts
                    )
                    areas.append(area)

            # If no areas matched, create generic ones
            if not areas:
                generic_areas = [
                    "Introduzione al Corso",
                    "Sviluppo dei Contenuti",
                    "Analisi e Approfondimento",
                    "Applicazioni Pratiche",
                    "Conclusioni e Sintesi"
                ]

                for i, area_name in enumerate(generic_areas):
                    area = KnowledgeArea(
                        id=f"{course_id}_area_{i}",
                        name=area_name,
                        description=f"Area di conoscenza: {area_name}",
                        keywords=[area_name.lower().split()[0]],
                        difficulty_level=0.5,
                        prerequisite_areas=[],
                        related_areas=[],
                        material_sources=[source.get("source", "Unknown") for source in sources],
                        coverage_score=0.5,
                        mastery_level=0.0,
                        last_assessed=None,
                        assessment_count=0,
                        quiz_questions_available=3,
                        concepts=[area_name.lower()]
                    )
                    areas.append(area)

            logger.info(f"Created {len(areas)} fallback knowledge areas")
            return areas

        except Exception as e:
            logger.error(f"Error creating fallback knowledge areas: {e}")
            return []

    def _create_fallback_knowledge_area(self, course_id: str, sources: List[Dict]) -> KnowledgeArea:
        """Create fallback knowledge area with generic concepts"""
        try:
            logger.info("Creating fallback knowledge area with generic concepts")

            # Create knowledge area
            knowledge_area = KnowledgeArea(
                id=f"{course_id}_fallback",
                name="Area di Conoscenza Generale",
                description="Concetti principali identificati automaticamente",
                main_concepts=[],
                all_concepts={},
                difficulty_level=0.5,
                coverage_score=0.6,
                mastery_level=0.0,
                last_updated=datetime.now(),
                material_sources=[source.get("source", "Unknown") for source in sources]
            )

            # Generic main concepts
            generic_concepts = [
                {"name": "Concetti Fondamentali", "keywords": ["concetto", "definizione", "base"], "difficulty": 0.3},
                {"name": "Sviluppo Teorico", "keywords": ["teoria", "principio", "modello"], "difficulty": 0.6},
                {"name": "Applicazioni Pratiche", "keywords": ["applicazione", "pratica", "esempio"], "difficulty": 0.5},
                {"name": "Analisi Critica", "keywords": ["analisi", "critica", "valutazione"], "difficulty": 0.7}
            ]

            for i, concept_data in enumerate(generic_concepts):
                concept = Concept(
                    id=f"{course_id}_fallback_concept_{i}",
                    name=concept_data["name"],
                    description=f"Area di studio: {concept_data['name']}",
                    keywords=concept_data["keywords"],
                    difficulty_level=concept_data["difficulty"],
                    mastery_level=0.0,
                    confidence_level=0.0,
                    last_studied=None,
                    study_count=0,
                    quiz_count=0,
                    material_sources=[source.get("source", "Unknown") for source in sources],
                    parent_concept_id=None,
                    sub_concept_ids=[],
                    position_x=150 * (i - 1.5),  # Spread horizontally
                    position_y=0
                )

                knowledge_area.add_concept(concept, is_main=True)

            logger.info(f"Created fallback knowledge area with {len(generic_concepts)} concepts")
            return knowledge_area

        except Exception as e:
            logger.error(f"Error creating fallback knowledge area: {e}")
            # Return minimal knowledge area
            return KnowledgeArea(
                id=f"{course_id}_minimal",
                name="Area di Conoscenza",
                description="Concetti base del corso",
                main_concepts=[],
                all_concepts={},
                difficulty_level=0.5,
                coverage_score=0.5,
                mastery_level=0.0,
                last_updated=datetime.now(),
                material_sources=[]
            )

    async def create_sub_concept_dynamically(self, course_id: str, parent_concept_id: str,
                                           context: str, user_interaction: str) -> Optional[Concept]:
        """Create sub-concept dynamically based on user interaction"""
        try:
            logger.info(f"Creating sub-concept for parent {parent_concept_id} based on interaction")

            # Get parent concept
            knowledge_area = self.knowledge_areas.get(course_id, {}).get(f"{course_id}_main")
            if not knowledge_area:
                logger.error(f"No knowledge area found for course {course_id}")
                return None

            parent_concept = knowledge_area.all_concepts.get(parent_concept_id)
            if not parent_concept:
                logger.error(f"Parent concept {parent_concept_id} not found")
                return None

            # Generate sub-concept based on context
            prompt = f"""
            Basandoti sull'interazione dell'utente e sul contesto, crea un sotto-concetto specifico.

            CONCETTO PADRE: {parent_concept.name}
            DESCRIZIONE PADRE: {parent_concept.description}
            INTERAZIONE UTENTE: {user_interaction}
            CONTESTO: {context}

            Crea un sotto-concetto specifico che approfondisce {parent_concept.name}.

            Restituisci JSON:
            {
                "name": "Nome del sotto-concetto",
                "description": "Descrizione dettagliata (max 60 parole)",
                "keywords": ["keyword1", "keyword2", "keyword3"],
                "difficulty": 0.6
            }
            """

            llm_response = await self.llm_service.generate_response(
                query=prompt,
                context={"parent_concept": parent_concept.name, "interaction": user_interaction},
                course_id=course_id
            )

            if not llm_response or llm_response.strip() == "":
                logger.error("Empty LLM response for sub-concept creation")
                return None

            try:
                concept_data = json.loads(llm_response)

                # Calculate position near parent with some offset
                offset_angle = len(parent_concept.sub_concept_ids) * 0.8
                offset_radius = 80

                sub_concept = Concept(
                    id=f"{course_id}_subconcept_{len(knowledge_area.all_concepts)}",
                    name=concept_data["name"],
                    description=concept_data["description"],
                    keywords=concept_data.get("keywords", []),
                    difficulty_level=concept_data.get("difficulty", 0.6),
                    mastery_level=0.0,
                    confidence_level=0.0,
                    last_studied=None,
                    study_count=0,
                    quiz_count=0,
                    material_sources=parent_concept.material_sources,
                    parent_concept_id=parent_concept_id,
                    sub_concept_ids=[],
                    position_x=parent_concept.position_x + offset_radius * 0.7 * (1 if offset_angle % 2 == 0 else -1),
                    position_y=parent_concept.position_y + offset_radius * 0.5
                )

                # Add to knowledge area
                knowledge_area.add_concept(sub_concept, is_main=False)
                knowledge_area.calculate_overall_mastery()

                # Save changes
                self.save_knowledge_areas()

                logger.info(f"Created sub-concept: {sub_concept.name}")
                return sub_concept

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse sub-concept LLM response: {e}")
                return None

        except Exception as e:
            logger.error(f"Error creating sub-concept: {e}")
            return None

    def generate_concept_visualization(self, course_id: str, user_id: str) -> Dict[str, Any]:
        """Generate visualization data for concepts and their relationships"""
        try:
            # Try to find any knowledge area for this course
            course_areas = self.knowledge_areas.get(course_id, {})
            knowledge_area = None

            # Look for main area first, then any area
            if f"{course_id}_main" in course_areas:
                knowledge_area = course_areas[f"{course_id}_main"]
            elif f"{course_id}_fallback" in course_areas:
                knowledge_area = course_areas[f"{course_id}_fallback"]
            else:
                # Take the first available area
                for area_id, area in course_areas.items():
                    knowledge_area = area
                    break

            if not knowledge_area:
                return {"error": "No knowledge area found"}

            # Generate concept nodes
            concepts = []
            for concept_id, concept in knowledge_area.all_concepts.items():
                # Get user progress for this concept
                user_progress = self._get_concept_progress(user_id, concept_id)

                # Color based on mastery level
                mastery_color = self._get_mastery_color(user_progress.mastery_level)

                # Size based on importance (main concepts bigger, sub-concepts smaller)
                node_size = 30 if concept_id in knowledge_area.main_concepts else 20

                concept_viz = ConceptVisualization(
                    concept_id=concept.id,
                    name=concept.name,
                    x=concept.position_x,
                    y=concept.position_y,
                    size=node_size + (user_progress.confidence_level * 10),  # Bigger if more confident
                    color=mastery_color,
                    mastery_level=user_progress.mastery_level,
                    has_sub_concepts=len(concept.sub_concept_ids) > 0,
                    parent_id=concept.parent_concept_id
                )
                concepts.append(concept_viz)

            # Generate connections
            connections = []
            for concept_id, concept in knowledge_area.all_concepts.items():
                # Parent-child connections
                for sub_id in concept.sub_concept_ids:
                    if sub_id in knowledge_area.all_concepts:
                        connection = ConnectionVisualization(
                            from_concept_id=concept_id,
                            to_concept_id=sub_id,
                            strength=0.8,
                            relationship_type="hierarchy"
                        )
                        connections.append(connection)

                # Related concepts connections (simple keyword overlap)
                for other_id, other_concept in knowledge_area.all_concepts.items():
                    if concept_id != other_id and not concept.parent_concept_id and not other_concept.parent_concept_id:
                        # Both are main concepts, check for relationships
                        keyword_overlap = len(set(concept.keywords) & set(other_concept.keywords))
                        if keyword_overlap > 0:
                            connection = ConnectionVisualization(
                                from_concept_id=concept_id,
                                to_concept_id=other_id,
                                strength=min(keyword_overlap * 0.2, 0.5),
                                relationship_type="related"
                            )
                            connections.append(connection)

            return {
                "concepts": [asdict(concept) for concept in concepts],
                "connections": [asdict(conn) for conn in connections],
                "stats": {
                    "total_concepts": len(knowledge_area.all_concepts),
                    "main_concepts": len(knowledge_area.main_concepts),
                    "sub_concepts": len(knowledge_area.all_concepts) - len(knowledge_area.main_concepts),
                    "average_mastery": knowledge_area.mastery_level,
                    "most_studied": self._get_most_studied_concept(knowledge_area, user_id)
                }
            }

        except Exception as e:
            logger.error(f"Error generating concept visualization: {e}")
            return {"error": str(e)}

    def _get_concept_progress(self, user_id: str, concept_id: str) -> LearningProgress:
        """Get user progress for a specific concept"""
        # Check if we have progress for this concept
        if user_id in self.learning_progress:
            for progress in self.learning_progress[user_id]:
                if progress.area_id == concept_id:
                    return progress

        # Return default progress
        return LearningProgress(
            user_id=user_id,
            course_id=concept_id.split("_")[0],
            area_id=concept_id,
            mastery_level=0.0,
            confidence_level=0.0,
            correct_answers=0,
            total_answers=0,
            last_activity=datetime.now(),
            improvement_trend=0.0,
            recommended_difficulty=0.5
        )

    def _get_mastery_color(self, mastery_level: float) -> str:
        """Get color based on mastery level"""
        if mastery_level >= 0.8:
            return "#10b981"  # Green - high mastery
        elif mastery_level >= 0.6:
            return "#3b82f6"  # Blue - good mastery
        elif mastery_level >= 0.4:
            return "#f59e0b"  # Amber - developing mastery
        else:
            return "#ef4444"  # Red - low mastery

    def _get_most_studied_concept(self, knowledge_area: KnowledgeArea, user_id: str) -> Optional[str]:
        """Get the concept the user has studied most"""
        most_studied = None
        max_count = 0

        for concept_id, concept in knowledge_area.all_concepts.items():
            progress = self._get_concept_progress(user_id, concept_id)
            if progress.total_answers > max_count:
                max_count = progress.total_answers
                most_studied = concept.name

        return most_studied
