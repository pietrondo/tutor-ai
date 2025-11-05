#!/usr/bin/env python3
"""
Test suite for the Advanced Search Service
"""

import unittest
import tempfile
import shutil
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Import the service
from services.advanced_search_service import (
    AdvancedSearchService,
    SearchType,
    SortOrder,
    SearchFilter,
    SearchQuery,
    SearchResult
)

class TestAdvancedSearchService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.search_service = AdvancedSearchService(self.test_dir)

        # Create test data structure
        self.annotations_dir = self.test_dir / "annotations"
        self.ocr_results_dir = self.test_dir / "ocr_results"
        self.annotations_dir.mkdir(parents=True, exist_ok=True)
        self.ocr_results_dir.mkdir(parents=True, exist_ok=True)

        # Create test annotations
        self._create_test_annotations()

        # Create test OCR results
        self._create_test_ocr_results()

        # Rebuild indexes with test data
        self.search_service._build_indexes()

    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_test_annotations(self):
        """Create test annotation files"""
        # Create user directory structure
        user_dir = self.annotations_dir / "test_user"
        course_dir = user_dir / "test_course"
        book_dir = course_dir / "test_book"
        book_dir.mkdir(parents=True, exist_ok=True)

        # Create annotation file
        annotations = [
            {
                "id": "ann_1",
                "user_id": "test_user",
                "pdf_filename": "document1.pdf",
                "selected_text": "This is important physics content",
                "content": "Note about physics formula",
                "page_number": 1,
                "type": "highlight",
                "tags": ["physics", "important", "chapter1"],
                "is_public": True,
                "is_favorite": False,
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-01T10:00:00"
            },
            {
                "id": "ann_2",
                "user_id": "test_user",
                "pdf_filename": "document1.pdf",
                "selected_text": "Chemistry experiment results",
                "content": "Lab notes about chemical reactions",
                "page_number": 2,
                "type": "note",
                "tags": ["chemistry", "experiment"],
                "is_public": False,
                "is_favorite": True,
                "created_at": "2023-01-02T15:30:00",
                "updated_at": "2023-01-02T15:30:00"
            },
            {
                "id": "ann_3",
                "user_id": "test_user",
                "pdf_filename": "document2.pdf",
                "selected_text": "Mathematical derivation",
                "content": "Step-by-step math solution",
                "page_number": 1,
                "type": "underline",
                "tags": ["mathematics", "calculus"],
                "is_public": True,
                "is_favorite": True,
                "created_at": "2023-01-03T09:15:00",
                "updated_at": "2023-01-03T09:15:00"
            }
        ]

        with open(book_dir / "document1.pdf.json", 'w', encoding='utf-8') as f:
            json.dump(annotations, f, indent=2)

        # Create annotations for another user
        user2_dir = self.annotations_dir / "test_user2"
        course2_dir = user2_dir / "test_course2"
        book2_dir = course2_dir / "test_book2"
        book2_dir.mkdir(parents=True, exist_ok=True)

        annotations2 = [
            {
                "id": "ann_4",
                "user_id": "test_user2",
                "pdf_filename": "document3.pdf",
                "selected_text": "Biology research paper",
                "content": "Notes on cellular biology",
                "page_number": 3,
                "type": "highlight",
                "tags": ["biology", "research"],
                "is_public": True,
                "is_favorite": False,
                "created_at": "2023-01-04T14:20:00",
                "updated_at": "2023-01-04T14:20:00"
            }
        ]

        with open(book2_dir / "document3.pdf.json", 'w', encoding='utf-8') as f:
            json.dump(annotations2, f, indent=2)

    def _create_test_ocr_results(self):
        """Create test OCR result files"""
        ocr_content_1 = """OCR Result for: document4.pdf
Total Pages: 5
Processed Pages: 5
Average Confidence: 92.5%
Engines Used: tesseract
Language: ita

========================

--- Page 1 ---
This is scanned physics text about quantum mechanics.
The principles discussed include wave-particle duality
and uncertainty principle applications.

--- Page 2 ---
Mathematical formulations of quantum theory
including Schrödinger equation and its solutions.

--- Page 3 ---
Experimental evidence supporting quantum mechanics
including double-slit experiment results.

--- Page 4 ---
Applications in modern physics and technology
including quantum computing concepts.

--- Page 5 ---
Historical development of quantum theory
from early 20th century to present day.
"""

        with open(self.ocr_results_dir / "document4_ocr.txt", 'w', encoding='utf-8') as f:
            f.write(ocr_content_1)

        ocr_content_2 = """OCR Result for: document5.pdf
Total Pages: 3
Processed Pages: 3
Average Confidence: 88.2%
Engines Used: easyocr
Language: eng

========================

--- Page 1 ---
Computer science algorithms and data structures
including sorting and searching techniques.

--- Page 2 ---
Complexity analysis and Big O notation
fundamental concepts in algorithm design.

--- Page 3 ---
Practical applications of algorithms
in software development and problem solving.
"""

        with open(self.ocr_results_dir / "document5_ocr.txt", 'w', encoding='utf-8') as f:
            f.write(ocr_content_2)

    def test_search_service_initialization(self):
        """Test search service initialization"""
        service = AdvancedSearchService(self.test_dir)
        self.assertIsNotNone(service)
        self.assertEqual(str(service.data_dir), self.test_dir)

    def test_text_search_basic(self):
        """Test basic text search functionality"""
        import asyncio

        async def test_search():
            query = SearchQuery(query="physics", search_type=SearchType.TEXT)
            result = await self.search_service.search(query)

            self.assertEqual(result.query, "physics")
            self.assertGreater(len(result.results), 0)
            self.assertGreater(result.total_count, 0)
            self.assertGreaterEqual(result.search_time, 0)

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_text_search_with_no_results(self):
        """Test text search with no matching results"""
        import asyncio

        async def test_search():
            query = SearchQuery(query="nonexistent_term_xyz", search_type=SearchType.TEXT)
            result = await self.search_service.search(query)

            self.assertEqual(result.query, "nonexistent_term_xyz")
            self.assertEqual(len(result.results), 0)
            self.assertEqual(result.total_count, 0)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_text_search_with_multiple_terms(self):
        """Test text search with multiple terms"""
        import asyncio

        async def test_search():
            query = SearchQuery(query="physics quantum", search_type=SearchType.TEXT)
            result = await self.search_service.search(query)

            # Should find results containing both terms
            self.assertGreater(len(result.results), 0)
            # Check that scores are calculated
            for search_result in result.results:
                self.assertGreaterEqual(search_result.score, 0)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_search_with_course_filter(self):
        """Test search with course filter"""
        import asyncio

        async def test_search():
            filters = SearchFilter(course_ids=["test_course"])
            query = SearchQuery(
                query="physics",
                search_type=SearchType.TEXT,
                filters=filters
            )
            result = await self.search_service.search(query)

            # All results should be from test_course
            for search_result in result.results:
                self.assertEqual(search_result.course_id, "test_course")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_search_with_user_filter(self):
        """Test search with user filter"""
        import asyncio

        async def test_search():
            filters = SearchFilter(user_ids=["test_user"])
            query = SearchQuery(
                query="physics",
                search_type=SearchType.TEXT,
                filters=filters
            )
            result = await self.search_service.search(query)

            # All results should be from test_user
            for search_result in result.results:
                self.assertEqual(search_result.user_id, "test_user")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_search_with_tags_filter(self):
        """Test search with tags filter"""
        import asyncio

        async def test_search():
            filters = SearchFilter(tags=["physics"])
            query = SearchQuery(
                query="content",
                search_type=SearchType.TEXT,
                filters=filters
            )
            result = await self.search_service.search(query)

            # Results should have physics tag
            for search_result in result.results:
                if search_result.tags:
                    self.assertIn("physics", search_result.tags)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_search_with_annotation_type_filter(self):
        """Test search with annotation type filter"""
        import asyncio

        async def test_search():
            filters = SearchFilter(annotation_types=["highlight"])
            query = SearchQuery(
                query="text",
                search_type=SearchType.TEXT,
                filters=filters
            )
            result = await self.search_service.search(query)

            # Results should be highlight annotations
            for search_result in result.results:
                if search_result.metadata and 'annotation_type' in search_result.metadata:
                    self.assertEqual(search_result.metadata['annotation_type'], "highlight")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_search_sort_by_relevance(self):
        """Test search results sorted by relevance"""
        import asyncio

        async def test_search():
            query = SearchQuery(
                query="physics",
                search_type=SearchType.TEXT,
                sort_order=SortOrder.RELEVANCE
            )
            result = await self.search_service.search(query)

            if len(result.results) > 1:
                # Check that results are sorted by score (descending)
                for i in range(len(result.results) - 1):
                    self.assertGreaterEqual(
                        result.results[i].score,
                        result.results[i + 1].score
                    )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_search_sort_by_date(self):
        """Test search results sorted by date"""
        import asyncio

        async def test_search():
            query = SearchQuery(
                query="text",
                search_type=SearchType.TEXT,
                sort_order=SortOrder.DATE
            )
            result = await self.search_service.search(query)

            if len(result.results) > 1:
                # Check that results are sorted by date (descending)
                for i in range(len(result.results) - 1):
                    current_date = result.results[i].created_at or datetime.min
                    next_date = result.results[i + 1].created_at or datetime.min
                    self.assertGreaterEqual(current_date, next_date)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_search_with_pagination(self):
        """Test search pagination"""
        import asyncio

        async def test_search():
            # First page
            query1 = SearchQuery(
                query="text",
                search_type=SearchType.TEXT,
                limit=2,
                offset=0
            )
            result1 = await self.search_service.search(query1)

            # Second page
            query2 = SearchQuery(
                query="text",
                search_type=SearchType.TEXT,
                limit=2,
                offset=2
            )
            result2 = await self.search_service.search(query2)

            # Check pagination works
            self.assertLessEqual(len(result1.results), 2)
            self.assertLessEqual(len(result2.results), 2)
            self.assertEqual(result1.total_count, result2.total_count)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_search_suggestions(self):
        """Test search suggestions functionality"""
        suggestions = self.search_service.get_search_suggestions("phys", limit=5)
        self.assertIsInstance(suggestions, list)
        self.assertLessEqual(len(suggestions), 5)

        # Suggestions should start with the query
        for suggestion in suggestions:
            self.assertTrue(suggestion.lower().startswith("phys"))

    def test_search_facets_generation(self):
        """Test search facets generation"""
        import asyncio

        async def test_search():
            query = SearchQuery(query="physics", search_type=SearchType.TEXT)
            result = await self.search_service.search(query)

            # Should generate facets
            self.assertIsInstance(result.facets, dict)

            # Should have type facets
            if "types" in result.facets:
                self.assertIsInstance(result.facets["types"], dict)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_ocr_results_search(self):
        """Test searching in OCR results"""
        import asyncio

        async def test_search():
            query = SearchQuery(query="quantum", search_type=SearchType.TEXT)
            result = await self.search_service.search(query)

            # Should find OCR results
            ocr_results = [r for r in result.results if r.type == "ocr_result"]
            self.assertGreater(len(ocr_results), 0)

            # Check OCR result structure
            for ocr_result in ocr_results:
                self.assertEqual(ocr_result.type, "ocr_result")
                self.assertIsNotNone(ocr_result.content)
                self.assertIsNotNone(ocr_result.metadata)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_search_highlights_generation(self):
        """Test search highlights generation"""
        import asyncio

        async def test_search():
            query = SearchQuery(
                query="physics",
                search_type=SearchType.TEXT,
                include_highlights=True
            )
            result = await self.search_service.search(query)

            # Check that highlights are generated
            for search_result in result.results:
                if search_result.metadata and 'highlights' in search_result.metadata:
                    self.assertIsInstance(search_result.metadata['highlights'], list)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_search_with_min_text_length_filter(self):
        """Test search with minimum text length filter"""
        import asyncio

        async def test_search():
            filters = SearchFilter(min_text_length=20)
            query = SearchQuery(
                query="physics",
                search_type=SearchType.TEXT,
                filters=filters
            )
            result = await self.search_service.search(query)

            # All results should have content length >= 20
            for search_result in result.results:
                self.assertGreaterEqual(len(search_result.content), 20)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_search())
        finally:
            loop.close()

    def test_rebuild_indexes(self):
        """Test rebuilding search indexes"""
        # Clear indexes
        self.search_service.annotations_index.clear()
        self.search_service.ocr_results_index.clear()

        # Rebuild
        self.search_service.rebuild_indexes()

        # Check indexes are rebuilt
        self.assertGreater(len(self.search_service.annotations_index), 0)
        self.assertGreater(len(self.search_service.ocr_results_index), 0)

    def test_search_query_validation(self):
        """Test search query validation"""
        # Test with empty query
        query = SearchQuery(query="", search_type=SearchType.TEXT)
        self.assertEqual(query.query, "")

        # Test with negative limit
        query = SearchQuery(query="test", search_type=SearchType.TEXT, limit=-1)
        self.assertEqual(query.limit, -1)

        # Test with negative offset
        query = SearchQuery(query="test", search_type=SearchType.TEXT, offset=-1)
        self.assertEqual(query.offset, -1)

    def test_search_filter_creation(self):
        """Test search filter creation"""
        # Test with all fields
        filters = SearchFilter(
            course_ids=["course1", "course2"],
            book_ids=["book1"],
            user_ids=["user1"],
            tags=["tag1", "tag2"],
            annotation_types=["highlight", "note"],
            is_public=True,
            is_favorite=False,
            min_text_length=50,
            language="ita"
        )

        self.assertEqual(filters.course_ids, ["course1", "course2"])
        self.assertEqual(filters.book_ids, ["book1"])
        self.assertEqual(filters.user_ids, ["user1"])
        self.assertEqual(filters.tags, ["tag1", "tag2"])
        self.assertEqual(filters.annotation_types, ["highlight", "note"])
        self.assertTrue(filters.is_public)
        self.assertFalse(filters.is_favorite)
        self.assertEqual(filters.min_text_length, 50)
        self.assertEqual(filters.language, "ita")

    def test_search_result_creation(self):
        """Test search result creation"""
        result = SearchResult(
            id="test_id",
            type="annotation",
            content="Test content",
            title="Test Title",
            source="test_source",
            course_id="course1",
            book_id="book1",
            page_number=1,
            user_id="user1",
            score=85.5,
            tags=["tag1"],
            created_at=datetime.now(),
            metadata={"test": "data"}
        )

        self.assertEqual(result.id, "test_id")
        self.assertEqual(result.type, "annotation")
        self.assertEqual(result.content, "Test content")
        self.assertEqual(result.title, "Test Title")
        self.assertEqual(result.source, "test_source")
        self.assertEqual(result.course_id, "course1")
        self.assertEqual(result.book_id, "book1")
        self.assertEqual(result.page_number, 1)
        self.assertEqual(result.user_id, "user1")
        self.assertEqual(result.score, 85.5)
        self.assertEqual(result.tags, ["tag1"])
        self.assertIsNotNone(result.created_at)
        self.assertEqual(result.metadata, {"test": "data"})


class TestAdvancedSearchServiceIntegration(unittest.TestCase):
    """Integration tests for advanced search service"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.search_service = AdvancedSearchService(self.test_dir)

        # Create realistic test data
        self._create_realistic_test_data()

        # Rebuild indexes
        self.search_service._build_indexes()

    def tearDown(self):
        """Clean up after integration tests."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_realistic_test_data(self):
        """Create realistic test data for integration tests"""
        # Create directory structure
        annotations_dir = self.test_dir / "annotations"
        ocr_results_dir = self.test_dir / "ocr_results"
        annotations_dir.mkdir(parents=True, exist_ok=True)
        ocr_results_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple users, courses, and books
        users = ["alice", "bob", "charlie"]
        courses = ["math101", "physics202", "chemistry303"]
        books = ["textbook1", "textbook2", "notes"]

        for user in users:
            user_dir = annotations_dir / user
            for course in courses:
                course_dir = user_dir / course
                for book in books:
                    book_dir = course_dir / book
                    book_dir.mkdir(parents=True, exist_ok=True)

                    # Create annotations with varied content
                    annotations = []
                    for i in range(3):
                        annotation = {
                            "id": f"{user}_{course}_{book}_ann_{i}",
                            "user_id": user,
                            "pdf_filename": f"{book}.pdf",
                            "selected_text": f"Sample text {i} for {course}",
                            "content": f"Detailed note {i} about {course} concepts",
                            "page_number": i + 1,
                            "type": ["highlight", "note", "underline"][i % 3],
                            "tags": [course, book, f"section{i}"],
                            "is_public": i % 2 == 0,
                            "is_favorite": i % 3 == 0,
                            "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                            "updated_at": (datetime.now() - timedelta(days=i)).isoformat()
                        }
                        annotations.append(annotation)

                    with open(book_dir / f"{book}.pdf.json", 'w', encoding='utf-8') as f:
                        json.dump(annotations, f, indent=2)

        # Create OCR results
        ocr_files = [
            ("lecture_notes.pdf", "Comprehensive lecture notes covering advanced topics"),
            ("research_paper.pdf", "Research findings with detailed analysis"),
            ("textbook_excerpts.pdf", "Key excerpts from academic textbooks")
        ]

        for filename, content_desc in ocr_files:
            ocr_content = f"""OCR Result for: {filename}
Total Pages: 10
Processed Pages: 10
Average Confidence: 91.5%
Engines Used: tesseract
Language: eng

========================

{content_desc}
Sample content for search testing.
This includes various topics and concepts.
"""

            with open(ocr_results_dir / f"{filename.replace('.pdf', '')}_ocr.txt", 'w', encoding='utf-8') as f:
                f.write(ocr_content)

    def test_comprehensive_search_functionality(self):
        """Test comprehensive search functionality"""
        import asyncio

        async def test_comprehensive_search():
            # Test different search types
            queries = [
                SearchQuery(query="mathematics", search_type=SearchType.TEXT),
                SearchQuery(query="physics", search_type=SearchType.TEXT),
                SearchQuery(query="chemistry", search_type=SearchType.TEXT)
            ]

            all_results = []
            for query in queries:
                result = await self.search_service.search(query)
                all_results.append(result)

            # Verify all searches returned results
            for result in all_results:
                self.assertGreater(result.total_count, 0)

            # Test filtering
            filters = SearchFilter(user_ids=["alice"])
            filtered_query = SearchQuery(
                query="text",
                search_type=Test.TEXT,
                filters=filters
            )
            filtered_result = await self.search_service(filtered_query)

            # All filtered results should be from alice
            for search_result in filtered_result.results:
                if search_result.user_id:
                    self.assertEqual(search_result.user_id, "alice")

            # Test sorting
            sorted_query = SearchQuery(
                query="text",
                search_type=SearchType.TEXT,
                sort_order=SortOrder.DATE
            )
            sorted_result = await self.search_service(sorted_query)

            # Verify sorting (if multiple results)
            if len(sorted_result.results) > 1:
                for i in range(len(sorted_result.results) - 1):
                    current = sorted_result.results[i].created_at or datetime.min
                    next_item = sorted_result.results[i + 1].created_at or datetime.min
                    self.assertGreaterEqual(current, next_item)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_comprehensive_search())
        finally:
            loop.close()

    def test_performance_with_large_dataset(self):
        """Test search performance with larger dataset"""
        import asyncio

        async def test_performance():
            # Measure search time
            start_time = datetime.now()

            query = SearchQuery(query="content", search_type=SearchType.TEXT)
            result = await self.search_service.search(query)

            end_time = datetime.now()
            search_time = (end_time - start_time).total_seconds()

            # Performance assertion (should complete within reasonable time)
            self.assertLess(search_time, 5.0)  # 5 seconds max
            self.assertGreater(result.search_time, 0)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_performance())
        finally:
            loop.close()


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedSearchService))
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedSearchServiceIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

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