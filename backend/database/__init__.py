"""
Database Package for CLE System
Contains models, connection management, and migrations
"""

from .connection import (
    Base, engine, SessionLocal, get_db, create_tables, drop_tables,
    reset_database, get_database_info, check_database_health,
    DatabaseTransaction, execute_transaction, initialize_database
)

from .models import (
    # User models
    User, Course, UserCourse,

    # Spaced Repetition models
    LearningCard, CardReview, StudySession, StudySessionCard,

    # Active Recall models
    Question, QuestionAttempt, QuizSession,

    # Dual Coding models
    VisualElement, DualCodingContent,

    # Metacognition models
    MetacognitiveSession, ReflectionActivity,

    # Elaboration Network models
    Concept, ConceptConnection, ElaborationNetwork,

    # Analytics models
    UserAnalytics
)

from .migrations import (
    Migration, MigrationManager, migration_manager,
    migrate_database, rollback_database, get_database_schema_info
)

__all__ = [
    # Connection and utilities
    "Base", "engine", "SessionLocal", "get_db", "create_tables", "drop_tables",
    "reset_database", "get_database_info", "check_database_health",
    "DatabaseTransaction", "execute_transaction", "initialize_database",

    # Models
    "User", "Course", "UserCourse",
    "LearningCard", "CardReview", "StudySession", "StudySessionCard",
    "Question", "QuestionAttempt", "QuizSession",
    "VisualElement", "DualCodingContent",
    "MetacognitiveSession", "ReflectionActivity",
    "Concept", "ConceptConnection", "ElaborationNetwork",
    "UserAnalytics",

    # Migrations
    "Migration", "MigrationManager", "migration_manager",
    "migrate_database", "rollback_database", "get_database_schema_info"
]

# Package version
__version__ = "1.0.0"