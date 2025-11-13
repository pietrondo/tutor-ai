try:
    from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
except Exception:
    Counter = None
    Histogram = None
    CollectorRegistry = None
    generate_latest = None
    CONTENT_TYPE_LATEST = "text/plain"

class Metrics:
    def __init__(self):
        if CollectorRegistry is not None:
            self.registry = CollectorRegistry()
            self.rag_requests_total = Counter("rag_requests_total", "RAG requests", registry=self.registry)
            self.rag_cache_hits_total = Counter("rag_cache_hits_total", "RAG cache hits", registry=self.registry)
            self.rag_llm_timeouts_total = Counter("rag_llm_timeouts_total", "LLM timeouts", registry=self.registry)
            self.rag_request_duration_seconds = Histogram("rag_request_duration_seconds", "RAG request duration", registry=self.registry, buckets=(0.05,0.1,0.2,0.3,0.5,0.7,1.0,2.0))
        else:
            self.registry = None
            self.rag_requests_total = 0
            self.rag_cache_hits_total = 0
            self.rag_llm_timeouts_total = 0
            self.rag_latencies = []

    def inc_requests(self):
        if hasattr(self.rag_requests_total, "inc"):
            self.rag_requests_total.inc()
        else:
            self.rag_requests_total += 1

    def inc_cache_hit(self):
        if hasattr(self.rag_cache_hits_total, "inc"):
            self.rag_cache_hits_total.inc()
        else:
            self.rag_cache_hits_total += 1

    def inc_llm_timeout(self):
        if hasattr(self.rag_llm_timeouts_total, "inc"):
            self.rag_llm_timeouts_total.inc()
        else:
            self.rag_llm_timeouts_total += 1

    def observe_latency(self, seconds: float):
        if hasattr(self, "rag_request_duration_seconds") and hasattr(self.rag_request_duration_seconds, "observe"):
            self.rag_request_duration_seconds.observe(seconds)
        else:
            self.rag_latencies.append(seconds)

    def export_prometheus(self):
        if self.registry is not None and generate_latest is not None:
            return CONTENT_TYPE_LATEST, generate_latest(self.registry)
        data = {
            "rag_requests_total": self.rag_requests_total,
            "rag_cache_hits_total": self.rag_cache_hits_total,
            "rag_llm_timeouts_total": self.rag_llm_timeouts_total,
            "rag_request_duration_seconds_count": len(self.rag_latencies),
            "rag_request_duration_seconds_avg": (sum(self.rag_latencies) / len(self.rag_latencies)) if self.rag_latencies else 0.0
        }
        return "application/json", bytes(str(data), "utf-8")

metrics = Metrics()

