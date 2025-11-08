"""
Adaptive Learning Service
Sistema completo di adaptive learning che analizza pattern utente
e personalizza l'esperienza di apprendimento
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import json
import uuid
import statistics

class LearningStyle(str, Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MIXED = "mixed"

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class LearningPace(str, Enum):
    SLOW = "slow"      # Più tempo, più ripetizioni
    NORMAL = "normal"  # Tempo standard
    FAST = "fast"      # Meno tempo, meno ripetizioni
    ADAPTIVE = "adaptive"  # Si adatta al topic

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    course_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Caratteristiche apprendimento
    learning_style: LearningStyle = LearningStyle.MIXED
    preferred_difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    learning_pace: LearningPace = LearningPace.NORMAL

    # Pattern comportamentali
    preferred_session_length: int = 30  # minuti
    best_study_times: List[str] = []   # es. ["morning", "evening"]
    preferred_content_types: List[str] = []  # es. ["video", "text", "exercises"]
    interaction_preferences: Dict[str, Any] = {}

    # Analytics apprendimento
    strength_areas: List[str] = []
    improvement_areas: List[str] = []
    mastery_levels: Dict[str, int] = {}  # topic -> livello (1-5)
    confidence_levels: Dict[str, float] = {}  # topic -> confidenza (0-1)

    # Pattern temporali
    study_frequency: float = 1.0  # sessioni per giorno
    average_session_duration: float = 25.0  # minuti
    retention_rate: float = 0.8  # tasso di ritenzione
    forgetting_curve_factor: float = 0.2  # quanto velocemente dimentica

    # Preferenze AI
    ai_response_style: str = "detailed"  # concise, detailed, conversational
    question_complexity_preference: str = "gradual"  # simple, gradual, complex
    example_type_preference: str = "mixed"  # real_world, academic, simplified

class AdaptiveLearningService:
    """
    Servizio principale per adaptive learning
    """

    def __init__(self, db_service, ai_service, analytics_service):
        self.db = db_service
        self.ai = ai_service
        self.analytics = analytics_service

    async def analyze_user_behavior(self, user_id: str, course_id: str,
                                  time_window_days: int = 30) -> UserProfile:
        """
        Analizza comportamento utente e crea/aggiorna profilo
        """
        # Raccolta dati
        behavior_data = await self._collect_behavior_data(
            user_id, course_id, time_window_days
        )

        # Analisi pattern
        profile_updates = await self._analyze_learning_patterns(behavior_data)

        # Carica profilo esistente o creane uno nuovo
        existing_profile = await self.db.get_user_profile(user_id, course_id)

        if existing_profile:
            # Aggiorna profilo esistente
            updated_profile = await self._update_profile(existing_profile, profile_updates)
        else:
            # Crea nuovo profilo
            updated_profile = UserProfile(
                user_id=user_id,
                course_id=course_id,
                **profile_updates
            )

        # Salva profilo aggiornato
        await self.db.save_user_profile(updated_profile)

        return updated_profile

    async def get_personalized_recommendations(self, user_id: str, course_id: str,
                                             current_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Genera raccomandazioni personalizzate basate su profilo
        """
        profile = await self.db.get_user_profile(user_id, course_id)
        if not profile:
            # Crea profilo base se non esiste
            profile = await self.analyze_user_behavior(user_id, course_id)

        recommendations = {
            "study_suggestions": [],
            "content_recommendations": [],
            "difficulty_adjustments": [],
            "learning_optimization": []
        }

        # Suggerimenti basati su aree di miglioramento
        for area in profile.improvement_areas:
            suggestions = await self._generate_area_improvement_suggestions(area, profile)
            recommendations["study_suggestions"].extend(suggestions)

        # Suggerimenti basati su stile di apprendimento
        style_suggestions = await self._generate_style_based_suggestions(profile)
        recommendations["learning_optimization"].extend(style_suggestions)

        # Contenuti raccomandati basati su mastery levels
        content_recs = await self._generate_content_recommendations(profile, current_context)
        recommendations["content_recommendations"] = content_recs

        # Aggiustamenti difficoltà
        difficulty_recs = await self._generate_difficulty_adjustments(profile)
        recommendations["difficulty_adjustments"] = difficulty_recs

        return recommendations

    async def adapt_content_difficulty(self, user_id: str, course_id: str,
                                     content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adatta difficoltà contenuto basandosi su profilo utente
        """
        profile = await self.db.get_user_profile(user_id, course_id)
        if not profile:
            return content

        adapted_content = content.copy()

        # Analizza difficoltà attuale contenuto
        current_difficulty = await self._analyze_content_difficulty(content)
        target_difficulty = await self._calculate_target_difficulty(profile, content)

        # Adatta contenuto se necessario
        if abs(current_difficulty - target_difficulty) > 0.3:
            adapted_content = await self._adjust_content_difficulty(
                content, current_difficulty, target_difficulty, profile
            )

        # Personalizza stile presentazione
        adapted_content = await self._personalize_content_style(adapted_content, profile)

        return adapted_content

    async def track_learning_progress(self, user_id: str, course_id: str,
                                    learning_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traccia evento di apprendimento e aggiorna profilo
        """
        # Estrai informazioni dall'evento
        event_type = learning_event.get("type")  # "quiz_completed", "note_taken", "chat_session"
        performance = learning_event.get("performance", {})  # score, accuracy, time_spent
        topics = learning_event.get("topics", [])
        difficulty = learning_event.get("difficulty", "intermediate")

        # Aggiorna statistiche immediate
        await self._update_immediate_stats(user_id, course_id, learning_event)

        # Aggiorna mastery levels per topic
        await self._update_mastery_levels(user_id, course_id, topics, performance)

        # Aggiorna confidence levels
        await self._update_confidence_levels(user_id, course_id, topics, performance)

        # Regola profilo se necessario
        profile = await self.db.get_user_profile(user_id, course_id)
        if profile:
            await self._adjust_profile_based_on_performance(profile, learning_event)

        # Genera feedback immediato
        feedback = await self._generate_learning_feedback(profile, learning_event)

        return {
            "feedback": feedback,
            "updated_mastery": profile.mastery_levels if profile else {},
            "recommendations": await self._get_immediate_recommendations(learning_event, profile)
        }

    async def generate_spaced_repetition_schedule(self, user_id: str, course_id: str) -> List[Dict[str, Any]]:
        """
        Genera schedule per spaced repetition basato su profilo utente
        """
        profile = await self.db.get_user_profile(user_id, course_id)
        if not profile:
            return []

        # Recupera materiali da ripassare
        materials_to_review = await self._get_materials_for_review(user_id, course_id)

        # Calcola intervalli ottimali basati su forgetting curve
        schedule = []
        for material in materials_to_review:
            optimal_interval = await self._calculate_optimal_review_interval(
                material, profile
            )

            if optimal_interval:
                schedule_item = {
                    "material_id": material["id"],
                    "material_type": material["type"],
                    "topic": material["topic"],
                    "current_mastery": material.get("mastery_level", 1),
                    "optimal_review_time": optimal_interval["next_review"],
                    "priority": optimal_interval["priority"],
                    "estimated_duration": optimal_interval["duration"]
                }
                schedule.append(schedule_item)

        # Ordina per priorità e tempo
        schedule.sort(key=lambda x: (x["priority"], x["optimal_review_time"]))

        return schedule[:20]  # Top 20 items

    async def _collect_behavior_data(self, user_id: str, course_id: str,
                                   time_window_days: int) -> Dict[str, Any]:
        """
        Raccoglie dati comportamentali utente
        """
        cutoff_date = datetime.now() - timedelta(days=time_window_days)

        # Chat sessions
        chat_sessions = await self.analytics.get_chat_sessions(user_id, course_id, cutoff_date)

        # Note prese
        notes = await self.analytics.get_user_notes(user_id, course_id, cutoff_date)

        # Quiz completati
        quizzes = await self.analytics.get_quiz_results(user_id, course_id, cutoff_date)

        # Annotazioni PDF
        annotations = await self.analytics.get_pdf_annotations(user_id, course_id, cutoff_date)

        # Sessioni di studio
        study_sessions = await self.analytics.get_study_sessions(user_id, course_id, cutoff_date)

        return {
            "chat_sessions": chat_sessions,
            "notes": notes,
            "quizzes": quizzes,
            "annotations": annotations,
            "study_sessions": study_sessions,
            "time_window_days": time_window_days
        }

    async def _analyze_learning_patterns(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizza pattern dai dati comportamentali
        """
        patterns = {}

        # Analisi sessioni chat
        chat_sessions = behavior_data.get("chat_sessions", [])
        if chat_sessions:
            patterns.update(await self._analyze_chat_patterns(chat_sessions))

        # Analisi note
        notes = behavior_data.get("notes", [])
        if notes:
            patterns.update(await self._analyze_note_patterns(notes))

        # Analisi quiz
        quizzes = behavior_data.get("quizzes", [])
        if quizzes:
            patterns.update(await self._analyze_quiz_patterns(quizzes))

        # Analisi sessioni studio
        study_sessions = behavior_data.get("study_sessions", [])
        if study_sessions:
            patterns.update(await self._analyze_study_session_patterns(study_sessions))

        return patterns

    async def _analyze_chat_patterns(self, chat_sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analizza pattern delle chat sessions
        """
        if not chat_sessions:
            return {}

        # Lunghezza media sessioni
        durations = [s.get("duration_minutes", 0) for s in chat_sessions]
        avg_duration = statistics.mean(durations) if durations else 0

        # Orari preferiti
        hours = [datetime.fromisoformat(s["created_at"]).hour for s in chat_sessions]
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        preferred_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        # Topic frequenti
        all_topics = []
        for session in chat_sessions:
            all_topics.extend(session.get("topics", []))

        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        frequent_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Stile interazione
        message_count = sum(s.get("message_count", 0) for s in chat_sessions)
        session_count = len(chat_sessions)
        avg_messages_per_session = message_count / session_count if session_count > 0 else 0

        interaction_style = "conversational"
        if avg_messages_per_session > 15:
            interaction_style = "detailed"
        elif avg_messages_per_session < 5:
            interaction_style = "concise"

        return {
            "preferred_session_length": int(avg_duration),
            "best_study_hours": [str(h) for h, _ in preferred_hours],
            "preferred_topics": [t for t, _ in frequent_topics],
            "interaction_preferences": {
                "style": interaction_style,
                "avg_messages_per_session": avg_messages_per_session
            }
        }

    async def _analyze_note_patterns(self, notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analizza pattern delle note
        """
        if not notes:
            return {}

        # Contenuti per tipo
        note_types = {}
        for note in notes:
            note_type = note.get("type", "personal")
            note_types[note_type] = note_types.get(note_type, 0) + 1

        # Lunghezza media note
        content_lengths = [len(note.get("content", "")) for note in notes]
        avg_content_length = statistics.mean(content_lengths) if content_lengths else 0

        # Frequenza tag
        all_tags = []
        for note in notes:
            all_tags.extend(note.get("tags", []))

        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Stile preferito basato su tipi note
        learning_style = "mixed"
        if note_types.get("pdf_annotation", 0) > note_types.get("personal", 0):
            learning_style = "reading_writing"
        elif note_types.get("chat_note", 0) > len(notes) * 0.6:
            learning_style = "auditory"

        return {
            "learning_style": learning_style,
            "preferred_content_types": list(note_types.keys()),
            "average_note_length": avg_content_length,
            "frequent_tags": [tag for tag, _ in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
        }

    async def _analyze_quiz_patterns(self, quizzes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analizza pattern dei quiz
        """
        if not quizzes:
            return {}

        # Performance scores
        scores = [q.get("score", 0) for q in quizzes if q.get("score") is not None]
        avg_score = statistics.mean(scores) if scores else 0

        # Aree di forza e miglioramento
        topic_performance = {}
        for quiz in quizzes:
            topic = quiz.get("topic", "general")
            score = quiz.get("score", 0)
            if topic not in topic_performance:
                topic_performance[topic] = []
            topic_performance[topic].append(score)

        strength_areas = []
        improvement_areas = []

        for topic, topic_scores in topic_performance.items():
            avg_topic_score = statistics.mean(topic_scores)
            if avg_topic_score >= 0.8:
                strength_areas.append(topic)
            elif avg_topic_score <= 0.5:
                improvement_areas.append(topic)

        # Livello difficoltà preferito
        difficulty_counts = {}
        for quiz in quizzes:
            diff = quiz.get("difficulty", "intermediate")
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

        preferred_difficulty = max(difficulty_counts.items(), key=lambda x: x[1])[0] if difficulty_counts else "intermediate"

        return {
            "preferred_difficulty": preferred_difficulty,
            "strength_areas": strength_areas,
            "improvement_areas": improvement_areas,
            "average_quiz_score": avg_score,
            "topic_performance": {topic: statistics.mean(scores) for topic, scores in topic_performance.items()}
        }

    async def _analyze_study_session_patterns(self, study_sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analizza pattern delle sessioni di studio
        """
        if not study_sessions:
            return {}

        # Durata media
        durations = [s.get("duration_minutes", 0) for s in study_sessions]
        avg_duration = statistics.mean(durations) if durations else 0

        # Frequenza studio
        date_counts = {}
        for session in study_sessions:
            date = datetime.fromisoformat(session["created_at"]).date()
            date_counts[date] = date_counts.get(date, 0) + 1

        # Calcola frequenza giornaliera
        total_days = (datetime.now().date() - min(date_counts.keys())).days
        study_frequency = len(date_counts) / total_days if total_days > 0 else 0

        # Ritmo apprendimento
        pace = "normal"
        if study_frequency < 0.3:
            pace = "slow"
        elif study_frequency > 1.5:
            pace = "fast"

        return {
            "learning_pace": pace,
            "study_frequency": study_frequency,
            "average_session_duration": avg_duration,
            "total_study_days": len(date_counts)
        }

    async def _update_profile(self, existing_profile: UserProfile,
                            updates: Dict[str, Any]) -> UserProfile:
        """
        Aggiorna profilo esistente con nuove analisi
        """
        # Aggiorna campi esistenti con strategia di media mobile
        for key, value in updates.items():
            if hasattr(existing_profile, key):
                current_value = getattr(existing_profile, key)
                setattr(existing_profile, key, self._merge_profile_values(key, current_value, value))

        existing_profile.updated_at = datetime.now()
        return existing_profile

    def _merge_profile_values(self, field: str, current: Any, new: Any) -> Any:
        """
        Unisce valori profilo usando strategie appropriate per ogni campo
        """
        if field in ["strength_areas", "improvement_areas", "preferred_topics"]:
            # Unisci liste, rimuovi duplicati
            if isinstance(current, list) and isinstance(new, list):
                return list(set(current + new))[:10]  # Max 10 items

        elif field in ["preferred_session_length", "average_session_duration"]:
            # Media mobile
            if isinstance(current, (int, float)) and isinstance(new, (int, float)):
                return int((current * 0.7 + new * 0.3))

        elif field == "learning_style":
            # Cambia solo se nuova preferenza è forte
            return new if new != "mixed" else current

        return new

    async def _generate_area_improvement_suggestions(self, area: str,
                                                   profile: UserProfile) -> List[str]:
        """
        Genera suggerimenti per aree di miglioramento
        """
        suggestions = []

        # Adatta suggerimenti in base allo stile di apprendimento
        if profile.learning_style == LearningStyle.VISUAL:
            suggestions.extend([
                f"📊 Guarda video e diagrammi su {area}",
                f"🎨 Crea mappe concettuali per {area}",
                f"📹 Cerca visualizzazioni interattive su {area}"
            ])
        elif profile.learning_style == LearningStyle.AUDITORY:
            suggestions.extend([
                f"🎧 Ascolta podcast o lezioni su {area}",
                f"💬 Discuti {area} con compagni di studio",
                f"🗣️ Spiega {area} a voce alta"
            ])
        elif profile.learning_style == LearningStyle.READING_WRITING:
            suggestions.extend([
                f"📚 Leggi articoli dettagliati su {area}",
                f"✍️ Scrivi riassunti su {area}",
                f"📝 Prendi note dettagliate durante lo studio"
            ])

        # Aggiungi suggerimenti basati sulla difficoltà
        if profile.preferred_difficulty in [DifficultyLevel.BEGINNER, DifficultyLevel.ELEMENTARY]:
            suggestions.append(f"🔖 Inizia con materiali base su {area}")

        return suggestions[:4]  # Max 4 suggerimenti

    async def _generate_style_based_suggestions(self, profile: UserProfile) -> List[str]:
        """
        Genera suggerimenti basati su stile di apprendimento
        """
        suggestions = []

        if profile.learning_style == LearningStyle.VISUAL:
            suggestions.extend([
                "🎨 Usa colori diversi per evidenziare concetti",
                "📊 Trasforma testi in diagrammi e flowchart",
                "🖼️ Usa immagini e visualizzazioni per memorizzare"
            ])
        elif profile.learning_style == LearningStyle.AUDITORY:
            suggestions.extend([
                "🎧 Usa tecniche di ripetizione a voce",
                "🎵 Crea mnemonici sonori o rime",
                "👥 Partecipa a gruppi di studio vocali"
            ])
        elif profile.learning_style == LearningStyle.KINESTHETIC:
            suggestions.extend([
                "🤏 Usa esempi pratici e applicazioni reali",
                "✋ Fai esperimenti e progetti pratici",
                "🚶 Muoviti mentre studi (passeggia, ecc.)"
            ])

        return suggestions

    async def _generate_content_recommendations(self, profile: UserProfile,
                                              current_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Genera raccomandazioni contenuto personalizzate
        """
        recommendations = []

        # Basato su aree di miglioramento
        for area in profile.improvement_areas[:3]:
            recommendations.append({
                "type": "remedial_content",
                "topic": area,
                "priority": "high",
                "suggested_format": profile.learning_style.value,
                "difficulty": profile.preferred_difficulty.value
            })

        # Basato su forza aree (contenuti avanzati)
        for area in profile.strength_areas[:2]:
            recommendations.append({
                "type": "advanced_content",
                "topic": area,
                "priority": "medium",
                "suggested_format": profile.learning_style.value,
                "difficulty": "advanced"
            })

        return recommendations

    async def _generate_difficulty_adjustments(self, profile: UserProfile) -> List[str]:
        """
        Genera suggerimenti per aggiustare difficoltà
        """
        adjustments = []

        if profile.preferred_difficulty in [DifficultyLevel.BEGINNER, DifficultyLevel.ELEMENTARY]:
            adjustments.extend([
                "📖 Inizia con concetti base prima di passare a complessi",
                "🔄 Usa ripetizioni spaziate per rafforzare fondamentali",
                "📝 Prendi note dettagliate sui concetti iniziali"
            ])
        elif profile.preferred_difficulty in [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]:
            adjustments.extend([
                "🎯 Sfìdati con problemi complessi e applicazioni reali",
                "🔗 Esplora collegamenti interdisciplinari",
                "📚 Cerca materiali di ricerca e approfondimenti"
            ])

        return adjustments

# Database service per adaptive learning
class AdaptiveLearningDBService:
    """
    Servizio database per persistenza profili adaptive learning
    """

    async def save_user_profile(self, profile: UserProfile):
        """Salva profilo utente"""
        pass

    async def get_user_profile(self, user_id: str, course_id: str) -> Optional[UserProfile]:
        """Recupera profilo utente"""
        pass

    async def update_user_profile(self, profile: UserProfile):
        """Aggiorna profilo utente"""
        pass

    async def delete_user_profile(self, user_id: str, course_id: str) -> bool:
        """Elimina profilo utente"""
        pass