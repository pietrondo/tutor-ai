import openai
import os
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.client = None
        self.model_type = os.getenv("LLM_TYPE", "openai")  # "openai" or "local"
        self.setup_client()

    def setup_client(self):
        if self.model_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            if api_key:
                self.client = openai.OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                # Usa il modello più recente disponibile
                self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
            else:
                raise ValueError("Chiave API OpenAI non trovata nelle variabili d'ambiente")
        else:
            # Per LLM locale (Ollama/LM Studio)
            self.base_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
            self.model = os.getenv("LOCAL_LLM_MODEL", "llama3.1")

    async def generate_response(self, query: str, context: Dict[str, Any], course_id: str) -> str:
        """Generate a tutoring response based on query and context"""

        context_text = context.get("text", "")
        sources = context.get("sources", [])

        system_prompt = f"""
        Sei un tutor universitario esperto e paziente. Il tuo ruolo è aiutare gli studenti a comprendere gli argomenti in modo chiaro e approfondito.

        Linee guida:
        - Rispondi in italiano
        - Sii chiaro, paziente ed incoraggiante
        - Usa il contesto fornito per basare le tue risposte
        - Se non conosci la risposta, ammettilo onestamente
        - Fai domande di follow-up per stimolare il pensiero critico
        - Adatta il linguaggio al livello universitario
        - Fornisci esempi pratici quando possibile

        Contesto rilevante:
        {context_text}
        """

        try:
            if self.model_type == "openai":
                # API OpenAI più recente con parametri avanzati
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    temperature=0.7,
                    max_tokens=1500,
                    top_p=0.9,
                    frequency_penalty=0.2,
                    presence_penalty=0.1,
                    response_format={"type": "text"}
                )
                return response.choices[0].message.content
            else:
                # LLM Locale (Ollama/LM Studio)
                import requests
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1500,
                    "stream": False
                }
                response = requests.post(f"{self.base_url}/chat/completions", json=payload)
                result = response.json()
                return result["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"Errore nella generazione della risposta: {e}")
            return "Mi dispiace, ho riscontrato un problema nell'elaborare la tua domanda. Riprova più tardi."

    async def generate_quiz(self, course_id: str, topic: str = None, difficulty: str = "medium", num_questions: int = 5) -> Dict[str, Any]:
        """Generate quiz questions based on course material"""

        system_prompt = f"""
        Sei un professore universitario esperto nella creazione di test di valutazione.
        Crea {num_questions} domande a scelta multipla sul corso specificato.

        Difficoltà: {difficulty}
        Argomento focus: {topic if topic else "tutti gli argomenti del corso"}

        Formato richiesto per ogni domanda:
        - Domanda chiara e precisa
        - 4 opzioni di risposta (A, B, C, D)
        - Una sola risposta corretta
        - Breve spiegazione della risposta corretta

        Restituisci il risultato in formato JSON.
        """

        try:
            if self.model_type == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Crea un quiz per il corso {course_id}"}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                content = response.choices[0].message.content
            else:
                import requests
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Crea un quiz per il corso {course_id}"}
                    ],
                    "stream": False
                }
                response = requests.post(f"{self.base_url}/v1/chat/completions", json=payload)
                content = response.json()["choices"][0]["message"]["content"]

            # Parse JSON response
            try:
                quiz_data = json.loads(content)
                return quiz_data
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "questions": [
                        {
                            "question": content[:200] + "...",
                            "options": {"A": "Opzione A", "B": "Opzione B", "C": "Opzione C", "D": "Opzione D"},
                            "correct": "A",
                            "explanation": "Spiegazione in elaborazione"
                        }
                    ],
                    "title": f"Quiz - {course_id}",
                    "difficulty": difficulty
                }

        except Exception as e:
            print(f"Error generating quiz: {e}")
            return {
                "error": "Impossibile generare il quiz in questo momento",
                "questions": []
            }

    async def generate_study_plan(self, course_id: str, topics: List[str], duration_weeks: int, learning_style: str = "balanced", study_hours_per_day: int = 3, difficulty_level: str = "intermediate") -> str:
        """Generate a personalized study plan with advanced AI prompts"""

        # Map learning styles to study approaches
        learning_approaches = {
            "visual": "Mappe mentali, diagrammi di flusso, color coding, video educativi, infografiche",
            "auditory": "Podcast, registrazione delle spiegazioni, studio in gruppo, discussione orale, audiolibri",
            "kinesthetic": "Esercizi pratici, simulazioni, progetto hands-on, insegnamento ad altri, applicazioni reali",
            "reading": "Testi dettagliati, appunti scritti, riassunti, tecniche SQ3R, highlight sistematico",
            "balanced": "Combinazione di metodi visivi, uditivi e pratici per massimizzare la ritenzione"
        }

        study_approach = learning_approaches.get(learning_style, learning_approaches["balanced"])

        system_prompt = f"""
        Sei un esperto accademico e learning scientist specializzato in neuroscienze dell'apprendimento e didattica universitaria avanzata.

        CONTESTO: Stai creando un piano di studio personalizzato per un corso universitario di {duration_weeks} settimane.

        PARAMETRI PERSONALIZZATI:
        - Corso: {course_id}
        - Argomenti: {', '.join(topics)}
        - Stile di apprendimento: {learning_style}
        - Ore di studio giornaliere: {study_hours_per_day}
        - Livello di difficoltà: {difficulty_level}
        - Approccio di studio raccomandato: {study_approach}

        PRINCIPI PEDAGOGICI DA APPLICARE:
        1. Spaced Repetition: Ripetizione distribuita ottimale (intervalli crescenti)
        2. Active Recall: Richiamo attivo delle informazioni
        3. Interleaving: Alternanza di argomenti diversi per migliorare la flessibilità cognitiva
        4. Elaboration: Approfondimento dei concetti attraverso connessioni personali
        5. Dual Coding: Combinazione di testo e elementi visivi quando possibile
        6. Metacognition: Sviluppo della consapevolezza sui propri processi di apprendimento

        STRUTTURA RICHIESTA per ogni settimana:

        ## Settimana X: [Tema Principale]

        ### Obiettivi di Apprendimento SMART
        - [Specifico] Obiettivo concreto e misurabile
        - [Misurabile] Come verificare il raggiungimento
        - [Raggiungibile] Realistico data la complessità
        - [Rilevante] Collegato agli obiettivi del corso
        - [Temporizzato] Con scadenze precise

        ### Programmazione Giornaliera (ore {study_hours_per_day}/giorno)
        - **Giorno 1**: [Argomento specifico] - [Tecnica di studio specifica per stile {learning_style}]
        - **Giorno 2**: [Argomento specifico] - [Sessione di active recall]
        - **Giorno 3**: [Argomento specifico] - [Esercizio pratico/applicazione]
        - **Giorno 4**: [Revisione e consolidamento] - [Spaced repetition]
        - **Giorno 5**: [Verifica e autovalutazione] - [Quiz o progetto pratico]
        - **Weekend**: [Recupero o studio leggero] - [Ripasso passivo]

        ### Tecniche di Studio Specifiche
        - Tecnica primaria basata su stile {learning_style}
        - Tecnica secondaria per rinforzo
        - Momento di verifica (quando e come)

        ### Risorse Consigliate
        - Materiale del corso (capitoli, slide)
        - Risorse supplementari online
        - Esercizi pratici o esempi

        ### Metriche di Successo
        - Checkpoint intermedi
        - Autovalutazione settimanale
        - Indicatori di comprensione

        ### Conseguenze Cognitive e Metacognitive
        - Warning comuni da evitare
        - Strategie di superamento ostacoli
        - Momenti di riflessione metacognitiva

        INDICAZIONI AGGIUNTIVE:
        - Includi pause strategiche basate sulla tecnica Pomodoro (25min studio + 5min pausa)
        - Prevedi sessioni di revisione cumulativa ogni 2 settimane
        - Alterna argomenti teorici e pratici quando possibile
        - Includi obiettivi di progressione graduale da principiante ad avanzato
        - Suggerisci momenti di studio collaborativo se appropriato
        - Integra momenti di apprendimento basato su problemi

        TONO E STILE: Motivazionale ma realistico, professionale ma accessibile, con incoraggiamenti specifici e strategie concrete.

        IMPORTANTE: Il piano deve essere flessibile e adattabile. Includi suggerimenti per modificare il programma in base al progresso effettivo.
        """

        try:
            user_prompt = f"""
            Crea un piano di studio personalizzato per il corso {course_id} con i seguenti requisiti:
            - Durata: {duration_weeks} settimane
            - Argomenti: {', '.join(topics)}
            - Stile apprendimento: {learning_style}
            - Ore giornaliere: {study_hours_per_day}
            - Livello: {difficulty_level}

            Genera un piano completo, dettagliato e motivazionale seguendo la struttura richiesta.
            """

            if self.model_type == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,  # Usa il modello configurato (GPT-4, GPT-4o, etc.)
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.8,  # Creativity leggermente più alta per piani di studio
                    max_tokens=3000,  # Aumentato per piani più dettagliati
                    top_p=0.9,
                    frequency_penalty=0.1,
                    presence_penalty=0.1,
                    response_format={"type": "text"}
                )
                return response.choices[0].message.content
            else:
                import requests
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 3000,
                    "stream": False
                }
                response = requests.post(f"{self.base_url}/chat/completions", json=payload)
                return response.json()["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"Error generating study plan: {e}")
            return "Mi dispiace, non ho potuto generare il piano di studio. Riprova più tardi."