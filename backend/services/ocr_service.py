#!/usr/bin/env python3
"""
OCR Service for processing scanned PDFs and images
Supports multiple OCR engines: Tesseract and EasyOCR
"""

import os
import io
import cv2
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
import easyocr
import tempfile
import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import asyncio
import aiofiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRService:
    """Service for OCR processing of PDFs and images"""

    def __init__(self, prefer_engine: str = "tesseract"):
        """
        Initialize OCR service

        Args:
            prefer_engine: Preferred OCR engine ("tesseract" or "easyocr")
        """
        self.prefer_engine = prefer_engine
        self.easyocr_reader = None

        # Configure Tesseract
        self.tesseract_available = self._check_tesseract()

        # Initialize EasyOCR on first use
        self.easyocr_available = True

        logger.info(f"OCR Service initialized with preferred engine: {prefer_engine}")
        logger.info(f"Tesseract available: {self.tesseract_available}")
        logger.info(f"EasyOCR available: {self.easyocr_available}")

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            return False

    def _init_easyocr(self):
        """Initialize EasyOCR reader on first use"""
        if self.easyocr_reader is None and self.easyocr_available:
            try:
                self.easyocr_reader = easyocr.Reader(['it', 'en'])
                logger.info("EasyOCR reader initialized")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self.easyocr_available = False

    def extract_images_from_pdf(self, pdf_path: str) -> List[Tuple[int, Image.Image]]:
        """
        Extract images from PDF pages

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of (page_number, image) tuples
        """
        images = []

        try:
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Get page as image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                images.append((page_num + 1, img))

            doc.close()

        except Exception as e:
            logger.error(f"Error extracting images from PDF {pdf_path}: {e}")

        return images

    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Preprocess image for better OCR results

        Args:
            image: PIL Image

        Returns:
            Preprocessed image as numpy array
        """
        # Convert to numpy array
        img_array = np.array(image)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Denoise
        denoised = cv2.medianBlur(binary, 5)

        return denoised

    def ocr_with_tesseract(self, image: Image.Image, lang: str = 'ita') -> Dict[str, Any]:
        """
        Perform OCR using Tesseract

        Args:
            image: PIL Image
            lang: Language code ('ita', 'eng', etc.)

        Returns:
            OCR result dictionary
        """
        if not self.tesseract_available:
            return {"text": "", "confidence": 0, "error": "Tesseract not available"}

        try:
            # Preprocess image
            processed_img = self.preprocess_image(image)

            # Perform OCR
            custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
            text = pytesseract.image_to_string(processed_img, lang=lang, config=custom_config)

            # Get confidence scores
            data = pytesseract.image_to_data(processed_img, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)

            # Calculate average confidence for detected words
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "text": text.strip(),
                "confidence": avg_confidence,
                "engine": "tesseract",
                "language": lang
            }

        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return {"text": "", "confidence": 0, "error": str(e), "engine": "tesseract"}

    def ocr_with_easyocr(self, image: Image.Image) -> Dict[str, Any]:
        """
        Perform OCR using EasyOCR

        Args:
            image: PIL Image

        Returns:
            OCR result dictionary
        """
        if not self.easyocr_available:
            return {"text": "", "confidence": 0, "error": "EasyOCR not available"}

        try:
            # Initialize EasyOCR if needed
            self._init_easyocr()
            if self.easyocr_reader is None:
                return {"text": "", "confidence": 0, "error": "EasyOCR initialization failed"}

            # Convert PIL to numpy array
            img_array = np.array(image)

            # Perform OCR
            results = self.easyocr_reader.readtext(img_array)

            # Combine text and calculate confidence
            text_parts = []
            confidences = []

            for (bbox, text, confidence) in results:
                text_parts.append(text)
                confidences.append(confidence)

            combined_text = " ".join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "text": combined_text.strip(),
                "confidence": avg_confidence * 100,  # Convert to percentage
                "engine": "easyocr",
                "language": "auto"
            }

        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return {"text": "", "confidence": 0, "error": str(e), "engine": "easyocr"}

    def ocr_image(self, image: Image.Image, language: str = 'ita') -> Dict[str, Any]:
        """
        Perform OCR on a single image using preferred engine

        Args:
            image: PIL Image
            language: Language code for Tesseract

        Returns:
            OCR result dictionary
        """
        results = []

        # Try preferred engine first
        if self.prefer_engine == "tesseract" and self.tesseract_available:
            result = self.ocr_with_tesseract(image, language)
            results.append(result)
        elif self.prefer_engine == "easyocr" and self.easyocr_available:
            result = self.ocr_with_easyocr(image)
            results.append(result)

        # Try fallback engine if preferred failed or had low confidence
        if len(results) == 0 or (results[0].get("confidence", 0) < 50 and results[0].get("text", "").strip()):
            if self.prefer_engine != "tesseract" and self.tesseract_available:
                fallback_result = self.ocr_with_tesseract(image, language)
                if fallback_result.get("text", "").strip():
                    results.append(fallback_result)
            elif self.prefer_engine != "easyocr" and self.easyocr_available:
                fallback_result = self.ocr_with_easyocr(image)
                if fallback_result.get("text", "").strip():
                    results.append(fallback_result)

        # Return best result (highest confidence with actual text)
        best_result = {"text": "", "confidence": 0, "engine": "none"}
        for result in results:
            if (result.get("confidence", 0) > best_result["confidence"] and
                result.get("text", "").strip()):
                best_result = result

        return best_result

    def ocr_pdf(self, pdf_path: str, language: str = 'ita') -> Dict[str, Any]:
        """
        Perform OCR on entire PDF document

        Args:
            pdf_path: Path to PDF file
            language: Language code for Tesseract

        Returns:
            OCR result dictionary with page-by-page text
        """
        if not os.path.exists(pdf_path):
            return {"error": f"PDF file not found: {pdf_path}"}

        logger.info(f"Starting OCR for PDF: {pdf_path}")

        # Extract images from PDF
        page_images = self.extract_images_from_pdf(pdf_path)

        if not page_images:
            return {"error": "No images could be extracted from PDF"}

        full_text = ""
        pages_data = []
        total_confidence = 0
        processed_pages = 0

        for page_num, image in page_images:
            logger.info(f"Processing page {page_num}/{len(page_images)}")

            # Perform OCR on page image
            page_result = self.ocr_image(image, language)

            if page_result.get("text", "").strip():
                page_text = f"--- Page {page_num} ---\n{page_result['text']}\n\n"
                full_text += page_text

                pages_data.append({
                    "page": page_num,
                    "text": page_result["text"],
                    "confidence": page_result.get("confidence", 0),
                    "engine": page_result.get("engine", "unknown")
                })

                total_confidence += page_result.get("confidence", 0)
                processed_pages += 1

            # Clean up
            image.close()

        # Calculate overall confidence
        avg_confidence = total_confidence / processed_pages if processed_pages > 0 else 0

        result = {
            "text": full_text.strip(),
            "total_pages": len(page_images),
            "processed_pages": processed_pages,
            "average_confidence": avg_confidence,
            "pages_data": pages_data,
            "language": language,
            "engines_used": list(set(page.get("engine", "unknown") for page in pages_data))
        }

        logger.info(f"OCR completed for {pdf_path}: {processed_pages}/{len(page_images)} pages processed")

        return result

    async def async_ocr_pdf(self, pdf_path: str, language: str = 'ita') -> Dict[str, Any]:
        """
        Asynchronous OCR processing for PDF

        Args:
            pdf_path: Path to PDF file
            language: Language code for Tesseract

        Returns:
            OCR result dictionary
        """
        # Run OCR in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.ocr_pdf, pdf_path, language)

    def detect_scanned_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Detect if PDF is scanned by checking for text content

        Args:
            pdf_path: Path to PDF file

        Returns:
            Detection result dictionary
        """
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            pages_with_text = 0
            total_text_length = 0

            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                text = page.get_text()

                if text.strip():
                    pages_with_text += 1
                    total_text_length += len(text.strip())

            doc.close()

            # Calculate metrics
            text_percentage = (pages_with_text / total_pages) * 100 if total_pages > 0 else 0
            avg_text_per_page = total_text_length / total_pages if total_pages > 0 else 0

            # Determine if likely scanned
            is_scanned = text_percentage < 30 or avg_text_per_page < 100

            return {
                "is_scanned": is_scanned,
                "total_pages": total_pages,
                "pages_with_text": pages_with_text,
                "text_percentage": text_percentage,
                "avg_text_per_page": avg_text_per_page,
                "recommendation": "ocr" if is_scanned else "text_extraction"
            }

        except Exception as e:
            logger.error(f"Error detecting scanned PDF {pdf_path}: {e}")
            return {
                "is_scanned": True,  # Assume scanned on error
                "error": str(e),
                "recommendation": "ocr"
            }

    def save_ocr_result(self, pdf_path: str, ocr_result: Dict[str, Any]) -> str:
        """
        Save OCR result to text file

        Args:
            pdf_path: Original PDF path
            ocr_result: OCR result dictionary

        Returns:
            Path to saved text file
        """
        try:
            # Create output path
            pdf_stem = Path(pdf_path).stem
            output_dir = Path(pdf_path).parent / "ocr_results"
            output_dir.mkdir(exist_ok=True)

            output_file = output_dir / f"{pdf_stem}_ocr.txt"

            # Save result
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"OCR Result for: {pdf_path}\n")
                f.write(f"Total Pages: {ocr_result.get('total_pages', 'N/A')}\n")
                f.write(f"Processed Pages: {ocr_result.get('processed_pages', 'N/A')}\n")
                f.write(f"Average Confidence: {ocr_result.get('average_confidence', 0):.1f}%\n")
                f.write(f"Engines Used: {', '.join(ocr_result.get('engines_used', []))}\n")
                f.write("=" * 50 + "\n\n")
                f.write(ocr_result.get('text', ''))

            logger.info(f"OCR result saved to: {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Error saving OCR result: {e}")
            return ""

# Global instance
ocr_service = OCRService()