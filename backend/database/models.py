"""
SQLAlchemy Database Models for CLE System
Corresponds to Pydantic models with proper relationships and constraints
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
import enum

from .connection import Base

# Import enums from models or create database-specific enums
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.common import (
        DifficultyLevel, LearningStyle, ContentType, SessionType,
        QuestionType, BloomLevel, CardType, MetacognitionPhase,
        ReflectionType, ElaborationDepth, ConnectionType,
        TransferDomain, UserFeedbackType, DataFormat
    )
except ImportError:
    # Fallback enum definitions for database setup
    from enum import Enum as BaseEnum

    class DifficultyLevel(str, BaseEnum):
        EASY = "easy"
        MEDIUM = "medium"
        HARD = "hard"
        ADAPTIVE = "adaptive"

    class LearningStyle(str, BaseEnum):
        VISUAL = "visual"
        KINESTHETIC = "kinesthetic"
        BALANCED = "balanced"

    class ContentType(str, BaseEnum):
        TEXT = "text"
        VIDEO = "video"
        AUDIO = "audio"
        INTERACTIVE = "interactive"

    class SessionType(str, BaseEnum):
        MIXED = "mixed"
        REVIEW = "review"
        NEW = "new"
        COMPREHENSIVE = "comprehensive"

    class QuestionType(str, BaseEnum):
        MULTIPLE_CHOICE = "multiple_choice"
        SHORT_ANSWER = "short_answer"
        ESSAY = "essay"
        TRUE_FALSE = "true_false"

    class BloomLevel(str, BaseEnum):
        REMEMBER = "remember"
        UNDERSTAND = "understand"
        APPLY = "apply"
        ANALYZE = "analyze"
        EVALUATE = "evaluate"
        CREATE = "create"

    class CardType(str, BaseEnum):
        BASIC = "basic"
        CLOZE = "cloze"
        CONCEPT = "concept"
        APPLICATION = "application"

    class MetacognitionPhase(str, BaseEnum):
        PLANNING = "planning"
        MONITORING = "monitoring"
        EVALUATION = "evaluation"

    class ReflectionType(str, BaseEnum):
        SUMMATIVE = "summative"
        FORMATIVE = "formative"
        SELF_ASSESSMENT = "self_assessment"

    class ElaborationDepth(str, BaseEnum):
        SHALLOW = "shallow"
        MODERATE = "moderate"
        DEEP = "deep"

    class ConnectionType(str, BaseEnum):
        PREREQUISITE = "prerequisite"
        RELATED = "related"
        CONTRASTING = "contrasting"
        EXAMPLE = "example"

    class TransferDomain(str, BaseEnum):
        ACADEMIC = "academic"
        PROFESSIONAL = "professional"
        PERSONAL = "personal"

    class UserFeedbackType(str, BaseEnum):
        RATING = "rating"
        COMMENT = "comment"
        SUGGESTION = "suggestion"

    class DataFormat(str, BaseEnum):
        JSON = "json"
        XML = "xml"
        CSV = "csv"

# =================== USER MODELS ===================

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    learning_style = Column(SQLEnum(LearningStyle), default=LearningStyle.BALANCED)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    courses = relationship("UserCourse", back_populates="user")
    learning_cards = relationship("LearningCard", back_populates="user")
    study_sessions = relationship("StudySession", back_populates="user")
    metacognitive_sessions = relationship("MetacognitiveSession", back_populates="user")

    @validates('email')
    def validate_email(self, key, email):
        if '@' not in email:
            raise ValueError('Invalid email format')
        return email.lower()

    @hybrid_property
    def total_cards_created(self):
        return len(self.learning_cards)

    @hybrid_property
    def total_study_sessions(self):
        return len(self.study_sessions)

# =================== COURSE MODELS ===================

class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    instructor_id = Column(String, ForeignKey("users.id"), nullable=True)
    difficulty = Column(SQLEnum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    content_type = Column(SQLEnum(ContentType), default=ContentType.TEXT)
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    instructor = relationship("User", foreign_keys=[instructor_id])
    users = relationship("UserCourse", back_populates="course")
    learning_cards = relationship("LearningCard", back_populates="course")
    study_sessions = relationship("StudySession", back_populates="course")
    metacognitive_sessions = relationship("MetacognitiveSession", back_populates="course")

class UserCourse(Base):
    __tablename__ = "user_courses"

    __table_args__ = (UniqueConstraint('user_id', 'course_id'),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    progress = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    preferences = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="courses")
    course = relationship("Course", back_populates="users")

# =================== SPACED REPETITION MODELS ===================

class LearningCard(Base):
    __tablename__ = "learning_cards"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    concept_id = Column(String, nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    card_type = Column(SQLEnum(CardType), default=CardType.BASIC)
    difficulty = Column(Float, default=0.5, index=True)
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=1)
    repetitions = Column(Integer, default=0)
    next_review = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    last_reviewed = Column(DateTime, nullable=True)
    review_count = Column(Integer, default=0)
    total_quality = Column(Float, default=0.0)
    context_tags = Column(JSON, default=list)
    source_material = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="learning_cards")
    course = relationship("Course", back_populates="learning_cards")
    reviews = relationship("CardReview", back_populates="card")
    study_sessions = relationship("StudySessionCard", back_populates="card")

    # Indexes for performance
    __table_args__ = (
        Index('idx_card_user_course', 'user_id', 'course_id'),
        Index('idx_card_next_review', 'next_review'),
        Index('idx_card_difficulty', 'difficulty'),
    )

    @validates('difficulty')
    def validate_difficulty(self, key, difficulty):
        if not 0 <= difficulty <= 1:
            raise ValueError('Difficulty must be between 0 and 1')
        return difficulty

class CardReview(Base):
    __tablename__ = "card_reviews"

    id = Column(String, primary_key=True, index=True)
    card_id = Column(String, ForeignKey("learning_cards.id"), nullable=False)
    session_id = Column(String, ForeignKey("study_sessions.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    quality_rating = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=True)
    new_interval_days = Column(Integer, nullable=False)
    new_ease_factor = Column(Float, nullable=False)
    new_repetitions = Column(Integer, nullable=False)
    next_review = Column(DateTime, nullable=False)
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    card = relationship("LearningCard", back_populates="reviews")
    session = relationship("StudySession", back_populates="reviews")
    user = relationship("User")

    # Indexes for performance
    __table_args__ = (
        Index('idx_review_card_date', 'card_id', 'reviewed_at'),
        Index('idx_review_user_date', 'user_id', 'reviewed_at'),
    )

class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    session_type = Column(SQLEnum(SessionType), default=SessionType.MIXED)
    total_cards = Column(Integer, default=0)
    cards_reviewed = Column(Integer, default=0)
    correct_reviews = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="study_sessions")
    course = relationship("Course", back_populates="study_sessions")
    cards = relationship("StudySessionCard", back_populates="session")
    reviews = relationship("CardReview", back_populates="session")

class StudySessionCard(Base):
    __tablename__ = "study_session_cards"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("study_sessions.id"), nullable=False)
    card_id = Column(String, ForeignKey("learning_cards.id"), nullable=False)
    order = Column(Integer, default=0)
    is_reviewed = Column(Boolean, default=False)
    reviewed_at = Column(DateTime, nullable=True)
    quality_rating = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Relationships
    session = relationship("StudySession", back_populates="cards")
    card = relationship("LearningCard", back_populates="study_sessions")

# =================== ACTIVE RECALL MODELS ===================

class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    question_type = Column(SQLEnum(QuestionType), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)  # For multiple choice questions
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    bloom_level = Column(SQLEnum(BloomLevel), nullable=False)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=False, index=True)
    concept_ids = Column(JSON, default=list)  # Related concepts
    source_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    course = relationship("Course")
    attempts = relationship("QuestionAttempt", back_populates="question")

    __table_args__ = (
        Index('idx_question_course_difficulty', 'course_id', 'difficulty'),
        Index('idx_question_bloom_level', 'bloom_level'),
    )

class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id = Column(String, primary_key=True, index=True)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, ForeignKey("quiz_sessions.id"), nullable=True)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False, index=True)
    confidence_level = Column(Integer, default=3)  # 1-5 scale
    time_taken_seconds = Column(Integer, nullable=True)
    hints_used = Column(Integer, default=0)
    score_achieved = Column(Float, default=0.0)
    feedback = Column(Text, nullable=True)
    attempted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    question = relationship("Question", back_populates="attempts")
    user = relationship("User")
    session = relationship("QuizSession", back_populates="attempts")

class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    session_type = Column(SQLEnum(SessionType), default=SessionType.MIXED)
    current_question_index = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_score = Column(Float, default=0.0)
    max_score = Column(Float, default=0.0)
    time_limit_minutes = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User")
    course = relationship("Course")
    attempts = relationship("QuestionAttempt", back_populates="session")

# =================== DUAL CODING MODELS ===================

class VisualElement(Base):
    __tablename__ = "visual_elements"

    id = Column(String, primary_key=True, index=True)
    content_id = Column(String, nullable=True)  # Link to content if created from content
    element_type = Column(String, nullable=False)  # diagram, chart, mind_map, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    visual_data = Column(JSON, nullable=False)  # Contains the visual representation data
    target_audience = Column(String, default="intermediate")
    learning_style = Column(SQLEnum(LearningStyle), default=LearningStyle.BALANCED)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class DualCodingContent(Base):
    __tablename__ = "dual_coding_content"

    id = Column(String, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(SQLEnum(ContentType), default=ContentType.TEXT)
    visual_elements = Column(JSON, default=list)  # IDs of visual elements
    learning_path = Column(JSON, default=dict)  # Structured learning path
    enhancement_level = Column(Integer, default=1)  # 1-5 scale
    target_audience = Column(String, default="intermediate")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    course = relationship("Course")
    user = relationship("User")

# =================== METACOGNITION MODELS ===================

class MetacognitiveSession(Base):
    __tablename__ = "metacognitive_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    session_type = Column(SQLEnum(SessionType), default=SessionType.COMPREHENSIVE)
    phase = Column(SQLEnum(MetacognitionPhase), default=MetacognitionPhase.PLANNING)
    learning_context = Column(JSON, default=dict)
    self_assessment = Column(JSON, default=dict)  # User's self-assessment data
    regulation_strategies = Column(JSON, default=list)  # Used regulation strategies
    insights = Column(Text, nullable=True)  # Key insights from the session
    effectiveness_rating = Column(Integer, nullable=True)  # 1-5 scale
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="metacognitive_sessions")
    course = relationship("Course", back_populates="metacognitive_sessions")
    activities = relationship("ReflectionActivity", back_populates="session")

class ReflectionActivity(Base):
    __tablename__ = "reflection_activities"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("metacognitive_sessions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    activity_type = Column(SQLEnum(ReflectionType), nullable=False)
    reflection_prompts = Column(JSON, default=list)
    user_responses = Column(JSON, default=list)
    duration_minutes = Column(Integer, nullable=True)
    effectiveness_score = Column(Float, nullable=True)
    insights_generated = Column(JSON, default=list)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("MetacognitiveSession", back_populates="activities")
    user = relationship("User")

# =================== ELABORATION NETWORK MODELS ===================

class Concept(Base):
    __tablename__ = "concepts"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    difficulty = Column(Float, default=0.5)
    mastery_level = Column(Float, default=0.0, index=True)
    prerequisite_ids = Column(JSON, default=list)  # IDs of prerequisite concepts
    related_ids = Column(JSON, default=list)  # IDs of related concepts
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    course = relationship("Course")
    source_connections = relationship("ConceptConnection", foreign_keys="ConceptConnection.source_concept_id", back_populates="source_concept")
    target_connections = relationship("ConceptConnection", foreign_keys="ConceptConnection.target_concept_id", back_populates="target_concept")

class ConceptConnection(Base):
    __tablename__ = "concept_connections"

    id = Column(String, primary_key=True, index=True)
    source_concept_id = Column(String, ForeignKey("concepts.id"), nullable=False)
    target_concept_id = Column(String, ForeignKey("concepts.id"), nullable=False)
    connection_type = Column(SQLEnum(ConnectionType), nullable=False)
    strength = Column(Float, default=0.5)  # 0-1 scale
    bidirectional = Column(Boolean, default=False)
    transfer_domains = Column(JSON, default=list)  # Applicable transfer domains
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    source_concept = relationship("Concept", foreign_keys=[source_concept_id], back_populates="source_connections")
    target_concept = relationship("Concept", foreign_keys=[target_concept_id], back_populates="target_connections")

    __table_args__ = (UniqueConstraint('source_concept_id', 'target_concept_id', 'connection_type'),)

class ElaborationNetwork(Base):
    __tablename__ = "elaboration_networks"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    network_data = Column(JSON, nullable=False)  # Complete network structure
    network_stats = Column(JSON, default=dict)  # Statistics about the network
    learning_objectives = Column(JSON, default=list)
    integration_level = Column(String, default="moderate")  # shallow, moderate, deep, transformative
    creation_method = Column(String, default="automatic")  # automatic, manual, hybrid
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User")
    course = relationship("Course")

# =================== ANALYTICS MODELS ===================

class UserAnalytics(Base):
    __tablename__ = "user_analytics"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=True)  # Course-specific or global
    metric_type = Column(String, nullable=False, index=True)  # cards_created, study_time, accuracy, etc.
    metric_value = Column(Float, nullable=False)
    context = Column(JSON, default=dict)  # Additional context for the metric
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User")
    course = relationship("Course")

    __table_args__ = (
        Index('idx_analytics_user_type_date', 'user_id', 'metric_type', 'recorded_at'),
    )