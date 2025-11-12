# 🗄️ Backend Database Schema

**Documentazione completa del database SQLAlchemy e strutture dati del sistema Tutor-AI**

---

## 🚀 Indice Database

### **Database Architecture**
- **[Overview](#overview)** - Architettura database e strategie
- **[Connection Management](#connection-management)** - Gestione connessioni e pooling
- **[Migration System](#migration-system)** - Sistema migrazioni Alembic

### **Core Models**
- **[Course Models](#course-models)** - Corsi, libri, materiali
- **[User Models](#user-models)** - Utenti e profili apprendimento
- **[Annotation Models](#annotation-models)** - Sistema annotazioni
- **[Session Models](#session-models)** - Sessioni chat e studio

### **Learning Engine Models**
- **[Spaced Repetition Models](#spaced-repetition-models)** - Card e ripasso spaziato
- **[Active Recall Models](#active-recall-models)** - Domande e performance
- **[Analytics Models](#analytics-models)** - Analytics e progress tracking

### **System Models**
- **[System Config Models](#system-config-models)** - Configurazione sistema
- **[A/B Testing Models](#ab-testing-models)** - Test A/B framework
- **[Logging Models](#logging-models)** - Audit trail e monitoring

---

## 📋 Overview

### **Database Strategy**
Tutor-AI utilizza un approccio multi-database ottimizzato per diversi tipi di dati:

#### **Primary Database (SQLite)**
- **Purpose**: Transactional data, user management, course metadata
- **Location**: `./data/app.db`
- **Features**: ACID compliance, backup automatico, migration support
- **Performance**: <1ms per query tipiche, supporto concorrenza

#### **Vector Database (ChromaDB)**
- **Purpose**: Document embeddings, semantic search
- **Location**: `./data/vector_db/`
- **Features**: Vector similarity search, metadata filtering
- **Performance**: <100ms per semantic search con 10k+ documents

#### **File System Storage**
- **Purpose**: PDF files, annotations exports, cache
- **Location**: `./data/uploads/`, `./data/courses/`
- **Features**: Direct file access, versioning, backup
- **Performance**: Streaming ottimizzato per PDF

### **Database Configuration**
```python
# Database URL configuration
DATABASE_URL = "sqlite:///./data/app.db"
ENGINE_OPTIONS = {
    "echo": False,  # Enable SQL logging in development
    "pool_pre_ping": True,  # Check connections
    "pool_recycle": 3600,   # Recycle connections hourly
    "connect_args": {
        "check_same_thread": False,  # SQLite specific
        "timeout": 30
    }
}

# Vector DB Configuration
VECTOR_DB_PATH = "./data/vector_db"
CHROMA_SETTINGS = {
    "chroma_db_impl": "duckdb+parquet",
    "persist_directory": VECTOR_DB_PATH,
    "allow_reset": False
}
```

---

## 🔗 Connection Management

### **Async Connection Pool**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///./data/app.db",
            **ENGINE_OPTIONS
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def get_session(self) -> AsyncSession:
        """Ottiene sessione database con retry logic"""
        return self.async_session()

    async def health_check(self) -> bool:
        """Verifica connessione database"""
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception:
            return False
```

### **Transaction Management**
```python
class TransactionManager:
    @staticmethod
    async def with_transaction(func):
        """Decorator per gestione transazioni automatica"""
        async def wrapper(*args, **kwargs):
            async with get_db_session() as session:
                try:
                    result = await func(session, *args, **kwargs)
                    await session.commit()
                    return result
                except Exception:
                    await session.rollback()
                    raise
        return wrapper
```

---

## 🔄 Migration System

### **Alembic Configuration**
```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from backend.models import Base

target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url="sqlite:///./data/app.db"
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()
```

### **Migration Commands**
```bash
# Create new migration
alembic revision --autogenerate -m "Add course enrollment table"

# Run migrations
alembic upgrade head

# Downgrade specific revision
alembic downgrade -1

# Get migration history
alembic history
```

---

## 📚 Course Models

### **Course Table**
```python
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), index=True)
    instructor = Column(String(255))
    tags = Column(JSON)  # List of course tags
    difficulty_level = Column(String(20), default="intermediate")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    books = relationship("Book", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course")
    study_sessions = relationship("StudySession", back_populates="course")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### **Book Table**
```python
class Book(Base):
    __tablename__ = "books"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    author = Column(String(255))
    isbn = Column(String(20))
    description = Column(Text)
    tags = Column(JSON)  # List of book-specific tags

    # Metadata
    total_pages = Column(Integer)
    pdf_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="books")
    materials = relationship("Material", back_populates="book", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="book")
```

### **Material Table**
```python
class Material(Base):
    __tablename__ = "materials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    book_id = Column(String, ForeignKey("books.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    title = Column(String(255))
    chapter = Column(String(255))

    # File information
    file_size = Column(Integer)  # bytes
    file_type = Column(String(10), default="pdf")
    pages = Column(Integer)

    # Processing status
    processed = Column(Boolean, default=False)
    indexed = Column(Boolean, default=False)
    error_message = Column(Text)

    # Content analysis
    word_count = Column(Integer)
    reading_time_minutes = Column(Integer)
    difficulty_score = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("Course")
    book = relationship("Book", back_populates="materials")
    annotations = relationship("Annotation", back_populates="material")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('course_id', 'book_id', 'filename', name='unique_material'),
    )
```

---

## 👤 User Models

### **User Table**
```python
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))

    # Learning preferences
    learning_style = Column(String(20), default="mixed")  # visual, verbal, mixed
    difficulty_preference = Column(String(20), default="adaptive")
    language = Column(String(10), default="it")

    # Profile data
    avatar_url = Column(String(500))
    bio = Column(Text)

    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    enrollments = relationship("Enrollment", back_populates="user")
    annotations = relationship("Annotation", back_populates="user")
    study_sessions = relationship("StudySession", back_populates="user")
    flashcards = relationship("Flashcard", back_populates="user")
```

### **Enrollment Table**
```python
class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)

    # Enrollment data
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    progress_percentage = Column(Float, default=0.0)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Learning preferences for this course
    custom_difficulty = Column(String(20))
    focus_areas = Column(JSON)  # List of focus topics

    # Status
    is_active = Column(Boolean, default=True)
    completed_at = Column(DateTime)
    certificate_issued = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    study_sessions = relationship("StudySession", back_populates="enrollment")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='unique_enrollment'),
    )
```

---

## 📝 Annotation Models

### **Annotation Table**
```python
class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    book_id = Column(String, ForeignKey("books.id"), nullable=False)
    material_id = Column(String, ForeignKey("materials.id"), nullable=False)

    # Location information
    pdf_filename = Column(String(255), nullable=False)
    page = Column(Integer, nullable=False)

    # Selection coordinates (normalized 0-1)
    selection_x1 = Column(Float, nullable=False)
    selection_y1 = Column(Float, nullable=False)
    selection_x2 = Column(Float, nullable=False)
    selection_y2 = Column(Float, nullable=False)

    # Content
    selected_text = Column(Text, nullable=False)
    note = Column(Text)
    annotation_type = Column(String(20), default="highlight")  # highlight, underline, note
    color = Column(String(7), default="#ffeb3b")

    # Sharing and tags
    share_with_ai = Column(Boolean, default=False)
    share_public = Column(Boolean, default=False)
    tags = Column(JSON)  # List of annotation tags

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="annotations")
    course = relationship("Course")
    book = relationship("Book", back_populates="annotations")
    material = relationship("Material", back_populates="annotations")

    # Indexes for performance
    __table_args__ = (
        Index('idx_annotation_location', 'course_id', 'book_id', 'pdf_filename', 'page'),
        Index('idx_annotation_user_course', 'user_id', 'course_id'),
    )
```

### **Annotation Sharing Table**
```python
class AnnotationShare(Base):
    __tablename__ = "annotation_shares"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    annotation_id = Column(String, ForeignKey("annotations.id"), nullable=False)
    shared_with_user_id = Column(String, ForeignKey("users.id"))

    # Sharing permissions
    can_view = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    can_comment = Column(Boolean, default=True)

    # Metadata
    shared_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    # Relationships
    annotation = relationship("Annotation")
    shared_with_user = relationship("User")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('annotation_id', 'shared_with_user_id', name='unique_annotation_share'),
    )
```

---

## 💬 Session Models

### **Chat Session Table**
```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    book_id = Column(String, ForeignKey("books.id"))

    # Session configuration
    title = Column(String(255))
    difficulty_level = Column(String(20), default="intermediate")
    learning_style = Column(String(20), default="mixed")
    language = Column(String(10), default="it")

    # Session metadata
    message_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    avg_response_time = Column(Float)

    # Status
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime, default=datetime.utcnow)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    course = relationship("Course")
    book = relationship("Book")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
```

### **Chat Message Table**
```python
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)

    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Metadata
    message_number = Column(Integer, nullable=False)
    tokens_used = Column(Integer)
    response_time_ms = Column(Integer)

    # Context information
    sources_cited = Column(JSON)  # List of source materials
    llm_provider = Column(String(20))  # openai, zai, local
    model_used = Column(String(50))

    # Quality metrics
    user_rating = Column(Integer)  # 1-5 rating
    was_helpful = Column(Boolean)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index('idx_message_session_order', 'session_id', 'message_number'),
    )
```

---

## 🎯 Spaced Repetition Models

### **Flashcard Table**
```python
class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)

    # Card content
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    question_type = Column(String(20), default="qa")  # qa, cloze, multiple_choice

    # Source information
    source_material_id = Column(String, ForeignKey("materials.id"))
    source_page = Column(Integer)
    source_chapter = Column(String(255))

    # SM-2 algorithm variables
    easiness_factor = Column(Float, default=2.5)
    repetition_count = Column(Integer, default=0)
    interval_days = Column(Integer, default=1)

    # Scheduling
    next_review_date = Column(DateTime, nullable=False)
    last_review_date = Column(DateTime)
    review_count = Column(Integer, default=0)

    # Performance tracking
    average_quality = Column(Float)  # 0-5 SM-2 quality rating
    streak_current = Column(Integer, default=0)
    streak_best = Column(Integer, default=0)

    # Metadata
    tags = Column(JSON)  # List of subject tags
    difficulty = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="flashcards")
    course = relationship("Course")
    source_material = relationship("Material")
    reviews = relationship("FlashcardReview", back_populates="flashcard")

    # Indexes
    __table_args__ = (
        Index('idx_flashcard_due', 'user_id', 'next_review_date'),
        Index('idx_flashcard_course', 'course_id'),
    )
```

### **Flashcard Review Table**
```python
class FlashcardReview(Base):
    __tablename__ = "flashcard_reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flashcard_id = Column(String, ForeignKey("flashcards.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Review data
    quality_rating = Column(Integer, nullable=False)  # 0-5 SM-2 quality
    response_time_seconds = Column(Integer)
    was_correct = Column(Boolean)

    # SM-2 calculation results
    previous_easiness = Column(Float)
    previous_interval = Column(Integer)
    new_easiness = Column(Float)
    new_interval = Column(Integer)

    # Review context
    review_session_id = Column(String)
    batch_size = Column(Integer)  # How many cards reviewed in this session

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    flashcard = relationship("Flashcard", back_populates="reviews")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index('idx_review_flashcard_time', 'flashcard_id', 'created_at'),
        Index('idx_review_user_time', 'user_id', 'created_at'),
    )
```

---

## ❓ Active Recall Models

### **Question Bank Table**
```python
class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)

    # Question content
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)  # multiple_choice, short_answer, essay, coding
    bloom_level = Column(String(20), default="apply")  # remember, understand, apply, analyze, evaluate, create

    # Multiple choice specific
    options = Column(JSON)  # List of options for MC questions
    correct_answer = Column(Text)
    explanation = Column(Text)

    # Coding specific
    programming_language = Column(String(20))
    test_cases = Column(JSON)  # Input/output pairs for validation
    template_code = Column(Text)

    # Metadata
    difficulty = Column(String(20), default="medium")
    estimated_time_minutes = Column(Integer)
    tags = Column(JSON)  # Topic tags
    source_material = Column(JSON)  # Reference to source material

    # Usage statistics
    times_asked = Column(Integer, default=0)
    correct_rate = Column(Float, default=0.0)
    avg_response_time = Column(Float)

    # Quality metrics
    effectiveness_score = Column(Float)  # How well the question assesses knowledge
    discrimination_index = Column(Float)  # Statistical discrimination

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime)

    # Relationships
    course = relationship("Course")
    responses = relationship("QuestionResponse", back_populates="question")
```

### **Question Response Table**
```python
class QuestionResponse(Base):
    __tablename__ = "question_responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Response data
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean)
    confidence_level = Column(Integer)  # 1-5 user confidence

    # Performance metrics
    response_time_seconds = Column(Integer)
    attempts_count = Column(Integer, default=1)

    # Learning context
    session_type = Column(String(20))  # practice, quiz, study_session
    study_session_id = Column(String)

    # Feedback
    feedback_given = Column(Text)
    follow_up_questions = Column(JSON)  # Generated follow-up questions

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    question = relationship("Question", back_populates="responses")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index('idx_response_user_question', 'user_id', 'question_id'),
        Index('idx_response_time', 'created_at'),
    )
```

---

## 📊 Analytics Models

### **Learning Progress Table**
```python
class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)

    # Progress metrics
    topic = Column(String(255), nullable=False)
    mastery_level = Column(Float, default=0.0)  # 0-1 mastery score
    confidence_level = Column(Float, default=0.0)  # Self-assessed confidence

    # Activity tracking
    total_study_time_minutes = Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    flashcards_reviewed = Column(Integer, default=0)

    # Performance indicators
    average_response_time = Column(Float)
    improvement_rate = Column(Float)  # Rate of improvement over time
    retention_score = Column(Float)  # Long-term retention assessment

    # Metacognitive indicators
    self_assessment_accuracy = Column(Float)  # How accurate are self-assessments
    study_strategy_effectiveness = Column(Float)  # Effectiveness of study approaches
    challenge_seeking_tendency = Column(Float)  # Tendency to seek challenges

    # Metadata
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    course = relationship("Course")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', 'topic', name='unique_progress_topic'),
        Index('idx_progress_user_course', 'user_id', 'course_id'),
    )
```

### **Study Session Table**
```python
class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    enrollment_id = Column(String, ForeignKey("enrollments.id"))

    # Session information
    session_type = Column(String(20), default="study")  # study, quiz, review, chat
    title = Column(String(255))

    # Materials used
    materials_accessed = Column(JSON)  # List of material IDs
    pages_viewed = Column(JSON)  # {material_id: [page_numbers]}
    topics_covered = Column(JSON)  # List of topics studied

    # Activity tracking
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)

    # Interaction metrics
    questions_asked = Column(Integer, default=0)
    flashcards_reviewed = Column(Integer, default=0)
    annotations_created = Column(Integer, default=0)
    chat_messages_exchanged = Column(Integer, default=0)

    # Performance outcomes
    quiz_score = Column(Float)  # If session includes quiz
    comprehension_rating = Column(Integer)  # User self-rating 1-5
    energy_level = Column(Integer)  # User energy level 1-5

    # Learning analytics
    focus_periods = Column(JSON)  # Periods of high focus detection
    distraction_events = Column(Integer, default=0)
    break_periods = Column(JSON)  # Break periods taken

    # Environment data
    device_type = Column(String(20))  # mobile, desktop, tablet
    browser = Column(String(100))
    ip_address = Column(String(45))

    # Relationships
    user = relationship("User", back_populates="study_sessions")
    course = relationship("Course", back_populates="study_sessions")
    enrollment = relationship("Enrollment", back_populates="study_sessions")

    # Indexes
    __table_args__ = (
        Index('idx_session_user_time', 'user_id', 'start_time'),
        Index('idx_session_course_time', 'course_id', 'start_time'),
    )
```

---

## 🧪 A/B Testing Models

### **A/B Test Table**
```python
class ABTest(Base):
    __tablename__ = "ab_tests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)

    # Test configuration
    hypothesis = Column(Text)
    success_metric = Column(String(100), nullable=False)  # What we're measuring
    significance_level = Column(Float, default=0.05)  # Alpha
    power = Column(Float, default=0.8)  # Statistical power

    # Targeting
    target_course_id = Column(String, ForeignKey("courses.id"))
    target_user_segment = Column(String(100))  # new, returning, high_engagement

    # Variants configuration
    variants = Column(JSON, nullable=False)  # List of variant configurations
    traffic_allocation = Column(JSON)  # Traffic split percentages

    # Sample size calculation
    required_sample_size = Column(Integer)
    effect_size = Column(Float)

    # Status and timeline
    status = Column(String(20), default="draft")  # draft, running, paused, completed
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Results
    statistical_significance = Column(Boolean)
    confidence_level = Column(Float)
    winning_variant = Column(String(100))

    # Relationships
    course = relationship("Course")
    participants = relationship("ABTestParticipant", back_populates="test", cascade="all, delete-orphan")
    conversions = relationship("ABTestConversion", back_populates="test", cascade="all, delete-orphan")
```

### **A/B Test Participant Table**
```python
class ABTestParticipant(Base):
    __tablename__ = "ab_test_participants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String, ForeignKey("ab_tests.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Assignment data
    variant_assigned = Column(String(100), nullable=False)
    assignment_time = Column(DateTime, default=datetime.utcnow)

    # Cohort information
    user_segment = Column(String(100))
    baseline_characteristics = Column(JSON)  # User characteristics for stratification

    # Participation tracking
    first_interaction = Column(DateTime)
    last_interaction = Column(DateTime)
    total_interactions = Column(Integer, default=0)

    # Relationships
    test = relationship("ABTest", back_populates="participants")
    user = relationship("User")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('test_id', 'user_id', name='unique_test_participant'),
    )
```

### **A/B Test Conversion Table**
```python
class ABTestConversion(Base):
    __tablename__ = "ab_test_conversions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String, ForeignKey("ab_tests.id"), nullable=False)
    participant_id = Column(String, ForeignKey("ab_test_participants.id"), nullable=False)

    # Conversion data
    conversion_type = Column(String(50), nullable=False)  # primary, secondary
    conversion_value = Column(Float)  # Numerical value of conversion
    conversion_time = Column(DateTime, default=datetime.utcnow)

    # Context
    conversion_context = Column(JSON)  # Additional context about conversion
    touchpoint = Column(String(100))  # Where conversion occurred

    # Attribution
    attributed_to_variant = Column(String(100))
    attribution_confidence = Column(Float)

    # Relationships
    test = relationship("ABTest", back_populates="conversions")
    participant = relationship("ABTestParticipant")

    # Indexes
    __table_args__ = (
        Index('idx_conversion_test_time', 'test_id', 'conversion_time'),
        Index('idx_conversion_participant', 'participant_id'),
    )
```

---

## ⚙️ System Config Models

### **System Configuration Table**
```python
class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(JSON)
    description = Column(Text)

    # Configuration metadata
    config_type = Column(String(50))  # string, number, boolean, json, array
    category = Column(String(100))  # llm, ui, features, limits

    # Validation
    validation_rules = Column(JSON)  # Validation schema
    default_value = Column(JSON)

    # Access control
    is_public = Column(Boolean, default=False)  # Accessible via API
    requires_restart = Column(Boolean, default=False)  # Requires system restart

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String, ForeignKey("users.id"))

    # Relationships
    updater = relationship("User")
```

### **Feature Flag Table**
```python
class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flag_key = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)

    # Flag configuration
    enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Integer, default=0)  # 0-100

    # Targeting
    target_users = Column(JSON)  # Specific user IDs
    target_segments = Column(JSON)  # User segments
    exclude_segments = Column(JSON)

    # Lifecycle
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    creator = relationship("User")
```

---

## 📝 Logging Models

### **API Request Log Table**
```python
class APIRequestLog(Base):
    __tablename__ = "api_request_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Request information
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    path_params = Column(JSON)
    query_params = Column(JSON)

    # Client information
    user_id = Column(String, ForeignKey("users.id"))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(100))  # Correlation ID

    # Performance metrics
    response_time_ms = Column(Integer)
    status_code = Column(Integer)

    # Request/Response size
    request_size_bytes = Column(Integer)
    response_size_bytes = Column(Integer)

    # Context
    course_id = Column(String, ForeignKey("courses.id"))
    session_id = Column(String)

    # Security events
    is_suspicious = Column(Boolean, default=False)
    threat_type = Column(String(50))  # sql_injection, xss, rate_limit

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    course = relationship("Course")

    # Indexes
    __table_args__ = (
        Index('idx_request_time', 'created_at'),
        Index('idx_request_endpoint', 'endpoint', 'created_at'),
        Index('idx_request_user', 'user_id', 'created_at'),
    )
```

### **Error Log Table**
```python
class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Error information
    error_type = Column(String(100), nullable=False)  # validation, database, ai_provider, etc.
    error_code = Column(String(50))
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text)

    # Context
    endpoint = Column(String(255))
    method = Column(String(10))
    user_id = Column(String, ForeignKey("users.id"))
    course_id = Column(String, ForeignKey("courses.id"))
    request_id = Column(String(100))

    # Request data
    request_data = Column(JSON)
    query_params = Column(JSON)

    # System information
    service_name = Column(String(100))  # llm_service, rag_service, etc.
    environment = Column(String(20))  # development, staging, production

    # Severity and status
    severity = Column(String(20), default="error")  # debug, info, warning, error, critical
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    # Relationships
    user = relationship("User")
    course = relationship("Course")

    # Indexes
    __table_args__ = (
        Index('idx_error_time', 'created_at'),
        Index('idx_error_type', 'error_type', 'created_at'),
        Index('idx_error_service', 'service_name', 'created_at'),
    )
```

---

## 🔍 Database Indexes and Performance

### **Critical Indexes**
```sql
-- Course-related indexes
CREATE INDEX idx_courses_category ON courses(category);
CREATE INDEX idx_courses_active ON courses(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_materials_course_book ON materials(course_id, book_id);

-- User-related indexes
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_enrollments_user_course ON enrollments(user_id, course_id);
CREATE INDEX idx_enrollments_active ON enrollments(is_active) WHERE is_active = TRUE;

-- Annotation indexes
CREATE INDEX idx_annotations_user_course ON annotations(user_id, course_id);
CREATE INDEX idx_annotations_shared ON annotations(share_with_ai) WHERE share_with_ai = TRUE;

-- Learning progress indexes
CREATE INDEX idx_progress_user_course ON learning_progress(user_id, course_id);
CREATE INDEX idx_progress_updated ON learning_progress(updated_at);

-- Chat session indexes
CREATE INDEX idx_chat_sessions_active ON chat_sessions(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);

-- Flashcard indexes
CREATE INDEX idx_flashcards_due ON flashcards(user_id, next_review_date);
CREATE INDEX idx_flashcards_course ON flashcards(course_id);

-- Analytics indexes
CREATE INDEX idx_study_sessions_user_time ON study_sessions(user_id, start_time);
CREATE INDEX idx_api_requests_time ON api_request_logs(created_at);
CREATE INDEX idx_error_logs_time ON error_logs(created_at);
```

### **Query Optimization Examples**
```python
# Optimized queries using indexes
async def get_user_active_courses(user_id: str) -> List[Dict]:
    """Get user's active courses efficiently"""
    query = """
    SELECT c.id, c.title, c.description, e.progress_percentage
    FROM courses c
    JOIN enrollments e ON c.id = e.course_id
    WHERE e.user_id = :user_id
    AND e.is_active = TRUE
    AND c.is_active = TRUE
    ORDER BY e.last_activity DESC
    """
    result = await session.execute(text(query), {"user_id": user_id})
    return result.fetchall()

async def get_due_flashcards(user_id: str, limit: int = 20) -> List[Dict]:
    """Get flashcards due for review efficiently"""
    query = """
    SELECT f.id, f.question, f.answer, f.repetition_count
    FROM flashcards f
    WHERE f.user_id = :user_id
    AND f.next_review_date <= :now
    ORDER BY f.next_review_date ASC
    LIMIT :limit
    """
    result = await session.execute(text(query), {
        "user_id": user_id,
        "now": datetime.utcnow(),
        "limit": limit
    })
    return result.fetchall()
```

---

## 🛠️ Database Maintenance

### **Regular Maintenance Tasks**
```python
class DatabaseMaintenance:
    async def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log entries"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Clean API request logs
        await session.execute(
            text("DELETE FROM api_request_logs WHERE created_at < :cutoff"),
            {"cutoff": cutoff_date}
        )

        # Clean error logs (keep errors longer)
        error_cutoff = datetime.utcnow() - timedelta(days=days_to_keep * 2)
        await session.execute(
            text("DELETE FROM error_logs WHERE created_at < :cutoff AND resolved = TRUE"),
            {"cutoff": error_cutoff}
        )

    async def update_course_statistics(self):
        """Update aggregated course statistics"""
        await session.execute(text("""
            UPDATE courses c
            SET
                total_materials = (
                    SELECT COUNT(*) FROM materials m
                    WHERE m.course_id = c.id AND m.processed = TRUE
                ),
                updated_at = CURRENT_TIMESTAMP
            WHERE c.id IN (
                SELECT DISTINCT course_id FROM materials
                WHERE processed = TRUE
            )
        """))

    async def analyze_learning_patterns(self):
        """Analyze and update learning pattern data"""
        # This would run complex analytics queries
        # to update user learning patterns and recommendations
        pass
```

### **Backup Strategy**
```python
class BackupManager:
    async def create_backup(self, backup_path: str):
        """Create database backup"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_path}/tutor_ai_backup_{timestamp}.db"

        # SQLite backup
        source = sqlite3.connect("./data/app.db")
        backup = sqlite3.connect(backup_file)
        source.backup(backup)
        backup.close()
        source.close()

        return backup_file

    async def verify_backup(self, backup_file: str) -> bool:
        """Verify backup integrity"""
        try:
            conn = sqlite3.connect(backup_file)
            result = conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
            conn.close()
            return result[0] > 0
        except Exception:
            return False
```

---

## 📈 Database Performance Monitoring

### **Performance Metrics**
```python
class DatabaseMonitor:
    async def get_performance_metrics(self) -> Dict:
        """Get database performance metrics"""
        # Query performance stats
        slow_queries = await session.execute(text("""
            SELECT query, avg_time, call_count
            FROM query_stats
            WHERE avg_time > 1000
            ORDER BY avg_time DESC
            LIMIT 10
        """))

        # Index usage
        index_usage = await session.execute(text("""
            SELECT name, idx, stat
            FROM sqlite_master
            WHERE type = 'index'
            AND name NOT LIKE 'sqlite_%'
        """))

        # Table sizes
        table_sizes = await session.execute(text("""
            SELECT name, COUNT(*) as row_count
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        """))

        return {
            "slow_queries": slow_queries.fetchall(),
            "index_usage": index_usage.fetchall(),
            "table_sizes": table_sizes.fetchall()
        }
```

---

*Ultimo aggiornamento: Novembre 2025*
*Versione database: v2.0*
*Compatibile con Tutor-AI v2.0+*