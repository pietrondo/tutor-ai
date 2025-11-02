import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import structlog
from .rag_service import RAGService
from .llm_service import LLMService

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
    current_session_index: int = 0
    is_active: bool = True

class StudyPlannerService:
    def __init__(self):
        self.rag_service = RAGService()
        self.llm_service = LLMService()
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
        """Generate a comprehensive study plan based on course materials"""
        try:
            # Get course documents from RAG
            documents_result = await self.rag_service.search_documents(course_id)

            if not documents_result.get('documents'):
                raise ValueError("No documents found for this course")

            # Extract topics and content from documents
            all_topics = []
            materials_summary = []

            for doc in documents_result['documents']:
                materials_summary.append({
                    'source': doc['source'],
                    'chunks_count': doc['total_chunks']
                })

                # Use RAG to extract topics from this document
                for chunk in doc['chunks'][:3]:  # Sample first few chunks
                    topics_query = f"Extract main topics and concepts from: {chunk['content']}"
                    context_result = await self.rag_service.retrieve_context(topics_query, course_id, k=3)
                    if context_result.get('text'):
                        # Use LLM to extract structured topics
                        topics_prompt = f"""
                        Based on the following text, extract 3-5 main topics or concepts that should be studied.
                        Return them as a simple list.

                        Text: {context_result['text'][:1000]}

                        Topics (one per line):
                        """
                        topics_response = await self.llm_service.generate_response(topics_prompt, {}, course_id)
                        if topics_response:
                            topics = [topic.strip() for topic in topics_response.split('\n') if topic.strip()]
                            all_topics.extend(topics[:2])  # Take top 2 topics per chunk

            # Remove duplicates and limit topics
            unique_topics = list(set(all_topics))[:15]  # Max 15 topics for manageable plan

            # Generate study sessions using LLM
            sessions = await self._generate_study_sessions(
                course_id,
                unique_topics,
                materials_summary,
                preferences
            )

            # Create study plan
            plan = StudyPlan(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title=f"Piano di Studio - {preferences.get('title', 'Generale')}",
                description=f"Piano personalizzato basato su {len(documents_result['documents'])} documenti",
                total_sessions=len(sessions),
                estimated_hours=sum(s.duration_minutes for s in sessions) // 60,
                difficulty_progression=preferences.get('difficulty_progression', 'graduale'),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                sessions=sessions
            )

            # Save plan
            await self.save_study_plan(plan)

            logger.info(f"Generated study plan for course {course_id} with {len(sessions)} sessions")
            return plan

        except Exception as e:
            logger.error(f"Error generating study plan: {e}")
            raise e

    async def _generate_study_sessions(self, course_id: str, topics: List[str],
                                     materials: List[Dict], preferences: Dict[str, Any]) -> List[StudySession]:
        """Generate individual study sessions using AI"""
        try:
            sessions_per_week = preferences.get('sessions_per_week', 3)
            session_duration = preferences.get('session_duration', 45)
            difficulty_level = preferences.get('difficulty_level', 'intermediate')

            # Group topics into logical sessions
            topics_per_session = max(1, len(topics) // (sessions_per_week * 4))  # 4-week plan

            sessions = []
            for i in range(0, len(topics), topics_per_session):
                session_topics = topics[i:i + topics_per_session]

                # Generate session details using LLM
                session_prompt = f"""
                Create a study session with the following details:
                - Topics: {', '.join(session_topics)}
                - Duration: {session_duration} minutes
                - Difficulty level: {difficulty_level}
                - Available materials: {[m['source'] for m in materials]}

                Provide:
                1. A compelling title for the session
                2. A brief description (2-3 sentences)
                3. 2-3 specific learning objectives
                4. Any prerequisites needed

                Format as JSON:
                {{
                    "title": "...",
                    "description": "...",
                    "objectives": ["...", "..."],
                    "prerequisites": ["...", "..."]
                }}
                """

                response = await self.llm_service.generate_response(session_prompt, {}, course_id)

                try:
                    session_data = json.loads(response)
                except:
                    # Fallback if JSON parsing fails
                    session_data = {
                        "title": f"Studio: {', '.join(session_topics[:2])}",
                        "description": f"Sessione di studio su {', '.join(session_topics)}",
                        "objectives": ["Comprendere i concetti chiave", "Applicare le conoscenze"],
                        "prerequisites": []
                    }

                session = StudySession(
                    id=str(uuid.uuid4()),
                    title=session_data.get('title', f"Sessione {i//topics_per_session + 1}"),
                    description=session_data.get('description', f"Studio di {', '.join(session_topics)}"),
                    duration_minutes=session_duration,
                    topics=session_topics,
                    materials=[m['source'] for m in materials],
                    difficulty=difficulty_level,
                    objectives=session_data.get('objectives', []),
                    prerequisites=session_data.get('prerequisites', []),
                    order_index=i // topics_per_session
                )

                sessions.append(session)

            return sessions

        except Exception as e:
            logger.error(f"Error generating study sessions: {e}")
            raise e

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