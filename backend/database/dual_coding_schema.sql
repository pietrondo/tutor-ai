-- Dual Coding Database Schema
-- Stores visual-verbal integrated learning content and user interactions

-- Main dual coding content table
CREATE TABLE IF NOT EXISTS dc_content (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    session_id TEXT,
    original_content TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN ('text', 'lecture', 'book_chapter', 'article', 'video_transcript', 'conversation', 'course_material')),
    target_audience TEXT NOT NULL DEFAULT 'intermediate',
    learning_style TEXT NOT NULL DEFAULT 'balanced' CHECK (learning_style IN ('visual', 'verbal', 'balanced', 'kinesthetic')),
    concepts TEXT NOT NULL,  -- JSON array of concepts and relationships
    visual_elements TEXT NOT NULL,  -- JSON array of visual elements
    verbal_content TEXT NOT NULL,  -- JSON verbal content
    interactions TEXT,  -- JSON learning interactions
    cognitive_load_score REAL DEFAULT 0.0 CHECK (cognitive_load_score >= 0.0 AND cognitive_load_score <= 1.0),
    dual_coding_score REAL DEFAULT 0.0 CHECK (dual_coding_score >= 0.0 AND dual_coding_score <= 1.0),
    visual_verbal_ratio REAL DEFAULT 0.4 CHECK (visual_verbal_ratio >= 0.0 AND visual_verbal_ratio <= 1.0),
    complexity_level TEXT DEFAULT 'medium' CHECK (complexity_level IN ('low', 'medium', 'high')),
    metadata TEXT,  -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Visual elements tracking table
CREATE TABLE IF NOT EXISTS dc_visual_elements (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL,
    element_type TEXT NOT NULL CHECK (element_type IN ('mind_map', 'flowchart', 'table', 'timeline', 'hierarchy', 'comparison', 'diagram', 'process_diagram', 'infographic', 'concept_map')),
    element_data TEXT NOT NULL,  -- JSON specific element data
    style_config TEXT,  -- JSON styling configuration
    cognitive_impact REAL DEFAULT 0.5 CHECK (cognitive_impact >= 0.0 AND cognitive_impact <= 1.0),
    complexity TEXT DEFAULT 'medium' CHECK (complexity IN ('low', 'medium', 'high')),
    file_path TEXT,  -- Path to generated image file if applicable
    rendering_metadata TEXT,  -- JSON rendering information
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES dc_content (id) ON DELETE CASCADE
);

-- User interactions with dual coding content
CREATE TABLE IF NOT EXISTS dc_user_interactions (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL,
    user_id TEXT,
    session_id TEXT,
    interaction_type TEXT NOT NULL,  -- view, explore, interact, complete
    interaction_data TEXT,  -- JSON interaction-specific data
    time_spent_seconds INTEGER DEFAULT 0,
    element_focused TEXT,  -- Which visual element was interacted with
    interaction_sequence INTEGER,  -- Order of interaction in session
    performance_metrics TEXT,  -- JSON performance data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES dc_content (id) ON DELETE CASCADE
);

-- Learning paths with dual coding integration
CREATE TABLE IF NOT EXISTS dc_learning_paths (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    user_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    learning_objectives TEXT,  -- JSON array of objectives
    nodes TEXT NOT NULL,  -- JSON array of learning path nodes
    total_estimated_time INTEGER,
    dual_coding_integration_score REAL DEFAULT 0.0,
    personalization_factors TEXT,  -- JSON personalization data
    current_position INTEGER DEFAULT 0,
    completion_status TEXT DEFAULT 'not_started' CHECK (completion_status IN ('not_started', 'in_progress', 'completed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Personalization profiles for dual coding
CREATE TABLE IF NOT EXISTS dc_personalization_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    preferred_visual_types TEXT,  -- JSON array of preferred visual element types
    optimal_cognitive_load REAL DEFAULT 0.6 CHECK (optimal_cognitive_load >= 0.0 AND optimal_cognitive_load <= 1.0),
    visual_verbal_preference REAL DEFAULT 0.5 CHECK (visual_verbal_preference >= 0.0 AND visual_verbal_preference <= 1.0),
    learning_style_confidence TEXT,  -- JSON confidence scores for different learning styles
    performance_history TEXT,  -- JSON array of performance data
    adaptation_history TEXT,  -- JSON array of adaptations made
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adaptive adjustments tracking
CREATE TABLE IF NOT EXISTS dc_adaptive_adjustments (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content_id TEXT,
    adjustment_type TEXT NOT NULL,  -- complexity, visual_verbal_ratio, interaction_type
    old_value TEXT,
    new_value TEXT,
    reason TEXT NOT NULL,
    confidence REAL DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    effectiveness_score REAL CHECK (effectiveness_score >= 0.0 AND effectiveness_score <= 1.0),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES dc_content (id) ON DELETE CASCADE
);

-- Assessment and feedback
CREATE TABLE IF NOT EXISTS dc_assessments (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL,
    user_id TEXT,
    assessment_type TEXT NOT NULL,  -- visual_comprehension, verbal_understanding, integration
    assessment_data TEXT NOT NULL,  -- JSON assessment questions/tasks
    user_responses TEXT,  -- JSON user responses
    scores TEXT,  -- JSON scoring breakdown
    completion_time_seconds INTEGER,
    self_assessment_rating INTEGER CHECK (self_assessment_rating >= 1 AND self_assessment_rating <= 5),
    feedback TEXT,  -- JSON qualitative feedback
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES dc_content (id) ON DELETE CASCADE
);

-- User feedback on dual coding content
CREATE TABLE IF NOT EXISTS dc_user_feedback (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL,
    user_id TEXT,
    visual_effectiveness_rating INTEGER CHECK (visual_effectiveness_rating >= 1 AND visual_effectiveness_rating <= 5),
    verbal_clarity_rating INTEGER CHECK (verbal_clarity_rating >= 1 AND verbal_clarity_rating <= 5),
    integration_quality_rating INTEGER CHECK (integration_quality_rating >= 1 AND integration_quality_rating <= 5),
    cognitive_load_rating INTEGER CHECK (cognitive_load_rating >= 1 AND cognitive_load_rating <= 5),
    overall_satisfaction INTEGER CHECK (overall_satisfaction >= 1 AND overall_satisfaction <= 5),
    qualitative_feedback TEXT,
    suggested_improvements TEXT,  -- JSON array of suggestions
    would_recommend BOOLEAN DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES dc_content (id) ON DELETE CASCADE
);

-- Performance tracking and progress
CREATE TABLE IF NOT EXISTS dc_performance_tracking (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    session_count INTEGER DEFAULT 0,
    total_time_spent INTEGER DEFAULT 0,  -- minutes
    average_session_length REAL DEFAULT 0.0,
    performance_improvement REAL DEFAULT 0.0,
    mastery_areas TEXT,  -- JSON array of mastered concepts
    improvement_areas TEXT,  -- JSON array of areas needing work
    next_recommended_focus TEXT,
    visual_processing_speed REAL,  -- elements per minute
    verbal_comprehension_rate REAL,  -- words per minute
    integration_ability REAL CHECK (integration_ability >= 0.0 AND integration_ability <= 1.0),
    retention_score REAL CHECK (retention_score >= 0.0 AND retention_score <= 1.0),
    transfer_ability REAL CHECK (transfer_ability >= 0.0 AND transfer_ability <= 1.0),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tracking_period_start TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    UNIQUE(user_id, course_id)
);

-- Analytics aggregation table
CREATE TABLE IF NOT EXISTS dc_analytics (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    user_id TEXT,
    period_days INTEGER NOT NULL,
    dual_coding_sessions INTEGER DEFAULT 0,
    visual_elements_created INTEGER DEFAULT 0,
    preferred_visual_types TEXT,  -- JSON count by type
    learning_outcomes TEXT,  -- JSON outcome metrics
    cognitive_load_metrics TEXT,  -- JSON load metrics
    integration_quality TEXT,  -- JSON quality metrics
    engagement_metrics TEXT,  -- JSON engagement data
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Content generation cache
CREATE TABLE IF NOT EXISTS dc_generation_cache (
    id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    course_id TEXT NOT NULL,
    generation_params TEXT NOT NULL,  -- JSON parameters used
    cached_content TEXT NOT NULL,  -- JSON cached dual coding content
    concepts_extracted TEXT,  -- JSON extracted concepts
    hit_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Content enhancement requests
CREATE TABLE IF NOT EXISTS dc_content_enhancements (
    id TEXT PRIMARY KEY,
    original_content_id TEXT NOT NULL,
    user_id TEXT,
    enhancement_type TEXT NOT NULL,  -- visual_elements, verbal_explanations, interactions
    enhancement_request TEXT NOT NULL,  -- JSON request details
    enhanced_content TEXT,  -- JSON enhanced content
    improvement_metrics TEXT,  -- JSON improvement measurements
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (original_content_id) REFERENCES dc_content (id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_dc_content_course_id ON dc_content(course_id);
CREATE INDEX IF NOT EXISTS idx_dc_content_session_id ON dc_content(session_id);
CREATE INDEX IF NOT EXISTS idx_dc_content_learning_style ON dc_content(learning_style);
CREATE INDEX IF NOT EXISTS idx_dc_content_complexity ON dc_content(complexity_level);
CREATE INDEX IF NOT EXISTS idx_dc_content_created_at ON dc_content(created_at);
CREATE INDEX IF NOT EXISTS idx_dc_content_dual_coding_score ON dc_content(dual_coding_score);

CREATE INDEX IF NOT EXISTS idx_dc_visual_elements_content_id ON dc_visual_elements(content_id);
CREATE INDEX IF NOT EXISTS idx_dc_visual_elements_type ON dc_visual_elements(element_type);
CREATE INDEX IF NOT EXISTS idx_dc_visual_elements_complexity ON dc_visual_elements(complexity);
CREATE INDEX IF NOT EXISTS idx_dc_visual_elements_impact ON dc_visual_elements(cognitive_impact);

CREATE INDEX IF NOT EXISTS idx_dc_user_interactions_content_id ON dc_user_interactions(content_id);
CREATE INDEX IF NOT EXISTS idx_dc_user_interactions_user_id ON dc_user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_dc_user_interactions_session_id ON dc_user_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_dc_user_interactions_type ON dc_user_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_dc_user_interactions_created_at ON dc_user_interactions(created_at);

CREATE INDEX IF NOT EXISTS idx_dc_learning_paths_course_id ON dc_learning_paths(course_id);
CREATE INDEX IF NOT EXISTS idx_dc_learning_paths_user_id ON dc_learning_paths(user_id);
CREATE INDEX IF NOT EXISTS idx_dc_learning_paths_status ON dc_learning_paths(completion_status);

CREATE INDEX IF NOT EXISTS idx_dc_personalization_user_id ON dc_personalization_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_dc_personalization_updated ON dc_personalization_profiles(last_updated);

CREATE INDEX IF NOT EXISTS idx_dc_adaptive_adjustments_user_id ON dc_adaptive_adjustments(user_id);
CREATE INDEX IF NOT EXISTS idx_dc_adaptive_adjustments_content_id ON dc_adaptive_adjustments(content_id);
CREATE INDEX IF NOT EXISTS idx_dc_adaptive_adjustments_type ON dc_adaptive_adjustments(adjustment_type);
CREATE INDEX IF NOT EXISTS idx_dc_adaptive_adjustments_applied_at ON dc_adaptive_adjustments(applied_at);

CREATE INDEX IF NOT EXISTS idx_dc_assessments_content_id ON dc_assessments(content_id);
CREATE INDEX IF NOT EXISTS idx_dc_assessments_user_id ON dc_assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_dc_assessments_type ON dc_assessments(assessment_type);
CREATE INDEX IF NOT EXISTS idx_dc_assessments_completed_at ON dc_assessments(completed_at);

CREATE INDEX IF NOT EXISTS idx_dc_feedback_content_id ON dc_user_feedback(content_id);
CREATE INDEX IF NOT EXISTS idx_dc_feedback_user_id ON dc_user_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_dc_feedback_overall_satisfaction ON dc_user_feedback(overall_satisfaction);

CREATE INDEX IF NOT EXISTS idx_dc_performance_user_course ON dc_performance_tracking(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_dc_performance_last_updated ON dc_performance_tracking(last_updated);

CREATE INDEX IF NOT EXISTS idx_dc_analytics_course_user ON dc_analytics(course_id, user_id);
CREATE INDEX IF NOT EXISTS idx_dc_analytics_period ON dc_analytics(period_days);
CREATE INDEX IF NOT EXISTS idx_dc_analytics_valid_until ON dc_analytics(valid_until);

CREATE INDEX IF NOT EXISTS idx_dc_cache_content_hash ON dc_generation_cache(content_hash);
CREATE INDEX IF NOT EXISTS idx_dc_cache_course_id ON dc_generation_cache(course_id);
CREATE INDEX IF NOT EXISTS idx_dc_cache_expires_at ON dc_generation_cache(expires_at);

CREATE INDEX IF NOT EXISTS idx_dc_enhancements_original_content_id ON dc_content_enhancements(original_content_id);
CREATE INDEX IF NOT EXISTS idx_dc_enhancements_user_id ON dc_content_enhancements(user_id);
CREATE INDEX IF NOT EXISTS idx_dc_enhancements_status ON dc_content_enhancements(status);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_dc_content_timestamp
    AFTER UPDATE ON dc_content
    FOR EACH ROW
BEGIN
    UPDATE dc_content SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_dc_learning_paths_timestamp
    AFTER UPDATE ON dc_learning_paths
    FOR EACH ROW
BEGIN
    UPDATE dc_learning_paths SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_dc_personalization_timestamp
    AFTER UPDATE ON dc_personalization_profiles
    FOR EACH ROW
BEGIN
    UPDATE dc_personalization_profiles SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_dc_performance_timestamp
    AFTER UPDATE ON dc_performance_tracking
    FOR EACH ROW
BEGIN
    UPDATE dc_performance_tracking SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;