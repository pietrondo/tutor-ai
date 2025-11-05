import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

class AnnotationService:
    def __init__(self):
        self.annotations_dir = "data/annotations"
        self.ensure_annotations_directory()

    def ensure_annotations_directory(self):
        """Ensure the annotations directory structure exists"""
        os.makedirs(self.annotations_dir, exist_ok=True)

    def create_annotation(self, annotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new annotation"""
        try:
            # Validate required fields
            required_fields = ["user_id", "pdf_filename", "pdf_path", "page_number"]
            for field in required_fields:
                if field not in annotation_data:
                    raise ValueError(f"Missing required field: {field}")

            new_annotation = {
                "id": str(uuid.uuid4()),
                "user_id": annotation_data["user_id"],
                "pdf_filename": annotation_data["pdf_filename"],
                "pdf_path": annotation_data["pdf_path"],
                "course_id": annotation_data.get("course_id", ""),
                "book_id": annotation_data.get("book_id", ""),
                "page_number": annotation_data["page_number"],
                "type": annotation_data.get("type", "highlight"),  # highlight, underline, note, strikeout
                "text": annotation_data.get("text", ""),
                "selected_text": annotation_data.get("selected_text", ""),
                "content": annotation_data.get("content", ""),  # For note annotations
                "position": annotation_data.get("position", {}),  # x, y, width, height
                "style": annotation_data.get("style", {
                    "color": "#ffeb3b",
                    "opacity": 0.3,
                    "stroke_color": "#fbc02d",
                    "stroke_width": 1
                }),
                "tags": annotation_data.get("tags", []),
                "is_public": annotation_data.get("is_public", False),
                "is_favorite": annotation_data.get("is_favorite", False),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Get existing annotations for this PDF
            annotations = self.get_annotations_for_pdf(
                annotation_data["user_id"],
                annotation_data["pdf_filename"],
                annotation_data.get("course_id", ""),
                annotation_data.get("book_id", "")
            )

            annotations.append(new_annotation)

            # Save annotations
            self._save_annotations(
                annotation_data["user_id"],
                annotation_data["pdf_filename"],
                annotation_data.get("course_id", ""),
                annotation_data.get("book_id", ""),
                annotations
            )

            return new_annotation

        except Exception as e:
            raise Exception(f"Error creating annotation: {e}")

    def get_annotations_for_pdf(self, user_id: str, pdf_filename: str, course_id: str = "", book_id: str = "") -> List[Dict[str, Any]]:
        """Get all annotations for a specific PDF and user"""
        try:
            annotations_file = self._get_annotations_file_path(user_id, pdf_filename, course_id, book_id)

            if not os.path.exists(annotations_file):
                return []

            with open(annotations_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            print(f"Error getting annotations: {e}")
            return []

    def get_annotation(self, user_id: str, annotation_id: str, pdf_filename: str = "", course_id: str = "", book_id: str = "") -> Optional[Dict[str, Any]]:
        """Get a specific annotation by ID"""
        try:
            if pdf_filename:
                annotations = self.get_annotations_for_pdf(user_id, pdf_filename, course_id, book_id)
            else:
                # Search across all user's PDFs
                annotations = self._get_all_user_annotations(user_id)

            return next((a for a in annotations if a["id"] == annotation_id), None)

        except Exception as e:
            raise Exception(f"Error getting annotation: {e}")

    def update_annotation(self, user_id: str, annotation_id: str, update_data: Dict[str, Any], pdf_filename: str = "", course_id: str = "", book_id: str = "") -> Optional[Dict[str, Any]]:
        """Update an existing annotation"""
        try:
            # Find the annotation
            annotation = self.get_annotation(user_id, annotation_id, pdf_filename, course_id, book_id)
            if not annotation:
                return None

            # Get the full PDF filename if not provided
            if not pdf_filename:
                pdf_filename = annotation["pdf_filename"]
                course_id = annotation.get("course_id", "")
                book_id = annotation.get("book_id", "")

            # Get all annotations for this PDF
            annotations = self.get_annotations_for_pdf(user_id, pdf_filename, course_id, book_id)

            # Find and update the annotation
            annotation_index = next((i for i, a in enumerate(annotations) if a["id"] == annotation_id), None)
            if annotation_index is None:
                return None

            # Update allowed fields
            allowed_fields = ["type", "content", "style", "tags", "is_public", "is_favorite"]
            for field in allowed_fields:
                if field in update_data:
                    annotations[annotation_index][field] = update_data[field]

            annotations[annotation_index]["updated_at"] = datetime.now().isoformat()

            # Save updated annotations
            self._save_annotations(user_id, pdf_filename, course_id, book_id, annotations)

            return annotations[annotation_index]

        except Exception as e:
            raise Exception(f"Error updating annotation: {e}")

    def delete_annotation(self, user_id: str, annotation_id: str, pdf_filename: str = "", course_id: str = "", book_id: str = "") -> bool:
        """Delete an annotation"""
        try:
            # Find the annotation
            annotation = self.get_annotation(user_id, annotation_id, pdf_filename, course_id, book_id)
            if not annotation:
                return False

            # Get the full PDF filename if not provided
            if not pdf_filename:
                pdf_filename = annotation["pdf_filename"]
                course_id = annotation.get("course_id", "")
                book_id = annotation.get("book_id", "")

            # Get all annotations for this PDF
            annotations = self.get_annotations_for_pdf(user_id, pdf_filename, course_id, book_id)

            # Remove the annotation
            annotations = [a for a in annotations if a["id"] != annotation_id]

            # Save updated annotations
            self._save_annotations(user_id, pdf_filename, course_id, book_id, annotations)

            return True

        except Exception as e:
            raise Exception(f"Error deleting annotation: {e}")

    def search_annotations(self, user_id: str, query: str, course_id: str = "", book_id: str = "", tags: List[str] = None, annotation_type: str = "") -> List[Dict[str, Any]]:
        """Search annotations by text content, tags, or type"""
        try:
            all_annotations = self._get_all_user_annotations(user_id)
            query = query.lower()

            filtered_annotations = []
            for annotation in all_annotations:
                # Filter by course and book if specified
                if course_id and annotation.get("course_id") != course_id:
                    continue
                if book_id and annotation.get("book_id") != book_id:
                    continue

                # Filter by type if specified
                if annotation_type and annotation.get("type") != annotation_type:
                    continue

                # Filter by tags if specified
                if tags and not any(tag in annotation.get("tags", []) for tag in tags):
                    continue

                # Search in text content
                if (query in annotation.get("text", "").lower() or
                    query in annotation.get("selected_text", "").lower() or
                    query in annotation.get("content", "").lower()):
                    filtered_annotations.append(annotation)

            # Sort by creation date (newest first)
            filtered_annotations.sort(key=lambda x: x["created_at"], reverse=True)

            return filtered_annotations

        except Exception as e:
            raise Exception(f"Error searching annotations: {e}")

    def get_public_annotations(self, pdf_filename: str, course_id: str = "", book_id: str = "") -> List[Dict[str, Any]]:
        """Get public annotations for a PDF from all users"""
        try:
            public_annotations = []

            # Iterate through all user directories
            for user_dir in os.listdir(self.annotations_dir):
                user_path = os.path.join(self.annotations_dir, user_dir)
                if os.path.isdir(user_path):
                    # Look for this specific PDF annotations
                    annotations_file = self._get_annotations_file_path(user_dir, pdf_filename, course_id, book_id)
                    if os.path.exists(annotations_file):
                        with open(annotations_file, 'r', encoding='utf-8') as f:
                            user_annotations = json.load(f)
                            # Filter public annotations and remove sensitive user info
                            for annotation in user_annotations:
                                if annotation.get("is_public", False):
                                    public_annotations.append({
                                        "id": annotation["id"],
                                        "user_id": user_dir,  # Keep user_id for attribution
                                        "page_number": annotation["page_number"],
                                        "type": annotation["type"],
                                        "selected_text": annotation.get("selected_text", ""),
                                        "content": annotation.get("content", ""),
                                        "position": annotation.get("position", {}),
                                        "style": annotation.get("style", {}),
                                        "tags": annotation.get("tags", []),
                                        "created_at": annotation["created_at"]
                                    })

            # Sort by creation date (newest first)
            public_annotations.sort(key=lambda x: x["created_at"], reverse=True)

            return public_annotations

        except Exception as e:
            raise Exception(f"Error getting public annotations: {e}")

    def export_annotations(self, user_id: str, format: str = "json", course_id: str = "", book_id: str = "") -> Union[str, Dict]:
        """Export user annotations in various formats"""
        try:
            all_annotations = self._get_all_user_annotations(user_id)

            # Filter by course and book if specified
            if course_id:
                all_annotations = [a for a in all_annotations if a.get("course_id") == course_id]
            if book_id:
                all_annotations = [a for a in all_annotations if a.get("book_id") == book_id]

            if format.lower() == "json":
                return {
                    "user_id": user_id,
                    "export_date": datetime.now().isoformat(),
                    "total_annotations": len(all_annotations),
                    "annotations": all_annotations
                }
            elif format.lower() == "markdown":
                return self._annotations_to_markdown(all_annotations)
            elif format.lower() == "csv":
                return self._annotations_to_csv(all_annotations)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            raise Exception(f"Error exporting annotations: {e}")

    def import_annotations(self, user_id: str, annotations_data: Union[str, Dict, List], format: str = "json") -> int:
        """Import annotations from various formats"""
        try:
            imported_count = 0

            if format.lower() == "json":
                if isinstance(annotations_data, str):
                    annotations = json.loads(annotations_data)
                elif isinstance(annotations_data, dict):
                    annotations = annotations_data.get("annotations", [])
                elif isinstance(annotations_data, list):
                    annotations = annotations_data
                else:
                    raise ValueError("Invalid JSON data format")

            elif format.lower() == "markdown":
                annotations = self._markdown_to_annotations(annotations_data)
            else:
                raise ValueError(f"Unsupported import format: {format}")

            # Process each annotation
            for annotation_data in annotations:
                # Set the user_id and ensure required fields
                annotation_data["user_id"] = user_id

                # Create the annotation
                self.create_annotation(annotation_data)
                imported_count += 1

            return imported_count

        except Exception as e:
            raise Exception(f"Error importing annotations: {e}")

    def get_annotation_stats(self, user_id: str, course_id: str = "", book_id: str = "") -> Dict[str, Any]:
        """Get statistics about user annotations"""
        try:
            all_annotations = self._get_all_user_annotations(user_id)

            # Filter by course and book if specified
            if course_id:
                all_annotations = [a for a in all_annotations if a.get("course_id") == course_id]
            if book_id:
                all_annotations = [a for a in all_annotations if a.get("book_id") == book_id]

            stats = {
                "total_annotations": len(all_annotations),
                "by_type": {},
                "by_pdf": {},
                "by_page": {},
                "public_annotations": 0,
                "favorite_annotations": 0,
                "tags_used": set(),
                "recent_activity": []
            }

            for annotation in all_annotations:
                # Count by type
                annotation_type = annotation.get("type", "highlight")
                stats["by_type"][annotation_type] = stats["by_type"].get(annotation_type, 0) + 1

                # Count by PDF
                pdf_name = annotation.get("pdf_filename", "Unknown")
                stats["by_pdf"][pdf_name] = stats["by_pdf"].get(pdf_name, 0) + 1

                # Count by page
                page_num = annotation.get("page_number", 0)
                stats["by_page"][str(page_num)] = stats["by_page"].get(str(page_num), 0) + 1

                # Count public and favorites
                if annotation.get("is_public", False):
                    stats["public_annotations"] += 1
                if annotation.get("is_favorite", False):
                    stats["favorite_annotations"] += 1

                # Collect tags
                stats["tags_used"].update(annotation.get("tags", []))

                # Recent activity (last 10)
                if len(stats["recent_activity"]) < 10:
                    stats["recent_activity"].append({
                        "id": annotation["id"],
                        "type": annotation.get("type", "highlight"),
                        "pdf_filename": annotation.get("pdf_filename", ""),
                        "page_number": annotation.get("page_number", 0),
                        "created_at": annotation["created_at"]
                    })

            stats["tags_used"] = list(stats["tags_used"])

            return stats

        except Exception as e:
            raise Exception(f"Error getting annotation stats: {e}")

    def _get_all_user_annotations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all annotations for a user across all PDFs"""
        try:
            all_annotations = []
            user_dir = os.path.join(self.annotations_dir, user_id)

            if not os.path.exists(user_dir):
                return all_annotations

            # Walk through all subdirectories
            for root, dirs, files in os.walk(user_dir):
                for file in files:
                    if file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                annotations = json.load(f)
                                all_annotations.extend(annotations)
                        except Exception as e:
                            print(f"Error reading annotations file {file_path}: {e}")

            return all_annotations

        except Exception as e:
            raise Exception(f"Error getting all user annotations: {e}")

    def _get_annotations_file_path(self, user_id: str, pdf_filename: str, course_id: str = "", book_id: str = "") -> str:
        """Get the file path for annotations of a specific PDF"""
        # Create directory structure: data/annotations/user_id/course_id/book_id/filename.json
        path_parts = [self.annotations_dir, user_id]

        if course_id:
            path_parts.append(course_id)
        if book_id:
            path_parts.append(book_id)

        # Create directory structure
        dir_path = os.path.join(*path_parts)
        os.makedirs(dir_path, exist_ok=True)

        # Use safe filename
        safe_filename = pdf_filename.replace('/', '_').replace('\\', '_').replace(':', '_')
        annotations_file = os.path.join(dir_path, f"{safe_filename}.json")

        return annotations_file

    def _save_annotations(self, user_id: str, pdf_filename: str, course_id: str, book_id: str, annotations: List[Dict[str, Any]]):
        """Save annotations to file"""
        try:
            annotations_file = self._get_annotations_file_path(user_id, pdf_filename, course_id, book_id)

            with open(annotations_file, 'w', encoding='utf-8') as f:
                json.dump(annotations, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise Exception(f"Error saving annotations: {e}")

    def _annotations_to_markdown(self, annotations: List[Dict[str, Any]]) -> str:
        """Convert annotations to Markdown format"""
        markdown_lines = [
            "# My PDF Annotations",
            f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*Total annotations: {len(annotations)}*",
            ""
        ]

        # Group by PDF
        annotations_by_pdf = {}
        for annotation in annotations:
            pdf_name = annotation.get("pdf_filename", "Unknown")
            if pdf_name not in annotations_by_pdf:
                annotations_by_pdf[pdf_name] = []
            annotations_by_pdf[pdf_name].append(annotation)

        for pdf_name, pdf_annotations in annotations_by_pdf.items():
            markdown_lines.append(f"## {pdf_name}")
            markdown_lines.append("")

            for annotation in pdf_annotations:
                page_num = annotation.get("page_number", 0)
                annotation_type = annotation.get("type", "highlight")
                selected_text = annotation.get("selected_text", "")
                content = annotation.get("content", "")
                created_at = annotation.get("created_at", "")

                markdown_lines.append(f"### Page {page_num} - {annotation_type.title()}")

                if selected_text:
                    markdown_lines.append(f"**Text:** {selected_text}")

                if content:
                    markdown_lines.append(f"**Note:** {content}")

                markdown_lines.append(f"*Created: {created_at}*")
                markdown_lines.append("")

        return "\n".join(markdown_lines)

    def _annotations_to_csv(self, annotations: List[Dict[str, Any]]) -> str:
        """Convert annotations to CSV format"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'ID', 'PDF Filename', 'Page Number', 'Type', 'Selected Text',
            'Content', 'Tags', 'Is Public', 'Is Favorite', 'Created At'
        ])

        # Data rows
        for annotation in annotations:
            writer.writerow([
                annotation.get('id', ''),
                annotation.get('pdf_filename', ''),
                annotation.get('page_number', ''),
                annotation.get('type', ''),
                annotation.get('selected_text', ''),
                annotation.get('content', ''),
                ';'.join(annotation.get('tags', [])),
                annotation.get('is_public', False),
                annotation.get('is_favorite', False),
                annotation.get('created_at', '')
            ])

        return output.getvalue()

    def _markdown_to_annotations(self, markdown_data: str) -> List[Dict[str, Any]]:
        """Convert Markdown data to annotations (basic implementation)"""
        # This is a simplified implementation
        # In a real scenario, you'd want more sophisticated parsing
        annotations = []

        # For now, return empty list as Markdown import would require complex parsing
        # This could be implemented in the future if needed
        return annotations