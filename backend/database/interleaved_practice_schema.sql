-- Interleaved Practice Database Schema
-- Stores interleaved practice schedules, sessions, and analytics

-- Interleaved practice schedules table
CREATE TABLE IF NOT EXISTS ip_schedules (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    concept_analysis TEXT NOT NULL,  -- JSON analysis of concepts and relationships
    interleaving_strategy TEXT NOT NULL,  -- JSON strategy configuration
    practice_sequence TEXT NOT NULL,  -- JSON practice segments
    reflection_points TEXT,  -- JSON reflection points
    effectiveness_metrics TEXT NOT NULL,  -- JSON predicted effectiveness
    metadata TEXT,  -- JSON additional metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Practice sessions tracking table
CREATE TABLE IF NOT EXISTS ip_sessions (
    id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    current_segment INTEGER DEFAULT 0,
    total_time_spent INTEGER DEFAULT 0,  -- minutes
    segments_completed TEXT,  -- JSON array of completed segment IDs
    performance_data TEXT,  -- JSON performance metrics
    user_feedback TEXT,  -- JSON user feedback data
    adaptation_history TEXT,  -- JSON adaptations made during session
    status TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'paused', 'cancelled')),
    completion_percentage REAL DEFAULT 0.0 CHECK (completion_percentage >= 0.0 AND completion_percentage <= 1.0),
    FOREIGN KEY (schedule_id) REFERENCES ip_schedules (id) ON DELETE CASCADE
);

-- Practice segments table
CREATE TABLE IF NOT EXISTS ip_practice_segments (
    id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    session_id TEXT,
    segment_index INTEGER NOT NULL,
    concept_id TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    practice_type TEXT NOT NULL CHECK (practice_type IN ('active_practice', 'mixed_practice', 'discrimination_practice', 'adaptive_practice', 'reflection', 'transition')),
    start_time INTEGER,  -- minutes from session start
    end_time INTEGER,  -- minutes from session start
    transition_to_next TEXT,
    micro_objectives TEXT,  -- JSON array of objectives
    success_criteria TEXT,  -- JSON array of success criteria
    actual_time_spent INTEGER,
    completion_status TEXT DEFAULT 'pending' CHECK (completion_status IN ('pending', 'in_progress', 'completed', 'skipped')),
    performance_score REAL CHECK (performance_score >= 0.0 AND performance_score <= 1.0),
    FOREIGN KEY (schedule_id) REFERENCES ip_schedules (id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES ip_sessions (id) ON DELETE CASCADE
);

-- Concept similarity analysis table
CREATE TABLE IF NOT EXISTS ip_concept_similarities (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    concept1_id TEXT NOT NULL,
    concept2_id TEXT NOT NULL,
    similarity_score REAL CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0),
    relationship_type TEXT,
    confidence REAL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    interleaving_suitability REAL CHECK (interleaving_suitability >= 0.0 AND interleaving_suitability <= 1.0),
    interleaving_type TEXT CHECK (interleaving_type IN ('contrasting', 'integrative', 'sequential', 'adaptive')),
    recommended_spacing INTEGER,  -- minutes between concepts
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    UNIQUE(course_id, concept1_id, concept2_id)
);

-- Interleaving pairs table
CREATE TABLE IF NOT EXISTS ip_interleaving_pairs (
    id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    concept1_id TEXT NOT NULL,
    concept2_id TEXT NOT NULL,
    similarity REAL NOT NULL CHECK (similarity >= 0.0 AND similarity <= 1.0),
    suitability REAL NOT NULL CHECK (suitability >= 0.0 AND suitability <= 1.0),
    interleaving_type TEXT NOT NULL,
    recommended_spacing INTEGER NOT NULL,
    effectiveness_observed REAL CHECK (effectiveness_observed >= 0.0 AND effectiveness_observed <= 1.0),
    usage_count INTEGER DEFAULT 0,
    FOREIGN KEY (schedule_id) REFERENCES ip_schedules (id) ON DELETE CASCADE
);

-- User preferences for interleaved practice
CREATE TABLE IF NOT EXISTS ip_user_preferences (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    preferred_patterns TEXT,  -- JSON array of PracticePattern
    interleaving_intensity_preference REAL DEFAULT 0.7 CHECK (interleaving_intensity_preference >= 0.1 AND interleaving_intensity_preference <= 1.0),
    transition_preference TEXT DEFAULT 'quick_review',
    reflection_preference TEXT DEFAULT 'guided',
    difficulty_preference TEXT DEFAULT 'adaptive' CHECK (difficulty_preference IN ('easy', 'medium', 'hard', 'adaptive')),
    session_duration_preference INTEGER DEFAULT 60,
    adaptation_sensitivity REAL DEFAULT 0.5 CHECK (adaptation_sensitivity >= 0.0 AND adaptation_sensitivity <= 1.0),
    max_concepts_per_session INTEGER DEFAULT 4,
    min_spacing_minutes INTEGER DEFAULT 3,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics tracking
CREATE TABLE IF NOT EXISTS ip_performance_metrics (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    session_id TEXT,
    concept_id TEXT,
    metric_type TEXT NOT NULL,  -- discrimination, transfer, retention, problem_solving
    metric_value REAL NOT NULL,
    measurement_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context_data TEXT,  -- JSON additional context
    improvement_trend REAL CHECK (improvement_trend >= -1.0 AND improvement_trend <= 1.0),
    confidence_level REAL CHECK (confidence_level >= 0.0 AND confidence_level <= 1.0),
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES ip_sessions (id) ON DELETE CASCADE
);

-- Pattern effectiveness analytics
CREATE TABLE IF NOT EXISTS ip_pattern_effectiveness (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    pattern TEXT NOT NULL,  -- ABAB, ABCABC, ABCDABCD, mixed, adaptive
    usage_count INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    average_performance REAL DEFAULT 0.0,
    concept_discrimination_score REAL DEFAULT 0.0,
    user_satisfaction REAL DEFAULT 0.0,
    cognitive_load_average REAL DEFAULT 0.0,
    engagement_average REAL DEFAULT 0.0,
    retention_confidence_average REAL DEFAULT 0.0,
    effectiveness_score REAL DEFAULT 0.0,
    recommended_for TEXT,  -- JSON array of recommended scenarios
    best_practice_indicators TEXT,  -- JSON best practice indicators
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, pattern)
);

-- Concept progress tracking
CREATE TABLE IF NOT EXISTS ip_concept_progress (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    mastery_level REAL DEFAULT 0.0 CHECK (mastery_level >= 0.0 AND mastery_level <= 1.0),
    discrimination_score REAL DEFAULT 0.0 CHECK (discrimination_score >= 0.0 AND discrimination_score <= 1.0),
    transfer_score REAL DEFAULT 0.0 CHECK (transfer_score >= 0.0 AND transfer_score <= 1.0),
    retention_score REAL DEFAULT 0.0 CHECK (retention_score >= 0.0 AND retention_score <= 1.0),
    practice_frequency REAL DEFAULT 0.0,  -- sessions per week
    last_practiced TIMESTAMP,
    mastery_progress REAL DEFAULT 0.0 CHECK (mastery_progress >= -1.0 AND mastery_progress <= 1.0),
    discrimination_improvement REAL DEFAULT 0.0 CHECK (discrimination_improvement >= -1.0 AND discrimination_improvement <= 1.0),
    transfer_improvement REAL DEFAULT 0.0 CHECK (transfer_improvement >= -1.0 AND transfer_improvement <= 1.0),
    improvement_trend TEXT DEFAULT 'stable' CHECK (improvement_trend IN ('improving', 'stable', 'declining')),
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    UNIQUE(user_id, course_id, concept_id)
);

-- Adaptive adjustments tracking
CREATE TABLE IF NOT EXISTS ip_adaptive_adjustments (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT,
    schedule_id TEXT,
    adjustment_type TEXT NOT NULL,
    original_value TEXT,
    new_value TEXT,
    reason TEXT NOT NULL,
    confidence REAL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    expected_impact REAL CHECK (expected_impact >= -1.0 AND expected_impact <= 1.0),
    actual_impact REAL CHECK (actual_impact >= -1.0 AND actual_impact <= 1.0),
    triggered_by TEXT,  -- user_feedback, performance_drop, time_constraint, etc.
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    effectiveness_observed REAL CHECK (effectiveness_observed >= 0.0 AND effectiveness_observed <= 1.0),
    FOREIGN KEY (session_id) REFERENCES ip_sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES ip_schedules (id) ON DELETE CASCADE
);

-- Session feedback collection
CREATE TABLE IF NOT EXISTS ip_session_feedback (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    pattern_effectiveness INTEGER CHECK (pattern_effectiveness >= 1 AND pattern_effectiveness <= 5),
    cognitive_load_rating INTEGER CHECK (cognitive_load_rating >= 1 AND cognitive_load_rating <= 5),
    concept_clarity INTEGER CHECK (concept_clarity >= 1 AND concept_clarity <= 5),
    engagement_level INTEGER CHECK (engagement_level >= 1 AND engagement_level <= 5),
    transfer_confidence INTEGER CHECK (transfer_confidence >= 1 AND transfer_confidence <= 5),
    qualitative_feedback TEXT,
    would_recommend_pattern BOOLEAN,
    suggestions_for_improvement TEXT,  -- JSON array of suggestions
    overall_satisfaction INTEGER CHECK (overall_satisfaction >= 1 AND overall_satisfaction <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES ip_sessions (id) ON DELETE CASCADE
);

-- Analytics aggregation table
CREATE TABLE IF NOT EXISTS ip_analytics (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    period_days INTEGER NOT NULL,
    interleaved_sessions INTEGER DEFAULT 0,
    total_concepts_practiced INTEGER DEFAULT 0,
    concept_discrimination_score REAL DEFAULT 0.0,
    transfer_improvement REAL DEFAULT 0.0,
    retention_rate REAL DEFAULT 0.0,
    practice_efficiency REAL DEFAULT 0.0,
    most_effective_patterns TEXT,  -- JSON array of patterns
    concept_progress_data TEXT,  -- JSON concept progress details
    pattern_effectiveness_data TEXT,  -- JSON pattern effectiveness details
    improvement_areas TEXT,  -- JSON array of improvement areas
    recommendations TEXT,  -- JSON array of recommendations
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Comparative analysis table
CREATE TABLE IF NOT EXISTS ip_comparative_analysis (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    baseline_performance TEXT NOT NULL,  -- JSON baseline metrics
    interleaved_performance TEXT NOT NULL,  -- JSON interleaved metrics
    blocked_performance TEXT,  -- JSON blocked practice metrics
    improvement_percentages TEXT,  -- JSON improvement percentages
    statistical_significance TEXT,  -- JSON significance data
    recommendations TEXT,  -- JSON analysis recommendations
    confidence_level REAL CHECK (confidence_level >= 0.0 AND confidence_level <= 1.0),
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Learning path integration table
CREATE TABLE IF NOT EXISTS ip_learning_paths (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    path_type TEXT NOT NULL,  -- interleaved, mixed, adaptive
    segments TEXT NOT NULL,  -- JSON path segments
    total_duration INTEGER NOT NULL,
    difficulty_progression TEXT,  -- JSON difficulty progression
    interleaving_progression TEXT,  -- JSON pattern progression
    estimated_completion TIMESTAMP,
    success_criteria TEXT,  -- JSON success criteria
    current_position INTEGER DEFAULT 0,
    completion_status TEXT DEFAULT 'not_started' CHECK (completion_status IN ('not_started', 'in_progress', 'completed', 'paused')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Schedule cache for performance optimization
CREATE TABLE IF NOT EXISTS ip_schedule_cache (
    id TEXT PRIMARY KEY,
    cache_key TEXT UNIQUE NOT NULL,
    user_id TEXT,
    course_id TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    cached_schedule TEXT NOT NULL,  -- JSON cached schedule data
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_ip_schedules_user_id ON ip_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_ip_schedules_course_id ON ip_schedules(course_id);
CREATE INDEX IF NOT EXISTS idx_ip_schedules_created_at ON ip_schedules(created_at);
CREATE INDEX IF NOT EXISTS idx_ip_schedules_updated_at ON ip_schedules(updated_at);

CREATE INDEX IF NOT EXISTS idx_ip_sessions_schedule_id ON ip_sessions(schedule_id);
CREATE INDEX IF NOT EXISTS idx_ip_sessions_user_id ON ip_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_ip_sessions_status ON ip_sessions(status);
CREATE INDEX IF NOT EXISTS idx_ip_sessions_started_at ON ip_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_ip_sessions_completion_percentage ON ip_sessions(completion_percentage);

CREATE INDEX IF NOT EXISTS idx_ip_segments_schedule_id ON ip_practice_segments(schedule_id);
CREATE INDEX IF NOT EXISTS idx_ip_segments_session_id ON ip_practice_segments(session_id);
CREATE INDEX IF NOT EXISTS idx_ip_segments_concept_id ON ip_practice_segments(concept_id);
CREATE INDEX IF NOT EXISTS idx_ip_segments_segment_index ON ip_practice_segments(segment_index);
CREATE INDEX IF NOT EXISTS idx_ip_segments_practice_type ON ip_practice_segments(practice_type);

CREATE INDEX IF NOT EXISTS idx_ip_similarities_course_id ON ip_concept_similarities(course_id);
CREATE INDEX IF NOT EXISTS idx_ip_similarities_concept1 ON ip_concept_similarities(concept1_id);
CREATE INDEX IF NOT EXISTS idx_ip_similarities_concept2 ON ip_concept_similarities(concept2_id);
CREATE INDEX IF NOT EXISTS idx_ip_similarities_similarity ON ip_concept_similarities(similarity_score);

CREATE INDEX IF NOT EXISTS idx_ip_pairs_schedule_id ON ip_interleaving_pairs(schedule_id);
CREATE INDEX IF NOT EXISTS idx_ip_pairs_suitability ON ip_interleaving_pairs(suitability);
CREATE INDEX IF NOT EXISTS idx_ip_pairs_usage_count ON ip_interleaving_pairs(usage_count);

CREATE INDEX IF NOT EXISTS idx_ip_preferences_user_id ON ip_user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_ip_preferences_last_updated ON ip_user_preferences(last_updated);

CREATE INDEX IF NOT EXISTS idx_ip_metrics_user_id ON ip_performance_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_ip_metrics_course_id ON ip_performance_metrics(course_id);
CREATE INDEX IF NOT EXISTS idx_ip_metrics_session_id ON ip_performance_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_ip_metrics_concept_id ON ip_performance_metrics(concept_id);
CREATE INDEX IF NOT EXISTS idx_ip_metrics_type ON ip_performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_ip_metrics_time ON ip_performance_metrics(measurement_time);

CREATE INDEX IF NOT EXISTS idx_ip_pattern_effectiveness_user_pattern ON ip_pattern_effectiveness(user_id, pattern);
CREATE INDEX IF NOT EXISTS idx_ip_pattern_effectiveness_score ON ip_pattern_effectiveness(effectiveness_score);
CREATE INDEX IF NOT EXISTS idx_ip_pattern_effectiveness_usage ON ip_pattern_effectiveness(usage_count);

CREATE INDEX IF NOT EXISTS idx_ip_progress_user_course ON ip_concept_progress(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_ip_progress_concept_id ON ip_concept_progress(concept_id);
CREATE INDEX IF NOT EXISTS idx_ip_progress_mastery ON ip_concept_progress(mastery_level);
CREATE INDEX IF NOT EXISTS idx_ip_progress_last_practiced ON ip_concept_progress(last_practiced);

CREATE INDEX IF NOT EXISTS idx_ip_adjustments_user_id ON ip_adaptive_adjustments(user_id);
CREATE INDEX IF NOT EXISTS idx_ip_adjustments_session_id ON ip_adaptive_adjustments(session_id);
CREATE INDEX IF NOT EXISTS idx_ip_adjustments_applied_at ON ip_adaptive_adjustments(applied_at);

CREATE INDEX IF NOT EXISTS idx_ip_feedback_session_id ON ip_session_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_ip_feedback_user_id ON ip_session_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_ip_feedback_effectiveness ON ip_session_feedback(pattern_effectiveness);

CREATE INDEX IF NOT EXISTS idx_ip_analytics_user_course ON ip_analytics(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_ip_analytics_period ON ip_analytics(period_days);
CREATE INDEX IF NOT EXISTS idx_ip_analytics_valid_until ON ip_analytics(valid_until);

CREATE INDEX IF NOT EXISTS idx_ip_comparative_user_course ON ip_comparative_analysis(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_ip_comparative_date ON ip_comparative_analysis(analysis_date);

CREATE INDEX IF NOT EXISTS idx_ip_learning_paths_user_course ON ip_learning_paths(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_ip_learning_paths_status ON ip_learning_paths(completion_status);

CREATE INDEX IF NOT EXISTS idx_ip_cache_key ON ip_schedule_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_ip_cache_expires_at ON ip_schedule_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_ip_cache_hit_count ON ip_schedule_cache(hit_count);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_ip_schedules_timestamp
    AFTER UPDATE ON ip_schedules
    FOR EACH ROW
BEGIN
    UPDATE ip_schedules SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_ip_user_preferences_timestamp
    AFTER UPDATE ON ip_user_preferences
    FOR EACH ROW
BEGIN
    UPDATE ip_user_preferences SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_ip_concept_similarities_timestamp
    AFTER UPDATE ON ip_concept_similarities
    FOR EACH ROW
BEGIN
    UPDATE ip_concept_similarities SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_ip_pattern_effectiveness_timestamp
    AFTER UPDATE ON ip_pattern_effectiveness
    FOR EACH ROW
BEGIN
    UPDATE ip_pattern_effectiveness SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_ip_learning_paths_timestamp
    AFTER UPDATE ON ip_learning_paths
    FOR EACH ROW
BEGIN
    UPDATE ip_learning_paths SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;