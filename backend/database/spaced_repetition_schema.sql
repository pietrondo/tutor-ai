-- Spaced Repetition Database Schema
-- Implements enhanced SM-2 algorithm with cognitive adjustments

-- Learning cards table
CREATE TABLE IF NOT EXISTS learning_cards (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    concept_id TEXT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    card_type TEXT DEFAULT 'basic' CHECK (card_type IN ('basic', 'cloze', 'concept', 'application')),
    difficulty REAL DEFAULT 0.5 CHECK (difficulty >= 0.0 AND difficulty <= 1.0),
    ease_factor REAL DEFAULT 2.5 CHECK (ease_factor >= 1.3 AND ease_factor <= 2.5),
    interval_days INTEGER DEFAULT 1,
    repetitions INTEGER DEFAULT 0,
    next_review TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed TIMESTAMP,
    review_count INTEGER DEFAULT 0,
    total_quality REAL DEFAULT 0.0 CHECK (total_quality >= 0.0 AND total_quality <= 5.0),
    context_tags TEXT,  -- JSON array
    source_material TEXT,
    cognitive_load_estimate REAL DEFAULT 1.0 CHECK (cognitive_load_estimate >= 0.1 AND cognitive_load_estimate <= 5.0),
    mastery_level REAL DEFAULT 0.0 CHECK (mastery_level >= 0.0 AND mastery_level <= 1.0),
    last_performance_rating INTEGER,  -- 0-5 scale
    average_response_time INTEGER DEFAULT 0,  -- milliseconds
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Study sessions table
CREATE TABLE IF NOT EXISTS study_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    cards_studied INTEGER DEFAULT 0,
    new_cards INTEGER DEFAULT 0,
    review_cards INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    total_time_seconds INTEGER DEFAULT 0,
    average_response_time INTEGER DEFAULT 0,
    session_rating INTEGER CHECK (session_rating >= 1 AND session_rating <= 5),
    session_type TEXT DEFAULT 'mixed' CHECK (session_type IN ('new', 'review', 'mixed', 'cram')),
    cognitive_load_experienced REAL CHECK (cognitive_load_experienced >= 1.0 AND cognitive_load_experienced <= 5.0),
    focus_level INTEGER CHECK (focus_level >= 1 AND focus_level <= 5),
    interruptions_count INTEGER DEFAULT 0,
    adaptation_suggestions TEXT,  -- JSON array
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Review sessions table (individual card reviews)
CREATE TABLE IF NOT EXISTS review_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    card_id TEXT NOT NULL,
    quality_rating INTEGER NOT NULL CHECK (quality_rating >= 0 AND quality_rating <= 5),
    response_time_ms INTEGER NOT NULL,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    previous_interval INTEGER,
    new_interval INTEGER,
    previous_ease_factor REAL,
    new_ease_factor REAL,
    previous_repetitions INTEGER,
    new_repetitions INTEGER,
    cognitive_adjustment REAL DEFAULT 0.0,
    difficulty_adjustment REAL DEFAULT 0.0,
    hint_used BOOLEAN DEFAULT FALSE,
    confidence_level INTEGER CHECK (confidence_level >= 1 AND confidence_level <= 5),
    FOREIGN KEY (session_id) REFERENCES study_sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES learning_cards (id) ON DELETE CASCADE
);

-- Card collections table (for organizing cards)
CREATE TABLE IF NOT EXISTS card_collections (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    collection_type TEXT DEFAULT 'custom' CHECK (collection_type IN ('auto_generated', 'custom', 'difficulty_based', 'concept_based')),
    card_count INTEGER DEFAULT 0,
    last_studied TIMESTAMP,
    average_mastery REAL DEFAULT 0.0 CHECK (average_mastery >= 0.0 AND average_mastery <= 1.0),
    study_frequency INTEGER DEFAULT 0,  -- times per week
    priority_level INTEGER DEFAULT 2 CHECK (priority_level >= 1 AND priority_level <= 5),
    tags TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Card collection membership table
CREATE TABLE IF NOT EXISTS card_collection_memberships (
    id TEXT PRIMARY KEY,
    collection_id TEXT NOT NULL,
    card_id TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by TEXT,  -- user or system
    reason TEXT,  -- why card was added
    mastery_when_added REAL,
    FOREIGN KEY (collection_id) REFERENCES card_collections (id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES learning_cards (id) ON DELETE CASCADE,
    UNIQUE(collection_id, card_id)
);

-- Learning analytics table
CREATE TABLE IF NOT EXISTS learning_analytics (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_days INTEGER DEFAULT 30,

    -- Card statistics
    total_cards INTEGER DEFAULT 0,
    new_cards INTEGER DEFAULT 0,
    learning_cards INTEGER DEFAULT 0,
    mature_cards INTEGER DEFAULT 0,
    relearning_cards INTEGER DEFAULT 0,

    -- Performance metrics
    average_retention_rate REAL DEFAULT 0.0 CHECK (average_retention_rate >= 0.0 AND average_retention_rate <= 1.0),
    average_quality_rating REAL DEFAULT 0.0 CHECK (average_quality_rating >= 0.0 AND average_quality_rating <= 5.0),
    average_response_time INTEGER DEFAULT 0,
    study_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,

    -- Progress indicators
    cards_per_day REAL DEFAULT 0.0,
    study_time_per_day INTEGER DEFAULT 0,  -- minutes
    mastery_progress REAL DEFAULT 0.0 CHECK (mastery_progress >= -1.0 AND mastery_progress <= 1.0),

    -- Difficulty distribution
    easy_cards INTEGER DEFAULT 0,
    medium_cards INTEGER DEFAULT 0,
    hard_cards INTEGER DEFAULT 0,

    -- Forgetting curve data
    forgetting_curve_data TEXT,  -- JSON array of retention rates over time

    -- Recommendations
    recommended_study_time INTEGER DEFAULT 0,  -- minutes per day
    recommended_new_cards INTEGER DEFAULT 0,
    recommended_review_cards INTEGER DEFAULT 0,
    focus_concepts TEXT,  -- JSON array

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_srs_preferences (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,

    -- Study session preferences
    max_new_cards_per_day INTEGER DEFAULT 20,
    max_review_cards_per_day INTEGER DEFAULT 100,
    session_duration_minutes INTEGER DEFAULT 30,

    -- Algorithm preferences
    starting_ease_factor REAL DEFAULT 2.5 CHECK (starting_ease_factor >= 1.3 AND starting_ease_factor <= 3.0),
    ease_factor_bonus REAL DEFAULT 0.1 CHECK (ease_factor_bonus >= 0.05 AND ease_factor_bonus <= 0.3),
    interval_modifier REAL DEFAULT 1.0 CHECK (interval_modifier >= 0.8 AND interval_modifier <= 1.5),

    -- Display preferences
    show_hints BOOLEAN DEFAULT FALSE,
    show_context BOOLEAN DEFAULT TRUE,
    show_source_material BOOLEAN DEFAULT TRUE,

    -- Cognitive preferences
    cognitive_load_threshold REAL DEFAULT 3.0 CHECK (cognitive_load_threshold >= 1.0 AND cognitive_load_threshold <= 5.0),
    response_time_weight REAL DEFAULT 0.1 CHECK (response_time_weight >= 0.0 AND response_time_weight <= 0.5),

    -- Notification preferences
    review_reminder_enabled BOOLEAN DEFAULT TRUE,
    review_reminder_time TEXT DEFAULT '19:00',  -- HH:MM format
    streak_reminder_enabled BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Card scheduling queue table
CREATE TABLE IF NOT EXISTS scheduling_queue (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    card_id TEXT NOT NULL,
    scheduled_for TIMESTAMP NOT NULL,
    priority INTEGER DEFAULT 0 CHECK (priority >= -10 AND priority <= 10),
    queue_type TEXT DEFAULT 'review' CHECK (queue_type IN ('new', 'review', 'relearn', 'cram')),
    interval_at_schedule INTEGER,
    ease_factor_at_schedule REAL,
    mastery_level_at_schedule REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processing_result TEXT,  -- processed, skipped, postponed
    FOREIGN KEY (card_id) REFERENCES learning_cards (id) ON DELETE CASCADE
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    metric_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Daily metrics
    cards_studied INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    average_accuracy REAL DEFAULT 0.0,
    average_response_time INTEGER DEFAULT 0,

    -- Retention metrics
    same_day_retention REAL DEFAULT 0.0,
    one_day_retention REAL DEFAULT 0.0,
    three_day_retention REAL DEFAULT 0.0,
    seven_day_retention REAL DEFAULT 0.0,

    -- Difficulty progression
    easy_card_accuracy REAL DEFAULT 0.0,
    medium_card_accuracy REAL DEFAULT 0.0,
    hard_card_accuracy REAL DEFAULT 0.0,

    -- Learning velocity
    new_cards_learned INTEGER DEFAULT 0,
    cards_graduated INTEGER DEFAULT 0,
    cards_forgotten INTEGER DEFAULT 0,

    -- Study patterns
    study_sessions_count INTEGER DEFAULT 0,
    average_session_length INTEGER DEFAULT 0,
    best_session_accuracy REAL DEFAULT 0.0,

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Adaptive learning insights table
CREATE TABLE IF NOT EXISTS learning_insights (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    insight_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    insight_type TEXT NOT NULL,  -- difficulty_pattern, forgetting_pattern, optimal_time, etc.
    confidence_score REAL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    description TEXT NOT NULL,
    actionable_recommendation TEXT,
    impact_assessment TEXT,  -- high, medium, low
    implementation_ease TEXT,  -- easy, moderate, challenging
    expected_improvement REAL CHECK (expected_improvement >= 0.0 AND expected_improvement <= 1.0),

    -- Related data
    related_cards TEXT,  -- JSON array of card IDs
    related_concepts TEXT,  -- JSON array of concept IDs
    time_horizon_days INTEGER DEFAULT 30,

    -- Status tracking
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'acknowledged', 'implemented', 'dismissed')),
    acknowledged_at TIMESTAMP,
    implemented_at TIMESTAMP,

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Error patterns table
CREATE TABLE IF NOT EXISTS error_patterns (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    card_id TEXT NOT NULL,
    error_type TEXT NOT NULL,  -- misconception, vocabulary, concept_confusion, etc.
    pattern_description TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    first_occurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_occurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_level REAL DEFAULT 0.5 CHECK (confidence_level >= 0.0 AND confidence_level <= 1.0),
    related_errors TEXT,  -- JSON array of related error IDs
    suggested_remediation TEXT,
    remediation_effectiveness REAL CHECK (remediation_effectiveness >= 0.0 AND remediation_effectiveness <= 1.0),
    FOREIGN KEY (card_id) REFERENCES learning_cards (id) ON DELETE CASCADE
);

-- Study goals table
CREATE TABLE IF NOT EXISTS study_goals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    goal_type TEXT NOT NULL,  -- cards_per_day, retention_rate, mastery_level, streak_days
    target_value REAL NOT NULL,
    current_value REAL DEFAULT 0.0,
    time_frame_days INTEGER NOT NULL,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_date TIMESTAMP NOT NULL,

    -- Goal metadata
    difficulty_level TEXT DEFAULT 'moderate' CHECK (difficulty_level IN ('easy', 'moderate', 'challenging')),
    priority_level INTEGER DEFAULT 2 CHECK (priority_level >= 1 AND priority_level <= 5),

    -- Status tracking
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'abandoned')),
    completion_percentage REAL DEFAULT 0.0 CHECK (completion_percentage >= 0.0 AND completion_percentage <= 100.0),

    -- Progress data
    milestones_achieved INTEGER DEFAULT 0,
    total_milestones INTEGER DEFAULT 0,
    last_milestone_date TIMESTAMP,

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Goal progress tracking table
CREATE TABLE IF NOT EXISTS goal_progress (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL,
    progress_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_value REAL NOT NULL,
    progress_delta REAL DEFAULT 0.0,
    milestone_achieved BOOLEAN DEFAULT FALSE,
    notes TEXT,
    automated_check BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (goal_id) REFERENCES study_goals (id) ON DELETE CASCADE
);

-- Study reminders table
CREATE TABLE IF NOT EXISTS study_reminders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    reminder_type TEXT NOT NULL,  -- due_cards, daily_goal, streak, review_needed
    trigger_time TIMESTAMP NOT NULL,
    message TEXT NOT NULL,
    priority INTEGER DEFAULT 2 CHECK (priority_level >= 1 AND priority_level <= 5),

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'acknowledged', 'cancelled')),
    sent_at TIMESTAMP,
    acknowledged_at TIMESTAMP,

    -- Effectiveness tracking
    action_taken BOOLEAN DEFAULT FALSE,
    action_details TEXT,
    effectiveness_rating INTEGER CHECK (effectiveness_rating >= 1 AND effectiveness_rating <= 5),

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Export data table
CREATE TABLE IF NOT EXISTS export_data (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    export_type TEXT NOT NULL,  -- cards, analytics, progress, full_export
    format TEXT NOT NULL,  -- json, csv, anki, xlsx
    data_content TEXT NOT NULL,  -- JSON or base64 encoded content
    file_size INTEGER DEFAULT 0,
    export_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    download_count INTEGER DEFAULT 0,
    last_downloaded TIMESTAMP,
    export_parameters TEXT,  -- JSON export parameters
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_learning_cards_user_id ON learning_cards(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_cards_course_id ON learning_cards(course_id);
CREATE INDEX IF NOT EXISTS idx_learning_cards_next_review ON learning_cards(next_review);
CREATE INDEX IF NOT EXISTS idx_learning_cards_card_type ON learning_cards(card_type);
CREATE INDEX IF NOT EXISTS idx_learning_cards_difficulty ON learning_cards(difficulty);
CREATE INDEX IF NOT EXISTS idx_learning_cards_mastery_level ON learning_cards(mastery_level);
CREATE INDEX IF NOT EXISTS idx_learning_cards_created_at ON learning_cards(created_at);
CREATE INDEX IF NOT EXISTS idx_learning_cards_last_reviewed ON learning_cards(last_reviewed);

CREATE INDEX IF NOT EXISTS idx_study_sessions_user_id ON study_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_study_sessions_course_id ON study_sessions(course_id);
CREATE INDEX IF NOT EXISTS idx_study_sessions_started_at ON study_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_study_sessions_session_type ON study_sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_study_sessions_rating ON study_sessions(session_rating);

CREATE INDEX IF NOT EXISTS idx_review_sessions_user_id ON review_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_review_sessions_session_id ON review_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_review_sessions_card_id ON review_sessions(card_id);
CREATE INDEX IF NOT EXISTS idx_review_sessions_quality_rating ON review_sessions(quality_rating);
CREATE INDEX IF NOT EXISTS idx_review_sessions_reviewed_at ON review_sessions(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_review_sessions_response_time ON review_sessions(response_time_ms);

CREATE INDEX IF NOT EXISTS idx_card_collections_user_id ON card_collections(user_id);
CREATE INDEX IF NOT EXISTS idx_card_collections_course_id ON card_collections(course_id);
CREATE INDEX IF NOT EXISTS idx_card_collections_collection_type ON card_collections(collection_type);
CREATE INDEX IF NOT EXISTS idx_card_collections_priority_level ON card_collections(priority_level);
CREATE INDEX IF NOT EXISTS idx_card_collections_last_studied ON card_collections(last_studied);

CREATE INDEX IF NOT EXISTS idx_analytics_user_course ON learning_analytics(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON learning_analytics(analysis_date);
CREATE INDEX IF NOT EXISTS idx_analytics_period ON learning_analytics(period_days);

CREATE INDEX IF NOT EXISTS idx_scheduling_queue_user_id ON scheduling_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduling_queue_scheduled_for ON scheduling_queue(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_scheduling_queue_priority ON scheduling_queue(priority);
CREATE INDEX IF NOT EXISTS idx_scheduling_queue_queue_type ON scheduling_queue(queue_type);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_user_course ON performance_metrics(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(metric_date);

CREATE INDEX IF NOT EXISTS idx_insights_user_course ON learning_insights(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_insights_type ON learning_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_confidence ON learning_insights(confidence_score);
CREATE INDEX IF NOT EXISTS idx_insights_status ON learning_insights(status);

CREATE INDEX IF NOT EXISTS idx_error_patterns_card_id ON error_patterns(card_id);
CREATE INDEX IF NOT EXISTS idx_error_patterns_frequency ON error_patterns(frequency);
CREATE INDEX IF NOT EXISTS idx_error_patterns_last_occurrence ON error_patterns(last_occurrence);

CREATE INDEX IF NOT EXISTS idx_study_goals_user_course ON study_goals(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_study_goals_status ON study_goals(status);
CREATE INDEX IF NOT EXISTS idx_study_goals_target_date ON study_goals(target_date);
CREATE INDEX IF NOT EXISTS idx_study_goals_goal_type ON study_goals(goal_type);

CREATE INDEX IF NOT EXISTS idx_goal_progress_goal_id ON goal_progress(goal_id);
CREATE INDEX IF NOT EXISTS idx_goal_progress_date ON goal_progress(progress_date);

CREATE INDEX IF NOT EXISTS idx_study_reminders_user_id ON study_reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_study_reminders_trigger_time ON study_reminders(trigger_time);
CREATE INDEX IF NOT EXISTS idx_study_reminders_status ON study_reminders(status);

CREATE INDEX IF NOT EXISTS idx_export_data_user_id ON export_data(user_id);
CREATE INDEX IF NOT EXISTS idx_export_data_export_date ON export_data(export_date);
CREATE INDEX IF NOT EXISTS idx_export_data_expires_at ON export_data(expires_at);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_learning_cards_last_reviewed
    AFTER UPDATE ON learning_cards
    FOR EACH ROW
WHEN NEW.last_reviewed != OLD.last_reviewed
BEGIN
    UPDATE learning_cards SET last_reviewed = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_card_collections_updated_at
    AFTER UPDATE ON card_collections
    FOR EACH ROW
BEGIN
    UPDATE card_collections SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_srs_preferences_updated_at
    AFTER UPDATE ON user_srs_preferences
    FOR EACH ROW
BEGIN
    UPDATE user_srs_preferences SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Views for common queries
CREATE VIEW IF NOT EXISTS user_card_stats AS
SELECT
    user_id,
    course_id,
    COUNT(*) as total_cards,
    COUNT(CASE WHEN repetitions = 0 THEN 1 END) as new_cards,
    COUNT(CASE WHEN repetitions > 0 AND repetitions < 3 THEN 1 END) as learning_cards,
    COUNT(CASE WHEN repetitions >= 3 THEN 1 END) as mature_cards,
    AVG(mastery_level) as average_mastery,
    AVG(ease_factor) as average_ease_factor,
    AVG(total_quality / GREATEST(review_count, 1)) as average_quality
FROM learning_cards
GROUP BY user_id, course_id;

CREATE VIEW IF NOT EXISTS due_cards AS
SELECT
    lc.*,
    CASE
        WHEN lc.next_review <= datetime('now') THEN 'overdue'
        WHEN lc.next_review <= datetime('now', '+1 day') THEN 'due_today'
        WHEN lc.next_review <= datetime('now', '+3 days') THEN 'due_soon'
        ELSE 'future'
    END as urgency_status
FROM learning_cards lc
WHERE lc.next_review <= datetime('now', '+7 days')
ORDER BY lc.next_review ASC;

CREATE VIEW IF NOT EXISTS study_streaks AS
SELECT
    user_id,
    course_id,
    DATE(started_at) as study_date,
    COUNT(*) as sessions_count,
    SUM(cards_studied) as total_cards_studied,
    SUM(total_time_seconds) as total_time_seconds,
    AVG(session_rating) as average_rating
FROM study_sessions
WHERE completed_at IS NOT NULL
GROUP BY user_id, course_id, DATE(started_at)
ORDER BY study_date DESC;