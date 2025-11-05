from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, darkblue
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
from typing import List, Dict, Any, Optional

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom styles for the PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=darkblue,
            alignment=1,  # Center alignment
            borderWidth=0,
            borderColor=HexColor('#3B82F6')
        ))

        # Slide title style
        self.styles.add(ParagraphStyle(
            name='SlideTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=12,
            spaceBefore=20,
            textColor=darkblue,
            borderWidth=0,
            borderLeft=3,
            borderLeftColor=HexColor('#3B82F6'),
            leftIndent=10
        ))

        # Content style
        self.styles.add(ParagraphStyle(
            name='SlideContent',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            leftIndent=20,
            bulletIndent=10,
            bulletColor=HexColor('#3B82F6')
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=HexColor('#374151'),
            alignment=0
        ))

        # Book info style
        self.styles.add(ParagraphStyle(
            name='BookInfo',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=HexColor('#6B7280'),
            alignment=1  # Center alignment
        ))

    def generate_pdf_from_slides(self, slides_data: Dict[str, Any], output_path: Optional[str] = None) -> bytes:
        """
        Generate a PDF from slide data

        Args:
            slides_data: Dictionary containing title and slides
            output_path: Optional path to save the PDF file

        Returns:
            PDF bytes
        """
        # Create a buffer to hold the PDF
        buffer = io.BytesIO()

        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Build the story (content)
        story = []

        # Title page
        story.append(Paragraph(slides_data.get('title', 'Presentazione'), self.styles['CustomTitle']))
        story.append(Spacer(1, 20))

        # Add book info if available
        if 'book_info' in slides_data:
            book_info = slides_data['book_info']
            if book_info.get('title'):
                story.append(Paragraph(f"Libro: {book_info['title']}", self.styles['BookInfo']))
            if book_info.get('author'):
                story.append(Paragraph(f"Autore: {book_info['author']}", self.styles['BookInfo']))
            story.append(Spacer(1, 30))

        # Add slides
        slides = slides_data.get('slides', [])
        for i, slide in enumerate(slides):
            # Add page break for each slide (except the first one if it's on title page)
            if i > 0:
                story.append(PageBreak())

            # Slide number and title
            slide_number = slide.get('slide_number', i + 1)
            title = slide.get('title', f'Slide {slide_number}')

            # Add slide title with number
            numbered_title = f"Slide {slide_number}: {title}"
            story.append(Paragraph(numbered_title, self.styles['SlideTitle']))

            # Add visual elements if available
            visual_elements = slide.get('visual_elements', [])
            if visual_elements:
                story.append(Paragraph("📊 Elementi Visivi Suggeriti:", self.styles['SubTitle']))
                for visual in visual_elements:
                    if visual:
                        visual_text = f"• {visual}"
                        story.append(Paragraph(visual_text, self.styles['SlideContent']))
                story.append(Spacer(1, 8))

            # Add examples if available
            examples = slide.get('examples', [])
            if examples:
                story.append(Paragraph("💡 Esempi Pratici:", self.styles['SubTitle']))
                for example in examples:
                    if example:
                        example_text = f"• {example}"
                        story.append(Paragraph(example_text, self.styles['SlideContent']))
                story.append(Spacer(1, 8))

            # Add main content
            content = slide.get('content', [])
            if isinstance(content, list):
                story.append(Paragraph("📚 Contenuti Principali:", self.styles['SubTitle']))
                story.append(Spacer(1, 4))

                for point_idx, point in enumerate(content, 1):
                    # Clean up the content point
                    cleaned_point = str(point).strip()
                    if cleaned_point:
                        # Enhanced formatting for detailed content
                        if len(cleaned_point) > 150:  # Long content, format as numbered paragraph
                            formatted_point = f"{point_idx}. {cleaned_point}"
                            para_style = self.styles['SlideContent']
                        else:
                            # Short content, use bullet format
                            if not cleaned_point.startswith('•') and not cleaned_point.startswith(f"{point_idx}."):
                                formatted_point = f"• {cleaned_point}"
                            else:
                                formatted_point = cleaned_point
                            para_style = self.styles['SlideContent']

                        # Add paragraph with proper spacing
                        story.append(Paragraph(formatted_point, para_style))
                        story.append(Spacer(1, 3))
            else:
                # Single content point
                cleaned_content = str(content).strip()
                if cleaned_content:
                    if not cleaned_content.startswith('•') and not cleaned_content.startswith('-'):
                        cleaned_content = f'• {cleaned_content}'
                    story.append(Paragraph(cleaned_content, self.styles['SlideContent']))

            # Add some space after each slide
            story.append(Spacer(1, 15))

        # Build the PDF
        doc.build(story)

        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Save to file if path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes

    def generate_pdf_from_images(self, slide_images: List[Dict], title: str, output_path: Optional[str] = None) -> bytes:
        """
        Generate a PDF from slide images created by Z.AI GLM Slide Agent

        Args:
            slide_images: List of dictionaries containing slide image data
            title: PDF title
            output_path: Optional path to save the PDF file

        Returns:
            PDF bytes
        """
        from reportlab.platypus import Image, PageBreak

        # Create a buffer to hold the PDF
        buffer = io.BytesIO()

        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        # Build the story (content)
        story = []

        # Title page
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Paragraph("Generated by Z.AI GLM Slide Agent", self.styles['SubTitle']))
        story.append(Spacer(1, 50))

        # Add each slide image as a full page
        for slide_data in slide_images:
            story.append(PageBreak())

            # Add slide number
            slide_number = slide_data.get('slide_number', '?')
            story.append(Paragraph(f"Slide {slide_number}", self.styles['SlideTitle']))
            story.append(Spacer(1, 20))

            # Decode base64 image data
            import base64
            try:
                image_data = base64.b64decode(slide_data['image_data'])

                # Create temporary image file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    temp_file.write(image_data)
                    temp_file_path = temp_file.name

                # Add image to PDF
                img = Image(temp_file_path, width=7*inch, height=5*inch)
                img.hAlign = 'CENTER'
                story.append(img)

                # Clean up temporary file
                import os
                os.unlink(temp_file_path)

            except Exception as e:
                # Fallback if image can't be processed
                story.append(Paragraph(f"[Slide {slide_number} Image]", self.styles['SubTitle']))
                story.append(Paragraph("Image could not be displayed", self.styles['SlideContent']))

        # Build the PDF
        doc.build(story)

        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Save to file if path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes

    def generate_pdf_from_html_content(self, html_content: str, slides_data: Dict, output_path: Optional[str] = None) -> bytes:
        """
        Generate a PDF from HTML content (placeholder for future implementation)

        Args:
            html_content: HTML content string
            slides_data: Dictionary containing slide data
            output_path: Optional path to save the PDF file

        Returns:
            PDF bytes
        """
        # For now, convert HTML to text and use the regular slide generator
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()

            # Create a simple slide from the text content
            simple_slides_data = {
                'title': slides_data.get('title', 'Presentazione'),
                'slides': [
                    {
                        'slide_number': 1,
                        'title': 'Contenuto Generato',
                        'content': text_content.split('\n')[:20]  # First 20 lines
                    }
                ]
            }

            return self.generate_pdf_from_slides(simple_slides_data, output_path)

        except Exception:
            # Fallback: create a simple PDF with HTML content
            simple_slides_data = {
                'title': slides_data.get('title', 'Presentazione'),
                'slides': [
                    {
                        'slide_number': 1,
                        'title': 'Contenuto HTML',
                        'content': [html_content[:1000] + "..." if len(html_content) > 1000 else html_content]
                    }
                ]
            }

            return self.generate_pdf_from_slides(simple_slides_data, output_path)

    def generate_simple_pdf(self, title: str, content: List[str], output_path: Optional[str] = None) -> bytes:
        """
        Generate a simple PDF with title and content list

        Args:
            title: PDF title
            content: List of content strings
            output_path: Optional path to save the PDF file

        Returns:
            PDF bytes
        """
        slides_data = {
            'title': title,
            'slides': [
                {
                    'slide_number': i + 1,
                    'title': f"Concetto {i + 1}",
                    'content': [content[i]] if i < len(content) else []
                }
                for i in range(len(content))
            ]
        }

        return self.generate_pdf_from_slides(slides_data, output_path)