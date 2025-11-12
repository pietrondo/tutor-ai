"""
Comprehensive Course Management API Tests

This test suite validates all course management endpoints including:
- CRUD operations for courses
- Course validation and error handling
- Performance and security testing
- Integration with related services
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import json
import uuid
from typing import Dict, List

from main import app
from tests.utils.test_helpers import (
    APITestClient, TestConfig, assert_valid_course, assert_valid_book,
    assert_api_response_time, DatabaseManager, PerformanceMonitor
)


class TestCourseCRUDOperations:
    """Test comprehensive CRUD operations for courses."""

    @pytest_asyncio.asyncio
    async def test_create_course_success(self, api_client: APITestClient):
        """Test successful course creation."""
        course_data = TestConfig.SAMPLE_COURSE.copy()
        course_data["title"] = "New Test Course: Advanced Python Programming"

        async with assert_api_response_time(
            lambda: api_client.client.post("/courses", json=course_data),
            max_duration_ms=1000
        ) as response:
            assert response.status_code == 200
            course_response = response.json()
            assert_valid_course(course_response)
            assert course_response["title"] == course_data["title"]
            assert course_response["subject"] == course_data["subject"]
            assert "id" in course_response
            assert "created_at" in course_response

    @pytest_asyncio.asyncio
    async def test_create_course_missing_required_fields(self, api_client: APITestClient):
        """Test course creation with missing required fields."""
        # Missing title
        invalid_data = {
            "description": "A course without a title",
            "subject": "Computer Science"
        }
        response = await api_client.client.post("/courses", json=invalid_data)
        assert response.status_code == 422  # Validation error

        # Missing subject
        invalid_data = {
            "title": "Test Course",
            "description": "A course without a subject"
        }
        response = await api_client.client.post("/courses", json=invalid_data)
        assert response.status_code == 422

    @pytest_asyncio.asyncio
    async def test_create_course_invalid_data(self, api_client: APITestClient):
        """Test course creation with invalid data."""
        # Empty title
        invalid_data = {
            "title": "",
            "description": "Course with empty title",
            "subject": "Computer Science"
        }
        response = await api_client.client.post("/courses", json=invalid_data)
        assert response.status_code == 422

        # Title too long
        invalid_data = {
            "title": "x" * 1000,  # Very long title
            "description": "Course with extremely long title",
            "subject": "Computer Science"
        }
        response = await api_client.client.post("/courses", json=invalid_data)
        assert response.status_code == 422

    @pytest_asyncio.asyncio
    async def test_get_all_courses_empty(self, api_client: APITestClient):
        """Test getting all courses when none exist."""
        response = await api_client.client.get("/courses")
        assert response.status_code == 200
        courses_response = response.json()
        assert "courses" in courses_response
        assert isinstance(courses_response["courses"], list)
        assert len(courses_response["courses"]) == 0

    @pytest_asyncio.asyncio
    async def test_get_all_courses_with_data(self, api_client: APITestClient):
        """Test getting all courses when courses exist."""
        # Create multiple courses
        courses = []
        for i in range(3):
            course_data = TestConfig.SAMPLE_COURSE.copy()
            course_data["title"] = f"Test Course {i+1}"
            created_course = await api_client.create_test_course(course_data)
            courses.append(created_course)

        # Get all courses
        response = await api_client.client.get("/courses")
        assert response.status_code == 200
        courses_response = response.json()
        assert "courses" in courses_response
        assert len(courses_response["courses"]) >= 3

        # Verify created courses are in the list
        course_ids = [course["id"] for course in courses_response["courses"]]
        for created_course in courses:
            assert created_course["id"] in course_ids

    @pytest_asyncio.asyncio
    async def test_get_course_by_id_success(self, api_client: APITestClient):
        """Test getting a specific course by ID."""
        # Create a course
        created_course = await api_client.create_test_course()
        course_id = created_course["id"]

        # Get the course
        response = await api_client.client.get(f"/courses/{course_id}")
        assert response.status_code == 200
        retrieved_course = response.json()
        assert_valid_course(retrieved_course)
        assert retrieved_course["id"] == course_id
        assert retrieved_course["title"] == created_course["title"]

    @pytest_asyncio.asyncio
    async def test_get_course_by_id_not_found(self, api_client: APITestClient):
        """Test getting a non-existent course."""
        fake_id = str(uuid.uuid4())
        response = await api_client.client.get(f"/courses/{fake_id}")
        assert response.status_code == 404
        error_response = response.json()
        assert "detail" in error_response
        assert "not found" in error_response["detail"].lower()

    @pytest_asyncio.asyncio
    async def test_update_course_success(self, api_client: APITestClient):
        """Test successful course update."""
        # Create a course
        created_course = await api_client.create_test_course()
        course_id = created_course["id"]

        # Update data
        update_data = {
            "title": "Updated Course Title",
            "description": "Updated course description",
            "difficulty_level": "advanced"
        }

        # Update the course
        response = await api_client.client.put(f"/courses/{course_id}", json=update_data)
        assert response.status_code == 200
        updated_course = response.json()
        assert_valid_course(updated_course)
        assert updated_course["id"] == course_id
        assert updated_course["title"] == update_data["title"]
        assert updated_course["description"] == update_data["description"]
        assert updated_course["difficulty_level"] == update_data["difficulty_level"]

    @pytest_asyncio.asyncio
    async def test_update_course_not_found(self, api_client: APITestClient):
        """Test updating a non-existent course."""
        fake_id = str(uuid.uuid4())
        update_data = {"title": "Updated Title"}
        response = await api_client.client.put(f"/courses/{fake_id}", json=update_data)
        assert response.status_code == 404

    @pytest_asyncio.asyncio
    async def test_delete_course_success(self, api_client: APITestClient):
        """Test successful course deletion."""
        # Create a course
        created_course = await api_client.create_test_course()
        course_id = created_course["id"]

        # Delete the course
        response = await api_client.client.delete(f"/courses/{course_id}")
        assert response.status_code == 200
        delete_response = response.json()
        assert "message" in delete_response
        assert "deleted" in delete_response["message"].lower()

        # Verify course is gone
        response = await api_client.client.get(f"/courses/{course_id}")
        assert response.status_code == 404

    @pytest_asyncio.asyncio
    async def test_delete_course_not_found(self, api_client: APITestClient):
        """Test deleting a non-existent course."""
        fake_id = str(uuid.uuid4())
        response = await api_client.client.delete(f"/courses/{fake_id}")
        assert response.status_code == 404


class TestCourseValidationAndSecurity:
    """Test course validation and security aspects."""

    @pytest_asyncio.asyncio
    async def test_sql_injection_attempt(self, api_client: APITestClient):
        """Test SQL injection attempts in course data."""
        malicious_data = {
            "title": "'; DROP TABLE courses; --",
            "description": "Test course with SQL injection attempt",
            "subject": "Computer Science"
        }
        response = await api_client.client.post("/courses", json=malicious_data)
        # Should either succeed with sanitized data or fail validation
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            # Verify no SQL injection occurred
            courses_response = await api_client.client.get("/courses")
            assert courses_response.status_code == 200
            # Database should still be intact

    @pytest_asyncio.asyncio
    async def test_xss_attempt(self, api_client: APITestClient):
        """Test XSS attempts in course data."""
        xss_data = {
            "title": "<script>alert('xss')</script>",
            "description": "<img src=x onerror=alert('xss')>",
            "subject": "Computer Science"
        }
        response = await api_client.client.post("/courses", json=xss_data)
        # Should either succeed with sanitized data or fail validation
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            # Verify XSS was sanitized
            course_response = response.json()
            assert "<script>" not in course_response["title"]
            assert "onerror" not in course_response["description"]

    @pytest_asyncio.asyncio
    async def test_unicode_handling(self, api_client: APITestClient):
        """Test proper handling of Unicode characters."""
        unicode_data = {
            "title": "测试课程：机器学习基础 🎓",
            "description": "这是一个包含emoji和中文字符的课程描述 📚",
            "subject": "人工智能"
        }
        response = await api_client.client.post("/courses", json=unicode_data)
        assert response.status_code == 200
        course_response = response.json()
        assert_valid_course(course_response)
        assert course_response["title"] == unicode_data["title"]
        assert course_response["description"] == unicode_data["description"]

    @pytest_asyncio.asyncio
    async def test_large_payload_handling(self, api_client: APITestClient):
        """Test handling of large payloads."""
        large_description = "A" * 10000  # 10KB description
        large_data = {
            "title": "Large Course Title",
            "description": large_description,
            "subject": "Computer Science"
        }
        response = await api_client.client.post("/courses", json=large_data)
        # Should either accept or reject based on size limits
        assert response.status_code in [200, 413, 422]


class TestCoursePerformance:
    """Test course management performance."""

    @pytest_asyncio.asyncio
    async def test_course_creation_performance(self, api_client: APITestClient):
        """Test course creation performance under load."""
        monitor = PerformanceMonitor()
        course_ids = []

        # Create 10 courses and measure performance
        for i in range(10):
            with monitor.start_timer(f"create_course_{i}"):
                course_data = TestConfig.SAMPLE_COURSE.copy()
                course_data["title"] = f"Performance Test Course {i}"
                response = await api_client.client.post("/courses", json=course_data)
                assert response.status_code == 200
                course_ids.append(response.json()["id"])

        # Assert all operations completed within reasonable time
        monitor.assert_performance(max_duration_ms=2000)

        # Cleanup
        for course_id in course_ids:
            await api_client.client.delete(f"/courses/{course_id}")

    @pytest_asyncio.asyncio
    async def test_course_list_performance(self, api_client: APITestClient):
        """Test course listing performance with many courses."""
        # Create 50 courses
        course_ids = []
        for i in range(50):
            course_data = TestConfig.SAMPLE_COURSE.copy()
            course_data["title"] = f"List Test Course {i}"
            response = await api_client.client.post("/courses", json=course_data)
            course_ids.append(response.json()["id"])

        # Measure list performance
        with PerformanceMonitor().start_timer("list_courses") as timer:
            response = await api_client.client.get("/courses")
            assert response.status_code == 200
            courses_response = response.json()
            assert len(courses_response["courses"]) >= 50

        # Should complete within 1 second
        assert timer.duration_ms < 1000

        # Cleanup
        for course_id in course_ids:
            await api_client.client.delete(f"/courses/{course_id}")


class TestCourseIntegration:
    """Test course integration with other services."""

    @pytest_asyncio.asyncio
    async def test_course_with_books_workflow(self, api_client: APITestClient):
        """Test complete workflow: create course -> upload PDF -> verify books."""
        # Create course
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Upload PDF
        pdf_response = await api_client.upload_test_pdf(course_id)
        assert pdf_response["status"] == "success"

        # Get course books
        books_response = await api_client.client.get(f"/courses/{course_id}/books")
        assert books_response.status_code == 200
        books = books_response.json()
        assert isinstance(books, list)
        assert len(books) > 0

        # Verify book structure
        book = books[0]
        assert_valid_book(book)
        assert book["course_id"] == course_id

    @pytest_asyncio.asyncio
    async def test_course_materials_integration(self, api_client: APITestClient):
        """Test course materials endpoint integration."""
        # Create course and upload PDF
        course = await api_client.create_test_course()
        course_id = course["id"]
        await api_client.upload_test_pdf(course_id)

        # Get materials
        materials_response = await api_client.client.get(f"/courses/{course_id}/materials")
        assert materials_response.status_code == 200
        materials = materials_response.json()
        assert "materials" in materials
        assert isinstance(materials["materials"], list)
        assert len(materials["materials"]) > 0

        # Verify material structure
        material = materials["materials"][0]
        assert "filename" in material
        assert "read_url" in material
        assert "download_url" in material
        assert "book_id" in material

    @pytest_asyncio.asyncio
    async def test_course_deletion_cascade(self, api_client: APITestClient):
        """Test that course deletion properly cascades to related data."""
        # Create course and upload PDF
        course = await api_client.create_test_course()
        course_id = course["id"]
        pdf_response = await api_client.upload_test_pdf(course_id)
        book_id = pdf_response.get("book_id")

        # Verify data exists
        books_response = await api_client.client.get(f"/courses/{course_id}/books")
        assert len(books_response.json()) > 0

        # Delete course
        response = await api_client.client.delete(f"/courses/{course_id}")
        assert response.status_code == 200

        # Verify course is gone
        response = await api_client.client.get(f"/courses/{course_id}")
        assert response.status_code == 404

        # Verify books are gone (or properly handled)
        books_response = await api_client.client.get(f"/courses/{course_id}/books")
        # Should either return 404 or empty list depending on implementation
        assert books_response.status_code in [404, 200]
        if books_response.status_code == 200:
            assert len(books_response.json()) == 0


class TestCourseErrorHandling:
    """Test error handling and edge cases."""

    @pytest_asyncio.asyncio
    async def test_invalid_course_id_format(self, api_client: APITestClient):
        """Test handling of invalid course ID formats."""
        invalid_ids = [
            "invalid-uuid",
            "123",
            "",
            "null",
            "../",
            "%2e%2e%2f"
        ]

        for invalid_id in invalid_ids:
            response = await api_client.client.get(f"/courses/{invalid_id}")
            # Should return 404 or 422 depending on validation
            assert response.status_code in [404, 422]

    @pytest_asyncio.asyncio
    async def test_concurrent_course_creation(self, api_client: APITestClient):
        """Test concurrent course creation."""
        import asyncio

        async def create_course(index):
            course_data = TestConfig.SAMPLE_COURSE.copy()
            course_data["title"] = f"Concurrent Course {index}"
            response = await api_client.client.post("/courses", json=course_data)
            return response

        # Create 5 courses concurrently
        tasks = [create_course(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert_valid_course(response.json())

    @pytest_asyncio.asyncio
    async def test_malformed_json_request(self, api_client: APITestClient):
        """Test handling of malformed JSON requests."""
        # Test with invalid JSON
        malformed_json = '{"title": "test", "description": "test", "subject": "test",}'

        # This should be handled by FastAPI's JSON parsing
        # but we test the endpoint's robustness
        response = await api_client.client.post(
            "/courses",
            content=malformed_json,
            headers={"Content-Type": "application/json"}
        )
        # Should handle gracefully
        assert response.status_code in [422, 400]

    @pytest_asyncio.asyncio
    async def test_empty_request_body(self, api_client: APITestClient):
        """Test handling of empty request body."""
        response = await api_client.client.post(
            "/courses",
            content="",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @pytest_asyncio.asyncio
    async def test_content_type_handling(self, api_client: APITestClient):
        """Test handling of different content types."""
        course_data = TestConfig.SAMPLE_COURSE.copy()

        # Test with wrong content type
        response = await api_client.client.post(
            "/courses",
            data=json.dumps(course_data),
            headers={"Content-Type": "text/plain"}
        )
        # Should either accept or reject based on configuration
        assert response.status_code in [200, 415, 422]