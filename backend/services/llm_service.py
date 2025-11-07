import openai
import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import json
from dotenv import load_dotenv
from datetime import datetime
import logging
import requests
import re

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelli ZAI (GLM) disponibili con le loro caratteristiche
ZAI_MODELS = {
    "glm-4.6": {
        "name": "GLM-4.6",
        "context_window": 200000,
        "max_tokens": 8192,
        "description": "Modello flagship ZAI per reasoning, coding e agentic tasks con thinking capabilities",
        "use_cases": ["complex_reasoning", "coding", "study_plans", "content_analysis", "agentic_tasks", "slide_creation"],
        "cost_per_1k_tokens": {"input": 0.003, "output": 0.012},
        "supports_agents": True,
        "supports_thinking": True
    },
    "4.6": {
        "name": "ZAI-4.6",
        "context_window": 200000,
        "max_tokens": 8192,
        "description": "Modello flagship ZAI per reasoning, coding e agentic tasks con thinking capabilities",
        "use_cases": ["complex_reasoning", "coding", "study_plans", "content_analysis", "agentic_tasks", "slide_creation"],
        "cost_per_1k_tokens": {"input": 0.003, "output": 0.012},
        "supports_agents": True,
        "supports_thinking": True
    },
    "glm-4.5": {
        "name": "GLM-4.5",
        "context_window": 128000,
        "max_tokens": 4096,
        "description": "Modello avanzato ZAI per task complessi con buone capacità di ragionamento",
        "use_cases": ["complex_reasoning", "study_plans", "content_analysis", "slide_creation"],
        "cost_per_1k_tokens": {"input": 0.002, "output": 0.008},
        "supports_agents": True,
        "supports_thinking": False
    },
    "glm-4.5v": {
        "name": "GLM-4.5V",
        "context_window": 128000,
        "max_tokens": 4096,
        "description": "Modello GLM-4.5 con capacità vision per analisi di immagini e documenti",
        "use_cases": ["visual_analysis", "document_analysis", "content_analysis", "slide_creation"],
        "cost_per_1k_tokens": {"input": 0.0025, "output": 0.01},
        "supports_agents": False,
        "supports_thinking": False,
        "supports_vision": True
    },
    "glm-4.5-air": {
        "name": "GLM-4.5 Air",
        "context_window": 128000,
        "max_tokens": 4096,
        "description": "Versione ottimizzata di GLM-4.5 per performance e costi ridotti",
        "use_cases": ["chat", "quiz", "quick_responses", "basic_analysis"],
        "cost_per_1k_tokens": {"input": 0.001, "output": 0.004},
        "supports_agents": False,
        "supports_thinking": False
    },
    "glm-4": {
        "name": "GLM-4",
        "context_window": 128000,
        "max_tokens": 4096,
        "description": "Modello GLM-4 standard per task generici",
        "use_cases": ["chat", "quiz", "basic_analysis"],
        "cost_per_1k_tokens": {"input": 0.0015, "output": 0.006},
        "supports_agents": False,
        "supports_thinking": False
    },
    "glm-4.1v": {
        "name": "GLM-4.1V",
        "context_window": 128000,
        "max_tokens": 4096,
        "description": "Modello GLM-4 con capacità vision per analisi visiva",
        "use_cases": ["visual_analysis", "document_analysis"],
        "cost_per_1k_tokens": {"input": 0.0018, "output": 0.007},
        "supports_agents": False,
        "supports_thinking": False,
        "supports_vision": True
    }
}

# Configurazioni per ZAI API
ZAI_CONFIG = {
    "base_url": "https://api.z.ai/api/paas/v4",
    "chat_endpoint": "/chat/completions",
    "models_endpoint": "/models",
    "timeout": float(os.getenv("ZAI_TIMEOUT", "60.0")),
    "max_retries": 3,
    "supports_streaming": True,
    "supports_agents": True
}

ZAI_AGENT_API_URL = "https://api.z.ai/api/v1"

# Modelli OpenAI disponibili con le loro caratteristiche
OPENAI_MODELS = {
    "gpt-5": {
        "name": "GPT-5",
        "context_window": 400000,
        "max_tokens": 8192,
        "description": "Modello flagship per coding, reasoning e agentic tasks con context window esteso",
        "use_cases": ["complex_reasoning", "coding", "study_plans", "content_analysis", "agentic_tasks"],
        "cost_per_1k_tokens": {"input": 0.025, "output": 0.125}
    },
    "gpt-5-pro": {
        "name": "GPT-5 Pro",
        "context_window": 400000,
        "max_tokens": 8192,
        "description": "Versione GPT-5 con compute extra per thinking harder e risposte più accurate",
        "use_cases": ["complex_reasoning", "detailed_analysis", "coding", "research"],
        "cost_per_1k_tokens": {"input": 0.075, "output": 0.375}
    },
    "gpt-5-mini": {
        "name": "GPT-5 Mini",
        "context_window": 200000,
        "max_tokens": 16384,
        "description": "Versione economica di GPT-5, veloce e capace per task quotidiani",
        "use_cases": ["chat", "quick_responses", "simple_quiz", "basic_analysis"],
        "cost_per_1k_tokens": {"input": 0.001, "output": 0.005}
    },
    "gpt-5-nano": {
        "name": "GPT-5 Nano",
        "context_window": 100000,
        "max_tokens": 16384,
        "description": "Versione ultraleggera di GPT-5 per task semplici e rapide",
        "use_cases": ["chat", "quick_responses", "simple_quiz"],
        "cost_per_1k_tokens": {"input": 0.0001, "output": 0.0005}
    },
    "gpt-5-codex": {
        "name": "GPT-5 Codex",
        "context_window": 200000,
        "max_tokens": 8192,
        "description": "Modello GPT-5 specializzato per programmazione e sviluppo software",
        "use_cases": ["coding", "debugging", "code_review", "technical_analysis"],
        "cost_per_1k_tokens": {"input": 0.01, "output": 0.05}
    },
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

class ZAIModelManager:
    """Gestisce l'interazione con i modelli ZAI (GLM)"""

    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or ZAI_CONFIG["base_url"]
        self.config = ZAI_CONFIG
        self.timeout = self.config.get("timeout", 60.0)
        self.max_retries = self.config.get("max_retries", 3)

    async def check_connection(self) -> bool:
        """Verifica se l'API ZAI è accessibile"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            # Usa un endpoint semplice per verificare la connessione
            test_url = f"{self.base_url}/models"
            response = requests.get(test_url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ZAI connection check failed: {e}")
            return False

    async def list_available_models(self) -> List[str]:
        """Elenca i modelli ZAI disponibili"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Estrai i nomi dei modelli dalla risposta
                return list(ZAI_MODELS.keys())
            return []
        except Exception as e:
            logger.error(f"Failed to list ZAI models: {e}")
            return []

    async def test_model(self, model_name: str) -> bool:
        """Testa se un modello specifico ZAI funziona correttamente"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10,
                "stream": False
            }
            response = requests.post(
                f"{self.base_url}{self.config['chat_endpoint']}",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ZAI model test failed for {model_name}: {e}")
            return False

    async def chat_completion(self, model_name: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Esegue una chat completion con i modelli ZAI con retry logic"""
        import time

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 1500),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": kwargs.get("stream", False)
        }

        # Aggiungi parametri specifici per ZAI
        # Note: thinking parameter not supported in current API version

        max_retries = self.config.get("max_retries", 3)
        base_delay = 1.0  # Base delay in seconds

        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}{self.config['chat_endpoint']}",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"ZAI API error: {response.status_code} - {response.text}")
                    # Don't retry on client errors (4xx)
                    if 400 <= response.status_code < 500:
                        raise Exception(f"ZAI API client error: {response.status_code} - {response.text}")

                    # For server errors, retry with backoff
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"ZAI API request failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(f"ZAI API request failed after {max_retries + 1} attempts: {response.status_code}")

            except requests.exceptions.Timeout as e:
                logger.warning(f"ZAI API timeout (attempt {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"ZAI API timed out after {max_retries + 1} attempts")
                    raise Exception(f"ZAI API timeout after {max_retries + 1} attempts: {e}")

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"ZAI API connection error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"ZAI API connection failed after {max_retries + 1} attempts")
                    raise Exception(f"ZAI API connection failed after {max_retries + 1} attempts: {e}")

            except Exception as e:
                logger.error(f"ZAI chat completion failed: {e}")
                if attempt < max_retries and not isinstance(e, requests.exceptions.RequestException):
                    # Retry for non-request exceptions
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Unexpected error (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    raise

        # This should never be reached, but just in case
        raise Exception("ZAI chat completion failed: Maximum retries exceeded")

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
            task_type: Tipo di task ('chat', 'quiz', 'study_plan', 'complex_reasoning', 'slide_creation')
            budget_conscious: Se True, preferisce modelli più economici
            context_size: Dimensione del contesto richiesto
            model_type: "openai", "zai", o "local"

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
        elif model_type == "zai":
            # Selezione per modelli ZAI (GLM)
            if budget_conscious:
                if task_type == "quiz":
                    return "glm-4.5-air"  # Più economico per quiz
                return "glm-4"  # Economico per task generici

            # Selezione basata sulle prestazioni per ZAI
            if task_type in ["slide_creation", "complex_reasoning", "coding"]:
                return "glm-4.6"  # Migliore per task complessi e agenti
            elif task_type in ["study_plan", "content_analysis"]:
                return "glm-4.5"  # Ottimo per analisi e piani
            elif task_type == "quiz":
                return "glm-4.5-air"  # Bilanciato per quiz
            else:  # chat
                return "glm-4.5"  # Buon compromesso
        else:  # modelli locali
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
        elif model_type == "zai":
            return ZAI_MODELS.get(model_name, {})
        else:
            return LOCAL_MODELS.get(model_name, {})

class LLMService:
    def __init__(self):
        self.client = None
        self.model_type = os.getenv("LLM_TYPE", "zai")  # "openai", "zai", "ollama", "lmstudio"
        self.default_model = os.getenv("ZAI_MODEL", "glm-4.6")
        self.budget_mode = os.getenv("BUDGET_MODE", "false").lower() == "true"
        self.local_manager = None
        self.zai_manager = None
        self.setup_client()

        # Setup model info based on type
        if self.model_type == "zai":
            self.model_info = ZAI_MODELS.get(self.default_model, ZAI_MODELS["glm-4.6"])
        elif self.model_type == "openai":
            self.model_info = OPENAI_MODELS.get(self.default_model, OPENAI_MODELS["gpt-4o"])
        else:
            self.model_info = LOCAL_MODELS.get(self.default_model, {"name": self.default_model})

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

        elif self.model_type == "zai":
            # Setup per ZAI Model API
            api_key = os.getenv("ZAI_API_KEY", "53a0e2804093424e97a175b54a289f5f.ZMphW59IaVT7eAya")
            base_url = os.getenv("ZAI_BASE_URL", ZAI_CONFIG["base_url"])

            if not api_key:
                logger.warning("Chiave API ZAI non trovata. Il servizio ZAI non sarà disponibile.")
                self.model_type = "openai"  # Fallback
                self.setup_client()  # Retry con OpenAI
                return

            try:
                self.zai_manager = ZAIModelManager(api_key, base_url)
                # Imposta il modello di default per ZAI
                self.default_model = os.getenv("ZAI_MODEL", "glm-4.6")
                logger.info(f"Manager ZAI inizializzato con modello: {self.default_model}")
            except Exception as e:
                logger.error(f"Errore nell'inizializzazione del manager ZAI: {e}")
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
        elif self.model_type == "zai" and self.zai_manager:
            # Prima controlla la connessione
            is_connected = await self.zai_manager.check_connection()
            result["zai_connection"] = is_connected

            if is_connected:
                # Ottieni i modelli disponibili (tutti i modelli ZAI sono disponibili)
                available_models = await self.zai_manager.list_available_models()
                result["models"] = ZAI_MODELS
                result["available_models"] = available_models
            else:
                result["models"] = ZAI_MODELS
                result["available_models"] = []
                result["error"] = "Connessione con ZAI non riuscita"
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
        elif self.model_type == "zai" and self.zai_manager:
            # Testa se il modello ZAI funziona
            if await self.zai_manager.test_model(model_name):
                self.default_model = model_name
                self.model_info = ZAI_MODELS.get(model_name, {
                    "name": model_name,
                    "context_window": 128000,
                    "max_tokens": 4096,
                    "description": f"Modello ZAI {model_name}",
                    "provider": "zai"
                })
                logger.info(f"Modello ZAI cambiato in: {model_name}")
                return True
            else:
                logger.warning(f"Il modello ZAI {model_name} non è disponibile o non funziona")
                return False
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

    async def test_zai_connection(self) -> Dict[str, Any]:
        """Testa la connessione con ZAI API"""
        if self.zai_manager:
            is_connected = await self.zai_manager.check_connection()
            available_models = []
            if is_connected:
                available_models = await self.zai_manager.list_available_models()

            return {
                "connected": is_connected,
                "provider": "zai",
                "url": self.zai_manager.base_url,
                "available_models": available_models
            }
        else:
            return {
                "connected": False,
                "provider": "none",
                "url": None,
                "available_models": []
            }

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
        elif self.model_type == "zai":
            # Usa il modello configurato ma seleziona il migliore se necessario
            recommended_model = ModelSelector.select_model(
                task_type="chat",
                budget_conscious=self.budget_mode,
                context_size=context_size,
                model_type="zai"
            )
            # Usa il modello raccomandato se è disponibile, altrimenti usa quello configurato
            model_to_use = recommended_model if recommended_model in ZAI_MODELS else self.default_model
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
            elif self.model_type == "zai" and self.zai_manager:
                # Verifica se il modello ZAI ha abbastanza contesto
                model_info = ZAI_MODELS.get(model_to_use)
                if model_info and context_size > model_info["context_window"] * 0.8:
                    logger.warning(f"Context size ({context_size}) close to ZAI model limit ({model_info['context_window']})")
                    # Tronca il contesto se necessario
                    max_context = int(model_info["context_window"] * 0.7)
                    context_text = context_text[-max_context:]
                    system_prompt = system_prompt.replace(
                        f"{context.get('text', '')}",
                        context_text
                    )

                # API ZAI
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]

                response = await self.zai_manager.chat_completion(
                    model_name=model_to_use,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=min(1500, model_info["max_tokens"] if model_info else 1500)
                )

                # Log per monitoraggio costi (stimato)
                if response and "choices" in response:
                    logger.info(f"ZAI API call - Model: {model_to_use}, Response received")
                    # Log dei costi per ZAI
                    if model_info:
                        logger.info(f"ZAI Model: {model_to_use}, Estimated cost: Low (ZAI pricing)")

                return response["choices"][0]["message"]["content"] if response and "choices" in response else "Risposta non disponibile"
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
            # Handle ZAI API errors
            if "ZAI" in str(e) or (self.model_type == "zai" and "429" in str(e)):
                logger.error(f"ZAI API error: {e}")
                if "429" in str(e):
                    return "Mi dispiace, ho raggiunto il limite di richieste ZAI. Riprova tra qualche istante."
                else:
                    return "Mi dispiace, c'è stato un problema con il servizio ZAI. Riprova più tardi."
            else:
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

    async def generate_slides_with_zai_agent(self, course_id: str, topic: str, num_slides: int = 10, slide_style: str = "modern", audience: str = "university") -> Dict[str, Any]:
        """
        Genera slide utilizzando gli agenti ZAI con capacità avanzate di creazione contenuti

        Args:
            course_id: ID del corso
            topic: Argomento principale delle slide
            num_slides: Numero di slide da generare
            slide_style: Stile delle slide (modern, academic, creative, minimal)
            audience: Tipo di pubblico (university, corporate, general)

        Returns:
            Dict con le slide generate e metadati
        """
        if self.model_type != "zai" or not self.zai_manager:
            logger.warning("ZAI agents not available, falling back to regular slide generation")
            return {"error": "ZAI not available", "slides": []}

        # Per gli agenti ZAI, non specificare un modello particolare
        # L'agente slides_glm_agent userà il modello appropriato internamente
        model_to_use = None

        system_prompt = f"""
        Sei un agente esperto nella creazione di presentazioni accademiche e didattiche.
        Il tuo compito è creare una presentazione completa e professionale su {topic} per un corso universitario.

        CONTESTO:
        - Corso: {course_id}
        - Argomento: {topic}
        - Numero slide: {num_slides}
        - Stile: {slide_style}
        - Pubblico: {audience}

        CAPACITÀ AGENTICHE:
        - Analizza la struttura ottimale per una presentazione accademica
        - Crea contenuti originali e ben strutturati
        - Genera elementi visivi e diagrammi descrittivi
        - Assicura coerenza narrativa tra le slide
        - Adatta il contenuto al livello universitario

        STRUTTURA RICHIESTA:
        1. Slide 1: Titolo e sottotitolo impattanti
        2. Slide 2: Obiettivi di apprendimento e agenda
        3. Slide 3-n: Contenuti principali con progressione logica
        4. Penultima slide: Riepilogo e punti chiave
        5. Ultima slide: Conclusioni e spunti di riflessione

        FORMATO JSON RICHIESTO:
        {{
            "title": "Titolo Presentazione",
            "subtitle": "Sottotitolo descrittivo",
            "theme": "{slide_style}",
            "total_slides": {num_slides},
            "slides": [
                {{
                    "id": 1,
                    "type": "title",
                    "title": "Titolo Slide",
                    "content": ["Contenuto principale"],
                    "visual_elements": ["descrizione elementi visivi"],
                    "notes": "Note per il relatore"
                }},
                {{
                    "id": 2,
                    "type": "content",
                    "title": "Titolo Contenuto",
                    "content": ["punto 1", "punto 2", "punto 3"],
                    "visual_elements": ["tipo di diagramma suggerito"],
                    "notes": "note aggiuntive"
                }}
            ]
        }}

        IMPORTANTE:
        - Sii originale e accademico
        - Includi esempi pratici quando possibile
        - Suggerisci elementi visivi appropriati
        - Mantieni coerenza e professionalità
        - Adatta il linguaggio al livello universitario
        """

        try:
            user_prompt = f"""
            Crea una presentazione completa su '{topic}' per il corso {course_id}.

            Requisiti specifici:
            - Numero slide: {num_slides}
            - Stile visivo: {slide_style}
            - Target: {audience}
            - Livello: universitario
            - Formato: JSON strutturato

            Utilizza le tue capacità agentiche per analizzare l'argomento e creare una presentazione
            strutturata, informativa e coinvolgente.
            """

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = await self.zai_manager.chat_completion(
                model_name=model_to_use,
                messages=messages,
                temperature=0.8,  # Creatività più alta per la generazione di contenuti
                max_tokens=4000   # Token sufficienti per slide multiple
            )

            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]

                # Prova a parseare il JSON
                try:
                    # Estrai JSON dal content se necessario
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(0)
                        slides_data = json.loads(json_content)
                    else:
                        # Fallback se non trova JSON
                        slides_data = {
                            "title": f"Presentazione: {topic}",
                            "subtitle": f"Corso: {course_id}",
                            "theme": slide_style,
                            "total_slides": num_slides,
                            "slides": [
                                {
                                    "id": 1,
                                    "type": "content",
                                    "title": topic,
                                    "content": [content[:500] + "..."],
                                    "visual_elements": ["testo"],
                                    "notes": "Contenuto generato dall'agente ZAI"
                                }
                            ]
                        }

                    logger.info(f"ZAI agent generated {len(slides_data.get('slides', []))} slides for {topic}")
                    return {
                        "success": True,
                        "model_used": model_to_use,
                        "generation_method": "zai_agent",
                        "slides_data": slides_data,
                        "metadata": {
                            "course_id": course_id,
                            "topic": topic,
                            "style": slide_style,
                            "audience": audience,
                            "generated_at": datetime.now().isoformat()
                        }
                    }

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse ZAI agent JSON response: {e}")
                    # Fallback con contenuto testuale
                    return {
                        "success": True,
                        "model_used": model_to_use,
                        "generation_method": "zai_agent_fallback",
                        "slides_data": {
                            "title": f"Presentazione: {topic}",
                            "subtitle": f"Corso: {course_id}",
                            "theme": slide_style,
                            "total_slides": 1,
                            "slides": [
                                {
                                    "id": 1,
                                    "type": "content",
                                    "title": topic,
                                    "content": [content],
                                    "visual_elements": ["testo"],
                                    "notes": "Contenuto generato dall'agente ZAI (formato testuale)"
                                }
                            ]
                        },
                        "metadata": {
                            "course_id": course_id,
                            "topic": topic,
                            "style": slide_style,
                            "note": "JSON parsing failed, returned as text"
                        }
                    }

            else:
                return {"success": False, "error": "No response from ZAI agent", "slides": []}

        except Exception as e:
            logger.error(f"Error in ZAI agent slide generation: {e}")
            return {
                "success": False,
                "error": f"ZAI agent error: {str(e)}",
                "slides": []
            }

    async def generate_slides_with_glm_slide_agent(
        self,
        course_id: str,
        topic: str,
        content_context: str = "",
        num_slides: int = 10,
        style: str = "modern",
        description: Optional[str] = None,
        include_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Generate rich slides using the Z.AI GLM Slide/Poster Agent.

        Args:
            course_id: ID del corso
            topic: Argomento principale delle slide
            content_context: Contesto aggiuntivo dai documenti del corso
            num_slides: Numero di slide desiderate
            style: Stile delle slide (modern, academic, creative, minimal)
            description: Prompt personalizzato da inviare all'agente
            include_pdf: Se True tenta di ottenere e scaricare il PDF generato

        Returns:
            Dizionario con percorsi, contenuti e metadati della generazione
        """
        if self.model_type != "zai" or not self.zai_manager:
            logger.error("GLM Slide Agent requires ZAI API access")
            return {"success": False, "error": "ZAI API not available", "slides": []}

        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            base_prompt = description.strip() if description else (
                f"Crea una presentazione professionale di {num_slides} slide su '{topic}' "
                f"per il corso '{course_id}' con stile {style}."
            )

            if content_context:
                trimmed_context = content_context.strip()
                if len(trimmed_context) > 600:
                    trimmed_context = f"{trimmed_context[:600].rstrip()}..."
                base_prompt = f"{base_prompt} Usa questo contesto del corso: {trimmed_context}"

            conversation_suffix = f"{timestamp}"
            conversation_id = (
                f"slides_{self._sanitize_for_filename(course_id or 'course', 'course', 24)}_"
                f"{self._sanitize_for_filename(topic, 'topic', 24)}_{conversation_suffix}"
            )

            headers = {
                "Authorization": f"Bearer {self.zai_manager.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "agent_id": "slides_glm_agent",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": base_prompt
                            }
                        ]
                    }
                ],
                "stream": False,
                "conversation_id": conversation_id,
                "request_id": f"req_{conversation_suffix}"
            }

            agent_url = f"{ZAI_AGENT_API_URL}/agents"
            status_code, agent_events, _, agent_error = await asyncio.to_thread(
                self._request_agent_stream,
                agent_url,
                headers,
                payload,
                180
            )

            if status_code != 200 or not agent_events:
                logger.error(
                    "GLM Slide Agent API error: %s - %s",
                    status_code,
                    agent_error or "empty response"
                )
                return {
                    "success": False,
                    "error": f"API Error: {status_code}",
                    "details": agent_error,
                    "slides": []
                }

            agent_data = agent_events[-1] if agent_events else {}

            status_marker = next(
                (evt.get("status") for evt in agent_events if isinstance(evt, dict) and evt.get("status")),
                None
            )

            if status_marker == "failed":
                error_info = next(
                    (evt.get("error") for evt in reversed(agent_events) if isinstance(evt, dict) and evt.get("error")),
                    None
                )
                message = None
                if isinstance(error_info, dict):
                    message = error_info.get("message") or error_info.get("detail")
                elif isinstance(error_info, str):
                    message = error_info
                return {
                    "success": False,
                    "error": message or "GLM Slide Agent failed",
                    "details": error_info,
                    "slides": []
                }

            async_id = next(
                (evt.get("async_id") for evt in agent_events if isinstance(evt, dict) and evt.get("async_id")),
                None
            )

            if status_marker == "pending" and async_id:
                async_result = await self._poll_glm_slide_async_result(
                    headers=headers,
                    async_id=async_id
                )
                if not async_result:
                    return {
                        "success": False,
                        "error": "Slide generation timed out during async polling",
                        "slides": []
                    }
                agent_events.append(async_result)
                agent_data = async_result

            parsed = self._parse_glm_slide_agent_messages(agent_events)
            html_content = self._select_primary_html(parsed)
            structured_data = self._extract_structured_slide_data(parsed)
            pdf_url = parsed["file_urls"][0] if parsed["file_urls"] else None
            image_urls = list(dict.fromkeys(parsed["image_urls"]))

            conversation_id = None
            for evt in reversed(agent_events):
                if isinstance(evt, dict) and evt.get("conversation_id"):
                    conversation_id = evt["conversation_id"]
                    break

            if include_pdf and not pdf_url and conversation_id:
                conversation_payload = {
                    "agent_id": "slides_glm_agent",
                    "conversation_id": conversation_id,
                    "custom_variables": {"include_pdf": True}
                }

                status_code_conv, conversation_events, _, conv_error = await asyncio.to_thread(
                    self._request_agent_stream,
                    f"{ZAI_AGENT_API_URL}/agents/conversation",
                    headers,
                    conversation_payload,
                    180
                )

                if status_code_conv == 200 and conversation_events:
                    conversation_parsed = self._parse_glm_slide_agent_messages(conversation_events)
                    if not html_content:
                        html_content = self._select_primary_html(conversation_parsed)
                    if not structured_data:
                        structured_data = self._extract_structured_slide_data(conversation_parsed)
                    if conversation_parsed["file_urls"]:
                        pdf_url = conversation_parsed["file_urls"][0]
                    if conversation_parsed["image_urls"]:
                        image_urls = list(
                            dict.fromkeys(image_urls + conversation_parsed["image_urls"])
                        )
                else:
                    logger.warning(
                        "GLM Slide Agent conversation fetch failed: %s - %s",
                        status_code_conv,
                        conv_error or "empty response"
                    )

            slides_dir = os.path.join("data", "slides")
            pdf_file_path = None
            html_file_path = None

            if include_pdf and pdf_url:
                try:
                    pdf_response = await asyncio.to_thread(
                        requests.get,
                        pdf_url,
                        timeout=180
                    )
                    if pdf_response.status_code == 200:
                        os.makedirs(slides_dir, exist_ok=True)
                        pdf_filename = f"{self._sanitize_for_filename(topic, 'slides', 40)}_{timestamp}.pdf"
                        pdf_file_path = os.path.join(slides_dir, pdf_filename)
                        with open(pdf_file_path, "wb") as pdf_file:
                            pdf_file.write(pdf_response.content)
                    else:
                        logger.warning(
                            "Failed to download slide PDF: %s - %s",
                            pdf_response.status_code,
                            pdf_response.text
                        )
                except requests.RequestException as download_error:
                    logger.warning("Slide PDF download error: %s", download_error)

            if html_content:
                os.makedirs(slides_dir, exist_ok=True)
                html_filename = f"{self._sanitize_for_filename(topic, 'slides', 40)}_{timestamp}.html"
                html_file_path = os.path.join(slides_dir, html_filename)
                with open(html_file_path, "w", encoding="utf-8") as html_file:
                    html_file.write(html_content)

            if not html_content and parsed["text_fragments"]:
                html_content = "\n".join(parsed["text_fragments"]).strip()

            return {
                "success": True,
                "generation_method": "zai_glm_slide_agent",
                "conversation_id": conversation_id,
                "slide_pdf_url": pdf_url,
                "slide_file_path": pdf_file_path or html_file_path,
                "slide_pdf_path": pdf_file_path,
                "slide_html_path": html_file_path,
                "html_content": html_content,
                "text_fragments": parsed["text_fragments"],
                "image_urls": image_urls,
                "slides_data": structured_data,
                "raw_response": agent_events,
                "metadata": {
                    "course_id": course_id,
                    "topic": topic,
                    "style": style,
                    "num_slides": num_slides,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }

        except requests.RequestException as request_error:
            logger.error("GLM Slide Agent request failed: %s", request_error)
            return {
                "success": False,
                "error": f"Request error: {request_error}",
                "slides": []
            }
        except Exception as exc:
            logger.error("Error in GLM Slide Agent generation: %s", exc)
            return {
                "success": False,
                "error": f"GLM Slide Agent error: {exc}",
                "slides": []
            }

    def _request_agent_stream(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        timeout: int = 120
    ) -> Tuple[int, List[Dict[str, Any]], str, Optional[str]]:
        events: List[Dict[str, Any]] = []
        raw_segments: List[str] = []
        content_type = ""
        error_text: Optional[str] = None

        with requests.post(url, headers=headers, json=payload, stream=True, timeout=timeout) as response:
            status_code = response.status_code
            content_type = response.headers.get("Content-Type", "")

            if status_code != 200:
                try:
                    error_text = response.text[:1000]
                except Exception:
                    error_text = None
                return status_code, events, content_type, error_text

            for raw_line in response.iter_lines(decode_unicode=True):
                if raw_line is None:
                    continue

                line = raw_line.strip()
                if not line:
                    continue

                raw_segments.append(line)

                if line.startswith("data:"):
                    line = line[5:].strip()

                if not line:
                    continue

                if line == "[DONE]":
                    break

                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

            if not events and raw_segments:
                error_text = "\n".join(raw_segments)[:1000]

            return status_code, events, content_type, error_text

    def _parse_glm_slide_agent_messages(self, agent_payload: Any) -> Dict[str, List[Any]]:
        parsed: Dict[str, List[Any]] = {
            "html_fragments": [],
            "text_fragments": [],
            "image_urls": [],
            "file_urls": [],
            "objects": []
        }

        if not agent_payload:
            return parsed

        if isinstance(agent_payload, dict):
            events = [agent_payload]
        elif isinstance(agent_payload, list):
            events = agent_payload
        else:
            return parsed

        for event in events:
            if not isinstance(event, dict):
                continue

            choices = event.get("choices", [])
            if not isinstance(choices, list):
                continue

            for choice in choices:
                if not isinstance(choice, dict):
                    continue

                messages = choice.get("message") or choice.get("messages")
                if isinstance(messages, dict):
                    messages = [messages]
                if not isinstance(messages, list):
                    continue

                for message in messages:
                    if not isinstance(message, dict):
                        continue

                    phase = (message.get("phase") or "").lower()
                    if phase and phase not in {"answer", "final_answer", "tool"}:
                        continue

                    contents = message.get("content", [])
                    if isinstance(contents, dict):
                        contents = [contents]
                    if not isinstance(contents, list):
                        continue

                    for item in contents:
                        if not isinstance(item, dict):
                            continue

                        item_type = item.get("type") or item.get("types")
                        if item_type == "text":
                            text_value = item.get("text")
                            if isinstance(text_value, str) and text_value.strip():
                                parsed["text_fragments"].append(text_value.strip())
                        elif item_type == "object":
                            obj_value = item.get("object") or {}
                            if isinstance(obj_value, dict):
                                parsed["objects"].append(obj_value)
                                output = obj_value.get("output") or obj_value.get("html") or obj_value.get("content")
                                if isinstance(output, str) and output.strip():
                                    parsed["html_fragments"].append(output.strip())
                                elif isinstance(output, dict):
                                    parsed["objects"].append(output)
                        elif item_type == "image_url":
                            image_url = item.get("image_url")
                            if isinstance(image_url, str) and image_url:
                                parsed["image_urls"].append(image_url)
                        elif item_type == "file_url":
                            file_url = item.get("file_url")
                            if isinstance(file_url, str) and file_url:
                                parsed["file_urls"].append(file_url)
                        elif item_type == "url":
                            generic_url = item.get("url")
                            if isinstance(generic_url, str) and generic_url:
                                parsed["file_urls"].append(generic_url)

        return parsed

    def _select_primary_html(self, parsed_payload: Dict[str, List[Any]]) -> Optional[str]:
        html_fragments = parsed_payload.get("html_fragments") or []
        if html_fragments:
            return "\n".join(html_fragments)

        text_fragments = parsed_payload.get("text_fragments") or []
        if text_fragments:
            combined = "\n".join(text_fragments)
            if "<" in combined and ">" in combined:
                return combined
        return None

    def _extract_structured_slide_data(self, parsed_payload: Dict[str, List[Any]]) -> Optional[Dict[str, Any]]:
        for obj in parsed_payload.get("objects", []):
            if not isinstance(obj, dict):
                continue
            output_candidate = obj.get("output") or obj.get("content") or obj
            if isinstance(output_candidate, dict):
                return output_candidate
            if isinstance(output_candidate, str):
                trimmed = output_candidate.strip()
                if trimmed.startswith("{") and trimmed.endswith("}"):
                    try:
                        return json.loads(trimmed)
                    except json.JSONDecodeError:
                        continue
        return None

    def _sanitize_for_filename(self, value: str, fallback: str, max_length: int = 60) -> str:
        if not value:
            return fallback
        sanitized = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
        sanitized = sanitized.strip("_")
        if not sanitized:
            sanitized = fallback
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        return sanitized

    async def _poll_glm_slide_async_result(
        self,
        headers: Dict[str, str],
        async_id: str,
        max_attempts: int = 10,
        delay_seconds: float = 3.0
    ) -> Optional[Dict[str, Any]]:
        polling_url = f"{ZAI_AGENT_API_URL}/agents/get-async-result"
        payload = {
            "agent_id": "slides_glm_agent",
            "async_id": async_id
        }

        for attempt in range(max_attempts):
            response = await asyncio.to_thread(
                requests.post,
                polling_url,
                headers=headers,
                json=payload,
                timeout=120
            )

            if response.status_code != 200:
                logger.error(
                    "Async result polling failed (%s): %s",
                    response.status_code,
                    response.text
                )
                return None

            data = response.json()
            status = (data.get("status") or "").lower()
            if status in {"", "success"}:
                return data
            if status == "failed":
                logger.error("GLM Slide Agent async task failed: %s", data)
                return data

            await asyncio.sleep(delay_seconds)

        logger.error("GLM Slide Agent async polling exceeded maximum attempts")
        return None
