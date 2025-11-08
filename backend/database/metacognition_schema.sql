-- Metacognition Framework Database Schema
-- Stores metacognitive sessions, reflections, and self-regulation data

-- Metacognitive sessions table
CREATE TABLE IF NOT EXISTS metacognitive_sessions (
    id TEXT PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    session_type TEXT DEFAULT 'comprehensive' CHECK (session_type IN ('comprehensive', 'planning', 'monitoring', 'evaluation', 'regulation', 'reflection')),
    focus_areas TEXT,  -- JSON array of focus areas
    duration_minutes INTEGER DEFAULT 30,
    scaffolding_level TEXT DEFAULT 'moderate' CHECK (scaffolding_level IN ('minimal', 'light', 'moderate', 'heavy', 'extensive')),
    metacognitive_goals TEXT,  -- JSON array
    learning_context TEXT NOT NULL,  -- JSON learning context
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    completion_percentage REAL DEFAULT 0.0 CHECK (completion_percentage >= 0.0 AND completion_percentage <= 1.0),
    session_quality REAL CHECK (session_quality >= 0.0 AND session_quality <= 1.0),
    overall_effectiveness REAL CHECK (overall_effectiveness >= 0.0 AND overall_effectiveness <= 1.0),
    insights_generated INTEGER DEFAULT 0,
    adaptations_suggested INTEGER DEFAULT 0,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Metacognitive phases table
CREATE TABLE IF NOT EXISTS metacognitive_phases (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    phase_name TEXT NOT NULL CHECK (phase_name IN ('planning', 'monitoring', 'evaluation', 'regulation')),
    phase_order INTEGER NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER DEFAULT 0,
    activities_completed INTEGER DEFAULT 0,
    effectiveness_rating REAL CHECK (effectiveness_rating >= 0.0 AND effectiveness_rating <= 1.0),
    challenges_encountered TEXT,  -- JSON array
    insights_gained TEXT,  -- JSON array
    adaptation_made BOOLEAN DEFAULT FALSE,
    satisfaction_level INTEGER CHECK (satisfaction_level >= 1 AND satisfaction_level <= 5),
    FOREIGN KEY (session_id) REFERENCES metacognitive_sessions (id) ON DELETE CASCADE
);

-- Reflection activities table
CREATE TABLE IF NOT EXISTS reflection_activities (
    id TEXT PRIMARY KEY,
    activity_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    session_id TEXT,
    activity_type TEXT NOT NULL CHECK (activity_type IN ('strategic', 'performance', 'affective', 'metacognitive_awareness', 'goal_setting', 'process_evaluation')),
    reflection_context TEXT NOT NULL,  -- JSON context data
    learning_objectives TEXT,  -- JSON array
    duration_minutes INTEGER DEFAULT 15,
    difficulty_level TEXT DEFAULT 'moderate' CHECK (difficulty_level IN ('easy', 'moderate', 'hard', 'adaptive')),

    -- Content
    reflection_framework TEXT,
    guiding_questions TEXT NOT NULL,  -- JSON array
    reflection_prompts TEXT NOT NULL,  -- JSON array
    self_assessment_criteria TEXT,  -- JSON array

    -- Expected outcomes
    expected_insights TEXT,  -- JSON array
    follow_up_actions TEXT,  -- JSON array
    success_criteria TEXT,  -- JSON array

    -- Scaffolding
    scaffolding_provided TEXT,  -- JSON scaffolding data
    hint_level INTEGER DEFAULT 0 CHECK (hint_level >= 0 AND hint_level <= 5),

    -- Status
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    completion_status TEXT DEFAULT 'pending' CHECK (completion_status IN ('pending', 'in_progress', 'completed', 'skipped')),
    reflection_quality REAL CHECK (reflection_quality >= 0.0 AND reflection_quality <= 1.0),

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES metacognitive_sessions (id) ON DELETE CASCADE
);

-- Reflection responses table
CREATE TABLE IF NOT EXISTS reflection_responses (
    id TEXT PRIMARY KEY,
    activity_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    response_type TEXT DEFAULT 'text' CHECK (response_type IN ('text', 'rating', 'multiple_choice', 'boolean')),
    confidence_level INTEGER CHECK (confidence_level >= 1 AND confidence_level <= 5),
    emotional_state TEXT CHECK (emotional_state IN ('positive', 'neutral', 'negative', 'mixed', 'uncertain')),
    response_time_seconds INTEGER DEFAULT 0,
    hints_used INTEGER DEFAULT 0,
    flagged_for_review BOOLEAN DEFAULT FALSE,
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES reflection_activities (id) ON DELETE CASCADE
);

-- Self-regulation activities table
CREATE TABLE IF NOT EXISTS self_regulation_activities (
    id TEXT PRIMARY KEY,
    regulation_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    session_id TEXT,
    regulation_phase TEXT NOT NULL CHECK (regulation_phase IN ('planning', 'monitoring', 'evaluation', 'regulation')),
    regulation_context TEXT NOT NULL,  -- JSON context
    challenges_identified TEXT,  -- JSON array
    goals TEXT,  -- JSON array
    current_strategies TEXT,  -- JSON array

    -- Recommended strategies
    strategies_recommended TEXT NOT NULL,  -- JSON array of strategy objects
    action_steps TEXT NOT NULL,  -- JSON array
    monitoring_tools TEXT,  -- JSON array
    success_criteria TEXT NOT NULL,  -- JSON array

    -- Implementation details
    timeline_suggested TEXT,
    resources_needed TEXT,  -- JSON array
    progress_tracking TEXT,  -- JSON progress indicators
    adaptation_protocols TEXT,  -- JSON array

    -- Status tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    implementation_started_at TIMESTAMP,
    implementation_completed_at TIMESTAMP,
    implementation_status TEXT DEFAULT 'planned' CHECK (implementation_status IN ('planned', 'in_progress', 'completed', 'paused', 'cancelled')),
    effectiveness_rating REAL CHECK (effectiveness_rating >= 0.0 AND effectiveness_rating <= 1.0),
    actual_outcomes TEXT,  -- JSON array
    lessons_learned TEXT,  -- JSON array

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES metacognitive_sessions (id) ON DELETE CASCADE
);

-- Metacognitive analytics table
CREATE TABLE IF NOT EXISTS metacognitive_analytics (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_days INTEGER DEFAULT 30,
    analysis_type TEXT DEFAULT 'comprehensive' CHECK (analysis_type IN ('comprehensive', 'focused', 'comparative', 'predictive')),

    -- Metacognitive Awareness Metrics
    self_regulation_skills TEXT NOT NULL,  -- JSON object with skill ratings
    reflection_quality TEXT NOT NULL,  -- JSON object with quality metrics
    strategy_sophistication REAL DEFAULT 0.0 CHECK (strategy_sophistication >= 0.0 AND strategy_sophistication <= 1.0),
    learning_autonomy REAL DEFAULT 0.0 CHECK (learning_autonomy >= 0.0 AND learning_autonomy <= 1.0),
    metacognitive_awareness REAL DEFAULT 0.0 CHECK (metacognitive_awareness >= 0.0 AND metacognitive_awareness <= 1.0),

    -- Performance Correlations
    strategy_effectiveness TEXT,  -- JSON object with effectiveness data
    adaptation_frequency REAL DEFAULT 0.0,
    goal_achievement_rate REAL DEFAULT 0.0 CHECK (goal_achievement_rate >= 0.0 AND goal_achievement_rate <= 1.0),
    challenge_resolution_rate REAL DEFAULT 0.0 CHECK (challenge_resolution_rate >= 0.0 AND challenge_resolution_rate <= 1.0),

    -- Learning Patterns
    preferred_regulation_strategies TEXT,  -- JSON array
    reflection_frequency REAL DEFAULT 0.0,
    self_monitoring_consistency REAL DEFAULT 0.0 CHECK (self_monitoring_consistency >= 0.0 AND self_monitoring_consistency <= 1.0),
    planning_effectiveness REAL DEFAULT 0.0 CHECK (planning_effectiveness >= 0.0 AND planning_effectiveness <= 1.0),

    -- Development Trends
    awareness_progression TEXT,  -- JSON object with progression data
    strategy_evolution TEXT,  -- JSON array of evolved strategies
    metacognitive_growth REAL DEFAULT 0.0 CHECK (metacognitive_growth >= -1.0 AND metacognitive_growth <= 1.0),

    -- Recommendations
    development_priorities TEXT,  -- JSON array
    strategy_recommendations TEXT,  -- JSON array of recommendations
    practice_opportunities TEXT,  -- JSON array
    refinement_areas TEXT,  -- JSON array

    -- Predictions
    next_week_focus TEXT,  -- JSON array of predicted focus areas
    potential_challenges TEXT,  -- JSON array
    success_probability REAL CHECK (success_probability >= 0.0 AND success_probability <= 1.0),

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Learning strategies table
CREATE TABLE IF NOT EXISTS learning_strategies (
    id TEXT PRIMARY KEY,
    strategy_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    strategy_type TEXT NOT NULL CHECK (strategy_type IN ('cognitive', 'metacognitive', 'resource_management', 'motivational', 'environmental')),
    strategy_description TEXT NOT NULL,

    -- Strategy details
    implementation_steps TEXT NOT NULL,  -- JSON array
    expected_outcomes TEXT,  -- JSON array
    success_metrics TEXT,  -- JSON array
    timeline_estimate TEXT,
    resource_requirements TEXT,  -- JSON array

    -- Personalization
    adaptation_level TEXT DEFAULT 'standard' CHECK (adaptation_level IN ('minimal', 'standard', 'extensive')),
    personalization_factors TEXT,  -- JSON array
    context_applicability TEXT,  -- JSON array of applicable contexts

    -- Usage data
    usage_count INTEGER DEFAULT 0,
    effectiveness_rating REAL CHECK (effectiveness_rating >= 0.0 AND effectiveness_rating <= 1.0),
    last_used TIMESTAMP,
    success_rate REAL DEFAULT 0.0 CHECK (success_rate >= 0.0 AND success_rate <= 1.0),

    -- Status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated', 'experimental')),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Strategy usage logs table
CREATE TABLE IF NOT EXISTS strategy_usage_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    usage_context TEXT NOT NULL,  -- JSON context
    implementation_quality REAL CHECK (implementation_quality >= 0.0 AND implementation_quality <= 1.0),
    outcome_rating REAL CHECK (outcome_rating >= 0.0 AND outcome_rating <= 1.0),
    challenges_faced TEXT,  -- JSON array
    modifications_made TEXT,  -- JSON array
    lessons_learned TEXT,  -- JSON array
    duration_minutes INTEGER DEFAULT 0,
    would_recommend BOOLEAN,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES learning_strategies (id) ON DELETE CASCADE
);

-- Metacognitive feedback table
CREATE TABLE IF NOT EXISTS metacognitive_feedback (
    id TEXT PRIMARY KEY,
    feedback_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('reflection_analysis', 'strategy_suggestion', 'progress_evaluation', 'challenge_identification', 'goal_adjustment')),
    feedback_data TEXT NOT NULL,  -- JSON feedback content
    context TEXT,  -- JSON additional context
    automated_insights TEXT,  -- JSON array of insights
    patterns_identified TEXT,  -- JSON array of patterns

    -- Analysis results
    insights_generated TEXT NOT NULL,  -- JSON array
    improvement_areas TEXT,  -- JSON array
    strengths_confirmed TEXT,  -- JSON array

    -- Recommendations
    immediate_actions TEXT,  -- JSON array
    strategy_adjustments TEXT,  -- JSON array
    practice_recommendations TEXT,  -- JSON array
    reflection_prompts TEXT,  -- JSON array

    -- Follow-up
    next_steps TEXT,  -- JSON array
    follow_up_schedule TEXT,  -- JSON schedule
    success_criteria TEXT,  -- JSON array

    -- Status
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    implemented_at TIMESTAMP,
    implementation_status TEXT DEFAULT 'pending' CHECK (implementation_status IN ('pending', 'acknowledged', 'implemented', 'dismissed')),
    effectiveness_observed REAL CHECK (effectiveness_observed >= 0.0 AND effectiveness_observed <= 1.0),
);

-- Metacognitive journal table
CREATE TABLE IF NOT EXISTS metacognitive_journals (
    id TEXT PRIMARY KEY,
    entry_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Content
    reflection_type TEXT NOT NULL,
    learning_experience TEXT NOT NULL,
    insights_gained TEXT,  -- JSON array
    challenges_faced TEXT,  -- JSON array
    strategies_used TEXT,  -- JSON array
    effectiveness_assessment TEXT,

    -- Metacognitive analysis
    awareness_level_during REAL CHECK (awareness_level_during >= 0.0 AND awareness_level_during <= 1.0),
    regulation_actions_taken TEXT,  -- JSON array
    planning_effectiveness TEXT,
    monitoring_quality TEXT,
    evaluation_insights TEXT,

    -- Future planning
    adjustments_planned TEXT,  -- JSON array
    new_strategies_considered TEXT,  -- JSON array
    goals_for_next_session TEXT,  -- JSON array

    -- System analysis
    automated_insights TEXT,  -- JSON array
    pattern_recognition TEXT,  -- JSON array
    suggestions_generated TEXT,  -- JSON array

    -- Entry metadata
    emotional_state TEXT,
    confidence_level INTEGER CHECK (confidence_level >= 1 AND confidence_level <= 5),
    satisfaction_level INTEGER CHECK (satisfaction_level >= 1 AND satisfaction_level <= 5),
    entry_length INTEGER DEFAULT 0,

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Metacognitive milestones table
CREATE TABLE IF NOT EXISTS metacognitive_milestones (
    id TEXT PRIMARY KEY,
    milestone_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    competency_area TEXT NOT NULL,
    description TEXT NOT NULL,
    milestone_level TEXT DEFAULT 'intermediate' CHECK (milestone_level IN ('beginner', 'intermediate', 'advanced', 'expert')),

    -- Achievement criteria
    criteria TEXT NOT NULL,  -- JSON object with criteria
    assessment_methods TEXT,  -- JSON array
    evidence_required TEXT,  -- JSON array

    -- Progress tracking
    current_level REAL DEFAULT 0.0 CHECK (current_level >= 0.0 AND current_level <= 1.0),
    target_level REAL DEFAULT 1.0 CHECK (target_level >= 0.0 AND target_level <= 1.0),
    progress_percentage REAL DEFAULT 0.0 CHECK (progress_percentage >= 0.0 AND progress_percentage <= 100.0),

    -- Achievement data
    achieved_date TIMESTAMP,
    evidence_submitted TEXT,  -- JSON array
    assessment_results TEXT,  -- JSON object

    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'achieved', 'mastered', 'paused')),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Metacognitive profiles table
CREATE TABLE IF NOT EXISTS metacognitive_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    overall_awareness_level REAL DEFAULT 0.5 CHECK (overall_awareness_level >= 0.0 AND overall_awareness_level <= 1.0),
    regulation_competence REAL DEFAULT 0.5 CHECK (regulation_competence >= 0.0 AND regulation_competence <= 1.0),
    reflection_depth REAL DEFAULT 0.5 CHECK (reflection_depth >= 0.0 AND reflection_depth <= 1.0),
    strategy_sophistication REAL DEFAULT 0.5 CHECK (strategy_sophistication >= 0.0 AND strategy_sophistication <= 1.0),
    learning_autonomy REAL DEFAULT 0.5 CHECK (learning_autonomy >= 0.0 AND learning_autonomy <= 1.0),

    -- Preferences and styles
    preferred_reflection_types TEXT,  -- JSON array
    regulation_style TEXT DEFAULT 'balanced' CHECK (regulation_style IN ('proactive', 'reactive', 'balanced', 'adaptive')),
    strategic_approach TEXT DEFAULT 'systematic' CHECK (strategic_approach IN ('systematic', 'intuitive', 'flexible', 'structured')),
    adaptability_level REAL DEFAULT 0.5 CHECK (adaptability_level >= 0.0 AND adaptability_level <= 1.0),

    -- Development areas
    strength_areas TEXT,  -- JSON array
    growth_areas TEXT,  -- JSON array
    target_competencies TEXT,  -- JSON array

    -- Historical data
    sessions_completed INTEGER DEFAULT 0,
    average_reflection_quality REAL DEFAULT 0.0 CHECK (average_reflection_quality >= 0.0 AND average_reflection_quality <= 1.0),
    strategy_effectiveness_rating REAL DEFAULT 0.0 CHECK (strategy_effectiveness_rating >= 0.0 AND strategy_effectiveness_rating <= 1.0),
    improvement_trajectory REAL DEFAULT 0.0 CHECK (improvement_trajectory >= -1.0 AND improvement_trajectory <= 1.0),

    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scaffolding configurations table
CREATE TABLE IF NOT EXISTS scaffolding_configurations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    scaffolding_level TEXT NOT NULL CHECK (scaffolding_level IN ('minimal', 'light', 'moderate', 'heavy', 'extensive')),
    description TEXT NOT NULL,
    support_provided TEXT NOT NULL,  -- JSON array of support types
    guidance_prompts TEXT NOT NULL,  -- JSON array
    independence_expected REAL CHECK (independence_expected >= 0.0 AND independence_expected <= 1.0),
    fading_schedule TEXT,  -- JSON fading schedule
    adaptation_triggers TEXT,  -- JSON array

    -- Effectiveness
    usage_count INTEGER DEFAULT 0,
    effectiveness_rating REAL CHECK (effectiveness_rating >= 0.0 AND effectiveness_rating <= 1.0),
    user_satisfaction INTEGER CHECK (user_satisfaction >= 1 AND user_satisfaction <= 5),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adaptive recommendations table
CREATE TABLE IF NOT EXISTS adaptive_recommendations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    recommendation_type TEXT NOT NULL CHECK (recommendation_type IN ('strategy', 'reflection', 'regulation', 'goal', 'resource')),
    recommendation_data TEXT NOT NULL,  -- JSON recommendation content
    context_data TEXT,  -- JSON context that led to recommendation
    confidence_score REAL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    priority_level INTEGER DEFAULT 2 CHECK (priority_level >= 1 AND priority_level <= 5),
    expected_impact REAL CHECK (expected_impact >= 0.0 AND expected_impact <= 1.0),
    implementation_ease TEXT CHECK (implementation_ease IN ('easy', 'moderate', 'challenging')),

    -- Status tracking
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    presented_at TIMESTAMP,
    accepted_at TIMESTAMP,
    implemented_at TIMESTAMP,
    completed_at TIMESTAMP,

    status TEXT DEFAULT 'generated' CHECK (status IN ('generated', 'presented', 'accepted', 'implemented', 'completed', 'rejected', 'expired')),

    -- Effectiveness
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    actual_impact REAL CHECK (actual_impact >= -1.0 AND actual_impact <= 1.0),
    feedback_text TEXT,

    expires_at TIMESTAMP,

    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Metacognitive competencies table
CREATE TABLE IF NOT EXISTS metacognitive_competencies (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    competency_name TEXT NOT NULL,
    competency_category TEXT NOT NULL CHECK (competency_category IN ('planning', 'monitoring', 'evaluation', 'regulation', 'reflection')),
    current_level REAL DEFAULT 0.0 CHECK (current_level >= 0.0 AND current_level <= 1.0),
    target_level REAL DEFAULT 0.8 CHECK (target_level >= 0.0 AND target_level <= 1.0),
    growth_rate REAL DEFAULT 0.0 CHECK (growth_rate >= -0.1 AND growth_rate <= 0.1),

    -- Assessment data
    assessment_methods TEXT,  -- JSON array
    evidence_indicators TEXT,  -- JSON array
    last_assessment TIMESTAMP,
    next_assessment TIMESTAMP,

    -- Development activities
    development_activities TEXT,  -- JSON array
    practice_frequency REAL DEFAULT 0.0,
    mastery_indicators TEXT,  -- JSON array

    -- Progress tracking
    breakthrough_moments TEXT,  -- JSON array
    persistent_challenges TEXT,  -- JSON array
    strength_Indicators TEXT,  -- JSON array

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_metacognitive_sessions_user_id ON metacognitive_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_sessions_course_id ON metacognitive_sessions(course_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_sessions_session_type ON metacognitive_sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_metacognitive_sessions_started_at ON metacognitive_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_metacognitive_sessions_completion ON metacognitive_sessions(completion_percentage);

CREATE INDEX IF NOT EXISTS idx_metacognitive_phases_session_id ON metacognitive_phases(session_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_phases_phase_name ON metacognitive_phases(phase_name);
CREATE INDEX IF NOT EXISTS idx_metacognitive_phases_effectiveness ON metacognitive_phases(effectiveness_rating);

CREATE INDEX IF NOT EXISTS idx_reflection_activities_user_id ON reflection_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_reflection_activities_course_id ON reflection_activities(course_id);
CREATE INDEX IF NOT EXISTS idx_reflection_activities_session_id ON reflection_activities(session_id);
CREATE INDEX IF NOT EXISTS idx_reflection_activities_type ON reflection_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_reflection_activities_status ON reflection_activities(completion_status);

CREATE INDEX IF NOT EXISTS idx_reflection_responses_activity_id ON reflection_responses(activity_id);
CREATE INDEX IF NOT EXISTS idx_reflection_responses_user_id ON reflection_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_reflection_responses_confidence ON reflection_responses(confidence_level);
CREATE INDEX IF NOT EXISTS idx_reflection_responses_responded_at ON reflection_responses(responded_at);

CREATE INDEX IF NOT EXISTS idx_self_regulation_user_id ON self_regulation_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_self_regulation_course_id ON self_regulation_activities(course_id);
CREATE INDEX IF NOT EXISTS idx_self_regulation_phase ON self_regulation_activities(regulation_phase);
CREATE INDEX IF NOT EXISTS idx_self_regulation_status ON self_regulation_activities(implementation_status);
CREATE INDEX IF NOT EXISTS idx_self_regulation_effectiveness ON self_regulation_activities(effectiveness_rating);

CREATE INDEX IF NOT EXISTS idx_metacognitive_analytics_user_course ON metacognitive_analytics(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_analytics_date ON metacognitive_analytics(analysis_date);
CREATE INDEX IF NOT EXISTS idx_metacognitive_analytics_type ON metacognitive_analytics(analysis_type);

CREATE INDEX IF NOT EXISTS idx_learning_strategies_user_id ON learning_strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_strategies_course_id ON learning_strategies(course_id);
CREATE INDEX IF NOT EXISTS idx_learning_strategies_type ON learning_strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_learning_strategies_effectiveness ON learning_strategies(effectiveness_rating);
CREATE INDEX IF NOT EXISTS idx_learning_strategies_status ON learning_strategies(status);

CREATE INDEX IF NOT EXISTS idx_strategy_usage_logs_strategy_id ON strategy_usage_logs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_usage_logs_user_id ON strategy_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_usage_logs_outcome ON strategy_usage_logs(outcome_rating);
CREATE INDEX IF NOT EXISTS idx_strategy_usage_logs_used_at ON strategy_usage_logs(used_at);

CREATE INDEX IF NOT EXISTS idx_metacognitive_feedback_user_id ON metacognitive_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_feedback_type ON metacognitive_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_metacognitive_feedback_status ON metacognitive_feedback(implementation_status);
CREATE INDEX IF NOT EXISTS idx_metacognitive_feedback_processed_at ON metacognitive_feedback(processed_at);

CREATE INDEX IF NOT EXISTS idx_metacognitive_journals_user_id ON metacognitive_journals(user_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_journals_course_id ON metacognitive_journals(course_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_journals_entry_date ON metacognitive_journals(entry_date);
CREATE INDEX IF NOT EXISTS idx_metacognitive_journals_reflection_type ON metacognitive_journals(reflection_type);

CREATE INDEX IF NOT EXISTS idx_metacognitive_milestones_user_id ON metacognitive_milestones(user_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_milestones_course_id ON metacognitive_milestones(course_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_milestones_competency ON metacognitive_milestones(competency_area);
CREATE INDEX IF NOT EXISTS idx_metacognitive_milestones_status ON metacognitive_milestones(status);
CREATE INDEX IF NOT EXISTS idx_metacognitive_milestones_progress ON metacognitive_milestones(progress_percentage);

CREATE INDEX IF NOT EXISTS idx_metacognitive_profiles_user_id ON metacognitive_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_profiles_updated_at ON metacognitive_profiles(last_updated);

CREATE INDEX IF NOT EXISTS idx_scaffolding_configurations_user_id ON scaffolding_configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_scaffolding_configurations_level ON scaffolding_configurations(scaffolding_level);
CREATE INDEX IF NOT EXISTS idx_scaffolding_configurations_effectiveness ON scaffolding_configurations(effectiveness_rating);

CREATE INDEX IF NOT EXISTS idx_adaptive_recommendations_user_id ON adaptive_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_adaptive_recommendations_course_id ON adaptive_recommendations(course_id);
CREATE INDEX IF NOT EXISTS idx_adaptive_recommendations_type ON adaptive_recommendations(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_adaptive_recommendations_status ON adaptive_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_adaptive_recommendations_priority ON adaptive_recommendations(priority_level);
CREATE INDEX IF NOT EXISTS idx_adaptive_recommendations_expires_at ON adaptive_recommendations(expires_at);

CREATE INDEX IF NOT EXISTS idx_metacognitive_competencies_user_id ON metacognitive_competencies(user_id);
CREATE INDEX IF NOT EXISTS idx_metacognitive_competencies_category ON metacognitive_competencies(competency_category);
CREATE INDEX IF NOT EXISTS idx_metacognitive_competencies_current_level ON metacognitive_competencies(current_level);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_metacognitive_sessions_completed_at
    AFTER UPDATE ON metacognitive_sessions
    FOR EACH ROW
WHEN NEW.completed_at != OLD.completed_at
BEGIN
    UPDATE metacognitive_sessions SET completed_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_metacognitive_phases_completed_at
    AFTER UPDATE ON metacognitive_phases
    FOR EACH ROW
WHEN NEW.completed_at != OLD.completed_at
BEGIN
    UPDATE metacognitive_phases SET completed_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_learning_strategies_updated_at
    AFTER UPDATE ON learning_strategies
    FOR EACH ROW
BEGIN
    UPDATE learning_strategies SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_metacognitive_profiles_updated_at
    AFTER UPDATE ON metacognitive_profiles
    FOR EACH ROW
BEGIN
    UPDATE metacognitive_profiles SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_metacognitive_milestones_updated_at
    AFTER UPDATE ON metacognitive_milestones
    FOR EACH ROW
BEGIN
    UPDATE metacognitive_milestones SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_scaffolding_configurations_updated_at
    AFTER UPDATE ON scaffolding_configurations
    FOR EACH ROW
BEGIN
    UPDATE scaffolding_configurations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_metacognitive_competencies_updated_at
    AFTER UPDATE ON metacognitive_competencies
    FOR EACH ROW
BEGIN
    UPDATE metacognitive_competencies SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Views for common queries
CREATE VIEW IF NOT EXISTS user_metacognitive_summary AS
SELECT
    mp.user_id,
    mp.overall_awareness_level,
    mp.regulation_competence,
    mp.reflection_depth,
    mp.strategy_sophistication,
    mp.learning_autonomy,
    COUNT(DISTINCT ms.id) as total_sessions,
    COUNT(DISTINCT ra.id) as total_reflections,
    COUNT(DISTINCT sra.id) as total_regulation_activities,
    AVG(ms.session_quality) as average_session_quality,
    AVG(ra.reflection_quality) as average_reflection_quality,
    AVG(sra.effectiveness_rating) as average_regulation_effectiveness
FROM metacognitive_profiles mp
LEFT JOIN metacognitive_sessions ms ON mp.user_id = ms.user_id
LEFT JOIN reflection_activities ra ON mp.user_id = ra.user_id
LEFT JOIN self_regulation_activities sra ON mp.user_id = sra.user_id
GROUP BY mp.user_id;

CREATE VIEW IF NOT EXISTS active_metacognitive_goals AS
SELECT
    mm.user_id,
    mm.course_id,
    mm.competency_area,
    mm.current_level,
    mm.target_level,
    mm.progress_percentage,
    mm.last_assessment,
    mm.next_assessment,
    CASE
        WHEN mm.next_assessment < datetime('now') THEN 'overdue'
        WHEN mm.next_assessment < datetime('now', '+3 days') THEN 'due_soon'
        ELSE 'on_track'
    END as urgency_status
FROM metacognitive_milestones mm
WHERE mm.status IN ('pending', 'in_progress')
ORDER BY mm.next_assessment ASC;

CREATE VIEW IF NOT EXISTS effective_strategies AS
SELECT
    ls.user_id,
    ls.strategy_id,
    ls.strategy_name,
    ls.strategy_type,
    ls.usage_count,
    ls.effectiveness_rating,
    AVG(sul.outcome_rating) as average_outcome_rating,
    COUNT(sul.id) as usage_logs_count,
    MAX(sul.used_at) as last_used_date
FROM learning_strategies ls
LEFT JOIN strategy_usage_logs sul ON ls.strategy_id = sul.strategy_id
WHERE ls.status = 'active'
GROUP BY ls.strategy_id
HAVING ls.usage_count > 0
ORDER BY ls.effectiveness_rating DESC;