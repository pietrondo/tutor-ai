"""
Active Recall Engine
Advanced adaptive question generation system for enhanced learning
Based on latest cognitive science research (2024-2025)
"""

import os
import json
import uuid
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import sqlite3
import random

@dataclass
class Question:
    """Enhanced question with adaptive features"""
    id: str
    course_id: str
    concept_id: Optional[str]
    question_type: str  # multiple_choice, short_answer, fill_in_blank, explanation, application, comparison
    question_text: str
    correct_answer: Any
    options: List[str]  # For multiple choice
    explanation: str
    difficulty: float  # 0.0-1.0
    bloom_level: str  # remember, understand, apply, analyze, evaluate, create
    context_tags: List[str]
    source_material: Optional[str]
    created_at: datetime
    last_used: Optional[datetime]
    usage_count: int
    success_rate: float
    average_response_time: float

@dataclass
class QuestionGenerationRequest:
    """Request for question generation"""
    course_id: str
    content: str
    concept_id: Optional[str] = None
    difficulty_target: float = 0.5
    question_types: List[str] = None
    num_questions: int = 5
    bloom_levels: List[str] = None
    context_tags: List[str] = None

class ActiveRecallEngine:
    """Enhanced Active Recall Engine with adaptive generation"""

    def __init__(self, db_path: str = "data/active_recall.db"):
        self.db_path = db_path
        self.ensure_database()

        # Question type configurations
        self.question_types = {
            "multiple_choice": {
                "weight": 0.3,
                "template": "multiple_choice",
                "description": "Multiple choice with distractors"
            },
            "short_answer": {
                "weight": 0.25,
                "template": "short_answer",
                "description": "Open-ended short answer"
            },
            "fill_in_blank": {
                "weight": 0.2,
                "template": "fill_in_blank",
                "description": "Fill in the blank"
            },
            "explanation": {
                "weight": 0.15,
                "template": "explanation",
                "description": "Explain concept"
            },
            "application": {
                "weight": 0.1,
                "template": "application",
                "description": "Apply knowledge to scenario"
            }
        }

        # Bloom's Taxonomy levels
        self.bloom_levels = {
            "remember": {"difficulty": 0.2, "weight": 0.3},
            "understand": {"difficulty": 0.4, "weight": 0.25},
            "apply": {"difficulty": 0.6, "weight": 0.2},
            "analyze": {"difficulty": 0.75, "weight": 0.15},
            "evaluate": {"difficulty": 0.9, "weight": 0.07},
            "create": {"difficulty": 1.0, "weight": 0.03}
        }

    def ensure_database(self):
        """Ensure database and tables exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                concept_id TEXT,
                question_type TEXT NOT NULL,
                question_text TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                options TEXT,
                explanation TEXT,
                difficulty REAL DEFAULT 0.5,
                bloom_level TEXT DEFAULT 'understand',
                context_tags TEXT,
                source_material TEXT,
                created_at TEXT NOT NULL,
                last_used TEXT,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                average_response_time REAL DEFAULT 0.0
            )
        """)

        # Question attempts tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_attempts (
                id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                user_answer TEXT,
                is_correct BOOLEAN,
                response_time_ms INTEGER,
                attempted_at TEXT NOT NULL,
                difficulty_rating INTEGER,
                confidence_rating INTEGER,
                FOREIGN KEY (question_id) REFERENCES questions (id)
            )
        """)

        # Question generation cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_cache (
                id TEXT PRIMARY KEY,
                content_hash TEXT UNIQUE,
                generated_questions TEXT NOT NULL,
                generation_time TEXT NOT NULL,
                used_count INTEGER DEFAULT 0
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_course_id ON questions(course_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_question_id ON question_attempts(question_id)")

        conn.commit()
        conn.close()

    async def generate_questions(self, request: QuestionGenerationRequest) -> List[Question]:
        """
        Generate adaptive questions based on content and parameters
        """
        try:
            # Check cache first
            content_hash = self._hash_content(request.content)
            cached_questions = self._get_cached_questions(content_hash)
            if cached_questions:
                return cached_questions

            # Determine optimal question types and bloom levels
            question_types = request.question_types or self._select_question_types(
                request.difficulty_target, request.num_questions
            )
            bloom_levels = request.bloom_levels or self._select_bloom_levels(
                request.difficulty_target, request.num_questions
            )

            # Generate questions using LLM
            questions = []

            for i in range(request.num_questions):
                question_type = random.choice(question_types)
                bloom_level = random.choice(bloom_levels)

                # Generate specific question based on type and level
                question = await self._generate_specific_question(
                    content=request.content,
                    question_type=question_type,
                    bloom_level=bloom_level,
                    difficulty_target=request.difficulty_target,
                    course_id=request.course_id,
                    concept_id=request.concept_id,
                    context_tags=request.context_tags or []
                )

                if question:
                    questions.append(question)

            # Cache the results
            self._cache_questions(content_hash, questions)

            return questions

        except Exception as e:
            print(f"Error generating questions: {e}")
            return []

    async def _generate_specific_question(
        self,
        content: str,
        question_type: str,
        bloom_level: str,
        difficulty_target: float,
        course_id: str,
        concept_id: str = None,
        context_tags: List[str] = None
    ) -> Optional[Question]:
        """Generate a specific type of question"""
        try:
            # This is where we would integrate with LLM service
            # For now, implementing heuristics-based generation

            if question_type == "multiple_choice":
                return self._generate_multiple_choice_question(
                    content, bloom_level, difficulty_target, course_id, concept_id, context_tags
                )
            elif question_type == "short_answer":
                return self._generate_short_answer_question(
                    content, bloom_level, difficulty_target, course_id, concept_id, context_tags
                )
            elif question_type == "fill_in_blank":
                return self._generate_fill_in_blank_question(
                    content, bloom_level, difficulty_target, course_id, concept_id, context_tags
                )
            elif question_type == "explanation":
                return self._generate_explanation_question(
                    content, bloom_level, difficulty_target, course_id, concept_id, context_tags
                )
            elif question_type == "application":
                return self._generate_application_question(
                    content, bloom_level, difficulty_target, course_id, concept_id, context_tags
                )
            else:
                return None

        except Exception as e:
            print(f"Error generating {question_type} question: {e}")
            return None

    def _generate_multiple_choice_question(
        self,
        content: str,
        bloom_level: str,
        difficulty_target: float,
        course_id: str,
        concept_id: str = None,
        context_tags: List[str] = None
    ) -> Question:
        """Generate multiple choice question"""

        # Extract key concepts from content
        concepts = self._extract_key_concepts(content)
        if len(concepts) < 1:
            return None

        # Select main concept
        main_concept = concepts[0]

        # Generate question stem
        question_stem = f"Which of the following best describes {main_concept}?"

        # Generate correct answer
        correct_answer = self._extract_definition(content, main_concept)
        if not correct_answer:
            correct_answer = f"The correct definition of {main_concept}"

        # Generate distractors
        distractors = self._generate_distractors(correct_answer, main_concept, difficulty_target, content)

        # Combine all options
        options = [correct_answer] + distractors
        random.shuffle(options)

        # Find correct option index
        correct_index = options.index(correct_answer)

        question = Question(
            id=str(uuid.uuid4()),
            course_id=course_id,
            concept_id=concept_id,
            question_type="multiple_choice",
            question_text=question_stem,
            correct_answer=chr(65 + correct_index),  # A, B, C, D
            options=options,
            explanation=f"The correct answer is {chr(65 + correct_index)}. {correct_answer}",
            difficulty=difficulty_target,
            bloom_level=bloom_level,
            context_tags=context_tags or [],
            source_material="auto_generated",
            created_at=datetime.now(),
            last_used=None,
            usage_count=0,
            success_rate=0.0,
            average_response_time=0.0
        )

        self._save_question(question)
        return question

    def _generate_short_answer_question(
        self,
        content: str,
        bloom_level: str,
        difficulty_target: float,
        course_id: str,
        concept_id: str = None,
        context_tags: List[str] = None
    ) -> Question:
        """Generate short answer question"""

        concepts = self._extract_key_concepts(content)
        if len(concepts) < 1:
            return None

        concept = concepts[0]

        question_stem = f"Explain {concept} in your own words:"

        if bloom_level in ["apply", "analyze"]:
            question_stem = f"How would you apply your understanding of {concept} to solve a real-world problem?"

        question = Question(
            id=str(uuid.uuid4()),
            course_id=course_id,
            concept_id=concept_id,
            question_type="short_answer",
            question_text=question_stem,
            correct_answer=self._extract_definition(content, concept),
            options=[],
            explanation="This question tests your understanding and ability to articulate the concept clearly.",
            difficulty=difficulty_target,
            bloom_level=bloom_level,
            context_tags=context_tags or [],
            source_material="auto_generated",
            created_at=datetime.now(),
            last_used=None,
            usage_count=0,
            success_rate=0.0,
            average_response_time=0.0
        )

        self._save_question(question)
        return question

    def _generate_fill_in_blank_question(
        self,
        content: str,
        bloom_level: str,
        difficulty_target: float,
        course_id: str,
        concept_id: str = None,
        context_tags: List[str] = None
    ) -> Question:
        """Generate fill in the blank question"""

        sentences = content.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]

        # Find a sentence with a key concept
        target_sentence = None
        target_concept = None

        for sentence in sentences:
            concepts = self._extract_key_concepts(sentence)
            if concepts:
                target_sentence = sentence
                target_concept = concepts[0]
                break

        if not target_sentence:
            return None

        # Create blank by replacing the concept
        question_text = target_sentence.replace(target_concept, "_______")

        question = Question(
            id=str(uuid.uuid4()),
            course_id=course_id,
            concept_id=concept_id,
            question_type="fill_in_blank",
            question_text=question_text + ".",
            correct_answer=target_concept,
            options=[],
            explanation=f"Fill in the blank with the correct term: {target_concept}",
            difficulty=difficulty_target,
            bloom_level=bloom_level,
            context_tags=context_tags or [],
            source_material="auto_generated",
            created_at=datetime.now(),
            last_used=None,
            usage_count=0,
            success_rate=0.0,
            average_response_time=0.0
        )

        self._save_question(question)
        return question

    def _generate_explanation_question(
        self,
        content: str,
        bloom_level: str,
        difficulty_target: float,
        course_id: str,
        concept_id: str = None,
        context_tags: List[str] = None
    ) -> Question:
        """Generate explanation question"""

        concepts = self._extract_key_concepts(content)
        if len(concepts) < 1:
            return None

        concept = concepts[0]

        question_text = f"Explain the significance of {concept} and its relationship to other concepts."

        # Extract key relationships
        explanation = self._extract_relationships(content, concept)
        if not explanation:
            explanation = f"Provide a detailed explanation of {concept}."

        question = Question(
            id=str(uuid.uuid4()),
            course_id=course_id,
            concept_id=concept_id,
            question_type="explanation",
            question_text=question_text,
            correct_answer=explanation,
            options=[],
            explanation="Your answer should demonstrate deep understanding of the concept.",
            difficulty=difficulty_target,
            bloom_level=bloom_level,
            context_tags=context_tags or [],
            source_material="auto_generated",
            created_at=datetime.now(),
            last_used=None,
            usage_count=0,
            success_rate=0.0,
            average_response_time=0.0
        )

        self._save_question(question)
        return question

    def _generate_application_question(
        self,
        content: str,
        bloom_level: str,
        difficulty_target: float,
        course_id: str,
        concept_id: str = None,
        context_tags: List[str] = None
    ) -> Question:
        """Generate application question"""

        concepts = self._extract_key_concepts(content)
        if len(concepts) < 1:
            return None

        concept = concepts[0]

        # Create scenario-based question
        scenarios = [
            f"Imagine you're working on a project where you need to apply {concept}. How would you approach it?",
            f"Describe a real-world situation where understanding {concept} would be crucial.",
            f"Create a step-by-step guide for applying {concept} in practice."
        ]

        question_text = random.choice(scenarios)

        question = Question(
            id=str(uuid.uuid4()),
            course_id=course_id,
            concept_id=concept_id,
            question_type="application",
            question_text=question_text,
            correct_answer=f"Apply {concept} by following best practices and considering the specific context.",
            options=[],
            explanation="Your answer should demonstrate practical application of the concept.",
            difficulty=difficulty_target,
            bloom_level=bloom_level,
            context_tags=context_tags or [],
            source_material="auto_generated",
            created_at=datetime.now(),
            last_used=None,
            usage_count=0,
            success_rate=0.0,
            average_response_time=0.0
        )

        self._save_question(question)
        return question

    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content using heuristics"""
        # Simple keyword extraction - in production, use NLP
        words = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', content)

        # Filter out common words and keep meaningful terms
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'this', 'that', 'these', 'those',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'can', 'may', 'might', 'must'
        }

        concepts = [word for word in words if len(word) > 3 and word.lower() not in common_words]

        # Return most frequent concepts
        from collections import Counter
        concept_counts = Counter(concepts)

        return [concept for concept, count in concept_counts.most_common(5)]

    def _extract_definition(self, content: str, concept: str) -> str:
        """Extract definition of a concept from content"""
        # Simple heuristic-based definition extraction
        sentences = content.split('.')

        for sentence in sentences:
            sentence = sentence.strip()
            if concept.lower() in sentence.lower():
                # Clean up the sentence
                definition = re.sub(r'\[.*?\]', '', sentence)  # Remove citations
                definition = re.sub(r'\s+', ' ', definition).strip()

                if len(definition) > 20 and len(definition) < 200:
                    return definition

        return f"The definition of {concept} based on the provided content."

    def _generate_distractors(self, correct_answer: str, concept: str, difficulty: float, content: str) -> List[str]:
        """Generate distractor answers for multiple choice"""
        distractors = []

        # Common distractor types
        if difficulty < 0.5:  # Easy level
            # Opposite meanings
            opposite_words = ["not", "never", "sometimes", "rarely", "always", "only"]
            for word in opposite_words:
                if word not in correct_answer.lower():
                    distractors.append(f"{word} {correct_answer.lower()}")
                    if len(distractors) >= 3:
                        break

        else:  # Medium/Hard level
            # Related but incorrect concepts
            concepts = self._extract_key_concepts(content)
            for other_concept in concepts:
                if other_concept != concept and len(other_concept) > 3:
                    distractors.append(f"A concept related to {other_concept}")
                    if len(distractors) >= 3:
                        break

        # Ensure we have exactly 3 distractors
        while len(distractors) < 3:
            generic_distractors = [
                "An incorrect option",
                "A misleading statement",
                "An unrelated concept"
            ]
            distractors.append(random.choice(generic_distractors))

        return distractors[:3]

    def _extract_relationships(self, content: str, concept: str) -> str:
        """Extract relationships involving a concept"""
        # Look for connection patterns
        relationship_patterns = [
            f"{concept} relates to",
            f"{concept} affects",
            f"{concept} is influenced by",
            f"{concept} interacts with",
            f"{concept} depends on"
        ]

        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(pattern in sentence.lower() for pattern in relationship_patterns):
                return sentence

        return f"The relationships involving {concept} based on the context provided."

    def _select_question_types(self, difficulty_target: float, num_questions: int) -> List[str]:
        """Select optimal question types based on difficulty"""
        # Adjust type distribution based on difficulty
        if difficulty_target < 0.4:  # Easy
            return ["multiple_choice"] * num_questions
        elif difficulty_target < 0.6:  # Medium
            types = ["multiple_choice", "short_answer", "fill_in_blank"]
            return [random.choice(types) for _ in range(num_questions)]
        elif difficulty_target < 0.8:  # Hard
            types = ["short_answer", "explanation", "application", "multiple_choice"]
            return [random.choice(types) for _ in range(num_questions)]
        else:  # Very Hard
            types = ["explanation", "application", "short_answer"]
            return [random.choice(types) for _ in range(num_questions)]

    def _select_bloom_levels(self, difficulty_target: float, num_questions: int) -> List[str]:
        """Select appropriate Bloom's levels based on difficulty"""
        if difficulty_target < 0.3:
            return ["remember"] * num_questions
        elif difficulty_target < 0.5:
            return ["remember", "understand"] * (num_questions // 2 + num_questions % 2)
        elif difficulty_target < 0.7:
            return ["understand", "apply", "analyze"] * (num_questions // 3 + 1)
        elif difficulty_target < 0.9:
            return ["apply", "analyze", "evaluate"] * (num_questions // 3 + 1)
        else:
            return ["analyze", "evaluate", "create"] * (num_questions // 3 + 1)

    def _hash_content(self, content: str) -> str:
        """Create hash of content for caching"""
        return str(hash(content))

    def _get_cached_questions(self, content_hash: str) -> Optional[List[Question]]:
        """Get cached questions if available"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT generated_questions FROM question_cache WHERE content_hash = ?",
                (content_hash,)
            )
            row = cursor.fetchone()

            conn.close()

            if row:
                questions_data = json.loads(row[0])
                return [Question(**q_data) for q_data in questions_data]
            return None

        except Exception as e:
            print(f"Error getting cached questions: {e}")
            return None

    def _cache_questions(self, content_hash: str, questions: List[Question]):
        """Cache generated questions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            questions_data = [asdict(q) for q in questions]

            cursor.execute(
                "INSERT OR REPLACE INTO question_cache VALUES (?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    content_hash,
                    json.dumps(questions_data),
                    datetime.now().isoformat(),
                    0
                )
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error caching questions: {e}")

    def _save_question(self, question: Question):
        """Save question to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO questions
                (id, course_id, concept_id, question_type, question_text, correct_answer,
                 options, explanation, difficulty, bloom_level, context_tags,
                 source_material, created_at, last_used, usage_count,
                 success_rate, average_response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                question.id, question.course_id, question.concept_id, question.question_type,
                question.question_text, str(question.correct_answer), json.dumps(question.options),
                question.explanation, question.difficulty, question.bloom_level,
                json.dumps(question.context_tags), question.source_material,
                question.created_at.isoformat(),
                question.last_used.isoformat() if question.last_used else None,
                question.usage_count, question.success_rate, question.average_response_time
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error saving question: {e}")

    def get_adaptive_questions(
        self,
        course_id: str,
        difficulty_target: float = 0.5,
        question_types: List[str] = None,
        num_questions: int = 10,
        bloom_levels: List[str] = None
    ) -> List[Question]:
        """Get questions adapted to user performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build query with adaptive logic
            query = "SELECT * FROM questions WHERE course_id = ?"
            params = [course_id]

            if difficulty_target:
                query += " AND difficulty BETWEEN ? AND ?"
                params.extend([max(0.0, difficulty_target - 0.1), min(1.0, difficulty_target + 0.1)])

            if question_types:
                placeholders = ','.join(['?' for _ in question_types])
                query += f" AND question_type IN ({placeholders})"
                params.extend(question_types)

            query += " ORDER BY (success_rate + usage_count) DESC, RANDOM() LIMIT ?"
            params.append(num_questions)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            questions = []
            for row in rows:
                question_data = {
                    'id': row[0],
                    'course_id': row[1],
                    'concept_id': row[2],
                    'question_type': row[3],
                    'question_text': row[4],
                    'correct_answer': row[5],
                    'options': json.loads(row[6]) if row[6] else [],
                    'explanation': row[7],
                    'difficulty': row[8],
                    'bloom_level': row[9],
                    'context_tags': json.loads(row[10]) if row[10] else [],
                    'source_material': row[11],
                    'created_at': datetime.fromisoformat(row[12]),
                    'last_used': datetime.fromisoformat(row[13]) if row[13] else None,
                    'usage_count': row[14],
                    'success_rate': row[15],
                    'average_response_time': row[16]
                }
                questions.append(Question(**question_data))

            return questions

        except Exception as e:
            print(f"Error getting adaptive questions: {e}")
            return []

    def record_question_attempt(
        self,
        question_id: str,
        user_answer: str,
        is_correct: bool,
        response_time_ms: int,
        difficulty_rating: int = None,
        confidence_rating: int = None
    ):
        """Record a question attempt for analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Record attempt
            cursor.execute("""
                INSERT INTO question_attempts
                (id, question_id, user_answer, is_correct, response_time_ms, attempted_at,
                 difficulty_rating, confidence_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), question_id, user_answer, is_correct, response_time_ms,
                datetime.now().isoformat(), difficulty_rating, confidence_rating
            ))

            # Update question statistics
            cursor.execute("""
                UPDATE questions
                SET usage_count = usage_count + 1,
                    last_used = ?,
                    success_rate = (
                        (success_rate * (usage_count - 1) + (1 if is_correct else 0)) / usage_count
                    ),
                    average_response_time = (
                        (average_response_time * (usage_count - 1) + response_time_ms) / usage_count
                    )
                WHERE id = ?
            """, (datetime.now().isoformat(), question_id))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error recording question attempt: {e}")

    def get_question_analytics(
        self,
        course_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive question analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            since_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Question statistics
            cursor.execute("""
                SELECT COUNT(*) as total_questions,
                       COUNT(DISTINCT question_type) as unique_types,
                       AVG(difficulty) as avg_difficulty,
                       AVG(success_rate) as avg_success_rate,
                       AVG(average_response_time) as avg_response_time
                FROM questions WHERE course_id = ?
            """, (course_id,))
            question_stats = cursor.fetchone()

            # Attempt statistics
            cursor.execute("""
                SELECT COUNT(*) as total_attempts,
                       AVG(CASE WHEN is_correct THEN 1 ELSE 0 END) as avg_accuracy,
                       AVG(response_time_ms) as avg_time,
                       COUNT(DISTINCT question_id) as unique_questions_attempted
                FROM question_attempts qa
                JOIN questions q ON qa.question_id = q.id
                WHERE q.course_id = ? AND qa.attempted_at >= ?
            """, (course_id, since_date))
            attempt_stats = cursor.fetchone()

            # Type distribution
            cursor.execute("""
                SELECT question_type, COUNT(*) as count
                FROM questions WHERE course_id = ?
                GROUP BY question_type
            """, (course_id,))
            type_distribution = dict(cursor.fetchall())

            # Bloom level distribution
            cursor.execute("""
                SELECT bloom_level, COUNT(*) as count
                FROM questions WHERE course_id = ?
                GROUP BY bloom_level
            """, (course_id,))
            bloom_distribution = dict(cursor.fetchall())

            conn.close()

            return {
                "period_days": days,
                "question_statistics": {
                    "total_questions": question_stats[0] or 0,
                    "unique_types": question_stats[1] or 0,
                    "avg_difficulty": round(question_stats[2] or 0, 2),
                    "avg_success_rate": round(question_stats[3] or 0, 2),
                    "avg_response_time": round(question_stats[4] or 0, 2)
                },
                "attempt_statistics": {
                    "total_attempts": attempt_stats[0] or 0,
                    "avg_accuracy": round(attempt_stats[1] or 0, 2),
                    "avg_time_ms": round(attempt_stats[2] or 0, 2),
                    "unique_questions_attempted": attempt_stats[3] or 0
                },
                "type_distribution": type_distribution,
                "bloom_distribution": bloom_distribution
            }

        except Exception as e:
            print(f"Error getting question analytics: {e}")
            return {}

# Global instance
active_recall_engine = ActiveRecallEngine()