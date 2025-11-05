#!/usr/bin/env python3
"""
Test suite for Annotation API endpoints
"""

import unittest
import json
import tempfile
import shutil
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

class TestAnnotationAPI(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = TestClient(app)

        # Sample annotation data
        self.sample_annotation = {
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

    @patch('services.annotation_service.AnnotationService')
    def test_create_annotation_success(self, mock_annotation_service):
        """Test successful annotation creation via API."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance

        created_annotation = self.sample_annotation.copy()
        created_annotation["id"] = "test_id"
        created_annotation["created_at"] = "2023-01-01T00:00:00"
        created_annotation["updated_at"] = "2023-01-01T00:00:00"

        mock_service_instance.create_annotation.return_value = created_annotation

        # Make API request
        response = self.client.post("/annotations", json=self.sample_annotation)

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data["success"])
        self.assertIn("annotation", response_data)
        self.assertEqual(response_data["annotation"]["id"], "test_id")

    @patch('services.annotation_service.AnnotationService')
    def test_create_annotation_missing_field(self, mock_annotation_service):
        """Test annotation creation with missing required field."""
        # Remove required field
        incomplete_data = self.sample_annotation.copy()
        del incomplete_data["user_id"]

        # Make API request
        response = self.client.post("/annotations", json=incomplete_data)

        # Assert response - should fail validation
        self.assertEqual(response.status_code, 422)  # Validation error

    @patch('services.annotation_service.AnnotationService')
    def test_get_annotations_for_pdf(self, mock_annotation_service):
        """Test getting annotations for a PDF."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance

        mock_annotations = [
            {
                "id": "test_id_1",
                "user_id": "test_user",
                "pdf_filename": "test_document.pdf",
                "selected_text": "First annotation"
            },
            {
                "id": "test_id_2",
                "user_id": "test_user",
                "pdf_filename": "test_document.pdf",
                "selected_text": "Second annotation"
            }
        ]

        mock_service_instance.get_annotations_for_pdf.return_value = mock_annotations

        # Make API request
        response = self.client.get("/annotations/test_user/test_document.pdf?course_id=test_course&book_id=test_book")

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("annotations", response_data)
        self.assertEqual(len(response_data["annotations"]), 2)

    @patch('services.annotation_service.AnnotationService')
    def test_get_annotation_by_id(self, mock_annotation_service):
        """Test getting a specific annotation by ID."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance

        mock_annotation = {
            "id": "test_id",
            "user_id": "test_user",
            "pdf_filename": "test_document.pdf",
            "selected_text": "Test annotation text"
        }

        mock_service_instance.get_annotation.return_value = mock_annotation

        # Make API request
        response = self.client.get("/annotations/test_user?annotation_id=test_id&pdf_filename=test_document.pdf")

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("annotation", response_data)
        self.assertEqual(response_data["annotation"]["id"], "test_id")

    @patch('services.annotation_service.AnnotationService')
    def test_get_annotation_not_found(self, mock_annotation_service):
        """Test getting a non-existent annotation."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance
        mock_service_instance.get_annotation.return_value = None

        # Make API request
        response = self.client.get("/annotations/test_user?annotation_id=nonexistent_id&pdf_filename=test_document.pdf")

        # Assert response
        self.assertEqual(response.status_code, 404)

    @patch('services.annotation_service.AnnotationService')
    def test_update_annotation(self, mock_annotation_service):
        """Test updating an annotation."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance

        updated_annotation = self.sample_annotation.copy()
        updated_annotation["id"] = "test_id"
        updated_annotation["content"] = "Updated content"
        updated_annotation["updated_at"] = "2023-01-01T00:00:00"

        mock_service_instance.update_annotation.return_value = updated_annotation

        # Make API request
        update_data = {"content": "Updated content"}
        response = self.client.put(
            "/annotations/test_user/test_id?pdf_filename=test_document.pdf&course_id=test_course&book_id=test_book",
            json=update_data
        )

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data["success"])
        self.assertIn("annotation", response_data)
        self.assertEqual(response_data["annotation"]["content"], "Updated content")

    @patch('services.annotation_service.AnnotationService')
    def test_delete_annotation(self, mock_annotation_service):
        """Test deleting an annotation."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance
        mock_service_instance.delete_annotation.return_value = True

        # Make API request
        response = self.client.delete(
            "/annotations/test_user/test_id?pdf_filename=test_document.pdf&course_id=test_course&book_id=test_book"
        )

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data["success"])

    @patch('services.annotation_service.AnnotationService')
    def test_delete_annotation_not_found(self, mock_annotation_service):
        """Test deleting a non-existent annotation."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance
        mock_service_instance.delete_annotation.return_value = False

        # Make API request
        response = self.client.delete(
            "/annotations/test_user/nonexistent_id?pdf_filename=test_document.pdf"
        )

        # Assert response
        self.assertEqual(response.status_code, 404)

    @patch('services.annotation_service.AnnotationService')
    def test_search_annotations(self, mock_annotation_service):
        """Test searching annotations."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance

        mock_search_results = [
            {
                "id": "search_result_1",
                "selected_text": "physics concept",
                "type": "highlight"
            },
            {
                "id": "search_result_2",
                "selected_text": "physics formula",
                "type": "note"
            }
        ]

        mock_service_instance.search_annotations.return_value = mock_search_results

        # Make API request
        search_request = {
            "query": "physics",
            "course_id": "test_course",
            "book_id": "test_book",
            "tags": ["important"],
            "annotation_type": "highlight"
        }
        response = self.client.post("/annotations/search/test_user", json=search_request)

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("annotations", response_data)
        self.assertEqual(len(response_data["annotations"]), 2)

    @patch('services.annotation_service.AnnotationService')
    def test_get_public_annotations(self, mock_annotation_service):
        """Test getting public annotations."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance

        mock_public_annotations = [
            {
                "id": "public_1",
                "user_id": "user1",
                "selected_text": "Public annotation 1"
            },
            {
                "id": "public_2",
                "user_id": "user2",
                "selected_text": "Public annotation 2"
            }
        ]

        mock_service_instance.get_public_annotations.return_value = mock_public_annotations

        # Make API request
        response = self.client.get("/annotations/public/test_document.pdf?course_id=test_course&book_id=test_book")

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("annotations", response_data)
        self.assertEqual(len(response_data["annotations"]), 2)

    @patch('services.annotation_service.AnnotationService')
    def test_export_annotations(self, mock_annotation_service):
        """Test exporting annotations."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance

        mock_export_data = {
            "user_id": "test_user",
            "export_date": "2023-01-01T00:00:00",
            "total_annotations": 2,
            "annotations": [
                {"id": "export_1", "selected_text": "First annotation"},
                {"id": "export_2", "selected_text": "Second annotation"}
            ]
        }

        mock_service_instance.export_annotations.return_value = mock_export_data

        # Make API request
        response = self.client.get("/annotations/test_user/export?format=json&course_id=test_course&book_id=test_book")

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["format"], "json")
        self.assertIn("data", response_data)
        self.assertEqual(response_data["data"]["total_annotations"], 2)

    @patch('services.annotation_service.AnnotationService')
    def test_import_annotations(self, mock_annotation_service):
        """Test importing annotations."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance
        mock_service_instance.import_annotations.return_value = 3

        # Make API request
        import_data = {
            "annotations": [
                {"id": "import_1", "selected_text": "Imported annotation 1"},
                {"id": "import_2", "selected_text": "Imported annotation 2"},
                {"id": "import_3", "selected_text": "Imported annotation 3"}
            ]
        }
        response = self.client.post("/annotations/test_user/import?format=json", json=import_data)

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["imported_count"], 3)

    @patch('services.annotation_service.AnnotationService')
    def test_get_annotation_stats(self, mock_annotation_service):
        """Test getting annotation statistics."""
        # Mock the service response
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance

        mock_stats = {
            "total_annotations": 10,
            "by_type": {"highlight": 5, "note": 3, "underline": 2},
            "by_pdf": {"test_document.pdf": 10},
            "by_page": {"1": 3, "2": 4, "3": 3},
            "public_annotations": 2,
            "favorite_annotations": 5,
            "tags_used": ["important", "test", "exam"],
            "recent_activity": [
                {"id": "recent_1", "type": "highlight", "created_at": "2023-01-01T00:00:00"}
            ]
        }

        mock_service_instance.get_annotation_stats.return_value = mock_stats

        # Make API request
        response = self.client.get("/annotations/test_user/stats?course_id=test_course&book_id=test_book")

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("stats", response_data)
        self.assertEqual(response_data["stats"]["total_annotations"], 10)
        self.assertEqual(response_data["stats"]["by_type"]["highlight"], 5)

    def test_export_annotations_invalid_format(self):
        """Test exporting annotations with invalid format."""
        # Make API request with invalid format
        response = self.client.get("/annotations/test_user/export?format=invalid")

        # Assert response
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported export format", response.json()["detail"])

    def test_import_annotations_invalid_format(self):
        """Test importing annotations with invalid format."""
        # Make API request with invalid format
        import_data = {"annotations": []}
        response = self.client.post("/annotations/test_user/import?format=invalid", json=import_data)

        # Assert response
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported import format", response.json()["detail"])

    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["status"], "healthy")
        self.assertIn("timestamp", response_data)


class TestAnnotationAPIErrorHandling(unittest.TestCase):
    """Test error handling in annotation API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    @patch('services.annotation_service.AnnotationService')
    def test_service_error_handling(self, mock_annotation_service):
        """Test API handles service errors gracefully."""
        # Mock service to raise an exception
        mock_service_instance = MagicMock()
        mock_annotation_service.return_value = mock_service_instance
        mock_service_instance.create_annotation.side_effect = Exception("Service error")

        # Make API request
        sample_annotation = {
            "user_id": "test_user",
            "pdf_filename": "test.pdf",
            "pdf_path": "/path/test.pdf",
            "page_number": 1
        }
        response = self.client.post("/annotations", json=sample_annotation)

        # Assert response
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertIn("detail", response_data)
        self.assertIn("Service error", response_data["detail"])

    def test_invalid_json_handling(self):
        """Test API handles invalid JSON gracefully."""
        # Make API request with invalid JSON
        response = self.client.post(
            "/annotations",
            data="invalid json content",
            headers={"content-type": "application/json"}
        )

        # Assert response
        self.assertEqual(response.status_code, 422)


class TestAnnotationAPIValidation(unittest.TestCase):
    """Test input validation in annotation API."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def test_create_annotation_validation(self):
        """Test validation of annotation creation data."""
        # Test missing required fields
        invalid_data = {
            "user_id": "test_user"
            # Missing pdf_filename, pdf_path, page_number
        }
        response = self.client.post("/annotations", json=invalid_data)
        self.assertEqual(response.status_code, 422)

        # Test invalid data types
        invalid_type_data = {
            "user_id": "test_user",
            "pdf_filename": "test.pdf",
            "pdf_path": "/path/test.pdf",
            "page_number": "not_a_number"  # Should be int
        }
        response = self.client.post("/annotations", json=invalid_type_data)
        self.assertEqual(response.status_code, 422)

    def test_search_annotation_validation(self):
        """Test validation of search request data."""
        # Test missing required query field
        invalid_search = {
            "course_id": "test_course"
            # Missing query field
        }
        response = self.client.post("/annotations/search/test_user", json=invalid_search)
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAnnotationAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestAnnotationAPIErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestAnnotationAPIValidation))

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