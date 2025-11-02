from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import json
from datetime import datetime, timedelta

from services.rag_service import RAGService
from services.llm_service import LLMService
from services.course_service import CourseService
from services.book_service import BookService
from services.study_tracker import StudyTracker
from services.study_planner_service import StudyPlannerService

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
book_service = BookService()
study_tracker = StudyTracker()
study_planner = StudyPlannerService()

# Data models
class CourseCreate(BaseModel):
    name: str
    description: str
    subject: str

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None

class BookCreate(BaseModel):
    title: str
    author: Optional[str] = ""
    isbn: Optional[str] = ""
    description: Optional[str] = ""
    year: Optional[str] = ""
    publisher: Optional[str] = ""
    chapters: Optional[List[str]] = []
    tags: Optional[List[str]] = []

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    year: Optional[str] = None
    publisher: Optional[str] = None
    chapters: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class ChatMessage(BaseModel):
    message: str
    course_id: str
    book_id: Optional[str] = None
    session_id: Optional[str] = None

class QuizRequest(BaseModel):
    course_id: str
    topic: Optional[str] = None
    difficulty: Optional[str] = "medium"

class StudyPlanCreate(BaseModel):
    course_id: str
    title: Optional[str] = "Piano di Studio Personalizzato"
    sessions_per_week: Optional[int] = 3
    session_duration: Optional[int] = 45
    difficulty_level: Optional[str] = "intermediate"
    difficulty_progression: Optional[str] = "graduale"

class SessionProgressUpdate(BaseModel):
    completed: bool

class BudgetModeRequest(BaseModel):
    enabled: bool

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

@app.put("/courses/{course_id}")
async def update_course(course_id: str, course_update: CourseUpdate):
    try:
        update_data = {k: v for k, v in course_update.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        course = course_service.update_course(course_id, update_data)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"success": True, "course": course}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/courses/{course_id}")
async def delete_course(course_id: str):
    try:
        success = course_service.delete_course(course_id)
        if not success:
            raise HTTPException(status_code=404, detail="Course not found")

        # Also delete RAG documents for this course
        rag_service.delete_course_documents(course_id)

        return {"success": True}
    except HTTPException:
        raise
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

# Book endpoints
@app.post("/courses/{course_id}/books")
async def create_book(course_id: str, book: BookCreate):
    try:
        result = book_service.create_book(course_id, book.dict())
        return {"success": True, "book": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}/books")
async def get_books(course_id: str):
    try:
        books = book_service.get_books_by_course(course_id)
        return {"books": books}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}/books/{book_id}")
async def get_book(course_id: str, book_id: str):
    try:
        book = book_service.get_book(course_id, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"book": book}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/courses/{course_id}/books/{book_id}")
async def update_book(course_id: str, book_id: str, book_update: BookUpdate):
    try:
        update_data = {k: v for k, v in book_update.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        book = book_service.update_book(course_id, book_id, update_data)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"success": True, "book": book}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/courses/{course_id}/books/{book_id}")
async def delete_book(course_id: str, book_id: str):
    try:
        success = book_service.delete_book(course_id, book_id)
        if not success:
            raise HTTPException(status_code=404, detail="Book not found")

        # Also delete RAG documents for this book
        rag_service.delete_book_documents(course_id, book_id)

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/courses/{course_id}/books/{book_id}/upload")
async def upload_book_material(course_id: str, book_id: str, file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Save file
        book_dir = f"data/courses/{course_id}/books/{book_id}"
        os.makedirs(book_dir, exist_ok=True)
        file_path = f"{book_dir}/{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process and index the PDF for the book
        await rag_service.index_pdf(file_path, course_id, book_id)

        return {"success": True, "message": "File uploaded and indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(chat_message: ChatMessage):
    try:
        # Retrieve relevant context (with optional book filter)
        context = await rag_service.retrieve_context(
            chat_message.message,
            chat_message.course_id,
            chat_message.book_id
        )

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

# Rimosso temporaneamente endpoint session perché StudySession non è definito
# @app.post("/study-session")
# async def record_study_session(session: StudySession):
#     try:
#         result = study_tracker.record_study_session(session.dict())
#         return {"success": True, "session_id": result}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-progress/{course_id}")
async def get_study_progress(course_id: str):
    try:
        progress = study_tracker.get_progress(course_id)
        return {"progress": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-progress/overview")
async def get_overall_progress():
    """Get overall progress across all courses"""
    try:
        courses = course_service.get_all_courses()
        overall_stats = {
            "total_study_time": 0,
            "total_sessions": 0,
            "courses_with_progress": 0,
            "total_concepts_learned": 0,
            "weekly_progress": [],
            "course_progress": []
        }

        # Calculate weekly progress (last 7 days)
        weekly_data = []
        for i in range(7):
            day = datetime.now() - timedelta(days=i)
            weekly_data.append({
                "day": day.strftime("%a")[:3],  # Lun, Mar, etc.
                "date": day.strftime("%Y-%m-%d"),
                "minutes": 0,
                "sessions": 0
            })
        weekly_data.reverse()  # Start from Monday

        for course in courses:
            course_id = course["id"]
            progress = study_tracker.get_progress(course_id)

            if progress.get("total_sessions", 0) > 0:
                overall_stats["courses_with_progress"] += 1
                overall_stats["total_study_time"] += progress.get("total_study_time", 0)
                overall_stats["total_sessions"] += progress.get("total_sessions", 0)
                overall_stats["total_concepts_learned"] += len(progress.get("topics_covered", []))

                overall_stats["course_progress"].append({
                    "course_id": course_id,
                    "course_name": course["name"],
                    "sessions": progress.get("total_sessions", 0),
                    "study_time": progress.get("total_study_time", 0),
                    "concepts": len(progress.get("topics_covered", []))
                })

        # Generate weekly breakdown (mock data for now since we don't have daily tracking)
        if overall_stats["total_sessions"] > 0:
            # Distribute sessions and time across the week
            for day_data in weekly_data:
                if overall_stats["total_sessions"] > 0:
                    day_data["sessions"] = max(0, overall_stats["total_sessions"] // 7 - 1 + (hash(day_data["date"]) % 3))
                    day_data["minutes"] = max(0, overall_stats["total_study_time"] // 7 - 10 + (hash(day_data["date"]) % 30))

        overall_stats["weekly_progress"] = weekly_data

        return overall_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-insights/{course_id}")
async def get_study_insights(course_id: str):
    try:
        insights = study_tracker.get_study_insights(course_id)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Model management endpoints
@app.get("/models")
async def get_available_models():
    """Get available models and their characteristics"""
    try:
        return await llm_service.get_available_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{model_name}")
async def set_model(model_name: str):
    """Set the active model"""
    try:
        success = await llm_service.set_model(model_name)
        if success:
            return {"success": True, "model": model_name}
        else:
            raise HTTPException(status_code=400, detail=f"Model {model_name} not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/budget-mode")
async def set_budget_mode(request: BudgetModeRequest):
    """Enable/disable budget mode"""
    try:
        llm_service.set_budget_mode(request.enabled)
        return {"success": True, "budget_mode": request.enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/local/test")
async def test_local_connection():
    """Test connection with local LLM provider"""
    try:
        return await llm_service.test_local_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/status")
async def get_rag_status():
    """Get RAG system status and statistics"""
    try:
        stats = rag_service.get_collection_stats()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "vector_db": {
                "collection_name": stats.get("collection_name", "course_materials"),
                "total_documents": stats.get("total_documents", 0),
                "embedding_model": rag_service.model_name,
                "model_loaded": rag_service.embedding_model is not None
            },
            "system_info": {
                "data_directory": "data/vector_db",
                "supported_formats": ["PDF"],
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "similarity_metric": "cosine"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/documents")
async def get_all_documents():
    """Get all indexed documents"""
    try:
        courses = course_service.get_all_courses()
        all_documents = []

        for course in courses:
            course_id = course["id"]
            course_docs = await rag_service.search_documents(course_id)
            if course_docs.get("documents"):
                for doc in course_docs["documents"]:
                    doc["course_name"] = course["name"]
                    doc["course_id"] = course_id
                all_documents.extend(course_docs["documents"])

        return {
            "documents": all_documents,
            "total_count": len(all_documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/analytics")
async def get_rag_analytics():
    """Get RAG system analytics"""
    try:
        courses = course_service.get_all_courses()
        total_documents = 0
        course_stats = []

        for course in courses:
            course_id = course["id"]
            course_docs = await rag_service.search_documents(course_id)
            doc_count = len(course_docs.get("documents", []))
            total_documents += doc_count

            course_stats.append({
                "course_id": course_id,
                "course_name": course["name"],
                "document_count": doc_count,
                "subject": course["subject"]
            })

        return {
            "analytics": {
                "total_documents": total_documents,
                "total_courses": len(courses),
                "courses_with_documents": len([c for c in course_stats if c["document_count"] > 0]),
                "course_stats": course_stats
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/documents/{course_id}")
async def get_course_documents(course_id: str, search_query: Optional[str] = None):
    """Get all indexed documents for a course"""
    try:
        result = await rag_service.search_documents(course_id, search_query)
        return {
            "documents": result.get("documents", []),
            "course_id": course_id,
            "total_count": len(result.get("documents", [])),
            "total_sources": result.get("total_sources", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Study Planner endpoints
@app.post("/study-plans")
async def create_study_plan(request: StudyPlanCreate):
    """Create a new study plan based on course materials"""
    try:
        plan = await study_planner.generate_study_plan(
            request.course_id,
            request.dict(exclude_unset=True)
        )
        return {"success": True, "plan": plan.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-plans/{plan_id}")
async def get_study_plan(plan_id: str):
    """Get a specific study plan"""
    try:
        plan = await study_planner.get_study_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Study plan not found")
        return {"success": True, "plan": plan.dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}/study-plans")
async def get_course_study_plans(course_id: str):
    """Get all study plans for a course"""
    try:
        plans = await study_planner.get_course_study_plans(course_id)
        return {"success": True, "plans": [plan.dict() for plan in plans]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/study-plans/{plan_id}/sessions/{session_id}")
async def update_session_progress(plan_id: str, session_id: str, request: SessionProgressUpdate):
    """Update session completion status"""
    try:
        success = await study_planner.update_session_progress(plan_id, session_id, request.completed)
        if not success:
            raise HTTPException(status_code=404, detail="Plan or session not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/study-plans/{plan_id}/regenerate")
async def regenerate_study_plan(plan_id: str, request: StudyPlanCreate):
    """Regenerate an existing study plan with new preferences"""
    try:
        new_plan = await study_planner.regenerate_plan(plan_id, request.dict(exclude_unset=True))
        return {"success": True, "plan": new_plan.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/study-plans/{plan_id}")
async def delete_study_plan(plan_id: str):
    """Delete a study plan"""
    try:
        success = await study_planner.delete_study_plan(plan_id)
        if not success:
            raise HTTPException(status_code=404, detail="Study plan not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)