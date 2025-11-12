"""
End-to-End Complete Learning Journey Tests

This test suite validates complete user workflows from start to finish:
- Course creation to completed learning session
- PDF upload through AI-assisted study
- Complete cognitive learning cycle
- Cross-platform compatibility
- Performance under realistic user scenarios
"""

import asyncio
import pytest
import uuid
import time
from pathlib import Path
from typing import Dict, List, Any
from httpx import AsyncClient
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import tempfile
import os

from main import app
from tests.utils.test_helpers import (
    APITestClient, TestConfig, TestDataManager, PerformanceMonitor
)


class TestCompleteLearningJourney:
    """Test complete end-to-end learning workflows."""

    @pytest_asyncio.asyncio
    async def test_complete_course_creation_to_study_session(self):
        """
        Test the complete workflow:
        1. Create course
        2. Upload PDF materials
        3. Navigate to study environment
        4. Interact with AI chat
        5. Complete learning session
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            monitor = PerformanceMonitor()

            try:
                # Step 1: Navigate to application and create course
                with monitor.start_timer("navigate_to_home"):
                    await page.goto("http://localhost:3000")
                    await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)

                # Click create course button
                with monitor.start_timer("create_course_start"):
                    await page.click('[data-testid="create-course-button"]')
                    await page.wait_for_selector('input[name="title"]', timeout=5000)

                # Fill course creation form
                course_data = {
                    "title": "E2E Test Course: Machine Learning Fundamentals",
                    "description": "A comprehensive end-to-end test course covering ML fundamentals",
                    "subject": "Computer Science",
                    "difficulty_level": "intermediate"
                }

                with monitor.start_timer("fill_course_form"):
                    await page.fill('input[name="title"]', course_data["title"])
                    await page.fill('textarea[name="description"]', course_data["description"])
                    await page.select_option('select[name="subject"]', course_data["subject"])
                    await page.select_option('select[name="difficulty_level"]', course_data["difficulty_level"])

                # Submit course creation
                with monitor.start_timer("submit_course"):
                    await page.click('button[type="submit"]')
                    await page.wait_for_selector('[data-testid="course-detail"]', timeout=10000)

                # Verify course was created
                course_title = await page.text_content('h1')
                assert course_data["title"] in course_title

                # Step 2: Upload PDF materials
                with monitor.start_timer("upload_pdf"):
                    await page.click('[data-testid="upload-pdf-button"]')
                    await page.wait_for_selector('input[type="file"]', timeout=5000)

                    # Create test PDF file
                    test_pdf_path = Path(__file__).parent / "test_material.pdf"
                    self._create_test_pdf_file(test_pdf_path)

                    # Upload file
                    await page.set_input_files('input[type="file"]', str(test_pdf_path))
                    await page.click('[data-testid="confirm-upload"]')
                    await page.wait_for_selector('[data-testid="upload-success"]', timeout=15000)

                # Step 3: Navigate to study environment
                with monitor.start_timer("navigate_to_study"):
                    await page.click('[data-testid="study-button"]')
                    await page.wait_for_selector('[data-testid="study-environment"]', timeout=10000)

                # Verify PDF is loaded
                await page.wait_for_selector('[data-testid="pdf-viewer"]', timeout=10000)

                # Step 4: Interact with AI chat
                with monitor.start_timer("ai_chat_interaction"):
                    await page.click('[data-testid="chat-input"]')
                    await page.fill('[data-testid="chat-input"]', "What are the key concepts in this material?")
                    await page.click('[data-testid="send-chat-button"]')
                    await page.wait_for_selector('[data-testid="chat-response"]', timeout=15000)

                    # Verify AI response
                    chat_response = await page.text_content('[data-testid="chat-response"]')
                    assert len(chat_response) > 50  # Should have substantial response

                # Step 5: Complete learning activities
                with monitor.start_timer("learning_activities"):
                    # Navigate through PDF pages
                    await page.click('[data-testid="next-page"]')
                    await page.wait_for_timeout(1000)

                    # Create annotation
                    await page.click('[data-testid="highlight-tool"]')
                    await page.dblclick('[data-testid="pdf-content"]')
                    await page.fill('[data-testid="annotation-input"]', "Important concept for understanding")
                    await page.click('[data-testid="save-annotation"]')

                    # Generate mind map
                    await page.click('[data-testid="mindmap-button"]')
                    await page.wait_for_selector('[data-testid="mindmap-container"]', timeout=10000)

                # Step 6: Complete session and view progress
                with monitor.start_timer("complete_session"):
                    await page.click('[data-testid="complete-session"]')
                    await page.wait_for_selector('[data-testid="session-summary"]', timeout=10000)

                    # Verify progress tracking
                    progress_text = await page.text_content('[data-testid="progress-summary"]')
                    assert "time" in progress_text.lower() or "progress" in progress_text.lower()

                # Verify overall performance
                monitor.assert_performance(max_duration_ms=30000)  # 30 seconds total

            finally:
                await context.close()
                await browser.close()
                # Cleanup test file
                test_pdf_path = Path(__file__).parent / "test_material.pdf"
                if test_pdf_path.exists():
                    test_pdf_path.unlink()

    def _create_test_pdf_file(self, path: Path):
        """Create a test PDF file for upload testing."""
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 150>>stream
BT/F1 16 Tf 72 750 Td(End-to-End Test Course Material) Tj
/F1 12 Tf 72 720 Td(Chapter 1: Introduction to Machine Learning) Tj
/F1 10 Tf 72 690 Td(Machine learning is a subset of artificial intelligence that) Tj
72 670 Td(enables systems to learn and improve from experience without) Tj
72 650 Td(being explicitly programmed. This chapter covers the fundamental) Tj
72 630 Td(concepts and algorithms that form the foundation of ML.) Tj
/F1 12 Tf 72 600 Td(Chapter 2: Supervised Learning) Tj
/F1 10 Tf 72 570 Td(Supervised learning algorithms learn from labeled training data.) Tj
72 550 Td(Common examples include classification and regression problems.) Tj
/F1 12 Tf 72 520 Td(Chapter 3: Neural Networks) Tj
/F1 10 Tf 72 490 Td(Neural networks are computing systems inspired by biological neural) Tj
72 470 Td(networks. They form the basis for deep learning and many modern AI) Tj
72 450 Td(applications.) Tj
ET
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
566
%%EOF"""
        with open(path, 'wb') as f:
            f.write(pdf_content)

    @pytest_asyncio.asyncio
    async def test_multi_user_concurrent_learning(self):
        """Test multiple users learning simultaneously."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # Create multiple user contexts
            contexts = []
            pages = []

            try:
                # Create 3 concurrent users
                for i in range(3):
                    context = await browser.new_context()
                    page = await context.new_page()
                    contexts.append(context)
                    pages.append(page)

                # Simulate concurrent activities
                async def user_activities(user_id: int, page: Page):
                    monitor = PerformanceMonitor()

                    with monitor.start_timer(f"user_{user_id}_session"):
                        await page.goto("http://localhost:3000")
                        await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)

                        # User interacts with different features
                        if user_id == 0:
                            # User 1: Creates course and uploads materials
                            await page.click('[data-testid="create-course-button"]')
                            await page.fill('input[name="title"]', f'Concurrent User {user_id} Course')
                            await page.click('button[type="submit"]')
                            await page.wait_for_timeout(2000)

                        elif user_id == 1:
                            # User 2: Studies existing materials
                            await page.click('[data-testid="course-card"]')
                            await page.wait_for_selector('[data-testid="study-button"]', timeout=5000)
                            await page.click('[data-testid="study-button"]')
                            await page.wait_for_timeout(3000)

                        else:
                            # User 3: Uses chat functionality
                            await page.click('[data-testid="course-card"]')
                            await page.wait_for_selector('[data-testid="chat-input"]', timeout=5000)
                            await page.fill('[data-testid="chat-input"]', f"Question from user {user_id}")
                            await page.click('[data-testid="send-chat-button"]')
                            await page.wait_for_timeout(3000)

                    return monitor.get_metrics()

                # Run all users concurrently
                tasks = [user_activities(i, pages[i]) for i in range(3)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Verify all users completed their activities successfully
                successful_users = sum(1 for result in results if not isinstance(result, Exception))
                assert successful_users >= 2, f"Only {successful_users}/3 users completed successfully"

            finally:
                for context in contexts:
                    await context.close()
                await browser.close()

    @pytest_asyncio.asyncio
    async def test_cross_device_compatibility(self):
        """Test application works across different device sizes."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # Test different viewport sizes
            viewports = [
                {"width": 1920, "height": 1080, "name": "Desktop"},
                {"width": 768, "height": 1024, "name": "Tablet"},
                {"width": 375, "height": 667, "name": "Mobile"}
            ]

            for viewport in viewports:
                context = await browser.new_context(viewport=viewport)
                page = await context.new_page()

                try:
                    await page.goto("http://localhost:3000")
                    await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)

                    # Test navigation
                    await page.click('[data-testid="create-course-button"]')
                    await page.wait_for_selector('input[name="title"]', timeout=5000)

                    # Test responsive elements
                    if viewport["width"] <= 768:
                        # Mobile/tablet should have hamburger menu
                        mobile_nav = await page.query_selector('[data-testid="mobile-nav"]')
                        assert mobile_nav is not None, f"Mobile navigation missing on {viewport['name']}"

                    # Test course creation works on all devices
                    await page.fill('input[name="title"]', f'{viewport["name"]} Test Course')
                    await page.click('button[type="submit"]')
                    await page.wait_for_timeout(2000)

                    # Verify successful creation
                    course_title = await page.text_content('h1')
                    assert viewport["name"] in course_title

                finally:
                    await context.close()

            await browser.close()

    @pytest_asyncio.asyncio
    async def test_cognitive_learning_complete_cycle(self):
        """Test complete cognitive learning cycle with all features."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto("http://localhost:3000")
                await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)

                # Create course with cognitive learning focus
                await page.click('[data-testid="create-course-button"]')
                await page.fill('input[name="title"]', "Cognitive Learning Test Course")
                await page.fill('textarea[name="description"]', "Testing complete cognitive learning cycle")
                await page.select_option('select[name="subject"]', "Education")
                await page.click('button[type="submit"]')
                await page.wait_for_selector('[data-testid="course-detail"]', timeout=10000)

                # Upload comprehensive learning material
                await page.click('[data-testid="upload-pdf-button"]')
                test_pdf_path = Path(__file__).parent / "cognitive_test.pdf"
                self._create_cognitive_learning_pdf(test_pdf_path)

                await page.set_input_files('input[type="file"]', str(test_pdf_path))
                await page.click('[data-testid="confirm-upload"]')
                await page.wait_for_selector('[data-testid="upload-success"]', timeout=15000)

                # Step 1: Initial assessment and spaced repetition
                await page.click('[data-testid="study-button"]')
                await page.wait_for_selector('[data-testid="study-environment"]', timeout=10000)

                # Create learning cards for spaced repetition
                await page.click('[data-testid="create-flashcard"]')
                await page.fill('[data-testid="flashcard-front"]', "What is cognitive load theory?")
                await page.fill('[data-testid="flashcard-back"]', "Cognitive load theory refers to the amount of working memory resources used during learning tasks.")
                await page.click('[data-testid="save-flashcard"]')

                # Step 2: Active recall with Bloom's taxonomy questions
                await page.click('[data-testid="practice-quiz"]')
                await page.wait_for_selector('[data-testid="quiz-question"]', timeout=10000)

                # Answer questions at different cognitive levels
                questions = await page.query_selector_all('[data-testid="quiz-question"]')
                for i, question in enumerate(questions[:3]):  # Answer first 3 questions
                    options = await question.query_selector_all('[data-testid="quiz-option"]')
                    if options:
                        await options[i % len(options)].click()

                await page.click('[data-testid="submit-quiz"]')
                await page.wait_for_selector('[data-testid="quiz-results"]', timeout=10000)

                # Step 3: Dual coding with visual-verbal integration
                await page.click('[data-testid="mindmap-button"]')
                await page.wait_for_selector('[data-testid="mindmap-container"]', timeout=10000)

                # Add visual elements to mind map
                await page.click('[data-testid="add-concept"]')
                await page.fill('[data-testid="concept-text"]', "Cognitive Load Types")
                await page.click('[data-testid="add-visual-element"]')
                await page.select_option('[data-testid="visual-type"]', "diagram")
                await page.click('[data-testid="save-visual"]')

                # Step 4: Metacognitive reflection
                await page.click('[data-testid="reflection-prompt"]')
                await page.wait_for_selector('[data-testid="reflection-form"]', timeout=10000)

                await page.select_option('[data-testid="confidence-rating"]', "4")
                await page.fill('[data-testid="learning-strategy"]', "I used visual diagrams and practice questions to reinforce understanding")
                await page.fill('[data-testid="next-steps"]', "Review the three types of cognitive load with examples")
                await page.click('[data-testid="submit-reflection"]')

                # Step 5: Elaboration and knowledge integration
                await page.click('[data-testid="elaboration-exercise"]')
                await page.wait_for_selector('[data-testid="elaboration-prompt"]', timeout=10000)

                await page.fill('[data-testid="elaboration-response"]', "Cognitive load theory relates to my previous understanding of working memory limitations. It helps explain why some learning materials are more effective than others. For example, when studying machine learning, I should break down complex algorithms into smaller, manageable chunks to reduce intrinsic cognitive load.")
                await page.click('[data-testid="submit-elaboration"]')

                # Step 6: Review progress and analytics
                await page.click('[data-testid="learning-analytics"]')
                await page.wait_for_selector('[data-testid="analytics-dashboard"]', timeout=10000)

                # Verify all cognitive learning components are tracked
                analytics_sections = await page.query_selector_all('[data-testid^="analytics-"]')
                cognitive_sections = [
                    "analytics-spaced-repetition",
                    "analytics-active-recall",
                    "analytics-dual-coding",
                    "analytics-metacognition",
                    "analytics-elaboration"
                ]

                tracked_components = []
                for section in analytics_sections:
                    section_id = await section.get_attribute('data-testid')
                    tracked_components.append(section_id)

                # At least 3 cognitive components should be tracked
                tracked_cognitive = [comp for comp in tracked_components
                                   if any(cog_comp in comp for cog_comp in cognitive_sections)]
                assert len(tracked_cognitive) >= 3, f"Only {len(tracked_cognitive)} cognitive components tracked"

                # Verify learning session completion
                await page.click('[data-testid="complete-learning-session"]')
                await page.wait_for_selector('[data-testid="session-completion-summary"]', timeout=10000)

                # Verify comprehensive summary
                summary_text = await page.text_content('[data-testid="session-completion-summary"]')
                assert any(term in summary_text.lower() for term in
                          ["progress", "completion", "learning", "cognitive"])

            finally:
                await context.close()
                await browser.close()
                # Cleanup
                test_pdf_path = Path(__file__).parent / "cognitive_test.pdf"
                if test_pdf_path.exists():
                    test_pdf_path.unlink()

    def _create_cognitive_learning_pdf(self, path: Path):
        """Create a comprehensive PDF for cognitive learning testing."""
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 800>>stream
BT/F1 16 Tf 72 750 Td(Cognitive Load Theory and Learning) Tj
/F1 12 Tf 72 720 Td(Chapter 1: Understanding Cognitive Load) Tj
/F1 10 Tf 72 690 Td(Cognitive load theory refers to the amount of working memory resources) Tj
72 670 Td(required during learning tasks. Understanding cognitive load is essential) Tj
72 650 Td(for designing effective learning materials and experiences.) Tj
/F1 12 Tf 72 620 Td(Chapter 2: Types of Cognitive Load) Tj
/F1 10 Tf 72 590 Td(1. Intrinsic Cognitive Load: The inherent difficulty of the subject) Tj
72 570 Td(material. Some topics are naturally more complex than others.) Tj
72 550 Td(2. Extraneous Cognitive Load: Load caused by the way information is) Tj
72 530 Td(presented. Poor design can increase unnecessary cognitive burden.) Tj
72 510 Td(3. Germane Cognitive Load: Load dedicated to processing information) Tj
72 490 Td(and constructing schemas. This is the "good" cognitive load that) Tj
72 470 Td(leads to deeper learning.) Tj
/F1 12 Tf 72 440 Td(Chapter 3: Applications in Learning Design) Tj
/F1 10 Tf 72 410 Td(Effective learning design should:) Tj
72 390 Td- Minimize extraneous load through clear presentation) Tj
72 370 Td- Manage intrinsic load by breaking complex topics into chunks) Tj
72 350 Td- Optimize germane load to encourage schema construction) Tj
72 330 Td- Use worked examples to reduce problem-solving load) Tj
72 310 Td- Provide scaffolding that can be gradually removed) Tj
/F1 12 Tf 72 280 Td(Chapter 4: Measurement and Assessment) Tj
/F1 10 Tf 72 250 Td(Cognitive load can be measured through:) Tj
72 230 Td- Self-report scales (NASA-TLX, mental effort ratings)) Tj
72 210 Td- Performance metrics (accuracy, time on task)) Tj
72 190 Td- Physiological measures (pupil dilation, heart rate variability)) Tj
72 170 Td- Behavioral indicators (error rates, help-seeking behavior)) Tj
ET
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
1216
%%EOF"""
        with open(path, 'wb') as f:
            f.write(pdf_content)

    @pytest_asyncio.asyncio
    async def test_error_recovery_and_resilience(self):
        """Test application resilience and error recovery."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto("http://localhost:3000")
                await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)

                # Test network error handling
                await page.route('**/api/courses', lambda route: route.abort())

                # Attempt to create course (should fail gracefully)
                await page.click('[data-testid="create-course-button"]')
                await page.fill('input[name="title"]', "Network Error Test Course")
                await page.click('button[type="submit"]')

                # Should show error message, not crash
                await page.wait_for_selector('[data-testid="error-message"]', timeout=5000)
                error_message = await page.text_content('[data-testid="error-message"]')
                assert "error" in error_message.lower() or "failed" in error_message.lower()

                # Test retry mechanism
                await page.unroute('**/api/courses')
                await page.click('[data-testid="retry-button"]')

                # Should either succeed or show appropriate message
                await page.wait_for_timeout(2000)

                # Test file upload error handling
                await page.goto("http://localhost:3000")  # Reset to home
                await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)
                await page.click('[data-testid="course-card"]')
                await page.wait_for_selector('[data-testid="upload-pdf-button"]', timeout=5000)

                # Simulate file upload error
                await page.route('**/api/upload', lambda route: route.fulfill(status=500))

                await page.click('[data-testid="upload-pdf-button"]')
                test_file_path = Path(__file__).parent / "error_test.txt"
                with open(test_file_path, 'w') as f:
                    f.write("test content")

                await page.set_input_files('input[type="file"]', str(test_file_path))
                await page.click('[data-testid="confirm-upload"]')

                # Should handle upload error gracefully
                await page.wait_for_timeout(2000)

                # Verify application is still functional
                await page.click('[data-testid="study-button"]')
                await page.wait_for_timeout(2000)  # Should not crash

            finally:
                await context.close()
                await browser.close()
                # Cleanup
                test_file_path = Path(__file__).parent / "error_test.txt"
                if test_file_path.exists():
                    test_file_path.unlink()

    @pytest_asyncio.asyncio
    async def test_performance_under_realistic_load(self):
        """Test application performance under realistic user load."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # Simulate realistic user session patterns
            session_patterns = [
                {
                    "name": "Quick Study Session",
                    "actions": ["navigate", "study", "chat", "exit"],
                    "duration": 300  # 5 minutes
                },
                {
                    "name": "Deep Learning Session",
                    "actions": ["navigate", "upload", "study", "mindmap", "quiz", "reflect", "exit"],
                    "duration": 1800  # 30 minutes
                },
                {
                    "name": "Review Session",
                    "actions": ["navigate", "study", "flashcards", "progress", "exit"],
                    "duration": 600  # 10 minutes
                }
            ]

            try:
                for pattern in session_patterns:
                    context = await browser.new_context()
                    page = await context.new_page()
                    monitor = PerformanceMonitor()

                    try:
                        session_start = time.time()

                        with monitor.start_timer(f"session_{pattern['name']}"):
                            for action in pattern["actions"]:
                                action_start = time.time()

                                if action == "navigate":
                                    await page.goto("http://localhost:3000")
                                    await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)

                                elif action == "upload":
                                    await page.click('[data-testid="course-card"]')
                                    await page.wait_for_selector('[data-testid="upload-pdf-button"]', timeout=5000)
                                    await page.click('[data-testid="upload-pdf-button"]')
                                    await page.wait_for_timeout(1000)

                                elif action == "study":
                                    if page.url == "http://localhost:3000/":
                                        await page.click('[data-testid="course-card"]')
                                    await page.wait_for_selector('[data-testid="study-button"]', timeout=5000)
                                    await page.click('[data-testid="study-button"]')
                                    await page.wait_for_selector('[data-testid="pdf-viewer"]', timeout=10000)
                                    await page.wait_for_timeout(2000)  # Simulate reading time

                                elif action == "chat":
                                    if "study" not in page.url:
                                        await page.click('[data-testid="course-card"]')
                                        await page.wait_for_selector('[data-testid="chat-input"]', timeout=5000)
                                    await page.fill('[data-testid="chat-input"]', "Can you explain the main concepts?")
                                    await page.click('[data-testid="send-chat-button"]')
                                    await page.wait_for_selector('[data-testid="chat-response"]', timeout=15000)

                                elif action == "mindmap":
                                    await page.click('[data-testid="mindmap-button"]')
                                    await page.wait_for_selector('[data-testid="mindmap-container"]', timeout=10000)
                                    await page.wait_for_timeout(1000)

                                elif action == "quiz":
                                    await page.click('[data-testid="practice-quiz"]')
                                    await page.wait_for_selector('[data-testid="quiz-question"]', timeout=10000)
                                    await page.wait_for_timeout(2000)

                                elif action == "reflect":
                                    await page.click('[data-testid="reflection-prompt"]')
                                    await page.wait_for_selector('[data-testid="reflection-form"]', timeout=5000)
                                    await page.wait_for_timeout(1000)

                                elif action == "flashcards":
                                    await page.click('[data-testid="flashcard-practice"]')
                                    await page.wait_for_selector('[data-testid="flashcard"]', timeout=5000)
                                    await page.wait_for_timeout(2000)

                                elif action == "progress":
                                    await page.click('[data-testid="progress-view"]')
                                    await page.wait_for_selector('[data-testid="progress-chart"]', timeout=5000)
                                    await page.wait_for_timeout(1000)

                                # Verify action completed within reasonable time
                                action_duration = time.time() - action_start
                                assert action_duration < 30, f"Action {action} took too long: {action_duration}s"

                        session_duration = time.time() - session_start

                        # Verify session performance
                        monitor.assert_performance(max_duration_ms=60000)  # 60 seconds max
                        assert session_duration < pattern["duration"], f"Session exceeded expected duration"

                    finally:
                        await context.close()

            finally:
                await browser.close()

    @pytest_asyncio.asyncio
    async def test_accessibility_compliance_e2e(self):
        """Test end-to-end accessibility compliance."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Test keyboard navigation
                await page.goto("http://localhost:3000")
                await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)

                # Navigate using keyboard only
                await page.keyboard.press('Tab')
                focused_element = await page.evaluate('document.activeElement.tagName')
                assert focused_element.lower() in ['button', 'a', 'input'], 'Keyboard navigation not working'

                # Test screen reader compatibility
                await page.click('[data-testid="create-course-button"]')
                await page.wait_for_selector('input[name="title"]', timeout=5000)

                # Check for ARIA labels
                title_input = await page.query_selector('input[name="title"]')
                aria_label = await title_input.get_attribute('aria-label')
                assert aria_label or await title_input.get_attribute('placeholder'), 'Missing accessibility labels'

                # Test color contrast (simulated)
                high_contrast_elements = await page.query_selector_all('[data-testid="high-contrast"]')
                # Should have sufficient contrast elements for accessibility

                # Test semantic HTML structure
                main_element = await page.query_selector('main')
                assert main_element is not None, 'Missing semantic main element'

                nav_element = await page.query_selector('nav')
                assert nav_element is not None, 'Missing semantic nav element'

                # Test form accessibility
                form_elements = await page.query_selector_all('input, select, textarea')
                for element in form_elements:
                    has_label = await element.evaluate('el => {
                        const id = el.getAttribute("aria-labelledby") || el.id;
                        return id && document.querySelector(`label[for="${id}"], [id="${id}"]`);
                    }')
                    assert has_label, f'Form element missing label: {await element.get_attribute("name")}'

            finally:
                await context.close()
                await browser.close()


class TestCrossBrowserCompatibility:
    """Test cross-browser compatibility."""

    @pytest_asyncio.asyncio
    async def test_chrome_compatibility(self):
        """Test Chrome browser compatibility."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto("http://localhost:3000")
                await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)

                # Test basic functionality
                await page.click('[data-testid="create-course-button"]')
                await page.fill('input[name="title"]', "Chrome Test Course")
                await page.click('button[type="submit"]')
                await page.wait_for_timeout(2000)

                # Verify success
                course_title = await page.text_content('h1')
                assert "Chrome Test Course" in course_title

            finally:
                await context.close()
                await browser.close()

    @pytest_asyncio.asyncio
    async def test_firefox_compatibility(self):
        """Test Firefox browser compatibility."""
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto("http://localhost:3000")
                await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)

                # Test PDF viewer compatibility
                await page.click('[data-testid="course-card"]')
                await page.wait_for_selector('[data-testid="study-button"]', timeout=5000)
                await page.click('[data-testid="study-button"]')
                await page.wait_for_selector('[data-testid="pdf-viewer"]', timeout=10000)

                # Verify PDF loads
                pdf_viewer = await page.query_selector('[data-testid="pdf-viewer"]')
                assert pdf_viewer is not None, "PDF viewer not working in Firefox"

            finally:
                await context.close()
                await browser.close()

    @pytest_asyncio.asyncio
    async def test_safari_compatibility(self):
        """Test Safari browser compatibility (webkit)."""
        async with async_playwright() as p:
            browser = await p.webkit.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto("http://localhost:3000")
                await page.wait_for_selector('[data-testid="course-list"]', timeout=10000)

                # Test mobile Safari features
                await page.set_viewport_size({"width": 375, "height": 667})

                # Test touch interactions
                await page.tap('[data-testid="course-card"]')
                await page.wait_for_timeout(2000)

                # Verify mobile layout works
                mobile_nav = await page.query_selector('[data-testid="mobile-nav"]')
                assert mobile_nav is not None, "Mobile navigation not working in Safari"

            finally:
                await context.close()
                await browser.close()