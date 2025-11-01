from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import json
from datetime import datetime

from services.rag_service import RAGService
from services.llm_service import LLMService
from services.course_service import CourseService
from services.study_tracker import StudyTracker

app = FastAPI(title="AI Tutor Backend", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

# Initialize services
rag_service = RAGService()
llm_service = LLMService()
course_service = CourseService()
study_tracker = StudyTracker()

# Data models
class CourseCreate(BaseModel):
    name: str
    description: str
    subject: str

class ChatMessage(BaseModel):
    message: str
    course_id: str
    session_id: Optional[str] = None

class QuizRequest(BaseModel):
    course_id: str
    topic: Optional[str] = None
    difficulty: Optional[str] = "medium"
    num_questions: Optional[int] = 5

class StudySession(BaseModel):
    course_id: str
    duration_minutes: int
    topics_studied: List[str]

# Routes
@app.get("/")
async def root():
    return {"message": "AI Tutor Backend API"}

@app.post("/courses")
async def create_course(course: CourseCreate):
    try:
        result = course_service.create_course(course.dict())
        return {"success": True, "course": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses")
async def get_courses():
    try:
        courses = course_service.get_all_courses()
        return {"courses": courses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}")
async def get_course(course_id: str):
    try:
        course = course_service.get_course(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"course": course}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/courses/{course_id}/upload")
async def upload_material(course_id: str, file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Save file
        course_dir = f"data/courses/{course_id}"
        os.makedirs(course_dir, exist_ok=True)
        file_path = f"{course_dir}/{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process and index the PDF
        await rag_service.index_pdf(file_path, course_id)

        return {"success": True, "message": "File uploaded and indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(chat_message: ChatMessage):
    try:
        # Retrieve relevant context
        context = await rag_service.retrieve_context(chat_message.message, chat_message.course_id)

        # Generate response
        response = await llm_service.generate_response(
            chat_message.message,
            context,
            chat_message.course_id
        )

        # Track session
        session_id = study_tracker.track_interaction(
            chat_message.course_id,
            chat_message.session_id,
            chat_message.message,
            response
        )

        return {
            "response": response,
            "session_id": session_id,
            "sources": context.get("sources", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quiz")
async def generate_quiz(quiz_request: QuizRequest):
    try:
        quiz = await llm_service.generate_quiz(
            quiz_request.course_id,
            quiz_request.topic,
            quiz_request.difficulty,
            quiz_request.num_questions
        )
        return {"quiz": quiz}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/study-session")
async def record_study_session(session: StudySession):
    try:
        result = study_tracker.record_study_session(session.dict())
        return {"success": True, "session_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-progress/{course_id}")
async def get_study_progress(course_id: str):
    try:
        progress = study_tracker.get_progress(course_id)
        return {"progress": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-insights/{course_id}")
async def get_study_insights(course_id: str):
    try:
        insights = study_tracker.get_study_insights(course_id)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)