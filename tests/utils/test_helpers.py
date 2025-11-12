"""
Test utilities and fixtures for Tutor-AI comprehensive testing suite.

This module provides common utilities, fixtures, and helper functions
for all backend tests to ensure consistency and reduce duplication.
"""

import asyncio
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncGenerator
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import aiosqlite

from main import app
from services.course_service import CourseService
from services.llm_service import LLMService
from services.rag_service import RAGService


class TestConfig:
    """Test configuration constants."""
    TEST_DATABASE_URL = "sqlite:///./test_data.db"
    TEST_UPLOAD_DIR = "./test_uploads"
    TEST_VECTOR_DB_PATH = "./test_vector_db"

    # Sample test data
    SAMPLE_COURSE = {
        "title": "Test Course: Introduction to Computer Science",
        "description": "A comprehensive test course covering fundamental CS concepts",
        "subject": "Computer Science",
        "difficulty_level": "beginner"
    }

    SAMPLE_BOOK = {
        "title": "Test Book: Algorithms Explained",
        "author": "Test Author",
        "description": "A test book covering algorithm fundamentals",
        "isbn": "978-0-123456-78-9"
    }

    SAMPLE_CHAT_MESSAGE = {
        "message": "What is machine learning and how does it work?",
        "course_id": "test-course-id",
        "context_filter": {
            "book_id": "test-book-id"
        }
    }


class APITestClient:
    """Enhanced API test client with common utilities."""

    def __init__(self, client: AsyncClient):
        self.client = client

    async def create_test_course(self, course_data: Optional[Dict] = None) -> Dict:
        """Create a test course and return its data."""
        data = course_data or TestConfig.SAMPLE_COURSE.copy()
        response = await self.client.post("/courses", json=data)
        assert response.status_code == 200, f"Failed to create course: {response.text}"
        return response.json()

    async def upload_test_pdf(self, course_id: str, filename: str = "test.pdf") -> Dict:
        """Upload a test PDF to the specified course."""
        # Create a minimal valid PDF for testing
        pdf_content = self._create_test_pdf_content()

        files = {"file": (filename, pdf_content, "application/pdf")}
        response = await self.client.post(f"/courses/{course_id}/upload", files=files)
        assert response.status_code == 200, f"Failed to upload PDF: {response.text}"
        return response.json()

    async def send_chat_message(self, message_data: Optional[Dict] = None) -> Dict:
        """Send a chat message and return the response."""
        data = message_data or TestConfig.SAMPLE_CHAT_MESSAGE.copy()
        response = await self.client.post("/chat", json=data)
        assert response.status_code == 200, f"Chat request failed: {response.text}"
        return response.json()

    def _create_test_pdf_content(self) -> bytes:
        """Create minimal PDF content for testing."""
        # This creates a valid but minimal PDF
        minimal_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000203 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
312
%%EOF"""
        return minimal_pdf


class MockLLMService:
    """Mock LLM service for reproducible testing."""

    def __init__(self):
        self.responses = {
            "default": "This is a mock AI response for testing purposes.",
            "chat": "Based on the course materials, here's a comprehensive explanation...",
            "quiz": {
                "questions": [
                    {
                        "question": "What is the primary concept discussed in this material?",
                        "type": "multiple_choice",
                        "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
                        "correct_answer": 0,
                        "explanation": "This is the correct explanation..."
                    }
                ]
            },
            "mindmap": {
                "central_concept": "Test Concept",
                "branches": [
                    {"text": "Branch 1", "children": [{"text": "Sub-branch 1.1"}]},
                    {"text": "Branch 2", "children": [{"text": "Sub-branch 2.1"}]}
                ]
            }
        }
        self.call_count = 0

    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate mock response."""
        self.call_count += 1
        response_type = kwargs.get("response_type", "default")
        return self.responses.get(response_type, self.responses["default"])

    async def generate_quiz(self, content: str, **kwargs) -> Dict:
        """Generate mock quiz."""
        self.call_count += 1
        return self.responses["quiz"]

    async def generate_mindmap(self, concept: str, **kwargs) -> Dict:
        """Generate mock mindmap."""
        self.call_count += 1
        return self.responses["mindmap"]


class PerformanceMonitor:
    """Monitor performance during tests."""

    def __init__(self):
        self.metrics = []

    def start_timer(self, operation: str) -> 'Timer':
        """Start a new timer for the given operation."""
        return Timer(operation, self.metrics)

    def get_metrics(self) -> List[Dict]:
        """Get all collected metrics."""
        return self.metrics.copy()

    def assert_performance(self, max_duration_ms: float = 2000):
        """Assert that all operations completed within the time limit."""
        for metric in self.metrics:
            duration_ms = metric["duration_ms"]
            assert duration_ms <= max_duration_ms, \
                f"Operation '{metric['operation']}' took {duration_ms}ms, expected < {max_duration_ms}ms"


class Timer:
    """Context manager for timing operations."""

    def __init__(self, operation: str, metrics: List[Dict]):
        self.operation = operation
        self.metrics = metrics
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.metrics.append({
                "operation": self.operation,
                "duration_ms": duration_ms,
                "timestamp": time.time()
            })


class DatabaseManager:
    """Manage test database state."""

    def __init__(self, db_path: str = "./test_data.db"):
        self.db_path = db_path

    async def setup_test_database(self):
        """Set up a clean test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        # Initialize database with schema
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    subject TEXT,
                    difficulty_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id TEXT PRIMARY KEY,
                    course_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT,
                    description TEXT,
                    file_path TEXT,
                    FOREIGN KEY (course_id) REFERENCES courses (id)
                )
            """)
            await db.commit()

    async def cleanup_test_database(self):
        """Clean up the test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    async def insert_test_course(self, course_data: Dict) -> str:
        """Insert a test course into the database."""
        course_id = str(uuid.uuid4())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO courses (id, title, description, subject, difficulty_level)
                VALUES (?, ?, ?, ?, ?)
            """, (course_id, course_data["title"], course_data["description"],
                  course_data["subject"], course_data["difficulty_level"]))
            await db.commit()
        return course_id

    async def insert_test_book(self, book_data: Dict, course_id: str) -> str:
        """Insert a test book into the database."""
        book_id = str(uuid.uuid4())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO books (id, course_id, title, author, description, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (book_id, course_id, book_data["title"], book_data["author"],
                  book_data["description"], book_data.get("file_path", "")))
            await db.commit()
        return book_id


# Pytest fixtures
@pytest_asyncio.fixture
async def test_db_manager():
    """Fixture for database management."""
    manager = DatabaseManager()
    await manager.setup_test_database()
    yield manager
    await manager.cleanup_test_database()


@pytest_asyncio.fixture
async def api_client():
    """Fixture for API test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield APITestClient(client)


@pytest_asyncio.fixture
async def mock_llm_service():
    """Fixture for mock LLM service."""
    return MockLLMService()


@pytest_asyncio.fixture
async def performance_monitor():
    """Fixture for performance monitoring."""
    return PerformanceMonitor()


@pytest.fixture
def sample_course_data():
    """Fixture providing sample course data."""
    return TestConfig.SAMPLE_COURSE.copy()


@pytest.fixture
def sample_book_data():
    """Fixture providing sample book data."""
    return TestConfig.SAMPLE_BOOK.copy()


@pytest.fixture
def sample_chat_message():
    """Fixture providing sample chat message."""
    return TestConfig.SAMPLE_CHAT_MESSAGE.copy()


# Utility functions
def assert_valid_course(course_data: Dict):
    """Assert that course data is valid."""
    required_fields = ["id", "title", "description", "subject", "difficulty_level"]
    for field in required_fields:
        assert field in course_data, f"Missing required field: {field}"
    assert isinstance(course_data["id"], str)
    assert len(course_data["id"]) > 0
    assert isinstance(course_data["title"], str)
    assert len(course_data["title"]) > 0


def assert_valid_book(book_data: Dict):
    """Assert that book data is valid."""
    required_fields = ["id", "course_id", "title", "author"]
    for field in required_fields:
        assert field in book_data, f"Missing required field: {field}"
    assert isinstance(book_data["id"], str)
    assert isinstance(book_data["course_id"], str)
    assert isinstance(book_data["title"], str)


def assert_valid_chat_response(response_data: Dict):
    """Assert that chat response is valid."""
    required_fields = ["response", "sources", "context"]
    for field in required_fields:
        assert field in response_data, f"Missing required field: {field}"
    assert isinstance(response_data["response"], str)
    assert len(response_data["response"]) > 0
    assert isinstance(response_data["sources"], list)


async def assert_api_response_time(api_call, max_duration_ms: float = 2000):
    """Assert that an API call completes within the time limit."""
    import time
    start_time = time.time()
    result = await api_call()
    duration_ms = (time.time() - start_time) * 1000
    assert duration_ms <= max_duration_ms, \
        f"API call took {duration_ms}ms, expected < {max_duration_ms}ms"
    return result


class TestDataManager:
    """Manage test data files and cleanup."""

    def __init__(self, base_dir: str = "./test_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.created_files = []

    def create_test_pdf(self, filename: str = "test.pdf") -> Path:
        """Create a test PDF file."""
        filepath = self.base_dir / filename

        # Create minimal PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT/F1 12 Tf 72 720 Td(Test PDF Content) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000203 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
312
%%EOF"""

        with open(filepath, "wb") as f:
            f.write(pdf_content)

        self.created_files.append(filepath)
        return filepath

    def create_test_text_file(self, filename: str = "test.txt", content: str = "Test content") -> Path:
        """Create a test text file."""
        filepath = self.base_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        self.created_files.append(filepath)
        return filepath

    def cleanup(self):
        """Clean up all created test files."""
        for filepath in self.created_files:
            if filepath.exists():
                filepath.unlink()
        self.created_files.clear()

        # Remove base directory if empty
        try:
            if self.base_dir.exists():
                self.base_dir.rmdir()
        except OSError:
            pass  # Directory not empty