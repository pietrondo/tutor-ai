"""
Enhanced Quiz Service for Tutor-AI
Integrates Bloom's taxonomy with GLM-4.6 complex reasoning capabilities
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import asyncio

from services.enhanced_llm_service import enhanced_llm_service
from services.advanced_model_selector import advanced_model_selector, TaskType, CognitiveLoad
from services.prompt_analytics_service import prompt_analytics_service
from models.unified_learning import Quiz, QuizQuestion, DifficultyLevel

class BloomLevel(str, Enum):
    """Bloom's taxonomy cognitive levels"""
    REMEMBER = "remember"      # Recall facts and basic concepts
    UNDERSTAND = "understand"  # Explain ideas and concepts
    APPLY = "apply"            # Use information in new situations
    ANALYZE = "analyze"        # Draw connections among ideas
    EVALUATE = "evaluate"      # Justify a stand or decision
    CREATE = "create"          # Produce new or original work

class QuestionFormat(str, Enum):
    """Different question formats"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    ORDERING = "ordering"
    CALCULATION = "calculation"

class LearningObjective(str, Enum):
    """Learning objective types"""
    FACTUAL_RECALL = "factual_recall"
    CONCEPTUAL_UNDERSTANDING = "conceptual_understanding"
    PROCEDURAL_APPLICATION = "procedural_application"
    ANALYTICAL_REASONING = "analytical_reasoning"
    EVALUATIVE_JUDGMENT = "evaluative_judgment"
    CREATIVE_SYNTHESIS = "creative_synthesis"

class EnhancedQuizService:
    """Enhanced quiz service with Bloom's taxonomy integration"""

    def __init__(self):
        self.llm_service = enhanced_llm_service
        self.model_selector = advanced_model_selector

        # Bloom's taxonomy specifications
        self.bloom_specifications = self._load_bloom_specifications()

    def _load_bloom_specifications(self) -> Dict[str, Dict[str, Any]]:
        """Load Bloom's taxonomy specifications and cognitive requirements"""

        return {
            BloomLevel.REMEMBER.value: {
                "cognitive_load": CognitiveLoad.LOW,
                "complexity": 1,
                "time_estimate_minutes": 1,
                "question_types": [
                    QuestionFormat.MULTIPLE_CHOICE,
                    QuestionFormat.TRUE_FALSE,
                    QuestionFormat.FILL_BLANK,
                    QuestionFormat.MATCHING
                ],
                "verb_examples": [
                    "list", "identify", "define", "name", "recall", "recognize",
                    "select", "state", "describe", "label", "match"
                ],
                "assessment_focus": "Factual recall and basic identification",
                "difficulty_range": (0.1, 0.4)
            },

            BloomLevel.UNDERSTAND.value: {
                "cognitive_load": CognitiveLoad.LOW,
                "complexity": 2,
                "time_estimate_minutes": 2,
                "question_types": [
                    QuestionFormat.MULTIPLE_CHOICE,
                    QuestionFormat.SHORT_ANSWER,
                    QuestionFormat.TRUE_FALSE
                ],
                "verb_examples": [
                    "explain", "describe", "summarize", "interpret", "classify",
                    "compare", "contrast", "paraphrase", "illustrate", "example"
                ],
                "assessment_focus": "Comprehension and explanation of meaning",
                "difficulty_range": (0.2, 0.5)
            },

            BloomLevel.APPLY.value: {
                "cognitive_load": CognitiveLoad.MEDIUM,
                "complexity": 3,
                "time_estimate_minutes": 3,
                "question_types": [
                    QuestionFormat.MULTIPLE_CHOICE,
                    QuestionFormat.SHORT_ANSWER,
                    QuestionFormat.CALCULATION,
                    QuestionFormat.ORDERING
                ],
                "verb_examples": [
                    "apply", "use", "implement", "solve", "demonstrate", "calculate",
                    "practice", "execute", "perform", "carry out", "apply"
                ],
                "assessment_focus": "Application of knowledge in new situations",
                "difficulty_range": (0.3, 0.6)
            },

            BloomLevel.ANALYZE.value: {
                "cognitive_load": CognitiveLoad.HIGH,
                "complexity": 4,
                "time_estimate_minutes": 5,
                "question_types": [
                    QuestionFormat.MULTIPLE_CHOICE,
                    QuestionFormat.SHORT_ANSWER,
                    QuestionFormat.ESSAY
                ],
                "verb_examples": [
                    "analyze", "examine", "compare", "contrast", "differentiate",
                    "organize", "attribute", "break down", "outline", "structure"
                ],
                "assessment_focus": "Breaking down information and examining relationships",
                "difficulty_range": (0.5, 0.7)
            },

            BloomLevel.EVALUATE.value: {
                "cognitive_load": CognitiveLoad.HIGH,
                "complexity": 5,
                "time_estimate_minutes": 7,
                "question_types": [
                    QuestionFormat.MULTIPLE_CHOICE,
                    QuestionFormat.SHORT_ANSWER,
                    QuestionFormat.ESSAY
                ],
                "verb_examples": [
                    "evaluate", "judge", "critique", "assess", "justify", "defend",
                    "recommend", "determine", "prioritize", "rank", "validate"
                ],
                "assessment_focus": "Making judgments and defending positions",
                "difficulty_range": (0.6, 0.8)
            },

            BloomLevel.CREATE.value: {
                "cognitive_load": CognitiveLoad.COMPLEX,
                "complexity": 6,
                "time_estimate_minutes": 10,
                "question_types": [
                    QuestionFormat.SHORT_ANSWER,
                    QuestionFormat.ESSAY,
                    QuestionFormat.MULTIPLE_CHOICE  # For evaluating creative work
                ],
                "verb_examples": [
                    "create", "design", "develop", "construct", "compose", "formulate",
                    "propose", "plan", "produce", "invent", "generate", "synthesize"
                ],
                "assessment_focus": "Production of new work and original thinking",
                "difficulty_range": (0.7, 1.0)
            }
        }

    async def generate_bloom_quiz(
        self,
        course_id: str,
        topic: str,
        bloom_level: BloomLevel,
        num_questions: int = 5,
        question_formats: Optional[List[QuestionFormat]] = None,
        learning_objectives: Optional[List[LearningObjective]] = None,
        context_material: Optional[str] = None,
        difficulty_adjustment: float = 0.0,
        enable_analytics: bool = True
    ) -> Dict[str, Any]:
        """
        Generate Bloom's taxonomy-aligned quiz using optimal models

        Args:
            course_id: Course identifier
            topic: Quiz topic
            bloom_level: Bloom's cognitive level
            num_questions: Number of questions to generate
            question_formats: Preferred question formats
            learning_objectives: Specific learning objectives
            context_material: Reference material for context
            difficulty_adjustment: +/- adjustment to base difficulty
            enable_analytics: Enable performance tracking
        """

        start_time = datetime.now()

        # Prepare enhanced quiz context
        context = self._prepare_bloom_quiz_context(
            course_id, topic, bloom_level, num_questions,
            question_formats, learning_objectives, context_material,
            difficulty_adjustment
        )

        # Select optimal model for Bloom level generation
        model_selection = self._select_bloom_model(bloom_level, context)

        # Generate Bloom-aligned prompt
        bloom_prompt = self._create_bloom_aligned_prompt(
            bloom_level, context
        )

        # Generate quiz using enhanced LLM service
        response = await self.llm_service.generate_enhanced_response(
            query=bloom_prompt,
            context=context,
            course_id=course_id,
            prompt_type="quiz_generation",
            enable_analytics=enable_analytics
        )

        # Process and structure Bloom quiz response
        processed_quiz = await self._process_bloom_quiz_response(
            response, topic, bloom_level, context
        )

        # Calculate execution metrics
        execution_time = (datetime.now() - start_time).total_seconds()

        # Add Bloom-specific metadata
        processed_quiz["bloom_metadata"] = {
            "bloom_level": bloom_level.value,
            "cognitive_complexity": self.bloom_specifications[bloom_level.value]["complexity"],
            "estimated_time_minutes": self.bloom_specifications[bloom_level.value]["time_estimate_minutes"],
            "target_objectives": [obj.value for obj in (learning_objectives or [])],
            "model_used": model_selection["model_name"],
            "reasoning_depth": model_selection.get("reasoning_depth", 3),
            "execution_time_seconds": execution_time,
            "alignment_score": self._calculate_bloom_alignment_score(processed_quiz, bloom_level)
        }

        return processed_quiz

    async def generate_adaptive_quiz(
        self,
        course_id: str,
        topic: str,
        learner_profile: Dict[str, Any],
        num_questions: int = 5,
        enable_analytics: bool = True
    ) -> Dict[str, Any]:
        """
        Generate adaptive quiz based on learner profile and performance

        Args:
            course_id: Course identifier
            topic: Quiz topic
            learner_profile: Learner's performance profile
            num_questions: Number of questions
            enable_analytics: Enable performance tracking
        """

        # Analyze learner profile
        mastery_level = learner_profile.get("mastery_level", 0.5)
        learning_style = learner_profile.get("learning_style", "balanced")
        challenge_areas = learner_profile.get("challenge_areas", [])

        # Determine optimal Bloom level distribution
        bloom_distribution = self._calculate_adaptive_bloom_distribution(
            mastery_level, challenge_areas
        )

        # Generate questions across multiple Bloom levels
        quiz_sections = []
        total_questions_generated = 0

        for bloom_level, num_level_questions in bloom_distribution.items():
            if num_level_questions > 0:
                section_quiz = await self.generate_bloom_quiz(
                    course_id=course_id,
                    topic=f"{topic} - {bloom_level.value.title()}",
                    bloom_level=BloomLevel(bloom_level),
                    num_questions=num_level_questions,
                    learning_objectives=self._get_objectives_for_level(bloom_level),
                    enable_analytics=enable_analytics
                )

                quiz_sections.append({
                    "bloom_level": bloom_level,
                    "section_title": f"{bloom_level.value.title()} Level Questions",
                    "questions": section_quiz["quiz"]["questions"],
                    "bloom_metadata": section_quiz["bloom_metadata"]
                })

                total_questions_generated += num_level_questions

        # Combine sections into unified quiz
        unified_quiz = self._combine_quiz_sections(quiz_sections, topic, num_questions)

        # Add adaptive metadata
        unified_quiz["adaptive_metadata"] = {
            "learner_profile_used": {
                "mastery_level": mastery_level,
                "learning_style": learning_style,
                "challenge_areas": challenge_areas
            },
            "bloom_distribution": bloom_distribution,
            "adaptive_strategy": "personalized_difficulty_distribution",
            "total_sections": len(quiz_sections),
            "total_questions": total_questions_generated
        }

        return unified_quiz

    async def generate_comprehensive_quiz(
        self,
        course_id: str,
        topic: str,
        learning_objectives: List[LearningObjective],
        total_questions: int = 20,
        bloom_distribution: Optional[Dict[str, int]] = None,
        enable_analytics: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive quiz covering multiple Bloom levels

        Args:
            course_id: Course identifier
            topic: Quiz topic
            learning_objectives: List of learning objectives
            total_questions: Total number of questions
            bloom_distribution: Specific distribution of questions by Bloom level
            enable_analytics: Enable performance tracking
        """

        # Determine Bloom level distribution
        if not bloom_distribution:
            bloom_distribution = self._calculate_comprehensive_distribution(
                learning_objectives, total_questions
            )

        # Generate questions for each Bloom level
        quiz_sections = []

        for bloom_level, num_questions in bloom_distribution.items():
            if num_questions > 0:
                level_objectives = [
                    obj for obj in learning_objectives
                    if self._objective_matches_bloom_level(obj, bloom_level)
                ]

                section_quiz = await self.generate_bloom_quiz(
                    course_id=course_id,
                    topic=f"{topic} - Comprehensive",
                    bloom_level=BloomLevel(bloom_level),
                    num_questions=num_questions,
                    learning_objectives=level_objectives,
                    enable_analytics=enable_analytics
                )

                quiz_sections.append({
                    "bloom_level": bloom_level,
                    "section_title": f"{bloom_level.value.title()} Level",
                    "questions": section_quiz["quiz"]["questions"],
                    "learning_objectives": [obj.value for obj in level_objectives],
                    "bloom_metadata": section_quiz["bloom_metadata"]
                })

        # Create comprehensive quiz
        comprehensive_quiz = self._combine_quiz_sections(
            quiz_sections, topic, total_questions
        )

        # Add comprehensive metadata
        comprehensive_quiz["comprehensive_metadata"] = {
            "learning_objectives": [obj.value for obj in learning_objectives],
            "bloom_distribution": bloom_distribution,
            "coverage_analysis": self._analyze_coverage(comprehensive_quiz, learning_objectives),
            "difficulty_progression": self._calculate_difficulty_progression(comprehensive_quiz),
            "estimated_completion_time": self._estimate_completion_time(comprehensive_quiz)
        }

        return comprehensive_quiz

    def _prepare_bloom_quiz_context(
        self,
        course_id: str,
        topic: str,
        bloom_level: BloomLevel,
        num_questions: int,
        question_formats: Optional[List[QuestionFormat]],
        learning_objectives: Optional[List[LearningObjective]],
        context_material: Optional[str],
        difficulty_adjustment: float
    ) -> Dict[str, Any]:

        spec = self.bloom_specifications[bloom_level.value]

        context = {
            "course_id": course_id,
            "topic": topic,
            "bloom_level": bloom_level.value,
            "cognitive_complexity": spec["complexity"],
            "target_difficulty": spec["difficulty_range"][0] + difficulty_adjustment,
            "num_questions": num_questions,
            "question_types": question_formats or spec["question_types"],
            "learning_objectives": [obj.value for obj in (learning_objectives or [])],
            "cognitive_load": spec["cognitive_load"].value,
            "time_estimate": spec["time_estimate_minutes"],
            "verb_examples": spec["verb_examples"],
            "assessment_focus": spec["assessment_focus"],
            "context_material": context_material or "",
            "difficulty_adjustment": difficulty_adjustment,
            "bloom_verb": spec["verb_examples"][0],  # Primary verb for this level
            "desired_outcomes": self._get_desired_outcomes(bloom_level),
            "common_misconceptions": self._get_common_misconceptions(bloom_level, topic)
        }

        return context

    def _create_bloom_aligned_prompt(self, bloom_level: BloomLevel, context: Dict[str, Any]) -> str:
        """Create prompt specifically aligned with Bloom's level"""

        spec = self.bloom_specifications[bloom_level.value]

        prompt = f"""
        GENERATE BLOOM'S TAXONOMY {bloom_level.value.upper()} LEVEL QUIZ

        BLOOM'S TAXONOMY FOCUS: {spec['assessment_focus']}
        COGNITIVE COMPLEXITY: Level {spec['complexity']} (1-6 scale)
        ESTIMATED TIME PER QUESTION: {spec['time_estimate_minutes']} minutes

        TARGET TOPIC: {context['topic']}
        NUMBER OF QUESTIONS: {context['num_questions']}
        TARGET DIFFICULTY: {context['target_difficulty']:.2f} (adjusted {context['difficulty_adjustment']:+.1f})

        LEARNING OBJECTIVES:
        {self._format_objectives(context['learning_objectives'])}

        QUESTION FORMATS ALLOWED:
        {self._format_question_types(context['question_types'])}

        BLOOM VERBS TO USE:
        {self._format_verbs(spec['verb_examples'])}

        ASSESSMENT REQUIREMENTS:
        - All questions must clearly assess {bloom_level.value} level cognitive skills
        - Questions must be answerable within the estimated time frame
        - Distractors (for multiple choice) should be plausible but incorrect
        - Include one clearly correct answer per question
        - Questions should align with the learning objectives

        DIFFICULTY CALIBRATION:
        - Base difficulty range: {spec['difficulty_range'][0]:.2f} - {spec['difficulty_range'][1]:.2f}
        - Apply cognitive load adjustments based on complexity
        - Consider {context['cognitive_load']} cognitive load requirements
        - Adjust for {context['time_estimate']} minute time constraints

        CONTEXT MATERIAL:
        {context['context_material']}

        COMMON MISCONCEPTIONS TO AVOID:
        {self._format_misconceptions(context['common_misconceptions'])}

        DESIRED LEARNING OUTCOMES:
        {self._format_outcomes(context['desired_outcomes'])}

        OUTPUT REQUIREMENTS:
        - Return JSON format with questions array
        - Each question includes: question_text, correct_answer, distractors, explanation
        - Include bloom_level, cognitive_load, time_estimate for each question
        - Provide difficulty_score (0.0-1.0) for each question
        - Add alignment_score with learning objectives

        Generate {context['num_questions']} high-quality {bloom_level.value} level questions that authentically assess cognitive understanding.
        """

        return prompt

    def _select_bloom_model(self, bloom_level: BloomLevel, context: Dict[str, Any]) -> Dict[str, Any]:
        """Select optimal model for Bloom level generation"""

        # Map Bloom levels to task types
        bloom_task_mapping = {
            BloomLevel.REMEMBER: TaskType.SIMPLE_QA,
            BloomLevel.UNDERSTAND: TaskType.SUMMARIZATION,
            BloomLevel.APPLY: TaskType.MULTISTEP_PROBLEM,
            BloomLevel.ANALYZE: TaskType.COMPLEX_REASONING,
            BloomLevel.EVALUATE: TaskType.CRITICAL_THINKING,
            BloomLevel.CREATE: TaskType.CREATIVE_GENERATION
        }

        task_type = bloom_task_mapping[bloom_level]

        # Select optimal model with GLM-4.6 preference for higher levels
        return self.model_selector.select_optimal_model(
            task_type=task_type,
            cognitive_load=self.bloom_specifications[bloom_level.value]["cognitive_load"],
            pedagogical_focus=PedagogicalFocus.ASSESSMENT,
            context_size=len(_create_bloom_aligned_prompt(bloom_level, context)),
            output_size=2000  # Estimated tokens for quiz generation
        )

    async def _process_bloom_quiz_response(self, response: Dict[str, Any], topic: str, bloom_level: BloomLevel, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process Bloom quiz response and structure it properly"""

        quiz_data = response.get("response", "")

        try:
            # Try to parse as JSON first
            if isinstance(quiz_data, str):
                try:
                    quiz_data = json.loads(quiz_data)
                except json.JSONDecodeError:
                    # If not JSON, try to extract quiz data from text
                    quiz_data = self._extract_quiz_from_text(quiz_data)

            # Create Quiz objects
            questions = []
            for i, q_data in enumerate(quiz_data.get("questions", [])):
                question = QuizQuestion(
                    id=str(uuid.uuid4()),
                    question=q_data.get("question", f"Question {i+1}"),
                    options=q_data.get("options", []),
                    correct_answer=q_data.get("correct_answer", ""),
                    explanation=q_data.get("explanation", ""),
                    question_type=self._infer_question_type(q_data),
                    difficulty=DifficultyLevel.MEDIUM,  # Will be adjusted
                    topic_tags=[topic, bloom_level.value]
                )

                # Adjust difficulty based on Bloom level
                base_difficulty = self.bloom_specifications[bloom_level.value]["difficulty_range"][0]
                question.difficulty = self._adjust_difficulty_for_bloom(
                    base_difficulty, q_data.get("difficulty_score", 0.5)
                )

                questions.append(question)

            # Create Quiz object
            quiz = Quiz(
                id=str(uuid.uuid4()),
                title=f"Bloom {bloom_level.value.title()} Quiz: {topic}",
                description=f"Assessment of {bloom_level.value} level cognitive skills for {topic}",
                questions=questions,
                difficulty=self._calculate_quiz_difficulty(questions, bloom_level),
                estimated_minutes=len(questions) * self.bloom_specifications[bloom_level.value]["time_estimate_minutes"],
                topic_tags=[topic, bloom_level.value, "bloom_taxonomy"],
                linked_concept_ids=[],
                source="bloom_enhanced"
            )

            return {
                "quiz": {
                    "id": quiz.id,
                    "title": quiz.title,
                    "description": quiz.description,
                    "questions": [q.dict() for q in questions],
                    "difficulty": quiz.difficulty.value,
                    "estimated_minutes": quiz.estimated_minutes,
                    "topic_tags": quiz.topic_tags,
                    "bloom_level": bloom_level.value
                },
                "bloom_analysis": {
                    "alignment_score": self._calculate_bloom_alignment_score(questions, bloom_level),
                    "cognitive_load_distribution": self._analyze_cognitive_load(questions),
                    "time_estimate_actual": sum(
                        self.bloom_specifications[bloom_level.value]["time_estimate_minutes"]
                        for _ in questions
                    ),
                    "difficulty_distribution": [q.difficulty.value for q in questions]
                }
            }

        except Exception as e:
            # Fallback response
            return {
                "quiz": {
                    "id": str(uuid.uuid4()),
                    "title": f"Bloom {bloom_level.value.title()} Quiz: {topic}",
                    "description": f"Assessment of {bloom_level.value} level cognitive skills",
                    "questions": [],
                    "difficulty": "medium",
                    "estimated_minutes": context.get("num_questions", 5) * self.bloom_specifications[bloom_level.value]["time_estimate_minutes"],
                    "topic_tags": [topic, bloom_level.value, "bloom_taxonomy"]
                },
                "error": str(e)
            }

    def _format_objectives(self, objectives: List[str]) -> str:
        """Format learning objectives for prompt"""
        if not objectives:
            return "No specific objectives provided"
        return "\n".join(f"- {obj}" for obj in objectives)

    def _format_question_types(self, question_types: List[QuestionFormat]) -> str:
        """Format question types for prompt"""
        if not question_types:
            return "Multiple choice format"
        return "\n".join(f"- {qt.value}" for qt in question_types)

    def _format_verbs(self, verbs: List[str]) -> str:
        """Format Bloom verbs for prompt"""
        if not verbs:
            return "Explain, describe, identify"
        return "\n".join(f"- {verb}" for verb in verbs)

    def _format_misconceptions(self, misconceptions: List[str]) -> str:
        """Format misconceptions for prompt"""
        if not misconceptions:
            return "No specific misconceptions identified"
        return "\n".join(f"- {misconception}" for misconception in misconceptions)

    def _format_outcomes(self, outcomes: List[str]) -> str:
        """Format desired outcomes for prompt"""
        if not outcomes:
            return "Demonstrate cognitive understanding"
        return "\n".join(f"- {outcome}" for outcome in outcomes)

    def _get_desired_outcomes(self, bloom_level: BloomLevel) -> List[str]:
        """Get desired learning outcomes for Bloom level"""
        outcomes_mapping = {
            BloomLevel.REMEMBER: [
                "Recall basic facts and terminology",
                "Identify key concepts and definitions",
                "Recognize fundamental patterns"
            ],
            BloomLevel.UNDERSTAND: [
                "Explain concepts in own words",
                "Interpret meaning and significance",
                "Classify information into categories"
            ],
            BloomLevel.APPLY: [
                "Apply concepts to new situations",
                "Use procedures to solve problems",
                "Demonstrate practical skills"
            ],
            BloomLevel.ANALYZE: [
                "Break down complex information",
                "Identify patterns and relationships",
                "Compare and contrast different elements"
            ],
            BloomLevel.EVALUATE: [
                "Make informed judgments",
                "Defend positions with evidence",
                "Assess effectiveness of solutions"
            ],
            BloomLevel.CREATE: [
                "Generate original ideas",
                "Design innovative solutions",
                "Synthesize information in new ways"
            ]
        }

        return outcomes_mapping.get(bloom_level, ["Demonstrate understanding"])

    def _get_common_misconceptions(self, bloom_level: BloomLevel, topic: str) -> List[str]:
        """Get common misconceptions for Bloom level and topic"""
        # This would ideally be database-driven or AI-generated
        # For now, return generic misconceptions
        return [
            f"Confusing {topic} with related concepts",
            "Overgeneralizing from limited examples",
            "Applying rules in inappropriate contexts"
        ]

    def _calculate_bloom_alignment_score(self, questions: List[QuizQuestion], bloom_level: BloomLevel) -> float:
        """Calculate how well questions align with Bloom level requirements"""

        if not questions:
            return 0.0

        spec = self.bloom_specifications[bloom_level.value]
        target_complexity = spec["complexity"]
        target_difficulty_range = spec["difficulty_range"]

        # Score each question for Bloom alignment
        alignment_scores = []
        for question in questions:
            # Question complexity score (1-6)
            question_complexity = self._assess_question_complexity(question)
            complexity_score = 1.0 - abs(question_complexity - target_complexity) / 6.0

            # Difficulty range alignment
            if hasattr(question, 'difficulty'):
                numeric_difficulty = {
                    DifficultyLevel.EASY.value: 0.25,
                    DifficultyLevel.MEDIUM.value: 0.5,
                    DifficultyLevel.HARD.value: 0.75
                }.get(question.difficulty.value, 0.5)

                if target_difficulty_range[0] <= numeric_difficulty <= target_difficulty_range[1]:
                    difficulty_score = 1.0
                else:
                    difficulty_score = max(0, 1.0 - min(
                        abs(numeric_difficulty - target_difficulty_range[0]),
                        abs(numeric_difficulty - target_difficulty_range[1])
                    ) / 0.25
                )
            else:
                difficulty_score = 0.5

            # Verb alignment with Bloom level
            verb_alignment = self._assess_verb_alignment(question.question, bloom_level)

            # Combined score
            alignment_score = (complexity_score * 0.3 + difficulty_score * 0.4 + verb_alignment * 0.3)
            alignment_scores.append(alignment_score)

        return sum(alignment_scores) / len(alignment_scores)

    def _assess_question_complexity(self, question: QuizQuestion) -> int:
        """Assess cognitive complexity of a question (1-6 scale)"""
        # This would ideally use NLP for accurate assessment
        # For now, use heuristics based on question text
        text = question.question.lower()

        complexity_indicators = {
            1: ["what", "define", "list", "identify", "state"],
            2: ["explain", "describe", "summarize", "classify"],
            3: ["apply", "use", "solve", "calculate", "demonstrate"],
            4: ["analyze", "compare", "contrast", "organize", "examine"],
            5: ["evaluate", "judge", "critique", "assess", "justify"],
            6: ["create", "design", "develop", "propose", "generate", "synthesize"]
        }

        # Find highest complexity level indicated
        max_complexity = 1
        for level, indicators in complexity_indicators.items():
            if any(indicator in text for indicator in indicators):
                max_complexity = max(max_complexity, level)

        return max_complexity

    def _assess_verb_alignment(self, question_text: str, bloom_level: BloomLevel) -> float:
        """Assess how well question verbs align with Bloom level"""

        spec = self.bloom_specifications[bloom_level.value]
        target_verbs = [verb.lower() for verb in spec["verb_examples"]]
        question_words = question_text.lower().split()

        # Count alignment
        alignment_count = sum(1 for word in question_words if word in target_verbs)

        # Return alignment score (0-1)
        return min(1.0, alignment_count / max(1, len(target_verbs)))

    def _adjust_difficulty_for_bloom(self, base_difficulty: float, difficulty_score: float) -> str:
        """Adjust difficulty based on Bloom level and difficulty score"""

        # Map to difficulty levels
        if base_difficulty < 0.3:
            return DifficultyLevel.EASY
        elif base_difficulty < 0.6:
            return DifficultyLevel.MEDIUM
        else:
            return DifficultyLevel.HARD

    def _calculate_quiz_difficulty(self, questions: List[QuizQuestion], bloom_level: BloomLevel) -> DifficultyLevel:
        """Calculate overall quiz difficulty"""

        if not questions:
            return DifficultyLevel.MEDIUM

        # Average difficulty of all questions
        difficulties = []
        for question in questions:
            if question.difficulty == DifficultyLevel.EASY:
                difficulties.append(0.25)
            elif question.difficulty == DifficultyLevel.MEDIUM:
                difficulties.append(0.5)
            elif question.difficulty == DifficultyLevel.HARD:
                difficulties.append(0.75)
            else:
                difficulties.append(0.5)  # Default

        avg_difficulty = sum(difficulties) / len(difficulties)

        # Adjust based on Bloom level
        spec_difficulty = self.bloom_specifications[bloom_level.value]["difficulty_range"]

        if avg_difficulty < spec_difficulty[0]:
            return DifficultyLevel.EASY
        elif avg_difficulty < spec_difficulty[1]:
            return DifficultyLevel.MEDIUM
        else:
            return DifficultyLevel.HARD

    def _analyze_cognitive_load(self, questions: List[QuizQuestion]) -> Dict[str, float]:
        """Analyze cognitive load distribution across questions"""

        load_counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "complex": 0
        }

        for question in questions:
            complexity = self._assess_question_complexity(question)
            if complexity <= 2:
                load_counts["low"] += 1
            elif complexity == 3:
                load_counts["medium"] += 1
            elif complexity == 4:
                load_counts["high"] += 1
            else:
                load_counts["complex"] += 1

        total = sum(load_counts.values())
        return {k: v/total if total > 0 else 0 for k, v in load_counts.items()}

    def _extract_quiz_from_text(self, text: str) -> Dict[str, Any]:
        """Extract quiz data from unstructured text response"""

        # This would use more sophisticated text parsing
        # For now, return minimal structure
        return {
            "questions": [
                {
                    "question": text[:200] + "..." if len(text) > 200 else text,
                    "correct_answer": "A",
                    "options": ["A", "B", "C", "D"],
                    "explanation": "Extracted from response"
                }
            ]
        }

    def _infer_question_type(self, question_data: Dict[str, Any]) -> QuestionFormat:
        """Infer question type from question data"""

        if "options" in question_data and question_data["options"]:
            return QuestionFormat.MULTIPLE_CHOICE
        elif "correct_answer" in question_data and question_data.get("correct_answer") in [True, False]:
            return QuestionFormat.TRUE_FALSE
        elif question_data.get("question", "").count("___") > 0:
            return QuestionFormat.FILL_BLANK
        else:
            return QuestionFormat.SHORT_ANSWER

    def _calculate_adaptive_bloom_distribution(self, mastery_level: float, challenge_areas: List[str]) -> Dict[str, int]:
        """Calculate adaptive Bloom level distribution based on learner profile"""

        if mastery_level < 0.3:
            # Struggling learner - focus on lower levels
            return {
                BloomLevel.REMEMBER.value: 2,
                BloomLevel.UNDERSTAND.value: 2,
                BloomLevel.APPLY.value: 1,
                BloomLevel.ANALYZE.value: 0,
                BloomLevel.EVALUATE.value: 0,
                BloomLevel.CREATE.value: 0
            }
        elif mastery_level < 0.7:
            # Intermediate learner - balanced distribution
            return {
                BloomLevel.REMEMBER.value: 1,
                BloomLevel.UNDERSTAND.value: 2,
                BloomLevel.APPLY.value: 2,
                BloomLevel.ANALYZE.value: 0,
                BloomLevel.EVALUATE.value: 0,
                BloomLevel.CREATE.value: 0
            }
        else:
            # Advanced learner - focus on higher levels
            return {
                BloomLevel.REMEMBER.value: 0,
                BloomLevel.UNDERSTAND.value: 1,
                BloomLevel.APPLY.value: 1,
                BloomLevel.ANALYZE.value: 2,
                BloomLevel.EVALUATE.value: 1,
                BloomLevel.CREATE.value: 0
            }

    def _get_objectives_for_level(self, bloom_level: BloomLevel) -> List[LearningObjective]:
        """Get learning objectives appropriate for Bloom level"""

        objective_mapping = {
            BloomLevel.REMEMBER: [LearningObjective.FACTUAL_RECALL],
            BloomLevel.UNDERSTAND: [LearningObjective.CONCEPTUAL_UNDERSTANDING],
            BloomLevel.APPLY: [LearningObjective.PROCEDURAL_APPLICATION],
            BloomLevel.ANALYZE: [LearningObjective.ANALYTICAL_REASONING],
            BloomLevel.EVALUATE: [LearningObjective.EVALUATIVE_JUDGMENT],
            BloomLevel.CREATE: [LearningObjective.CREATIVE_SYNTHESIS]
        }

        return objective_mapping.get(bloom_level, [LearningObjective.CONCEPTUAL_UNDERSTANDING])

    def _objective_matches_bloom_level(self, objective: LearningObjective, bloom_level: BloomLevel) -> bool:
        """Check if learning objective matches Bloom level"""

        objective_bloom_mapping = {
            LearningObjective.FACTUAL_RECALL: BloomLevel.REMEMBER,
            LearningObjective.CONCEPTUAL_UNDERSTANDING: BloomLevel.UNDERSTAND,
            LearningObjective.PROCEDURAL_APPLICATION: BloomLevel.APPLY,
            LearningObjective.ANALYTICAL_REASONING: BloomLevel.ANALYZE,
            LearningObjective.EVALUATIVE_JUDGMENT: BloomLevel.EVALUATE,
            LearningObjective.CREATIVE_SYNTHESIS: BloomLevel.CREATE
        }

        return objective_bloom_mapping.get(objective) == bloom_level

    def _calculate_comprehensive_distribution(self, learning_objectives: List[LearningObjective], total_questions: int) -> Dict[str, int]:
        """Calculate comprehensive Bloom distribution based on learning objectives"""

        # Count objectives by Bloom level
        level_counts = {}
        for objective in learning_objectives:
            for bloom_level in BloomLevel:
                if self._objective_matches_bloom_level(objective, bloom_level):
                    level_counts[bloom_level.value] = level_counts.get(bloom_level.value, 0) + 1

        # If no specific objectives, use balanced distribution
        if not level_counts:
            return {
                BloomLevel.REMEMBER.value: max(1, total_questions // 6),
                BloomLevel.UNDERSTAND.value: max(1, total_questions // 6),
                BloomLevel.APPLY.value: max(1, total_questions // 6),
                BloomLevel.ANALYZE.value: max(1, total_questions // 6),
                BloomLevel.EVALUATE.value: max(1, total_questions // 6),
                BloomLevel.CREATE.value: max(1, total_questions // 6)
            }

        # Distribute questions based on objective priorities
        distribution = {}
        remaining_questions = total_questions

        # Sort levels by priority
        priority_order = [
            BloomLevel.UNDERSTAND,  # Foundation
            BloomLevel.APPLY,        # Practical application
            BloomLevel.ANALYZE,       # Critical thinking
            BloomLevel.EVALUATE,      # Judgment
            BloomLevel.CREATE,        # Creativity
            BloomLevel.REMEMBER       # Basic recall
        ]

        for level in priority_order:
            level_key = level.value
            if level_key in level_counts and remaining_questions > 0:
                count = max(1, min(level_counts[level_key], remaining_questions // len(priority_order)))
                distribution[level_key] = count
                remaining_questions -= count

        # Distribute any remaining questions evenly
        if remaining_questions > 0:
            for level in priority_order:
                level_key = level.value
                if level_key not in distribution:
                    distribution[level_key] = 0
                distribution[level_key] += 1
                remaining_questions -= 1
                if remaining_questions == 0:
                    break

        return distribution

    def _combine_quiz_sections(self, quiz_sections: List[Dict[str, Any]], topic: str, total_questions: int) -> Dict[str, Any]:
        """Combine multiple quiz sections into unified quiz"""

        # Combine all questions
        all_questions = []
        section_metadata = []

        question_count = 0
        for section in quiz_sections:
            section_questions = section.get("questions", [])
            all_questions.extend(section_questions)

            section_metadata.append({
                "bloom_level": section["bloom_level"],
                "title": section["section_title"],
                "question_count": len(section_questions),
                "starting_index": question_count
            })

            question_count += len(section_questions)

        return {
            "quiz": {
                "id": str(uuid.uuid4()),
                "title": f"Comprehensive Quiz: {topic}",
                "description": f"Multi-level assessment covering {len(quiz_sections)} Bloom's taxonomy levels",
                "questions": all_questions,
                "total_questions": len(all_questions),
                "sections": section_metadata,
                "estimated_time_minutes": sum(
                    section.get("bloom_metadata", {}).get("estimated_time_minutes", 5)
                    for section in quiz_sections
                )
            }
        }

    def _analyze_coverage(self, comprehensive_quiz: Dict[str, Any], learning_objectives: List[LearningObjective]) -> Dict[str, Any]:
        """Analyze how well quiz covers learning objectives"""

        questions = comprehensive_quiz["quiz"]["questions"]
        sections = comprehensive_quiz["quiz"].get("sections", [])

        coverage_analysis = {
            "total_objectives": len(learning_objectives),
            "covered_objectives": 0,
            "partially_covered": 0,
            "uncovered_objectives": 0,
            "objective_coverage": {}
        }

        # Analyze coverage for each objective
        for objective in learning_objectives:
            objective_coverage = {
                "objective": objective.value,
                "covered_sections": [],
                "related_questions": 0,
                "coverage_level": "none"
            }

            # Check which sections cover this objective
            for section in sections:
                section_objectives = section.get("learning_objectives", [])
                if objective.value in section_objectives:
                    objective_coverage["covered_sections"].append(section["bloom_level"])
                    objective_coverage["related_questions"] += section["question_count"]
                    objective_coverage["coverage_level"] = "complete"
                    coverage_analysis["covered_objectives"] += 1

            # Determine overall coverage level
            if objective_coverage["related_questions"] > 0:
                if objective_coverage["coverage_level"] == "complete":
                    pass  # Already marked
                else:
                    objective_coverage["coverage_level"] = "partial"
                    coverage_analysis["partially_covered"] += 1
            else:
                objective_coverage["coverage_level"] = "none"
                coverage_analysis["uncovered_objectives"] += 1

            coverage_analysis["objective_coverage"][objective.value] = objective_coverage

        # Calculate coverage percentages
        total_objectives = coverage_analysis["total_objectives"]
        if total_objectives > 0:
            coverage_analysis["coverage_percentage"] = (
                (coverage_analysis["covered_objectives"] + coverage_analysis["partially_covered"] * 0.5) / total_objectives
            ) * 100
        else:
            coverage_analysis["coverage_percentage"] = 0

        return coverage_analysis

    def _calculate_difficulty_progression(self, comprehensive_quiz: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate difficulty progression across the quiz"""

        sections = comprehensive_quiz["quiz"].get("sections", [])

        progression = {
            "sections": [],
            "overall_progression": "balanced",  # balanced, front_loaded, back_loaded
            "difficulty_trend": "stable"  # increasing, decreasing, stable
            "average_difficulty": 0.0
        }

        difficulties = []
        section_analysis = []

        for section in sections:
            section_difficulties = section.get("bloom_metadata", {}).get("difficulty_distribution", [])

            if section_difficulties:
                avg_difficulty = sum(section_difficulties) / len(section_difficulties)
                difficulties.append(avg_difficulty)

                section_analysis.append({
                    "bloom_level": section["bloom_level"],
                    "section_title": section["section_title"],
                    "average_difficulty": avg_difficulty,
                    "difficulty_range": [
                        min(section_difficulties),
                        max(section_difficulties)
                    ]
                })

        progression["sections"] = section_analysis
        progression["average_difficulty"] = sum(difficulties) / len(difficulties) if difficulties else 0.5

        # Analyze progression pattern
        if len(difficulties) > 1:
            increasing_count = sum(1 for i in range(1, len(difficulties)) if difficulties[i] > difficulties[i-1])

            if increasing_count >= len(difficulties) * 0.7:
                progression["difficulty_trend"] = "increasing"
            elif increasing_count <= len(difficulties) * 0.3:
                progression["difficulty_trend"] = "stable"
            else:
                progression["difficulty_trend"] = "decreasing"

        return progression

    def _estimate_completion_time(self, comprehensive_quiz: Dict[str, Any]) -> Dict[str, float]:
        """Estimate quiz completion time in minutes"""

        sections = comprehensive_quiz["quiz"].get("sections", [])

        total_time = 0
        time_by_level = {}
        confidence_intervals = []

        for section in sections:
            bloom_level = section.get("bloom_level")
            section_time = section.get("bloom_metadata", {}).get("estimated_time_minutes", 5)
            question_count = section.get("question_count", 0)

            # Calculate time with confidence interval
            actual_time = section_time * question_count
            confidence_interval = actual_time * 0.2  # ±20% confidence interval

            total_time += actual_time
            confidence_intervals.append(confidence_interval)

            if bloom_level not in time_by_level:
                time_by_level[bloom_level] = []
            time_by_level[bloom_level].append(actual_time)

        # Calculate overall confidence interval
        total_confidence = sum(confidence_intervals)

        return {
            "estimated_total_minutes": total_time,
            "confidence_interval_minutes": total_confidence,
            "time_by_bloom_level": time_by_level,
            "per_question_average": total_time / comprehensive_quiz["quiz"]["total_questions"]
        }

# Global instance
enhanced_quiz_service = EnhancedQuizService()