-- Active Recall Database Schema
-- Stores questions, sessions, attempts, and performance analytics

-- Questions table - stores generated questions
CREATE TABLE IF NOT EXISTS ar_questions (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('multiple_choice', 'short_answer', 'fill_in_blank', 'explanation', 'application')),
    bloom_level TEXT NOT NULL CHECK (bloom_level IN ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')),
    difficulty TEXT NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    question_data TEXT NOT NULL,  -- JSON data for question-specific content
    explanation TEXT NOT NULL,
    context_tags TEXT,  -- JSON array of context tags
    time_estimate_seconds INTEGER DEFAULT 60,
    points_possible INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Quiz sessions table - tracks quiz sessions
CREATE TABLE IF NOT EXISTS ar_quiz_sessions (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    user_id TEXT,
    questions TEXT NOT NULL,  -- JSON array of question IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    time_limit_minutes INTEGER,
    current_question_index INTEGER DEFAULT 0,
    total_score REAL DEFAULT 0.0,
    max_score REAL DEFAULT 0.0,
    session_config TEXT,  -- JSON config for session settings
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Question attempts table - stores user answers and performance
CREATE TABLE IF NOT EXISTS ar_question_attempts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    user_answer TEXT NOT NULL,  -- JSON data for user's answer
    time_taken_seconds INTEGER NOT NULL,
    confidence_level INTEGER DEFAULT 3 CHECK (confidence_level >= 1 AND confidence_level <= 5),
    hints_used INTEGER DEFAULT 0,
    is_correct BOOLEAN NOT NULL,
    score_achieved REAL DEFAULT 0.0 CHECK (score_achieved >= 0.0 AND score_achieved <= 1.0),
    correct_answer TEXT NOT NULL,  -- JSON data for correct answer
    explanation_feedback TEXT,
    specific_feedback TEXT,
    improvement_suggestions TEXT,  -- JSON array of suggestions
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES ar_quiz_sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES ar_questions (id) ON DELETE CASCADE
);

-- Performance tracking by concept
CREATE TABLE IF NOT EXISTS ar_concept_performance (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    concept TEXT NOT NULL,
    mastery_level REAL DEFAULT 0.0 CHECK (mastery_level >= 0.0 AND mastery_level <= 1.0),
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    recent_accuracy REAL DEFAULT 0.0,
    improvement_trend TEXT DEFAULT 'stable' CHECK (improvement_trend IN ('improving', 'stable', 'declining')),
    recommended_focus BOOLEAN DEFAULT FALSE,
    last_attempted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    UNIQUE(user_id, course_id, concept)
);

-- Learning recommendations cache
CREATE TABLE IF NOT EXISTS ar_learning_recommendations (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    recommended_difficulty TEXT CHECK (recommended_difficulty IN ('easy', 'medium', 'hard')),
    suggested_question_types TEXT,  -- JSON array
    suggested_bloom_levels TEXT,  -- JSON array
    focus_concepts TEXT,  -- JSON array
    review_concepts TEXT,  -- JSON array
    study_time_recommendation INTEGER,  -- minutes per session
    practice_frequency TEXT CHECK (practice_frequency IN ('daily', 'every_other_day', 'twice_weekly', 'weekly')),
    performance_metrics TEXT,  -- JSON performance data
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Question generation cache
CREATE TABLE IF NOT EXISTS ar_question_cache (
    id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    course_id TEXT NOT NULL,
    generation_params TEXT NOT NULL,  -- JSON parameters used for generation
    cached_questions TEXT NOT NULL,  -- JSON array of generated questions
    concepts_extracted TEXT,  -- JSON array of concepts
    hit_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Adaptive difficulty progression
CREATE TABLE IF NOT EXISTS ar_difficulty_progression (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    date TEXT NOT NULL,  -- YYYY-MM-DD format
    easy_accuracy REAL DEFAULT 0.0,
    medium_accuracy REAL DEFAULT 0.0,
    hard_accuracy REAL DEFAULT 0.0,
    overall_accuracy REAL DEFAULT 0.0,
    questions_attempted INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    UNIQUE(user_id, course_id, date)
);

-- Learning analytics aggregation
CREATE TABLE IF NOT EXISTS ar_learning_analytics (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    period_days INTEGER NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    total_questions_attempted INTEGER DEFAULT 0,
    overall_accuracy REAL DEFAULT 0.0,
    avg_confidence_level REAL DEFAULT 0.0,
    learning_velocity REAL DEFAULT 0.0,  -- questions mastered per week
    retention_rate REAL DEFAULT 0.0,
    question_type_stats TEXT,  -- JSON stats by question type
    bloom_level_stats TEXT,  -- JSON stats by Bloom level
    difficulty_progression TEXT,  -- JSON progression data
    concept_performance TEXT,  -- JSON concept performance
    improvement_areas TEXT,  -- JSON array of improvement areas
    strengths TEXT,  -- JSON array of strengths
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_ar_questions_course_id ON ar_questions(course_id);
CREATE INDEX IF NOT EXISTS idx_ar_questions_type ON ar_questions(type);
CREATE INDEX IF NOT EXISTS idx_ar_questions_difficulty ON ar_questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_ar_questions_bloom_level ON ar_questions(bloom_level);
CREATE INDEX IF NOT EXISTS idx_ar_questions_created_at ON ar_questions(created_at);

CREATE INDEX IF NOT EXISTS idx_ar_sessions_course_id ON ar_quiz_sessions(course_id);
CREATE INDEX IF NOT EXISTS idx_ar_sessions_user_id ON ar_quiz_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_ar_sessions_created_at ON ar_quiz_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_ar_sessions_status ON ar_quiz_sessions(started_at, completed_at);

CREATE INDEX IF NOT EXISTS idx_ar_attempts_session_id ON ar_question_attempts(session_id);
CREATE INDEX IF NOT EXISTS idx_ar_attempts_question_id ON ar_question_attempts(question_id);
CREATE INDEX IF NOT EXISTS idx_ar_attempts_user_id ON ar_question_attempts(id); -- User can be derived from session
CREATE INDEX IF NOT EXISTS idx_ar_attempts_attempted_at ON ar_question_attempts(attempted_at);
CREATE INDEX IF NOT EXISTS idx_ar_attempts_correct ON ar_question_attempts(is_correct);

CREATE INDEX IF NOT EXISTS idx_concept_performance_user_course ON ar_concept_performance(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_concept_performance_concept ON ar_concept_performance(concept);
CREATE INDEX IF NOT EXISTS idx_concept_performance_mastery ON ar_concept_performance(mastery_level);
CREATE INDEX IF NOT EXISTS idx_concept_performance_updated ON ar_concept_performance(updated_at);

CREATE INDEX IF NOT EXISTS idx_recommendations_user_course ON ar_learning_recommendations(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_valid_until ON ar_learning_recommendations(valid_until);

CREATE INDEX IF NOT EXISTS idx_question_cache_content_hash ON ar_question_cache(content_hash);
CREATE INDEX IF NOT EXISTS idx_question_cache_course_id ON ar_question_cache(course_id);
CREATE INDEX IF NOT EXISTS idx_question_cache_expires_at ON ar_question_cache(expires_at);

CREATE INDEX IF NOT EXISTS idx_difficulty_progression_user_course ON ar_difficulty_progression(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_difficulty_progression_date ON ar_difficulty_progression(date);

CREATE INDEX IF NOT EXISTS idx_analytics_user_course ON ar_learning_analytics(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_analytics_valid_until ON ar_learning_analytics(valid_until);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_ar_questions_timestamp
    AFTER UPDATE ON ar_questions
    FOR EACH ROW
BEGIN
    UPDATE ar_questions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_concept_performance_timestamp
    AFTER UPDATE ON ar_concept_performance
    FOR EACH ROW
BEGIN
    UPDATE ar_concept_performance SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;