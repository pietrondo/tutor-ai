import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class StudyTracker:
    def __init__(self):
        self.tracking_dir = "data/tracking"
        self.sessions_file = os.path.join(self.tracking_dir, "study_sessions.json")
        self.progress_file = os.path.join(self.tracking_dir, "progress.json")
        self.ensure_tracking_directory()

    def ensure_tracking_directory(self):
        """Ensure the tracking directory and files exist"""
        os.makedirs(self.tracking_dir, exist_ok=True)

        # Initialize sessions file
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'w') as f:
                json.dump([], f)

        # Initialize progress file
        if not os.path.exists(self.progress_file):
            with open(self.progress_file, 'w') as f:
                json.dump({}, f)

    def track_interaction(self, course_id: str, session_id: str = None, question: str = "", answer: str = "") -> str:
        """Track a chat interaction within a study session"""
        try:
            # Get or create session ID
            if not session_id:
                session_id = str(uuid.uuid4())

            # Load existing sessions
            sessions = self.get_sessions_raw()

            # Find or create session
            session = next((s for s in sessions if s["id"] == session_id), None)
            if not session:
                session = {
                    "id": session_id,
                    "course_id": course_id,
                    "start_time": datetime.now().isoformat(),
                    "interactions": [],
                    "topics_studied": set(),
                    "duration_minutes": 0
                }
                sessions.append(session)

            # Add interaction
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer": answer,
                "type": "chat"
            }
            session["interactions"].append(interaction)

            # Extract topics from question (simple keyword extraction)
            topics = self.extract_topics(question)
            session["topics_studied"].update(topics)

            # Update session end time
            session["last_interaction"] = datetime.now().isoformat()

            # Save sessions
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2)

            # Update progress
            self.update_progress(course_id, session_id, topics)

            return session_id

        except Exception as e:
            print(f"Error tracking interaction: {e}")
            return session_id

    def record_study_session(self, session_data: Dict[str, Any]) -> str:
        """Record a completed study session"""
        try:
            sessions = self.get_sessions_raw()

            new_session = {
                "id": str(uuid.uuid4()),
                "course_id": session_data["course_id"],
                "start_time": datetime.now().isoformat(),
                "end_time": (datetime.now() + timedelta(minutes=session_data["duration_minutes"])).isoformat(),
                "duration_minutes": session_data["duration_minutes"],
                "topics_studied": session_data["topics_studied"],
                "interactions": [],
                "type": "manual"
            }

            sessions.append(new_session)

            # Save sessions
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2)

            # Update progress
            self.update_progress(session_data["course_id"], new_session["id"], session_data["topics_studied"])

            return new_session["id"]

        except Exception as e:
            print(f"Error recording study session: {e}")
            raise Exception(f"Error recording study session: {e}")

    def get_sessions_raw(self) -> List[Dict[str, Any]]:
        """Get raw sessions data from file"""
        try:
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def get_progress(self, course_id: str) -> Dict[str, Any]:
        """Get study progress for a specific course"""
        try:
            # Load progress data
            with open(self.progress_file, 'r') as f:
                progress_data = json.load(f)

            if course_id not in progress_data:
                return {
                    "course_id": course_id,
                    "total_sessions": 0,
                    "total_study_time": 0,
                    "topics_covered": [],
                    "last_study_date": None,
                    "streak_days": 0,
                    "weekly_goal": 7,  # hours
                    "weekly_progress": 0
                }

            progress = progress_data[course_id]

            # Calculate current streak
            progress["streak_days"] = self.calculate_streak(course_id)

            # Calculate weekly progress
            progress["weekly_progress"] = self.get_weekly_study_time(course_id)

            return progress

        except Exception as e:
            print(f"Error getting progress: {e}")
            return {
                "course_id": course_id,
                "error": str(e),
                "total_sessions": 0,
                "total_study_time": 0
            }

    def update_progress(self, course_id: str, session_id: str, topics: List[str]):
        """Update progress data after a session"""
        try:
            # Load existing progress
            with open(self.progress_file, 'r') as f:
                progress_data = json.load(f)

            # Initialize course progress if not exists
            if course_id not in progress_data:
                progress_data[course_id] = {
                    "total_sessions": 0,
                    "total_study_time": 0,
                    "topics_covered": [],
                    "last_study_date": None,
                    "created_at": datetime.now().isoformat()
                }

            progress = progress_data[course_id]
            progress["total_sessions"] += 1
            progress["last_study_date"] = datetime.now().isoformat()

            # Add new topics
            for topic in topics:
                if topic not in progress["topics_covered"]:
                    progress["topics_covered"].append(topic)

            # Calculate session duration (if it's a chat session)
            sessions = self.get_sessions_raw()
            session = next((s for s in sessions if s["id"] == session_id), None)
            if session and session.get("duration_minutes"):
                progress["total_study_time"] += session["duration_minutes"]

            # Save progress
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)

        except Exception as e:
            print(f"Error updating progress: {e}")

    def extract_topics(self, text: str) -> List[str]:
        """Extract topics from text (simple keyword extraction)"""
        # Simple keyword extraction - can be enhanced with NLP
        common_academic_terms = [
            "algoritmo", "funzione", "derivata", "integrale", "equazione",
            "matrice", "vettore", "probabilità", "statistica", "teorema",
            "definizione", "esempio", "applicazione", "proprietà", "metodo"
        ]

        text_lower = text.lower()
        found_topics = []

        for term in common_academic_terms:
            if term in text_lower:
                found_topics.append(term)

        # Also extract words in quotes as potential topics
        import re
        quoted_words = re.findall(r'"([^"]+)"', text)
        found_topics.extend(quoted_words)

        return list(set(found_topics))

    def calculate_streak(self, course_id: str) -> int:
        """Calculate current study streak for a course"""
        try:
            sessions = self.get_sessions_raw()
            course_sessions = [s for s in sessions if s["course_id"] == course_id]

            if not course_sessions:
                return 0

            # Sort sessions by date
            course_sessions.sort(key=lambda x: x.get("start_time", ""))

            # Calculate streak
            streak = 0
            current_date = datetime.now().date()

            # Check if studied today
            studied_today = any(
                datetime.fromisoformat(s["start_time"]).date() == current_date
                for s in course_sessions
            )

            if studied_today:
                streak = 1
                current_date -= timedelta(days=1)
            else:
                # Check if studied yesterday
                studied_yesterday = any(
                    datetime.fromisoformat(s["start_time"]).date() == current_date - timedelta(days=1)
                    for s in course_sessions
                )
                if not studied_yesterday:
                    return 0
                streak = 1
                current_date -= timedelta(days=2)

            # Count consecutive days
            while current_date >= datetime.now().date() - timedelta(days=365):
                studied_on_date = any(
                    datetime.fromisoformat(s["start_time"]).date() == current_date
                    for s in course_sessions
                )
                if studied_on_date:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break

            return streak

        except Exception as e:
            print(f"Error calculating streak: {e}")
            return 0

    def get_weekly_study_time(self, course_id: str) -> float:
        """Get total study time for the current week (in hours)"""
        try:
            sessions = self.get_sessions_raw()
            course_sessions = [s for s in sessions if s["course_id"] == course_id]

            # Get current week's start (Monday)
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())

            weekly_time = 0
            for session in course_sessions:
                session_date = datetime.fromisoformat(session["start_time"]).date()
                if session_date >= week_start:
                    weekly_time += session.get("duration_minutes", 0)

            return weekly_time / 60.0  # Convert to hours

        except Exception as e:
            print(f"Error calculating weekly study time: {e}")
            return 0.0

    def track_timer_session(self, session_type: str, duration_minutes: int, course_id: str = None) -> str:
        """Track a Pomodoro timer session"""
        try:
            session_id = str(uuid.uuid4())

            sessions = self.get_sessions_raw()

            timer_session = {
                "id": session_id,
                "course_id": course_id or "general",
                "start_time": (datetime.now() - timedelta(minutes=duration_minutes)).isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_minutes": duration_minutes,
                "session_type": session_type,  # "work", "short_break", "long_break"
                "topics_studied": [],
                "interactions": [],
                "type": "timer"
            }

            sessions.append(timer_session)

            # Save sessions
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2)

            # Update progress if it's a work session
            if session_type == "work" and course_id:
                self.update_progress(course_id, session_id, [])

            return session_id

        except Exception as e:
            print(f"Error tracking timer session: {e}")
            return session_id

    def get_comprehensive_analytics(self, course_id: str = None, days_range: int = 30) -> Dict[str, Any]:
        """Get comprehensive learning analytics with advanced metrics"""
        try:
            sessions = self.get_sessions_raw()

            # Filter by course if specified
            if course_id:
                sessions = [s for s in sessions if s["course_id"] == course_id]

            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days_range)
            recent_sessions = [
                s for s in sessions
                if datetime.fromisoformat(s["start_time"]) >= cutoff_date
            ]

            if not recent_sessions:
                return {"message": "No recent study activity found"}

            # Basic metrics
            total_sessions = len(recent_sessions)
            total_study_time = sum(s.get("duration_minutes", 0) for s in recent_sessions if s.get("session_type") == "work")
            total_break_time = sum(s.get("duration_minutes", 0) for s in recent_sessions if s.get("session_type") in ["short_break", "long_break"])

            # Session type breakdown
            work_sessions = [s for s in recent_sessions if s.get("session_type") == "work"]
            break_sessions = [s for s in recent_sessions if s.get("session_type") in ["short_break", "long_break"]]
            chat_sessions = [s for s in recent_sessions if s.get("type") == "chat"]

            # Time-based analytics
            study_hours_by_day = {}
            study_sessions_by_hour = {}
            productivity_by_hour = {}

            for session in work_sessions:
                session_date = datetime.fromisoformat(session["start_time"]).date()
                session_hour = datetime.fromisoformat(session["start_time"]).hour

                # Daily study hours
                date_str = session_date.isoformat()
                study_hours_by_day[date_str] = study_hours_by_day.get(date_str, 0) + session.get("duration_minutes", 0) / 60

                # Hourly patterns
                study_sessions_by_hour[session_hour] = study_sessions_by_hour.get(session_hour, 0) + 1

                # Productivity score (sessions per hour)
                if session_hour not in productivity_by_hour:
                    productivity_by_hour[session_hour] = {"sessions": 0, "total_time": 0}
                productivity_by_hour[session_hour]["sessions"] += 1
                productivity_by_hour[session_hour]["total_time"] += session.get("duration_minutes", 0)

            # Calculate productivity scores
            for hour, data in productivity_by_hour.items():
                avg_time = data["total_time"] / data["sessions"] if data["sessions"] > 0 else 0
                productivity_by_hour[hour] = {
                    "sessions": data["sessions"],
                    "average_duration": avg_time,
                    "productivity_score": min(100, (avg_time / 25) * 100)  # Optimal 25min sessions
                }

            # Weekly patterns
            study_by_weekday = {}
            for session in work_sessions:
                weekday = datetime.fromisoformat(session["start_time"]).strftime("%A")
                study_by_weekday[weekday] = study_by_weekday.get(weekday, 0) + 1

            # Focus metrics
            avg_focus_session = total_study_time / len(work_sessions) if work_sessions else 0
            focus_efficiency = min(100, (avg_focus_session / 25) * 100) if avg_focus_session > 0 else 0

            # Break compliance
            break_compliance = 0
            if work_sessions:
                expected_breaks = len(work_sessions)
                actual_breaks = len(break_sessions)
                break_compliance = min(100, (actual_breaks / expected_breaks) * 100)

            # Topic mastery (based on frequency)
            all_topics = []
            for session in recent_sessions:
                all_topics.extend(session.get("topics_studied", []))

            from collections import Counter
            topic_counts = Counter(all_topics)

            # Learning velocity (topics per week)
            weeks_studied = len(set(datetime.fromisoformat(s["start_time"]).isocalendar().week for s in recent_sessions))
            learning_velocity = len(topic_counts) / weeks_studied if weeks_studied > 0 else 0

            # Streak analytics
            current_streak = self.calculate_streak(course_id) if course_id else 0
            longest_streak = self.calculate_longest_streak(course_id)

            # Goal progress
            weekly_goal_hours = 7  # Default goal
            current_week_hours = study_hours_by_day.get(datetime.now().date().isoformat(), 0)
            weekly_progress = min(100, (current_week_hours / weekly_goal_hours) * 100)

            # Generate insights and recommendations
            insights = self.generate_study_insights({
                "total_sessions": total_sessions,
                "avg_focus_session": avg_focus_session,
                "focus_efficiency": focus_efficiency,
                "break_compliance": break_compliance,
                "productivity_by_hour": productivity_by_hour,
                "study_by_weekday": study_by_weekday,
                "learning_velocity": learning_velocity,
                "current_streak": current_streak
            })

            return {
                "period_days": days_range,
                "total_sessions": total_sessions,
                "work_sessions": len(work_sessions),
                "break_sessions": len(break_sessions),
                "chat_sessions": len(chat_sessions),

                "time_metrics": {
                    "total_study_hours": total_study_time / 60,
                    "total_break_hours": total_break_time / 60,
                    "average_focus_session": avg_focus_session,
                    "focus_efficiency": focus_efficiency,
                    "break_compliance": break_compliance
                },

                "patterns": {
                    "study_hours_by_day": study_hours_by_day,
                    "study_sessions_by_hour": study_sessions_by_hour,
                    "productivity_by_hour": productivity_by_hour,
                    "study_by_weekday": study_by_weekday
                },

                "learning_metrics": {
                    "unique_topics": len(topic_counts),
                    "topic_mastery": [{"topic": topic, "frequency": count, "mastery_level": min(5, count // 3)} for topic, count in topic_counts.most_common(10)],
                    "learning_velocity": learning_velocity,
                    "most_productive_hour": max(productivity_by_hour.items(), key=lambda x: x[1]["productivity_score"])[0] if productivity_by_hour else None
                },

                "streak_metrics": {
                    "current_streak": current_streak,
                    "longest_streak": longest_streak,
                    "weekly_goal_progress": weekly_progress
                },

                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error getting comprehensive analytics: {e}")
            return {"error": str(e)}

    def calculate_longest_streak(self, course_id: str = None) -> int:
        """Calculate the longest study streak"""
        try:
            sessions = self.get_sessions_raw()
            if course_id:
                sessions = [s for s in sessions if s["course_id"] == course_id]

            if not sessions:
                return 0

            # Get unique study dates
            study_dates = set()
            for session in sessions:
                if session.get("session_type") == "work" or session.get("type") == "chat":
                    study_dates.add(datetime.fromisoformat(session["start_time"]).date())

            if not study_dates:
                return 0

            # Sort dates and find longest consecutive sequence
            sorted_dates = sorted(study_dates)

            longest_streak = 1
            current_streak = 1

            for i in range(1, len(sorted_dates)):
                if sorted_dates[i] == sorted_dates[i-1] + timedelta(days=1):
                    current_streak += 1
                    longest_streak = max(longest_streak, current_streak)
                else:
                    current_streak = 1

            return longest_streak

        except Exception as e:
            print(f"Error calculating longest streak: {e}")
            return 0

    def generate_study_insights(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable insights based on study metrics"""
        insights = []

        # Focus session insights
        avg_focus = metrics.get("avg_focus_session", 0)
        if avg_focus < 15:
            insights.append("Le tue sessioni di studio sono brevi. Prova ad aumentare gradualmente la durata per migliorare la concentrazione.")
        elif avg_focus > 35:
            insights.append("Le tue sessioni sono molto lunghe. Considera pause più frequenti per mantenere l'efficacia.")

        # Break compliance insights
        break_compliance = metrics.get("break_compliance", 0)
        if break_compliance < 50:
            insights.append("Stai saltando molte pause. Le pause regolari sono essenziali per il mantenimento della concentrazione.")

        # Productivity pattern insights
        productivity_by_hour = metrics.get("productivity_by_hour", {})
        if productivity_by_hour:
            best_hour = max(productivity_by_hour.items(), key=lambda x: x[1]["productivity_score"])[0]
            insights.append(f"La tua ora più produttiva è le {best_hour}:00. Sfrutta questo periodo per gli argomenti più difficili.")

        # Weekly pattern insights
        study_by_weekday = metrics.get("study_by_weekday", {})
        if study_by_weekday:
            least_productive_day = min(study_by_weekday.items(), key=lambda x: x[1])[0]
            insights.append(f"{least_productive_day} è il tuo giorno meno produttivo. Considera di riprogrammare o aggiungere incentivi.")

        # Learning velocity insights
        velocity = metrics.get("learning_velocity", 0)
        if velocity < 2:
            insights.append("Stai coprendo pochi argomenti a settimana. Prova a diversificare gli argomenti o aumentare la frequenza di studio.")

        # Streak insights
        current_streak = metrics.get("current_streak", 0)
        if current_streak >= 7:
            insights.append("Complimenti! Hai una streak di una settimana. Mantieni questa costanza.")
        elif current_streak >= 3:
            insights.append(f"Ottima costanza con {current_streak} giorni consecutivi. Continua così!")
        elif current_streak == 0:
            insights.append("Ricomincia a studiare oggi per costruire una nuova streak di apprendimento.")

        return insights

    def get_study_insights(self, course_id: str) -> Dict[str, Any]:
        """Get detailed insights about study patterns (legacy method)"""
        return self.get_comprehensive_analytics(course_id, days_range=30)