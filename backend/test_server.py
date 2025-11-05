#!/usr/bin/env python3
"""
Minimal FastAPI server to test PDF generation endpoints
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import base64
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pdf_generator import PDFGenerator

app = FastAPI(title="PDF Generation Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ZAISlideGenerationRequest(BaseModel):
    course_id: str
    topic: str
    num_slides: int = 10
    slide_style: str = "modern"
    audience: str = "university"

def get_pdf_generator():
    return PDFGenerator()

@app.get("/")
async def root():
    return {"message": "PDF Generation Test Server"}

@app.post("/generate-slides/zai-pdf")
async def generate_pdf_with_zai_agent(
    request: ZAISlideGenerationRequest,
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    Test endpoint for PDF generation using mock ZAI data
    """
    try:
        print(f"PDF generation request: {request}")

        # Mock slides data for testing
        slides_data = {
            "title": f"Presentazione: {request.topic}",
            "slides": [
                {
                    "title": f"Sezione {i+1}: {request.topic}",
                    "content": [
                        f"Punto 1 della sezione {i+1}",
                        f"Punto 2 della sezione {i+1}",
                        f"Punto 3 della sezione {i+1}",
                        f"Punto 4 della sezione {i+1}"
                    ]
                }
                for i in range(min(request.num_slides, 5))
            ]
        }

        # Generate PDF
        pdf_bytes = pdf_generator.generate_pdf_from_slides(slides_data)

        # Create a response with the PDF file
        pdf_base64 = base64.b64encode(pdf_bytes).decode()

        return {
            "success": True,
            "pdf_data": pdf_base64,
            "filename": f"{slides_data.get('title', 'presentazione').replace(' ', '_')}.pdf",
            "slides_preview": slides_data,
            "message": "PDF generato con successo con ZAI"
        }

    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")

if __name__ == "__main__":
    import uvicorn
    print("Starting test server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)