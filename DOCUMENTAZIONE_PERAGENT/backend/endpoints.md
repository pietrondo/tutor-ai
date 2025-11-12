# 📡 Backend API Endpoints Reference

**Catalogo completo di tutte le API REST FastAPI del sistema Tutor-AI**

---

## 🚀 Indice Endpoint

### **Core API**
- **[Gestione Corsi](#gestione-corsi)** - CRUD corsi, libri, materiali
- **[Chat & Tutoring](#chat--tutoring)** - Sessioni chat, RAG, context awareness
- **[Document Operations](#document-operations)** - Upload, processing, annotazioni PDF

### **Cognitive Learning Engine (CLE)**
- **[Spaced Repetition](#spaced-repetition)** - Sistema ripetizione spaziata SM-2+
- **[Active Recall](#active-recall)** - Multi-format questions Bloom's taxonomy
- **[Dual Coding](#dual-coding)** - Visual-verbal integration

### **Enhanced Services**
- **[Mindmaps & Visualization](#mindmaps--visualization)** - Mappe concettuali AI
- **[Study Planning](#study-planning)** - Piani studio personalizzati
- **[Slides Generation](#slides-generation)** - Presentazioni automatiche
- **[Search & Discovery](#search--discovery)** - Hybrid semantic search

### **Analytics & Optimization**
- **[A/B Testing Framework](#ab-testing-framework)** - Test statistici multi-strategia
- **[Continuous Improvement](#continuous-improvement)** - ML-based optimization
- **[Learning Analytics](#learning-analytics)** - Progress tracking e metacognition

### **System & Utilities**
- **[Health & Monitoring](#health--monitoring)** - System checks e performance
- **[Configuration](#configuration)** - Gestione configurazione sistema

---

## 🎓 Gestione Corsi

### **Core Course Management**

#### **Get All Courses**
```http
GET /courses
```
**Response**: Lista corsi con metadati completi
```json
{
  "courses": [
    {
      "id": "course_abc123",
      "title": "Corso di Informatica",
      "description": "Introduzione alla programmazione",
      "book_count": 3,
      "total_materials": 15,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-20T14:22:00Z"
    }
  ]
}
```

#### **Create New Course**
```http
POST /courses
Content-Type: application/json

{
  "title": "Nuovo Corso",
  "description": "Descrizione del corso",
  "category": "computer_science"
}
```

#### **Get Course Details**
```http
GET /courses/{course_id}
```
**Response**: Dettagli corso con libri e materials
```json
{
  "id": "course_abc123",
  "title": "Corso di Informatica",
  "books": [
    {
      "id": "book_def456",
      "title": "Algoritmi e Strutture Dati",
      "pdf_count": 8,
      "materials": [
        {
          "filename": "capitolo1.pdf",
          "title": "Introduzione agli Algoritmi",
          "read_url": "/courses/course_abc123/materials/capitolo1.pdf",
          "download_url": "/api/materials/download/course_abc123/capitolo1.pdf"
        }
      ]
    }
  ]
}
```

#### **Update Course**
```http
PUT /courses/{course_id}
Content-Type: application/json

{
  "title": "Titolo Aggiornato",
  "description": "Descrizione aggiornata"
}
```

#### **Delete Course**
```http
DELETE /courses/{course_id}
```

### **Book Management**

#### **Upload PDF Document**
```http
POST /courses/{course_id}/upload
Content-Type: multipart/form-data

files: [File1.pdf, File2.pdf]
```

#### **Get Course Books**
```http
GET /courses/{course_id}/books
```

#### **Get Book Details**
```http
GET /courses/{course_id}/books/{book_id}
```

#### **Update Book Metadata**
```http
PUT /courses/{course_id}/books/{book_id}
Content-Type: application/json

{
  "title": "Titolo Libro Aggiornato",
  "description": "Descrizione aggiornata",
  "tags": ["algoritmi", "strutture dati"]
}
```

#### **Delete Book**
```http
DELETE /courses/{course_id}/books/{book_id}
```

### **Materials Access**

#### **Get All Course Materials**
```http
GET /courses/{course_id}/materials
```
**Response**: Tutti i materiali con URL diretti
```json
{
  "materials": [
    {
      "filename": "capitolo1.pdf",
      "title": "Introduzione agli Algoritmi",
      "book_id": "book_def456",
      "book_title": "Algoritmi e Strutture Dati",
      "read_url": "/courses/course_abc123/materials/capitolo1.pdf?book=book_def456",
      "download_url": "/api/materials/download/course_abc123/capitolo1.pdf"
    }
  ]
}
```

#### **Get Book-Specific Materials**
```http
GET /courses/{course_id}/books/{book_id}/materials
```

#### **Direct Material Access**
```http
GET /courses/{course_id}/materials/{filename}?book={book_id}
```
**Headers**: `Content-Type: application/pdf` streaming

---

## 💬 Chat & Tutoring

### **Enhanced Course Chat**

#### **Create Chat Session**
```http
POST /course-chat
Content-Type: application/json

{
  "course_id": "course_abc123",
  "book_id": "book_def456",
  "user_id": "user_789",
  "difficulty": "intermediate",
  "learning_style": "visual",
  "language": "it",
  "session_id": "session_xyz"
}
```
**Response**: Chat con RAG context e metadata
```json
{
  "response": "La risposta dell'AI tutor...",
  "sources": [
    {
      "type": "book_chunk",
      "content": "...testo dal libro...",
      "book_title": "Algoritmi e Strutture Dati",
      "page": 15
    }
  ],
  "session_id": "session_xyz",
  "context": {
    "course_name": "Corso di Informatica",
    "book_title": "Algoritmi e Strutture Dati",
    "materials_used": 3,
    "retrieval_strategy": "hybrid_rag"
  },
  "suggestions": [
    "Vorresti un esempio pratico di algoritmo?",
    "Possiamo approfondire la complessità temporale?"
  ]
}
```

#### **Continue Chat Session**
```http
POST /course-chat
Content-Type: application/json

{
  "message": "Puoi spiegarmi meglio la ricorsione?",
  "course_id": "course_abc123",
  "book_id": "book_def456",
  "session_id": "session_xyz",
  "context_history": [...]
}
```

### **Legacy Chat (RAG Enhanced)**

#### **Basic RAG Chat**
```http
POST /chat
Content-Type: application/json

{
  "message": "Spiegami gli algoritmi di ordinamento",
  "course_id": "course_abc123",
  "book_id": "book_def456"
}
```

### **Mindmap Generation**

#### **Generate Concept Map**
```http
POST /mindmap
Content-Type: application/json

{
  "topic": "Strutture Dati",
  "course_id": "course_abc123",
  "book_id": "book_def456",
  "depth": 3,
  "focus_areas": ["algoritmi", "performance"]
}
```
**Response**: Mappa concettuale strutturata
```json
{
  "topic": "Strutture Dati",
  "concepts": [
    {
      "id": "arrays",
      "title": "Array",
      "level": 1,
      "description": "Struttura dati sequenziale",
      "connections": ["linked_lists", "sorting_algorithms"]
    }
  ],
  "relationships": [
    {
      "from": "arrays",
      "to": "linked_lists",
      "type": "alternative"
    }
  ]
}
```

---

## 📄 Document Operations

### **PDF Processing**

#### **Upload Materials**
```http
POST /api/materials/upload
Content-Type: multipart/form-data

course_id: course_abc123
book_id: book_def456
files: [file1.pdf, file2.pdf]
```

#### **Download Material**
```http
GET /api/materials/download/{course_id}/{filename}
```
**Headers**: `Content-Disposition: attachment; filename="filename.pdf"`

### **Annotation System**

#### **Create Annotation**
```http
POST /annotations
Content-Type: application/json

{
  "course_id": "course_abc123",
  "book_id": "book_def456",
  "pdf_filename": "capitolo1.pdf",
  "page": 15,
  "selection": {
    "start": { "x": 100, "y": 200 },
    "end": { "x": 300, "y": 220 }
  },
  "text": "Testo selezionato",
  "note": "Nota personale importante",
  "type": "highlight",
  "color": "#ffeb3b",
  "share_with_ai": true,
  "tags": ["importante", "esame"]
}
```

#### **Get Annotations**
```http
GET /annotations?course_id={course_id}&book_id={book_id}&pdf={filename}
```

#### **Update Annotation**
```http
PUT /annotations/{annotation_id}
Content-Type: application/json

{
  "note": "Nota aggiornata",
  "share_with_ai": false
}
```

#### **Delete Annotation**
```http
DELETE /annotations/{annotation_id}
```

#### **Export/Import Annotations**
```http
GET /annotations/export?course_id={course_id}&format=json
POST /annotations/import?course_id={course_id}
Content-Type: application/json

{
  "annotations": [...]
}
```

---

## 🧠 Cognitive Learning Engine (CLE)

### **Spaced Repetition System**

#### **Create Learning Card**
```http
POST /api/spaced-repetition/card
Content-Type: application/json

{
  "course_id": "course_abc123",
  "question": "Cos'è la notazione Big O?",
  "answer": "La notazione Big O descrive la complessità computazionale...",
  "difficulty": 2.5,
  "tags": ["algoritmi", "complessità"],
  "source_material": {
    "book_id": "book_def456",
    "page": 42
  }
}
```

#### **Get Due Cards for Review**
```http
GET /api/spaced-repetition/cards/due/{course_id}
```
**Response**: Card pronte per ripasso
```json
{
  "due_cards": [
    {
      "id": "card_789",
      "question": "Cos'è la notazione Big O?",
      "difficulty": 2.5,
      "interval_days": 7,
      "repetitions": 3,
      "next_review": "2024-01-22T10:30:00Z"
    }
  ]
}
```

#### **Update Card Performance**
```http
PUT /api/spaced-repetition/card/{card_id}/review
Content-Type: application/json

{
  "rating": 4,  // 0-5 SM-2 algorithm
  "review_time_seconds": 45,
  "course_id": "course_abc123"
}
```

### **Active Recall Engine**

#### **Generate Questions**
```http
POST /api/active-recall/generate-questions
Content-Type: application/json

{
  "topic": "Algoritmi di ordinamento",
  "course_id": "course_abc123",
  "difficulty": "intermediate",
  "question_types": ["multiple_choice", "short_answer", "coding"],
  "count": 10,
  "bloom_taxonomy_level": "apply"
}
```
**Response**: Domande multi-formato
```json
{
  "questions": [
    {
      "id": "q_001",
      "type": "multiple_choice",
      "question": "Quale algoritmo ha complessità O(n log n) nel caso peggiore?",
      "options": [
        "Bubble Sort",
        "Quick Sort",
        "Insertion Sort",
        "Selection Sort"
      ],
      "correct_answer": 1,
      "explanation": "Quick Sort ha complessità O(n log n) nel caso medio e peggiore con pivot ottimizzato."
    }
  ]
}
```

#### **Submit Answer**
```http
POST /api/active-recall/submit-answer
Content-Type: application/json

{
  "question_id": "q_001",
  "answer": "Quick Sort",
  "course_id": "course_abc123",
  "time_taken_seconds": 30
}
```

### **Dual Coding Service**

#### **Create Visual-Verbal Content**
```http
POST /api/dual-coding/create
Content-Type: application/json

{
  "concept": "Binary Search Tree",
  "course_id": "course_abc123",
  "element_types": ["diagram", "explanation", "example"],
  "learning_style": "visual"
}
```
**Response**: Contenuto visivo-verbale integrato
```json
{
  "concept": "Binary Search Tree",
  "elements": [
    {
      "type": "diagram",
      "content": "diagramma del BST...",
      "description": "Visualizzazione struttura albero binario"
    },
    {
      "type": "explanation",
      "content": "Un BST è un albero binario dove ogni nodo...",
      "description": "Spiegazione testuale dettagliata"
    }
  ],
  "integration_notes": "Il diagramma mostra come i valori sono organizzati..."
}
```

---

## 🎨 Enhanced Services

### **Mindmaps & Visualization**

#### **AI-Generated Mindmap**
```http
POST /api/mindmap/generate
Content-Type: application/json

{
  "topic": "Machine Learning Fundamentals",
  "course_id": "course_abc123",
  "complexity": "intermediate",
  "expand_depth": 4,
  "focus_concepts": ["supervised", "unsupervised", "neural_networks"]
}
```

#### **Get Existing Mindmap**
```http
GET /api/mindmap/{mindmap_id}
```

#### **Export Mindmap**
```http
GET /api/mindmap/{mindmap_id}/export?format=json|svg|png
```

### **Study Planning**

#### **Generate Personalized Plan**
```http
POST /api/study-plan/generate
Content-Type: application/json

{
  "course_id": "course_abc123",
  "study_duration_weeks": 8,
  "daily_hours": 2,
  "learning_objectives": [
    "Understand basic algorithms",
    "Master sorting techniques",
    "Learn data structures"
  ],
  "current_knowledge_level": "beginner",
  "preferred_study_times": ["morning", "evening"]
}
```
**Response**: Piano studio personalizzato
```json
{
  "plan_id": "plan_xyz",
  "weeks": [
    {
      "week": 1,
      "title": "Introduction to Algorithms",
      "daily_sessions": [
        {
          "day": 1,
          "duration_minutes": 90,
          "topics": ["Algorithm definition", "Complexity analysis"],
          "materials": ["capitolo1.pdf", "video_introduction"],
          "exercises": ["complexity_exercises.pdf"]
        }
      ]
    }
  ],
  "milestones": [
    {
      "week": 4,
      "title": "Mid-course Assessment",
      "description": "Complete understanding of basic algorithms"
    }
  ]
}
```

#### **Update Study Progress**
```http
POST /api/study-plan/{plan_id}/progress
Content-Type: application/json

{
  "session_id": "session_abc",
  "completion_percentage": 85,
  "topics_completed": ["Algorithm definition", "Complexity analysis"],
  "difficulty_rating": 3,
  "notes": "Struggled with mathematical notation"
}
```

### **Slides Generation**

#### **Generate Presentation**
```http
POST /api/slides/generate
Content-Type: application/json

{
  "topic": "Introduction to Data Structures",
  "course_id": "course_abc123",
  "slide_count": 15,
  "include_visuals": true,
  "target_audience": "beginner",
  "key_points": [
    "Definition of data structures",
    "Types of data structures",
    "Real-world applications"
  ]
}
```
**Response**: Slides generati AI
```json
{
  "presentation_id": "slides_123",
  "slides": [
    {
      "slide_number": 1,
      "title": "Introduction to Data Structures",
      "content": {
        "main_points": ["Definition", "Importance", "Applications"],
        "visual_elements": ["data_structure_diagram.svg"],
        "speaker_notes": "Start with definition and real-world examples"
      }
    }
  ],
  "export_options": ["pptx", "pdf", "html"]
}
```

---

## 🔍 Search & Discovery

### **Advanced Search**

#### **Hybrid Semantic Search**
```http
POST /api/search
Content-Type: application/json

{
  "query": "binary search algorithm complexity",
  "course_id": "course_abc123",
  "search_type": "hybrid",
  "filters": {
    "book_id": "book_def456",
    "content_types": ["explanation", "example", "code"],
    "difficulty": ["beginner", "intermediate"]
  },
  "max_results": 20,
  "include_snippets": true
}
```
**Response**: Risultati search con metadata
```json
{
  "results": [
    {
      "content": "Binary search has O(log n) time complexity...",
      "source": {
        "book_title": "Algoritmi e Strutture Dati",
        "page": 67,
        "chapter": "Binary Search",
        "pdf_filename": "capitolo4.pdf"
      },
      "relevance_score": 0.95,
      "content_type": "explanation",
      "snippet": "Binary search achieves O(log n) complexity by..."
    }
  ],
  "total_results": 15,
  "search_time_ms": 125
}
```

#### **Course-Specific Search**
```http
GET /api/search/courses/{course_id}?q={query}&type={semantic|keyword}
```

#### **Material Recommendations**
```http
GET /api/recommendations/{course_id}?topic={topic}&count={count}
```

---

## 📊 Analytics & Optimization

### **A/B Testing Framework**

#### **Create A/B Test**
```http
POST /api/ab-testing/create
Content-Type: application/json

{
  "test_name": "teaching_strategy_comparison",
  "hypothesis": "Visual explanations improve concept retention",
  "variants": [
    {
      "name": "control",
      "strategy": "text_explanation",
      "weight": 0.5
    },
    {
      "name": "treatment",
      "strategy": "visual_explanation",
      "weight": 0.5
    }
  ],
  "success_metric": "retention_score",
  "sample_size": 100,
  "course_id": "course_abc123"
}
```

#### **Get Test Results**
```http
GET /api/ab-testing/results/{test_id}
```
**Response**: Risultati statistici
```json
{
  "test_id": "test_abc",
  "status": "completed",
  "results": {
    "control": {
      "conversions": 45,
      "conversion_rate": 0.45,
      "confidence_interval": [0.35, 0.55]
    },
    "treatment": {
      "conversions": 62,
      "conversion_rate": 0.62,
      "confidence_interval": [0.52, 0.72]
    }
  },
  "statistical_significance": {
    "p_value": 0.023,
    "is_significant": true,
    "confidence_level": 0.95
  }
}
```

### **Continuous Improvement System**

#### **Record Learning Interaction**
```http
POST /api/continuous-improvement/interaction
Content-Type: application/json

{
  "user_id": "user_789",
  "course_id": "course_abc123",
  "interaction_type": "chat_query",
  "content": "Explain binary search",
  "response_quality": 4,
  "time_to_response": 1250,
  "follow_up_actions": ["asked_clarification", "requested_example"],
  "llm_provider": "openai",
  "model": "gpt-4"
}
```

#### **Get Optimization Insights**
```http
GET /api/continuous-improvement/insights/{course_id}
```
**Response**: Pattern e ottimizzazioni
```json
{
  "course_id": "course_abc123",
  "period": "last_30_days",
  "insights": [
    {
      "pattern": "Users struggle with recursion",
      "frequency": 0.73,
      "recommendation": "Add visual examples for recursion",
      "impact_score": 8.5
    }
  ],
  "llm_performance": {
    "openai_gpt4": {
      "avg_response_time": 1.2,
      "user_satisfaction": 4.3
    },
    "zai_llama": {
      "avg_response_time": 2.1,
      "user_satisfaction": 3.9
    }
  }
}
```

### **Learning Analytics**

#### **Get Learning Progress**
```http
GET /api/learning-analytics/progress/{course_id}?user_id={user_id}
```
**Response**: Progress dettagliato
```json
{
  "course_id": "course_abc123",
  "user_id": "user_789",
  "overall_progress": 0.68,
  "topic_mastery": {
    "algorithms": 0.85,
    "data_structures": 0.72,
    "complexity": 0.45
  },
  "learning_metrics": {
    "study_time_total_hours": 24.5,
    "questions_answered": 127,
    "average_response_time": 45,
    "improvement_rate": 0.23
  },
  "metacognitive_indicators": {
    "self_assessment_accuracy": 0.78,
    "study_strategy_effectiveness": 0.65,
    "challenge-seeking": 0.71
  }
}
```

#### **Get Metacognitive Profile**
```http
GET /api/learning-analytics/metacognitive/{user_id}
```

---

## 🏥 Health & Monitoring

### **System Health**

#### **Health Check**
```http
GET /health
```
**Response**: System status
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "vector_db": "healthy",
    "llm_providers": {
      "openai": "healthy",
      "zai": "healthy"
    }
  },
  "performance": {
    "avg_response_time_ms": 150,
    "memory_usage": "2.1GB",
    "cpu_usage": "15%"
  }
}
```

#### **Service Status**
```http
GET /api/system/status
```

#### **Performance Metrics**
```http
GET /api/system/metrics?period=1h|24h|7d
```

### **Configuration Management**

#### **Get System Configuration**
```http
GET /api/system/config
```

#### **Update Configuration**
```http
PUT /api/system/config
Content-Type: application/json

{
  "llm_provider": "openai",
  "max_tokens": 4000,
  "temperature": 0.7
}
```

---

## 🔐 Rate Limiting & Security

### **Rate Limits**
- **Chat endpoints**: 100 richieste/ora per user
- **Upload endpoints**: 20 files/ora, max 50MB total
- **Search endpoints**: 200 query/ora
- **Analytics endpoints**: 1000 richieste/ora

### **Security Headers**
Tutte le risposte includono:
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: "1; mode=block"
Strict-Transport-Security: max-age=31536000
```

### **CORS Configuration**
```http
Access-Control-Allow-Origin: http://localhost:3001
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

---

## 📝 Error Responses

### **Standard Error Format**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "course_id",
      "issue": "Course not found"
    },
    "timestamp": "2024-01-15T10:30:45Z",
    "request_id": "req_abc123"
  }
}
```

### **Common Error Codes**
- `VALIDATION_ERROR` - Parametri non validi
- `NOT_FOUND` - Risorsa non trovata
- `UNAUTHORIZED` - Autenticazione richiesta
- `RATE_LIMIT_EXCEEDED` - Limite richieste superato
- `SERVICE_UNAVAILABLE` - Servizio temporaneamente non disponibile
- `FILE_TOO_LARGE` - File supera dimensioni massime
- `UNSUPPORTED_FORMAT` - Formato non supportato

---

## 🚀 Performance Optimization

### **Caching Strategy**
- **RAG responses**: 1 ora cache basata su course_id + query
- **Course materials**: 24 ore cache metadata
- **User progress**: 15 minuti cache analytics
- **System configuration**: 1 ora cache settings

### **Response Time Targets**
- **Chat requests**: < 2 secondi
- **Search queries**: < 500 ms
- **Material upload**: < 30 secondi (100MB file)
- **Analytics queries**: < 1 secondo

### **Pagination**
Tutti gli endpoint che ritornano liste supportano:
```http
GET /courses?page=1&size=20&sort=created_at&order=desc
```

---

*Ultimo aggiornamento: Novembre 2025*
*Versione API: v2.0*
*Compatibile con Tutor-AI v2.0+*
