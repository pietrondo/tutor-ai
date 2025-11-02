import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class BookService:
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

    def create_book(self, course_id: str, book_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new book within a course"""
        try:
            courses_data = self._get_courses_data()
            course = next((c for c in courses_data if c["id"] == course_id), None)

            if not course:
                raise Exception(f"Course {course_id} not found")

            if "books" not in course:
                course["books"] = []

            new_book = {
                "id": str(uuid.uuid4()),
                "title": book_data["title"],
                "author": book_data.get("author", ""),
                "isbn": book_data.get("isbn", ""),
                "description": book_data.get("description", ""),
                "year": book_data.get("year", ""),
                "publisher": book_data.get("publisher", ""),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "materials": [],
                "study_sessions": 0,
                "total_study_time": 0,
                "chapters": book_data.get("chapters", []),
                "tags": book_data.get("tags", [])
            }

            course["books"].append(new_book)
            course["updated_at"] = datetime.now().isoformat()

            # Create book directory for materials
            book_dir = os.path.join(self.courses_dir, course_id, "books", new_book["id"])
            os.makedirs(book_dir, exist_ok=True)

            # Save updated courses data
            self._save_courses_data(courses_data)

            return new_book

        except Exception as e:
            raise Exception(f"Error creating book: {e}")

    def get_books_by_course(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all books for a specific course"""
        try:
            course = self._get_course_by_id(course_id)
            if not course:
                return []

            books = course.get("books", [])

            # Add materials count for each book
            for book in books:
                book_dir = os.path.join(self.courses_dir, course_id, "books", book["id"])
                if os.path.exists(book_dir):
                    materials = [f for f in os.listdir(book_dir) if f.endswith('.pdf')]
                    book["materials_count"] = len(materials)
                else:
                    book["materials_count"] = 0

            return books

        except Exception as e:
            raise Exception(f"Error getting books: {e}")

    def get_book(self, course_id: str, book_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific book by ID"""
        try:
            books = self.get_books_by_course(course_id)
            book = next((b for b in books if b["id"] == book_id), None)

            if book:
                # Get detailed materials info
                book_dir = os.path.join(self.courses_dir, course_id, "books", book_id)
                if os.path.exists(book_dir):
                    materials = []
                    for filename in os.listdir(book_dir):
                        if filename.endswith('.pdf'):
                            file_path = os.path.join(book_dir, filename)
                            stat = os.stat(file_path)
                            materials.append({
                                "filename": filename,
                                "size": stat.st_size,
                                "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "file_path": file_path
                            })
                    book["materials"] = materials
                else:
                    book["materials"] = []

            return book

        except Exception as e:
            raise Exception(f"Error getting book: {e}")

    def update_book(self, course_id: str, book_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update book information"""
        try:
            courses_data = self._get_courses_data()
            course = next((c for c in courses_data if c["id"] == course_id), None)

            if not course:
                return None

            if "books" not in course:
                return None

            book_index = next((i for i, b in enumerate(course["books"]) if b["id"] == book_id), None)

            if book_index is None:
                return None

            # Update allowed fields
            allowed_fields = ["title", "author", "isbn", "description", "year", "publisher", "chapters", "tags"]
            for field in allowed_fields:
                if field in update_data:
                    course["books"][book_index][field] = update_data[field]

            course["books"][book_index]["updated_at"] = datetime.now().isoformat()
            course["updated_at"] = datetime.now().isoformat()

            # Save updated courses data
            self._save_courses_data(courses_data)

            return course["books"][book_index]

        except Exception as e:
            raise Exception(f"Error updating book: {e}")

    def delete_book(self, course_id: str, book_id: str) -> bool:
        """Delete a book and all its materials"""
        try:
            courses_data = self._get_courses_data()
            course = next((c for c in courses_data if c["id"] == course_id), None)

            if not course:
                return False

            if "books" not in course:
                return False

            # Remove book from course
            course["books"] = [b for b in course["books"] if b["id"] != book_id]
            course["updated_at"] = datetime.now().isoformat()

            # Save updated courses data
            self._save_courses_data(courses_data)

            # Delete book directory
            book_dir = os.path.join(self.courses_dir, course_id, "books", book_id)
            if os.path.exists(book_dir):
                import shutil
                shutil.rmtree(book_dir)

            return True

        except Exception as e:
            raise Exception(f"Error deleting book: {e}")

    def update_book_stats(self, course_id: str, book_id: str, study_session_duration: int):
        """Update book statistics after a study session"""
        try:
            courses_data = self._get_courses_data()
            course = next((c for c in courses_data if c["id"] == course_id), None)

            if course and "books" in course:
                book_index = next((i for i, b in enumerate(course["books"]) if b["id"] == book_id), None)

                if book_index is not None:
                    course["books"][book_index]["study_sessions"] += 1
                    course["books"][book_index]["total_study_time"] += study_session_duration
                    course["books"][book_index]["updated_at"] = datetime.now().isoformat()
                    course["updated_at"] = datetime.now().isoformat()

                    # Save updated courses data
                    self._save_courses_data(courses_data)

        except Exception as e:
            print(f"Error updating book stats: {e}")

    def search_books(self, course_id: str, query: str) -> List[Dict[str, Any]]:
        """Search books within a course by title, author, or description"""
        try:
            books = self.get_books_by_course(course_id)
            query = query.lower()

            filtered_books = []
            for book in books:
                if (query in book["title"].lower() or
                    query in book.get("author", "").lower() or
                    query in book.get("description", "").lower() or
                    any(query in tag.lower() for tag in book.get("tags", []))):
                    filtered_books.append(book)

            return filtered_books

        except Exception as e:
            raise Exception(f"Error searching books: {e}")

    def _get_courses_data(self) -> List[Dict[str, Any]]:
        """Get courses data from file"""
        try:
            with open(self.courses_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_courses_data(self, data: List[Dict[str, Any]]):
        """Save courses data to file"""
        with open(self.courses_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _get_course_by_id(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get course by ID"""
        courses_data = self._get_courses_data()
        return next((c for c in courses_data if c["id"] == course_id), None)