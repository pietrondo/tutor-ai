# ZAI Slide Agent - Implementation Guide

## 🎯 **Overview**

Questa guida spiega come implementare e utilizzare l'agente ZAI Slide Generation nel sistema Tutor-AI. Include code examples, best practices, e troubleshooting tips.

## 🏗️ **Architecture**

### System Flow

```
Frontend Request → API Endpoint → LLM Service → ZAI API → PDF Generator → Response
     ↓               ↓              ↓           ↓            ↓           ↓
  React UI     FastAPI Route   ZAIManager   slides_glm_agent  PDF    Download
```

### Key Components

1. **API Layer** (`main.py`)
   - `/generate-slides/zai-pdf` - Main endpoint
   - Request validation and response formatting
   - Error handling and logging

2. **Service Layer** (`llm_service.py`)
   - `ZAIManager` class - Core ZAI integration
   - `generate_slides_with_zai_agent()` - Main method
   - Retry logic and error handling

3. **Generation Layer** (`pdf_generator.py`)
   - HTML to PDF conversion
   - Professional styling and layout
   - File management

## 🔧 **Implementation Details**

### 1. Configuration Setup

```python
# backend/services/llm_service.py
class ZAIManager:
    def __init__(self, api_key: str, model: str = "glm-4.5"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.z.ai/api/paas/v4"
        self.timeout = 120
        self.max_retries = 3
```

### 2. Request Validation

```python
def validate_slide_request(request: SlideRequest) -> bool:
    if not request.topic or len(request.topic.strip()) < 10:
        raise ValueError("Topic must be at least 10 characters")

    if request.num_slides < 1 or request.num_slides > 50:
        raise ValueError("Number of slides must be between 1 and 50")

    # Sanitize input
    allowed_styles = ["modern", "academic", "corporate", "creative"]
    if request.slide_style not in allowed_styles:
        request.slide_style = "modern"

    return True
```

### 3. Prompt Engineering

```python
def create_zai_slides_prompt(topic: str, course_context: str = "", num_slides: int = 10,
                           slide_style: str = "modern", audience: str = "university") -> str:

    # Base prompt structure
    base_prompt = f"Crea una presentazione professionale in formato PDF su: {topic}"

    # Add context
    if course_context:
        base_prompt += f"\n\nContesto del corso: {course_context}"

    # Add specifications
    specifications = f"""

    Specifiche richieste:
    - Numero di slide: {num_slides}
    - Stile: {slide_style}
    - Pubblico target: {audience}

    Struttura:
    1. Slide titolo con argomento e autore
    2. Introduzione con contesto e obiettivi
    3. Sviluppo con {num_slides-3} slide di contenuto
    4. Conclusioni con punti chiave

    Istruzioni:
    - Usa linguaggio appropriato per {audience}
    - Include esempi pratici dove possibile
    - Mantieni coerenza stilistica
    - Aggiungi elementi visivi accattivanti
    """

    return base_prompt + specifications
```

### 4. API Communication

```python
async def call_zai_agent(self, prompt: str, conversation_id: str = None) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "agent_id": "slides_glm_agent",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "conversation_id": conversation_id or self._generate_conversation_id(),
        "request_id": self._generate_request_id()
    }

    try:
        response = await self._make_request_with_retry(payload)
        return self._parse_response(response)
    except Exception as e:
        logger.error(f"ZAI agent call failed: {e}")
        raise
```

### 5. Retry Logic

```python
async def _make_request_with_retry(self, payload: dict, max_retries: int = 3) -> requests.Response:
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.z.ai/api/v1/agents",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response
            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Rate limited, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                continue
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                if attempt == max_retries - 1:
                    raise Exception(f"API request failed: {response.status_code}")

        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                raise Exception("Request timeout after retries")
            await asyncio.sleep(2 ** attempt)
```

### 6. Response Processing

```python
def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
    try:
        data = response.json()

        if "choices" not in data or len(data["choices"]) == 0:
            raise Exception("Invalid response format")

        generated_content = data["choices"][0]["message"]["content"]

        # Extract slides preview if available
        slides_preview = self._extract_slides_preview(generated_content)

        return {
            "content": generated_content,
            "slides_preview": slides_preview,
            "usage": data.get("usage", {}),
            "model": data.get("model", self.model)
        }

    except Exception as e:
        logger.error(f"Failed to parse ZAI response: {e}")
        raise
```

## 🎨 **Frontend Integration**

### React Component Example

```typescript
// frontend/src/components/SlideGenerator.tsx
import React, { useState } from 'react';

interface SlideRequest {
  topic: string;
  num_slides: number;
  slide_style: string;
  audience: string;
  course_id: string;
}

export const SlideGenerator: React.FC = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);

  const generateSlides = async (request: SlideRequest) => {
    setIsGenerating(true);
    setProgress(0);

    try {
      const response = await fetch('/generate-slides/zai-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error('Generation failed');
      }

      const result = await response.json();

      // Download PDF
      if (result.success) {
        downloadPdf(result.pdf_data, result.filename);
      }

    } catch (error) {
      console.error('Error generating slides:', error);
    } finally {
      setIsGenerating(false);
      setProgress(0);
    }
  };

  const downloadPdf = (base64Data: string, filename: string) => {
    const blob = base64ToBlob(base64Data, 'application/pdf');
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="slide-generator">
      {/* Form inputs */}
      <button
        onClick={() => generateSlides(slideRequest)}
        disabled={isGenerating}
      >
        {isGenerating ? 'Generating...' : 'Generate Slides'}
      </button>
    </div>
  );
};
```

## 🧪 **Testing**

### Unit Tests

```python
# tests/test_zai_service.py
import pytest
from unittest.mock import Mock, patch
from services.llm_service import ZAIManager

class TestZAIManager:

    @pytest.fixture
    def zai_manager(self):
        return ZAIManager(api_key="test_key", model="glm-4.5")

    @patch('services.llm_service.requests.post')
    def test_generate_slides_success(self, mock_post, zai_manager):
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "<html>...</html>"}}],
            "usage": {"total_tokens": 1000}
        }
        mock_post.return_value = mock_response

        result = await zai_manager.generate_slides_with_agent(
            course_id="test",
            topic="Test Topic",
            num_slides=5
        )

        assert result["success"] is True
        assert "pdf_data" in result
        mock_post.assert_called_once()

    @patch('services.llm_service.requests.post')
    def test_rate_limit_retry(self, mock_post, zai_manager):
        # Mock rate limit then success
        mock_post.side_effect = [
            Mock(status_code=429),
            Mock(status_code=200, json={"choices": [{"message": {"content": "test"}}]})
        ]

        with patch('asyncio.sleep'):
            result = await zai_manager.call_zai_agent("test prompt")

        assert mock_post.call_count == 2
        assert result is not None
```

### Integration Tests

```python
# tests/test_zai_integration.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_slide_generation_endpoint():
    request_data = {
        "course_id": "test_course",
        "topic": "Introduction to Machine Learning",
        "num_slides": 5,
        "slide_style": "modern",
        "audience": "university"
    }

    response = client.post("/generate-slides/zai-pdf", json=request_data)

    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "pdf_data" in result
    assert "filename" in result

def test_invalid_request():
    invalid_request = {
        "topic": "short",  # Too short
        "num_slides": 100,  # Too many
        "slide_style": "invalid",
        "audience": "university"
    }

    response = client.post("/generate-slides/zai-pdf", json=invalid_request)
    assert response.status_code == 400
```

## 📊 **Performance Optimization**

### 1. Caching Strategy

```python
from functools import lru_cache
import hashlib

class SlideCache:
    def __init__(self):
        self.cache = {}
        self.max_size = 100

    def get_cache_key(self, topic: str, num_slides: int, style: str) -> str:
        content = f"{topic}_{num_slides}_{style}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, cache_key: str) -> Optional[Dict]:
        return self.cache.get(cache_key)

    def set(self, cache_key: str, result: Dict, ttl: int = 3600):
        # Simple LRU eviction
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        result["cached_at"] = time.time()
        result["ttl"] = ttl
        self.cache[cache_key] = result
```

### 2. Concurrent Request Handling

```python
import asyncio
from asyncio import Semaphore

class ConcurrencyLimiter:
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = Semaphore(max_concurrent)

    async def generate_with_limit(self, request_data: Dict):
        async with self.semaphore:
            return await generate_slides_with_zai_agent(**request_data)
```

### 3. Resource Monitoring

```python
import psutil
import logging

class ResourceMonitor:
    def __init__(self):
        self.memory_threshold = 80  # percentage
        self.cpu_threshold = 80     # percentage

    def check_resources(self) -> bool:
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=1)

        if memory_percent > self.memory_threshold:
            logging.warning(f"High memory usage: {memory_percent}%")
            return False

        if cpu_percent > self.cpu_threshold:
            logging.warning(f"High CPU usage: {cpu_percent}%")
            return False

        return True
```

## 🔍 **Debugging Tools**

### 1. Request Logging

```python
import json
from datetime import datetime

class RequestLogger:
    def __init__(self, log_file: str = "zai_requests.log"):
        self.log_file = log_file

    def log_request(self, request_data: Dict, response_data: Dict, duration: float):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request": request_data,
            "response_summary": {
                "success": response_data.get("success", False),
                "tokens_used": response_data.get("usage", {}).get("total_tokens", 0),
                "model": response_data.get("model", "unknown")
            },
            "duration_seconds": duration
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
```

### 2. Health Check Endpoint

```python
@app.get("/health/zai")
async def check_zai_health():
    try:
        # Test API connectivity
        response = requests.get(
            "https://api.z.ai/api/paas/v4/models",
            headers={"Authorization": f"Bearer {os.getenv('ZAI_API_KEY')}"},
            timeout=5
        )

        if response.status_code == 200:
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        else:
            return {"status": "unhealthy", "error": f"API returned {response.status_code}"}

    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 🚀 **Deployment Considerations**

### 1. Environment Configuration

```python
# config.py
import os
from typing import Optional

class ZAIConfig:
    def __init__(self):
        self.api_key = os.getenv("ZAI_API_KEY")
        self.model = os.getenv("ZAI_MODEL", "glm-4.5")
        self.base_url = os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/paas/v4")
        self.timeout = int(os.getenv("ZAI_TIMEOUT", "120"))
        self.max_retries = int(os.getenv("ZAI_MAX_RETRIES", "3"))

        # Slide-specific settings
        self.max_slides = int(os.getenv("ZAI_MAX_SLIDES", "20"))
        self.default_style = os.getenv("ZAI_DEFAULT_SLIDE_STYLE", "modern")
        self.default_audience = os.getenv("ZAI_DEFAULT_AUDIENCE", "university")

    def validate(self) -> bool:
        if not self.api_key:
            raise ValueError("ZAI_API_KEY is required")
        return True
```

### 2. Error Monitoring

```python
from dataclasses import dataclass
from enum import Enum

class ErrorType(Enum):
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    UNKNOWN = "unknown"

@dataclass
class ErrorMetrics:
    error_type: ErrorType
    count: int = 0
    last_occurrence: Optional[datetime] = None
    sample_message: Optional[str] = None

class ErrorTracker:
    def __init__(self):
        self.errors = {}

    def track_error(self, error_type: ErrorType, message: str):
        if error_type not in self.errors:
            self.errors[error_type] = ErrorMetrics(error_type)

        error = self.errors[error_type]
        error.count += 1
        error.last_occurrence = datetime.utcnow()
        error.sample_message = message[:200]  # Keep sample short

    def get_metrics(self) -> Dict[str, ErrorMetrics]:
        return self.errors
```

## 📚 **Resources and References**

- [Z.AI API Documentation](https://docs.z.ai/api-reference/agents/agent)
- [Complete Documentation](./ZAI_SLIDE_AGENT_DOCUMENTATION.md)
- [Quick Reference](./ZAI_QUICK_REFERENCE.md)
- [Example Code Repository](https://github.com/example/zai-integration)

---

**Version**: 1.0
**Last Updated**: 2025-11-03
**Maintainer**: Tutor-AI Development Team