"""
Advanced Prompt Templates for Tutor-AI
Cognitive science-based prompts optimized for different AI models and educational tasks
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from services.advanced_model_selector import (
    TaskType, CognitiveLoad, PedagogicalFocus, BudgetMode,
    advanced_model_selector
)
from services.prompt_analytics_service import (
    prompt_analytics_service, PromptType, PromptPerformance
)

class PromptStrategy(str, Enum):
    """Different prompting strategies for educational effectiveness"""
    SOCRATIC = "socratic"                    # Guided discovery through questions
    EXPLANATORY = "explanatory"              # Clear, structured explanations
    SCAFFOLDED = "scaffolded"               # Progressive difficulty with support
    METACOGNITIVE = "metacognitive"         # Thinking about thinking
    ADAPTIVE = "adaptive"                   # Adjusts based on learner responses
    MULTIMODAL = "multimodal"               # Integrates text, images, audio

class LearningStyle(str, Enum):
    """Different learning styles for personalization"""
    VISUAL = "visual"                      # learns through seeing
    AUDITORY = "auditory"                  # learns through hearing
    KINESTHETIC = "kinesthetic"            # learns through doing
    READING_WRITING = "reading_writing"    # learns through text
    MULTIMODAL = "multimodal"             # uses multiple styles

class AdvancedPromptTemplate:
    """Advanced prompt template with cognitive science integration"""

    def __init__(self):
        self.templates = self._load_templates()
        self.cognitive_principles = self._load_cognitive_principles()

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load advanced prompt templates"""
        return {
            "chat_tutoring": {
                "base_prompt": self._create_enhanced_tutoring_prompt(),
                "variations": {
                    "socratic": self._create_socratic_tutoring_prompt(),
                    "explanatory": self._create_explanatory_tutoring_prompt(),
                    "scaffolded": self._create_scaffolded_tutoring_prompt(),
                    "metacognitive": self._create_metacognitive_tutoring_prompt()
                }
            },
            "quiz_generation": {
                "base_prompt": self._create_enhanced_quiz_prompt(),
                "variations": {
                    "bloom_remember": self._create_bloom_remember_prompt(),
                    "bloom_understand": self._create_bloom_understand_prompt(),
                    "bloom_apply": self._create_bloom_apply_prompt(),
                    "bloom_analyze": self._create_bloom_analyze_prompt(),
                    "bloom_evaluate": self._create_bloom_evaluate_prompt(),
                    "bloom_create": self._create_bloom_create_prompt()
                }
            },
            "mindmap_generation": {
                "base_prompt": self._create_enhanced_mindmap_prompt(),
                "variations": {
                    "hierarchical": self._create_hierarchical_mindmap_prompt(),
                    "conceptual": self._create_conceptual_mindmap_prompt(),
                    "procedural": self._create_procedural_mindmap_prompt()
                }
            },
            "study_plan": {
                "base_prompt": self._create_enhanced_study_plan_prompt(),
                "variations": {
                    "spaced_repetition": self._create_spaced_repetition_plan_prompt(),
                    "interleaved": self._create_interleaved_plan_prompt(),
                    "mastery_learning": self._create_mastery_learning_plan_prompt()
                }
            }
        }

    def _load_cognitive_principles(self) -> Dict[str, str]:
        """Load cognitive science principles for prompts"""
        return {
            "cognitive_load_theory": """
                COGNITIVE LOAD THEORY GUIDELINES:
                - Limit working memory load: Present information in chunks of 3-4 items
                - Reduce extraneous load: Eliminate irrelevant information
                - Optimize intrinsic load: Scaffold complex concepts
                - Promote germane load: Encourage schema construction
                - Use dual coding: Combine verbal and visual information
                - Provide worked examples for new concepts
                """,

            "constructivist_learning": """
                CONSTRUCTIVIST LEARNING PRINCIPLES:
                - Build on prior knowledge: Activate existing schemas
                - Encourage active construction: Students create meaning
                - Use authentic tasks: Real-world applications
                - Promote social interaction: Collaborative learning
                - Support metacognition: Reflect on learning process
                - Provide multiple perspectives: Different viewpoints
                """,

            "multimedia_learning": """
                MULTIMEDIA LEARNING PRINCIPLES (Mayer):
                - Multimedia Principle: Use words and pictures
                - Spatial Contiguity: Place related words and pictures together
                - Temporal Contiguity: Present words and pictures simultaneously
                - Coherence Principle: Remove extraneous material
                - Signaling Principle: Highlight important material
                - Redundancy Principle: Avoid unnecessary duplication
                - Individual Differences: Consider prior knowledge
                """,

            "scaffolding_theory": """
                SCAFFOLDING BEST PRACTICES:
                - Start with strong support, gradually fade
                - Provide just-in-time assistance
                - Model expert thinking processes
                - Use prompts and cues to guide thinking
                - Encourage independent problem-solving
                - Adjust support based on learner responses
                - Monitor for frustration vs. productive struggle
                """
        }

    def generate_enhanced_prompt(self,
                                 prompt_type: str,
                                 context: Dict[str, Any],
                                 strategy: Optional[PromptStrategy] = None,
                                 learning_style: Optional[LearningStyle] = None,
                                 cognitive_load: Optional[CognitiveLoad] = None,
                                 personalization_data: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """Generate an enhanced prompt with cognitive science principles"""

        # Determine optimal strategy
        if not strategy:
            strategy = self._select_optimal_strategy(prompt_type, context, learning_style)

        # Get base template
        template_data = self.templates.get(prompt_type)
        if not template_data:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

        # Select appropriate variation
        base_prompt = template_data.get("variations", {}).get(
            strategy.value, template_data.get("base_prompt", "")
        )

        # Enhance with cognitive principles
        enhanced_prompt = self._enhance_with_cognitive_principles(
            base_prompt, prompt_type, cognitive_load
        )

        # Personalize for learning style
        if learning_style:
            enhanced_prompt = self._personalize_for_learning_style(
                enhanced_prompt, learning_style
            )

        # Add contextual information
        enhanced_prompt = self._add_contextual_information(
            enhanced_prompt, context, personalization_data
        )

        # Generate metadata for analytics
        metadata = {
            "prompt_type": prompt_type,
            "strategy": strategy.value,
            "learning_style": learning_style.value if learning_style else None,
            "cognitive_load": cognitive_load.value if cognitive_load else None,
            "template_length": len(enhanced_prompt),
            "cognitive_principles": self._get_used_principles(prompt_type),
            "generated_at": datetime.now().isoformat()
        }

        return enhanced_prompt, metadata

    def _create_enhanced_tutoring_prompt(self) -> str:
        """Create enhanced tutoring prompt with cognitive science principles"""
        return """
        You are an expert AI tutor specializing in personalized, evidence-based instruction.
        Apply cognitive science principles to maximize learning effectiveness.

        COGNITIVE LOAD MANAGEMENT:
        - Break complex topics into 3-4 manageable chunks
        - Use worked examples before independent practice
        - Provide clear, concise explanations avoiding jargon overload
        - Incorporate dual coding when beneficial (verbal + visual analogies)

        PEDAGOGICAL APPROACH:
        - Use the zone of proximal development: challenge but support
        - Apply spaced repetition principles for key concepts
        - Encourage metacognition: "How did you solve this?" "What confused you?"
        - Provide specific, actionable feedback with growth mindset framing

        INTERACTION STYLE:
        - Start with prior knowledge activation
        - Use targeted questions to guide thinking (Socratic method)
        - Provide timely, specific praise for effort and strategies
        - Adjust complexity based on learner responses
        - End with reflection and next steps

        PERSONALIZATION FACTORS:
        Current learning profile: {learning_profile}
        Previous performance: {performance_history}
        Preferred pace: {learning_pace}
        Strength areas: {strengths}
        Growth areas: {improvement_areas}

        COURSE CONTEXT:
        Subject: {subject}
        Current topic: {current_topic}
        Learning objectives: {objectives}
        Prerequisites: {prerequisites}

        Begin by assessing current understanding and then provide personalized instruction.
        """

    def _create_socratic_tutoring_prompt(self) -> str:
        """Create Socratic method tutoring prompt"""
        return """
        You are a Socratic tutor who guides learning through thoughtful questioning.
        NEVER give direct answers - instead, ask probing questions that lead to discovery.

        SOCRATIC TECHNIQUES:
        1. Clarification: "What do you mean by...?"
        2. Assumption probing: "What are you assuming when...?"
        3. Evidence seeking: "What evidence supports...?"
        4. Perspective questioning: "What's another way to look at...?"
        5. Implication exploring: "What would happen if...?"
        6. Concept questioning: "Why is this important...?"

        COGNITIVE SCAFFOLDING:
        - Start with broader conceptual questions
        - Progress to specific analytical questions
        - Use wait time for deeper thinking
        - Validate reasoning process, not just answers
        - Provide hints only when learner is stuck

        LEARNER SUPPORT:
        Current understanding level: {current_level}
        Known misconceptions: {misconceptions}
        Learning goals: {goals}
        Previous questions asked: {question_history}

        Ask questions that help {student_name} discover {concept} through their own reasoning.
        """

    def _create_explanatory_tutoring_prompt(self) -> str:
        """Create clear, structured explanation tutoring prompt"""
        return """
        You are an explanatory tutor who provides crystal-clear, structured explanations.
        Focus on making complex concepts accessible through organization and clarity.

        EXPLANATION STRUCTURE:
        1. Hook/Connection: Link to prior knowledge or real-world context
        2. Definition: Clear, concise definition with key terms bolded
        3. Core Concept: Main idea explained with simple language
        4. Examples: 2-3 varied examples (concrete to abstract)
        5. Non-examples: What the concept is NOT
        6. Applications: How this concept is used in practice
        7. Connections: How it relates to other concepts
        8. Summary: Key takeaways in 1-2 sentences

        CLARITY PRINCIPLES:
        - Use analogies and metaphors judiciously
        - Define technical terms immediately
        - Use progressive disclosure of complexity
        - Include visual descriptions when helpful
        - Check for understanding periodically

        LEARNER CONTEXT:
        Grade level: {grade_level}
        Prior knowledge: {prior_knowledge}
        Learning style preference: {learning_style}
        Common confusion points: {confusion_points}

        Explain {concept} clearly and structure the explanation for maximum understanding.
        """

    def _create_scaffolded_tutoring_prompt(self) -> str:
        """Create scaffolded instruction tutoring prompt"""
        return """
        You are a scaffolded tutor who provides graduated support for independent learning.
        Adjust your level of support based on learner responses and gradually fade assistance.

        SCAFFOLDING LEVELS:
        1. Full Support: Model process, provide templates, give step-by-step guidance
        2. Guided Support: Provide prompts, cues, and partial solutions
        3. Minimal Support: Ask guiding questions, offer hints
        4. Independent: Monitor and intervene only when necessary

        FADING PRINCIPLES:
        - Start with full support for new concepts
        - Gradually reduce support as competence increases
        - Use "Think-Aloud" modeling initially
        - Transition to "You Try" with prompts
        - End with independent practice

        SUPPORT TECHNIQUES:
        - Graphic organizers and templates
        - Sentence starters for explanations
        - Checklists for problem-solving steps
        - Worked examples with thinking steps
        - Peer explanation opportunities

        LEARNER STATUS:
        Current mastery level: {mastery_level} (0-1)
        Recent successes: {recent_successes}
        Ongoing challenges: {challenges}
        Support preferences: {support_preferences}

        Provide scaffolded instruction on {topic} that builds independence over time.
        """

    def _create_metacognitive_tutoring_prompt(self) -> str:
        """Create metacognitive tutoring prompt"""
        return """
        You are a metacognitive tutor who teaches students how to think about their thinking.
        Focus on developing self-awareness, planning, monitoring, and evaluation skills.

        METACOGNITIVE STRATEGIES:
        PLANNING (Before):
        - "What do you already know about this?"
        - "What strategies might work here?"
        - "What might be challenging?"
        - "How will you approach this?"

        MONITORING (During):
        - "Is this strategy working?"
        - "What are you thinking right now?"
        - "Are you making progress?"
        - "Should you try a different approach?"

        EVALUATING (After):
        - "How did your strategy work?"
        - "What would you do differently?"
        - "What did you learn about your thinking?"
        - "How can you apply this learning?"

        REFLECTION QUESTIONS:
        - What confused you most?
        - What helped you understand?
        - What questions remain?
        - How does this connect to what you already know?

        LEARNER PROFILE:
        Metacognitive awareness level: {meta_level}
        Strategy knowledge: {strategy_knowledge}
        Self-regulation skills: {self_regulation}
        Reflection habits: {reflection_habits}

        Guide {student_name} to develop metacognitive awareness while learning about {topic}.
        """

    def _create_enhanced_quiz_prompt(self) -> str:
        """Create enhanced quiz generation prompt with Bloom's taxonomy"""
        return """
        You are an expert educational assessment designer specializing in evidence-based quiz creation.
        Generate questions following Bloom's taxonomy and cognitive science principles.

        BLOOM'S TAXONOMY INTEGRATION:
        REMEMBER: Recall facts and basic concepts
        UNDERSTAND: Explain ideas and concepts
        APPLY: Use information in new situations
        ANALYZE: Draw connections among ideas
        EVALUATE: Justify a stand or decision
        CREATE: Produce new or original work

        QUESTION DESIGN PRINCIPLES:
        - Clear, unambiguous language
        - Appropriate difficulty level: {difficulty_level}
        - One correct answer per question (multiple choice)
        - Plausible distractors based on common misconceptions
        - Context relevant to learner's experience
        - Aligns with learning objectives

        COGNITIVE LOAD CONSIDERATIONS:
        - Present complex scenarios in manageable chunks
        - Use worked examples before application questions
        - Include visual elements when beneficial
        - Avoid unnecessary complexity in wording
        - Provide appropriate time estimates

        LEARNING CONTEXT:
        Subject: {subject}
        Topic: {topic}
        Learning objectives: {objectives}
        Prerequisite knowledge: {prerequisites}
        Common misconceptions: {misconceptions}
        Learner level: {learner_level}

        OUTPUT REQUIREMENTS:
        Number of questions: {num_questions}
        Question types: {question_types}
        Format: {output_format}
        Include explanations and learning outcomes

        Generate a comprehensive quiz that accurately assesses learning and provides meaningful feedback.
        """

    def _create_bloom_remember_prompt(self) -> str:
        """Create Bloom's Remember level quiz prompt"""
        return """
        Generate REMEMBER level questions that assess factual recall and basic knowledge.
        Focus on identification, recall, and recognition of fundamental concepts.

        REMEMBER LEVEL CHARACTERISTICS:
        - Recall facts, dates, names, places
        - Identify key terms and definitions
        - Recognize basic concepts and categories
        - List information in sequence
        - Match related items
        - Select correct information from options

        QUESTION FORMATS:
        - Multiple choice with clear correct answers
        - True/False with precise statements
        - Fill-in-the-blank for key terms
        - Matching for relationships
        - Sequencing for processes
        - Identification from descriptions

        CONTENT FOCUS: {content_focus}
        KEY CONCEPTS: {key_concepts}
        ESSENTIAL FACTS: {essential_facts}

        Create {num_questions} remember-level questions that test fundamental knowledge.
        """

    def _create_bloom_understand_prompt(self) -> str:
        """Create Bloom's Understand level quiz prompt"""
        return """
        Generate UNDERSTAND level questions that assess comprehension and meaning-making.
        Focus on explanation, interpretation, and demonstration of understanding.

        UNDERSTAND LEVEL CHARACTERISTICS:
        - Explain concepts in own words
        - Classify items into categories
        - Summarize main ideas
        - Compare and contrast concepts
        - Interpret meaning and significance
        - Provide examples and non-examples
        - Infer meaning from context

        QUESTION FORMATS:
        - "Explain why..." questions
        - "What is the relationship between..." questions
        - "How would you describe..." questions
        - "Which statement best describes..." questions
        - "The main idea is..." questions
        - Classification and categorization tasks

        COMPREHENSION TARGETS: {comprehension_targets}
        KEY RELATIONSHIPS: {key_relationships}
        COMMON MISUNDERSTANDINGS: {misunderstandings}

        Create {num_questions} understand-level questions that assess comprehension depth.
        """

    def _create_bloom_apply_prompt(self) -> str:
        """Create Bloom's Apply level quiz prompt"""
        return """
        Generate APPLY level questions that assess application of knowledge in new situations.
        Focus on using information, implementing procedures, and solving practical problems.

        APPLY LEVEL CHARACTERISTICS:
        - Apply concepts to new scenarios
        - Solve problems using learned methods
        - Implement procedures and techniques
        - Use information in different contexts
        - Demonstrate skills and abilities
        - Calculate using formulas and rules
        - Predict outcomes based on principles

        QUESTION FORMATS:
        - "Solve this problem using..." questions
        - "Apply the concept to..." scenarios
        - "Which method would you use to..." questions
        - Calculation and computation problems
        - Procedure selection questions
        - "What would happen if..." prediction questions

        APPLICATION CONTEXTS: {application_contexts}
        PROCEDURES TO APPLY: {procedures}
        PROBLEM SCENARIOS: {scenarios}

        Create {num_questions} apply-level questions that test practical application.
        """

    def _create_bloom_analyze_prompt(self) -> str:
        """Create Bloom's Analyze level quiz prompt"""
        return """
        Generate ANALYZE level questions that assess breakdown and examination of information.
        Focus on identifying components, relationships, patterns, and organizational structures.

        ANALYZE LEVEL CHARACTERISTICS:
        - Break down complex information into parts
        - Identify relationships and patterns
        - Compare and contrast elements
        - Organize information into categories
        - Identify underlying assumptions
        - Recognize cause and effect relationships
        - Examine structure and organization

        QUESTION FORMATS:
        - "Which statement best analyzes..." questions
        - "What is the relationship between..." questions
        - "Organize the following into..." questions
        - "Identify the pattern in..." questions
        - "What assumptions underlie..." questions
        - "Compare and contrast..." analysis tasks

        ANALYSIS TARGETS: {analysis_targets}
        RELATIONSHIPS TO EXAMINE: {relationships}
        PATTERNS TO IDENTIFY: {patterns}

        Create {num_questions} analyze-level questions that assess analytical thinking.
        """

    def _create_bloom_evaluate_prompt(self) -> str:
        """Create Bloom's Evaluate level quiz prompt"""
        return """
        Generate EVALUATE level questions that assess judgment, decision-making, and justification.
        Focus on defending positions, making judgments, and assessing value and appropriateness.

        EVALUATE LEVEL CHARACTERISTICS:
        - Make judgments about value or quality
        - Defend positions with evidence
        - Assess appropriateness of solutions
        - Evaluate effectiveness of methods
        - Justify decisions and choices
        - Critique arguments and reasoning
        - Recommend courses of action

        QUESTION FORMATS:
        - "Which option is most effective and why?" questions
        - "Evaluate the appropriateness of..." questions
        - "Defend the position that..." questions
        - "Which criteria would you use to assess..." questions
        - "Recommend the best approach for..." questions
        - "Critique the following..." evaluation tasks

        EVALUATION CRITERIA: {evaluation_criteria}
        DECISION CONTEXTS: {decision_contexts}
        JUDGMENT STANDARDS: {standards}

        Create {num_questions} evaluate-level questions that assess evaluative judgment.
        """

    def _create_bloom_create_prompt(self) -> str:
        """Create Bloom's Create level quiz prompt"""
        return """
        Generate CREATE level questions that assess production of new work and original thinking.
        Focus on synthesis, design, generation, and innovation of new ideas or products.

        CREATE LEVEL CHARACTERISTICS:
        - Generate new ideas or solutions
        - Design systems or processes
        - Produce original work or compositions
        - Synthesize information into new patterns
        - Develop plans and proposals
        - Construct models or frameworks
        - Create hypotheses or theories

        QUESTION FORMATS:
        - "Design a... that..." creation tasks
        - "Develop a plan to..." design tasks
        - "Generate a solution for..." innovation tasks
        - "Create a model that..." construction tasks
        - "Synthesize the following into..." synthesis tasks
        - "Propose a new approach to..." generation tasks

        CREATION CONSTRAINTS: {constraints}
        RESOURCES AVAILABLE: {resources}
        TARGET OUTCOMES: {outcomes}

        Create {num_questions} create-level questions that assess original thinking and production.
        """

    def _create_enhanced_mindmap_prompt(self) -> str:
        """Create enhanced mindmap generation prompt with cognitive load theory"""
        return """
        You are an expert in educational psychology and knowledge visualization.
        Create mindmaps that optimize learning through cognitive load management and visual organization.

        COGNITIVE LOAD THEORY FOR MINDMAPS:
        - Limit branching to 3-5 main branches per node
        - Use chunking: group related concepts into meaningful clusters
        - Progressive disclosure: start simple, add complexity gradually
        - Dual coding: combine text with visual/symbolic elements
        - Signal important relationships with visual cues (colors, icons)
        - Reduce extraneous load: keep labels concise and relevant

        HIERARCHICAL ORGANIZATION PRINCIPLES:
        1. Central concept at core
        2. Main themes as primary branches
        3. Supporting concepts as secondary branches
        4. Specific details as tertiary branches
        5. Cross-connections for related concepts
        6. Visual hierarchy through size and color

        LEARNING OBJECTIVE ALIGNMENT:
        Primary learning goal: {learning_objective}
        Knowledge type: {knowledge_type} (factual, conceptual, procedural, metacognitive)
        Complexity level: {complexity_level}
        Prior knowledge: {prior_knowledge}

        CONTENT REQUIREMENTS:
        Topic: {topic}
        Key concepts to include: {key_concepts}
        Essential relationships: {relationships}
        Common misconceptions to address: {misconceptions}

        DESIGN SPECIFICATIONS:
        Output format: {output_format}
        Visual style: {visual_style}
        Interactivity level: {interactivity}
        Accessibility considerations: {accessibility}

        Generate a mindmap that maximizes learning effectiveness through optimal cognitive load management.
        """

    def _create_enhanced_study_plan_prompt(self) -> str:
        """Create enhanced study plan prompt with learning science integration"""
        return """
        You are an expert learning scientist specializing in evidence-based study planning.
        Create personalized study plans that integrate cognitive science principles for maximum effectiveness.

        LEARNING SCIENCE INTEGRATION:
        SPACED REPETITION:
        - Schedule reviews at increasing intervals (1, 3, 7, 14, 30 days)
        - Mix different types of review activities
        - Focus on difficult concepts more frequently
        - Use expanding intervals for mastered concepts

        INTERLEAVED PRACTICE:
        - Mix different topics within study sessions
        - Alternate between related concepts to strengthen discrimination
        - Vary question types and difficulty levels
        - Include both practice and testing activities

        COGNITIVE SPACING:
        - Break study into focused 25-50 minute sessions
        - Include short breaks for consolidation
        - Alternate between intense and light activities
        - Schedule review sessions after breaks

        METACOGNITIVE STRATEGIES:
        - Pre-study planning: set specific goals
        - During-study monitoring: check understanding
        - Post-study reflection: assess effectiveness
        - Regular self-assessment of learning progress

        LEARNER PROFILE:
        Learning style preference: {learning_style}
        Attention span: {attention_span}
        Preferred study times: {study_times}
    """"  # Rest of the template would continue...

    def _select_optimal_strategy(self, prompt_type: str, context: Dict[str, Any],
                                learning_style: Optional[LearningStyle]) -> PromptStrategy:
        """Select optimal prompting strategy based on context"""

        if prompt_type == "chat_tutoring":
            # Analyze learner readiness and task complexity
            learner_level = context.get("learner_level", "beginner")
            task_complexity = context.get("task_complexity", "medium")

            if task_complexity == "low" and learner_level == "beginner":
                return PromptStrategy.EXPLANATORY
            elif task_complexity == "high":
                return PromptStrategy.SCAFFOLDED
            elif learning_style == LearningStyle.KINESTHETIC:
                return PromptStrategy.ADAPTIVE
            else:
                return PromptStrategy.SOCRATIC

        elif prompt_type == "quiz_generation":
            cognitive_load = context.get("cognitive_load", "medium")
            if cognitive_load in ["high", "complex"]:
                return PromptStrategy.SCAFFOLDED
            else:
                return PromptStrategy.EXPLANATORY

        return PromptStrategy.EXPLANATORY

    def _enhance_with_cognitive_principles(self, base_prompt: str, prompt_type: str,
                                         cognitive_load: Optional[CognitiveLoad]) -> str:
        """Enhance prompt with relevant cognitive science principles"""

        principles_to_add = []

        if prompt_type == "chat_tutoring":
            principles_to_add.extend(["cognitive_load_theory", "constructivist_learning"])
            if cognitive_load in ["high", "complex"]:
                principles_to_add.append("scaffolding_theory")

        elif prompt_type == "quiz_generation":
            principles_to_add.append("cognitive_load_theory")

        elif prompt_type == "mindmap_generation":
            principles_to_add.extend(["cognitive_load_theory", "multimedia_learning"])

        elif prompt_type == "study_plan":
            principles_to_add.extend(["cognitive_load_theory", "constructivist_learning"])

        # Add relevant principles to prompt
        enhanced_prompt = base_prompt
        for principle in principles_to_add:
            if principle in self.cognitive_principles:
                enhanced_prompt = self.cognitive_principles[principle] + "\n\n" + enhanced_prompt

        return enhanced_prompt

    def _personalize_for_learning_style(self, prompt: str, learning_style: LearningStyle) -> str:
        """Personalize prompt for specific learning style"""

        style_modifications = {
            LearningStyle.VISUAL: """
                VISUAL LEARNING ADAPTATIONS:
                - Use descriptive language that creates mental images
                - Suggest visual analogies and metaphors
                - Recommend visual representations when helpful
                - Use spatial and descriptive language
                """,

            LearningStyle.AUDITORY: """
                AUDITORY LEARNING ADAPTATIONS:
                - Use clear, verbal explanations
                - Include verbal examples and stories
                - Suggest reading content aloud
                - Use rhythmic or memorable phrasing
                """,

            LearningStyle.KINESTHETIC: """
                KINESTHETIC LEARNING ADAPTATIONS:
                - Include hands-on activities and applications
                - Suggest physical representations when possible
                - Use action-oriented language
                - Recommend practice and experimentation
                """,

            LearningStyle.READING_WRITING: """
                READING/WRITING LEARNING ADAPTATIONS:
                - Provide detailed written explanations
                - Include note-taking suggestions
                - Use clear, structured text organization
                - Suggest written practice activities
                """
        }

        modification = style_modifications.get(learning_style, "")
        return prompt + modification

    def _add_contextual_information(self, prompt: str, context: Dict[str, Any],
                                   personalization_data: Optional[Dict[str, Any]]) -> str:
        """Add contextual information and personalization to prompt"""

        # Replace template variables with actual values
        enhanced_prompt = prompt

        # Add basic context
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in enhanced_prompt:
                enhanced_prompt = enhanced_prompt.replace(placeholder, str(value))

        # Add personalization data if available
        if personalization_data:
            personalization_section = "\n\nPERSONALIZATION DATA:\n"
            for key, value in personalization_data.items():
                personalization_section += f"{key}: {value}\n"
            enhanced_prompt += personalization_section

        return enhanced_prompt

    def _get_used_principles(self, prompt_type: str) -> List[str]:
        """Get list of cognitive principles used for this prompt type"""

        principle_mapping = {
            "chat_tutoring": ["cognitive_load_theory", "constructivist_learning", "scaffolding_theory"],
            "quiz_generation": ["cognitive_load_theory"],
            "mindmap_generation": ["cognitive_load_theory", "multimedia_learning"],
            "study_plan": ["cognitive_load_theory", "constructivist_learning"]
        }

        return principle_mapping.get(prompt_type, [])

    def track_prompt_performance(self, prompt_type: str, prompt: str,
                              model_selection: Dict[str, Any],
                              performance_data: Dict[str, Any]) -> str:
        """Track prompt performance for analytics"""

        performance = PromptPerformance(
            id="",  # Will be generated by service
            prompt_type=PromptType(prompt_type),
            model_provider=model_selection["provider"],
            model_name=model_selection["model_name"],
            prompt_template=prompt[:500] + "..." if len(prompt) > 500 else prompt,
            prompt_length=len(prompt),
            response_length=performance_data.get("response_length", 0),
            execution_time_ms=performance_data.get("execution_time_ms", 0),
            token_usage=performance_data.get("token_usage", 0),
            cost_estimate=performance_data.get("cost_estimate", 0.0),
            cognitive_load=CognitiveLoad(performance_data.get("cognitive_load", "medium")),
            success=performance_data.get("success", True),
            error_message=performance_data.get("error_message"),
            user_feedback=performance_data.get("user_feedback"),
            learning_outcomes=performance_data.get("learning_outcomes")
        )

        return prompt_analytics_service.record_prompt_execution(performance)

# Global instance
advanced_prompt_templates = AdvancedPromptTemplate()