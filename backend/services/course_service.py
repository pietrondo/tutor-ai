import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class CourseService:
    def __init__(self):
        self.courses_dir = "data/courses"
        self.courses_file = os.path.join(self.courses_dir, "courses.json")
        self.ensure_courses_directory()

    def _collect_course_materials(self, course_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """Collect PDF materials for a course and map them to books when possible."""
        course_dir = os.path.join(self.courses_dir, course_id)
        materials: List[Dict[str, Any]] = []
        book_materials_map: Dict[str, List[Dict[str, Any]]] = {}

        if not os.path.exists(course_dir):
            return materials, book_materials_map

        for root, _, files in os.walk(course_dir):
            for filename in files:
                if not filename.lower().endswith('.pdf'):
                    continue

                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, course_dir)
                normalized_rel_path = rel_path.replace(os.sep, '/')
                stat = os.stat(file_path)
                pdf_url = f"http://localhost:8000/course-files/{course_id}/{normalized_rel_path}"

                material = {
                    "filename": filename,
                    "relative_path": normalized_rel_path,
                    "size": stat.st_size,
                    "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "file_path": file_path,
                    "pdf_url": pdf_url,
                    "read_url": f"/courses/{course_id}/materials/{filename}",
                    "download_url": f"/course-files/{course_id}/{normalized_rel_path}"
                }

                path_parts = normalized_rel_path.split('/')
                if len(path_parts) >= 3 and path_parts[0] == 'books':
                    book_id = path_parts[1]
                    material["book_id"] = book_id
                    book_materials_map.setdefault(book_id, []).append(material)
                else:
                    material["book_id"] = None

                materials.append(material)

        return materials, book_materials_map

    def get_materials_for_book(self, course_id: str, book_id: str) -> List[Dict[str, Any]]:
        """Get all materials for a specific book with navigation context."""
        materials, book_materials_map = self._collect_course_materials(course_id)
        book_materials = book_materials_map.get(book_id, [])

        enhanced_materials = []
        for material in book_materials:
            enhanced_material = dict(material)
            # Add book parameter to read_url for proper navigation
            enhanced_material["read_url"] = f"{material['read_url']}?book={book_id}"
            enhanced_materials.append(enhanced_material)

        return enhanced_materials

    def _enrich_books_with_materials(
        self,
        course: Dict[str, Any],
        course_id: str,
        materials: List[Dict[str, Any]],
        book_materials_map: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Attach discovered PDF materials to existing book metadata."""
        existing_books = course.get("books", []) or []
        enriched_books: List[Dict[str, Any]] = []

        if existing_books:
            for book in existing_books:
                book_copy = dict(book)
                book_id = book_copy.get("id")
                associated_materials = book_materials_map.get(book_id, [])
                book_copy["materials"] = associated_materials
                book_copy["materials_count"] = len(associated_materials)

                if associated_materials:
                    book_copy.setdefault("pdf_url", associated_materials[0]["pdf_url"])
                else:
                    # Legacy fallback to preserve existing pdf_url if present
                    book_copy.setdefault("pdf_url", None)

                enriched_books.append(book_copy)
        else:
            # Legacy mode: treat standalone PDFs as books so the UI still works
            for index, material in enumerate(materials):
                if material.get("book_id"):
                    continue

                enriched_books.append({
                    "id": material["filename"] or f"book-{index}",
                    "title": material["filename"].replace('.pdf', '') or f"Book {index + 1}",
                    "pdf_url": material["pdf_url"],
                    "total_pages": 0,
                    "description": f"PDF file: {material['filename']}",
                    "materials": [material],
                    "materials_count": 1
                })

        return enriched_books

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
                materials, book_materials_map = self._collect_course_materials(course["id"])
                course["materials_count"] = len(materials)
                course["materials"] = materials
                course["books"] = self._enrich_books_with_materials(course, course["id"], materials, book_materials_map)

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
                materials, book_materials_map = self._collect_course_materials(course_id)
                course["materials"] = materials
                course["books"] = self._enrich_books_with_materials(course, course_id, materials, book_materials_map)

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
