# 📊 Sistema di Logging Backend - Documentazione Tecnica

## 📋 Overview

Il sistema di logging backend di Tutor-AI è progettato per fornire visibilità completa sulle operazioni del sistema, debugging avanzato, monitoring delle performance e tracciamento degli eventi di sicurezza.

## 🏗️ Architettura del Sistema

### Componenti Principali

1. **`logging_config.py`** - Configurazione centralizzata del logging
2. **`middleware/logging_middleware.py`** - Middleware per logging HTTP request/response
3. **Enhanced Services** - Logging integrato nei servizi esistenti (RAG, LLM, etc.)
4. **`utils/error_handlers.py`** - Sistema avanzato di gestione errori
5. **`scripts/log_analyzer.py`** - Strumenti di analisi log

### Dipendenze

```python
# requirements.txt additions (già incluse)
structlog>=24.4.0          # Structured logging
logging                    # Python standard library
fastapi                   # Web framework
pydantic                  # Data validation
```

## 🔧 Configurazione Centralizzata

### logging_config.py

#### Funzionalità Principali

```python
from logging_config import (
    setup_logging,           # Configurazione iniziale
    get_logger,             # Logger standard
    get_structlog_logger,   # Logger strutturato
    RequestLogger,          # Logging HTTP
    SecurityLogger,         # Eventi sicurezza
    PerformanceLogger,      # Metriche performance
    LoggedTimer            # Timing contestuale
)
```

#### Inizializzazione Automatica

Il sistema si inizializza automaticamente all'avvio dell'applicazione:

```python
# main.py
from logging_config import setup_logging, get_logger

# Setup centralizzato con configurazione environment-aware
setup_logging(
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    log_dir=os.getenv('LOG_DIR', './logs'),
    enable_console=True,
    enable_file=True
)

logger = get_logger(__name__)
logger.info("Tutor-AI Backend Application Started")
```

#### Configurazione Avanzata

```python
# Personalizzazione completa
setup_logging(
    log_level="DEBUG",                    # Livello logging
    log_dir="/var/log/tutor-ai",         # Directory log
    service_name="tutor-ai-backend",     # Nome servizio
    enable_console=True,                 # Output console
    enable_file=True,                    # File output
    max_file_size=50*1024*1024,         # 50MB per file
    backup_count=10                      # 10 backup files
)
```

### Formati di Output

#### Console Format (Development)
```
2024-01-15 10:30:45 | INFO    | abc12345 | LLMService:generate_response:234 | API request completed successfully
```

#### JSON Format (Production)
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "LLMService",
  "message": "API request completed successfully",
  "module": "llm_service",
  "function": "generate_response",
  "line": 234,
  "service": "tutor-ai-backend",
  "environment": "production",
  "process_id": 12345,
  "thread_id": 67890,
  "correlation_id": "abc12345",
  "metadata": {
    "operation": "llm_generate",
    "duration_ms": 1250,
    "tokens_used": 150
  }
}
```

## 🌐 HTTP Request/Response Logging Middleware

### APILoggingMiddleware

#### Funzionalità

- **Request Tracking**: Logging completo di tutte le richieste HTTP
- **Response Analytics**: Statistiche sulle risposte
- **Performance Monitoring**: Tracking dei tempi di risposta
- **Security Detection**: Rilevamento automatico minacce
- **Client Intelligence**: Analisi client e user agent

#### Configurazione

```python
from middleware.logging_middleware import create_api_logging_middleware

app.add_middleware(
    create_api_logging_middleware(
        log_level="INFO",
        log_request_body=True,           # Log request body
        log_response_body=False,         # Log response body
        excluded_paths={"/health", "/metrics"},  # Path esclusi
        performance_threshold_ms=1000.0, # Soglia slow requests
        rate_limit_tracking=True         # Tracking rate limiting
    )
)
```

#### Eventi Loggati

##### Request Logging
```python
{
  "event_type": "api_request",
  "method": "POST",
  "path": "/api/chat",
  "query_params": {"course_id": "123"},
  "headers": {"content-type": "application/json"},
  "client_info": {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "browser": "Chrome",
    "os": "Windows",
    "device": "Desktop"
  },
  "request_size": 1024,
  "correlation_id": "abc12345"
}
```

##### Response Logging
```python
{
  "event_type": "api_response",
  "method": "POST",
  "path": "/api/chat",
  "status_code": 200,
  "duration_ms": 1250.5,
  "response_size": 2048,
  "performance_category": "slow"
}
```

##### Security Events
```python
{
  "event_type": "security_sql_injection_attempt",
  "description": "SQL injection pattern detected",
  "client_ip": "192.168.1.100",
  "pattern": "union select",
  "endpoint": "/api/search",
  "severity": "WARNING"
}
```

### Detection Patterns

#### SQL Injection
```python
SQL_INJECTION_PATTERNS = [
    r"union\s+select",
    r"drop\s+table",
    r"insert\s+into",
    r"delete\s+from",
    r"exec\s*\(",
    r"script\s*>",
    r"javascript:",
    r"vbscript:"
]
```

#### XSS Patterns
```python
XSS_PATTERNS = [
    r"<script",
    r"</script>",
    r"javascript:",
    r"onerror=",
    r"onload=",
    r"onclick=",
    r"alert\s*\("
]
```

#### Path Traversal
```python
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"%2e%2e%2f",
    r"%2e%2e%5c",
    r"/etc/passwd",
    r"/etc/shadow",
    r"\\windows\\system32"
]
```

## 🔧 Enhanced Service Logging

### LLMService Integration

#### Logging Initialization
```python
class LLMService:
    def __init__(self):
        # Enhanced logging setup
        self.logger = get_structlog_logger("LLMService")
        self.security_logger = SecurityLogger()

        # Performance tracking
        self.request_count = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
```

#### Request Logging
```python
async def generate_response(self, prompt: str, model: str = None):
    with LoggedTimer("llm_generate_response", logger=self.logger):
        self.logger.info(
            "LLM request started",
            extra={
                "operation": "llm_generate",
                "model": model or self.default_model,
                "prompt_length": len(prompt),
                "request_count": self.request_count + 1
            }
        )

        try:
            response = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=[{"role": "user", "content": prompt}]
            )

            # Update tracking metrics
            self.request_count += 1
            self.total_tokens_used += response.usage.total_tokens

            self.logger.info(
                "LLM request completed",
                extra={
                    "operation": "llm_generate",
                    "model": model,
                    "tokens_used": response.usage.total_tokens,
                    "total_tokens": self.total_tokens_used,
                    "cost": self._calculate_cost(response.usage),
                    "response_length": len(response.choices[0].message.content)
                }
            )

            return response

        except Exception as e:
            self.logger.error(
                "LLM request failed",
                extra={
                    "operation": "llm_generate",
                    "model": model,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise
```

### RAGService Integration

#### Performance Tracking
```python
class RAGService:
    def __init__(self):
        # Enhanced logging setup
        self.logger = get_structlog_logger("RAGService")
        self.performance_logger = PerformanceLogger()

        # Performance tracking
        self.retrieval_count = 0
        self.total_documents_processed = 0
        self.average_retrieval_time = 0.0
```

#### Retrieval Operations Logging
```python
async def retrieve_context(self, query: str, course_id: str, book_id: str = None):
    start_time = time.time()

    self.logger.info(
        "Context retrieval started",
        extra={
            "operation": "context_retrieval",
            "query_length": len(query),
            "course_id": course_id,
            "book_id": book_id,
            "retrieval_count": self.retrieval_count + 1
        }
    )

    try:
        # Document retrieval
        documents = await self._retrieve_documents(query, course_id, book_id)

        # Embedding generation
        with LoggedTimer("embedding_generation", logger=self.logger):
            embeddings = await self._generate_embeddings(query)

        # Vector search
        with LoggedTimer("vector_search", logger=self.logger):
            results = await self._search_vectors(embeddings, documents)

        duration_ms = (time.time() - start_time) * 1000

        # Update performance metrics
        self.retrieval_count += 1
        self.total_documents_processed += len(documents)
        self.average_retrieval_time = (
            (self.average_retrieval_time * (self.retrieval_count - 1) + duration_ms) /
            self.retrieval_count
        )

        self.logger.info(
            "Context retrieval completed",
            extra={
                "operation": "context_retrieval",
                "duration_ms": duration_ms,
                "documents_found": len(documents),
                "results_returned": len(results),
                "average_retrieval_time": self.average_retrieval_time,
                "total_processed": self.total_documents_processed
            }
        )

        return results

    except Exception as e:
        self.logger.error(
            "Context retrieval failed",
            extra={
                "operation": "context_retrieval",
                "course_id": course_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )
        raise
```

## 🚨 Enhanced Error Handling

### ErrorHandler Class

#### Enhanced Features
```python
class ErrorHandler:
    def __init__(self):
        # Enhanced logging setup
        self.logger = get_structlog_logger("ErrorHandler")
        self.security_logger = SecurityLogger()

        # Analytics tracking
        self.error_counts: Dict[str, int] = {}
        self.error_rates: Dict[str, float] = {}
        self.suspicious_activity: Dict[str, int] = {}
```

#### Advanced Error Logging
```python
async def create_error_response(self, error: Exception, request: Request) -> JSONResponse:
    # Extract request information
    client_ip = self._get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "Unknown")
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4())[:8])

    # Categorize error
    error_type = self._categorize_error(error)
    severity = self._determine_severity(error, client_ip)

    # Enhanced logging with full context
    log_entry = {
        "error_type": error_type,
        "severity": severity,
        "correlation_id": correlation_id,
        "request_method": request.method,
        "request_path": request.url.path,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "error_details": {
            "exception_class": error.__class__.__name__,
            "exception_message": str(error),
            "stack_trace": traceback.format_exc(),
            "request_id": getattr(request.state, "request_id", None)
        },
        "security_context": {
            "is_suspicious": self._is_suspicious_activity(client_ip),
            "rate_limit_exceeded": self._is_rate_limited(client_ip),
            "blocked_patterns": self._check_blocked_patterns(request)
        }
    }

    # Log with appropriate level
    if severity == "CRITICAL":
        self.logger.critical(f"Critical error: {error.message}", extra=log_entry, exc_info=True)
        self.security_logger.log_security_event(
            event_type="critical_error",
            description=f"Critical system error: {error.message}",
            severity="CRITICAL",
            client_ip=client_ip,
            **log_entry
        )
    elif severity == "HIGH":
        self.logger.error(f"High severity error: {error.message}", extra=log_entry, exc_info=True)
    else:
        self.logger.warning(f"Error: {error.message}", extra=log_entry)

    # Track error analytics
    self._track_error_analytics(error_type, client_ip)

    # Create standardized response
    return JSONResponse(
        status_code=getattr(error, "status_code", 500),
        content={
            "success": False,
            "error": {
                "type": error_type,
                "message": getattr(error, "message", "An error occurred"),
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

### Error Analytics Dashboard

#### Error Tracking Methods
```python
def _track_error_analytics(self, error_type: str, client_ip: str):
    """Track error patterns and detect anomalies"""
    current_time = datetime.now()

    # Update error counts
    self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

    # Track client-specific errors
    client_key = f"{client_ip}:{error_type}"
    self.suspicious_activity[client_key] = self.suspicious_activity.get(client_key, 0) + 1

    # Detect error spikes
    if self.suspicious_activity[client_key] > 10:  # Threshold
        self.security_logger.log_security_event(
            event_type="error_spike_detected",
            description=f"High error rate from {client_ip}: {error_type}",
            severity="WARNING",
            client_ip=client_ip,
            error_type=error_type,
            error_count=self.suspicious_activity[client_key]
        )

def get_error_analytics(self, hours: int = 24) -> Dict[str, Any]:
    """Get comprehensive error analytics"""
    cutoff_time = datetime.now() - timedelta(hours=hours)

    # Query error database for analytics
    with sqlite3.connect(self.error_log_path) as conn:
        cursor = conn.cursor()

        # Error distribution
        cursor.execute('''
            SELECT error_type, COUNT(*) as count
            FROM error_logs
            WHERE timestamp >= ?
            GROUP BY error_type
            ORDER BY count DESC
        ''', (cutoff_time,))

        error_distribution = dict(cursor.fetchall())

        # Timeline analysis
        cursor.execute('''
            SELECT
                datetime(timestamp, 'localtime') as hour,
                COUNT(*) as errors
            FROM error_logs
            WHERE timestamp >= ?
            GROUP BY strftime('%Y-%m-%d %H', timestamp)
            ORDER BY hour
        ''', (cutoff_time,))

        error_timeline = dict(cursor.fetchall())

        # Top error sources
        cursor.execute('''
            SELECT request_path, COUNT(*) as count
            FROM error_logs
            WHERE timestamp >= ? AND request_path IS NOT NULL
            GROUP BY request_path
            ORDER BY count DESC
            LIMIT 10
        ''', (cutoff_time,))

        top_error_sources = dict(cursor.fetchall())

    return {
        "error_distribution": error_distribution,
        "error_timeline": error_timeline,
        "top_error_sources": top_error_sources,
        "total_errors": sum(error_distribution.values()),
        "error_types": list(error_distribution.keys()),
        "peak_error_hour": max(error_timeline.items(), key=lambda x: x[1])[0] if error_timeline else None
    }
```

## 🛠️ Log Analysis Tools

### scripts/log_analyzer.py

#### Funzionalità Principali

```bash
# Monitoraggio in tempo reale
python scripts/log_analyzer.py monitor --filters "ERROR" "security"

# Analisi completa logs
python scripts/log_analyzer.py analyze --hours 24 --format json

# Statistiche errori
python scripts/log_analyzer.py errors --hours 48

# Ricerca pattern specifici
python scripts/log_analyzer.py search --pattern "database.*timeout" --context 5

# Export logs per analisi esterna
python scripts/log_analyzer.py export --output logs_export.json --format json

# Cleanup vecchi log
python scripts/log_analyzer.py cleanup --days 30 --dry-run
```

#### Advanced Search Patterns

##### Performance Issues
```bash
# Trova richieste lente
python scripts/log_analyzer.py search --pattern "duration_ms.*[0-9]{4,}"

# Database timeouts
python scripts/log_analyzer.py search --pattern "database.*timeout|connection.*failed"

# Memory usage elevato
python scripts/log_analyzer.py search --pattern "memory_used.*[0-9]{3,}"
```

##### Security Analysis
```bash
# SQL injection attempts
python scripts/log_analyzer.py search --pattern "sql_injection_attempt|union.*select"

# XSS attempts
python scripts/log_analyzer.py search --pattern "xss_attempt|<script"

# Rate limiting violations
python scripts/log_analyzer.py search --pattern "rate_limit_exceeded|high_request_rate"
```

##### Error Analysis
```bash
# Errori critici
python scripts/log_analyzer.py search --pattern "CRITICAL|FATAL"

# LLM service errors
python scripts/log_analyzer.py search --pattern "LLMService.*ERROR|provider.*failed"

# File system errors
python scripts/log_analyzer.py search --pattern "permission.*denied|file.*not.*found"
```

### Real-time Monitoring

#### Custom Monitoring Script
```python
#!/usr/bin/env python3
import time
import subprocess
import json
from datetime import datetime

def monitor_system_health():
    """Monitoraggio salute sistema in tempo reale"""

    while True:
        try:
            # Error rate check
            result = subprocess.run([
                "python", "scripts/log_analyzer.py", "errors", "--hours", "1"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                # Parse error statistics
                error_stats = json.loads(result.stdout)
                error_rate = error_stats.get('error_rate', 0)

                # Alert threshold
                if error_rate > 5.0:  # 5% error rate threshold
                    print(f"🚨 HIGH ERROR RATE: {error_rate:.2f}%")
                    # Send alert (email, slack, etc.)

                # Display status
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error Rate: {error_rate:.2f}% | Total Errors: {error_stats.get('total_errors', 0)}")

            # Check for security events
            security_result = subprocess.run([
                "python", "scripts/log_analyzer.py", "search", "--pattern", "security_event", "--hours", "1"
            ], capture_output=True, text=True)

            if security_result.returncode == 0:
                security_events = json.loads(security_result.stdout)
                if len(security_events) > 0:
                    print(f"🔒 Security Events (1h): {len(security_events)}")

            time.sleep(60)  # Check every minute

        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_system_health()
```

## 🔧 Configuration e Environment

### Environment Variables

```env
# Logging Configuration
LOG_LEVEL=INFO                          # DEBUG, INFO, WARN, ERROR, FATAL
LOG_DIR=./logs                         # Directory log files
ENVIRONMENT=development                 # development, staging, production

# Performance Logging
ENABLE_PERFORMANCE_LOGGING=true        # Enable performance metrics
PERFORMANCE_THRESHOLD_MS=1000          # Slow request threshold

# Security Logging
ENABLE_SECURITY_LOGGING=true           # Enable security event logging
RATE_LIMIT_THRESHOLD=100               # Requests per minute threshold

# Log Rotation
LOG_MAX_FILE_SIZE=10485760             # 10MB max file size
LOG_BACKUP_COUNT=5                     # Number of backup files
LOG_COMPRESS_OLD_FILES=true            # Compress old log files

# Remote Logging (Optional)
REMOTE_LOGGING_ENABLED=false           # Enable remote log aggregation
REMOTE_LOG_ENDPOINT=                   # Remote logging service URL
REMOTE_LOG_API_KEY=                    # API key for remote logging
```

### Docker Configuration

#### docker-compose.yml Logging
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - LOG_DIR=./logs
      - ENVIRONMENT=production
      - ENABLE_PERFORMANCE_LOGGING=true
      - ENABLE_SECURITY_LOGGING=true
    volumes:
      - ./logs:/app/logs              # Mount log directory
      - ./data:/app/data              # Mount data directory
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=backend"
    labels:
      - "tutor-ai.service=backend"
      - "tutor-ai.logging.enabled=true"
```

#### Log Rotation Configuration
```yaml
# docker-compose.yml per log rotation
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"                # Rotate at 10MB
        max-file: "5"                  # Keep 5 files
        compress: "true"               # Compress old files
        labels: "service=backend,environment=${ENVIRONMENT}"
```

### Production Configuration

#### Production Logging Setup
```python
# main.py production configuration
import os
from logging_config import setup_logging

# Production logging configuration
is_production = os.getenv('ENVIRONMENT') == 'production'

setup_logging(
    log_level=os.getenv('LOG_LEVEL', 'INFO' if is_production else 'DEBUG'),
    log_dir=os.getenv('LOG_DIR', '/var/log/tutor-ai'),
    enable_console=not is_production,    # No console logging in production
    enable_file=True,
    max_file_size=int(os.getenv('LOG_MAX_FILE_SIZE', 50*1024*1024)),  # 50MB
    backup_count=int(os.getenv('LOG_BACKUP_COUNT', 10)),
    service_name="tutor-ai-backend-production"
)
```

## 📊 Performance Considerations

### Logging Performance Impact

#### Best Practices
```python
# ✅ Good: Use structured logging with lazy evaluation
logger.info(
    "User operation completed",
    extra={
        "user_id": user.id,
        "operation": "file_upload",
        "file_size": file.size,
        "duration_ms": duration
    }
)

# ✅ Good: Use LoggedTimer for performance critical sections
with LoggedTimer("database_operation", logger=logger):
    result = await database.query(...)

# ❌ Avoid: Complex string formatting in hot paths
logger.info(f"User {user.id} uploaded file {file.name} of size {file.size} in {duration}ms")
```

#### Async Logging Considerations
```python
# For high-performance scenarios, consider async logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncLogger:
    def __init__(self, logger):
        self.logger = logger
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="async_logger")

    async def async_info(self, message: str, extra: Dict[str, Any] = None):
        """Async logging to avoid blocking event loop"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self.logger.info,
            message,
            extra
        )

# Usage
async_logger = AsyncLogger(logger)
await async_logger.async_info("Async operation completed", extra={"operation": "test"})
```

### Memory Management

#### Structured Data Size
```python
# ✅ Good: Limit metadata size
logger.info("Operation completed", extra={
    "operation": "file_processing",
    "file_count": len(files),           # Count instead of list
    "total_size": sum(f.size for f in files),  # Aggregate instead of details
    "success": True
})

# ❌ Avoid: Large metadata objects
logger.info("Operation completed", extra={
    "operation": "file_processing",
    "files": [{"name": f.name, "content": f.content} for f in files]  # Too large
})
```

## 🔍 Troubleshooting Guide

### Common Issues

#### 1. Log Files Not Created
```bash
# Check permissions
ls -la logs/
chmod 755 logs/
chmod 644 logs/*.log

# Check environment variables
echo $LOG_DIR
echo $LOG_LEVEL
```

#### 2. Missing Correlation IDs
```python
# Ensure middleware is properly configured
app.add_middleware(
    create_api_logging_middleware(
        log_level="INFO",
        enable_correlation_ids=True
    )
)
```

#### 3. Performance Issues
```bash
# Check log file sizes
du -sh logs/

# Monitor disk space
df -h

# Check log rotation
ls -la logs/*.{log,gz}
```

#### 4. Security Events Not Logged
```python
# Verify security logging is enabled
if os.getenv('ENABLE_SECURITY_LOGGING', 'true').lower() == 'true':
    security_logger.log_security_event(...)
```

### Debug Commands

#### Log System Status
```bash
# Check logging configuration
python -c "
from logging_config import get_logger
logger = get_logger('test')
logger.info('Logging system test')
"

# Verify middleware is active
curl -X GET http://localhost:8000/health -H "X-Test-Header: test"
# Check logs for correlation ID

# Test error logging
python -c "
from logging_config import get_logger
logger = get_logger('test')
try:
    raise Exception('Test error')
except Exception as e:
    logger.error('Test error logging', exc_info=True)
"
```

#### Performance Monitoring
```bash
# Monitor log generation rate
watch -n 1 'ls -la logs/ && wc -l logs/*.log'

# Check for log bottlenecks
python scripts/log_analyzer.py performance --hours 1
```

## 📈 Monitoring e Alerting

### Metrics Collection

#### Custom Metrics Endpoint
```python
from fastapi import APIRouter
from logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/metrics/logging")
async def get_logging_metrics():
    """Get current logging system metrics"""
    return {
        "total_log_entries": get_total_log_count(),
        "error_rate": calculate_error_rate(hours=1),
        "average_response_time": get_average_response_time(),
        "active_correlation_ids": get_active_correlation_count(),
        "log_file_size": get_log_file_sizes(),
        "security_events_last_hour": get_security_event_count(hours=1)
    }
```

### Alert Thresholds

#### Recommended Thresholds
```python
ALERT_THRESHOLDS = {
    "error_rate_percent": 5.0,          # Alert if > 5% errors
    "response_time_ms": 2000.0,         # Alert if avg > 2s
    "security_events_per_hour": 10,     # Alert if > 10 security events
    "disk_usage_percent": 80.0,         # Alert if > 80% disk usage
    "log_file_size_mb": 100.0,          # Alert if log file > 100MB
    "correlation_timeout_minutes": 30    # Alert if correlation > 30min
}
```

---

## 📚 Riferimenti e Link

- **Documentazione Ufficiale**: [CLAUDE.md](../../../CLAUDE.md)
- **API Documentation**: [API Reference](../api/README.md)
- **Development Guide**: [Development Guidelines](../development/README.md)
- **Troubleshooting**: [Troubleshooting Guide](../troubleshooting/README.md)
- **Configuration**: [Configuration Guide](../configuration/README.md)

## 🔗 File Correlati

- `backend/logging_config.py` - Configurazione logging centralizzata
- `backend/middleware/logging_middleware.py` - Middleware HTTP logging
- `backend/utils/error_handlers.py` - Sistema gestione errori
- `scripts/log_analyzer.py` - Strumenti analisi log
- `backend/services/llm_service.py` - Enhanced LLM service logging
- `backend/services/rag_service.py` - Enhanced RAG service logging