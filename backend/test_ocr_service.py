#!/usr/bin/env python3
"""
Test suite for the OCR Service
"""

import unittest
import tempfile
import os
import shutil
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
from services.ocr_service import OCRService

class TestOCRService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.ocr_service = OCRService()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_test_image(self, text="Test Text", size=(800, 600)):
        """Create a test image with text."""
        img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(img)

        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None

        # Draw text centered
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(text) * 10
            text_height = 20

        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2

        draw.text((x, y), text, fill='black', font=font)

        return img

    def create_test_pdf_with_images(self, texts=["Page 1 Text", "Page 2 Text"]):
        """Create a test PDF with images containing text."""
        pdf_path = os.path.join(self.test_dir, "test.pdf")
        doc = fitz.open()

        for i, text in enumerate(texts):
            # Create image with text
            img = self.create_test_image(text)
            img_path = os.path.join(self.test_dir, f"page_{i+1}.png")
            img.save(img_path)

            # Create PDF page and insert image
            page = doc.new_page(width=612, height=792)  # Letter size
            rect = fitz.Rect(50, 50, 562, 742)  # Leave margins
            page.insert_image(rect, filename=img_path)

        doc.save(pdf_path)
        doc.close()

        return pdf_path

    def test_ocr_service_initialization(self):
        """Test OCR service initialization."""
        service = OCRService()
        self.assertIsNotNone(service)
        self.assertIn(service.prefer_engine, ["tesseract", "easyocr"])

    def test_check_tesseract_availability(self):
        """Test Tesseract availability check."""
        available = self.ocr_service._check_tesseract()
        self.assertIsInstance(available, bool)

    def test_init_easyocr(self):
        """Test EasyOCR initialization."""
        # Should not raise exception
        self.ocr_service._init_easyocr()
        # EasyOCR reader might be None if not available
        self.assertTrue(self.ocr_service.easyocr_available or self.ocr_service.easyocr_reader is None)

    def test_preprocess_image(self):
        """Test image preprocessing."""
        img = self.create_test_image("Test")
        processed = self.ocr_service.preprocess_image(img)

        self.assertEqual(len(processed.shape), 2)  # Should be grayscale
        self.assertEqual(processed.dtype, np.uint8)

    def test_ocr_with_tesseract(self):
        """Test OCR with Tesseract."""
        if not self.ocr_service.tesseract_available:
            self.skipTest("Tesseract not available")

        img = self.create_test_image("Hello World")
        result = self.ocr_service.ocr_with_tesseract(img)

        self.assertIn("text", result)
        self.assertIn("confidence", result)
        self.assertIn("engine", result)
        self.assertEqual(result["engine"], "tesseract")

    def test_ocr_with_easyocr(self):
        """Test OCR with EasyOCR."""
        if not self.ocr_service.easyocr_available:
            self.skipTest("EasyOCR not available")

        img = self.create_test_image("Hello World")
        result = self.ocr_service.ocr_with_easyocr(img)

        self.assertIn("text", result)
        self.assertIn("confidence", result)
        self.assertIn("engine", result)
        self.assertEqual(result["engine"], "easyocr")

    def test_ocr_image(self):
        """Test OCR on a single image."""
        img = self.create_test_image("Test OCR Text")
        result = self.ocr_service.ocr_image(img)

        self.assertIn("text", result)
        self.assertIn("confidence", result)
        self.assertIn("engine", result)

        # Should extract some text (may not be perfect due to image quality)
        if result.get("text"):
            self.assertGreater(len(result["text"].strip()), 0)

    def test_extract_images_from_pdf(self):
        """Test extracting images from PDF."""
        pdf_path = self.create_test_pdf_with_images(["Page 1", "Page 2"])
        images = self.ocr_service.extract_images_from_pdf(pdf_path)

        self.assertEqual(len(images), 2)
        self.assertEqual(images[0][0], 1)  # Page numbers start from 1
        self.assertEqual(images[1][0], 2)

        # Clean up
        for page_num, img in images:
            img.close()

    def test_ocr_pdf(self):
        """Test OCR on entire PDF."""
        if not self.ocr_service.tesseract_available and not self.ocr_service.easyocr_available:
            self.skipTest("No OCR engines available")

        pdf_path = self.create_test_pdf_with_images(["First Page", "Second Page"])
        result = self.ocr_service.ocr_pdf(pdf_path)

        self.assertIn("text", result)
        self.assertIn("total_pages", result)
        self.assertIn("processed_pages", result)
        self.assertIn("average_confidence", result)
        self.assertIn("pages_data", result)

        self.assertEqual(result["total_pages"], 2)
        self.assertGreaterEqual(result["processed_pages"], 0)
        self.assertLessEqual(result["processed_pages"], 2)

    def test_detect_scanned_pdf(self):
        """Test scanned PDF detection."""
        # Create PDF with images (scanned-like)
        pdf_path = self.create_test_pdf_with_images(["Scanned Content"])
        result = self.ocr_service.detect_scanned_pdf(pdf_path)

        self.assertIn("is_scanned", result)
        self.assertIn("total_pages", result)
        self.assertIn("pages_with_text", result)
        self.assertIn("text_percentage", result)
        self.assertIn("recommendation", result)

        self.assertEqual(result["total_pages"], 1)
        self.assertGreaterEqual(result["pages_with_text"], 0)
        self.assertLessEqual(result["pages_with_text"], 1)

    def test_save_ocr_result(self):
        """Test saving OCR result to file."""
        ocr_result = {
            "text": "Sample OCR text",
            "total_pages": 1,
            "processed_pages": 1,
            "average_confidence": 85.5,
            "pages_data": [
                {"page": 1, "text": "Sample", "confidence": 85.5, "engine": "tesseract"}
            ],
            "language": "ita",
            "engines_used": ["tesseract"]
        }

        pdf_path = os.path.join(self.test_dir, "test.pdf")
        # Create a dummy PDF file
        with open(pdf_path, 'wb') as f:
            f.write(b"dummy pdf content")

        output_file = self.ocr_service.save_ocr_result(pdf_path, ocr_result)

        self.assertTrue(os.path.exists(output_file))
        self.assertTrue(output_file.endswith("_ocr.txt"))

        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Sample OCR text", content)
            self.assertIn("85.5%", content)

    def test_prefer_engine_setting(self):
        """Test setting preferred OCR engine."""
        # Test with tesseract
        service_tesseract = OCRService(prefer_engine="tesseract")
        self.assertEqual(service_tesseract.prefer_engine, "tesseract")

        # Test with easyocr
        service_easyocr = OCRService(prefer_engine="easyocr")
        self.assertEqual(service_easyocr.prefer_engine, "easyocr")

    def test_engine_fallback(self):
        """Test engine fallback when preferred engine fails."""
        # Create a service with non-existent preferred engine
        service = OCRService(prefer_engine="nonexistent")
        # Should still initialize without error
        self.assertIsNotNone(service)

    def test_async_ocr_pdf(self):
        """Test asynchronous OCR processing."""
        import asyncio

        if not self.ocr_service.tesseract_available and not self.ocr_service.easyocr_available:
            self.skipTest("No OCR engines available")

        pdf_path = self.create_test_pdf_with_images(["Async Test"])

        async def test_async():
            result = await self.ocr_service.async_ocr_pdf(pdf_path)
            return result

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_async())
            self.assertIn("text", result)
            self.assertIn("total_pages", result)
        finally:
            loop.close()

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        img = self.create_test_image("High Quality Text")

        if self.ocr_service.tesseract_available:
            result = self.ocr_service.ocr_with_tesseract(img)
            if result.get("confidence"):
                self.assertGreaterEqual(result["confidence"], 0)
                self.assertLessEqual(result["confidence"], 100)

        if self.ocr_service.easyocr_available:
            result = self.ocr_service.ocr_with_easyocr(img)
            if result.get("confidence"):
                self.assertGreaterEqual(result["confidence"], 0)
                self.assertLessEqual(result["confidence"], 100)

    def test_error_handling(self):
        """Test error handling in OCR operations."""
        # Test with non-existent file
        result = self.ocr_service.ocr_pdf("nonexistent.pdf")
        self.assertIn("error", result)

        # Test detect with non-existent file
        result = self.ocr_service.detect_scanned_pdf("nonexistent.pdf")
        self.assertIn("error", result)

        # Test save OCR result with invalid path
        ocr_result = {"text": "test"}
        output_file = self.ocr_service.save_ocr_result("nonexistent.pdf", ocr_result)
        self.assertEqual(output_file, "")


class TestOCRServiceIntegration(unittest.TestCase):
    """Integration tests for OCR service with real scenarios."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.ocr_service = OCRService()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after integration tests."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_multiple_page_document(self):
        """Test OCR on a multi-page document."""
        if not self.ocr_service.tesseract_available and not self.ocr_service.easyocr_available:
            self.skipTest("No OCR engines available")

        # Create a 3-page PDF
        texts = ["First page content", "Second page content", "Third page content"]
        pdf_path = os.path.join(self.test_dir, "multipage.pdf")

        # Create PDF with images
        doc = fitz.open()
        for i, text in enumerate(texts):
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((100, 300), text, fill='black')
            img_path = os.path.join(self.test_dir, f"page_{i+1}.png")
            img.save(img_path)

            page = doc.new_page()
            rect = fitz.Rect(50, 50, 750, 550)
            page.insert_image(rect, filename=img_path)

        doc.save(pdf_path)
        doc.close()

        # Process with OCR
        result = self.ocr_service.ocr_pdf(pdf_path)

        self.assertEqual(result["total_pages"], 3)
        self.assertGreaterEqual(result["processed_pages"], 0)

        # Should find text from at least some pages
        if result.get("text") and len(result["text"].strip()) > 0:
            self.assertIn("page", result["text"].lower())

    def test_different_languages(self):
        """Test OCR with different languages."""
        if not self.ocr_service.tesseract_available:
            self.skipTest("Tesseract not available")

        # Test with Italian text
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((100, 300), "Ciao mondo", fill='black')

        result_it = self.ocr_service.ocr_with_tesseract(img, lang='ita')
        self.assertIn("engine", result_it)
        self.assertEqual(result_it["engine"], "tesseract")

        # Test with English text
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((100, 300), "Hello world", fill='black')

        result_en = self.ocr_service.ocr_with_tesseract(img, lang='eng')
        self.assertIn("engine", result_en)
        self.assertEqual(result_en["engine"], "tesseract")


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestOCRService))
    suite.addTests(loader.loadTestsFromTestCase(TestOCRServiceIntegration))

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