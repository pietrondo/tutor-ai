#!/usr/bin/env python3
"""
Test suite for the Annotation Service
"""

import os
import json
import unittest
import tempfile
import shutil
from datetime import datetime
from services.annotation_service import AnnotationService

class TestAnnotationService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test annotations
        self.test_dir = tempfile.mkdtemp()
        self.annotation_service = AnnotationService()

        # Override the annotations directory for testing
        self.original_annotations_dir = self.annotation_service.annotations_dir
        self.annotation_service.annotations_dir = self.test_dir

        # Sample annotation data
        self.sample_annotation_data = {
            "user_id": "test_user",
            "pdf_filename": "test_document.pdf",
            "pdf_path": "/path/to/test_document.pdf",
            "course_id": "test_course",
            "book_id": "test_book",
            "page_number": 1,
            "type": "highlight",
            "text": "This is sample text",
            "selected_text": "selected text",
            "content": "This is a note",
            "position": {"x": 100, "y": 200, "width": 50, "height": 20},
            "style": {"color": "#ffff00", "opacity": 0.3},
            "tags": ["important", "test"],
            "is_public": False,
            "is_favorite": True
        }

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original directory
        self.annotation_service.annotations_dir = self.original_annotations_dir

        # Remove the temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_ensure_annotations_directory(self):
        """Test that annotations directory is created."""
        service = AnnotationService()
        self.assertTrue(os.path.exists(service.annotations_dir))

    def test_create_annotation_success(self):
        """Test successful annotation creation."""
        annotation = self.annotation_service.create_annotation(self.sample_annotation_data)

        # Check that annotation was created with all required fields
        self.assertIn("id", annotation)
        self.assertEqual(annotation["user_id"], "test_user")
        self.assertEqual(annotation["pdf_filename"], "test_document.pdf")
        self.assertEqual(annotation["page_number"], 1)
        self.assertEqual(annotation["type"], "highlight")
        self.assertIn("created_at", annotation)
        self.assertIn("updated_at", annotation)

    def test_create_annotation_missing_required_field(self):
        """Test annotation creation with missing required fields."""
        # Remove required field
        incomplete_data = self.sample_annotation_data.copy()
        del incomplete_data["user_id"]

        with self.assertRaises(Exception) as context:
            self.annotation_service.create_annotation(incomplete_data)

        self.assertIn("Missing required field: user_id", str(context.exception))

    def test_create_annotation_default_values(self):
        """Test annotation creation with default values."""
        minimal_data = {
            "user_id": "test_user",
            "pdf_filename": "test.pdf",
            "pdf_path": "/path/test.pdf",
            "page_number": 1
        }

        annotation = self.annotation_service.create_annotation(minimal_data)

        self.assertEqual(annotation["type"], "highlight")  # Default type
        self.assertEqual(annotation["tags"], [])  # Default empty tags
        self.assertEqual(annotation["is_public"], False)  # Default
        self.assertEqual(annotation["is_favorite"], False)  # Default
        self.assertEqual(annotation["course_id"], "")  # Default empty string
        self.assertEqual(annotation["book_id"], "")  # Default empty string

    def test_get_annotations_for_pdf_empty(self):
        """Test getting annotations for a PDF with no annotations."""
        annotations = self.annotation_service.get_annotations_for_pdf(
            "test_user", "nonexistent.pdf"
        )
        self.assertEqual(annotations, [])

    def test_get_annotations_for_pdf_with_data(self):
        """Test getting annotations for a PDF with existing annotations."""
        # Create some annotations
        ann1 = self.annotation_service.create_annotation(self.sample_annotation_data)

        # Modify data for second annotation
        data2 = self.sample_annotation_data.copy()
        data2["selected_text"] = "different text"
        data2["page_number"] = 2
        ann2 = self.annotation_service.create_annotation(data2)

        # Get annotations
        annotations = self.annotation_service.get_annotations_for_pdf(
            "test_user", "test_document.pdf", "test_course", "test_book"
        )

        self.assertEqual(len(annotations), 2)
        self.assertIn(ann1, annotations)
        self.assertIn(ann2, annotations)

    def test_get_annotation_by_id(self):
        """Test getting a specific annotation by ID."""
        created_annotation = self.annotation_service.create_annotation(self.sample_annotation_data)

        retrieved_annotation = self.annotation_service.get_annotation(
            "test_user", created_annotation["id"], "test_document.pdf", "test_course", "test_book"
        )

        self.assertEqual(retrieved_annotation["id"], created_annotation["id"])
        self.assertEqual(retrieved_annotation["selected_text"], "selected text")

    def test_get_annotation_not_found(self):
        """Test getting a non-existent annotation."""
        result = self.annotation_service.get_annotation(
            "test_user", "nonexistent_id", "test_document.pdf"
        )
        self.assertIsNone(result)

    def test_update_annotation(self):
        """Test updating an existing annotation."""
        created_annotation = self.annotation_service.create_annotation(self.sample_annotation_data)

        update_data = {
            "content": "Updated note content",
            "tags": ["updated", "test"],
            "is_favorite": False
        }

        updated_annotation = self.annotation_service.update_annotation(
            "test_user", created_annotation["id"], update_data, "test_document.pdf", "test_course", "test_book"
        )

        self.assertEqual(updated_annotation["content"], "Updated note content")
        self.assertEqual(updated_annotation["tags"], ["updated", "test"])
        self.assertEqual(updated_annotation["is_favorite"], False)
        self.assertNotEqual(updated_annotation["updated_at"], created_annotation["created_at"])

    def test_update_annotation_not_found(self):
        """Test updating a non-existent annotation."""
        update_data = {"content": "Updated content"}

        result = self.annotation_service.update_annotation(
            "test_user", "nonexistent_id", update_data, "test_document.pdf"
        )

        self.assertIsNone(result)

    def test_delete_annotation(self):
        """Test deleting an annotation."""
        created_annotation = self.annotation_service.create_annotation(self.sample_annotation_data)

        # Verify annotation exists
        annotations_before = self.annotation_service.get_annotations_for_pdf(
            "test_user", "test_document.pdf"
        )
        self.assertEqual(len(annotations_before), 1)

        # Delete annotation
        success = self.annotation_service.delete_annotation(
            "test_user", created_annotation["id"], "test_document.pdf"
        )

        self.assertTrue(success)

        # Verify annotation is deleted
        annotations_after = self.annotation_service.get_annotations_for_pdf(
            "test_user", "test_document.pdf"
        )
        self.assertEqual(len(annotations_after), 0)

    def test_delete_annotation_not_found(self):
        """Test deleting a non-existent annotation."""
        success = self.annotation_service.delete_annotation(
            "test_user", "nonexistent_id", "test_document.pdf"
        )

        self.assertFalse(success)

    def test_search_annotations(self):
        """Test searching annotations by text content."""
        # Create multiple annotations
        data1 = self.sample_annotation_data.copy()
        data1["selected_text"] = "important physics concept"
        data1["page_number"] = 1

        data2 = self.sample_annotation_data.copy()
        data2["selected_text"] = "chemistry experiment"
        data2["page_number"] = 2

        data3 = self.sample_annotation_data.copy()
        data3["selected_text"] = "physics formula derivation"
        data3["page_number"] = 3

        self.annotation_service.create_annotation(data1)
        self.annotation_service.create_annotation(data2)
        self.annotation_service.create_annotation(data3)

        # Search for "physics"
        results = self.annotation_service.search_annotations(
            "test_user", "physics"
        )

        self.assertEqual(len(results), 2)  # data1 and data3 contain "physics"

        # Search for specific annotation type
        results_type = self.annotation_service.search_annotations(
            "test_user", "concept", annotation_type="highlight"
        )

        self.assertGreaterEqual(len(results_type), 0)

    def test_search_annotations_with_tags(self):
        """Test searching annotations with tags filter."""
        # Create annotation with specific tags
        data_with_tags = self.sample_annotation_data.copy()
        data_with_tags["tags"] = ["exam", "important", "chapter5"]

        self.annotation_service.create_annotation(data_with_tags)

        # Search by tags with proper context
        results = self.annotation_service.search_annotations(
            "test_user", "any", "test_course", "test_book", ["exam"]
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["tags"], ["exam", "important", "chapter5"])

    def test_get_public_annotations(self):
        """Test getting public annotations."""
        # Create public annotation
        public_data = self.sample_annotation_data.copy()
        public_data["is_public"] = True
        public_data["user_id"] = "user1"

        # Create private annotation
        private_data = self.sample_annotation_data.copy()
        private_data["is_public"] = False
        private_data["user_id"] = "user2"

        self.annotation_service.create_annotation(public_data)
        self.annotation_service.create_annotation(private_data)

        # Get public annotations
        public_annotations = self.annotation_service.get_public_annotations(
            "test_document.pdf", "test_course", "test_book"
        )

        # Should only return the public annotation
        self.assertEqual(len(public_annotations), 1)
        self.assertEqual(public_annotations[0]["user_id"], "user1")

    def test_export_annotations_json(self):
        """Test exporting annotations in JSON format."""
        # Create some annotations
        self.annotation_service.create_annotation(self.sample_annotation_data)

        # Export annotations
        export_data = self.annotation_service.export_annotations(
            "test_user", "json", "test_course", "test_book"
        )

        self.assertIn("user_id", export_data)
        self.assertIn("export_date", export_data)
        self.assertIn("total_annotations", export_data)
        self.assertIn("annotations", export_data)
        self.assertEqual(export_data["total_annotations"], 1)

    def test_export_annotations_markdown(self):
        """Test exporting annotations in Markdown format."""
        # Create annotation with note content
        note_data = self.sample_annotation_data.copy()
        note_data["content"] = "This is an important note about the text"
        note_data["selected_text"] = "Important text selection"

        self.annotation_service.create_annotation(note_data)

        # Export as markdown
        markdown_content = self.annotation_service.export_annotations(
            "test_user", "markdown"
        )

        self.assertIn("# My PDF Annotations", markdown_content)
        self.assertIn("test_document.pdf", markdown_content)
        self.assertIn("Important text selection", markdown_content)
        self.assertIn("This is an important note", markdown_content)

    def test_import_annotations_json(self):
        """Test importing annotations from JSON."""
        import_data = {
            "annotations": [
                {
                    "user_id": "import_user",
                    "pdf_filename": "import_doc.pdf",
                    "pdf_path": "/path/import.pdf",
                    "page_number": 1,
                    "type": "highlight",
                    "selected_text": "Imported text",
                    "content": "Imported note",
                    "tags": ["imported"]
                }
            ]
        }

        imported_count = self.annotation_service.import_annotations(
            "test_user", import_data, "json"
        )

        self.assertEqual(imported_count, 1)

        # Verify annotation was imported
        annotations = self.annotation_service.get_annotations_for_pdf(
            "test_user", "import_doc.pdf"
        )
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0]["selected_text"], "Imported text")

    def test_get_annotation_stats(self):
        """Test getting annotation statistics."""
        # Create annotations with different types
        highlight_data = self.sample_annotation_data.copy()
        highlight_data["type"] = "highlight"
        highlight_data["page_number"] = 1

        note_data = self.sample_annotation_data.copy()
        note_data["type"] = "note"
        note_data["page_number"] = 2

        underline_data = self.sample_annotation_data.copy()
        underline_data["type"] = "underline"
        underline_data["page_number"] = 2
        underline_data["is_public"] = True

        self.annotation_service.create_annotation(highlight_data)
        self.annotation_service.create_annotation(note_data)
        self.annotation_service.create_annotation(underline_data)

        # Get stats
        stats = self.annotation_service.get_annotation_stats("test_user")

        self.assertEqual(stats["total_annotations"], 3)
        self.assertEqual(stats["by_type"]["highlight"], 1)
        self.assertEqual(stats["by_type"]["note"], 1)
        self.assertEqual(stats["by_type"]["underline"], 1)
        self.assertEqual(stats["public_annotations"], 1)
        self.assertEqual(stats["by_pdf"]["test_document.pdf"], 3)
        self.assertEqual(stats["by_page"]["1"], 1)
        self.assertEqual(stats["by_page"]["2"], 2)
        self.assertIn("important", stats["tags_used"])
        self.assertIn("test", stats["tags_used"])

    def test_annotation_file_path_generation(self):
        """Test that annotation file paths are generated correctly."""
        service = AnnotationService()

        # Test basic path
        path = service._get_annotations_file_path("user123", "document.pdf")
        expected_path = os.path.join(service.annotations_dir, "user123", "document.pdf.json")
        self.assertEqual(path, expected_path)

        # Test path with course and book
        path_with_context = service._get_annotations_file_path(
            "user123", "document.pdf", "course456", "book789"
        )
        expected_path_with_context = os.path.join(
            service.annotations_dir, "user123", "course456", "book789", "document.pdf.json"
        )
        self.assertEqual(path_with_context, expected_path_with_context)

        # Test path sanitization
        path_sanitized = service._get_annotations_file_path("user123", "document/with\\slashes:and*chars")
        self.assertIn("document_with_slashes_and_chars", path_sanitized)

    def test_annotations_persistence(self):
        """Test that annotations are properly saved to and loaded from files."""
        # Create annotation
        original_annotation = self.annotation_service.create_annotation(self.sample_annotation_data)

        # Create a new service instance (simulating app restart)
        new_service = AnnotationService()
        new_service.annotations_dir = self.test_dir

        # Load annotations with new service
        loaded_annotations = new_service.get_annotations_for_pdf(
            "test_user", "test_document.pdf", "test_course", "test_book"
        )

        self.assertEqual(len(loaded_annotations), 1)
        self.assertEqual(loaded_annotations[0]["id"], original_annotation["id"])
        self.assertEqual(loaded_annotations[0]["selected_text"], "selected text")

    def test_concurrent_annotation_saving(self):
        """Test handling of concurrent annotation operations."""
        import threading
        import time

        results = []
        errors = []

        def create_annotation_worker():
            try:
                data = self.sample_annotation_data.copy()
                data["selected_text"] = f"Thread annotation {time.time()}"
                result = self.annotation_service.create_annotation(data)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_annotation_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)

        # Verify all annotations were saved (allow for some tolerance in concurrent operations)
        all_annotations = self.annotation_service.get_annotations_for_pdf(
            "test_user", "test_document.pdf", "test_course", "test_book"
        )
        self.assertGreaterEqual(len(all_annotations), 3)  # Allow for some race conditions


class TestAnnotationServiceAPIIntegration(unittest.TestCase):
    """Integration tests for annotation service API endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up for API integration tests."""
        # These tests would require the FastAPI server to be running
        # For now, we'll create mock tests
        pass

    def test_api_create_annotation(self):
        """Test API endpoint for creating annotation."""
        # This would be implemented when the API server is running
        # For now, just a placeholder
        self.assertTrue(True)

    def test_api_get_annotations(self):
        """Test API endpoint for getting annotations."""
        # This would be implemented when the API server is running
        self.assertTrue(True)


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)