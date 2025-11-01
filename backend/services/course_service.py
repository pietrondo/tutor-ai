import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class CourseService:
    def __init__(self):
        self.courses_dir = "data/courses"
        self.courses_file = os.path.join(self.courses_dir, "courses.json")
        self.ensure_courses_directory()

    def ensure_courses_directory(self):
        """Ensure the courses directory and file exist"""
        os.makedirs(self.courses_dir, exist_ok=True)

        if not os.path.exists(self.courses_file):
            with open(self.courses_file, 'w') as f:
                json.dump([], f)

    def create_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new course"""
        try:
            courses = self.get_all_courses_raw()

            new_course = {
                "id": str(uuid.uuid4()),
                "name": course_data["name"],
                "description": course_data["description"],
                "subject": course_data["subject"],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "materials": [],
                "study_sessions": 0,
                "total_study_time": 0
            }

            courses.append(new_course)

            # Create course directory
            course_dir = os.path.join(self.courses_dir, new_course["id"])
            os.makedirs(course_dir, exist_ok=True)

            # Save courses data
            with open(self.courses_file, 'w') as f:
                json.dump(courses, f, indent=2)

            return new_course

        except Exception as e:
            raise Exception(f"Error creating course: {e}")

    def get_all_courses(self) -> List[Dict[str, Any]]:
        """Get all courses with additional metadata"""
        try:
            courses = self.get_all_courses_raw()

            for course in courses:
                # Add materials count
                course_dir = os.path.join(self.courses_dir, course["id"])
                if os.path.exists(course_dir):
                    materials = [f for f in os.listdir(course_dir) if f.endswith('.pdf')]
                    course["materials_count"] = len(materials)
                    course["materials"] = materials
                else:
                    course["materials_count"] = 0
                    course["materials"] = []

            return courses

        except Exception as e:
            raise Exception(f"Error getting courses: {e}")

    def get_all_courses_raw(self) -> List[Dict[str, Any]]:
        """Get raw courses data from file"""
        try:
            with open(self.courses_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific course by ID"""
        try:
            courses = self.get_all_courses()
            course = next((c for c in courses if c["id"] == course_id), None)

            if course:
                # Get detailed materials info
                course_dir = os.path.join(self.courses_dir, course_id)
                if os.path.exists(course_dir):
                    materials = []
                    for filename in os.listdir(course_dir):
                        if filename.endswith('.pdf'):
                            file_path = os.path.join(course_dir, filename)
                            stat = os.stat(file_path)
                            materials.append({
                                "filename": filename,
                                "size": stat.st_size,
                                "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "file_path": file_path
                            })
                    course["materials"] = materials
                else:
                    course["materials"] = []

            return course

        except Exception as e:
            raise Exception(f"Error getting course: {e}")

    def update_course(self, course_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update course information"""
        try:
            courses = self.get_all_courses_raw()
            course_index = next((i for i, c in enumerate(courses) if c["id"] == course_id), None)

            if course_index is None:
                return None

            # Update allowed fields
            allowed_fields = ["name", "description", "subject"]
            for field in allowed_fields:
                if field in update_data:
                    courses[course_index][field] = update_data[field]

            courses[course_index]["updated_at"] = datetime.now().isoformat()

            # Save updated courses
            with open(self.courses_file, 'w') as f:
                json.dump(courses, f, indent=2)

            return courses[course_index]

        except Exception as e:
            raise Exception(f"Error updating course: {e}")

    def delete_course(self, course_id: str) -> bool:
        """Delete a course and all its materials"""
        try:
            courses = self.get_all_courses_raw()
            courses = [c for c in courses if c["id"] != course_id]

            # Save updated courses
            with open(self.courses_file, 'w') as f:
                json.dump(courses, f, indent=2)

            # Delete course directory
            course_dir = os.path.join(self.courses_dir, course_id)
            if os.path.exists(course_dir):
                import shutil
                shutil.rmtree(course_dir)

            return True

        except Exception as e:
            raise Exception(f"Error deleting course: {e}")

    def update_course_stats(self, course_id: str, study_session_duration: int):
        """Update course statistics after a study session"""
        try:
            courses = self.get_all_courses_raw()
            course_index = next((i for i, c in enumerate(courses) if c["id"] == course_id), None)

            if course_index is not None:
                courses[course_index]["study_sessions"] += 1
                courses[course_index]["total_study_time"] += study_session_duration
                courses[course_index]["updated_at"] = datetime.now().isoformat()

                # Save updated courses
                with open(self.courses_file, 'w') as f:
                    json.dump(courses, f, indent=2)

        except Exception as e:
            print(f"Error updating course stats: {e}")

    def get_courses_by_subject(self, subject: str) -> List[Dict[str, Any]]:
        """Get courses filtered by subject"""
        try:
            courses = self.get_all_courses()
            return [c for c in courses if c["subject"].lower() == subject.lower()]
        except Exception as e:
            raise Exception(f"Error getting courses by subject: {e}")

    def search_courses(self, query: str) -> List[Dict[str, Any]]:
        """Search courses by name, description, or subject"""
        try:
            courses = self.get_all_courses()
            query = query.lower()

            filtered_courses = []
            for course in courses:
                if (query in course["name"].lower() or
                    query in course["description"].lower() or
                    query in course["subject"].lower()):
                    filtered_courses.append(course)

            return filtered_courses

        except Exception as e:
            raise Exception(f"Error searching courses: {e}")