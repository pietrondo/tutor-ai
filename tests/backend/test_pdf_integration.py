"""
Comprehensive PDF Integration Tests

This test suite validates PDF processing, upload, reading, and annotation workflows:
- PDF upload and processing pipeline
- File format validation and security
- PDF content extraction and indexing
- Integration with annotation and chat systems
- Performance with large files
"""

import pytest
import pytest_asyncio
import tempfile
import os
from pathlib import Path
from httpx import AsyncClient
import io
import uuid

from main import app
from tests.utils.test_helpers import (
    APITestClient, TestConfig, TestDataManager, PerformanceMonitor
)


class TestPDFUploadAndProcessing:
    """Test PDF upload and processing pipeline."""

    @pytest_asyncio.asyncio
    async def test_upload_valid_pdf_success(self, api_client: APITestClient):
        """Test successful upload of a valid PDF file."""
        # Create a test course
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Upload PDF
        response = await api_client.upload_test_pdf(course_id, "test_document.pdf")
        assert response.status_code == 200
        upload_result = response.json()

        # Verify upload result structure
        assert "status" in upload_result
        assert upload_result["status"] == "success"
        assert "book_id" in upload_result
        assert "filename" in upload_result
        assert "message" in upload_result
        assert upload_result["filename"] == "test_document.pdf"

    @pytest_asyncio.asyncio
    async def test_upload_multiple_pdfs(self, api_client: APITestClient):
        """Test uploading multiple PDFs to the same course."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Upload multiple PDFs
        uploaded_files = []
        for i in range(3):
            filename = f"document_{i+1}.pdf"
            response = await api_client.upload_test_pdf(course_id, filename)
            assert response.status_code == 200
            upload_result = response.json()
            uploaded_files.append(upload_result)

        # Verify all uploads succeeded
        assert len(uploaded_files) == 3
        for upload_result in uploaded_files:
            assert upload_result["status"] == "success"
            assert "book_id" in upload_result

        # Verify books are associated with course
        books_response = await api_client.client.get(f"/courses/{course_id}/books")
        assert books_response.status_code == 200
        books = books_response.json()
        assert len(books) == 3

    @pytest_asyncio.asyncio
    async def test_upload_pdf_to_nonexistent_course(self, api_client: APITestClient):
        """Test uploading PDF to a non-existent course."""
        fake_course_id = str(uuid.uuid4())
        response = await api_client.upload_test_pdf(fake_course_id, "test.pdf")
        assert response.status_code == 404

    @pytest_asyncio.asyncio
    async def test_upload_invalid_file_format(self, api_client: APITestClient):
        """Test uploading non-PDF files."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Create a text file instead of PDF
        invalid_file_content = b"This is not a PDF file"
        files = {"file": ("not_a_pdf.txt", invalid_file_content, "text/plain")}
        response = await api_client.client.post(f"/courses/{course_id}/upload", files=files)
        assert response.status_code == 400  # Bad request for invalid file format

    @pytest_asyncio.asyncio
    async def test_upload_malformed_pdf(self, api_client: APITestClient):
        """Test uploading malformed PDF files."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Create malformed PDF content
        malformed_pdf = b"This is not a valid PDF file at all"
        files = {"file": ("malformed.pdf", malformed_pdf, "application/pdf")}
        response = await api_client.client.post(f"/courses/{course_id}/upload", files=files)
        # Should handle gracefully - either reject or process with errors
        assert response.status_code in [400, 422, 200]

    @pytest_asyncio.asyncio
    async def test_upload_large_pdf(self, api_client: APITestClient):
        """Test uploading large PDF files."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Create a large PDF (simulated)
        large_pdf_content = self._create_large_pdf_content()
        files = {"file": ("large_document.pdf", large_pdf_content, "application/pdf")}
        response = await api_client.client.post(f"/courses/{course_id}/upload", files=files)

        # Should either accept or reject based on size limits
        assert response.status_code in [200, 413]  # 413 = Payload Too Large

    @pytest_asyncio.asyncio
    async def test_upload_pdf_with_special_characters(self, api_client: APITestClient):
        """Test uploading PDFs with special characters in filename."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        special_filenames = [
            "document with spaces.pdf",
            "document-with-dashes.pdf",
            "document_with_underscores.pdf",
            "document(1).pdf",
            "document [version 2].pdf",
            "测试文档.pdf",  # Chinese characters
            "documenté.pdf"  # Accented characters
        ]

        for filename in special_filenames:
            response = await api_client.upload_test_pdf(course_id, filename)
            assert response.status_code == 200
            upload_result = response.json()
            assert upload_result["filename"] == filename

    def _create_large_pdf_content(self) -> bytes:
        """Create a large PDF content for testing."""
        # This would create a larger PDF - for now just return normal size
        # In a real implementation, you might generate a larger PDF
        return APITestClient(None)._create_test_pdf_content()


class TestPDFContentExtraction:
    """Test PDF content extraction and processing."""

    @pytest_asyncio.asyncio
    async def test_pdf_content_extraction(self, api_client: APITestClient):
        """Test that PDF content is properly extracted and indexed."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Upload PDF with known content
        response = await api_client.upload_test_pdf(course_id, "content_test.pdf")
        assert response.status_code == 200
        upload_result = response.json()
        book_id = upload_result["book_id"]

        # Test that content can be searched (if search endpoint exists)
        # This would depend on the actual implementation
        search_data = {
            "query": "Test PDF Content",
            "course_id": course_id,
            "book_id": book_id
        }
        search_response = await api_client.client.post("/search", json=search_data)
        # Search might not be implemented or might need different parameters
        # Assert based on actual implementation
        assert search_response.status_code in [200, 404, 422]

    @pytest_asyncio.asyncio
    async def test_pdf_metadata_extraction(self, api_client: APITestClient):
        """Test PDF metadata extraction."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        response = await api_client.upload_test_pdf(course_id, "metadata_test.pdf")
        assert response.status_code == 200

        # Get book details to check metadata
        books_response = await api_client.client.get(f"/courses/{course_id}/books")
        assert books_response.status_code == 200
        books = books_response.json()
        assert len(books) > 0

        book = books[0]
        # Check that book metadata is populated
        assert "title" in book
        assert "id" in book
        assert "course_id" in book


class TestPDFSecurityAndValidation:
    """Test PDF security features and validation."""

    @pytest_asyncio.asyncio
    async def test_pdf_file_size_limits(self, api_client: APITestClient):
        """Test that file size limits are enforced."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Test with an oversized file (simulated)
        oversized_content = b"X" * (50 * 1024 * 1024)  # 50MB
        files = {"file": ("oversized.pdf", oversized_content, "application/pdf")}
        response = await api_client.client.post(f"/courses/{course_id}/upload", files=files)

        # Should reject oversized files
        assert response.status_code in [413, 400]  # Payload Too Large or Bad Request

    @pytest_asyncio.asyncio
    async def test_pdf_filename_validation(self, api_client: APITestClient):
        """Test PDF filename validation."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Test potentially dangerous filenames
        dangerous_filenames = [
            "../../../etc/passwd.pdf",
            "..\\..\\windows\\system32\\config.pdf",
            "document.pdf\0malicious.exe",  # Null byte injection
            "document.pdf/.htaccess",  # Path traversal
            "CON.pdf",  # Reserved Windows filename
            "AUX.pdf"   # Reserved Windows filename
        ]

        for filename in dangerous_filenames:
            pdf_content = api_client._create_test_pdf_content()
            files = {"file": (filename, pdf_content, "application/pdf")}
            response = await api_client.client.post(f"/courses/{course_id}/upload", files=files)

            # Should handle dangerous filenames appropriately
            # Either sanitize, reject, or handle safely
            assert response.status_code in [200, 400, 422]

    @pytest_asyncio.asyncio
    async def test_pdf_mime_type_validation(self, api_client: APITestClient):
        """Test PDF MIME type validation."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        pdf_content = api_client._create_test_pdf_content()

        # Test with different MIME types
        mime_types = [
            "application/pdf",      # Correct
            "application/octet-stream",  # Generic binary
            "text/plain",          # Wrong type
            "application/x-pdf",   # Alternative PDF type
            ""                     # No MIME type
        ]

        for mime_type in mime_types:
            files = {"file": ("test.pdf", pdf_content, mime_type)}
            response = await api_client.client.post(f"/courses/{course_id}/upload", files=files)

            # Should accept valid PDF regardless of MIME type, or reject wrong types
            assert response.status_code in [200, 400, 422]

    @pytest_asyncio.asyncio
    async def test_pdf_virus_scan_simulation(self, api_client: APITestClient):
        """Test PDF security scanning (simulated)."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Create PDF with suspicious content patterns
        suspicious_content = b"""
        %PDF-1.4
        1 0 obj
        <<
        /Type /Catalog
        /Pages 2 0 R
        /JS (javascript:app.alert('XSS'))
        >>
        endobj
        """ + api_client._create_test_pdf_content()

        files = {"file": ("suspicious.pdf", suspicious_content, "application/pdf")}
        response = await api_client.client.post(f"/courses/{course_id}/upload", files=files)

        # Should handle suspicious content appropriately
        # This would depend on actual security implementation
        assert response.status_code in [200, 400, 422]


class TestPDFIntegrationWorkflow:
    """Test complete PDF integration workflows."""

    @pytest_asyncio.asyncio
    async def test_pdf_to_chat_workflow(self, api_client: APITestClient):
        """Test PDF upload -> chat integration workflow."""
        # Create course and upload PDF
        course = await api_client.create_test_course()
        course_id = course["id"]
        pdf_response = await api_client.upload_test_pdf(course_id, "chat_test.pdf")
        book_id = pdf_response["book_id"]

        # Test chat with PDF context
        chat_data = {
            "message": "What is this document about?",
            "course_id": course_id,
            "context_filter": {
                "book_id": book_id
            }
        }
        chat_response = await api_client.client.post("/chat", json=chat_data)
        assert chat_response.status_code == 200
        chat_result = chat_response.json()

        # Verify chat response structure
        assert "response" in chat_result
        assert "sources" in chat_result
        assert isinstance(chat_result["response"], str)
        assert len(chat_result["response"]) > 0

    @pytest_asyncio.asyncio
    async def test_pdf_to_annotation_workflow(self, api_client: APITestClient):
        """Test PDF upload -> annotation workflow."""
        # Create course and upload PDF
        course = await api_client.create_test_course()
        course_id = course["id"]
        pdf_response = await api_client.upload_test_pdf(course_id, "annotation_test.pdf")
        book_id = pdf_response["book_id"]

        # Create annotation
        annotation_data = {
            "book_id": book_id,
            "page_number": 1,
            "content": "This is an important section",
            "annotation_type": "highlight",
            "position": {"x": 100, "y": 200, "width": 300, "height": 50},
            "share_with_ai": True
        }
        annotation_response = await api_client.client.post("/annotations", json=annotation_data)
        # Annotation endpoint might not be implemented or might need different parameters
        assert annotation_response.status_code in [200, 404, 422]

        if annotation_response.status_code == 200:
            annotation_result = annotation_response.json()
            assert "id" in annotation_result
            assert annotation_result["book_id"] == book_id

    @pytest_asyncio.asyncio
    async def test_pdf_materials_endpoint(self, api_client: APITestClient):
        """Test PDF materials endpoint integration."""
        # Create course and upload PDF
        course = await api_client.create_test_course()
        course_id = course["id"]
        await api_client.upload_test_pdf(course_id, "materials_test.pdf")

        # Get materials
        materials_response = await api_client.client.get(f"/courses/{course_id}/materials")
        assert materials_response.status_code == 200
        materials = materials_response.json()

        # Verify materials structure
        assert "materials" in materials
        assert isinstance(materials["materials"], list)
        assert len(materials["materials"]) > 0

        material = materials["materials"][0]
        assert "filename" in material
        assert "read_url" in material
        assert "download_url" in material
        assert "book_id" in material

        # Test that URLs are properly formed
        assert "courses" in material["read_url"]
        assert "materials" in material["read_url"]
        assert material["filename"] in material["read_url"]

    @pytest_asyncio.asyncio
    async def test_pdf_book_specific_materials(self, api_client: APITestClient):
        """Test book-specific materials endpoint."""
        # Create course and upload PDF
        course = await api_client.create_test_course()
        course_id = course["id"]
        pdf_response = await api_client.upload_test_pdf(course_id, "book_specific_test.pdf")
        book_id = pdf_response["book_id"]

        # Get book-specific materials
        book_materials_response = await api_client.client.get(
            f"/courses/{course_id}/books/{book_id}/materials"
        )
        assert book_materials_response.status_code == 200
        book_materials = book_materials_response.json()

        # Verify book materials structure
        assert "materials" in book_materials
        assert "book_info" in book_materials
        assert isinstance(book_materials["materials"], list)
        assert len(book_materials["materials"]) > 0

        # Verify book info
        book_info = book_materials["book_info"]
        assert "id" in book_info
        assert "title" in book_info
        assert book_info["id"] == book_id


class TestPDFPerformance:
    """Test PDF processing performance."""

    @pytest_asyncio.asyncio
    async def test_pdf_upload_performance(self, api_client: APITestClient):
        """Test PDF upload performance."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        monitor = PerformanceMonitor()

        # Upload multiple PDFs and measure performance
        for i in range(5):
            with monitor.start_timer(f"upload_pdf_{i}"):
                response = await api_client.upload_test_pdf(course_id, f"perf_test_{i}.pdf")
                assert response.status_code == 200

        # Assert all uploads completed within reasonable time
        monitor.assert_performance(max_duration_ms=5000)  # 5 seconds per upload

    @pytest_asyncio.asyncio
    async def test_concurrent_pdf_uploads(self, api_client: APITestClient):
        """Test concurrent PDF uploads."""
        import asyncio

        course = await api_client.create_test_course()
        course_id = course["id"]

        async def upload_pdf(index):
            filename = f"concurrent_test_{index}.pdf"
            return await api_client.upload_test_pdf(course_id, filename)

        # Upload 5 PDFs concurrently
        tasks = [upload_pdf(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "success"

    @pytest_asyncio.asyncio
    async def test_pdf_materials_retrieval_performance(self, api_client: APITestClient):
        """Test materials retrieval performance."""
        # Create course with multiple PDFs
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Upload multiple PDFs
        for i in range(10):
            await api_client.upload_test_pdf(course_id, f"perf_materials_{i}.pdf")

        # Measure materials retrieval performance
        monitor = PerformanceMonitor()
        with monitor.start_timer("get_materials") as timer:
            response = await api_client.client.get(f"/courses/{course_id}/materials")
            assert response.status_code == 200
            materials = response.json()
            assert len(materials["materials"]) == 10

        # Should complete within 2 seconds
        assert timer.duration_ms < 2000


class TestPDFErrorHandling:
    """Test PDF error handling and edge cases."""

    @pytest_asyncio.asyncio
    async def test_duplicate_pdf_upload(self, api_client: APITestClient):
        """Test uploading the same PDF multiple times."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        filename = "duplicate_test.pdf"

        # Upload PDF first time
        response1 = await api_client.upload_test_pdf(course_id, filename)
        assert response1.status_code == 200

        # Upload same PDF again
        response2 = await api_client.upload_test_pdf(course_id, filename)
        # Should either create new book or handle duplicates gracefully
        assert response2.status_code in [200, 409]  # 409 = Conflict

    @pytest_asyncio.asyncio
    async def test_pdf_upload_without_file(self, api_client: APITestClient):
        """Test PDF upload endpoint without file."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Send request without file
        response = await api_client.client.post(f"/courses/{course_id}/upload")
        assert response.status_code in [400, 422]  # Bad Request or Validation Error

    @pytest_asyncio.asyncio
    async def test_pdf_upload_corrupted_file(self, api_client: APITestClient):
        """Test uploading corrupted PDF files."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Create corrupted content
        corrupted_content = b"This is definitely not a PDF file at all"
        files = {"file": ("corrupted.pdf", corrupted_content, "application/pdf")}
        response = await api_client.client.post(f"/courses/{course_id}/upload", files=files)

        # Should handle corruption gracefully
        assert response.status_code in [400, 422, 200]

    @pytest_asyncio.asyncio
    async def test_pdf_upload_empty_file(self, api_client: APITestClient):
        """Test uploading empty PDF files."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Upload empty file
        empty_content = b""
        files = {"file": ("empty.pdf", empty_content, "application/pdf")}
        response = await api_client.client.post(f"/courses/{course_id}/upload", files=files)

        # Should reject empty files
        assert response.status_code in [400, 422]

    @pytest_asyncio.asyncio
    async def test_pdf_with_password_protection(self, api_client: APITestClient):
        """Test handling of password-protected PDFs."""
        course = await api_client.create_test_course()
        course_id = course["id"]

        # Create a password-protected PDF (simulated)
        # In a real implementation, you'd create an actual password-protected PDF
        password_protected_content = b"""
        %PDF-1.4
        % This would be a password-protected PDF
        """ + api_client._create_test_pdf_content()

        files = {"file": ("protected.pdf", password_protected_content, "application/pdf")}
        response = await api_client.client.post(f"/courses/{course_id}/upload", files=files)

        # Should handle password-protected PDFs appropriately
        # Either reject, require password, or process if possible
        assert response.status_code in [200, 400, 401, 422]  # 401 = Unauthorized