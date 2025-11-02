import openai
import os
from typing import List, Dict, Any, Optional
import json
from dotenv import load_dotenv
from datetime import datetime
import logging

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelli OpenAI disponibili con le loro caratteristiche (solo modelli esistenti)
OPENAI_MODELS = {
    "gpt-4o": {
        "name": "GPT-4 Omni",
        "context_window": 128000,
        "max_tokens": 4096,
        "description": "Modello più recente e versatile, eccellente per testo, codice e ragionamento",
        "use_cases": ["chat", "quiz", "study_plans", "content_analysis"],
        "cost_per_1k_tokens": {"input": 0.005, "output": 0.015}
    },
    "gpt-4o-mini": {
        "name": "GPT-4 Omni Mini",
        "context_window": 128000,
        "max_tokens": 16384,
        "description": "Versione più economica di GPT-4o, veloce e capace",
        "use_cases": ["chat", "quick_responses", "simple_quiz"],
        "cost_per_1k_tokens": {"input": 0.00015, "output": 0.0006}
    },
    "gpt-4-turbo": {
        "name": "GPT-4 Turbo",
        "context_window": 128000,
        "max_tokens": 4096,
        "description": "Modello potente con conoscenza aggiornata",
        "use_cases": ["complex_reasoning", "quiz", "study_plans"],
        "cost_per_1k_tokens": {"input": 0.01, "output": 0.03}
    },
    "gpt-4": {
        "name": "GPT-4",
        "context_window": 8192,
        "max_tokens": 4096,
        "description": "Modello GPT-4 standard per task complessi",
        "use_cases": ["complex_reasoning", "detailed_analysis"],
        "cost_per_1k_tokens": {"input": 0.03, "output": 0.06}
    },
    "gpt-3.5-turbo": {
        "name": "GPT-3.5 Turbo",
        "context_window": 16385,
        "max_tokens": 4096,
        "description": "Modello veloce ed economico per task semplici",
        "use_cases": ["basic_chat", "simple_quiz"],
        "cost_per_1k_tokens": {"input": 0.0005, "output": 0.0015}
    }
}

# Modelli locali comuni (Ollama/LM Studio) con le loro caratteristiche
LOCAL_MODELS = {
    # Modelli Ollama popolari
    "llama3.1:8b": {
        "name": "Llama 3.1 8B",
        "context_window": 128000,
        "max_tokens": 4096,
        "description": "Modello Meta di 8 miliardi di parametri, eccellente per italiano",
        "provider": "ollama",
        "use_cases": ["chat", "quiz", "study_plans"],
        "recommended_vram": "8GB"
    },
    "llama3.1:70b": {
        "name": "Llama 3.1 70B",
        "context_window": 128000,
        "max_tokens": 4096,
        "description": "Modello Meta di 70 miliardi di parametri, molto potente",
        "provider": "ollama",
        "use_cases": ["complex_reasoning", "study_plans", "detailed_analysis"],
        "recommended_vram": "24GB"
    },
    "qwen2.5:7b": {
        "name": "Qwen2.5 7B",
        "context_window": 32768,
        "max_tokens": 8192,
        "description": "Modello Alibaba ottimo per multilingua e codice",
        "provider": "ollama",
        "use_cases": ["chat", "coding", "quiz"],
        "recommended_vram": "8GB"
    },
    "mistral:7b": {
        "name": "Mistral 7B",
        "context_window": 32768,
        "max_tokens": 4096,
        "description": "Modello francese efficiente e veloce",
        "provider": "ollama",
        "use_cases": ["chat", "quick_responses"],
        "recommended_vram": "6GB"
    },
    "codellama:7b": {
        "name": "Code Llama 7B",
        "context_window": 16384,
        "max_tokens": 4096,
        "description": "Specializzato in programmazione e codice",
        "provider": "ollama",
        "use_cases": ["coding", "technical_explanations"],
        "recommended_vram": "8GB"
    },
    # Modelli LM Studio compatibili
    "thebloke/llama-2-13b-chat-ggml": {
        "name": "Llama 2 13B Chat",
        "context_window": 4096,
        "max_tokens": 2048,
        "description": "Modello Llama 2 ottimizzato per chat",
        "provider": "lmstudio",
        "use_cases": ["chat", "basic_quiz"],
        "recommended_vram": "8GB"
    },
    "thebloke/mistral-7b-instruct-v0.2-gguf": {
        "name": "Mistral 7B Instruct",
        "context_window": 4096,
        "max_tokens": 2048,
        "description": "Mistral ottimizzato per istruzioni",
        "provider": "lmstudio",
        "use_cases": ["chat", "quiz"],
        "recommended_vram": "6GB"
    }
}

# Configurazioni predefinite per i provider locali
LOCAL_PROVIDER_CONFIGS = {
    "ollama": {
        "default_url": "http://localhost:11434/v1",
        "health_endpoint": "/api/tags",
        "list_models_endpoint": "/api/tags",
        "chat_endpoint": "/v1/chat/completions",
        "supports_streaming": True,
        "timeout": 60.0
    },
    "lmstudio": {
        "default_url": "http://localhost:1234/v1",
        "health_endpoint": "/health",
        "list_models_endpoint": "/v1/models",
        "chat_endpoint": "/v1/chat/completions",
        "supports_streaming": True,
        "timeout": 120.0
    }
}

class LocalModelManager:
    """Gestisce l'interazione con modelli locali (Ollama/LM Studio)"""

    def __init__(self, provider: str, base_url: str):
        self.provider = provider.lower()
        self.base_url = base_url.rstrip('/')
        self.config = LOCAL_PROVIDER_CONFIGS.get(self.provider, {})
        self.timeout = self.config.get("timeout", 60.0)

    async def check_connection(self) -> bool:
        """Verifica se il provider locale è accessibile"""
        try:
            import requests
            health_url = f"{self.base_url}{self.config.get('health_endpoint', '/health')}"
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection check failed for {self.provider}: {e}")
            return False

    async def list_available_models(self) -> List[str]:
        """Elenca i modelli disponibili dal provider locale"""
        try:
            import requests
            list_url = f"{self.base_url}{self.config.get('list_models_endpoint', '/api/tags')}"
            response = requests.get(list_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if self.provider == "ollama":
                    return [model["name"] for model in data.get("models", [])]
                elif self.provider == "lmstudio":
                    return [model["id"] for model in data.get("data", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to list models for {self.provider}: {e}")
            return []

    async def test_model(self, model_name: str) -> bool:
        """Testa se un modello specifico funziona correttamente"""
        try:
            import requests
            chat_url = f"{self.base_url}{self.config.get('chat_endpoint', '/v1/chat/completions')}"
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10,
                "stream": False
            }
            response = requests.post(chat_url, json=payload, timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Model test failed for {model_name}: {e}")
            return False

class ModelSelector:
    """Helper class per selezionare il modello migliore in base al task e al budget"""

    @staticmethod
    def select_model(task_type: str, budget_conscious: bool = False, context_size: int = 1000, model_type: str = "openai") -> str:
        """
        Seleziona il modello migliore in base al tipo di task

        Args:
            task_type: Tipo di task ('chat', 'quiz', 'study_plan', 'complex_reasoning')
            budget_conscious: Se True, preferisce modelli più economici
            context_size: Dimensione del contesto richiesto
            model_type: "openai" o "local"

        Returns:
            Nome del modello consigliato
        """
        if model_type == "openai":
            if budget_conscious:
                if context_size <= 16000:
                    return "gpt-3.5-turbo"
                return "gpt-4o-mini"

            # Selezione basata sulle prestazioni
            if task_type in ["study_plan", "complex_reasoning"]:
                return "gpt-4o"
            elif task_type == "quiz":
                return "gpt-4o-mini"
            else:  # chat
                return "gpt-4o"
        else:  # modeli locali
            # Raccomandazioni per modelli locali basate sulle performance
            if budget_conscious:
                return "mistral:7b"  # Più leggero e veloce

            if task_type in ["study_plan", "complex_reasoning"]:
                return "llama3.1:70b"  # Più potente se disponibile
            elif task_type == "quiz":
                return "llama3.1:8b"  # Buon bilanciamento
            else:  # chat
                return "llama3.1:8b"  # Generale purpose

    @staticmethod
    def get_model_info(model_name: str, model_type: str = "openai") -> Dict[str, Any]:
        """Ottiene informazioni su un modello specifico"""
        if model_type == "openai":
            return OPENAI_MODELS.get(model_name, {})
        else:
            return LOCAL_MODELS.get(model_name, {})

class LLMService:
    def __init__(self):
        self.client = None
        self.model_type = os.getenv("LLM_TYPE", "openai")  # "openai", "ollama", "lmstudio"
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.budget_mode = os.getenv("BUDGET_MODE", "false").lower() == "true"
        self.local_manager = None
        self.setup_client()
        self.model_info = OPENAI_MODELS.get(self.default_model, OPENAI_MODELS["gpt-4o"])

    def setup_client(self):
        if self.model_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

            if not api_key:
                raise ValueError("Chiave API OpenAI non trovata nelle variabili d'ambiente")

            try:
                self.client = openai.OpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    timeout=30.0,  # Timeout di 30 secondi
                    max_retries=3  # Massimo 3 tentativi
                )
                logger.info(f"Client OpenAI inizializzato con base URL: {base_url}")
            except Exception as e:
                logger.error(f"Errore nell'inizializzazione del client OpenAI: {e}")
                raise

        elif self.model_type in ["ollama", "lmstudio"]:
            # Per provider locali
            base_url = os.getenv("LOCAL_LLM_URL",
                LOCAL_PROVIDER_CONFIGS[self.model_type]["default_url"])
            self.model = os.getenv("LOCAL_LLM_MODEL", "llama3.1:8b" if self.model_type == "ollama" else "thebloke/mistral-7b-instruct-v0.2-gguf")
            self.local_manager = LocalModelManager(self.model_type, base_url)
            logger.info(f"Manager per {self.model_type} inizializzato con URL: {base_url}")

        else:
            # Legacy local LLM configuration
            self.base_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
            self.model = os.getenv("LOCAL_LLM_MODEL", "llama3.1")
            self.model_type = "local"
            logger.warning("Using legacy local LLM configuration. Consider using 'ollama' or 'lmstudio' type.")

    async def get_available_models(self) -> Dict[str, Any]:
        """Restituisce la lista dei modelli disponibili con le loro caratteristiche"""
        result = {
            "current_model": self.default_model,
            "budget_mode": self.budget_mode,
            "model_type": self.model_type
        }

        if self.model_type == "openai":
            result["models"] = OPENAI_MODELS
        elif self.model_type in ["ollama", "lmstudio"] and self.local_manager:
            # Prima controlla la connessione
            is_connected = await self.local_manager.check_connection()
            result["local_connection"] = is_connected

            if is_connected:
                # Ottieni i modelli disponibili dal provider
                available_models = await self.local_manager.list_available_models()
                # Combina con i modelli predefiniti
                local_models = LOCAL_MODELS.copy()
                for model in available_models:
                    if model not in local_models:
                        local_models[model] = {
                            "name": model,
                            "context_window": 4096,  # Default
                            "max_tokens": 2048,      # Default
                            "description": f"Modello {model} disponibile localmente",
                            "provider": self.model_type,
                            "use_cases": ["chat"],
                            "recommended_vram": "Unknown"
                        }
                result["models"] = local_models
                result["available_models"] = available_models
            else:
                result["models"] = LOCAL_MODELS
                result["available_models"] = []
                result["error"] = f"Connessione con {self.model_type} non riuscita"
        else:
            # Legacy mode o fallback
            result["models"] = LOCAL_MODELS

        return result

    async def set_model(self, model_name: str) -> bool:
        """Cambia il modello corrente"""
        if self.model_type == "openai":
            if model_name in OPENAI_MODELS:
                self.default_model = model_name
                self.model_info = OPENAI_MODELS[model_name]
                logger.info(f"Modello OpenAI cambiato in: {model_name}")
                return True
        elif self.model_type in ["ollama", "lmstudio"] and self.local_manager:
            # Testa se il modello funziona
            if await self.local_manager.test_model(model_name):
                self.model = model_name
                self.model_info = LOCAL_MODELS.get(model_name, {
                    "name": model_name,
                    "context_window": 4096,
                    "max_tokens": 2048,
                    "description": f"Modello {model_name}",
                    "provider": self.model_type
                })
                logger.info(f"Modello locale cambiato in: {model_name}")
                return True
            else:
                logger.warning(f"Il modello {model_name} non è disponibile o non funziona")
                return False
        return False

    def set_budget_mode(self, enabled: bool):
        """Abilita/disabilita la modalità budget"""
        self.budget_mode = enabled
        logger.info(f"Modalità budget: {'abilitata' if enabled else 'disabilitata'}")

    async def test_local_connection(self) -> Dict[str, Any]:
        """Testa la connessione con il provider locale"""
        if self.local_manager:
            is_connected = await self.local_manager.check_connection()
            available_models = []
            if is_connected:
                available_models = await self.local_manager.list_available_models()

            return {
                "connected": is_connected,
                "provider": self.model_type,
                "url": self.local_manager.base_url,
                "available_models": available_models
            }
        else:
            return {
                "connected": False,
                "provider": "none",
                "url": None,
                "available_models": []
            }

    async def generate_response(self, query: str, context: Dict[str, Any], course_id: str) -> str:
        """Generate a tutoring response based on query and context"""

        context_text = context.get("text", "")
        sources = context.get("sources", [])
        context_size = len(context_text)

        # Seleziona il modello migliore in base al contesto
        if self.model_type == "openai":
            model_to_use = ModelSelector.select_model(
                task_type="chat",
                budget_conscious=self.budget_mode,
                context_size=context_size,
                model_type="openai"
            )
        elif self.model_type in ["ollama", "lmstudio"]:
            # Usa il modello configurato ma seleziona il migliore se necessario
            recommended_model = ModelSelector.select_model(
                task_type="chat",
                budget_conscious=self.budget_mode,
                context_size=context_size,
                model_type="local"
            )
            # Usa il modello raccomandato se è disponibile, altrimenti usa quello configurato
            if self.local_manager:
                available_models = await self.local_manager.list_available_models()
                if recommended_model in available_models:
                    model_to_use = recommended_model
                else:
                    model_to_use = self.model
            else:
                model_to_use = self.model
        else:
            model_to_use = self.model

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
                # Verifica se il modello ha abbastanza contesto
                model_info = OPENAI_MODELS.get(model_to_use)
                if model_info and context_size > model_info["context_window"] * 0.8:
                    logger.warning(f"Context size ({context_size}) close to model limit ({model_info['context_window']})")
                    # Tronca il contesto se necessario
                    max_context = int(model_info["context_window"] * 0.7)
                    context_text = context_text[-max_context:]
                    system_prompt = system_prompt.replace(
                        f"{context.get('text', '')}",
                        context_text
                    )

                # API OpenAI più recente con parametri avanzati
                response = self.client.chat.completions.create(
                    model=model_to_use,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    temperature=0.7,
                    max_tokens=min(1500, model_info["max_tokens"] if model_info else 1500),
                    top_p=0.9,
                    frequency_penalty=0.2,
                    presence_penalty=0.1,
                    response_format={"type": "text"}
                )

                # Log per monitoraggio costi
                usage = response.usage
                if usage:
                    model_info = OPENAI_MODELS.get(model_to_use)
                    if model_info:
                        cost = (usage.prompt_tokens * model_info["cost_per_1k_tokens"]["input"] / 1000 +
                               usage.completion_tokens * model_info["cost_per_1k_tokens"]["output"] / 1000)
                        logger.info(f"API call - Model: {model_to_use}, Tokens: {usage.total_tokens}, Cost: ${cost:.4f}")

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

        except openai.RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            return "Mi dispiace, ho raggiunto il limite di richieste. Riprova tra qualche istante."
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return "Mi dispiace, c'è stato un problema con il servizio. Riprova più tardi."
        except Exception as e:
            logger.error(f"Errore nella generazione della risposta: {e}")
            return "Mi dispiace, ho riscontrato un problema nell'elaborare la tua domanda. Riprova più tardi."

    async def generate_quiz(self, course_id: str, topic: str = None, difficulty: str = "medium", num_questions: int = 5) -> Dict[str, Any]:
        """Generate quiz questions based on course material"""

        # Seleziona il modello migliore per la generazione di quiz
        if self.model_type == "openai":
            model_to_use = ModelSelector.select_model(
                task_type="quiz",
                budget_conscious=self.budget_mode,
                context_size=2000
            )
        else:
            model_to_use = self.model

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

        Restituisci il risultato in formato JSON con questa struttura:
        {{
          "title": "Titolo del quiz",
          "difficulty": "{difficulty}",
          "questions": [
            {{
              "question": "Testo della domanda",
              "options": {{
                "A": "Opzione A",
                "B": "Opzione B",
                "C": "Opzione C",
                "D": "Opzione D"
              }},
              "correct": "A",
              "explanation": "Spiegazione della risposta corretta"
            }}
          ]
        }}
        """

        try:
            if self.model_type == "openai":
                response = self.client.chat.completions.create(
                    model=model_to_use,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Crea un quiz per il corso {course_id}"}
                    ],
                    temperature=0.7,
                    max_tokens=2500,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content

                # Log per monitoraggio costi
                usage = response.usage
                if usage:
                    model_info = OPENAI_MODELS.get(model_to_use)
                    if model_info:
                        cost = (usage.prompt_tokens * model_info["cost_per_1k_tokens"]["input"] / 1000 +
                               usage.completion_tokens * model_info["cost_per_1k_tokens"]["output"] / 1000)
                        logger.info(f"Quiz generation - Model: {model_to_use}, Tokens: {usage.total_tokens}, Cost: ${cost:.4f}")
            else:
                import requests
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Crea un quiz per il corso {course_id}"}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2500,
                    "stream": False
                }
                response = requests.post(f"{self.base_url}/v1/chat/completions", json=payload)
                content = response.json()["choices"][0]["message"]["content"]

            # Parse JSON response
            try:
                quiz_data = json.loads(content)
                # Valida la struttura del quiz
                if "questions" not in quiz_data:
                    raise ValueError("Invalid quiz structure")
                return quiz_data
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse quiz JSON: {e}")
                # Fallback if JSON parsing fails
                return {
                    "title": f"Quiz - {course_id}",
                    "difficulty": difficulty,
                    "questions": [
                        {
                            "question": content[:200] + "...",
                            "options": {"A": "Opzione A", "B": "Opzione B", "C": "Opzione C", "D": "Opzione D"},
                            "correct": "A",
                            "explanation": "Spiegazione in elaborazione"
                        }
                    ]
                }

        except openai.RateLimitError as e:
            logger.error(f"Rate limit exceeded in quiz generation: {e}")
            return {
                "error": "Limite di richieste raggiunto. Riprova tra qualche istante.",
                "questions": []
            }
        except openai.APIError as e:
            logger.error(f"OpenAI API error in quiz generation: {e}")
            return {
                "error": "Problema con il servizio. Riprova più tardi.",
                "questions": []
            }
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
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