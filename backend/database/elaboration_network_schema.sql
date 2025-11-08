-- Elaboration Network Database Schema
-- Stores knowledge networks, concept connections, and transfer pathways

-- Knowledge networks table
CREATE TABLE IF NOT EXISTS en_networks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    network_type TEXT DEFAULT 'hybrid_elaboration',
    topology TEXT DEFAULT 'scale_free',
    integration_level TEXT DEFAULT 'deep',
    knowledge_base TEXT NOT NULL,  -- JSON knowledge structure
    network_architecture TEXT NOT NULL,  -- JSON NetworkArchitecture
    connection_matrix TEXT NOT NULL,  -- JSON ConnectionMatrix
    transfer_networks TEXT NOT NULL,  -- JSON TransferNetwork
    optimized_network TEXT NOT NULL,  -- JSON OptimizedNetwork
    network_metrics TEXT NOT NULL,  -- JSON NetworkMetrics
    learning_objectives TEXT,  -- JSON learning objectives
    focus_concepts TEXT,  -- JSON focus concepts
    metadata TEXT,  -- JSON additional metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Concepts table
CREATE TABLE IF NOT EXISTS en_concepts (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    attributes TEXT,  -- JSON array
    relationships TEXT,  -- JSON array
    complexity TEXT DEFAULT 'moderate',
    category TEXT DEFAULT 'general',
    importance REAL DEFAULT 0.5 CHECK (importance >= 0.0 AND importance <= 1.0),
    prerequisites TEXT,  -- JSON array
    related_concepts TEXT,  -- JSON array
    mastery_level REAL DEFAULT 0.0 CHECK (mastery_level >= 0.0 AND mastery_level <= 1.0),
    last_practiced TIMESTAMP,
    cle_integration TEXT,  -- JSON CLE phase integrations
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Concept connections table
CREATE TABLE IF NOT EXISTS en_connections (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    connection_type TEXT NOT NULL,
    strength REAL DEFAULT 0.5 CHECK (strength >= 0.0 AND strength <= 1.0),
    bidirectional BOOLEAN DEFAULT FALSE,
    cle_enhancement TEXT,  -- JSON CLE phase enhancements
    transfer_potential REAL DEFAULT 0.0 CHECK (transfer_potential >= 0.0 AND transfer_potential <= 1.0),
    description TEXT,
    evidence TEXT,  -- JSON array of evidence
    cle_strength_boost REAL DEFAULT 0.0 CHECK (cle_strength_boost >= 0.0 AND cle_strength_boost <= 0.2),
    predicted_retention REAL DEFAULT 0.0 CHECK (predicted_retention >= 0.0 AND predicted_retention <= 1.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Transfer pathways table
CREATE TABLE IF NOT EXISTS en_transfer_pathways (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    pathway_id TEXT NOT NULL,
    source_concept TEXT NOT NULL,
    target_concept TEXT NOT NULL,
    connection_strength REAL NOT NULL,
    transfer_score REAL NOT NULL,
    domains TEXT NOT NULL,  -- JSON array of TransferDomain
    readiness_factors TEXT,  -- JSON array
    scaffolding_needs TEXT,  -- JSON array
    success_criteria TEXT,  -- JSON array
    estimated_time INTEGER DEFAULT 0,
    transfer_depth TEXT DEFAULT 'near_transfer',
    effectiveness_score REAL CHECK (effectiveness_score >= 0.0 AND effectiveness_score <= 1.0),
    usage_count INTEGER DEFAULT 0,
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Knowledge clusters table
CREATE TABLE IF NOT EXISTS en_knowledge_clusters (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    cluster_id TEXT NOT NULL,
    concepts TEXT NOT NULL,  -- JSON array of concept IDs
    centrality REAL DEFAULT 0.5 CHECK (centrality >= 0.0 AND centrality <= 1.0),
    coherence REAL DEFAULT 0.5 CHECK (coherence >= 0.0 AND coherence <= 1.0),
    cluster_type TEXT DEFAULT 'general',
    hub_concept TEXT,
    sub_clusters TEXT,  -- JSON array
    cluster_strength REAL DEFAULT 0.0 CHECK (cluster_strength >= 0.0 AND cluster_strength <= 1.0),
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Elaboration activities table
CREATE TABLE IF NOT EXISTS en_elaboration_activities (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    activity_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    title TEXT NOT NULL,
    connection_type TEXT,
    strength REAL,
    cle_enhancements TEXT,  -- JSON array
    elaboration_tasks TEXT NOT NULL,  -- JSON array of ElaborationTask
    estimated_time INTEGER NOT NULL,
    elaboration_depth TEXT,
    transfer_score REAL,
    domains TEXT,  -- JSON array of TransferDomain
    readiness_factors TEXT,  -- JSON array
    scaffolding_needs TEXT,  -- JSON array
    success_criteria TEXT,  -- JSON array
    comprehensive_depth TEXT,
    difficulty_level TEXT DEFAULT 'moderate',
    completion_status TEXT DEFAULT 'pending' CHECK (completion_status IN ('pending', 'in_progress', 'completed', 'skipped')),
    effectiveness_score REAL CHECK (effectiveness_score >= 0.0 AND effectiveness_score <= 1.0),
    user_feedback TEXT,  -- JSON feedback data
    completed_at TIMESTAMP,
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Activity templates table
CREATE TABLE IF NOT EXISTS en_activity_templates (
    id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    connection_types TEXT NOT NULL,  -- JSON array
    transfer_domains TEXT NOT NULL,  -- JSON array
    base_tasks TEXT NOT NULL,  -- JSON array of ElaborationTask
    customization_options TEXT,  -- JSON array
    estimated_duration INTEGER NOT NULL,
    difficulty_level TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0,
    effectiveness_score REAL DEFAULT 0.0 CHECK (effectiveness_score >= 0.0 AND effectiveness_score <= 1.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assessment framework table
CREATE TABLE IF NOT EXISTS en_assessment_frameworks (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    assessment_types TEXT NOT NULL,  -- JSON array of AssessmentType
    evaluation_criteria TEXT NOT NULL,  -- JSON EvaluationCriteria
    feedback_mechanisms TEXT NOT NULL,  -- JSON array of FeedbackMechanism
    progress_tracking TEXT NOT NULL,  -- JSON ProgressTracking
    adaptation_triggers TEXT,  -- JSON array
    reporting_frequency TEXT DEFAULT 'weekly',
    last_assessment TIMESTAMP,
    overall_effectiveness REAL CHECK (overall_effectiveness >= 0.0 AND overall_effectiveness <= 1.0),
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- CLE integration data table
CREATE TABLE IF NOT EXISTS en_cle_integration (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    phase_data TEXT NOT NULL,  -- JSON CLEPhaseData objects
    integrated_metrics TEXT NOT NULL,  -- JSON IntegratedMetrics
    cle_effectiveness REAL DEFAULT 0.0 CHECK (cle_effectiveness >= 0.0 AND cle_effectiveness <= 1.0),
    integration_quality REAL DEFAULT 0.0 CHECK (integration_quality >= 0.0 AND integration_quality <= 1.0),
    synergy_multiplier REAL DEFAULT 1.0 CHECK (synergy_multiplier >= 1.0 AND synergy_multiplier <= 3.0),
    optimization_opportunities TEXT,  -- JSON array
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Knowledge gaps table
CREATE TABLE IF NOT EXISTS en_knowledge_gaps (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    concept_name TEXT NOT NULL,
    current_mastery REAL NOT NULL,
    complexity TEXT NOT NULL,
    importance REAL NOT NULL,
    gap_severity TEXT DEFAULT 'medium',
    recommended_action TEXT,
    priority INTEGER CHECK (priority >= 1 AND priority <= 5),
    identified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    addressed_at TIMESTAMP,
    improvement_made REAL CHECK (improvement_made >= -1.0 AND improvement_made <= 1.0),
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Strength areas table
CREATE TABLE IF NOT EXISTS en_strength_areas (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    concept_name TEXT NOT NULL,
    mastery_level REAL NOT NULL,
    complexity TEXT NOT NULL,
    transfer_potential REAL CHECK (transfer_potential >= 0.0 AND transfer_potential <= 1.0),
    application_opportunities TEXT,  -- JSON array
    identified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    utilized_at TIMESTAMP,
    utilization_effectiveness REAL CHECK (utilization_effectiveness >= 0.0 AND utilization_effectiveness <= 1.0),
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- User network profiles table
CREATE TABLE IF NOT EXISTS en_user_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    network_preference TEXT DEFAULT 'adaptive',
    elaboration_style TEXT DEFAULT 'balanced',
    transfer_domain_preferences TEXT,  -- JSON array of TransferDomain
    connection_patterns TEXT,  -- JSON array
    learning_velocity REAL DEFAULT 0.0,
    transfer_confidence REAL DEFAULT 0.5 CHECK (transfer_confidence >= 0.0 AND transfer_confidence <= 1.0),
    metacognitive_awareness REAL DEFAULT 0.5 CHECK (metacognitive_awareness >= 0.0 AND metacognitive_awareness <= 1.0),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Network personalization table
CREATE TABLE IF NOT EXISTS en_network_personalization (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    network_id TEXT NOT NULL,
    customization_preferences TEXT NOT NULL,  -- JSON preferences
    learning_objectives TEXT,  -- JSON array
    challenge_areas TEXT,  -- JSON array
    strength_areas TEXT,  -- JSON array
    adaptation_history TEXT,  -- JSON array
    effectiveness_feedback TEXT,  -- JSON feedback scores
    personalization_score REAL DEFAULT 0.0 CHECK (personalization_score >= 0.0 AND personalization_score <= 1.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Elaboration sessions table
CREATE TABLE IF NOT EXISTS en_elaboration_sessions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    network_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    activity_ids TEXT,  -- JSON array of activity IDs
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_time_spent INTEGER DEFAULT 0,
    progress_tracking TEXT,  -- JSON progress data
    user_responses TEXT,  -- JSON array of responses
    adaptations_made TEXT,  -- JSON array of adaptations
    completion_percentage REAL DEFAULT 0.0 CHECK (completion_percentage >= 0.0 AND completion_percentage <= 1.0),
    effectiveness_score REAL CHECK (effectiveness_score >= 0.0 AND effectiveness_score <= 1.0),
    session_quality REAL CHECK (session_quality >= 0.0 AND session_quality <= 1.0),
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Network analytics table
CREATE TABLE IF NOT EXISTS en_network_analytics (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    period_days INTEGER NOT NULL,
    total_concepts INTEGER DEFAULT 0,
    total_connections INTEGER DEFAULT 0,
    network_density REAL DEFAULT 0.0,
    clustering_coefficient REAL DEFAULT 0.0,
    average_path_length REAL DEFAULT 0.0,
    transfer_readiness REAL DEFAULT 0.0,
    elaboration_quality REAL DEFAULT 0.0,
    cle_integration_score REAL DEFAULT 0.0,
    knowledge_integration REAL DEFAULT 0.0,
    learning_outcomes TEXT,  -- JSON LearningOutcomes
    recommendations TEXT,  -- JSON array
    improvement_trends TEXT,  -- JSON trends data
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Network milestones table
CREATE TABLE IF NOT EXISTS en_network_milestones (
    id TEXT PRIMARY KEY,
    milestone_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    milestone_type TEXT NOT NULL,
    description TEXT NOT NULL,
    criteria TEXT NOT NULL,  -- JSON criteria
    achievement_date TIMESTAMP,
    status TEXT DEFAULT 'pending',
    achievement_evidence TEXT,  -- JSON evidence
    impact_assessment REAL CHECK (impact_assessment >= 0.0 AND impact_assessment <= 1.0),
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Achievement records table
CREATE TABLE IF NOT EXISTS en_achievement_records (
    id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL UNIQUE,
    milestone_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    achievement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    achieved_criteria TEXT NOT NULL,  -- JSON achieved criteria
    evidence TEXT,  -- JSON array
    impact_assessment REAL CHECK (impact_assessment >= 0.0 AND impact_assessment <= 1.0),
    recognition_level TEXT DEFAULT 'recognition',
    next_milestone TEXT,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Visualization data table
CREATE TABLE IF NOT EXISTS en_visualization_data (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    visualization_type TEXT DEFAULT 'interactive',
    layout_algorithm TEXT DEFAULT 'force_directed',
    color_scheme TEXT DEFAULT 'cognitive',
    nodes TEXT NOT NULL,  -- JSON nodes data
    edges TEXT NOT NULL,  -- JSON edges data
    clusters TEXT,  -- JSON clusters data
    pathways TEXT,  -- JSON pathways data
    metrics TEXT NOT NULL,  -- JSON metrics
    config_options TEXT,  -- JSON configuration
    last_generated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Network optimization history table
CREATE TABLE IF NOT EXISTS en_optimization_history (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    optimization_type TEXT NOT NULL,
    original_metrics TEXT,  -- JSON original metrics
    optimized_metrics TEXT,  -- JSON optimized metrics
    improvements_made TEXT,  -- JSON array of improvements
    performance_impact REAL DEFAULT 0.0,
    optimization_reason TEXT,
    algorithm_version TEXT DEFAULT '1.0',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    effectiveness_observed REAL CHECK (effectiveness_observed >= 0.0 AND effectiveness_observed <= 1.0),
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Comparative analysis table
CREATE TABLE IF NOT EXISTS en_comparative_analysis (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    course_id TEXT NOT NULL,
    analysis_type TEXT DEFAULT 'temporal',
    comparison_periods TEXT,  -- JSON array of periods
    network_evolution TEXT,  -- JSON evolution data
    performance_trends TEXT,  -- JSON trends
    improvement_patterns TEXT,  -- JSON array
    strategic_insights TEXT,  -- JSON array
    visualizations TEXT,  -- JSON array
    strategic_recommendations TEXT,  -- JSON array
    improvement_roadmap TEXT,  -- JSON roadmap
    confidence_level REAL CHECK (confidence_level >= 0.0 AND confidence_level <= 1.0),
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Network export cache table
CREATE TABLE IF NOT EXISTS en_export_cache (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    export_format TEXT DEFAULT 'json',
    include_analytics BOOLEAN DEFAULT TRUE,
    include_activities BOOLEAN DEFAULT TRUE,
    export_purpose TEXT DEFAULT 'analysis',
    cached_data TEXT NOT NULL,  -- JSON cached export data
    file_size INTEGER DEFAULT 0,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    FOREIGN KEY (network_id) REFERENCES en_networks (id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_en_networks_user_id ON en_networks(user_id);
CREATE INDEX IF NOT EXISTS idx_en_networks_course_id ON en_networks(course_id);
CREATE INDEX IF NOT EXISTS idx_en_networks_network_type ON en_networks(network_type);
CREATE INDEX IF NOT EXISTS idx_en_networks_created_at ON en_networks(created_at);
CREATE INDEX IF NOT EXISTS idx_en_networks_updated_at ON en_networks(updated_at);

CREATE INDEX IF NOT EXISTS idx_en_concepts_network_id ON en_concepts(network_id);
CREATE INDEX IF NOT EXISTS idx_en_concepts_name ON en_concepts(name);
CREATE INDEX IF NOT EXISTS idx_en_concepts_category ON en_concepts(category);
CREATE INDEX IF NOT EXISTS idx_en_concepts_importance ON en_concepts(importance);
CREATE INDEX IF NOT EXISTS idx_en_concepts_mastery_level ON en_concepts(mastery_level);

CREATE INDEX IF NOT EXISTS idx_en_connections_network_id ON en_connections(network_id);
CREATE INDEX IF NOT EXISTS idx_en_connections_source_id ON en_connections(source_id);
CREATE INDEX IF NOT EXISTS idx_en_connections_target_id ON en_connections(target_id);
CREATE INDEX IF NOT EXISTS idx_en_connections_type ON en_connections(connection_type);
CREATE INDEX IF NOT EXISTS idx_en_connections_strength ON en_connections(strength);
CREATE INDEX IF NOT EXISTS idx_en_connections_transfer_potential ON en_connections(transfer_potential);

CREATE INDEX IF NOT EXISTS idx_en_pathways_network_id ON en_transfer_pathways(network_id);
CREATE INDEX IF NOT EXISTS idx_en_pathways_source_concept ON en_transfer_pathways(source_concept);
CREATE INDEX IF NOT EXISTS idx_en_pathways_target_concept ON en_transfer_pathways(target_concept);
CREATE INDEX IF NOT EXISTS idx_en_pathways_transfer_score ON en_transfer_pathways(transfer_score);

CREATE INDEX IF NOT EXISTS idx_en_clusters_network_id ON en_knowledge_clusters(network_id);
CREATE INDEX IF NOT EXISTS idx_en_clusters_centrality ON en_knowledge_clusters(centrality);
CREATE INDEX IF NOT EXISTS idx_en_clusters_coherence ON en_knowledge_clusters(coherence);

CREATE INDEX IF NOT EXISTS idx_en_activities_network_id ON en_elaboration_activities(network_id);
CREATE INDEX IF NOT EXISTS idx_en_activities_type ON en_elaboration_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_en_activities_status ON en_elaboration_activities(completion_status);
CREATE INDEX IF NOT EXISTS idx_en_activities_difficulty ON en_elaboration_activities(difficulty_level);

CREATE INDEX IF NOT EXISTS idx_en_assessments_network_id ON en_assessment_frameworks(network_id);
CREATE INDEX IF NOT EXISTS idx_en_assessments_effectiveness ON en_assessment_frameworks(overall_effectiveness);

CREATE INDEX IF NOT EXISTS idx_en_cle_integration_network_id ON en_cle_integration(network_id);
CREATE INDEX IF NOT EXISTS idx_en_cle_integration_effectiveness ON en_cle_integration(cle_effectiveness);

CREATE INDEX IF NOT EXISTS idx_en_gaps_network_id ON en_knowledge_gaps(network_id);
CREATE INDEX IF NOT EXISTS idx_en_gaps_severity ON en_knowledge_gaps(gap_severity);
CREATE INDEX IF NOT EXISTS idx_en_gaps_priority ON en_knowledge_gaps(priority);

CREATE INDEX IF NOT EXISTS idx_en_strengths_network_id ON en_strength_areas(network_id);
CREATE INDEX IF NOT EXISTS idx_en_strengths_transfer_potential ON en_strength_areas(transfer_potential);

CREATE INDEX IF NOT EXISTS idx_en_profiles_user_id ON en_user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_en_profiles_last_updated ON en_user_profiles(last_updated);

CREATE INDEX IF NOT EXISTS idx_en_personalization_user_id ON en_network_personalization(user_id);
CREATE INDEX IF NOT EXISTS idx_en_personalization_network_id ON en_network_personalization(network_id);

CREATE INDEX IF NOT EXISTS idx_en_sessions_network_id ON en_elaboration_sessions(network_id);
CREATE INDEX IF NOT EXISTS idx_en_sessions_user_id ON en_elaboration_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_en_sessions_start_time ON en_elaboration_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_en_sessions_effectiveness ON en_elaboration_sessions(effectiveness_score);

CREATE INDEX IF NOT EXISTS idx_en_analytics_user_course ON en_network_analytics(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_en_analytics_period ON en_network_analytics(period_days);
CREATE INDEX IF NOT EXISTS idx_en_analytics_valid_until ON en_network_analytics(valid_until);

CREATE INDEX IF NOT EXISTS idx_en_milestones_user_course ON en_network_milestones(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_en_milestones_type ON en_network_milestones(milestone_type);
CREATE INDEX IF NOT EXISTS idx_en_milestones_status ON en_network_milestones(status);

CREATE INDEX IF NOT EXISTS idx_en_achievements_user_id ON en_achievement_records(user_id);
CREATE INDEX IF NOT EXISTS idx_en_achievements_milestone_id ON en_achievement_records(milestone_id);
CREATE INDEX IF NOT EXISTS idx_en_achievements_date ON en_achievement_records(achievement_date);

CREATE INDEX IF NOT EXISTS idx_en_visualization_network_id ON en_visualization_data(network_id);
CREATE INDEX IF NOT EXISTS idx_en_visualization_type ON en_visualization_data(visualization_type);
CREATE INDEX IF NOT EXISTS idx_en_visualization_generated ON en_visualization_data(last_generated);

CREATE INDEX IF NOT EXISTS idx_en_optimization_network_id ON en_optimization_history(network_id);
CREATE INDEX IF NOT EXISTS idx_en_optimization_type ON en_optimization_history(optimization_type);
CREATE INDEX IF NOT EXISTS idx_en_optimization_applied_at ON en_optimization_history(applied_at);

CREATE INDEX IF NOT EXISTS idx_en_comparative_user_course ON en_comparative_analysis(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_en_comparative_analysis_date ON en_comparative_analysis(analysis_date);

CREATE INDEX IF NOT EXISTS idx_en_export_network_id ON en_export_cache(network_id);
CREATE INDEX IF NOT EXISTS idx_en_export_format ON en_export_cache(export_format);
CREATE INDEX IF NOT EXISTS idx_en_export_expires_at ON en_export_cache(expires_at);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_en_networks_timestamp
    AFTER UPDATE ON en_networks
    FOR EACH ROW
BEGIN
    UPDATE en_networks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_en_concepts_last_practiced
    AFTER UPDATE ON en_concepts
    FOR EACH ROW
WHEN NEW.mastery_level != OLD.mastery_level
BEGIN
    UPDATE en_concepts SET last_practiced = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_en_user_profiles_timestamp
    AFTER UPDATE ON en_user_profiles
    FOR EACH ROW
BEGIN
    UPDATE en_user_profiles SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_en_cle_integration_timestamp
    AFTER UPDATE ON en_cle_integration
    FOR EACH ROW
BEGIN
    UPDATE en_cle_integration SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;