"""
Spaced Repetition Service
Enhanced SM-2 algorithm implementation for optimal learning scheduling
Based on latest cognitive science research (2024-2025)
"""

import os
import json
import uuid
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import sqlite3

@dataclass
class LearningCard:
    """Learning card with spaced repetition metadata"""
    id: str
    course_id: str
    concept_id: Optional[str]
    question: str
    answer: str
    card_type: str  # basic, cloze, concept, application
    difficulty: float  # 0.0-1.0
    ease_factor: float  # SM-2 ease factor
    interval_days: int
    repetitions: int
    next_review: datetime
    created_at: datetime
    last_reviewed: Optional[datetime] = None
    review_count: int = 0
    total_quality: float = 0.0  # Average quality rating
    context_tags: List[str] = None
    source_material: Optional[str] = None

    def __post_init__(self):
        if self.context_tags is None:
            self.context_tags = []

@dataclass
class ReviewSession:
    """Single card review session"""
    id: str
    card_id: str
    session_id: str
    quality_rating: int  # 0-5 (0=blackout, 5=perfect)
    response_time_ms: int
    reviewed_at: datetime
    previous_interval: int
    previous_ease_factor: float
    previous_repetitions: int

@dataclass
class StudySession:
    """Complete study session with multiple cards"""
    id: str
    course_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    cards_studied: int
    correct_reviews: int
    average_response_time: float
    session_type: str  # new_review, overdue, mixed

class SpacedRepetitionService:
    """Enhanced Spaced Repetition System with SM-2 algorithm and cognitive optimizations"""

    def __init__(self, db_path: str = "data/spaced_repetition.db"):
        self.db_path = db_path
        self.ensure_database()

        # SM-2 Algorithm parameters (enhanced based on 2024 research)
        self.MIN_EASE_FACTOR = 1.3
        self.MAX_EASE_FACTOR = 2.5
        self.DEFAULT_EASE_FACTOR = 2.5
        self.MIN_INTERVAL = 1
        self.MAX_INTERVAL = 36500  # ~100 years

        # Cognitive optimization parameters
        self.WRONG_ANSWER_PENALTY = 0.2
        self.SLOW_RESPONSE_PENALTY = 10000  # 10 seconds
        self.FAST_RESPONSE_BONUS = 3000  # 3 seconds
        self.DIFFICULTY_FACTOR_WEIGHT = 0.1

    def ensure_database(self):
        """Ensure database and tables exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Learning cards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_cards (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                concept_id TEXT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                card_type TEXT DEFAULT 'basic',
                difficulty REAL DEFAULT 0.0,
                ease_factor REAL DEFAULT 2.5,
                interval_days INTEGER DEFAULT 1,
                repetitions INTEGER DEFAULT 0,
                next_review TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_reviewed TEXT,
                review_count INTEGER DEFAULT 0,
                total_quality REAL DEFAULT 0.0,
                context_tags TEXT,
                source_material TEXT
            )
        """)

        # Review sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_sessions (
                id TEXT PRIMARY KEY,
                card_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                quality_rating INTEGER NOT NULL,
                response_time_ms INTEGER NOT NULL,
                reviewed_at TEXT NOT NULL,
                previous_interval INTEGER NOT NULL,
                previous_ease_factor REAL NOT NULL,
                previous_repetitions INTEGER NOT NULL,
                FOREIGN KEY (card_id) REFERENCES learning_cards (id)
            )
        """)

        # Study sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                cards_studied INTEGER DEFAULT 0,
                correct_reviews INTEGER DEFAULT 0,
                average_response_time REAL DEFAULT 0.0,
                session_type TEXT DEFAULT 'mixed'
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_next_review ON learning_cards(next_review)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_course_id ON learning_cards(course_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_card_id ON review_sessions(card_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_session_id ON review_sessions(session_id)")

        conn.commit()
        conn.close()

    def calculate_next_review_sm2(self, card: LearningCard, quality_rating: int,
                                 response_time_ms: int) -> Tuple[float, int, int]:
        """
        Enhanced SM-2 algorithm with cognitive optimizations
        Returns: (new_ease_factor, new_interval_days, new_repetitions)
        """
        # Base SM-2 calculation
        ease_factor = card.ease_factor
        repetitions = card.repetitions
        interval_days = card.interval_days

        # Apply cognitive penalties/bonuses
        cognitive_adjustment = self._calculate_cognitive_adjustment(
            quality_rating, response_time_ms, card.difficulty
        )

        quality_rating = max(0, min(5, quality_rating + cognitive_adjustment))

        if quality_rating < 3:
            # Failed review - reset card
            repetitions = 0
            interval_days = 1
            ease_factor = max(self.MIN_EASE_FACTOR, ease_factor - 0.2)
        else:
            # Successful review - advance card
            if repetitions == 0:
                interval_days = 1
            elif repetitions == 1:
                interval_days = 6
            else:
                interval_days = round(interval_days * ease_factor)

            # Update ease factor based on performance
            ease_factor += (0.1 - (5 - quality_rating) * (0.08 + (5 - quality_rating) * 0.02))
            ease_factor = max(self.MIN_EASE_FACTOR, min(self.MAX_EASE_FACTOR, ease_factor))

        repetitions += 1

        # Apply interval limits
        interval_days = max(self.MIN_INTERVAL, min(self.MAX_INTERVAL, interval_days))

        return ease_factor, interval_days, repetitions

    def _calculate_cognitive_adjustment(self, quality_rating: int, response_time_ms: int,
                                     difficulty: float) -> float:
        """Calculate cognitive adjustment based on response time and difficulty"""
        adjustment = 0.0

        # Response time adjustment
        if quality_rating >= 3:  # Only adjust for correct answers
            if response_time_ms > self.SLOW_RESPONSE_PENALTY:
                adjustment -= 0.2  # Penalize slow correct answers
            elif response_time_ms < self.FAST_RESPONSE_BONUS:
                adjustment += 0.1  # Bonus for fast correct answers

        # Difficulty adjustment
        if difficulty > 0.7 and quality_rating == 3:  # Hard card with just passing grade
            adjustment -= 0.1
        elif difficulty < 0.3 and quality_rating >= 4:  # Easy card with excellent performance
            adjustment += 0.1

        return adjustment

    def create_card(self, course_id: str, question: str, answer: str,
                    card_type: str = "basic", concept_id: str = None,
                    context_tags: List[str] = None, source_material: str = None) -> str:
        """Create a new learning card"""
        card_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Calculate initial difficulty based on content
        difficulty = self._estimate_card_difficulty(question, answer)

        card = LearningCard(
            id=card_id,
            course_id=course_id,
            concept_id=concept_id,
            question=question,
            answer=answer,
            card_type=card_type,
            difficulty=difficulty,
            ease_factor=self.DEFAULT_EASE_FACTOR,
            interval_days=1,
            repetitions=0,
            next_review=now,
            created_at=now,
            context_tags=context_tags or [],
            source_material=source_material
        )

        self._save_card(card)
        return card_id

    def _estimate_card_difficulty(self, question: str, answer: str) -> float:
        """Estimate card difficulty based on content analysis"""
        # Simple heuristic-based difficulty estimation
        question_words = len(question.split())
        answer_words = len(answer.split())
        total_words = question_words + answer_words

        # Factors that increase difficulty
        difficulty_factors = 0.0

        # Length factor
        if total_words > 100:
            difficulty_factors += 0.3
        elif total_words > 50:
            difficulty_factors += 0.2
        elif total_words < 10:
            difficulty_factors -= 0.1

        # Complex question indicators
        question_lower = question.lower()
        if any(word in question_lower for word in ['why', 'how', 'explain', 'analyze', 'compare']):
            difficulty_factors += 0.2

        # Technical content indicators
        technical_terms = ['formula', 'equation', 'theorem', 'algorithm', 'process', 'system']
        if any(term in question_lower or term in answer.lower() for term in technical_terms):
            difficulty_factors += 0.1

        # Normalize to 0-1 range
        difficulty = min(1.0, max(0.0, 0.3 + difficulty_factors))
        return difficulty

    def _save_card(self, card: LearningCard):
        """Save card to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO learning_cards
            (id, course_id, concept_id, question, answer, card_type, difficulty,
             ease_factor, interval_days, repetitions, next_review, created_at,
             last_reviewed, review_count, total_quality, context_tags, source_material)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            card.id, card.course_id, card.concept_id, card.question, card.answer,
            card.card_type, card.difficulty, card.ease_factor, card.interval_days,
            card.repetitions, card.next_review.isoformat(), card.created_at.isoformat(),
            card.last_reviewed.isoformat() if card.last_reviewed else None,
            card.review_count, card.total_quality, json.dumps(card.context_tags),
            card.source_material
        ))

        conn.commit()
        conn.close()

    def get_due_cards(self, course_id: str, limit: int = 20,
                     card_types: List[str] = None) -> List[LearningCard]:
        """Get cards due for review"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(timezone.utc).isoformat()

        query = """
            SELECT * FROM learning_cards
            WHERE course_id = ? AND next_review <= ?
        """
        params = [course_id, now]

        if card_types:
            placeholders = ','.join(['?' for _ in card_types])
            query += f" AND card_type IN ({placeholders})"
            params.extend(card_types)

        query += " ORDER BY next_review ASC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        cards = []
        for row in rows:
            cards.append(self._row_to_card(row))

        return cards

    def _row_to_card(self, row) -> LearningCard:
        """Convert database row to LearningCard object"""
        return LearningCard(
            id=row[0],
            course_id=row[1],
            concept_id=row[2],
            question=row[3],
            answer=row[4],
            card_type=row[5],
            difficulty=row[6],
            ease_factor=row[7],
            interval_days=row[8],
            repetitions=row[9],
            next_review=datetime.fromisoformat(row[10]),
            created_at=datetime.fromisoformat(row[11]),
            last_reviewed=datetime.fromisoformat(row[12]) if row[12] else None,
            review_count=row[13],
            total_quality=row[14],
            context_tags=json.loads(row[15]) if row[15] else [],
            source_material=row[16]
        )

    def review_card(self, card_id: str, quality_rating: int, response_time_ms: int,
                   session_id: str = None) -> Dict[str, Any]:
        """Process card review and update scheduling"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current card
        cursor.execute("SELECT * FROM learning_cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Card {card_id} not found")

        card = self._row_to_card(row)

        # Record previous state
        review_session = ReviewSession(
            id=str(uuid.uuid4()),
            card_id=card_id,
            session_id=session_id or str(uuid.uuid4()),
            quality_rating=quality_rating,
            response_time_ms=response_time_ms,
            reviewed_at=datetime.now(timezone.utc),
            previous_interval=card.interval_days,
            previous_ease_factor=card.ease_factor,
            previous_repetitions=card.repetitions
        )

        # Calculate next review
        new_ease, new_interval, new_repetitions = self.calculate_next_review_sm2(
            card, quality_rating, response_time_ms
        )

        # Update card
        next_review = datetime.now(timezone.utc) + timedelta(days=new_interval)

        # Update statistics
        total_reviews = card.review_count + 1
        total_quality = ((card.total_quality * card.review_count) + quality_rating) / total_reviews

        cursor.execute("""
            UPDATE learning_cards SET
                ease_factor = ?, interval_days = ?, repetitions = ?,
                next_review = ?, last_reviewed = ?, review_count = ?,
                total_quality = ?, difficulty = ?
            WHERE id = ?
        """, (
            new_ease, new_interval, new_repetitions, next_review.isoformat(),
            review_session.reviewed_at.isoformat(), total_reviews,
            total_quality, self._update_difficulty(card, quality_rating), card_id
        ))

        # Save review session
        cursor.execute("""
            INSERT INTO review_sessions
            (id, card_id, session_id, quality_rating, response_time_ms, reviewed_at,
             previous_interval, previous_ease_factor, previous_repetitions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            review_session.id, review_session.card_id, review_session.session_id,
            review_session.quality_rating, review_session.response_time_ms,
            review_session.reviewed_at.isoformat(), review_session.previous_interval,
            review_session.previous_ease_factor, review_session.previous_repetitions
        ))

        conn.commit()
        conn.close()

        return {
            "card_id": card_id,
            "next_review": next_review.isoformat(),
            "interval_days": new_interval,
            "ease_factor": new_ease,
            "repetitions": new_repetitions,
            "quality_rating": quality_rating,
            "review_session_id": review_session.id
        }

    def _update_difficulty(self, card: LearningCard, quality_rating: int) -> float:
        """Update card difficulty based on review performance"""
        if quality_rating >= 4:  # Good performance
            return max(0.0, card.difficulty - 0.05)
        elif quality_rating <= 2:  # Poor performance
            return min(1.0, card.difficulty + 0.1)
        return card.difficulty

    def get_learning_analytics(self, course_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive learning analytics for a course"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        # Card statistics
        cursor.execute("""
            SELECT COUNT(*) as total_cards,
                   COUNT(CASE WHEN next_review <= datetime('now') THEN 1 END) as due_cards,
                   AVG(difficulty) as avg_difficulty,
                   AVG(total_quality) as avg_quality
            FROM learning_cards WHERE course_id = ?
        """, (course_id,))
        card_stats = cursor.fetchone()

        # Review statistics
        cursor.execute("""
            SELECT COUNT(*) as total_reviews,
                   AVG(quality_rating) as avg_quality,
                   AVG(response_time_ms) as avg_response_time,
                   COUNT(CASE WHEN quality_rating >= 3 THEN 1 END) as correct_reviews
            FROM review_sessions rs
            JOIN learning_cards lc ON rs.card_id = lc.id
            WHERE lc.course_id = ? AND rs.reviewed_at >= ?
        """, (course_id, since_date))
        review_stats = cursor.fetchone()

        # Learning curve data
        cursor.execute("""
            SELECT DATE(reviewed_at) as review_date,
                   AVG(quality_rating) as daily_avg_quality,
                   COUNT(*) as daily_reviews
            FROM review_sessions rs
            JOIN learning_cards lc ON rs.card_id = lc.id
            WHERE lc.course_id = ? AND rs.reviewed_at >= ?
            GROUP BY DATE(reviewed_at)
            ORDER BY review_date
        """, (course_id, since_date))
        learning_curve = cursor.fetchall()

        conn.close()

        return {
            "period_days": days,
            "card_statistics": {
                "total_cards": card_stats[0] or 0,
                "due_cards": card_stats[1] or 0,
                "avg_difficulty": round(card_stats[2] or 0, 2),
                "avg_quality": round(card_stats[3] or 0, 2)
            },
            "review_statistics": {
                "total_reviews": review_stats[0] or 0,
                "avg_quality": round(review_stats[1] or 0, 2),
                "avg_response_time_ms": round(review_stats[2] or 0, 0),
                "correct_reviews": review_stats[3] or 0,
                "accuracy_rate": round((review_stats[3] or 0) / max(1, review_stats[0] or 0), 2)
            },
            "learning_curve": [
                {
                    "date": row[0],
                    "avg_quality": round(row[1] or 0, 2),
                    "reviews_count": row[2] or 0
                }
                for row in learning_curve
            ]
        }

    def generate_cards_from_content(self, course_id: str, content: str,
                                   source_material: str = None) -> List[str]:
        """Auto-generate learning cards from study content"""
        cards_created = []

        # Split content into chunks
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]

        for paragraph in paragraphs[:20]:  # Limit to prevent excessive generation
            # Generate question-answer pairs using LLM
            if len(paragraph) > 50:  # Only meaningful paragraphs
                try:
                    qa_pair = self._extract_qa_from_content(paragraph)
                    if qa_pair:
                        card_id = self.create_card(
                            course_id=course_id,
                            question=qa_pair["question"],
                            answer=qa_pair["answer"],
                            card_type="auto_generated",
                            context_tags=["auto_generated"],
                            source_material=source_material
                        )
                        cards_created.append(card_id)
                except Exception as e:
                    print(f"Error generating card from paragraph: {e}")
                    continue

        return cards_created

    def _extract_qa_from_content(self, content: str) -> Optional[Dict[str, str]]:
        """Extract question-answer pair from content using heuristics"""
        # This is a simplified version - in production, would use LLM
        sentences = content.split('.')

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue

            # Look for definitional content
            if any(indicator in sentence.lower() for indicator in ['is defined as', 'refers to', 'means']):
                question = f"What is {sentence.split()[0]}?"
                answer = sentence
                return {"question": question, "answer": answer}

        # Fallback: create generic question
        if len(content) > 100:
            question = f"Explain the key concept in this passage."
            answer = content
            return {"question": question, "answer": answer}

        return None

    def get_study_recommendations(self, course_id: str) -> Dict[str, Any]:
        """Get personalized study recommendations based on performance"""
        analytics = self.get_learning_analytics(course_id, days=14)

        recommendations = []

        # Accuracy-based recommendations
        if analytics["review_statistics"]["accuracy_rate"] < 0.7:
            recommendations.append({
                "type": "accuracy_low",
                "message": "Focus on cards with low accuracy. Consider reviewing fundamentals.",
                "priority": "high"
            })

        # Response time recommendations
        if analytics["review_statistics"]["avg_response_time_ms"] > 8000:
            recommendations.append({
                "type": "response_slow",
                "message": "Your response times are slow. Try to answer more quickly to strengthen recall.",
                "priority": "medium"
            })

        # Due cards recommendations
        if analytics["card_statistics"]["due_cards"] > 20:
            recommendations.append({
                "type": "many_due",
                "message": f"You have {analytics['card_statistics']['due_cards']} cards due. Consider shorter, more frequent sessions.",
                "priority": "high"
            })

        # New cards recommendations
        if analytics["card_statistics"]["total_cards"] < 50:
            recommendations.append({
                "type": "add_cards",
                "message": "Add more learning cards to improve your study coverage.",
                "priority": "medium"
            })

        return {
            "recommendations": recommendations,
            "optimal_session_size": self._calculate_optimal_session_size(analytics),
            "next_session_focus": self._determine_next_focus(analytics)
        }

    def _calculate_optimal_session_size(self, analytics: Dict[str, Any]) -> int:
        """Calculate optimal number of cards per session based on performance"""
        accuracy = analytics["review_statistics"]["accuracy_rate"]
        response_time = analytics["review_statistics"]["avg_response_time_ms"]

        # Adjust session size based on performance
        base_size = 20

        if accuracy < 0.7 or response_time > 10000:
            base_size = 15  # Smaller sessions for struggling learners
        elif accuracy > 0.9 and response_time < 3000:
            base_size = 30  # Larger sessions for strong performers

        return base_size

    def _determine_next_focus(self, analytics: Dict[str, Any]) -> str:
        """Determine focus area for next study session"""
        if analytics["card_statistics"]["due_cards"] > 0:
            return "due_cards"
        elif analytics["review_statistics"]["accuracy_rate"] < 0.8:
            return "difficult_cards"
        else:
            return "new_cards"

# Global instance
spaced_repetition_service = SpacedRepetitionService()