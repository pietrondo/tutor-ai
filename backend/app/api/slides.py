from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging
import uuid
import os
import base64
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

from services.llm_service import LLMService

router = APIRouter(prefix="/slides", tags=["slides"])

# Data models
class SlideGenerationRequest(BaseModel):
    course_id: str
    book_id: Optional[str] = None
    topic: str
    description: Optional[str] = None
    num_slides: int = 8
    style: str = "modern"
    audience: str = "university"

class SlideGenerationResponse(BaseModel):
    success: bool
    slide_id: str
    topic: str
    slide_urls: List[str]
    download_urls: List[str]
    metadata: Dict[str, Any]

class SlideVersionRequest(BaseModel):
    original_slide_id: str
    topic: Optional[str] = None
    description: Optional[str] = None
    num_slides: Optional[int] = None
    style: Optional[str] = None

class SlideListRequest(BaseModel):
    course_id: str
    book_id: Optional[str] = None
    topic: Optional[str] = None
    limit: int = 20

# Slide storage service
class SlideStorageService:
    def __init__(self):
        self.storage_file = "data/slide_generations.json"
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w') as f:
                json.dump({"slides": {}, "version": "1.0"}, f, indent=2)

    def _load_storage(self):
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except:
            return {"slides": {}, "version": "1.0"}

    def _save_storage(self, data):
        data["last_updated"] = datetime.now().isoformat()
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)

    def save_slide_generation(self, slide_data: Dict) -> str:
        storage = self._load_storage()
        slide_id = slide_data["id"]

        # Use course+topic as key for grouping
        key = f"{slide_data['course_id']}_{slide_data['topic'].lower().replace(' ', '_')}"

        if key not in storage["slides"]:
            storage["slides"][key] = []

        storage["slides"][key].append(slide_data)
        self._save_storage(storage)
        return slide_id

    def get_slides(self, course_id: str, book_id: Optional[str] = None, topic: Optional[str] = None, limit: int = 20) -> List[Dict]:
        storage = self._load_storage()
        results = []

        for slide_list in storage["slides"].values():
            for slide in slide_list:
                if slide["course_id"] != course_id:
                    continue
                if book_id and slide.get("book_id") != book_id:
                    continue
                if topic and topic.lower() not in slide["topic"].lower():
                    continue
                results.append(slide)

        # Sort by creation date (newest first)
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results[:limit]

    def get_slide_versions(self, course_id: str, topic: str) -> List[Dict]:
        storage = self._load_storage()
        key = f"{course_id}_{topic.lower().replace(' ', '_')}"

        if key in storage["slides"]:
            slides = storage["slides"][key]
            slides.sort(key=lambda x: x["created_at"], reverse=True)
            return slides
        return []

    def get_slide(self, slide_id: str) -> Optional[Dict]:
        """Get a specific slide by ID"""
        storage = self._load_storage()

        for slide_list in storage["slides"].values():
            for slide in slide_list:
                if slide["id"] == slide_id:
                    return slide
        return None

# Dependency injection
def get_slide_storage() -> SlideStorageService:
    return SlideStorageService()

def get_llm_service() -> LLMService:
    return LLMService()

@router.post("/generate", response_model=SlideGenerationResponse)
async def generate_slides(
    request: SlideGenerationRequest,
    llm_service: LLMService = Depends(get_llm_service),
    slide_storage: SlideStorageService = Depends(get_slide_storage)
):
    """
    Generate slides using Z.AI GLM Slide Agent
    """
    try:
        slide_id = str(uuid.uuid4())

        rag_context = ""
        if request.book_id:
            try:
                from services.rag_service import RAGService

                rag_service = RAGService()
                rag_response = await rag_service.retrieve_context(
                    f"Create slides about {request.topic}",
                    request.course_id,
                    request.book_id,
                    k=5
                )
                rag_context = rag_response.get("text", "")
                if rag_context:
                    logger.info(
                        "Retrieved RAG context for slide generation: %s characters",
                        len(rag_context)
                    )
            except Exception as exc:
                logger.warning(f"Failed to get RAG context: {exc}")

        use_zai_agent = llm_service.model_type == "zai" and getattr(llm_service, "zai_manager", None)

        if not use_zai_agent:
            logger.warning("ZAI not available, creating slides with RAG content")

            slide_content = await generate_slide_content(
                request.topic,
                request.num_slides,
                request.style,
                rag_context
            )

            slide_urls = []
            for index, content in enumerate(slide_content):
                pdf_bytes = create_slide_pdf(content, request.style, index + 1, request.num_slides)
                slide_url = f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}"
                slide_urls.append(slide_url)

            slide_data = {
                "id": slide_id,
                "course_id": request.course_id,
                "book_id": request.book_id,
                "topic": request.topic,
                "description": request.description or f"Slides with RAG content for {request.topic}",
                "num_slides": request.num_slides,
                "style": request.style,
                "audience": request.audience,
                "slide_urls": slide_urls,
                "download_urls": slide_urls,
                "generation_method": "rag_content",
                "created_at": datetime.now().isoformat(),
                "response_content": f"Generated {request.num_slides} slides with RAG content about {request.topic}",
                "version": 1
            }

            slide_storage.save_slide_generation(slide_data)

            return SlideGenerationResponse(
                success=True,
                slide_id=slide_id,
                topic=request.topic,
                slide_urls=slide_urls,
                download_urls=slide_urls,
                metadata={
                    "generation_method": "rag_content",
                    "num_slides": len(slide_urls),
                    "style": request.style,
                    "audience": request.audience,
                    "created_at": slide_data["created_at"],
                    "content_type": "HTML slides with RAG content"
                }
            )

        description = request.description.strip() if request.description else (
            f"Create a professional {request.num_slides}-slide presentation about {request.topic} "
            f"for {request.audience} level students with {request.style} style"
        )

        if rag_context:
            description = (
                f"{description}. Use this context from course materials: {rag_context[:500]}"
            )

        zai_result = await llm_service.generate_slides_with_glm_slide_agent(
            course_id=request.course_id,
            topic=request.topic,
            content_context=rag_context,
            num_slides=request.num_slides,
            style=request.style,
            description=description,
            include_pdf=True
        )

        if not zai_result.get("success"):
            error_message = zai_result.get("error") or "Z.AI slide agent request failed"
            logger.error("ZAI slide agent failed: %s", zai_result)
            raise HTTPException(status_code=500, detail=error_message)

        def build_local_url(path: Optional[str]) -> Optional[str]:
            if not path:
                return None
            try:
                if os.path.exists(path):
                    return f"/slides/static/{os.path.basename(path)}"
            except Exception as exc:
                logger.debug(f"Unable to build local slide URL for {path}: {exc}")
            return None

        slide_urls: List[str] = []
        pdf_url = zai_result.get("slide_pdf_url")
        html_path = zai_result.get("slide_html_path")
        pdf_path = zai_result.get("slide_pdf_path")
        image_urls = zai_result.get("image_urls", [])
        pdf_local_url = build_local_url(pdf_path)
        html_local_url = build_local_url(html_path)

        if pdf_url:
            slide_urls.append(pdf_url)

        for img_url in image_urls:
            if img_url and img_url not in slide_urls:
                slide_urls.append(img_url)

        if pdf_local_url and pdf_local_url not in slide_urls:
            slide_urls.append(pdf_local_url)
        if not slide_urls and pdf_path:
            slide_urls.append(pdf_path)
        if not slide_urls and html_local_url:
            slide_urls.append(html_local_url)
        if not slide_urls and html_path:
            slide_urls.append(html_path)

        download_urls: List[str] = []
        if pdf_url:
            download_urls.append(pdf_url)
        if pdf_local_url and pdf_local_url not in download_urls:
            download_urls.append(pdf_local_url)
        if pdf_path and pdf_path not in download_urls:
            download_urls.append(pdf_path)
        if html_local_url and html_local_url not in download_urls:
            download_urls.append(html_local_url)
        if html_path and not download_urls:
            download_urls.append(html_path)
        if not download_urls:
            download_urls = slide_urls.copy()

        slide_data = {
            "id": slide_id,
            "course_id": request.course_id,
            "book_id": request.book_id,
            "topic": request.topic,
            "description": description,
            "num_slides": request.num_slides,
            "style": request.style,
            "audience": request.audience,
            "slide_urls": slide_urls,
            "download_urls": download_urls,
            "generation_method": zai_result.get("generation_method", "zai_glm_slide_agent"),
            "created_at": datetime.now().isoformat(),
            "response_content": zai_result.get("html_content") or "\n".join(zai_result.get("text_fragments", [])),
            "slides_data": zai_result.get("slides_data"),
            "image_urls": zai_result.get("image_urls", []),
            "slide_pdf_url": pdf_url,
            "slide_pdf_path": pdf_path,
            "slide_pdf_local_url": pdf_local_url,
            "slide_html_path": html_path,
            "slide_html_local_url": html_local_url,
            "conversation_id": zai_result.get("conversation_id"),
            "metadata": zai_result.get("metadata", {}),
            "version": 1
        }

        slide_storage.save_slide_generation(slide_data)

        response_metadata = {
            "generation_method": slide_data["generation_method"],
            "num_slides": zai_result.get("metadata", {}).get("num_slides", request.num_slides),
            "style": request.style,
            "audience": request.audience,
            "created_at": slide_data["created_at"],
            "pdf_path": pdf_path,
            "pdf_url": pdf_url,
            "html_path": html_path,
            "pdf_local_url": pdf_local_url,
            "html_local_url": html_local_url,
            "image_count": len(zai_result.get("image_urls", [])),
            "conversation_id": slide_data.get("conversation_id")
        }

        if zai_result.get("slides_data") is not None:
            response_metadata["slides_data"] = zai_result["slides_data"]

        return SlideGenerationResponse(
            success=True,
            slide_id=slide_id,
            topic=request.topic,
            slide_urls=slide_urls,
            download_urls=download_urls,
            metadata=response_metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating slides: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate slides: {str(e)}")

@router.post("/regenerate")
async def regenerate_slides(
    request: SlideVersionRequest,
    llm_service: LLMService = Depends(get_llm_service),
    slide_storage: SlideStorageService = Depends(get_slide_storage)
):
    """
    Regenerate slides based on an existing generation
    """
    try:
        # Find the original slide
        storage = slide_storage._load_storage()
        original_slide = None

        for slide_list in storage["slides"].values():
            for slide in slide_list:
                if slide["id"] == request.original_slide_id:
                    original_slide = slide
                    break
            if original_slide:
                break

        if not original_slide:
            raise HTTPException(status_code=404, detail="Original slide not found")

        # Create new generation request based on original
        new_request = SlideGenerationRequest(
            course_id=original_slide["course_id"],
            book_id=original_slide.get("book_id"),
            topic=request.topic or original_slide["topic"],
            description=request.description,
            num_slides=request.num_slides or original_slide["num_slides"],
            style=request.style or original_slide["style"],
            audience=original_slide["audience"]
        )

        # Generate new slides
        result = await generate_slides(new_request, llm_service, slide_storage)

        # Update version info
        storage = slide_storage._load_storage()
        for slide_list in storage["slides"].values():
            for slide in slide_list:
                if slide["id"] == result.slide_id:
                    slide["version"] = len([s for s in slide_list if s["topic"] == slide["topic"]])
                    slide["regenerated_from"] = request.original_slide_id
                    break

        slide_storage._save_storage(storage)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating slides: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to regenerate slides: {str(e)}")

@router.get("/list")
async def list_slides(
    course_id: str,
    book_id: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 20,
    slide_storage: SlideStorageService = Depends(get_slide_storage)
):
    """
    List slide generations for a course
    """
    try:
        slides = slide_storage.get_slides(course_id, book_id, topic, limit)
        return {
            "success": True,
            "slides": slides,
            "count": len(slides)
        }
    except Exception as e:
        logger.error(f"Error listing slides: {e}")
        raise HTTPException(status_code=500, detail="Failed to list slides")

@router.get("/versions")
async def get_slide_versions(
    course_id: str,
    topic: str,
    slide_storage: SlideStorageService = Depends(get_slide_storage)
):
    """
    Get all versions of slides for a specific topic
    """
    try:
        versions = slide_storage.get_slide_versions(course_id, topic)
        return {
            "success": True,
            "versions": versions,
            "count": len(versions),
            "topic": topic
        }
    except Exception as e:
        logger.error(f"Error getting slide versions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get slide versions")

@router.get("/{slide_id}")
async def get_slide(
    slide_id: str,
    slide_storage: SlideStorageService = Depends(get_slide_storage)
):
    """
    Get a specific slide generation by ID
    """
    try:
        storage = slide_storage._load_storage()

        for slide_list in storage["slides"].values():
            for slide in slide_list:
                if slide["id"] == slide_id:
                    return {
                        "success": True,
                        "slide": slide
                    }

        raise HTTPException(status_code=404, detail="Slide not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting slide: {e}")
        raise HTTPException(status_code=500, detail="Failed to get slide")

@router.delete("/{slide_id}")
async def delete_slide(
    slide_id: str,
    slide_storage: SlideStorageService = Depends(get_slide_storage)
):
    """
    Delete a slide generation
    """
    try:
        storage = slide_storage._load_storage()

        for key, slide_list in storage["slides"].items():
            for i, slide in enumerate(slide_list):
                if slide["id"] == slide_id:
                    slide_list.pop(i)
                    if not slide_list:
                        del storage["slides"][key]
                    slide_storage._save_storage(storage)
                    return {
                        "success": True,
                        "message": "Slide deleted successfully"
                    }

        raise HTTPException(status_code=404, detail="Slide not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting slide: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete slide")

@router.get("/stats")
async def get_stats(slide_storage: SlideStorageService = Depends(get_slide_storage)):
    """
    Get slide generation statistics
    """
    try:
        storage = slide_storage._load_storage()

        total_slides = 0
        total_topics = set()
        total_courses = set()

        for slide_list in storage["slides"].values():
            for slide in slide_list:
                total_slides += 1
                total_topics.add(slide["topic"])
                total_courses.add(slide["course_id"])

        return {
            "success": True,
            "stats": {
                "total_generations": total_slides,
                "unique_topics": len(total_topics),
                "unique_courses": len(total_courses),
                "last_updated": storage.get("last_updated")
            }
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")


@router.get("/download/{slide_id}")
async def download_unified_pdf(slide_id: str, slide_storage: SlideStorageService = Depends(get_slide_storage)):
    """
    Generate and download a unified PDF with all slides
    """
    try:
        # Get slide data
        slide_data = slide_storage.get_slide(slide_id)
        if not slide_data:
            raise HTTPException(status_code=404, detail="Slide not found")

        # Generate slide content again
        slide_content = await generate_slide_content(
            slide_data["topic"],
            slide_data["num_slides"],
            slide_data["style"],
            ""  # We'll regenerate RAG context if needed
        )

        # Create unified PDF
        pdf_bytes = create_unified_pdf(slide_content, slide_data)

        # Return as downloadable file
        import base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode()

        return {
            "success": True,
            "filename": f"{slide_data['topic'].replace(' ', '_').lower()}_completo.pdf",
            "pdf_url": f"data:application/pdf;base64,{pdf_base64}",
            "size": len(pdf_bytes)
        }

    except Exception as e:
        logger.error(f"Error generating unified PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")


# Helper functions for generating slide content
async def generate_slide_content(topic: str, num_slides: int, style: str, rag_context: str = "") -> List[Dict]:
    """Generate structured content for slides based on topic and RAG context"""

    # Basic slide structure
    if num_slides == 1:
        return [
            {
                "title": topic,
                "content": [
                    f"Panoramica su {topic}",
                    rag_context[:200] + "..." if rag_context else "Contenuto in elaborazione...",
                    "Punti chiave e concetti principali"
                ],
                "type": "title"
            }
        ]

    slides = []

    # Title slide
    slides.append({
        "title": topic,
        "content": [
            f"Presentazione su {topic}",
            f"Generata il {datetime.now().strftime('%d/%m/%Y')}",
            f"Stile: {style}"
        ],
        "type": "title"
    })

    # Content slides
    if rag_context:
        # Split RAG content into chunks for different slides
        content_chunks = split_text_into_chunks(rag_context, num_slides - 2)

        for i, chunk in enumerate(content_chunks):
            slides.append({
                "title": f"{topic} - Parte {i + 1}",
                "content": [
                    chunk,
                    "Analisi e approfondimento",
                    "Applicazioni pratiche"
                ],
                "type": "content"
            })
    else:
        # Enhanced content slides when no RAG context is available
        # Generate meaningful content based on common topics
        topic_lower = topic.lower()

        # Topic-specific content generation
        if "america" in topic_lower or "scoperta" in topic_lower:
            content_templates = [
                ["Il contesto storico della scoperta", "Le rotte commerciali verso l'Oriente", "La ricerca di nuove vie marittime"],
                ["I protagonisti dell'esplorazione", "Cristoforo Colombo e il suo progetto", "I finanziatori e i sostenitori"],
                ["Il viaggio e l'impatto", "La partenza da Palos de la Frontera", "L'arrivo nel Nuovo Mondo"],
                ["Le conseguenze storiche", "Lo scambio colombiano", "La trasformazione del mondo conosciuto"],
                ["L'eredità della scoperta", "L'impatto sulla cultura europea", "La nascita di un'era globale"]
            ]
        elif "caboto" in topic_lower or "giovanni caboto" in topic_lower:
            content_templates = [
                ["Giovanni Caboto: l'esploratore", "Le sue origini italiane", "La sua formazione marinara"],
                ["Il progetto inglese", "Il supporto di Enrico VII", "La preparazione del viaggio"],
                ["La scoperta del Nord America", "L'approdo sulle coste del Canada", "Il territorio di 'Nuova Terra'"],
                ["Le conseguenze per l'Inghilterra", "Le rivendicazioni territoriali", "Le future esplorazioni"],
                ["L'eredità di Caboto", "Il suo ruolo nella storia", "I suoi successori nelle esplorazioni"]
            ]
        elif "roma" in topic_lower or "romano" in topic_lower:
            content_templates = [
                ["Le origini di Roma", "La leggenda di Romolo e Remo", "La fondazione della città"],
                ["La Repubblica Romana", "Le istituzioni politiche", "L'espansione territoriale"],
                ["L'Impero Romano", "Da Ottaviano Augusto", "La massima espansione"],
                ["La società romana", "La struttura sociale", "La vita quotidiana"],
                ["L'eredità di Roma", "Il diritto romano", "L'influenza sulla civiltà occidentale"]
            ]
        else:
            # Generic but meaningful content for any topic
            content_templates = [
                [f"Introduzione a {topic}", f"Il contesto storico e culturale", f"L'importanza nella storia"],
                [f"Gli aspetti principali di {topic}", f"Le caratteristiche fondamentali", f"Gli elementi distintivi"],
                [f"Lo sviluppo di {topic}", f"Le fasi evolutive", f"I cambiamenti nel tempo"],
                [f"L'impatto di {topic}", f"Le conseguenze storiche", f"L'influenza sulla società"],
                [f"L'eredità di {topic}", f"La rilevanza attuale", f"Gli insegnamenti per il presente"]
            ]

        # Use templates or generate generic content if more slides needed
        for i in range(min(num_slides - 2, len(content_templates))):
            slides.append({
                "title": f"{topic} - Parte {i + 1}",
                "content": content_templates[i],
                "type": "content"
            })

        # Add more generic slides if needed
        for i in range(len(content_templates), num_slides - 2):
            slides.append({
                "title": f"{topic} - Approfondimento {i + 1}",
                "content": [
                    f"Analisi approfondita di {topic}",
                    f"Aspetti secondari ma rilevanti",
                    f"Connessioni con altri ambiti"
                ],
                "type": "content"
            })

    # Conclusion slide
    slides.append({
        "title": "Conclusioni",
        "content": [
            "Riepilogo dei punti principali",
            "Considerazioni finali",
            "Domande e discussione"
        ],
        "type": "conclusion"
    })

    return slides[:num_slides]


def split_text_into_chunks(text: str, num_chunks: int) -> List[str]:
    """Split text into roughly equal chunks"""
    if not text:
        return [""] * num_chunks

    # Clean and prepare text
    text = text.strip()
    words = text.split()

    if len(words) <= num_chunks:
        return text.split('\n') if '\n' in text else [text] * num_chunks

    chunk_size = len(words) // num_chunks
    chunks = []

    for i in range(num_chunks):
        start = i * chunk_size
        end = start + chunk_size if i < num_chunks - 1 else len(words)
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)

    return chunks


def create_slide_pdf(content: Dict, style: str, slide_number: int, total_slides: int) -> bytes:
    """Create PDF representation of a slide using ReportLab"""

    # Create a buffer for the PDF
    buffer = io.BytesIO()

    # Create the PDF document with A4 page size
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)

    # Container for the story
    story = []

    # Define styles
    styles = getSampleStyleSheet()

    # Create custom style for title
    title_style = ParagraphStyle(
        'CustomTitle',
        fontSize=24,
        leading=28,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor=HexColor('#333333')
    )

    # Create custom style for content
    content_style = ParagraphStyle(
        'CustomContent',
        fontSize=14,
        leading=18,
        spaceAfter=6,
        alignment=TA_LEFT,
        textColor=HexColor('#333333')
    )

    # Create custom style for slide info
    slide_info_style = ParagraphStyle(
        'SlideInfo',
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
        textColor=HexColor('#666666')
    )

    styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Normal'],
                            fontSize=24, leading=28, spaceAfter=12,
                            alignment=TA_CENTER, textColor=HexColor('#333333')))

    styles.add(ParagraphStyle(name='CustomContent', parent=styles['Normal'],
                            fontSize=14, leading=18, spaceAfter=6,
                            alignment=TA_LEFT, textColor=HexColor('#333333')))

    styles.add(ParagraphStyle(name='SlideInfo', parent=styles['Normal'],
                            fontSize=10, leading=12,
                            alignment=TA_CENTER, textColor=HexColor('#666666')))

    # Add title
    story.append(Paragraph(content['title'], styles['CustomTitle']))
    story.append(Spacer(1, 20))

    # Add content items
    for item in content['content']:
        if item.strip():
            # Split long content into lines for better readability
            lines = item.split('\n') if '\n' in item else [item]
            for line in lines:
                if line.strip():
                    story.append(Paragraph(line.strip(), styles['CustomContent']))
                    story.append(Spacer(1, 6))

    story.append(Spacer(1, 40))

    # Add slide footer
    story.append(Paragraph(f"Slide {slide_number} di {total_slides}", styles['SlideInfo']))

    # Build the PDF
    doc.build(story)

    # Get the PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def create_unified_pdf(slide_content: List[Dict], slide_data: Dict) -> bytes:
    """Create a unified PDF with all slides together"""

    # Create a buffer for the PDF
    buffer = io.BytesIO()

    # Create the PDF document with A4 page size
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)

    # Container for the story
    story = []

    # Define styles
    styles = getSampleStyleSheet()

    # Create custom styles
    title_style = ParagraphStyle(
        'MainTitle',
        fontSize=28,
        leading=32,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#1e40af')
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontSize=18,
        leading=22,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=HexColor('#64748b')
    )

    content_style = ParagraphStyle(
        'UnifiedContent',
        fontSize=14,
        leading=18,
        spaceAfter=8,
        alignment=TA_LEFT,
        textColor=HexColor('#1f2937')
    )

    slide_title_style = ParagraphStyle(
        'SlideTitle',
        fontSize=20,
        leading=24,
        spaceAfter=12,
        alignment=TA_LEFT,
        textColor=HexColor('#1e40af')
    )

    # Add main title
    story.append(Paragraph(slide_data["topic"], title_style))
    story.append(Spacer(1, 20))

    # Add metadata
    story.append(Paragraph(f"Generato il: {datetime.now().strftime('%d/%m/%Y')}", subtitle_style))
    story.append(Paragraph(f"Stile: {slide_data.get('style', 'Professional')}", subtitle_style))
    story.append(Paragraph(f"Numero slide: {len(slide_content)}", subtitle_style))
    story.append(Spacer(1, 40))

    # Add all slides content
    for i, slide in enumerate(slide_content):
        # Add slide title
        if slide.get('title'):
            story.append(Paragraph(f"Slide {i+1}: {slide['title']}", slide_title_style))
            story.append(Spacer(1, 12))

        # Add slide content
        for item in slide.get('content', []):
            if item and item.strip():
                # Split long content into lines for better readability
                lines = item.split('\n') if '\n' in item else [item]
                for line in lines:
                    if line.strip():
                        story.append(Paragraph(line.strip(), content_style))
                        story.append(Spacer(1, 6))

        # Add spacing between slides (but not after the last one)
        if i < len(slide_content) - 1:
            story.append(Spacer(1, 30))
            story.append(Paragraph("=" * 50, subtitle_style))
            story.append(Spacer(1, 30))

    # Build the PDF
    doc.build(story)

    # Get the PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
