# ZAI Slide Agent - Quick Reference

## 🚀 **Quick Start**

### 1. Configuration
```bash
# .env file
LLM_TYPE=zai
ZAI_API_KEY=your_key_here
ZAI_MODEL=glm-4.5
ZAI_BASE_URL=https://api.z.ai/api/paas/v4/
```

### 2. API Call Example
```python
# Direct API call
curl -X POST "https://api.z.ai/api/v1/agents" \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "slides_glm_agent",
    "messages": [{"role": "user", "content": "Create 5 slides about AI ethics"}],
    "stream": false
  }'
```

### 3. Use via Tutor-AI
```python
# Backend endpoint
POST /generate-slides/zai-pdf
{
  "course_id": "your_course_id",
  "topic": "Artificial Intelligence in Education",
  "num_slides": 8,
  "slide_style": "modern",
  "audience": "university"
}
```

## 📋 **Model Selection Guide**

| Use Case | Recommended Model | Why |
|----------|-------------------|-----|
| **Slide Generation** | `glm-4.5` | Balanced cost/performance |
| **Complex Topics** | `glm-4.6` | Best reasoning, thinking mode |
| **Quick Drafts** | `glm-4.5-air` | Fast, cheap, good enough |
| **Visual Content** | `glm-4.5v` | Vision capabilities |

## 💡 **Prompt Templates**

### Basic Template
```
Create a professional presentation on [TOPIC] for [AUDIENCE] with [NUM_SLIDES] slides in [STYLE] format.
```

### Advanced Template
```
Crea una presentazione professionale in formato PDF su [ARGOMENTO] per [PUBBLICO TARGET].

Requisiti:
- Numero slide: [NUM_SLIDES]
- Stile: [MODERN/ACADEMIC/CORPORATE]
- Durata: [TIME_ESTIMATE]
- Include: [DATA/CHARTS/EXAMPLES]

Struttura richiesta:
1. Introduzione con contesto
2. Sviluppo con punti chiave
3. Esempi pratici/case study
4. Conclusioni e takeaways
```

## 🔧 **Common Tasks**

### Generate Simple Slides
```python
topic = "Climate Change Basics"
prompt = f"Create 5 slides about {topic} for high school students"
```

### Academic Presentation
```python
topic = "Machine Learning Applications"
prompt = f"""Generate academic presentation on {topic} for university computer science students.
Include technical details, algorithms, and real-world applications. Use modern academic style."""
```

### Corporate Slides
```python
topic = "Q4 Sales Results"
prompt = f"""Create professional business presentation on {topic} for executive meeting.
Include data visualization, key metrics, and strategic recommendations."""
```

## ⚠️ **Troubleshooting**

### Error: "Unknown Model"
```bash
# Fix model name
ZAI_MODEL=glm-4.5  # NOT glm-4
```

### Error: Rate Limited
```python
# Implement retry
import time
time.sleep(2 ** attempt)  # Exponential backoff
```

### Slow Response
```python
# Use faster model
ZAI_MODEL=glm-4.5-air
# Or reduce slides requested
num_slides = 5  # Instead of 20
```

## 📊 **Cost Estimation**

**Per 10 slides with glm-4.5**: ~$0.04
- Input: 1,000 tokens × $0.002 = $0.002
- Output: 5,000 tokens × $0.008 = $0.04
- **Total**: ~$0.04 per presentation

## 🛠 **Development Commands**

```bash
# Test ZAI connection
curl -H "Authorization: Bearer $ZAI_API_KEY" \
     "https://api.z.ai/api/paas/v4/models"

# Check logs
docker logs tutor-ai-backend --tail 50

# Test endpoint
curl -X POST "http://localhost:8000/generate-slides/zai-pdf" \
  -H "Content-Type: application/json" \
  -d '{"topic":"Test","num_slides":3}'
```

## 📁 **Key Files**

- `backend/services/llm_service.py` - Core ZAI integration
- `backend/services/pdf_generator.py` - PDF creation logic
- `backend/.env` - Configuration
- `backend/main.py` - API endpoints
- `docs/ZAI_SLIDE_AGENT_DOCUMENTATION.md` - Full documentation

## 🔗 **Useful Links**

- [Z.AI API Docs](https://docs.z.ai/api-reference/agents/agent)
- [Slide Generation Guide](https://docs.z.ai/guides/agents/slide)
- [Model Reference](https://docs.z.ai/models)
- [Internal Documentation](./ZAI_SLIDE_AGENT_DOCUMENTATION.md)

---
*Version: 1.0 | Updated: 2025-11-03*