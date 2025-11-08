from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from datetime import datetime
from typing import Dict, Any

app = FastAPI(title="Tutor AI - Simple Backend", version="1.0.0")

# Configurazione CORS per permettere richieste dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path del file concept maps
CONCEPT_MAPS_PATH = "data/concept_maps.json"
CONCEPT_METRICS_PATH = "data/concept_metrics.json"

def ensure_data_dir():
    """Assicura che la directory data esista"""
    os.makedirs("data", exist_ok=True)

def load_concept_maps() -> Dict[str, Any]:
    """Carica le mappa dei concetti"""
    if not os.path.exists(CONCEPT_MAPS_PATH):
        return {"concept_maps": {}}
    try:
        with open(CONCEPT_MAPS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"concept_maps": {}}

def save_concept_maps(data: Dict[str, Any]):
    """Salva le mappa dei concetti"""
    ensure_data_dir()
    with open(CONCEPT_MAPS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_concept_metrics() -> Dict[str, Any]:
    """Carica le metriche dei concetti"""
    if not os.path.exists(CONCEPT_METRICS_PATH):
        return {}
    try:
        with open(CONCEPT_METRICS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_concept_metrics(data: Dict[str, Any]):
    """Salva le metriche dei concetti"""
    ensure_data_dir()
    with open(CONCEPT_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_fallback_concepts(course_id: str) -> Dict[str, Any]:
    """Genera concetti di fallback quando non ci sono documenti"""
    return {
        "course_id": course_id,
        "generated_at": datetime.now().isoformat(),
        "source_count": 0,
        "is_fallback": True,
        "concepts": [
            {
                "id": "introduzione",
                "name": "Introduzione al Corso",
                "summary": "Concetti fondamentali e panoramica della materia",
                "chapter": {"title": "Capitolo 1", "index": 1},
                "related_topics": ["concetti base", "terminologia", "obiettivi del corso"],
                "learning_objectives": [
                    "Comprendere gli obiettivi principali del corso",
                    "Familiarizzare con la terminologia di base",
                    "Identificare le aree tematiche principali"
                ],
                "suggested_reading": ["Materiale introduttivo del corso"],
                "recommended_minutes": 30,
                "quiz_outline": [
                    "Quali sono gli obiettivi principali di questo corso?",
                    "Spiegare i concetti fondamentali introdotti"
                ]
            },
            {
                "id": "concetti-fondamentali",
                "name": "Concetti Fondamentali",
                "summary": "Principi teorici e base della disciplina",
                "chapter": {"title": "Capitolo 2", "index": 2},
                "related_topics": ["teoria principale", "principi base", "fondamenti"],
                "learning_objectives": [
                    "Comprendere i principi teorici fondamentali",
                    "Applicare i concetti base a problemi semplici",
                    "Distinguere tra teoria e pratica"
                ],
                "suggested_reading": ["Testi di riferimento principali"],
                "recommended_minutes": 45,
                "quiz_outline": [
                    "Definire i concetti fondamentali della materia",
                    "Spiegare l'applicazione dei principi base"
                ]
            },
            {
                "id": "applicazioni-pratiche",
                "name": "Applicazioni Pratiche",
                "summary": "Esercizi e applicazioni reali dei concetti studiati",
                "chapter": {"title": "Capitolo 3", "index": 3},
                "related_topics": ["esercizi", "casi studio", "problemi pratici"],
                "learning_objectives": [
                    "Applicare la teoria a problemi pratici",
                    "Risolvere esercizi tipici della materia",
                    "Analizzare casi studio reali"
                ],
                "suggested_reading": ["Eserciziari e casi studio"],
                "recommended_minutes": 60,
                "quiz_outline": [
                    "Risolvere un problema pratico applicando i concetti",
                    "Analizzare un caso studio specifico"
                ]
            },
            {
                "id": "approfondimenti",
                "name": "Approfondimenti Tematici",
                "summary": "Argomenti avanzati e aree specialistiche della disciplina",
                "chapter": {"title": "Capitolo 4", "index": 4},
                "related_topics": ["argomenti avanzati", "specializzazioni", "tematiche complesse"],
                "learning_objectives": [
                    "Esplorare argomenti avanzati della materia",
                    "Comprendere le interconnessioni tra diversi concetti",
                    "Sviluppare competenze specialistiche"
                ],
                "suggested_reading": ["Articoli scientifici e testi avanzati"],
                "recommended_minutes": 50,
                "quiz_outline": [
                    "Spiegare le relazioni tra concetti avanzati",
                    "Applicare conoscenze specialistiche a problemi complessi"
                ]
            },
            {
                "id": "valutazione-e-revisione",
                "name": "Valutazione e Revisione",
                "summary": "Verifica dell'apprendimento e preparazione per esami",
                "chapter": {"title": "Capitolo 5", "index": 5},
                "related_topics": ["verifica", "esercizi di revisione", "preparazione esami"],
                "learning_objectives": [
                    "Verificare la comprensione dei concetti principali",
                    "Identificare aree che richiedono ulteriore studio",
                    "Prepararsi efficacemente per le valutazioni"
                ],
                "suggested_reading": ["Materiale di ripasso e esercizi di valutazione"],
                "recommended_minutes": 40,
                "quiz_outline": [
                    "Valutare la comprensione generale della materia",
                    "Identificare punti di forza e di debolezza"
                ]
            }
        ]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Tutor AI Simple Backend - Concepts API"}

@app.get("/courses")
async def get_courses():
    """Endpoint per ottenere i corsi"""
    courses = [
        {"id": "90a903c0-4ef6-4415-ae3b-9dbc70ad69a9", "name": "Corso di Test", "subject": "Informatica", "materials_count": 0}
    ]
    return {"courses": courses}

@app.get("/courses/{course_id}/books")
async def get_course_books(course_id: str):
    """Endpoint per ottenere i libri di un corso"""
    books = [
        {"id": "7a8b3b91-46c0-4b47-9e2b-083f79dc9f29", "title": "Libro di Test", "author": "Autore Test", "materials_count": 0}
    ]
    return {"books": books}

@app.get("/courses/{course_id}/concepts")
async def get_concept_map(course_id: str):
    """Endpoint per ottenere la mappa dei concetti"""
    concept_maps = load_concept_maps()

    if course_id not in concept_maps["concept_maps"]:
        # Genera automaticamente concetti fallback se non esistono
        fallback_map = generate_fallback_concepts(course_id)
        concept_maps["concept_maps"][course_id] = fallback_map
        save_concept_maps(concept_maps)

    return {"concept_map": concept_maps["concept_maps"][course_id]}

@app.get("/courses/{course_id}/concepts/metrics")
async def get_concept_metrics(course_id: str):
    """Endpoint per ottenere le metriche dei concetti"""
    all_metrics = load_concept_metrics()
    course_metrics = all_metrics.get(course_id, {})

    # Genera metriche di default se non esistono
    if not course_metrics:
        # Carica la concept map per generare metriche di default
        concept_maps = load_concept_maps()
        concept_map = concept_maps["concept_maps"].get(course_id, {})

        if concept_map.get("concepts"):
            for concept in concept_map["concepts"]:
                course_metrics[concept["id"]] = {
                    "stats": {
                        "average_score": 0.0,
                        "attempts_count": 0,
                        "average_time_seconds": 0.0
                    },
                    "last_attempt": None
                }

            all_metrics[course_id] = course_metrics
            save_concept_metrics(all_metrics)

    return {"metrics": course_metrics}

@app.post("/courses/{course_id}/concepts/generate")
async def generate_concept_map(course_id: str, payload: dict = None):
    """Endpoint per generare una nuova mappa dei concetti"""
    try:
        # Simula la generazione (in questo caso usa sempre i fallback)
        concept_map = generate_fallback_concepts(course_id)

        # Salva la mappa
        concept_maps = load_concept_maps()
        concept_maps["concept_maps"][course_id] = concept_map
        save_concept_maps(concept_maps)

        # Genera metriche di base
        all_metrics = load_concept_metrics()
        course_metrics = {}

        for concept in concept_map["concepts"]:
            course_metrics[concept["id"]] = {
                "stats": {
                    "average_score": 0.0,
                    "attempts_count": 0,
                    "average_time_seconds": 0.0
                },
                "last_attempt": None
            }

        all_metrics[course_id] = course_metrics
        save_concept_metrics(all_metrics)

        return {"success": True, "concept_map": concept_map}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/courses/{course_id}/concepts/{concept_id}/quiz-results")
async def save_quiz_results(course_id: str, concept_id: str, payload: dict):
    """Endpoint per salvare i risultati dei quiz"""
    try:
        all_metrics = load_concept_metrics()

        if course_id not in all_metrics:
            all_metrics[course_id] = {}

        concept_metrics = all_metrics[course_id].get(concept_id, {
            "stats": {
                "average_score": 0.0,
                "attempts_count": 0,
                "average_time_seconds": 0.0
            },
            "last_attempt": None
        })

        # Aggiorna le metriche
        score = payload.get("score", 0.0)
        time_seconds = payload.get("time_seconds", 0.0)

        stats = concept_metrics["stats"]
        stats["attempts_count"] += 1

        # Calcola la media ponderata
        total_attempts = stats["attempts_count"]
        if total_attempts == 1:
            stats["average_score"] = score
            stats["average_time_seconds"] = time_seconds
        else:
            # Media ponderata
            prev_total = (stats["average_score"] * (total_attempts - 1))
            stats["average_score"] = (prev_total + score) / total_attempts

            prev_time_total = (stats["average_time_seconds"] * (total_attempts - 1))
            stats["average_time_seconds"] = (prev_time_total + time_seconds) / total_attempts

        concept_metrics["last_attempt"] = datetime.now().isoformat()
        all_metrics[course_id][concept_id] = concept_metrics
        save_concept_metrics(all_metrics)

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/quiz")
async def generate_quiz(payload: dict):
    """Endpoint per generare quiz"""
    course_id = payload.get("course_id", "")
    topic = payload.get("topic", "Generale")
    difficulty = payload.get("difficulty", "medium")
    num_questions = payload.get("num_questions", 5)

    # Quiz di esempio
    quiz = {
        "title": f"Quiz - {topic}",
        "difficulty": difficulty,
        "questions": [
            {
                "question": f"Qual è il concetto principale di {topic}?",
                "options": {
                    "A": "Opzione A",
                    "B": "Opzione B",
                    "C": "Opzione C",
                    "D": "Opzione D"
                },
                "correct": "A",
                "explanation": f"La spiegazione della risposta corretta per {topic}"
            },
            {
                "question": f"Come si applica {topic} in pratica?",
                "options": {
                    "A": "Applicazione A",
                    "B": "Applicazione B",
                    "C": "Applicazione C",
                    "D": "Applicazione D"
                },
                "correct": "B",
                "explanation": f"Dettagli sull'applicazione pratica di {topic}"
            }
        ]
    }

    return {"quiz": quiz}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)