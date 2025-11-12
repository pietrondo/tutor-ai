# ⚙️ Backend Services Reference

**Documentazione dettagliata dei 40+ servizi specializzati FastAPI del sistema Tutor-AI**

---

## 🚀 Indice Servizi

### **Core Services**
- **[LLM Service](#llm-service)** - Multi-provider AI integration
- **[RAG Service](#rag-service)** - Retrieval-Augmented Generation con ChromaDB
- **[Course Service](#course-service)** - Gestione corsi, libri, materiali
- **[Annotation Service](#annotation-service)** - Sistema annotazioni PDF

### **Cognitive Learning Engine (CLE)**
- **[Spaced Repetition Service](#spaced-repetition-service)** - Enhanced SM-2 algorithm
- **[Active Recall Service](#active-recall-service)** - Multi-format question generation
- **[Dual Coding Service](#dual-coding-service)** - Visual-verbal integration

### **Enhanced AI Services**
- **[Mindmap Service](#mindmap-service)** - AI-generated concept maps
- **[Study Plan Service](#study-plan-service)** - Personalized learning paths
- **[Slide Generation Service](#slide-generation-service)** - AI presentation creation
- **[Search Service](#search-service)** - Hybrid semantic search

### **Analytics & Optimization**
- **[A/B Testing Service](#ab-testing-service)** - Statistical testing framework
- **[Continuous Improvement Service](#continuous-improvement-service)** - ML-based optimization
- **[Learning Analytics Service](#learning-analytics-service)** - Progress tracking
- **[Performance Analytics Service](#performance-analytics-service)** - System monitoring

### **Utility Services**
- **[File Processing Service](#file-processing-service)** - PDF/Document handling
- **[Vector DB Service](#vector-db-service)** - ChromaDB integration
- **[Cache Service](#cache-service)** - Redis caching layer
- **[Logging Service](#logging-service)** - Structured logging system

---

## 🤖 LLM Service

### **Overview**
Servizio centralizzato per l'integrazione con multi-provider di Large Language Models. Supporta OpenAI, Z.AI, OpenRouter, e modelli locali (Ollama/LM Studio).

### **Features Principali**
- **Multi-Provider Support**: Switch dinamico tra provider
- **Automatic Fallback**: Failover automatico tra provider
- **Token Management**: Monitoraggio e ottimizzazione token usage
- **Performance Monitoring**: Tracking tempi risposta e qualità
- **Context Management**: Gestione contesto conversazionale
- **Streaming Support**: Risposte streaming per用户体验

### **Metodi Chiave**

#### **Model Selection**
```python
class ModelSelector:
    def select_optimal_model(
        self,
        task_type: str,  # "chat", "generation", "analysis"
        complexity: str,  # "simple", "intermediate", "complex"
        latency_requirement: str,  # "realtime", "standard", "batch"
        context_size: int
    ) -> str:
        """Selezione intelligente del modello ottimale"""

    def get_provider_config(self, provider: str) -> Dict:
        """Configurazione provider specifica"""
```

#### **Response Generation**
```python
async def generate_response(
    self,
    prompt: str,
    context: Optional[List[Dict]] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    stream: bool = False
) -> Union[str, AsyncIterator[str]]:
    """Genera risposta con fallback automatico"""
```

#### **Performance Monitoring**
```python
class LLMPerformanceTracker:
    def track_request(self, provider: str, model: str, metrics: Dict):
        """Tracciamento performance richiesta"""

    def get_provider_stats(self, provider: str) -> Dict:
        """Statistiche performance provider"""

    def optimize_routing(self) -> Dict:
        """Ottimizzazione routing basata su performance"""
```

### **Configurazione**
```python
# Provider configuration
LLM_PROVIDERS = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "models": ["gpt-4", "gpt-3.5-turbo"],
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
        "max_retries": 3
    },
    "zai": {
        "api_key": os.getenv("ZAI_API_KEY"),
        "models": ["glm-4.6", "glm-3.5"],
        "base_url": "https://api.z.ai/v1",
        "timeout": 45,
        "max_retries": 2
    },
    "local": {
        "api_key": "local-key",
        "models": ["llama3.1", "qwen2.5"],
        "base_url": "http://localhost:11434/v1",
        "timeout": 60,
        "max_retries": 1
    }
}
```

### **Uso Tipico**
```python
from backend.services.llm_service import LLMService

llm_service = LLMService()

# Chat con contesto
response = await llm_service.generate_response(
    prompt="Explain binary search algorithms",
    context=[
        {"role": "user", "content": "I'm studying data structures"},
        {"role": "assistant", "content": "Binary search is a fundamental algorithm..."}
    ],
    temperature=0.3,
    max_tokens=1500
)

# Streaming
async for chunk in llm_service.generate_response_stream(
    prompt="Generate examples of sorting algorithms",
    stream=True
):
    print(chunk, end="")
```

---

## 🔍 RAG Service

### **Overview**
Servizio Retrieval-Augmented Generation per contestualizzare le risposte AI con materiali didattici specifici del corso.

### **Features Principali**
- **Hybrid Search**: Combina keyword e semantic search
- **Context Filtering**: Filtraggio per corso, libro, capitolo
- **Chunking Strategy**: Ottimizzazione dimensioni chunk per PDF
- **Source Attribution**: Citazione automatica fonti
- **Relevance Scoring**: Scoring rilevanza contenuto
- **Cache Layer**: Cache risultati ricerca

### **Metodi Chiave**

#### **Context Retrieval**
```python
class RAGService:
    async def retrieve_context(
        self,
        query: str,
        course_id: str,
        book_id: Optional[str] = None,
        max_chunks: int = 5,
        min_relevance: float = 0.7,
        search_type: str = "hybrid"  # "keyword", "semantic", "hybrid"
    ) -> List[Dict]:
        """Recupera contesto rilevante dai materiali"""

    async def hybrid_search(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict]:
        """Ricerca ibrida keyword + semantica"""
```

#### **Chunk Processing**
```python
class DocumentChunker:
    def create_chunks(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
        strategy: str = "sliding_window"  # "sentence", "paragraph", "sliding_window"
    ) -> List[Dict]:
        """Crea chunk ottimizzati per PDF"""

    def extract_metadata(self, chunk: Dict, source: Dict) -> Dict:
        """Estrae metadata dal chunk"""
```

#### **Vector Database Integration**
```python
class VectorDBManager:
    async def index_document(
        self,
        course_id: str,
        book_id: str,
        chunks: List[Dict]
    ) -> bool:
        """Indicizza documento in ChromaDB"""

    async def similarity_search(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict]:
        """Ricerca similarità vettoriale"""
```

### **Uso Tipico**
```python
from backend.services.rag_service import RAGService

rag_service = RAGService()

# Retrieve context per chat
context = await rag_service.retrieve_context(
    query="How does binary search work?",
    course_id="course_abc123",
    book_id="book_def456",
    max_chunks=3,
    search_type="hybrid"
)

# Context result format
[
    {
        "content": "Binary search works by...",
        "source": {
            "book_title": "Algorithms and Data Structures",
            "chapter": "Binary Search",
            "page": 45,
            "pdf_filename": "chapter3.pdf"
        },
        "relevance_score": 0.92,
        "chunk_id": "chunk_789"
    }
]
```

---

## 📚 Course Service

### **Overview**
Servizio centrale per la gestione completa dei corsi, inclusi libri, materiali didattici, e organizzazione contenuti.

### **Features Principali**
- **Course CRUD**: Creazione, lettura, aggiornamento, eliminazione corsi
- **Book Management**: Gestione libri associati ai corsi
- **Material Processing**: Upload e processing PDF
- **File Organization**: Organizzazione automatica file system
- **Metadata Management**: Gestione metadati contenuti
- **Access Control**: Controllo accesso materiali

### **Metodi Chiave**

#### **Course Management**
```python
class CourseService:
    async def create_course(
        self,
        title: str,
        description: str,
        category: str,
        instructor: Optional[str] = None
    ) -> Dict:
        """Crea nuovo corso con ID univoco"""

    async def get_course_details(
        self,
        course_id: str,
        include_materials: bool = True,
        include_books: bool = True
    ) -> Dict:
        """Ottiene dettagli completi corso"""

    async def update_course(
        self,
        course_id: str,
        updates: Dict[str, Any]
    ) -> Dict:
        """Aggiorna metadata corso"""
```

#### **Book Management**
```python
async def create_book(
    self,
    course_id: str,
    title: str,
    author: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict:
    """Crea nuovo libro associato al corso"""

async def add_pdf_to_book(
    self,
    course_id: str,
    book_id: str,
    pdf_file: UploadFile,
    title: Optional[str] = None,
    chapter: Optional[str] = None
) -> Dict:
    """Aggiunge PDF al libro con processing automatico"""
```

#### **Material Processing**
```python
class MaterialProcessor:
    async def process_pdf_upload(
        self,
        file: UploadFile,
        course_id: str,
        book_id: str
    ) -> Dict:
        """Processa upload PDF con estrazione testo"""

    async def extract_text_from_pdf(
        self,
        pdf_path: str,
        extract_images: bool = False,
        extract_tables: bool = True
    ) -> Dict:
        """Estrae testo, immagini, tabelle da PDF"""

    def generate_material_metadata(
        self,
        pdf_path: str,
        course_id: str,
        book_id: str
    ) -> Dict:
        """Genera metadata completi per materiale"""
```

### **File Structure Management**
```python
class FileManager:
    def organize_course_files(self, course_id: str) -> Dict:
        """Organizza struttura file system corso"""

    def get_material_path(
        self,
        course_id: str,
        book_id: str,
        filename: str
    ) -> str:
        """Genera path file materiale"""

    def validate_file_access(
        self,
        course_id: str,
        book_id: str,
        filename: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Valida accesso file materiali"""
```

### **Uso Tipico**
```python
from backend.services.course_service import CourseService

course_service = CourseService()

# Create new course
course = await course_service.create_course(
    title="Data Structures and Algorithms",
    description="Fundamental algorithms and data structures",
    category="computer_science"
)

# Add book to course
book = await course_service.create_book(
    course_id=course["id"],
    title="Introduction to Algorithms",
    author="Thomas H. Cormen",
    tags=["algorithms", "data_structures", "computer_science"]
)

# Process PDF upload
result = await course_service.process_pdf_upload(
    pdf_file=uploaded_file,
    course_id=course["id"],
    book_id=book["id"]
)
```

---

## 📝 Annotation Service

### **Overview**
Sistema avanzato di annotazioni per PDF con sincronizzazione AI, supportando highlight, note, e sharing intelligente.

### **Features Principali**
- **Multi-format Annotations**: Highlight, underline, text notes
- **Spatial Annotation**: Coordinate precise su pagine PDF
- **AI Sharing**: Condivisione selettiva con AI tutor
- **Collaborative Features**: Condivisione note tra utenti
- **Export/Import**: Backup e migrazione annotazioni
- **Version Control**: Storia modifiche annotazioni

### **Metodi Chiave**

#### **Annotation Management**
```python
class AnnotationService:
    async def create_annotation(
        self,
        course_id: str,
        book_id: str,
        pdf_filename: str,
        page: int,
        selection: Dict[str, Any],  # x,y coordinates
        text: str,
        note: Optional[str] = None,
        annotation_type: str = "highlight",
        color: str = "#ffeb3b",
        share_with_ai: bool = False,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """Crea nuova annotazione"""

    async def get_annotations(
        self,
        course_id: str,
        book_id: Optional[str] = None,
        pdf_filename: Optional[str] = None,
        page: Optional[int] = None,
        include_ai_shared: bool = True
    ) -> List[Dict]:
        """Recupera annotazioni con filtri"""
```

#### **AI Integration**
```python
async def get_ai_shared_annotations(
    self,
    course_id: str,
    book_id: str,
    pdf_filename: str
) -> List[Dict]:
    """Recupera annotazioni condivise con AI"""

async def merge_annotations_with_context(
    self,
    context_chunks: List[Dict],
    course_id: str,
    book_id: str,
    pdf_filename: str
) -> List[Dict]:
    """Unisce annotazioni personali con context RAG"""
```

#### **Export/Import**
```python
async def export_annotations(
    self,
    course_id: str,
    format: str = "json"  # "json", "csv", "pdf"
) -> Union[Dict, bytes]:
    """Esporta annotazioni corso"""

async def import_annotations(
    self,
    course_id: str,
    annotations_data: Union[Dict, List[Dict]],
    merge_strategy: str = "append"  # "append", "replace", "merge"
) -> Dict:
    """Importa annotazioni da backup"""
```

### **Data Models**
```python
@dataclass
class Annotation:
    id: str
    course_id: str
    book_id: str
    pdf_filename: str
    page: int
    selection: Dict[str, float]  # x1, y1, x2, y2
    text: str
    note: Optional[str]
    type: str  # "highlight", "underline", "note"
    color: str
    share_with_ai: bool
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str]
```

### **Uso Tipico**
```python
from backend.services.annotation_service import AnnotationService

annotation_service = AnnotationService()

# Create highlight annotation
annotation = await annotation_service.create_annotation(
    course_id="course_abc123",
    book_id="book_def456",
    pdf_filename="chapter1.pdf",
    page=15,
    selection={
        "x1": 100.5, "y1": 200.2,
        "x2": 300.8, "y2": 220.1
    },
    text="Binary search algorithm runs in O(log n) time",
    note="Important complexity analysis",
    annotation_type="highlight",
    color="#ffeb3b",
    share_with_ai=True,
    tags=["algorithms", "complexity", "important"]
)
```

---

## 🧠 Spaced Repetition Service

### **Overview**
Implementazione avanzata dell'algoritmo SM-2 (SuperMemo 2) per spaced repetition con ottimizzazioni personalizzate.

### **Features Principali**
- **Enhanced SM-2 Algorithm**: Algoritmo SM-2 migliorato con adaptation dinamica
- **Auto-Card Generation**: Generazione automatica flashcard dai materiali
- **Difficulty Adaptation": Adattamento difficoltà basato su performance
- **Priority Management": Gestione priorità card per esami
- **Analytics Dashboard": Analytics performance ripasso
- **Batch Review": Revisione efficiente batch card

### **Metodi Chiave**

#### **Card Management**
```python
class SpacedRepetitionService:
    async def create_card(
        self,
        course_id: str,
        question: str,
        answer: str,
        difficulty: float = 2.5,  # SM-2 initial difficulty
        tags: Optional[List[str]] = None,
        source_material: Optional[Dict] = None
    ) -> Dict:
        """Crea nuova card con algoritmo SM-2"""

    async def calculate_next_review(
        self,
        card: Dict,
        quality: int  # 0-5 SM-2 quality rating
    ) -> Dict:
        """Calcola prossimo ripasso con SM-2 enhanced"""

    async def get_due_cards(
        self,
        course_id: str,
        limit: int = 20,
        priority_tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """Recupera card pronte per ripasso"""
```

#### **SM-2 Enhanced Algorithm**
```python
class EnhancedSM2:
    def calculate_interval(
        self,
        repetition: int,
        easiness_factor: float,
        interval: int,
        quality: int
    ) -> Tuple[int, float]:
        """Calcola intervallo con SM-2 enhanced"""

    def adapt_difficulty(
        self,
        card: Dict,
        performance_history: List[int]
    ) -> float:
        """Adatta difficoltà basata su storia performance"""

    def optimize_review_schedule(
        self,
        cards: List[Dict],
        available_time: int,  # minutes
        deadline_weight: float = 1.5
    ) -> List[Dict]:
        """Ottimizza schedule ripasso basato su tempo"""
```

### **Card Generation**
```python
class AutoCardGenerator:
    async def generate_from_materials(
        self,
        course_id: str,
        book_id: str,
        topic: str,
        count: int = 10,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """Genera card automatiche da materiali"""

    def extract_key_concepts(
        self,
        text_chunk: str,
        min_importance: float = 0.7
    ) -> List[str]:
        """Estrae concetti chiave dal testo"""

    def generate_question_variants(
        self,
        concept: str,
        context: str
    ) -> List[Dict]:
        """Genera varianti domanda per concetto"""
```

### **Uso Tipico**
```python
from backend.services.spaced_repetition_service import SpacedRepetitionService

sr_service = SpacedRepetitionService()

# Create new card
card = await sr_service.create_card(
    course_id="course_abc123",
    question="What is the time complexity of binary search?",
    answer="O(log n) - Binary search runs in logarithmic time",
    difficulty=2.0,
    tags=["algorithms", "complexity", "binary_search"],
    source_material={
        "book_id": "book_def456",
        "page": 67,
        "chapter": "Binary Search"
    }
)

# Review card
review_result = await sr_service.submit_review(
    card_id=card["id"],
    quality=4,  # Good response
    time_taken_seconds=30,
    course_id="course_abc123"
)
```

---

## ❓ Active Recall Service

### **Overview**
Servizio per generazione di domande multi-format basate sulla tassonomia di Bloom per active recall learning.

### **Features Principali**
- **Bloom's Taxonomy Integration**: Domande per ogni livello cognitivo
- **Multi-Format Questions**: Multiple choice, short answer, coding, essay
- **Adaptive Difficulty**: Adattamento difficoltà basato su performance
- **Context-Aware Generation**: Domande specifiche al materiale corso
- **Performance Analytics**: Analytics per identificare knowledge gaps
- **Gamification Elements**: Punteggi e achievement per engagement

### **Metodi Chiave**

#### **Question Generation**
```python
class ActiveRecallService:
    async def generate_questions(
        self,
        topic: str,
        course_id: str,
        difficulty: str = "medium",
        question_types: List[str] = None,
        bloom_level: str = "apply",  # "remember", "understand", "apply", "analyze", "evaluate", "create"
        count: int = 10,
        context_materials: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """Genera domande multi-formato"""

    async def generate_multiple_choice(
        self,
        concept: str,
        context: str,
        difficulty: float
    ) -> Dict:
        """Genera domanda multiple choice con distrattori"""

    async def generate_coding_question(
        self,
        algorithm: str,
        language: str = "python",
        difficulty: str = "medium"
    ) -> Dict:
        """Genera esercizio di programmazione"""
```

#### **Adaptive Learning**
```python
class AdaptiveQuestionEngine:
    def analyze_performance(
        self,
        user_answers: List[Dict],
        topic_patterns: Dict[str, float]
    ) -> Dict:
        """Analizza performance per identificare pattern"""

    def adjust_difficulty(
        self,
        current_difficulty: float,
        recent_performance: List[int],
        topic_mastery: Dict[str, float]
    ) -> float:
        """Adatta difficoltà basata su performance"""

    def recommend_focus_areas(
        self,
        performance_data: Dict,
        course_objectives: List[str]
    ) -> List[str]:
        """Raccomanda aree di focus per studio"""
```

### **Question Templates**
```python
class QuestionTemplates:
    ALGORITHM_TEMPLATES = {
        "complexity_analysis": {
            "multiple_choice": "What is the time complexity of {algorithm}?",
            "short_answer": "Explain why {algorithm} has O({complexity}) complexity.",
            "coding": "Implement {algorithm} and analyze its complexity."
        },
        "comparison": {
            "multiple_choice": "Which algorithm is better for {scenario}?",
            "explanation": "Compare {algorithm1} and {algorithm2} for {use_case}."
        }
    }

    def generate_from_template(
        self,
        template_name: str,
        variables: Dict[str, str]
    ) -> str:
        """Genera domanda da template"""
```

### **Performance Tracking**
```python
class PerformanceTracker:
    async def track_answer(
        self,
        user_id: str,
        question_id: str,
        answer: str,
        is_correct: bool,
        time_taken: int,
        confidence: Optional[int] = None
    ) -> Dict:
        """Traccia risposta con analytics"""

    def get_learning_gaps(
        self,
        user_id: str,
        course_id: str
    ) -> List[Dict]:
        """Identifica knowledge gaps"""

    def generate_recommendations(
        self,
        performance_data: Dict
    ) -> List[str]:
        """Genera raccomandazioni studio"""
```

### **Uso Tipico**
```python
from backend.services.active_recall_service import ActiveRecallService

ar_service = ActiveRecallService()

# Generate questions for topic
questions = await ar_service.generate_questions(
    topic="Sorting Algorithms",
    course_id="course_abc123",
    difficulty="intermediate",
    question_types=["multiple_choice", "short_answer", "coding"],
    bloom_level="apply",
    count=5
)

# Submit answer
result = await ar_service.submit_answer(
    question_id=questions[0]["id"],
    user_answer="Quick Sort",
    is_correct=True,
    time_taken_seconds=45,
    confidence=4
)
```

---

## 🎨 Dual Coding Service

### **Overview**
Servizio per creare contenuti visual-verbal integrati basati sul principio di dual coding per migliorare retention.

### **Features Principali**
- **Visual-Verbal Integration**: Combinazione ottimale testo e immagini
- **Multi-Modal Content**: Diagrammi, spiegazioni, esempi, animazioni
- **Learning Style Adaptation**: Adattamento a stili di apprendimento
- **Interactive Elements**: Elementi interattivi per engagement
- **AI-Generated Visuals**: Generazione automatica diagrammi e flowcharts
- **Concept Mapping**: Mappe concettuali visuali

### **Metodi Chiave**

#### **Content Creation**
```python
class DualCodingService:
    async def create_dual_coding_content(
        self,
        concept: str,
        course_id: str,
        element_types: List[str] = None,
        learning_style: str = "visual",  # "visual", "verbal", "mixed"
        complexity: str = "medium"
    ) -> Dict:
        """Crea contenuto visual-verbal integrato"""

    async def generate_visual_element(
        self,
        concept: str,
        element_type: str,  # "diagram", "flowchart", "mindmap", "timeline"
        style: str = "modern"
    ) -> Dict:
        """Genera elemento visuale AI"""

    async def create_explanation(
        self,
        concept: str,
        visual_context: Dict,
        detail_level: str = "medium"
    ) -> Dict:
        """Crea spiegazione testuale coordinata con visuale"""
```

#### **Element Types Management**
```python
class ElementTypesManager:
    ELEMENT_TYPES = {
        "diagram": {
            "description": "Structural representation of concept",
            "use_cases": ["processes", "structures", "relationships"]
        },
        "flowchart": {
            "description": "Step-by-step process visualization",
            "use_cases": ["algorithms", "workflows", "decision_trees"]
        },
        "mindmap": {
            "description": "Hierarchical concept connections",
            "use_cases": ["brainstorming", "knowledge_organization"]
        },
        "timeline": {
            "description": "Chronological sequence visualization",
            "use_cases": ["historical_events", "process_stages"]
        },
        "comparison_table": {
            "description": "Side-by-side feature comparison",
            "use_cases": ["concepts_comparison", "algorithm_analysis"]
        },
        "example": {
            "description": "Concrete illustration with visual aids",
            "use_cases": ["complex_concepts", "practical_application"]
        },
        "metaphor": {
            "description": "Analogy-based visual explanation",
            "use_cases": ["abstract_concepts", "intuitive_understanding"]
        },
        "animation": {
            "description": "Dynamic visual representation",
            "use_cases": ["processes", "transformations", "algorithms"]
        },
        "infographic": {
            "description": "Information-rich visual summary",
            "use_cases": ["data_visualization", "concept_overview"]
        },
        "interactive_simulation": {
            "description": "User-controlled visual exploration",
            "use_cases": ["experiments", "parameter_effects"]
        }
    }
```

#### **Learning Style Integration**
```python
class LearningStyleAdapter:
    def adapt_for_visual_learner(
        self,
        content: Dict,
        base_concept: str
    ) -> Dict:
        """Adatta contenuto per learner visuale"""

    def adapt_for_verbal_learner(
        self,
        content: Dict,
        base_concept: str
    ) -> Dict:
        """Adatta contenuto per learner verbale"""

    def create_mixed_approach(
        self,
        visual_content: Dict,
        verbal_content: Dict
    ) -> Dict:
        """Crea approccio misto bilanciato"""
```

### **Visual Generation**
```python
class VisualGenerator:
    async def generate_diagram(
        self,
        concept: str,
        style: str = "modern",
        complexity: str = "medium"
    ) -> Dict:
        """Genera diagramma concettuale"""

    async def create_flowchart(
        self,
        process_steps: List[str],
        decision_points: List[Dict] = None
    ) -> Dict:
        """Crea flowchart processo"""

    def generate_mindmap_structure(
        self,
        central_concept: str,
        sub_concepts: List[str],
        connections: List[Dict] = None
    ) -> Dict:
        """Genera struttura mindmap"""
```

### **Uso Tipico**
```python
from backend.services.dual_coding_service import DualCodingService

dc_service = DualCodingService()

# Create dual coding content
content = await dc_service.create_dual_coding_content(
    concept="Binary Search Tree",
    course_id="course_abc123",
    element_types=["diagram", "explanation", "example"],
    learning_style="visual",
    complexity="intermediate"
)

# Content structure
{
    "concept": "Binary Search Tree",
    "elements": [
        {
            "type": "diagram",
            "title": "BST Structure",
            "content": "<svg>...</svg>",  # Visual diagram
            "description": "Visual representation of tree structure"
        },
        {
            "type": "explanation",
            "title": "How BST Works",
            "content": "A binary search tree maintains order...",
            "description": "Textual explanation coordinated with diagram"
        },
        {
            "type": "example",
            "title": "Search Operation Example",
            "content": "Finding value 42 in the BST...",
            "visual_aid": "step-by-step visualization"
        }
    ],
    "integration_notes": "Study the diagram first, then read explanation...",
    "learning_style": "visual",
    "complexity": "intermediate"
}
```

---

*Continua con altri servizi nella prossima sezione...*

---

## 📊 Analytics Services Overview

### **A/B Testing Service**
Statistical framework per test A/B di strategie didattiche:
- **Test Design**: Configurazione test con varianti e metrics
- **Statistical Analysis**: Analisi significatività statistica
- **Real-time Monitoring**: Monitoring risultati in tempo reale
- **Sample Size Calculator**: Calcolo dimensione campione ottimale

### **Continuous Improvement Service**
Machine learning system per ottimizzazione continua:
- **Pattern Recognition**: Identificazione pattern apprendimento
- **Performance Optimization**: Ottimizzazione strategie LLM
- **Insight Generation**: Generazione insight actionable
- **Automated Testing**: Test automatici migliorie

### **Learning Analytics Service**
Comprehensive learning progress tracking:
- **Progress Monitoring**: Monitoraggio progresso individuale
- **Metacognitive Analysis**: Analisi metacognizione
- **Knowledge Mapping**: Mappatura conoscenze
- **Performance Prediction**: Predizione performance

---

*Ultimo aggiornamento: Novembre 2025*
*Versione servizi: v2.0*
*Compatibile con Tutor-AI v2.0+*