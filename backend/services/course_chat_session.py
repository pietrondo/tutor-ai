"""
Course Chat Session Management
Advanced session management for course-specific chatbot with persistent context
"""

import json
import uuid
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union, Literal
from dataclasses import dataclass, asdict
from enum import Enum
import pickle

class SessionContextType(Enum):
    """Types of context that can be stored in a session"""
    TOPIC_HISTORY = "topic_history"
    CONCEPT_MAP = "concept_map"
    STUDY_PROGRESS = "study_progress"
    LEARNING_STYLE = "learning_style"
    DIFFICULTY_LEVEL = "difficulty_level"
    FREQUENT_CONCEPTS = "frequent_concepts"
    PREFERRED_EXAMPLES = "preferred_examples"
    MISUNDERSTANDINGS = "misunderstandings"

@dataclass
class ChatMessage:
    """Enhanced chat message with metadata"""
    id: str
    timestamp: datetime
    role: Literal["user", "assistant"]
    content: str
    sources: List[Dict[str, Any]]
    context_used: List[str]  # Which contexts were used for generation
    confidence_score: float  # AI confidence in its response
    topic_tags: List[str]  # Auto-detected topics
    response_time_ms: int
    is_followup: bool = False
    parent_message_id: Optional[str] = None

@dataclass
class CourseSession:
    """Course-specific chat session with rich context"""
    id: str
    course_id: str
    created_at: datetime
    last_activity: datetime
    messages: List[ChatMessage]
    context: Dict[str, Any]  # Persistent session context
    metadata: Dict[str, Any]
    statistics: Dict[str, Any]

class CourseChatSessionManager:
    """Advanced session manager for course-specific chatbots"""

    def __init__(self):
        self.session_dir = "data/chat_sessions"
        self.context_dir = "data/session_contexts"
        self.sessions_file = os.path.join(self.session_dir, "course_sessions.json")
        self.ensure_directories()

        # Configuration
        self.max_messages_per_session = 100
        self.session_timeout_hours = 48
        self.max_context_memory = 50  # max context items to store

    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.session_dir, exist_ok=True)
        os.makedirs(self.context_dir, exist_ok=True)

        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'w') as f:
                json.dump({}, f)

    def get_or_create_session(self, course_id: str, session_id: Optional[str] = None) -> CourseSession:
        """Get existing session or create new one"""
        if session_id:
            session = self.load_session(session_id)
            if session and session.course_id == course_id:
                return self._cleanup_old_messages(session)

        # Create new session
        session_id = str(uuid.uuid4())
        session = CourseSession(
            id=session_id,
            course_id=course_id,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            messages=[],
            context=self._initialize_context(course_id),
            metadata={
                "device_type": "web",
                "preferred_response_length": "medium",
                "verbosity_level": "detailed",
                "language": "it"
            },
            statistics={
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "total_response_time_ms": 0,
                "average_confidence": 0.0,
                "topics_discussed": set(),
                "concepts_covered": set(),
                "sources_used": set()
            }
        )

        self.save_session(session)
        return session

    def add_message(self, session_id: str, role: str, content: str,
                   sources: List[Dict[str, Any]] = None, context_used: List[str] = None,
                   confidence_score: float = 0.0, response_time_ms: int = 0,
                   topic_tags: List[str] = None, is_followup: bool = False,
                   parent_message_id: Optional[str] = None) -> ChatMessage:
        """Add a message to the session and update context"""
        session = self.load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        message = ChatMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            role=role,
            content=content,
            sources=sources or [],
            context_used=context_used or [],
            confidence_score=confidence_score,
            topic_tags=topic_tags or [],
            response_time_ms=response_time_ms,
            is_followup=is_followup,
            parent_message_id=parent_message_id
        )

        session.messages.append(message)
        session.last_activity = datetime.now(timezone.utc)

        # Update statistics
        session.statistics["total_messages"] += 1
        session.statistics[f"{role}_messages"] += 1
        session.statistics["total_response_time_ms"] += response_time_ms

        if topic_tags:
            session.statistics["topics_discussed"].update(topic_tags)

        if sources:
            for source in sources:
                session.statistics["sources_used"].add(source.get("book_title", ""))

        # Update session context based on message
        self._update_session_context(session, message)

        # Save session
        self.save_session(session)

        return message

    def get_session_context(self, session_id: str, context_type: Optional[SessionContextType] = None) -> Any:
        """Get session context, optionally filtered by type"""
        session = self.load_session(session_id)
        if not session:
            return None

        if context_type:
            return session.context.get(context_type.value, {})
        return session.context

    def update_session_context(self, session_id: str, context_type: SessionContextType,
                              context_data: Any):
        """Update specific context type in session"""
        session = self.load_session(session_id)
        if session:
            session.context[context_type.value] = context_data
            session.last_activity = datetime.now(timezone.utc)
            self.save_session(session)

    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get formatted conversation history for context"""
        session = self.load_session(session_id)
        if not session:
            return []

        messages = session.messages[-limit:]
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "sources": msg.sources
            }
            for msg in messages
        ]

    def get_course_analytics(self, course_id: str) -> Dict[str, Any]:
        """Get analytics for all sessions in a course"""
        sessions_data = self._load_sessions_dict()
        course_sessions = [
            session for session in sessions_data.values()
            if session.get("course_id") == course_id
        ]

        if not course_sessions:
            return {}

        # Aggregate statistics
        total_sessions = len(course_sessions)
        total_messages = sum(s.get("statistics", {}).get("total_messages", 0) for s in course_sessions)
        avg_confidence = sum(s.get("statistics", {}).get("average_confidence", 0) for s in course_sessions) / max(len(course_sessions), 1)

        # Get most discussed topics
        all_topics = set()
        for session in course_sessions:
            all_topics.update(session.get("statistics", {}).get("topics_discussed", []))

        # Get recent activity
        recent_sessions = sorted(
            course_sessions,
            key=lambda x: x.get("last_activity", ""),
            reverse=True
        )[:5]

        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "average_confidence": round(avg_confidence, 3),
            "unique_topics": len(all_topics),
            "recent_sessions": recent_sessions,
            "most_active_day": self._get_most_active_day(course_sessions)
        }

    def cleanup_expired_sessions(self):
        """Clean up sessions older than timeout"""
        sessions_data = self._load_sessions_dict()
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.session_timeout_hours)

        active_sessions = {}
        for session_id, session_data in sessions_data.items():
            last_activity = datetime.fromisoformat(
                session_data.get("last_activity", session_data.get("created_at", datetime.now(timezone.utc).isoformat()))
            )
            if last_activity > cutoff_time:
                active_sessions[session_id] = session_data

        with open(self.sessions_file, 'w') as f:
            json.dump(active_sessions, f, indent=2)

        return len(sessions_data) - len(active_sessions)

    def _initialize_context(self, course_id: str) -> Dict[str, Any]:
        """Initialize context for a new course session"""
        return {
            SessionContextType.TOPIC_HISTORY.value: {
                "discussed_topics": [],
                "topic_frequency": {},
                "last_discussed": {}
            },
            SessionContextType.CONCEPT_MAP.value: {
                "concepts": {},
                "relationships": {},
                "misunderstandings": {}
            },
            SessionContextType.STUDY_PROGRESS.value: {
                "covered_materials": set(),
                "completed_exercises": [],
                "mastery_levels": {},
                "study_streak": 0,
                "last_study_session": None
            },
            SessionContextType.LEARNING_STYLE.value: {
                "preferred_format": "explanations",  # explanations, examples, analogies
                "complexity_preference": "gradual",  # gradual, direct, detailed
                "interaction_style": "conversational"  # conversational, formal, casual
            },
            SessionContextType.DIFFICULTY_LEVEL.value: {
                "current_level": "intermediate",
                "adaptation_history": [],
                "performance_feedback": []
            },
            SessionContextType.FREQUENT_CONCEPTS.value: {
                "high_frequency": [],
                "recent_queries": [],
                "concept_relationships": {}
            },
            SessionContextType.PREFERRED_EXAMPLES.value: {
                "types": [],  # real_world, academic, simplified
                "subjects": [],  # specific subject areas
                "difficulty_preference": "mixed"
            }
        }

    def _update_session_context(self, session: CourseSession, message: ChatMessage):
        """Update session context based on new message"""
        # Update topic history
        topic_history = session.context.get(SessionContextType.TOPIC_HISTORY.value, {})
        if message.topic_tags:
            for topic in message.topic_tags:
                topic_history["topic_frequency"][topic] = topic_history["topic_frequency"].get(topic, 0) + 1
                topic_history["last_discussed"][topic] = message.timestamp.isoformat()

            # Track concept relationships
            if message.is_followup and message.parent_message_id:
                parent_topic = self._get_message_topic(session, message.parent_message_id)
                if parent_topic and message.topic_tags:
                    for current_topic in message.topic_tags:
                        relationships = session.context[SessionContextType.CONCEPT_MAP.value]["relationships"]
                        key = f"{parent_topic}->{current_topic}"
                        relationships[key] = relationships.get(key, 0) + 1

    def _get_message_topic(self, session: CourseSession, message_id: str) -> Optional[str]:
        """Get primary topic of a message"""
        for message in session.messages:
            if message.id == message_id and message.topic_tags:
                return message.topic_tags[0] if message.topic_tags else None
        return None

    def _cleanup_old_messages(self, session: CourseSession) -> CourseSession:
        """Remove old messages to keep session manageable"""
        if len(session.messages) > self.max_messages_per_session:
            # Keep the most recent messages
            session.messages = session.messages[-self.max_messages_per_session:]
        return session

    def load_session(self, session_id: str) -> Optional[CourseSession]:
        """Load session from storage"""
        sessions_data = self._load_sessions_dict()
        session_data = sessions_data.get(session_id)

        if not session_data:
            return None

        # Convert datetime strings back to datetime objects
        session_data["created_at"] = datetime.fromisoformat(session_data["created_at"])
        session_data["last_activity"] = datetime.fromisoformat(session_data["last_activity"])

        # Convert messages
        messages = []
        for msg_data in session_data.get("messages", []):
            msg_data["timestamp"] = datetime.fromisoformat(msg_data["timestamp"])
            messages.append(ChatMessage(**msg_data))
        session_data["messages"] = messages

        return CourseSession(**session_data)

    def save_session(self, session: CourseSession):
        """Save session to storage"""
        # Convert session to dict for JSON serialization
        session_dict = asdict(session)

        # Convert datetime objects to strings
        session_dict["created_at"] = session.created_at.isoformat()
        session_dict["last_activity"] = session.last_activity.isoformat()

        # Convert messages to dict
        session_dict["messages"] = [asdict(msg) for msg in session.messages]
        for msg_dict in session_dict["messages"]:
            msg_dict["timestamp"] = msg_dict["timestamp"].replace("Z", "+00:00")

        # Handle non-serializable objects in statistics
        session_dict["statistics"]["topics_discussed"] = list(session.statistics["topics_discussed"])
        session_dict["statistics"]["concepts_covered"] = list(session.statistics["concepts_covered"])
        session_dict["statistics"]["sources_used"] = list(session.statistics["sources_used"])

        # Load existing sessions
        sessions_data = self._load_sessions_dict()
        sessions_data[session.id] = session_dict

        # Save to file
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions_data, f, indent=2)

    def _load_sessions_dict(self) -> Dict[str, Any]:
        """Load all sessions as dict"""
        try:
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _get_most_active_day(self, sessions: List[Dict]) -> Optional[str]:
        """Find the most active day from session data"""
        day_counts = {}
        for session in sessions:
            created_date = session.get("created_at", "").split("T")[0]
            if created_date:
                day_counts[created_date] = day_counts.get(created_date, 0) + 1

        if day_counts:
            return max(day_counts, key=day_counts.get)
        return None

# Global instance
course_chat_session_manager = CourseChatSessionManager()