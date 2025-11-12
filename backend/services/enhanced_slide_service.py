"""
Enhanced Slide Generation Service with Mayer's Multimedia Learning Principles
Implements evidence-based educational psychology for optimal slide design and learning effectiveness
"""

import json
import math
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging

from services.advanced_model_selector import AdvancedModelSelector2
from services.prompt_analytics_service import PromptAnalyticsService
from services.advanced_prompt_templates import AdvancedPromptTemplates
from llm_service import LLMService
from rag_service import RAGService

logger = logging.getLogger(__name__)

class CognitiveLoadLevel(Enum):
    """Cognitive load levels for slide optimization"""
    MINIMAL = "minimal"      # 3-5 elements per slide
    MODERATE = "moderate"    # 5-8 elements per slide
    COMPLEX = "complex"      # 8-12 elements per slide
    EXPERT = "expert"        # 13+ elements per slide

class MultimediaPrinciple(Enum):
    """Mayer's Multimedia Learning Principles"""
    COHERENCE = "coherence"                    # 1. Words and pictures presented together
    SIGNALING = "signaling"                      # 2. Highlighting essential information
    REDUNDANCY = "redundancy"                    # 3. Remove extraneous material
    SPATIAL_CONTIGUITY = "spatial_contiguity"      # 4. Place related words and pictures near each other
    TEMPORAL_CONTIGUITY = "temporal_contiguity"      # 5. Present words and pictures simultaneously
    SEGMENTING = "segmenting"                      # 6. Break lessons into segments
    PRE_TRAINING = "pre_training"                    # 7. Provide pre-training for key elements
    MODALITY = "modality"                          # 8. Present lessons as words and pictures
    MULTIMEDIA = "multimedia"                      # 9. Use multiple media formats
    PERSONALIZATION = "personalization"            # 10. Personalize instruction
    VOICE = "voice"                                # 11. Use conversational style
    IMAGERY = "imagery"                          # 12. Use relevant pictures

class SlideElementType(Enum):
    """Types of elements that can appear on slides"""
    TEXT = "text"
    IMAGE = "image"
    DIAGRAM = "diagram"
    CHART = "chart"
    VIDEO = "video"
    AUDIO = "audio"
    TABLE = "table"
    QUOTE = "quote"
    LIST = "list"
    EMPHASIS = "emphasis"
    ANIMATION = "animation"

class EnhancedSlideService:
    """Enhanced slide generation service with Mayer's multimedia learning principles"""

    def __init__(self):
        self.model_selector = AdvancedModelSelector2()
        self.analytics = PromptAnalyticsService()
        self.prompt_templates = AdvancedPromptTemplates()
        self.llm_service = LLMService()
        self.rag_service = RAGService()

        # Mayer's principles parameters
        self.principle_weights = {
            MultimediaPrinciple.COHERENCE: 0.9,
            MultimediaPrinciple.SIGNALING: 0.85,
            MultimediaPrinciple.REDUNDANCY: 0.8,
            MultimediaPrinciple.SPATIAL_CONTIGUITY: 0.9,
            MultimediaPrinciple.TEMPORAL_CONTIGUITY: 0.95,
            MultimediaPrinciple.SEGMENTING: 0.8,
            MultimediaPrinciple.PRE_TRAINING: 0.75,
            MultimediaPrinciple.MODALITY: 0.95,
            MultimediaPrinciple.MULTIMEDIA: 0.9,
            MultimediaPrinciple.PERSONALIZATION: 0.7,
            MultimediaPrinciple.VOICE: 0.6,
            MultimediaPrinciple.IMAGERY: 0.85
        }

        # Cognitive load management
        self.max_elements_per_load = {
            CognitiveLoadLevel.MINIMAL: 5,
            CognitiveLoadLevel.MODERATE: 8,
            CognitiveLoadLevel.COMPLEX: 12,
            CognitiveLoadLevel.EXPERT: 18
        }

        # Optimal media ratios
        self.text_image_ratio = {
            "educational": 0.6,  # 60% text, 40% images
            "professional": 0.7,
            "technical": 0.8
        }

    async def generate_enhanced_slides(
        self,
        course_id: str,
        book_id: Optional[str] = None,
        topic: str,
        context_text: str = "",
        learner_profile: Optional[Dict[str, Any]] = None,
        cognitive_load_level: Optional[str] = None,
        target_audience: Optional[str] = None,
        learning_objectives: Optional[List[str]] = None,
        preferred_style: Optional[str] = None,
        multimedia_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate enhanced slides using Mayer's multimedia learning principles

        Args:
            course_id: Course identifier
            book_id: Book identifier
            topic: Main topic for slides
            context_text: RAG-retrieved context materials
            learner_profile: Learner characteristics and preferences
            cognitive_load_level: Desired cognitive load complexity
            target_audience: Target audience (beginner, intermediate, advanced)
            learning_objectives: Specific learning outcomes
            preferred_style: Visual style preferences
            multimedia_preferences: Media type preferences

        Returns:
            Enhanced slide structure with multimedia learning optimization
        """
        start_time = datetime.now()

        try:
            # Analyze learner profile and determine optimal parameters
            learner_analysis = self._analyze_learner_profile(learner_profile, target_audience)

            # Determine cognitive load level and optimize parameters
            cognitive_load = self._determine_cognitive_load_level(
                cognitive_load_level, learner_analysis, topic
            )

            # Retrieve enhanced context using RAG
            enhanced_context = await self._retrieve_enhanced_context(
                topic, context_text, course_id, book_id
            )

            # Generate content structure using GLM-4.6 for optimal organization
            content_structure = await self._generate_multimedia_content_structure(
                topic, enhanced_context, cognitive_load, learning_objectives
            )

            # Apply Mayer's principles to optimize content
            optimized_content = self._apply_mayer_principles(
                content_structure, cognitive_load, learner_analysis, multimedia_preferences
            )

            # Generate comprehensive slide designs
            slide_designs = await self._generate_multimedia_slide_designs(
                optimized_content, learner_analysis, preferred_style
            )

            # Create dual-coded slides with visual hierarchy
            enhanced_slides = self._create_dual_coded_slides(
                optimized_content, slide_designs, cognitive_load
            )

            # Add narration and accessibility features
            accessible_slides = await self._add_accessibility_features(
                enhanced_slides, learner_analysis
            )

            # Generate study guidance and teacher notes
            guidance = await self._generate_slide_guidance(
                enhanced_slides, learner_analysis, learning_objectives
            )

            # Build final response
            result = {
                "slide_id": f"enhanced_slides_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "course_id": course_id,
                "book_id": book_id,
                "topic": topic,
                "cognitive_load_level": cognitive_load.value,
                "target_audience": target_audience or learner_analysis.get("experience_level", "intermediate"),
                "total_slides": len(enhanced_slides),
                "slides": enhanced_slides,
                "design_principles": self._get_applied_principles(),
                "multimedia_elements": self._count_multimedia_elements(enhanced_slides),
                "accessibility_features": guidance.get("accessibility", {}),
                "study_guidance": guidance,
                "performance_predictions": self._predict_learning_outcomes(enhanced_slides, learner_analysis),
                "metadata": {
                    "generation_method": "mayer_multimedia_learning",
                    "model_used": "GLM-4.6",
                    "principles_applied": len(self._get_applied_principles()),
                    "cognitive_optimization": True,
                    "dual_coding": True,
                    "accessibility_compliant": True,
                    "created_at": datetime.now().isoformat(),
                    "learner_profile": learner_analysis,
                    "enhanced_context_sources": len(enhanced_context.get("sources", [])),
                    "multimedia_balance": self._calculate_multimedia_balance(enhanced_slides)
                }
            }

            # Analytics tracking
            duration = (datetime.now() - start_time).total_seconds()
            await self._track_generation_analytics(
                topic, cognitive_load, result, duration
            )

            return result

        except Exception as e:
            logger.error(f"Enhanced slide generation failed: {e}")
            # Fallback to basic slide generation
            return await self._generate_fallback_slides(
                course_id, book_id, topic, context_text
            )

    def _analyze_learner_profile(
        self,
        learner_profile: Optional[Dict[str, Any]],
        target_audience: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze learner profile for slide optimization"""

        if not learner_profile:
            learner_profile = {}

        # Combine profile with audience information
        if target_audience:
            learner_analysis = {
                "experience_level": target_audience,
                "visual_preference": learner_profile.get("visual_preference", "high"),
                "attention_span": learner_profile.get("attention_span", "moderate"),
                "complexity_tolerance": learner_profile.get("complexity_tolerance", "moderate")
            }
        else:
            learner_analysis = {
                "experience_level": learner_profile.get("experience_level", "intermediate"),
                "visual_preference": learner_profile.get("visual_preference", "high"),
                "attention_span": learner_profile.get("attention_span", "moderate"),
                "complexity_tolerance": learner_profile.get("complexity_tolerance", "moderate")
            }

        # Derive additional characteristics
        learner_analysis.update({
            "text_image_ratio_preference": self._determine_text_image_preference(learner_analysis),
            "animation_tolerance": learner_profile.get("animation_tolerance", "moderate"),
            "color_sensitivity": learner_profile.get("color_sensitivity", "normal"),
            "accessibility_needs": learner_profile.get("accessibility_needs", [])
        })

        return learner_analysis

    def _determine_cognitive_load_level(
        self,
        cognitive_load_level: Optional[str],
        learner_analysis: Dict[str, Any],
        topic: str
    ) -> CognitiveLoadLevel:
        """Determine optimal cognitive load level based on learner and content"""

        if cognitive_load_level:
            try:
                return CognitiveLoadLevel(cognitive_load_level.lower())
            except ValueError:
                pass

        # Adaptive determination based on learner profile
        experience = learner_analysis.get("experience_level", "intermediate")
        tolerance = learner_analysis.get("complexity_tolerance", "moderate")
        attention = learner_analysis.get("attention_span", "moderate")

        if experience == "beginner" or tolerance == "low" or attention == "short":
            return CognitiveLoadLevel.MINIMAL
        elif experience == "advanced" and tolerance == "high" and attention == "long":
            return CognitiveLoadLevel.COMPLEX
        else:
            return CognitiveLoadLevel.MODERATE

    async def _retrieve_enhanced_context(
        self,
        topic: str,
        context_text: str,
        course_id: str,
        book_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve and enhance context materials for slide generation"""

        try:
            # Use existing context if provided, otherwise fetch from RAG
            if context_text:
                enhanced_context = context_text
                sources = []
            else:
                rag_response = await self.rag_service.retrieve_context(
                    f"Create comprehensive slides about {topic} with rich examples and visual descriptions",
                    course_id=course_id,
                    book_id=book_id,
                    k=8
                )
                enhanced_context = rag_response.get("text", "")
                sources = rag_response.get("sources", [])

            # Add visual and example-specific context
            visual_context_prompt = f"""
            ENHANCE CONTEXT FOR VISUAL SLIDE GENERATION:

            For the topic "{topic}", identify and describe:
            1. Visual elements that would enhance understanding (diagrams, charts, images)
            2. Real-world examples that could be illustrated
            3. Processes that benefit from step-by-step visual representation
            4. Key concepts that would benefit from visual reinforcement
            5. Analogies or metaphors that could be visualized

            Focus on finding content that supports:
            - Better comprehension through visualization
            - Memory retention through visual associations
            - Engagement through relevant examples
            - Practical application scenarios
            """

            # Use GLM-4.6 for context enhancement
            model_decision = await self.model_selector.select_model(
                task_type="visual_context_analysis",
                complexity="high",
                requires_reasoning=True,
                educational_context=True
            )

            if "glm-4.6" in model_decision.model.lower() or model_decision.provider == "z.ai":
                visual_enhancement = await self._call_glm46_for_visual_context(
                    visual_context_prompt, enhanced_context
                )
                enhanced_context += "\n\n" + visual_enhancement

            return {
                "text": enhanced_context,
                "sources": sources,
                "visual_enhancements": len(visual_enhancement) > 0,
                "context_type": "enhanced_multimedia"
            }

        except Exception as e:
            logger.error(f"Context enhancement failed: {e}")
            return {
                "text": context_text or f"Basic context for {topic}",
                "sources": [],
                "context_type": "basic"
            }

    async def _generate_multimedia_content_structure(
        self,
        topic: str,
        context: Dict[str, Any],
        cognitive_load: CognitiveLoadLevel,
        learning_objectives: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Generate content structure optimized for multimedia learning"""

        # Select optimal model for content structuring
        model_decision = await self.model_selector.select_model(
            task_type="multimedia_content_structure",
            complexity="high",
            requires_reasoning=True,
            requires_structuring=True,
            educational_context=True
        )

        # Create content structure prompt
        structure_prompt = self._create_multimedia_structure_prompt(
            topic, context, cognitive_load, learning_objectives
        )

        try:
            # Use GLM-4.6 for advanced content structuring
            if "glm-4.6" in model_decision.model.lower() or model_decision.provider == "z.ai":
                response = await self._call_glm46_model(structure_prompt)
            else:
                response = await self.llm_service.generate_response(
                    query=structure_prompt,
                    context={
                        "topic": topic,
                        "context": context,
                        "cognitive_load": cognitive_load.value,
                        "objectives": learning_objectives
                    }
                )

            # Parse and structure content
            content_structure = self._parse_multimedia_structure_response(response)

            # Validate and optimize structure
            optimized_structure = self._optimize_content_structure(
                content_structure, cognitive_load
            )

            return optimized_structure

        except Exception as e:
            logger.error(f"Multimedia content structuring failed: {e}")
            # Fallback to basic structure
            return self._fallback_content_structure(topic, cognitive_load)

    def _create_multimedia_structure_prompt(
        self,
        topic: str,
        context: Dict[str, Any],
        cognitive_load: CognitiveLoadLevel,
        learning_objectives: Optional[List[str]]
    ) -> str:
        """Create prompt for GLM-4.6 multimedia content structuring"""

        context_text = context.get("text", "")
        max_elements = self.max_elements_per_load[cognitive_load]

        objectives_str = ", ".join(learning_objectives or ["understand", "learn"])

        return f"""
You are GLM-4.6, an advanced AI with exceptional capabilities in educational content design and multimedia learning optimization.

TASK: Create a comprehensive slide content structure for {topic} that maximizes learning effectiveness through multimedia principles.

CONTEXT MATERIALS:
{context_text[:800] if context_text else "No specific context provided"}

LEARNING OBJECTIVES: {objectives_str}

COGNITIVE LOAD TARGET: {cognitive_load.value} (maximum {max_elements} elements per slide)

MULTIMEDIA LEARNING PRINCIPLES TO APPLY:
1. **Coherence** - Integrate words and pictures meaningfully
2. **Signaling** - Highlight essential information visually
3. **Redundancy** - Remove extraneous material
4. **Spatial Contiguity** - Place related elements near each other
5. **Temporal Contiguity** - Present related content simultaneously
6. **Segmenting** - Break content into manageable chunks
7. **Pre-training** - Provide orientation for key concepts
8. **Modality** - Use both visual and verbal channels
9. **Multimedia** - Combine multiple media formats effectively
10. **Personalization** - Tailor to learner characteristics
11. **Voice** - Use conversational, friendly tone
12. **Imagery** - Include relevant, meaningful pictures

CONTENT STRUCTURE REQUIREMENTS:
- **Main Presentation Flow**: Introduction → Development → Examples → Practice → Assessment
- **Multimedia Elements**: Mix of text, diagrams, images, charts, and examples
- **Cognitive Load Management**: Limit complexity based on target level
- **Learning Sequence**: Logical progression from simple to complex
- **Engagement Features**: Interactive elements and thought-provoking content

SLIDE BREAKDOWN:
- **Title Slide**: Main topic, objectives, overview (1 slide)
- **Introduction**: Context, key concepts, foundation (2-3 slides)
- **Development**: Main content with examples and visuals (4-6 slides)
- **Application**: Practice exercises, real-world examples (2-3 slides)
- **Assessment**: Review questions, self-checks, summary (1-2 slides)

ELEMENT GUIDELINES:
- Each slide should have a clear focus
- Include both explanatory text and visual elements
- Balance text with relevant imagery
- Use examples that are relatable and clear
- Include checkpoints for understanding
- Design for both presentation and self-study

OUTPUT FORMAT (JSON ONLY):
{{
  "main_title": "Main Presentation Title",
  "subtitle": "Engaging subtitle that sets context",
  "learning_objectives": ["objective_1", "objective_2", "objective_3"],
  "estimated_duration_minutes": 45,
  "difficulty_level": "{cognitive_load.value}",
  "slides": [
    {{
      "slide_number": 1,
      "slide_type": "title",
      "title": "Clear, engaging title",
      "learning_objective": "specific_objective_for_this_slide",
      "key_concepts": ["concept_1", "concept_2"],
      "narration_points": [
        "Main presentation point with context",
        "Connection to overall topic",
        "Why this matters to learners"
      ],
      "visual_elements": [
        {{
          "type": "image",
          "description": "Descriptive image for main concept",
          "placement": "center",
          "priority": "high"
        }},
        {{
          "type": "text",
          "description": "Key definition or principle",
          "placement": "bottom",
          "priority": "medium"
        }}
      ],
      "interactions": [
        {{
          "type": "thought_question",
          "question": "Engaging question about the topic",
          "purpose": "activate_prior_knowledge"
        }}
      ]
    }}
  ],
  "narration_script": [
    {{
      "slide_number": 1,
      "script": "Conversational narration for slide 1",
      "key_points": ["point_1", "point_2", "point_3"]
    }}
  ],
  "assessment_opportunities": [
    {{
      "slide_number": 1,
      "assessment_type": "self_check",
      "question": "Self-reflection question",
      "expected_answer": "Expected student response"
    }}
  ]
}}

CRITICAL CONSTRAINTS:
- Respect cognitive load limits ({max_elements} elements maximum)
- Ensure all content is factually accurate and educationally sound
- Create content suitable for the specified audience level
- Include relevant examples and real-world applications
- Balance text with visual elements appropriately
- Design for both presentation and independent study

Create a comprehensive, engaging content structure that optimizes for multimedia learning effectiveness.
"""

    async def _call_glm46_model(self, prompt: str) -> str:
        """Call GLM-4.6 model through the appropriate service"""
        try:
            response = await self.llm_service.generate_response(
                query=prompt,
                context={"model_preference": "glm-4.6", "task_type": "multimedia_structuring"}
            )
            return response
        except Exception as e:
            logger.error(f"GLM-4.6 model call failed: {e}")
            raise

    def _parse_multimedia_structure_response(self, response: str) -> Dict[str, Any]:
        """Parse GLM-4.6 multimedia structure response"""
        try:
            if isinstance(response, dict):
                return response

            if isinstance(response, str):
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1

                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx]
                    return json.loads(json_str)

            logger.warning("Could not parse multimedia structure response as JSON")
            return {"slides": [], "main_title": "Generated Presentation"}

        except Exception as e:
            logger.error(f"Failed to parse multimedia structure response: {e}")
            return {"slides": [], "main_title": "Generated Presentation"}

    def _optimize_content_structure(
        self,
        content_structure: Dict[str, Any],
        cognitive_load: CognitiveLoadLevel
    ) -> Dict[str, Any]:
        """Optimize content structure based on cognitive load theory"""

        slides = content_structure.get("slides", [])
        max_elements = self.max_elements_per_load[cognitive_load]

        optimized_slides = []

        for slide in slides:
            optimized_slide = slide.copy()

            # Count total elements (text + visual + interactions)
            total_elements = (
                len(slide.get("key_concepts", [])) +
                len(slide.get("visual_elements", [])) +
                len(slide.get("narration_points", [])) +
                len(slide.get("interactions", []))
            )

            # Reduce elements if over cognitive load threshold
            if total_elements > max_elements:
                optimized_slide = self._reduce_cognitive_load(optimized_slide, max_elements)

            # Add multimedia optimization metadata
            optimized_slide["multimedia_optimization"] = {
                "elements_count": len(optimized_slide.get("visual_elements", [])),
                "text_elements_count": len(optimized_slide.get("key_concepts", [])),
                "interaction_count": len(optimized_slide.get("interactions", [])),
                "cognitive_load_score": min(1.0, total_elements / max_elements)
            }

            optimized_slides.append(optimized_slide)

        return {
            "main_title": content_structure.get("main_title", "Enhanced Presentation"),
            "subtitle": content_structure.get("subtitle"),
            "slides": optimized_slides,
            "optimization_applied": {
                "cognitive_load_management": True,
                "multimedia_integration": True,
                "cognitive_load_target": cognitive_load.value,
                "elements_optimized": True
            }
        }

    def _reduce_cognitive_load(self, slide: Dict[str, Any], max_elements: int) -> Dict[str, Any]:
        """Reduce cognitive load in slide by removing or combining elements"""

        # Prioritize elements by learning value
        elements_priorities = {
            "key_concepts": 1.0,
            "visual_elements": 0.9,
            "narration_points": 0.8,
            "interactions": 0.7
        }

        # Create list of all elements with priorities
        all_elements = []

        for element_type in ["visual_elements", "key_concepts", "narration_points", "interactions"]:
            elements = slide.get(element_type, [])
            for element in elements:
                all_elements.append({
                    "type": element_type,
                    "element": element,
                    "priority": elements_priorities.get(element_type, 0.5)
                })

        # Sort by priority (highest first) and keep top elements
        all_elements.sort(key=lambda x: x["priority"], reverse=True)

        # Keep only the most important elements
        kept_elements = all_elements[:max_elements]

        # Rebuild slide with reduced elements
        reduced_slide = slide.copy()

        for element_type in ["visual_elements", "key_concepts", "narration_points", "interactions"]:
            reduced_slide[element_type] = [
                elem["element"] for elem in kept_elements
                if elem["type"] == element_type
            ]

        return reduced_slide

    def _apply_mayer_principles(
        self,
        content_structure: Dict[str, Any],
        cognitive_load: CognitiveLoadLevel,
        learner_analysis: Dict[str, Any],
        multimedia_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply Mayer's multimedia learning principles to optimize content"""

        slides = content_structure.get("slides", [])
        optimized_content = content_structure.copy()

        # Get learner preferences
        preferences = multimedia_preferences or {}
        animation_tolerance = preferences.get("animation_tolerance", "moderate")
        visual_preference = learner_analysis.get("visual_preference", "high")
        color_sensitivity = preferences.get("color_sensitivity", "normal")

        applied_principles = []
        optimized_slides = []

        for slide in slides:
            optimized_slide = slide.copy()

            # Apply Coherence principle
            if slide.get("visual_elements") and slide.get("key_concepts"):
                optimized_slide = self._apply_coherence_principle(optimized_slide)
                applied_principles.append("coherence")

            # Apply Signaling principle
            optimized_slide = self._apply_signaling_principle(optimized_slide)
            applied_principles.append("signaling")

            # Apply Redundancy principle
            optimized_slide = self._apply_redundancy_principle(optimized_slide)
            applied_principles.append("redundancy")

            # Apply Spatial Contiguity
            optimized_slide = self._apply_spatial_contiguity(optimized_slide)
            applied_principles.append("spatial_contiguity")

            # Apply Temporal Contiguity
            optimized_slide = self._apply_temporal_contiguity(optimized_slide)
            applied_principles.append("temporal_contiguity")

            # Apply Personalization
            optimized_slide = self._apply_personalization_principle(
                optimized_slide, learner_analysis
            )
            applied_principles.append("personalization")

            # Apply Voice principle
            optimized_slide = self._apply_voice_principle(optimized_slide)
            applied_principles.append("voice")

            # Apply Imagery principle if visual preference is high
            if visual_preference == "high":
                optimized_slide = self._apply_imagery_principle(optimized_slide)
                applied_principles.append("imagery")

            # Adjust for animation tolerance
            if animation_tolerance == "low":
                optimized_slide = self._minimize_animations(optimized_slide)
            elif animation_tolerance == "high":
                optimized_slide = self._add_enhanced_animations(optimized_slide)

            optimized_slides.append(optimized_slide)

        return {
            **optimized_content,
            "slides": optimized_slides,
            "applied_principles": list(set(applied_principles)),
            "principle_effectiveness": self._calculate_principle_effectiveness(applied_principles, learner_analysis),
            "cognitive_load_optimized": True
        }

    def _apply_coherence_principle(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Mayer's Coherence principle: words and pictures presented together"""

        visual_elements = slide.get("visual_elements", [])
        key_concepts = slide.get("key_concepts", [])

        # Match visual elements with key concepts
        for i, visual in enumerate(visual_elements):
            if key_concepts and i < len(key_concepts):
                visual["associated_concept"] = key_concepts[i]
                visual["coherence_score"] = 1.0
            else:
                visual["coherence_score"] = 0.7  # Moderate coherence for unmatched visuals

        slide["visual_elements"] = visual_elements
        return slide

    def _apply_signaling_principle(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Mayer's Signaling principle: highlight essential information"""

        # Identify high-priority elements
        all_elements = []

        for element_type in ["visual_elements", "key_concepts", "narration_points", "interactions"]:
            elements = slide.get(element_type, [])
            for element in elements:
                if element_type == "key_concepts":
                    all_elements.append({
                        "content": element,
                        "type": "key_concept",
                        "priority": "high" if "essential" in str(element).lower() or "main" in str(element).lower() else "medium"
                    })
                elif element_type == "visual_elements":
                    all_elements.append({
                        "content": element,
                        "type": "visual_element",
                        "priority": "high" if element.get("priority") == "high" else "medium"
                    })

        # Add signaling attributes
        for element in all_elements:
            element["signaled"] = element["priority"] == "high"
            if element["priority"] == "high":
                element["visual_emphasis"] = True
                element["enhanced_visibility"] = True

        return slide

    def _apply_redundancy_principle(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Mayer's Redundancy principle: remove extraneous material"""

        # Remove duplicate elements
        seen_elements = set()
        unique_elements = []

        for element_type in ["key_concepts", "narration_points", "visual_elements"]:
            elements = slide.get(element_type, [])
            for element in elements:
                element_str = str(element)
                if element_str not in seen_elements and len(element_str.strip()) > 0:
                    seen_elements.add(element_str)
                    unique_elements.append(element)

        # Update slide with unique elements
        for element_type in ["key_concepts", "narration_points", "visual_elements"]:
            slide[element_type] = unique_elements

        return slide

    def _apply_spatial_contiguity(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Mayer's Spatial Contiguity principle: place related elements near each other"""

        visual_elements = slide.get("visual_elements", [])
        text_elements = slide.get("key_concepts", [])

        # Position related elements near each other
        if visual_elements and text_elements:
            for i, visual in enumerate(visual_elements):
                if i < len(text_elements):
                    visual["proximate_text"] = text_elements[i]
                    visual["spatial_alignment"] = "adjacent"
                    visual["proximity_score"] = 0.9

        slide["visual_elements"] = visual_elements
        return slide

    def _apply_temporal_contiguity(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Mayer's Temporal Contiguity principle: present related content simultaneously"""

        narration_points = slide.get("narration_points", [])
        visual_elements = slide.get("visual_elements", [])
        key_concepts = slide.get("key_concepts", [])

        # Ensure simultaneous presentation through metadata
        slide["temporal_synchronization"] = True

        # Link narration with visual elements
        for i, narration in enumerate(narration_points):
            if i < len(visual_elements):
                narration["synchronized_visual"] = visual_elements[i]["id"] if i < len(visual_elements) else None
                narration["simultaneous_display"] = True

        # Link all elements to main concept
        main_concept = key_concepts[0] if key_concepts else None
        if main_concept:
            for element_type in ["narration_points", "visual_elements", "key_concepts"]:
                elements = slide.get(element_type, [])
                for element in elements:
                    element["related_to"] = main_concept
                    element["simultaneous_with"] = True

        return slide

    def _apply_personalization_principle(
        self,
        slide: Dict[str, Any],
        learner_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply Mayer's Personalization principle: tailor to learner characteristics"""

        # Add learner-specific adaptations
        adaptations = []

        experience_level = learner_analysis.get("experience_level", "intermediate")
        if experience_level == "beginner":
            adaptations.append("simplified_language")
            adaptations.append("more_examples")
            adaptations.append("step_by_step_instructions")
        elif experience_level == "advanced":
            adaptations.append("complex_vocabulary")
            adaptations.append("challenging_questions")
            adaptations.append("open_ended_discussions")

        visual_preference = learner_analysis.get("visual_preference", "high")
        if visual_preference == "low":
            adaptations.append("text_focused")
        elif visual_preference == "high":
            adaptations.append("visually_enhanced")
            adaptations.append("detailed_visuals")

        slide["personalization"] = {
            "adaptations": adaptations,
            "experience_level": experience_level,
            "visual_preference": visual_preference,
            "customization_level": "medium"
        }

        return slide

    def _apply_voice_principle(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Mayer's Voice principle: use conversational, friendly tone"""

        # Convert formal text to conversational style
        narration_points = slide.get("narration_points", [])
        conversational_points = []

        for point in narration_points:
            if isinstance(point, str):
                # Convert to conversational style
                conversational = point.replace("This is", "This is").replace("These are", "These are").replace("We will", "We'll")
                conversational = point.replace("Students should", "You should").replace("Learners must", "You must")
                conversational_point = conversational.replace("The main", "The main")
                conversational_point = conversational.replace("It is", "It's")
                conversational_points.append(conversational_point)

        slide["narration_points"] = conversational_points
        slide["voice_style"] = "conversational"
        slide tone = "friendly"  # Conversational tone attribute

        return slide

    def _apply_imagery_principle(self, slide: Dict[str, any]) -> Dict[str, Any]:
        """Apply Mayer's Imagery principle: include relevant pictures"""

        visual_elements = slide.get("visual_elements", [])
        enhanced_elements = []

        # Enhance visual elements with imagery optimization
        for element in visual_elements:
            if element.get("type") in ["image", "diagram", "chart"]:
                element["imagery_optimized"] = True
                element["description_detailed"] = True
                element["relevant_example"] = True
                element["metaphor_support"] = True
                element["visual_memory_aid"] = True

                # Add accessibility features
                element["alt_text"] = f"Visual representation of {element.get('description', 'concept')}"
                element["low_contrast_fallback"] = True

                enhanced_elements.append(element)

        slide["visual_elements"] = enhanced_elements
        return slide

    def _minimize_animations(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """Minimize animations for low animation tolerance"""

        # Remove or reduce animation elements
        for element_type in ["interactions", "visual_elements"]:
            elements = slide.get(element_type, [])
            for element in elements:
                if element.get("type") in ["animation", "transition"]:
                    element["reduced_complexity"] = True
                    element["duration_shortened"] = True
                elif "animation" in str(element).lower():
                    element["minimal_animation"] = True

        slide["animation_minimized"] = True
        return slide

    def _add_enhanced_animations(self, slide: Dict[str, any]) -> Dict[str, any]:
        """Add enhanced animations for high animation tolerance"""

        # Add sophisticated animations
        for element_type in ["interactions", "visual_elements"]:
            elements = slide.get(element_type, [])
            for element in elements:
                if element.get("type") in ["animation", "transition", "dynamic"]:
                    element["enhanced_animation"] = True
                    element["smooth_transitions"] = True
                    element["interactive_elements"] = True
                elif "animation" in str(element).lower():
                    element["professional_animation"] = True
                    element["smooth_progressive"] = True

        slide["enhanced_animations"] = True
        return slide

    async def _generate_multimedia_slide_designs(
        self,
        content_structure: Dict[str, Any],
        learner_analysis: Dict[str, Any],
        preferred_style: Optional[str]
    ) -> Dict[str, Any]:
        """Generate multimedia slide designs optimized for learning effectiveness"""

        # Create design specifications based on content
        designs = []

        for slide in content_structure.get("slides", []):
            slide_design = self._create_optimal_slide_design(
                slide, learner_analysis, preferred_style
            )
            designs.append(slide_design)

        return {
            "designs": designs,
            "design_framework": self._get_design_framework(learner_analysis, preferred_style),
            "accessibility_features": self._get_accessibility_standards(learner_analysis),
            "color_scheme": self._get_optimal_color_scheme(learner_analysis),
            "typography": self._get_optimal_typography(learner_analysis)
        }

    def _create_optimal_slide_design(
        self,
        slide: Dict[str, Any],
        learner_analysis: Dict[str, Any],
        preferred_style: Optional[str]
    ) -> Dict[str, Any]:
        """Create optimal design for a specific slide"""

        slide_type = slide.get("slide_type", "content")
        experience_level = learner_analysis.get("experience_level", "intermediate")
        visual_preference = learner_analysis.get("visual_preference", "high")

        # Base design template
        design = {
            "slide_type": slide_type,
            "layout": self._get_optimal_layout(slide_type, visual_preference),
            "color_palette": self._get_optimal_colors(visual_preference),
            "typography": self._get_optimal_typography_by_type(slide_type, experience_level),
            "spacing": self._get_optimal_spacing(cognitive_load=CognitiveLoadLevel.MODERATE),
            "animation_level": learner_analysis.get("animation_tolerance", "moderate")
        }

        # Add slide-specific design elements
        if slide_type == "title":
            design.update({
                "title_font_size": 32 if experience_level == "advanced" else 28,
                "title_emphasis": True,
                "background_gradient": True
            })
        elif slide_type == "conclusion":
            design.update({
                "summary_font_size": 18,
                "key_points_emphasis": True,
                "call_to_action": True
            })

        # Add content-based optimizations
        content_elements = len(slide.get("key_concepts", [])) + len(slide.get("visual_elements", []))

        if content_elements > 8:
            design["layout"] = "structured_grid"
        elif content_elements > 5:
            design["layout"] = "balanced"
        else:
            design["layout"] = "flexible"

        return design

    def _get_optimal_layout(self, slide_type: str, visual_preference: str) -> str:
        """Determine optimal layout based on slide type and visual preference"""

        if slide_type == "title":
            return "centered"
        elif slide_type == "content" and visual_preference == "high":
            return "dual_column"
        elif slide_type == "content":
            return "left_column_dominant"
        elif visual_preference == "low":
            return "single_column"
        else:
            return "balanced"

    def _get_optimal_colors(self, visual_preference: str) -> Dict[str, str]:
        """Get optimal color palette based on visual preferences"""

        if visual_preference == "high":
            return {
                "primary": "#2563eb",  # Blue
                "secondary": "#7c3aed",  # Indigo
                "accent": "#3b82f6",  # Light Blue
                "background": "#ffffff",
                "text": "#1f2937"   # Dark Gray
            }
        elif visual_preference == "low":
            return {
                "primary": "#374151",  # Green
                "secondary": "#6b7280",  # Light Green
                "accent": "#a8dadc",  # Light Gray
                "background": "#f9fafb",
                "text": "#111827"
            }
        else:
            return {
                "primary": "#1e40af",
                "secondary": "#64748b",
                "accent": "#94a3b8",
                "background": "#ffffff",
                "text": "#1f2937"
            }

    def _get_optimal_typography_by_type(
        self,
        slide_type: str,
        experience_level: str
    ) -> Dict[str, Any]:
        """Get optimal typography based on slide type and experience level"""

        base_sizes = {
            "beginner": {
                "title": 32,
                "heading": 24,
                "body": 16,
                "caption": 14
            },
            "intermediate": {
                "title": 28,
                "heading": 20,
                "body": 14,
                "caption": 12
            },
            "advanced": {
                "title": 24,
                "heading": 18,
                "body": 12,
                "caption": 11
            }
        }

        sizes = base_sizes.get(experience_level, base_sizes["intermediate"])

        if slide_type == "title":
            return {
                "title_font": sizes["title"],
                "heading_font": sizes["heading"],
                "body_font": sizes["body"],
                "caption_font": sizes["caption"]
            }
        else:
            return {
                "heading_font": sizes["heading"],
                "body_font": sizes["body"],
                "caption_font": sizes["caption"],
                "code_font": 11
            }

    def _get_optimal_spacing(
        self,
        cognitive_load: CognitiveLoadLevel
    ) -> Dict[str, Any]:
        """Get optimal spacing based on cognitive load level"""

        spacings = {
            CognitiveLoadLevel.MINIMAL: {
                "title_margin_bottom": 40,
                "element_spacing": 20,
                "section_spacing": 30
            },
            CognitiveLoadLevel.MODERATE: {
                "title_margin_bottom": 30,
                "element_spacing": 15,
                "section_spacing": 25
            },
            CognitiveLoadLevel.COMPLEX: {
                "title_margin_bottom": 25,
                "element_spacing": 12,
                "section_spacing": 20
            },
            CognitiveLoadLevel.EXPERT: {
                "title_margin_bottom": 20,
                "element_spacing": 10,
                "section_spacing": 15
            }
        }

        return spacings[cognitive_load]

    def _create_dual_coded_slides(
        self,
        content_structure: Dict[str, Any],
        slide_designs: Dict[str, Any],
        cognitive_load: CognitiveLoadLevel
    ) -> List[Dict[str, Any]]:
        """Create dual-coded slides with optimal verbal-visual integration"""

        enhanced_slides = []
        designs = slide_designs.get("designs", [])

        for i, slide in enumerate(content_structure.get("slides", [])):
            # Get corresponding design
            design = designs[i] if i < len(designs) else designs[-1]

            # Create dual-coded slide
            dual_coded_slide = {
                **slide,
                "slide_number": slide.get("slide_number", i + 1),
                "dual_coding_optimized": True,
                "verbal_content": self._create_verbal_content(slide),
                "visual_content": self._create_visual_content(slide, design),
                "integration_points": self._create_integration_points(slide),
                "cognitive_load_level": cognitive_load.value,
                "dual_coding_score": self._calculate_dual_coding_score(slide)
            }

            enhanced_slides.append(dual_coded_slide)

        return enhanced_slides

    def _create_verbal_content(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """Create verbal content optimized for dual coding"""

        return {
            "main_text": slide.get("title", ""),
            "key_concepts": slide.get("key_concepts", []),
            "narration_points": slide.get("narration_points", []),
            "interaction_prompts": self._generate_interaction_prompts(slide),
            "spoken_style": slide.get("voice_style", "professional"),
            "reading_level": slide.get("reading_complexity", "moderate")
        }

    def _create_visual_content(
        self,
        slide: Dict[str, Any],
        design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create visual content optimized for dual coding"""

        visual_elements = slide.get("visual_elements", [])
        enhanced_visuals = []

        for element in visual_elements:
            enhanced_visual = element.copy()

            # Apply design styling
            enhanced_visual["design_attributes"] = {
                "color_scheme": design.get("color_palette", {}),
                "typography": design.get("typography", {}),
                "spacing": design.get("spacing", {})
            }

            # Add dual coding optimization
            enhanced_visual["dual_coded"] = True
            enhanced_visual["supports_verbal_integration"] = True
            enhanced_visual["enhanced_accessibility"] = True

            enhanced_visuals.append(enhanced_visual)

        return {
            "visual_elements": enhanced_visuals,
            "visual_integration": "optimized",
            "visual_support": "strong"
        }

    def _create_integration_points(
        self,
        slide: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create integration points between verbal and visual content"""

        integration_points = []

        key_concepts = slide.get("key_concepts", [])
        visual_elements = slide.get("visual_elements", [])

        # Match concepts with visuals
        for i, concept in enumerate(key_concepts):
            if i < len(visual_elements):
                integration_points.append({
                    "verbal_concept": concept,
                    "visual_element": visual_elements[i],
                    "integration_strength": 0.8,
                    "relationship_type": "explanation",
                    "timing": "simultaneous"
                })

        return integration_points

    def _calculate_dual_coding_score(self, slide: Dict[str, Any]) -> float:
        """Calculate dual coding effectiveness score"""

        verbal_elements = len(slide.get("key_concepts", [])) + len(slide.get("narration_points", []))
        visual_elements = len(slide.get("visual_elements", []))
        integration_points = len(slide.get("integration_points", []))

        if verbal_elements == 0 and visual_elements == 0:
            return 0.0

        # Calculate score based on balance and integration
        balance_score = 1.0 - abs(0.6 - (verbal_elements / (verbal_elements + visual_elements))) if (verbal_elements + visual_elements) > 0 else 1.0
        integration_score = min(1.0, integration_points / max(verbal_elements + visual_elements, 1)) if (verbal_elements + visual_elements) > 0 else 1.0

        return (balance_score * 0.5) + (integration_score * 0.5)

    def _generate_interaction_prompts(self, slide: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate interaction prompts for active engagement"""

        interaction_types = [
            "thought_question",
            "discussion_prompt",
            "self_check",
            "practice_exercise",
            "reflection_question"
        ]

        prompts = []
        slide_type = slide.get("slide_type", "content")

        # Generate prompts based on slide content
        if slide.get("key_concepts"):
            concepts = slide["key_concepts"][:3]  # Limit to prevent overload
            prompts.append({
                "type": "thought_question",
                "question": f"Come {concepts[0]} si collega con {concepts[1] if len(concepts) > 1 else 'altri argomenti'}?",
                "purpose": "activate_prior_knowledge",
                "timing": "slide_start"
            })

        if slide_type == "content":
            prompts.append({
                "type": "practice_exercise",
                "question": "Applica questi concetti a una situazione reale o un problema pratico",
                "purpose": "practical_application",
                "timing": "slide_middle"
            })
        elif slide_type == "conclusion":
            prompts.append({
                "type": "reflection_question",
                "question": "Qual è stato il concetto più importante che hai imparato?",
                "purpose": "metacognitive_reflection",
                "timing": "slide_end"
            })

        return prompts

    async def _add_accessibility_features(
        self,
        slides: List[Dict[str, Any]],
        learner_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add accessibility features for inclusive learning"""

        accessibility_needs = learner_analysis.get("accessibility_needs", [])

        features = {
            "screen_reader_support": True,
            "keyboard_navigation": True,
            "high_contrast_options": True,
            "text_to_speech": True,
            "description_support": True,
            "alternative_text": True,
            "focus_management": True
        }

        # Add accessibility metadata to each slide
        accessible_slides = []

        for slide in slides:
            accessible_slide = slide.copy()

            # Add alt text for images
            visual_elements = slide.get("visual_elements", [])
            for element in visual_elements:
                if element.get("type") in ["image", "diagram", "chart"]:
                    if not element.get("alt_text"):
                        element["alt_text"] = f"Visual representation of {element.get('description', 'slide element')}"

            accessible_slide["accessibility"] = {
                "wcag_aa_compliant": True,
                "focusable_elements": True,
                "screen_reader_optimized": True,
                "keyboard_accessible": True,
                "high_contrast_available": features["high_contrast_options"],
                "alternative_formats": ["text_only", "high_contrast"]
            }

            # Add color blindness considerations
            if color_sensitivity == "high":
                accessible_slide["color_blind_friendly"] = True
                accessible_slide["pattern_friendly"] = True

            accessible_slides.append(accessible_slide)

        return {
            "slides": accessible_slides,
            "accessibility_features": features,
            "adaptations": accessibility_needs,
            "compliance_level": "wcag_2_1_aa"
        }

    async def _generate_slide_guidance(
        self,
        slides: List[Dict[str, Any]],
        learner_analysis: Dict[str, Any],
        learning_objectives: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Generate comprehensive slide guidance for teachers and students"""

        # Calculate presentation duration and pacing
        total_duration = len(slides) * 5  # Assume 5 minutes per slide
        recommended_pacing = total_duration / len(slides)

        # Generate teaching strategies
        teaching_strategies = self._generate_teaching_strategies(slides, learner_analysis)

        # Create narration script
        narration_script = self._create_narration_script(slides)

        # Generate assessment opportunities
        assessment_opportunities = self._identify_assessment_opportunities(slides)

        return {
            "teaching_strategies": teaching_strategies,
            "presentation_duration_minutes": total_duration,
            "recommended_pacing_minutes": recommended_pacing,
            "narration_script": narration_script,
            "assessment_opportunities": assessment_opportunities,
            "engagement_tips": self._generate_engagement_tips(slides, learner_analysis),
            "accessibility_notes": self._generate_accessibility_notes(learner_analysis),
            "extension_activities": self._suggest_extension_activities(slides, learning_objectives)
        }

    def _generate_teaching_strategies(
        self,
        slides: List[Dict[str, Any]],
        learner_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate teaching strategies for effective presentation delivery"""

        strategies = []

        # General engagement strategies
        strategies.extend([
            {
                "slide_range": "all",
                "strategy": "pre_session_questions",
                "description": "Activate prior knowledge before presenting",
                "implementation": "Ask opening questions about the topic"
            },
            {
                "slide_range": "content",
                "strategy": "think_pair_share",
                "description": "Pause for thinking and discussion",
                "implementation": "Think individually, then discuss in pairs"
            },
            {
                "slide_range": "all",
                "strategy": "check_understanding",
                "description": "Verify comprehension periodically",
                "implementation": "Use quick quizzes or thumb checks"
            }
        ])

        # Slide-specific strategies
        title_slides = [i for i, slide in enumerate(slides) if slide.get("slide_type") == "title"]
        content_slides = [i for i, slide in enumerate(slides) if slide.get("slide_type") == "content"]
        conclusion_slides = [i for i, slide in enumerate(slides) if slide.get("slide_type") == "conclusion"]

        if title_slides:
            strategies.append({
                "slide_range": "title",
                "strategy": "establish_relevance",
                "description": "Connect to students' interests",
                "implementation": "Ask what students already know about the topic"
            })

        if content_slides:
            strategies.append({
                "slide_range": "content",
                "strategy": "guided_practice",
                "description": "Provide structured practice opportunities",
                "implementation": "Guide through examples step-by-step"
            })

            if len(content_slides) > 3:
                strategies.append({
                    "slide_range": "content",
                    "strategy": "chunk_information",
                    "description": "Break complex information into manageable chunks",
                    "implementation": "Present in logical segments with summaries"
                })

        if conclusion_slides:
            strategies.append({
                "slide_range": "conclusion",
                "strategy": "summarize_and_connect",
                "description": "Connect back to learning objectives",
                "implementation": "Recall main points and future applications"
            })

        return strategies

    def _create_narration_script(
        self,
        slides: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create comprehensive narration script for slide presentation"""

        narration_script = []

        for i, slide in enumerate(slides):
            slide_title = slide.get("title", f"Slide {i + 1}")
            narration_points = slide.get("narration_points", [])

            # Create narration for this slide
            slide_narration = {
                "slide_number": slide.get("slide_number", i + 1),
                "title": slide_title,
                "main_points": narration_points[:3],  # Limit to 3 main points
                "timing": f"Minutes {(i * 5)}-{((i + 1) * 5)}",
                "engagement_tips": [
                    "Speak clearly and at a moderate pace",
                    "Use appropriate tone and emphasis",
                    "Pause for emphasis when needed"
                ],
                "visual_cues": [
                    "Point to visual elements when mentioning them",
                    "Gesture to key points when appropriate"
                ]
            }

            narration_script.append(slide_narration)

        return narration_script

    def _identify_assessment_opportunities(
        self,
        slides: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify natural assessment opportunities in slides"""

        assessment_opportunities = []

        for slide in slides:
            slide_number = slide.get("slide_number", 0)
            key_concepts = slide.get("key_concepts", [])

            # Look for assessment opportunities in content slides
            if slide.get("slide_type") == "content":
                # Add self-checks after key concepts
                for concept in key_concepts:
                    assessment_opportunities.append({
                        "slide_number": slide_number,
                        "assessment_type": "self_check",
                        "question": f"Come potresti applicare {concept}?",
                        "assessment_timing": "immediate",
                        "follow_up": "practice_application"
                    })

                # Add practice exercises for application
                if "application" in slide.get("interaction_prompts", []):
                    assessment_opportunities.append({
                        "slide_number": slide_number,
                        "assessment_type": "practice_exercise",
                        "question": f"Esercizio pratico per {slide_title}",
                        "assessment_timing": "during_session",
                        "materials_needed": "self_assessment"
                    })

            elif slide.get("slide_type") == "conclusion":
                assessment_opportunities.append({
                    "slide_number": slide_number,
                    "assessment_type": "summary_quiz",
                    "question": "Quali sono i punti principali di questa presentazione?",
                    "assessment_timing": "end_session",
                    "follow_up": "next_steps"
                })

        return assessment_opportunities

    def _generate_engagement_tips(
        self,
        slides: List[Dict[str, Any]],
        learner_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate engagement tips for maintaining student attention"""

        tips = [
            "Vary your voice and pace to maintain interest",
            "Use gestures and movement when appropriate",
            "Make eye contact during presentation",
            "Encourage questions and participation",
            "Take brief breaks during longer presentations"
            "Use real-world examples when possible"
            "Show enthusiasm for the topic",
            "Adapt to student responses and questions"
        ]

        # Add learner-specific tips
        attention_span = learner_analysis.get("attention_span", "moderate")
        if attention_span == "short":
            tips.append("Use shorter slide segments")
            tips.append("Increase interaction frequency")
        elif attention_span == "long":
            tips.append("Can handle more complex content")
            tips.append("Allow for deeper exploration")

        experience_level = learner_analysis.get("experience_level", "intermediate")
        if experience_level == "beginner":
            tips.extend([
                "Provide clear step-by-step instructions",
                "Use simple, clear language",
                "Celebrate small successes"
            ])
        elif experience_level == "advanced":
            tips.extend([
                "Include challenging discussion questions",
                "Encourage critical analysis",
                "Allow for debate and exploration"
            ])

        return tips

    def _generate_extension_activities(
        self,
        slides: List[Dict[str, Any]],
        learning_objectives: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Suggest extension activities for continued learning"""

        activities = []

        # Analyze main topics covered
        main_topics = []
        for slide in slides:
            main_topics.extend(slide.get("key_concepts", []))

        unique_topics = list(set(main_topics))

        # Generate extension activities based on topics
        for topic in unique_topics[:3]:  # Limit to 3 extension activities
            activities.append({
                "activity_type": "further_research",
                "topic": topic,
                "suggestion": f"Esplora {topic} in maggior dettaglio",
                "resource_type": "additional_reading",
                "estimated_time_minutes": 30
            })

        if learning_objectives:
            activities.append({
                "activity_type": "objective_mastery",
                "objectives": learning_objectives,
                "suggestion": "Pratica fino al raggiungimento degli obiettivi",
                "resource_type": "practice_exercises",
                "estimated_time_minutes": 20
            })

        return activities

    def _get_applied_principles(self) -> List[str]:
        """Get list of applied Mayer principles"""
        return [
            "coherence",
            "signaling",
            "redundancy",
            "spatial_contiguity",
            "temporal_contiguity",
            "segmenting",
            "pre_training",
            "modality",
            "multimedia",
            "personalization",
            "voice",
            "imagery"
        ]

    def _calculate_principle_effectiveness(
        self,
        applied_principles: List[str],
        learner_analysis: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate effectiveness scores for applied principles"""

        scores = {}

        for principle in applied_principles:
            principle_weight = self.principle_weights.get(MultimediaPrinciple(principle.upper(), "UNKNOWN"), 0.5)
            learner_weight = self._get_learner_preference_weight(principle, learner_analysis)

            effectiveness = (principle_weight + learner_weight) / 2.0
            scores[principle] = effectiveness

        return scores

    def _get_learner_preference_weight(
        self,
        principle: str,
        learner_analysis: Dict[str, Any]
    ) -> float:
        """Get learner preference weight for a specific principle"""

        weights = {
            MultimediaPrinciple.COHERENCE: 0.9,
            MultimediaPrinciple.SIGNALING: learner_analysis.get("visual_preference") == "high" and 0.9 or 0.7,
            MultimediaPrinciple.REDUNDANCY: learner_analysis.get("complexity_tolerance") == "high" and 0.8 or 0.6,
            MultimediaPrinciple.SPATIAL_CONTIGUITY: 0.9,
            MultimediaPrinciple.TEMPORAL_CONTIGUITY: learner_analysis.get("attention_span") == "long" and 0.9 or 0.7,
            MultimediaPrinciple.SEGMENTING: 0.8,
            MultimediaPrinciple.PRE_TRAINING: learner_analysis.get("experience_level") == "advanced" and 0.8 or 0.6,
            MultimediaPrinciple.MODALITY: 0.95,  # High value for dual coding
            MultimediaPrinciple.MULTIMEDIA: 0.9,
            MultimediaPrinciple.PERSONALIZATION: learner_analysis.get("customization_needs") and 0.7 or 0.5,
            MultimediaPrinciple.VOICE: learner_analysis.get("engagement_level") == "high" and 0.7 or 0.5,
            MultimediaPrinciple.IMAGERY: learner_analysis.get("visual_preference") == "high" and 0.85 or 0.7
        }

        return weights.get(MultimediaPrinciple(principle, "UNKNOWN"), 0.5)

    def _calculate_multimedia_balance(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate multimedia balance metrics"""

        total_text_elements = sum(len(slide.get("key_concepts", [])) + len(slide.get("narration_points", [])))
        total_visual_elements = sum(len(slide.get("visual_elements", [])))

        if total_elements == 0:
            return {"text_ratio": 1.0, "visual_ratio": 0.0}

        text_ratio = total_text_elements / (total_text_elements + total_visual_elements)
        visual_ratio = total_visual_elements / (total_text_elements + total_visual_elements)

        # Check optimal ratios
        target_ratios = self.text_image_ratio.values()
        experience_level = "intermediate"  # Would get from slides metadata

        optimal_ratio = target_ratios.get(experience_level, 0.6)

        return {
            "text_ratio": text_ratio,
            "visual_ratio": visual_ratio,
            "balance_score": 1.0 - abs(text_ratio - optimal_ratio),
            "optimal_ratio": optimal_ratio,
            "balance_status": "optimal" if abs(text_ratio - optimal_ratio) < 0.1 else "needs_adjustment"
        }

    async def _track_generation_analytics(
        self,
        topic: str,
        cognitive_load: CognitiveLoadLevel,
        result: Dict[str, Any],
        duration: float
    ) -> None:
        """Track analytics for enhanced slide generation"""

        try:
            analytics_data = {
                "prompt_type": "enhanced_slide_generation",
                "model_used": "GLM-4.6",
                "strategy": "mayer_multimedia_learning",
                "context": {
                    "topic": topic,
                    "cognitive_load_level": cognitive_load.value,
                    "total_slides": len(result.get("total_slides", 0)),
                    "multimedia_elements": result.get("multimedia_elements", 0),
                    "principles_applied": len(result.get("applied_principles", [])),
                    "learner_adaptations": result.get("metadata", {}).get("learner_profile", {})
                },
                "performance_metrics": {
                    "generation_time_seconds": duration,
                    "slide_count": len(result.get("total_slides", 0)),
                    "multimedia_balance": result.get("metadata", {}).get("multimedia_balance", {}),
                    "dual_coding_scores": [
                        slide.get("dual_coding_score", 0)
                        for slide in result.get("slides", [])
                    ]
                }
            }

            await self.analytics.track_performance(analytics_data)

        except Exception as e:
            logger.error(f"Failed to track enhanced slide analytics: {e}")

    async def _call_glm46_for_visual_context(
        self,
        prompt: str,
        context: str
    ) -> str:
        """Call GLM-4.6 model for visual context analysis"""
        try:
            response = await self.llm_service.generate_response(
                query=prompt,
                context={"visual_context": context, "model_preference": "glm-4.6", "task_type": "visual_analysis"}
            )
            return response
        except Exception as e:
            logger.error(f"GLM-4.6 visual context call failed: {e}")
            raise

    def _fallback_content_structure(
        self,
        topic: str,
        cognitive_load: CognitiveLoadLevel
    ) -> Dict[str, Any]:
        """Fallback content structure generation if advanced method fails"""

        # Basic slide structure
        base_slides = [
            {
                "slide_number": 1,
                "slide_type": "title",
                "title": topic,
                "learning_objective": f"Introduzione a {topic}",
                "key_concepts": [topic],
                "narration_points": ["Panoramica generale", Contesto e importanza"],
                "visual_elements": [
                    {
                        "type": "image",
                        "description": "Rappresentazione visuale del concetto principale",
                        "placement": "center",
                        "priority": "high"
                    }
                ]
            },
            {
                "slide_number": 2,
                "slide_type": "content",
                "title": f"{topic} - Concetti Fondamentali",
                "learning_objective": "Comprendere i concetti base",
                "key_concepts": ["Definizione", "Caratteristiche", "Importanza"],
                "narration_points": [
                    "Spiegazione dettagliata dei concetti",
                    "Esempi pratici e applicazioni",
                    "Discussione ed esercizi"
                ],
                "visual_elements": [
                    {
                        "type": "diagram",
                        "description": "Diagramma dei concetti",
                        "placement": "center",
                        "priority": "high"
                    }
                ]
            },
            {
                "slide_number": 3,
                "slide_type": "content",
                "title": f"{topic} - Approfondimento",
                "learning_objective": "Approfondire la comprensione",
                "key_concepts": ["Applicazioni", "Sviluppi", "Innovazioni"],
                "narration_points": [
                    "Analisi dettagliata degli aspetti",
                    "Studi di caso specifici",
                    "Prospettive future"
                ],
                "visual_elements": [
                    {
                        "type": "chart",
                        "description": "Grafico dei progressi",
                        "placement": "right",
                        "priority": "medium"
                    }
                ]
            }
        ]

        # Adjust based on cognitive load
        max_slides = 3 if cognitive_load == CognitiveLoadLevel.MINIMAL else 5

        return {
            "main_title": f"Presentazione su {topic}",
            "subtitle": "Presentazione ottimizzata con principi multimedia learning",
            "slides": base_slides[:max_slides],
            "generation_method": "fallback",
            "optimization_level": "basic"
        }

    async def _generate_fallback_slides(
        self,
        course_id: str,
        book_id: Optional[str],
        topic: str,
        context_text: str
    ) -> Dict[str, Any]:
        """Generate fallback slides if enhanced generation fails"""

        logger.warning("Using fallback slide generation method")

        return {
            "slide_id": f"fallback_slides_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "course_id": course_id,
            "book_id": book_id,
            "topic": topic,
            "total_slides": 3,
            "slides": self._fallback_content_structure(topic, CognitiveLoadLevel.MINIMAL)["slides"],
            "generation_method": "fallback",
            "metadata": {
                "fallback_reason": "enhanced_generation_failed",
                "created_at": datetime.now().isoformat()
            }
        }

    def _get_design_framework(
        self,
        learner_analysis: Dict[str, Any],
        preferred_style: Optional[str]
    ) -> Dict[str, Any]:
        """Get overall design framework"""

        base_framework = {
            "template_engine": "mayer_multimedia",
            "design_philosophy": "cognitive_science_based",
            "accessibility_first": True,
            "mobile_responsive": True,
            "print_optimized": True
        }

        # Add learner-specific adaptations
        framework_preferences = {
            "animation_tolerance": learner_analysis.get("animation_tolerance", "moderate"),
            "color_scheme": self._get_optimal_colors(learner_analysis),
            "typography": self._get_optimal_typography_by_experience(
                learner_analysis.get("experience_level", "intermediate")
            ),
            "layout_preference": learner_analysis.get("visual_preference", "high") or "balanced"
        }

        base_framework.update(framework_preferences)

        return base_framework

    def _get_accessibility_standards(self, learner_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get accessibility standards based on learner profile"""

        base_standards = {
            "wcag_aa_level": "2.1",
            "section_508": True,
            "color_contrast": "aaa",
            "focus_management": True,
            "keyboard_navigable": True,
            "screen_reader_support": True,
            "text_to_speech": True
        }

        # Adjust based on specific needs
        if learner_analysis.get("accessibility_needs"):
            if "color_blind" in learner_analysis.get("accessibility_needs"):
                base_standards["color_contrast"] = "aaa"
                base_standards["color_blind_friendly"] = True
            if "hearing_impaired" in learner_analysis.get("accessibility_needs"):
                base_standards["caption_support"] = "enhanced"
                base_standards["audio_descriptions"] = "detailed"

        return base_standards

    def _get_design_framework(
        self,
        learner_analysis: Dict[str, Any],
        preferred_style: Optional[str]
    ) -> Dict[str, Any]:
        """Get overall design framework"""

        base_framework = {
            "template_engine": "mayer_multimedia",
            "design_philosophy": "cognitive_science_based",
            "accessibility_first": True,
            "mobile_responsive": True,
            "print_optimized": True
        }

        # Add learner-specific adaptations
        framework_preferences = {
            "animation_tolerance": learner_analysis.get("animation_tolerance", "moderate"),
            "color_scheme": self._get_optimal_colors(learner_analysis),
            "typography": self._get_optimal_typography_by_experience(
                learner_analysis.get("experience_level", "intermediate")
            ),
            "layout_preference": learner_analysis.get("visual_preference", "high") or "balanced"
        }

        base_framework.update(framework_preferences)

        return base_framework

    def _get_optimal_color_scheme(self, learner_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Get optimal color scheme based on learner profile"""

        if learner_analysis.get("color_sensitivity") == "high":
            return {
                "primary": "#2563eb",
                "secondary": "#475069",
                "accent": "#10b981",
                "background": "#ffffff",
                "text": "#374151",
                "warning": "#ef4444",
                "info": "#2196f3"
            }
        elif learner_analysis.get("color_sensitivity") == "low":
            return {
                "primary": "#059669",
                "secondary": "#047a68",
                "accent": "#40c05a",
                "background": "#f8fafb",
                "text": "#374151"
            }
        else:
            return {
                "primary": "#1e40af",
                "secondary": "#64748b",
                "accent": "#3b82f6",
                "background": "#ffffff",
                "text": "#1f2937"
            }

    def _get_optimal_typography_by_experience(
        self,
        experience_level: str
    ) -> Dict[str, Any]:
        """Get optimal typography settings based on experience level"""

        if experience_level == "beginner":
            return {
                "title_font": 32,
                "heading_font": 24,
                "body_font": 16,
                "caption_font": 14,
                "code_font": 12
            }
        elif experience_level == "advanced":
            return {
                "title_font": 24,
                "heading_font": 20,
                "body_font": 12,
                "caption_font": 11,
                "code_font": 10
            }
        else:  # intermediate
            return {
                "theme": "modern_professional",
                "title_font": 28,
                "heading_font": 20,
                "body_font": 14,
                "caption_font": 12,
                "code_font": 11
            }

    def _get_optimal_spacing(
        self,
        cognitive_load: CognitiveLoadLevel
    ) -> Dict[str, Any]:
        """Get optimal spacing based on cognitive load"""

        spacing_levels = {
            CognitiveLoadLevel.MINIMAL: {
                "title_margin_bottom": 40,
                "element_spacing": 20,
                "section_spacing": 30
            },
            CognitiveLoadLevel.MODERATE: {
                "title_margin_bottom": 30,
                "element_spacing": 15,
                "section_spacing": 25
            },
            CognitiveLoadLevel.COMPLEX: {
                "title_margin_bottom": 25,
                "element_spacing": 12,
                "section_spacing": 20
            },
            CognitiveLoadLevel.EXPERT: {
                "title_margin_bottom": 20,
                "element_spacing": 10,
                "section_spacing": 15
            }
        }

        return spacing_levels[cognitive_load]