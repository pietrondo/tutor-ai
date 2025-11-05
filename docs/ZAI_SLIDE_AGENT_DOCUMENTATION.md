# Documentazione Interna - ZAI Slide Agent

## 📋 **Panoramica**

Il sistema Tutor-AI utilizza l'agente **`slides_glm_agent`** di Z.AI per generare presentazioni professionali in formato PDF. Questa documentazione descrive l'implementazione, configurazione e best practices per l'utilizzo ottimale dell'agente.

## 🚀 **Architettura del Sistema**

### Componenti Principali

1. **LLM Service** (`backend/services/llm_service.py`)
   - Gestisce la comunicazione con l'API Z.AI
   - Implementa retry logic e error handling
   - Supporta streaming per feedback real-time

2. **PDF Generator** (`backend/services/pdf_generator.py`)
   - Converte il contenuto generato in PDF
   - Gestisce layout e styling professionali
   - Supporta output multi-formato (PDF/PPTX)

3. **API Endpoints** (`backend/main.py`)
   - `/generate-slides/zai-pdf` - Generazione PDF
   - `/generate-slides/zai-agent` - Agente completo
   - Supporto CORS e validazione input

## 🔧 **Configurazione Z.AI**

### Environment Variables

```bash
# Configurazione Base
LLM_TYPE=zai
ZAI_API_KEY=your_api_key_here
ZAI_BASE_URL=https://api.z.ai/api/paas/v4/
ZAI_MODEL=glm-4.5

# Modelli Disponibili
# glm-4.6  - Flagship, thinking capabilities, 200K context
# glm-4.5  - Advanced, 128K context, ottimo per slide
# glm-4.5v - Vision capabilities
# glm-4.5-air - Leggero e veloce
```

### Modelli Supportati per Slide Generation

| Modello | Context Window | Max Tokens | Costo (1K tokens) | Specializzazione |
|---------|----------------|------------|-------------------|------------------|
| `glm-4.6` | 200K | 8192 | $0.003/$0.012 | Flagship, thinking |
| `glm-4.5` | 128K | 4096 | $0.002/$0.008 | **Raccomandato per slide** |
| `glm-4.5v` | 128K | 4096 | $0.0025/$0.010 | Vision + analysis |
| `glm-4.5-air` | 128K | 4096 | $0.001/$0.004 | Veloce ed economico |

## 📡 **API Z.AI - Slide Agent**

### Endpoint Principale

```
POST https://api.z.ai/api/v1/agents
```

### Request Structure

```python
payload = {
    "agent_id": "slides_glm_agent",
    "messages": [
        {
            "role": "user",
            "content": "describe your slide needs in one sentence"
        }
    ],
    "stream": false,  # true per feedback real-time
    "conversation_id": "unique_conversation_identifier",
    "request_id": "unique_request_identifier"
}
```

### Headers

```python
headers = {
    "Authorization": f"Bearer {ZAI_API_KEY}",
    "Content-Type": "application/json"
}
```

## 🎯 **Implementazione nel Sistema**

### Classe ZAIManager

```python
class ZAIManager:
    def __init__(self, api_key: str, model: str = "glm-4.5"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.z.ai/api/paas/v4"

    async def generate_slides_with_agent(self,
        course_id: str,
        topic: str,
        num_slides: int = 10,
        slide_style: str = "modern",
        audience: str = "university"
    ) -> Dict[str, Any]:
```

### Metodi Principali

1. **`generate_slides_with_zai_agent()`** - Generazione completa slide
2. **`generate_slides_with_glm_slide_agent()`** - Agente specifico GLM
3. **`create_zai_slides_prompt()`** - Costruzione prompt ottimizzato

## 📝 **Best Practices per Prompt**

### Principi Guida

1. **Concise e Specifico**: Una frase che descriva chiaramente l'obiettivo
2. **Smart Information Search**: L'agente cerca automaticamente fonti multiple
3. **Elegant Visual Design**: Layout professionali integrati
4. **Context Awareness**: Include audience e stile richiesto

### Esempi di Prompt Efficaci

```python
# Buono - Specifico e conciso
"Crea una presentazione professionale sulla storia della Roma antica per studenti universitari con stile moderno"

# Buono - Con requisiti chiari
"Genera 8 slide sul cambiamento climatico con dati scientifici recenti per presentazione aziendale"

# Buono - Con formato specificato
"Presentazione in 10 slide sull'intelligenza artificiale nel settore medico con design accademico"
```

### Template Prompt Interno

```python
def create_zai_slides_prompt(topic: str, course_context: str = "", num_slides: int = 10,
                           slide_style: str = "modern", audience: str = "university") -> str:

    prompt = f"""Crea una presentazione professionale in formato PDF per il seguente argomento: {topic}

    Contesto del corso: {course_context}
    Numero di slide: {num_slides}
    Stile: {slide_style}
    Pubblico target: {audience}

    Istruzioni specifiche:
    1. Crea una struttura logica e coerente
    2. Includi introduzione, sviluppo e conclusione
    3. Usa linguaggio appropriato per il pubblico target
    4. Aggiungi elementi visivi accattivanti
    5. Mantieni coerenza stilistica throughout
    6. Include data e sources quando appropriato

    Formato output: HTML completo con styling CSS integrato"""

    return prompt
```

## 💰 **Cost Optimization**

### Pricing Structure

- **Base Rate**: $0.7 per Milione di tokens
- **Input Tokens**: ~$0.002 per 1K (glm-4.5)
- **Output Tokens**: ~$0.008 per 1K (glm-4.5)

### Strategie di Ottimizzazione

1. **Model Selection**: Usa `glm-4.5-air` per task semplici
2. **Prompt Engineering**: Prompt concisi riducono token usage
3. **Streaming**: Abilitato per feedback real-time
4. **Batch Processing**: Group multiple requests when possible

### Cost Estimation

```python
# Stimazione costi per presentazione standard
def estimate_slide_generation_cost(num_slides: int = 10, model: str = "glm-4.5"):
    # Input tokens ~100 per slide in prompt
    input_tokens = num_slides * 100
    # Output tokens ~500 per slide generated
    output_tokens = num_slides * 500

    if model == "glm-4.5":
        cost_input = (input_tokens / 1000) * 0.002
        cost_output = (output_tokens / 1000) * 0.008

    total_cost = cost_input + cost_output
    return total_cost  # ~$0.04 per 10 slides
```

## 🔍 **Error Handling e Debugging**

### Common Error Codes

| Code | Messaggio | Causa | Soluzione |
|------|-----------|-------|-----------|
| 1211 | "Unknown Model" | Modello non valido | Usa modello supportato |
| 400 | "Bad Request" | Prompt mal formattato | Verifica formato JSON |
| 401 | "Unauthorized" | API key non valida | Controlla API key |
| 429 | "Rate Limited" | Troppe richieste | Implementa retry logic |
| 500 | "Internal Error" | Errore server Z.AI | Retry con backoff |

### Retry Logic Implementation

```python
async def zai_request_with_retry(payload: dict, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.z.ai/api/v1/agents",
                headers=headers,
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                logger.error(f"ZAI API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
```

## 🚨 **Security Considerations**

### API Key Management

1. **Environment Variables**: Never hardcode API keys
2. **Vault Storage**: Considerare secrets manager in production
3. **Rotation**: Implementare rotation periodica delle API key
4. **Monitoring**: Log access patterns per detection anomalia

### Input Validation

```python
def validate_slide_request(course_id: str, topic: str, num_slides: int) -> bool:
    # Input sanitization
    if not topic or len(topic.strip()) < 10:
        raise ValueError("Topic too short or empty")

    if num_slides < 1 or num_slides > 50:
        raise ValueError("Invalid number of slides")

    # XSS prevention
    import re
    if re.search(r'[<>"\']', topic):
        raise ValueError("Invalid characters in topic")

    return True
```

## 📊 **Monitoring e Analytics**

### Key Metrics da Tracciare

1. **Request Success Rate**: Percentuale successi/fallimenti
2. **Response Time**: Latency media per richiesta
3. **Token Usage**: Input/output tokens per richiesta
4. **Cost Tracking**: Costi aggregati per periodo
5. **Error Distribution**: Tipi di errori più frequenti

### Logging Structure

```python
# Structured logging example
logger.info("ZAI slide generation started", extra={
    "course_id": course_id,
    "topic": topic,
    "num_slides": num_slides,
    "model": model,
    "request_id": request_id,
    "timestamp": datetime.utcnow().isoformat()
})
```

## 🔄 **Future Enhancements**

### Roadmap Implementazione

1. **PPTX Export Support** - Attualmente in sviluppo da Z.AI
2. **Custom Templates** - Layout personalizzati per brand
3. **Multilingual Support** - Slide in lingue multiple
4. **Collaborative Editing** - Editing multi-utente real-time
5. **Advanced Analytics** - Engagement tracking per slide

### Integration Opportunities

1. **RAG Enhancement** - Integrazione con documenti corso
2. **Voice Narration** - Audio generation per slide
3. **Interactive Elements** - Quizzes e polls integrati
4. **Version Control** - Tracking modifiche presentazioni

## 🛠 **Troubleshooting Guide**

### Common Issues and Solutions

#### Issue 1: "Unknown Model" Error
```bash
# Symptom: 400 error with code 1211
# Cause: Invalid model identifier
# Solution: Update .env file
ZAI_MODEL=glm-4.5  # Use valid model
```

#### Issue 2: Slow Response Times
```bash
# Symptom: Requests taking >60 seconds
# Cause: Network latency or model overload
# Solution:
# 1. Check network connectivity
# 2. Use glm-4.5-air for faster responses
# 3. Implement proper timeout handling
```

#### Issue 3: High Token Usage
```python
# Symptom: Unexpectedly high costs
# Cause: Verbose prompts or large responses
# Solution:
# 1. Optimize prompt length
# 2. Set reasonable max_tokens limits
# 3. Monitor token usage in logs
```

## 📚 **References and Resources**

### Official Documentation
- [Z.AI Agents API](https://docs.z.ai/api-reference/agents/agent)
- [Z.AI Slide Generation Guide](https://docs.z.ai/guides/agents/slide)
- [Model Documentation](https://docs.z.ai/models)

### Internal Resources
- Implementation: `backend/services/llm_service.py`
- API Endpoints: `backend/main.py`
- PDF Generation: `backend/services/pdf_generator.py`

### Support Contacts
- Z.AI Support: [support@z.ai](mailto:support@z.ai)
- Internal Development Team: Dev Slack Channel
- Documentation Issues: Create GitHub Issue

---

**Last Updated**: 2025-11-03
**Version**: 1.0
**Maintainer**: Tutor-AI Development Team