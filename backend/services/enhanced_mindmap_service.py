"""
Enhanced Mindmap Service with Cognitive Load Theory and GLM-4.6 Integration
Implements advanced educational psychology principles for concept map generation
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from enum import Enum

from services.advanced_model_selector import AdvancedModelSelector
from services.prompt_analytics_service import PromptAnalyticsService
from services.advanced_prompt_templates import AdvancedPromptTemplates
from llm_service import LLMService
from services.study_tracker import StudyTracker
from services.rag_service import RAGService

logger = logging.getLogger(__name__)

class StudySessionContext:
    """Context data for study session aware mindmap generation"""

    def __init__(self, session_data: Dict[str, Any] = None):
        self.session_id = session_data.get("session_id") if session_data else None
        self.course_id = session_data.get("course_id") if session_data else None
        self.book_id = session_data.get("book_id") if session_data else None
        self.current_progress = session_data.get("current_progress", 0) if session_data else 0
        self.weak_areas = session_data.get("weak_areas", []) if session_data else []
        self.mastery_levels = session_data.get("mastery_levels", {}) if session_data else {}
        self.quiz_performance = session_data.get("quiz_performance", {}) if session_data else {}
        self.study_time_today = session_data.get("study_time_today", 0) if session_data else 0
        self.preferred_difficulty = session_data.get("preferred_difficulty", "adaptive") if session_data else "adaptive"
        self.recently_studied = session_data.get("recently_studied", []) if session_data else []
        self.goals = session_data.get("goals", []) if session_data else []

class CognitiveLoadLevel(Enum):
    """Cognitive load levels for mindmap optimization"""
    MINIMAL = "minimal"      # 3-4 concepts, simple relationships
    MODERATE = "moderate"    # 5-7 concepts, some cross-connections
    COMPLEX = "complex"      # 8-12 concepts, rich relationships
    EXPERT = "expert"        # 13+ concepts, complex networks

class KnowledgeType(Enum):
    """Types of knowledge for mindmap structuring"""
    FACTUAL = "factual"         # Facts, terms, basic concepts
    CONCEPTUAL = "conceptual"   # Relationships, categories, principles
    PROCEDURAL = "procedural"   # Processes, methods, how-to
    METACOGNITIVE = "metacognitive"  # Learning strategies, reflection

class RelationshipType(Enum):
    """Types of relationships between concepts"""
    HIERARCHICAL = "hierarchical"    # Parent-child, part-whole
    CAUSAL = "causal"              # Cause-effect relationships
    COMPARATIVE = "comparative"     # Similarities, differences
    TEMPORAL = "temporal"          # Time sequences, stages
    ASSOCIATIVE = "associative"    # Related concepts, context

class EnhancedMindmapService:
    """Enhanced mindmap generation with cognitive science and GLM-4.6 integration"""

    def __init__(self):
        self.model_selector = AdvancedModelSelector()
        self.analytics = PromptAnalyticsService()
        self.prompt_templates = AdvancedPromptTemplates()
        self.llm_service = LLMService()
        self.study_tracker = StudyTracker()
        self.rag_service = RAGService()

        # Cognitive load theory parameters
        self.max_branches_per_node = {
            CognitiveLoadLevel.MINIMAL: 3,
            CognitiveLoadLevel.MODERATE: 4,
            CognitiveLoadLevel.COMPLEX: 5,
            CognitiveLoadLevel.EXPERT: 6
        }

        self.max_concepts_per_level = {
            CognitiveLoadLevel.MINIMAL: (4, 8),     # (main, total)
            CognitiveLoadLevel.MODERATE: (6, 15),
            CognitiveLoadLevel.COMPLEX: (8, 25),
            CognitiveLoadLevel.EXPERT: (10, 40)
        }

    async def generate_enhanced_mindmap(
        self,
        topic: str,
        context_text: str,
        course_id: str,
        book_id: str,
        learner_profile: Optional[Dict[str, Any]] = None,
        cognitive_load_level: Optional[str] = None,
        knowledge_type: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
        previous_mindmaps: Optional[List[Dict[str, Any]]] = None,
        session_context: Optional[StudySessionContext] = None
    ) -> Dict[str, Any]:
        """
        Generate enhanced mindmap using cognitive load theory and GLM-4.6 relationship modeling

        Args:
            topic: Main topic for the mindmap
            context_text: RAG-retrieved context materials
            course_id: Course identifier
            book_id: Book identifier
            learner_profile: Learner's characteristics and preferences
            cognitive_load_level: Desired cognitive load complexity
            knowledge_type: Type of knowledge being mapped
            focus_areas: Specific areas to focus on
            previous_mindmaps: Previously generated mindmaps for progression
            session_context: Study session context for personalization

        Returns:
            Enhanced mindmap structure with cognitive optimization and session awareness
        """
        start_time = datetime.now()

        try:
            # Analyze learner profile and determine optimal parameters
            learner_analysis = self._analyze_learner_profile(learner_profile)

            # Enhance learner analysis with session context if available
            if session_context:
                learner_analysis = self._enhance_learner_analysis_with_session_context(
                    learner_analysis, session_context
                )

            cognitive_load = self._determine_cognitive_load_level(
                cognitive_load_level, learner_analysis, topic
            )
            knowledge_type_enum = self._determine_knowledge_type(knowledge_type, topic)

            # Enhance context text with session-specific information if available
            enhanced_context_text = self._enhance_context_with_session_data(
                context_text, session_context, focus_areas
            )

            # Extract core concepts using GLM-4.6 for relationship modeling
            concepts_analysis = await self._extract_concepts_with_glm46(
                topic, enhanced_context_text, cognitive_load, knowledge_type_enum
            )

            # Build mindmap structure with cognitive optimization
            mindmap_structure = self._build_cognitively_optimized_structure(
                concepts_analysis, cognitive_load, knowledge_type_enum
            )

            # Enhance structure with session context if available
            if session_context:
                mindmap_structure = self._enhance_structure_with_session_context(
                    mindmap_structure, session_context, concepts_analysis
                )

            # Enhance with learning science principles
            enhanced_mindmap = await self._enhance_with_learning_science(
                mindmap_structure, learner_analysis, knowledge_type_enum
            )

            # Generate study guidance and AI interaction hints
            study_guidance = await self._generate_study_guidance(
                enhanced_mindmap, learner_analysis, knowledge_type_enum
            )

            # Build final response
            result = {
                "id": f"enhanced_mindmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": enhanced_mindmap["title"],
                "overview": enhanced_mindmap["overview"],
                "cognitive_load_level": cognitive_load.value,
                "knowledge_type": knowledge_type_enum.value,
                "nodes": enhanced_mindmap["nodes"],
                "relationships": enhanced_mindmap["relationships"],
                "study_guidance": study_guidance,
                "learning_optimizations": enhanced_mindmap["optimizations"],
                "session_aware": session_context is not None,
                "metadata": {
                    "course_id": course_id,
                    "book_id": book_id,
                    "learner_profile": learner_analysis,
                    "session_context": {
                        "session_id": session_context.session_id,
                        "current_progress": session_context.current_progress,
                        "weak_areas": session_context.weak_areas,
                        "preferred_difficulty": session_context.preferred_difficulty
                    } if session_context else None,
                    "generation_model": "GLM-4.6",
                    "cognitive_optimization": True,
                    "session_enhanced": session_context is not None,
                    "created_at": datetime.now().isoformat(),
                    "focus_areas": focus_areas or [],
                    "concept_count": len(enhanced_mindmap["nodes"]),
                    "relationship_count": len(enhanced_mindmap["relationships"])
                }
            }

            # Analytics tracking
            duration = (datetime.now() - start_time).total_seconds()
            await self._track_generation_analytics(
                topic, cognitive_load, knowledge_type_enum, result, duration
            )

            return result

        except Exception as e:
            logger.error(f"Enhanced mindmap generation failed: {e}")
            # Fallback to basic mindmap
            return await self._generate_fallback_mindmap(topic, context_text, course_id, book_id)

    def _analyze_learner_profile(self, learner_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze learner profile to determine optimal mindmap parameters"""
        if not learner_profile:
            learner_profile = {}

        # Default characteristics for unknown learners
        analysis = {
            "experience_level": learner_profile.get("experience_level", "intermediate"),
            "attention_span": learner_profile.get("attention_span", "moderate"),
            "visual_preference": learner_profile.get("visual_preference", "high"),
            "complexity_tolerance": learner_profile.get("complexity_tolerance", "moderate"),
            "learning_style": learner_profile.get("learning_style", "mixed"),
            "previous_exposure": learner_profile.get("previous_exposure", []),
            "preferred_depth": learner_profile.get("preferred_depth", "balanced")
        }

        # Calculate cognitive capacity parameters
        if analysis["experience_level"] == "beginner":
            analysis["cognitive_capacity"] = "lower"
            analysis["need_for_scaffolding"] = "high"
        elif analysis["experience_level"] == "advanced":
            analysis["cognitive_capacity"] = "higher"
            analysis["need_for_scaffolding"] = "low"
        else:
            analysis["cognitive_capacity"] = "moderate"
            analysis["need_for_scaffolding"] = "moderate"

        return analysis

    def _determine_cognitive_load_level(
        self,
        requested_level: Optional[str],
        learner_analysis: Dict[str, Any],
        topic: str
    ) -> CognitiveLoadLevel:
        """Determine optimal cognitive load level based on learner and topic"""
        if requested_level:
            try:
                return CognitiveLoadLevel(requested_level.lower())
            except ValueError:
                pass

        # Adaptive determination based on learner profile
        experience = learner_analysis.get("experience_level", "intermediate")
        tolerance = learner_analysis.get("complexity_tolerance", "moderate")

        if experience == "beginner" or tolerance == "low":
            return CognitiveLoadLevel.MINIMAL
        elif experience == "advanced" and tolerance == "high":
            return CognitiveLoadLevel.EXPERT
        elif tolerance == "high":
            return CognitiveLoadLevel.COMPLEX
        else:
            return CognitiveLoadLevel.MODERATE

    def _determine_knowledge_type(self, knowledge_type: Optional[str], topic: str) -> KnowledgeType:
        """Determine the primary knowledge type for the mindmap"""
        if knowledge_type:
            try:
                return KnowledgeType(knowledge_type.lower())
            except ValueError:
                pass

        # Analyze topic to infer knowledge type
        topic_lower = topic.lower()

        # Keyword-based classification
        factual_keywords = ["definizioni", "termini", "concetti base", "introduzione"]
        conceptual_keywords = ["relazioni", "principi", "teorie", "modelli"]
        procedural_keywords = ["processi", "metodi", "procedure", "come fare"]
        metacognitive_keywords = ["strategie", "apprendimento", "studio", "riflessione"]

        if any(keyword in topic_lower for keyword in factual_keywords):
            return KnowledgeType.FACTUAL
        elif any(keyword in topic_lower for keyword in procedural_keywords):
            return KnowledgeType.PROCEDURAL
        elif any(keyword in topic_lower for keyword in metacognitive_keywords):
            return KnowledgeType.METACOGNITIVE
        else:
            return KnowledgeType.CONCEPTUAL  # Default assumption

    async def _extract_concepts_with_glm46(
        self,
        topic: str,
        context_text: str,
        cognitive_load: CognitiveLoadLevel,
        knowledge_type: KnowledgeType
    ) -> Dict[str, Any]:
        """Use GLM-4.6 for advanced concept extraction and relationship modeling"""

        # Select optimal model for concept analysis
        model_decision = await self.model_selector.select_model(
            task_type="concept_analysis",
            complexity="high",
            requires_reasoning=True,
            educational_context=True
        )

        # Create concept extraction prompt
        extraction_prompt = self._create_concept_extraction_prompt(
            topic, context_text, cognitive_load, knowledge_type
        )

        try:
            # Use selected model (prefer GLM-4.6 for complex reasoning)
            if "glm-4.6" in model_decision.model.lower() or model_decision.provider == "z.ai":
                response = await self._call_glm46_model(extraction_prompt, context_text)
            else:
                response = await self.llm_service.generate_response(
                    query=extraction_prompt,
                    context={"text": context_text, "topic": topic}
                )

            # Parse and structure the concepts
            concepts = self._parse_concepts_response(response)

            # Validate and optimize concept set
            optimized_concepts = self._optimize_concept_set(
                concepts, cognitive_load, knowledge_type
            )

            return optimized_concepts

        except Exception as e:
            logger.error(f"GLM-4.6 concept extraction failed: {e}")
            # Fallback to simpler extraction
            return self._fallback_concept_extraction(topic, context_text, cognitive_load)

    def _create_concept_extraction_prompt(
        self,
        topic: str,
        context_text: str,
        cognitive_load: CognitiveLoadLevel,
        knowledge_type: KnowledgeType
    ) -> str:
        """Create prompt for GLM-4.6 concept extraction and relationship modeling"""

        max_concepts = self.max_concepts_per_level[cognitive_load][1]
        max_branches = self.max_branches_per_node[cognitive_load]

        return f"""
You are GLM-4.6, an advanced AI with exceptional reasoning capabilities for educational content analysis.

TASK: Extract and model concepts from educational materials for optimal mindmap generation.

TOPIC: {topic}
KNOWLEDGE TYPE: {knowledge_type.value}
COGNITIVE LOAD TARGET: {cognitive_load.value} (max {max_concepts} concepts, max {max_branches} branches per node)

ANALYSIS REQUIREMENTS:
1. **Concept Identification**: Extract the most important concepts from the context
2. **Relationship Modeling**: Identify meaningful relationships between concepts
3. **Hierarchical Organization**: Determine parent-child relationships
4. **Cognitive Optimization**: Ensure concept count fits cognitive load level
5. **Educational Value**: Prioritize concepts with high learning impact

RELATIONSHIP TYPES TO IDENTIFY:
- HIERARCHICAL: part-of, type-of, category relationships
- CAUSAL: cause-effect, leads-to relationships
- COMPARATIVE: similar-to, different-from relationships
- TEMPORAL: before-after, sequence relationships
- ASSOCIATIVE: related-to, context relationships

CONTEXT MATERIALS:
{context_text}

OUTPUT FORMAT (JSON ONLY):
{{
  "core_concepts": [
    {{
      "id": "concept_id",
      "title": "Concept Title",
      "definition": "Clear, concise definition",
      "importance_score": 0.8,
      "complexity_level": "basic|intermediate|advanced",
      "knowledge_type": "{knowledge_type.value}"
    }}
  ],
  "relationships": [
    {{
      "source": "concept_id_1",
      "target": "concept_id_2",
      "type": "hierarchical|causal|comparative|temporal|associative",
      "strength": 0.9,
      "description": "Brief description of relationship"
    }}
  ],
  "hierarchy": {{
    "root_concept": "main_concept_id",
    "primary_branches": ["concept_id_1", "concept_id_2"],
    "organization_rationale": "Why this structure works best for learning"
  }}
}}

CRITICAL CONSTRAINTS:
- Maximum {max_concepts} total concepts
- Maximum {max_branches} branches per node
- Focus on pedagogical value over completeness
- Ensure logical coherence and flow
- Optimize for cognitive load management

Analyze the context and extract the optimal concept structure.
"""

    async def _call_glm46_model(self, prompt: str, context: str) -> str:
        """Call GLM-4.6 model through the appropriate service"""
        try:
            # This would integrate with the GLM-4.6 API through Z.AI
            # For now, use the enhanced LLM service with model selection
            response = await self.llm_service.generate_response(
                query=prompt,
                context={"text": context, "model_preference": "glm-4.6"}
            )
            return response
        except Exception as e:
            logger.error(f"GLM-4.6 model call failed: {e}")
            raise

    def _parse_concepts_response(self, response: str) -> Dict[str, Any]:
        """Parse GLM-4.6 concept extraction response"""
        try:
            # Try to extract JSON from response
            if isinstance(response, dict):
                return response

            # Try to parse JSON string
            if isinstance(response, str):
                # Look for JSON in the response
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1

                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx]
                    return json.loads(json_str)

            # If no valid JSON found, create fallback structure
            logger.warning("Could not parse concepts response as JSON")
            return {"core_concepts": [], "relationships": [], "hierarchy": {}}

        except Exception as e:
            logger.error(f"Failed to parse concepts response: {e}")
            return {"core_concepts": [], "relationships": [], "hierarchy": {}}

    def _optimize_concept_set(
        self,
        concepts: Dict[str, Any],
        cognitive_load: CognitiveLoadLevel,
        knowledge_type: KnowledgeType
    ) -> Dict[str, Any]:
        """Optimize concept set based on cognitive load theory"""

        core_concepts = concepts.get("core_concepts", [])
        relationships = concepts.get("relationships", [])
        hierarchy = concepts.get("hierarchy", {})

        # Filter concepts based on importance and cognitive load
        max_main_concepts, max_total_concepts = self.max_concepts_per_level[cognitive_load]

        # Sort by importance score
        sorted_concepts = sorted(
            core_concepts,
            key=lambda x: x.get("importance_score", 0),
            reverse=True
        )

        # Limit concepts based on cognitive load
        selected_concepts = sorted_concepts[:max_total_concepts]

        # Filter relationships to only include selected concepts
        selected_ids = {c["id"] for c in selected_concepts}
        filtered_relationships = [
            r for r in relationships
            if r.get("source") in selected_ids and r.get("target") in selected_ids
        ]

        # Optimize hierarchy
        if hierarchy.get("root_concept") not in selected_ids:
            # Find new root from most important concept
            if selected_concepts:
                hierarchy["root_concept"] = selected_concepts[0]["id"]

        # Update primary branches to include only selected concepts
        hierarchy["primary_branches"] = [
            branch_id for branch_id in hierarchy.get("primary_branches", [])
            if branch_id in selected_ids
        ]

        return {
            "core_concepts": selected_concepts,
            "relationships": filtered_relationships,
            "hierarchy": hierarchy,
            "optimization_applied": {
                "original_count": len(core_concepts),
                "optimized_count": len(selected_concepts),
                "cognitive_load_level": cognitive_load.value,
                "relationships_filtered": len(relationships) - len(filtered_relationships)
            }
        }

    def _build_cognitively_optimized_structure(
        self,
        concepts_analysis: Dict[str, Any],
        cognitive_load: CognitiveLoadLevel,
        knowledge_type: KnowledgeType
    ) -> Dict[str, Any]:
        """Build cognitively optimized mindmap structure"""

        core_concepts = concepts_analysis.get("core_concepts", [])
        relationships = concepts_analysis.get("relationships", [])
        hierarchy = concepts_analysis.get("hierarchy", {})

        # Build hierarchical node structure
        nodes = []
        concept_map = {c["id"]: c for c in core_concepts}

        # Create root node
        root_id = hierarchy.get("root_concept")
        if root_id and root_id in concept_map:
            root_concept = concept_map[root_id]
            root_node = self._create_node_structure(
                root_concept, 0, cognitive_load, knowledge_type, is_root=True
            )
            nodes.append(root_node)

        # Create hierarchical structure for other concepts
        primary_branches = hierarchy.get("primary_branches", [])
        for branch_id in primary_branches:
            if branch_id in concept_map and branch_id != root_id:
                branch_concept = concept_map[branch_id]
                branch_node = self._create_node_structure(
                    branch_concept, 1, cognitive_load, knowledge_type
                )

                # Add child concepts
                children = self._find_child_concepts(
                    branch_id, relationships, concept_map, cognitive_load
                )
                branch_node["children"] = children

                nodes.append(branch_node)

        # Add remaining concepts not in primary branches
        processed_ids = {root_id} if root_id else set()
        processed_ids.update(primary_branches)

        remaining_concepts = [
            c for c in core_concepts
            if c["id"] not in processed_ids
        ]

        # Group remaining concepts appropriately
        for concept in remaining_concepts[:3]:  # Limit to prevent overcrowding
            node = self._create_node_structure(
                concept, 1, cognitive_load, knowledge_type
            )
            nodes.append(node)

        return {
            "title": f"Mappa Concettuale: {concept_map[root_id]['title'] if root_id and root_id in concept_map else 'Argomento'}",
            "overview": f"Mappa concettuale ottimizzata per apprendimento efficaci con {len(nodes)} concetti principali",
            "nodes": nodes,
            "relationships": self._enhance_relationships(relationships, concept_map),
            "cognitive_optimizations": {
                "max_branches_per_node": self.max_branches_per_node[cognitive_load],
                "total_concepts": len(core_concepts),
                "cognitive_load_level": cognitive_load.value,
                "knowledge_type": knowledge_type.value
            }
        }

    def _create_node_structure(
        self,
        concept: Dict[str, Any],
        level: int,
        cognitive_load: CognitiveLoadLevel,
        knowledge_type: KnowledgeType,
        is_root: bool = False
    ) -> Dict[str, Any]:
        """Create optimized node structure"""

        max_children = self.max_branches_per_node[cognitive_load] - level

        node = {
            "id": concept["id"],
            "title": concept["title"],
            "summary": concept.get("definition", ""),
            "level": level,
            "importance": concept.get("importance_score", 0.5),
            "complexity": concept.get("complexity_level", "intermediate"),
            "ai_hint": self._generate_ai_hint(concept, knowledge_type),
            "study_actions": self._generate_study_actions(concept, knowledge_type),
            "priority": 1 if is_root else (2 if level == 1 else 3),
            "max_children": max_children,
            "children": [],
            "visual_style": self._determine_visual_style(level, cognitive_load, is_root)
        }

        return node

    def _generate_ai_hint(self, concept: Dict[str, Any], knowledge_type: KnowledgeType) -> str:
        """Generate AI interaction hints for the concept"""

        hints_by_type = {
            KnowledgeType.FACTUAL: "Chiedimi di definire questo concetto e fornire esempi concreti",
            KnowledgeType.CONCEPTUAL: "Chiedimi di spiegare le relazioni tra questo concetto e altri argomenti",
            KnowledgeType.PROCEDURAL: "Chiedimi di dimostrare passo dopo passo come applicare questo processo",
            KnowledgeType.METACOGNITIVE: "Chiedimi di riflettere su come questo approccio migliora il mio apprendimento"
        }

        base_hint = hints_by_type.get(knowledge_type, "Chiedimi di approfondire questo concetto")

        if concept.get("complexity_level") == "advanced":
            return f"{base_hint} con esempi avanzati e applicazioni complesse"
        elif concept.get("complexity_level") == "basic":
            return f"{base_hint} partendo da spiegazioni semplici e chiare"

        return base_hint

    def _generate_study_actions(self, concept: Dict[str, Any], knowledge_type: KnowledgeType) -> List[str]:
        """Generate specific study actions for the concept"""

        actions_by_type = {
            KnowledgeType.FACTUAL: [
                "Memorizza la definizione usando tecniche di ripetizione spaziata",
                "Crea flashcard con termine e definizione",
                "Trova esempi reali che illustrano il concetto"
            ],
            KnowledgeType.CONCEPTUAL: [
                "Spiega il concetto con parole tue",
                "Crea una analogia per semplificare il concetto",
                "Compara con concetti simili per trovare differenze"
            ],
            KnowledgeType.PROCEDURAL: [
                "Pratica il procedimento passo dopo passo",
                "Applica il processo a un caso reale",
                "Insegna il procedimento a qualcun altro"
            ],
            KnowledgeType.METACOGNITIVE: [
                "Rifletti su quando usare questa strategia",
                "Valuta l'efficacia di questo approccio",
                "Pianifica come integrare questo nelle tue abitudini di studio"
            ]
        }

        return actions_by_type.get(knowledge_type, [
            "Studia il concetto attentamente",
            "Applica quanto appreso",
            "Verifica la comprensione"
        ])

    def _determine_visual_style(
        self,
        level: int,
        cognitive_load: CognitiveLoadLevel,
        is_root: bool
    ) -> Dict[str, Any]:
        """Determine visual styling for the node"""

        if is_root:
            return {
                "size": "large",
                "color": "#2563eb",
                "border_width": 3,
                "font_weight": "bold"
            }
        elif level == 1:
            return {
                "size": "medium",
                "color": "#7c3aed",
                "border_width": 2,
                "font_weight": "semibold"
            }
        else:
            return {
                "size": "small",
                "color": "#64748b",
                "border_width": 1,
                "font_weight": "normal"
            }

    def _find_child_concepts(
        self,
        parent_id: str,
        relationships: List[Dict[str, Any]],
        concept_map: Dict[str, str],
        cognitive_load: CognitiveLoadLevel
    ) -> List[Dict[str, Any]]:
        """Find child concepts for a parent based on relationships"""

        max_children = self.max_branches_per_node[cognitive_load]
        children = []

        # Find hierarchical relationships where this is the parent
        child_relationships = [
            r for r in relationships
            if r.get("source") == parent_id and r.get("type") == "hierarchical"
        ]

        # Sort by relationship strength
        child_relationships.sort(key=lambda x: x.get("strength", 0), reverse=True)

        # Create child nodes
        for rel in child_relationships[:max_children]:
            child_id = rel.get("target")
            if child_id in concept_map:
                child_concept = concept_map[child_id]
                child_node = self._create_node_structure(
                    child_concept, 2, cognitive_load, KnowledgeType.CONCEPTUAL
                )
                children.append(child_node)

        return children

    def _enhance_relationships(
        self,
        relationships: List[Dict[str, Any]],
        concept_map: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Enhance relationships with additional metadata"""

        enhanced = []
        for rel in relationships:
            source_id = rel.get("source")
            target_id = rel.get("target")

            if source_id in concept_map and target_id in concept_map:
                enhanced_rel = {
                    "source": source_id,
                    "target": target_id,
                    "source_title": concept_map[source_id]["title"],
                    "target_title": concept_map[target_id]["title"],
                    "type": rel.get("type", "associative"),
                    "strength": rel.get("strength", 0.5),
                    "description": rel.get("description", ""),
                    "visual_cue": self._get_visual_cue(rel.get("type"))
                }
                enhanced.append(enhanced_rel)

        return enhanced

    def _get_visual_cue(self, relationship_type: str) -> Dict[str, str]:
        """Get visual cues for relationship types"""

        cues = {
            "hierarchical": {"color": "#2563eb", "style": "solid", "arrow": "true"},
            "causal": {"color": "#dc2626", "style": "solid", "arrow": "true"},
            "comparative": {"color": "#16a34a", "style": "dashed", "arrow": "false"},
            "temporal": {"color": "#9333ea", "style": "solid", "arrow": "true"},
            "associative": {"color": "#64748b", "style": "dotted", "arrow": "false"}
        }

        return cues.get(relationship_type, cues["associative"])

    async def _enhance_with_learning_science(
        self,
        mindmap_structure: Dict[str, Any],
        learner_analysis: Dict[str, Any],
        knowledge_type: KnowledgeType
    ) -> Dict[str, Any]:
        """Enhance mindmap with learning science principles"""

        # Add cognitive load optimizations
        optimizations = mindmap_structure.get("cognitive_optimizations", {})

        # Add dual coding elements
        nodes = mindmap_structure.get("nodes", [])
        for node in nodes:
            node["dual_coding"] = {
                "visual_suggestion": self._suggest_visual_element(node, knowledge_type),
                "verbal_anchor": node.get("summary", ""),
                "interaction_type": "visual+text"
            }

            # Add scaffolding hints based on learner profile
            scaffolding_level = learner_analysis.get("need_for_scaffolding", "moderate")
            node["scaffolding"] = self._generate_scaffolding(node, scaffolding_level)

        # Add metacognitive prompts
        mindmap_structure["metacognitive_prompts"] = self._generate_metacognitive_prompts(
            knowledge_type, learner_analysis
        )

        # Add retrieval practice suggestions
        mindmap_structure["retrieval_practice"] = self._generate_retrieval_practice_suggestions(
            nodes, knowledge_type
        )

        # Update optimizations
        optimizations.update({
            "dual_coding_applied": True,
            "scaffolding_included": True,
            "metacognitive_prompts": True,
            "retrieval_practice": True
        })

        mindmap_structure["optimizations"] = optimizations

        return mindmap_structure

    def _suggest_visual_element(self, node: Dict[str, Any], knowledge_type: KnowledgeType) -> str:
        """Suggest visual elements for dual coding"""

        suggestions_by_type = {
            KnowledgeType.FACTUAL: "Icona simbolica o immagine rappresentativa del concetto",
            KnowledgeType.CONCEPTUAL: "Diagramma relazionale o mappa visuale semplificata",
            KnowledgeType.PROCEDURAL: "Flussogramma o sequenza visuale dei passaggi",
            KnowledgeType.METACOGNITIVE: "Infografica strategica o schema riflessivo"
        }

        return suggestions_by_type.get(knowledge_type, "Elemento visivo rappresentativo")

    def _generate_scaffolding(self, node: Dict[str, Any], scaffolding_level: str) -> Dict[str, Any]:
        """Generate scaffolding support based on learner needs"""

        if scaffolding_level == "high":
            return {
                "prerequisites": f"Concetti necessari per capire {node['title']}",
                "step_by_step": "Approccio graduale con esempi progressivi",
                "support_questions": ["Qual è l'idea principale?", "Come si collega a ciò che già conosci?"]
            }
        elif scaffolding_level == "low":
            return {
                "challenge_questions": [f"Come puoi applicare {node['title']} in contesti nuovi?"],
                "extension_tasks": ["Esplora implicazioni più profonde di questo concetto"]
            }
        else:
            return {
                "review_points": ["Riepiloga i punti chiave", "Verifica la comprensione"],
                "practice_suggestions": ["Applica con esempi personali", "Confronta con concetti simili"]
            }

    def _generate_metacognitive_prompts(
        self,
        knowledge_type: KnowledgeType,
        learner_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate metacognitive prompts for reflection"""

        base_prompts = {
            KnowledgeType.FACTUAL: [
                "Come posso ricordare meglio questa informazione?",
                "Quali strategie di memorizzazione funzionano meglio per me?"
            ],
            KnowledgeType.CONCEPTUAL: [
                "Ho davvero capito le relazioni tra questi concetti?",
                "Come posso spiegare questa idea con parole mie?"
            ],
            KnowledgeType.PROCEDURAL: [
                "Quali parti del processo sono più difficili per me?",
                "Come posso migliorare la mia esecuzione?"
            ],
            KnowledgeType.METACOGNITIVE: [
                "Questo approccio funziona per il mio stile di apprendimento?",
                "Quando e come dovrei usare questa strategia?"
            ]
        }

        return base_prompts.get(knowledge_type, [
            "Come sto imparando questo argomento?",
            "Cosa posso fare per migliorare la mia comprensione?"
        ])

    def _generate_retrieval_practice_suggestions(
        self,
        nodes: List[Dict[str, Any]],
        knowledge_type: KnowledgeType
    ) -> Dict[str, Any]:
        """Generate retrieval practice suggestions"""

        practice_types = {
            KnowledgeType.FACTUAL: {
                "method": "flashcard_recall",
                "description": "Usa flashcard per testare la memorizzazione di definizioni e termini",
                "frequency": "giornaliero per la prima settimana, poi a intervalli crescenti"
            },
            KnowledgeType.CONCEPTUAL: {
                "method": "free_recall",
                "description": "Scrivi tutto ciò che ricordi sui concetti e le loro relazioni",
                "frequency": "alternando studio e recupero ogni 30 minuti"
            },
            KnowledgeType.PROCEDURAL: {
                "method": "practice_demonstration",
                "description": "Pratica il procedimento senza guardare le istruzioni",
                "frequency": "immediato ripasso dopo l'apprendimento, poi dopo 24 ore"
            },
            KnowledgeType.METACOGNITIVE: {
                "method": "reflective_journalling",
                "description": "Scrivi riflessioni su come applichi le strategie di apprendimento",
                "frequency": "settimanale per monitorare i progressi"
            }
        }

        return {
            "primary_method": practice_types.get(knowledge_type, practice_types[KnowledgeType.CONCEPTUAL]),
            "key_concepts": [node["title"] for node in nodes[:5]],  # Focus on main concepts
            "schedule_recommendations": "Pratica attiva subito dopo lo studio, poi a 1 giorno, 3 giorni, 1 settimana"
        }

    async def _generate_study_guidance(
        self,
        mindmap: Dict[str, Any],
        learner_analysis: Dict[str, Any],
        knowledge_type: KnowledgeType
    ) -> Dict[str, Any]:
        """Generate comprehensive study guidance for the mindmap"""

        nodes = mindmap.get("nodes", [])
        cognitive_level = mindmap.get("cognitive_optimizations", {}).get("cognitive_load_level", "moderate")

        # Create phased study plan
        study_phases = [
            {
                "phase": "Esplorazione Iniziale",
                "duration_minutes": 20,
                "objectives": ["Ottenere una visione d'insieme", "Identificare i concetti principali"],
                "activities": [
                    "Esamina la struttura generale della mappa",
                    "Leggi i titoli e i riassunti dei nodi principali",
                    "Fai domande iniziali sui concetti sconosciuti"
                ],
                "ai_interaction": "Chiedi all'AI una panoramica generale dell'argomento"
            },
            {
                "phase": "Studio Approfondito",
                "duration_minutes": 45,
                "objectives": ["Comprendere dettagliatamente i concetti", "Stabilire connessioni"],
                "activities": [
                    "Studia ogni nodo principale con i suoi figli",
                    "Usa gli hint AI per approfondire i concetti difficili",
                    "Completa le azioni di studio suggerite"
                ],
                "ai_interaction": "Chiedi spiegazioni dettagliate ed esempi specifici"
            },
            {
                "phase": "Pratica Attiva",
                "duration_minutes": 30,
                "objectives": ["Testare la comprensione", "Applicare i concetti"],
                "activities": [
                    "Usa le suggestioni di retrieval practice",
                    "Spiega i concetti ad alta voce",
                    "Crea connessioni personali con gli argomenti"
                ],
                "ai_interaction": "Chiedi all'AI di farti domande di verifica"
            },
            {
                "phase": "Consolidamento e Metacognizione",
                "duration_minutes": 15,
                "objectives": ["Riflettere sull'apprendimento", "Pianificare il ripasso"],
                "activities": [
                    "Usa i prompt metacognitivi inclusi",
                    "Identifica aree che necessitano ulteriore studio",
                    "Pianifica sessioni di ripasso future"
                ],
                "ai_interaction": "Discuti con l'AI le strategie di studio più efficaci"
            }
        ]

        # Add personalization based on learner profile
        if learner_analysis.get("attention_span") == "short":
            for phase in study_phases:
                phase["duration_minutes"] = min(phase["duration_minutes"], 25)

        # Generate specific guidance based on knowledge type
        type_specific_guidance = {
            KnowledgeType.FACTUAL: {
                "focus": "Memorizzazione e richiamo preciso",
                "key_strategy": "Ripetizione spaziata e flashcard",
                "assessment_tip": "Testa la capacità di richiamare definizioni esatte"
            },
            KnowledgeType.CONCEPTUAL: {
                "focus": "Comprensione profonda e relazioni",
                "key_strategy": "Elaborazione e analogie",
                "assessment_tip": "Spiega i concetti con parole tue e trova esempi"
            },
            KnowledgeType.PROCEDURAL: {
                "focus": "Esecuzione corretta del processo",
                "key_strategy": "Pratica guidata e progressiva",
                "assessment_tip": "Dimostra il procedimento senza guardare"
            },
            KnowledgeType.METACOGNITIVE: {
                "focus": "Auto-regolazione e strategie",
                "key_strategy": "Riflessione guidata e monitoraggio",
                "assessment_tip": "Valuta l'efficacia delle strategie utilizzate"
            }
        }

        return {
            "study_phases": study_phases,
            "total_study_time": sum(phase["duration_minutes"] for phase in study_phases),
            "knowledge_type_guidance": type_specific_guidance.get(knowledge_type),
            "cognitive_load_considerations": {
                "level": cognitive_level,
                "recommendations": self._get_cognitive_load_recommendations(cognitive_level),
                "break_suggestions": "Pausa di 5 minuti ogni 25 minuti di studio intenso"
            },
            "ai_integration_tips": [
                "Usa gli hint AI solo dopo aver provato a comprendere da solo",
                "Fai domande specifiche invece di richieste generiche",
                "Chiedi esempi personali per collegare i concetti alla tua esperienza"
            ]
        }

    def _get_cognitive_load_recommendations(self, cognitive_level: str) -> List[str]:
        """Get recommendations based on cognitive load level"""

        recommendations = {
            "minimal": [
                "Concentrati sui concetti più importanti prima di espandere",
                "Fai pause frequenti per consolidare le informazioni",
                "Usa esempi molto semplici e concreti"
            ],
            "moderate": [
                "Procedi gradualmente da un concetto all'altro",
                "Verifica la comprensione prima di passare ad argomenti complessi",
                "Usa analogie per collegare concetti difficili"
            ],
            "complex": [
                "Suddividi i concetti complessi in parti più piccole",
                "Crea riassunti intermedi durante lo studio",
                "Usa mappe visive per organizzare le relazioni"
            ],
            "expert": [
                "Esplora le interconnessioni tra i concetti",
                "Cerca applicazioni avanzate e contesti diversi",
                "Sfida te stesso con problemi complessi"
            ]
        }

        return recommendations.get(cognitive_level, recommendations["moderate"])

    async def _track_generation_analytics(
        self,
        topic: str,
        cognitive_load: CognitiveLoadLevel,
        knowledge_type: KnowledgeType,
        result: Dict[str, Any],
        duration: float
    ) -> None:
        """Track analytics for enhanced mindmap generation"""

        try:
            analytics_data = {
                "prompt_type": "enhanced_mindmap_generation",
                "model_used": "GLM-4.6",
                "strategy": "cognitive_load_optimization",
                "topic_complexity": "advanced" if cognitive_load.value in ["complex", "expert"] else "basic",
                "context": {
                    "topic": topic,
                    "cognitive_load_level": cognitive_load.value,
                    "knowledge_type": knowledge_type.value,
                    "concept_count": len(result.get("nodes", [])),
                    "relationship_count": len(result.get("relationships", [])),
                    "generation_time_seconds": duration,
                    "success": True
                }
            }

            await self.analytics.track_performance(analytics_data)

        except Exception as e:
            logger.error(f"Failed to track enhanced mindmap analytics: {e}")

    async def _generate_fallback_mindmap(
        self,
        topic: str,
        context_text: str,
        course_id: str,
        book_id: str
    ) -> Dict[str, Any]:
        """Generate fallback mindmap if enhanced generation fails"""

        return {
            "id": f"fallback_mindmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": f"Mappa Concettuale: {topic}",
            "overview": "Mappa concettuale di base generata con metodo alternativo",
            "nodes": [
                {
                    "id": "root",
                    "title": topic,
                    "summary": "Concetto principale dell'argomento",
                    "ai_hint": "Chiedimi di spiegare questo argomento in dettaglio",
                    "study_actions": ["Studia i materiali disponibili", "Crea riassunti personali"],
                    "priority": 1,
                    "level": 0,
                    "children": []
                }
            ],
            "relationships": [],
            "study_guidance": {
                "study_phases": [
                    {
                        "phase": "Studio Base",
                        "duration_minutes": 30,
                        "objectives": ["Comprendere i concetti fondamentali"],
                        "activities": ["Leggi i materiali", "Crea appunti"],
                        "ai_interaction": "Chiedi chiarimenti sui concetti"
                    }
                ],
                "total_study_time": 30
            },
            "metadata": {
                "course_id": course_id,
                "book_id": book_id,
                "generation_method": "fallback",
                "created_at": datetime.now().isoformat()
            }
        }

    def _fallback_concept_extraction(
        self,
        topic: str,
        context_text: str,
        cognitive_load: CognitiveLoadLevel
    ) -> Dict[str, Any]:
        """Fallback concept extraction using basic text analysis"""

        # Simple keyword extraction for fallback
        words = topic.split()
        core_concepts = []

        for i, word in enumerate(words[:5]):  # Limit to prevent overload
            if len(word) > 3:  # Skip very short words
                core_concepts.append({
                    "id": f"concept_{i}",
                    "title": word.capitalize(),
                    "definition": f"Concetto relativo a {word}",
                    "importance_score": 0.8 - (i * 0.1),
                    "complexity_level": "basic",
                    "knowledge_type": "conceptual"
                })

        return {
            "core_concepts": core_concepts,
            "relationships": [],
            "hierarchy": {"root_concept": core_concepts[0]["id"] if core_concepts else "root"}
        }

    def _enhance_learner_analysis_with_session_context(
        self,
        learner_analysis: Dict[str, Any],
        session_context: StudySessionContext
    ) -> Dict[str, Any]:
        """Enhance learner analysis with session-specific data"""

        enhanced_analysis = learner_analysis.copy()

        # Adjust experience level based on recent performance
        if session_context.quiz_performance:
            avg_performance = sum(session_context.quiz_performance.values()) / len(session_context.quiz_performance)
            if avg_performance > 0.8:
                enhanced_analysis["experience_level"] = "advanced"
            elif avg_performance > 0.6:
                enhanced_analysis["experience_level"] = "intermediate"
            else:
                enhanced_analysis["experience_level"] = "beginner"

        # Adjust attention span based on study time today
        if session_context.study_time_today > 120:  # More than 2 hours
            enhanced_analysis["attention_span"] = "short"
        elif session_context.study_time_today < 30:
            enhanced_analysis["attention_span"] = "long"

        # Set complexity tolerance based on weak areas
        if len(session_context.weak_areas) > 3:
            enhanced_analysis["complexity_tolerance"] = "low"
        elif len(session_context.weak_areas) == 0:
            enhanced_analysis["complexity_tolerance"] = "high"

        # Add session-specific goals
        enhanced_analysis["session_goals"] = session_context.goals
        enhanced_analysis["current_focus"] = session_context.recently_studied

        return enhanced_analysis

    def _enhance_context_with_session_data(
        self,
        context_text: str,
        session_context: Optional[StudySessionContext],
        focus_areas: Optional[List[str]]
    ) -> str:
        """Enhance RAG context with session-specific information"""

        if not session_context:
            return context_text

        enhanced_context = context_text

        # Add progress information
        if session_context.current_progress > 0:
            enhanced_context += f"\n\nPROGRESSO CORRENTE: Lo studente ha completato il {session_context.current_progress}% del materiale."

        # Add weak areas for emphasis
        if session_context.weak_areas:
            weak_areas_text = ", ".join(session_context.weak_areas)
            enhanced_context += f"\n\nAREE DI MIGLIORAMENTO: Prestare particolare attenzione a: {weak_areas_text}."

        # Add recent study context
        if session_context.recently_studied:
            recent_text = ", ".join(session_context.recently_studied[-5:])  # Last 5 topics
            enhanced_context += f"\n\nARGOMENTI RECENTI: Già studiato di recente: {recent_text}."

        # Add focus areas
        if focus_areas:
            focus_text = ", ".join(focus_areas)
            enhanced_context += f"\n\nAREE DI FOCUS: Argomenti prioritari: {focus_text}."

        # Add mastery level hints
        if session_context.mastery_levels:
            mastery_text = "; ".join([f"{concept}: {level}" for concept, level in session_context.mastery_levels.items() if level < 0.7])
            if mastery_text:
                enhanced_context += f"\n\nLIVELLI DI MASTERY: Concetti che necessitano attenzione: {mastery_text}."

        return enhanced_context

    def _enhance_structure_with_session_context(
        self,
        mindmap_structure: Dict[str, Any],
        session_context: StudySessionContext,
        concepts_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance mindmap structure with session-specific metadata"""

        enhanced_nodes = []

        for node in mindmap_structure.get("nodes", []):
            enhanced_node = node.copy()

            # Add session metadata
            enhanced_node["session_metadata"] = {
                "priority_adjusted": False,
                "mastery_level": None,
                "recently_studied": False,
                "weak_area": False,
                "recommended_action": None
            }

            # Check if this concept is in weak areas
            node_title_lower = node.get("title", "").lower()
            if any(weak.lower() in node_title_lower for weak in session_context.weak_areas):
                enhanced_node["session_metadata"]["weak_area"] = True
                enhanced_node["session_metadata"]["priority_adjusted"] = True
                # Increase priority for weak areas
                if enhanced_node.get("priority"):
                    enhanced_node["priority"] = max(1, enhanced_node["priority"] - 1)

            # Check if recently studied
            if any(recent.lower() in node_title_lower for recent in session_context.recently_studied):
                enhanced_node["session_metadata"]["recently_studied"] = True

            # Add mastery level if available
            for concept, mastery in session_context.mastery_levels.items():
                if concept.lower() in node_title_lower:
                    enhanced_node["session_metadata"]["mastery_level"] = mastery
                    break

            # Add recommended study actions based on session context
            if enhanced_node["session_metadata"]["weak_area"]:
                enhanced_node["session_metadata"]["recommended_action"] = "focused_review"
            elif enhanced_node["session_metadata"]["recently_studied"]:
                enhanced_node["session_metadata"]["recommended_action"] = "practice_application"
            elif enhanced_node["session_metadata"]["mastery_level"] and enhanced_node["session_metadata"]["mastery_level"] < 0.5:
                enhanced_node["session_metadata"]["recommended_action"] = "foundational_review"
            else:
                enhanced_node["session_metadata"]["recommended_action"] = "normal_study"

            enhanced_nodes.append(enhanced_node)

        mindmap_structure["nodes"] = enhanced_nodes

        # Add session-specific study guidance
        if not mindmap_structure.get("session_guidance"):
            mindmap_structure["session_guidance"] = {}

        mindmap_structure["session_guidance"] = {
            "focus_on_weak_areas": len(session_context.weak_areas) > 0,
            "recommended_study_order": self._generate_session_aware_study_order(
                enhanced_nodes, session_context
            ),
            "estimated_study_time": self._estimate_study_time_for_session(
                enhanced_nodes, session_context
            ),
            "adaptive_suggestions": self._generate_adaptive_suggestions(
                session_context, concepts_analysis
            )
        }

        return mindmap_structure

    def _generate_session_aware_study_order(
        self,
        nodes: List[Dict[str, Any]],
        session_context: StudySessionContext
    ) -> List[str]:
        """Generate optimal study order based on session context"""

        # Prioritize weak areas first
        weak_nodes = [node["id"] for node in nodes if node["session_metadata"]["weak_area"]]

        # Then recently studied concepts (for reinforcement)
        recent_nodes = [node["id"] for node in nodes if node["session_metadata"]["recently_studied"] and node["id"] not in weak_nodes]

        # Then low mastery concepts
        low_mastery_nodes = [
            node["id"] for node in nodes
            if node["session_metadata"]["mastery_level"] and node["session_metadata"]["mastery_level"] < 0.6
            and node["id"] not in weak_nodes + recent_nodes
        ]

        # Finally remaining concepts by original priority
        remaining_nodes = [
            node["id"] for node in nodes
            if node["id"] not in weak_nodes + recent_nodes + low_mastery_nodes
        ]

        return weak_nodes + recent_nodes + low_mastery_nodes + remaining_nodes

    def _estimate_study_time_for_session(
        self,
        nodes: List[Dict[str, Any]],
        session_context: StudySessionContext
    ) -> Dict[str, Any]:
        """Estimate study time based on session context and node complexity"""

        base_time_per_node = 15  # minutes

        total_time = 0
        breakdown = {"weak_areas": 0, "review": 0, "new_concepts": 0}

        for node in nodes:
            node_time = base_time_per_node

            # Adjust time based on session metadata
            if node["session_metadata"]["weak_area"]:
                node_time *= 1.5  # 50% more time for weak areas
                breakdown["weak_areas"] += node_time
            elif node["session_metadata"]["recently_studied"]:
                node_time *= 0.7  # 30% less time for recent concepts
                breakdown["review"] += node_time
            else:
                breakdown["new_concepts"] += node_time

            # Adjust based on mastery level
            mastery = node["session_metadata"]["mastery_level"]
            if mastery and mastery < 0.3:
                node_time *= 1.3  # 30% more time for very low mastery
            elif mastery and mastery > 0.8:
                node_time *= 0.8  # 20% less time for high mastery

            total_time += node_time

        # Adjust based on current fatigue (study time today)
        if session_context.study_time_today > 120:  # More than 2 hours
            total_time *= 0.8  # Reduce estimated time due to fatigue
        elif session_context.study_time_today < 30:  # Less than 30 minutes
            total_time *= 1.1  # Slightly more time for fresh start

        return {
            "total_minutes": int(total_time),
            "breakdown": breakdown,
            "adjusted_for_fatigue": session_context.study_time_today > 120
        }

    def _generate_adaptive_suggestions(
        self,
        session_context: StudySessionContext,
        concepts_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate adaptive suggestions based on session context and concept analysis"""

        suggestions = []

        # Fatigue-based suggestions
        if session_context.study_time_today > 120:
            suggestions.append("Hai già studiato molto oggi. Concentrati su concetti più semplici e ripasso.")
        elif session_context.study_time_today < 30:
            suggestions.append("Sei all'inizio della sessione. Affronta i concetti più difficili quando sei più fresco.")

        # Weak area suggestions
        if len(session_context.weak_areas) > 2:
            suggestions.append("Hai diverse aree di miglioramento. Prioritizza i concetti fondamentali prima di passare a quelli avanzati.")
        elif len(session_context.weak_areas) == 1:
            suggestions.append(f"Concentrati specificamente su: {session_context.weak_areas[0]}")

        # Progress-based suggestions
        if session_context.current_progress > 80:
            suggestions.append("Sei quasi alla fine del materiale. Concentrati sul consolidare e integrare i concetti.")
        elif session_context.current_progress < 20:
            suggestions.append("Sei all'inizio del percorso. Dedica tempo a costruire basi solide.")

        # Performance-based suggestions
        if session_context.quiz_performance:
            avg_performance = sum(session_context.quiz_performance.values()) / len(session_context.quiz_performance)
            if avg_performance > 0.8:
                suggestions.append("Le tue performance sono eccellenti. Puoi affrontare sfide più complesse.")
            elif avg_performance < 0.5:
                suggestions.append("Concentrati sulla comprensione di base prima di passare ad applicazioni complesse.")

        # Goal-based suggestions
        if session_context.goals:
            suggestions.append(f"Ricorda i tuoi obiettivi: {', '.join(session_context.goals[:2])}")

        return suggestions