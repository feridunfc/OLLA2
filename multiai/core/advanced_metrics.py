# multiai/core/advanced_metrics.py
import time
import functools
import logging
from typing import Dict, Any, Callable

from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Business/tech metrics
API_REQUESTS = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Latency of API requests in seconds', ['endpoint'])
LEDGER_WRITES = Counter('ledger_writes_total', 'Ledger writes', ['status'])
LEDGER_VERIFICATIONS = Counter('ledger_verifications_total', 'Ledger verifications', ['status'])
LLM_CALLS = Counter('llm_calls_total', 'Total LLM calls', ['provider', 'status'])
LLM_TOKEN_USAGE = Counter('llm_tokens_total', 'Total tokens used', ['provider', 'type'])
AGENT_EXECUTIONS = Counter('agent_executions_total', 'Agent executions', ['agent_type', 'status'])
BUDGET_USAGE = Gauge('budget_usage_ratio', 'Budget usage ratio')
CACHE_HIT_RATE = Gauge('cache_hit_ratio', 'Cache hit rate')
SANDBOX_EXECUTIONS = Counter('sandbox_executions_total', 'Sandbox executions', ['type', 'status'])
ACTIVE_SPRINTS = Gauge('active_sprints', 'Number of active sprints')

LLM_RESPONSE_TIME = Histogram('llm_response_time_seconds', 'LLM response time (s)')
AGENT_EXECUTION_TIME = Histogram('agent_execution_time_seconds', 'Agent execution time (s)')
LEDGER_OPERATION_TIME = Histogram('ledger_operation_time_seconds', 'Ledger operation time (s)')

class MetricsCollector:
    def record_llm_call(self, provider: str, success: bool, tokens_used: Dict[str, int], duration: float):
        status = "success" if success else "error"
        LLM_CALLS.labels(provider=provider, status=status).inc()
        LLM_RESPONSE_TIME.observe(duration)
        for token_type, count in tokens_used.items():
            LLM_TOKEN_USAGE.labels(provider=provider, type=token_type).inc(count)

    def record_agent_execution(self, agent_type: str, success: bool, duration: float):
        status = "success" if success else "error"
        AGENT_EXECUTIONS.labels(agent_type=agent_type, status=status).inc()
        AGENT_EXECUTION_TIME.observe(duration)

    def record_sandbox_execution(self, exec_type: str, success: bool):
        status = "success" if success else "error"
        SANDBOX_EXECUTIONS.labels(type=exec_type, status=status).inc()

    def update_budget_metrics(self, used: float, total: float):
        if total > 0:
            BUDGET_USAGE.set(used / total)

    def update_cache_metrics(self, hits: int, misses: int):
        total = hits + misses
        if total > 0:
            CACHE_HIT_RATE.set(hits / total)

metrics_collector = MetricsCollector()

def track_agent(agent_type: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                AGENT_EXECUTIONS.labels(agent_type=agent_type, status='success').inc()
                AGENT_EXECUTION_TIME.observe(time.time() - start)
                return result
            except Exception:
                AGENT_EXECUTIONS.labels(agent_type=agent_type, status='error').inc()
                AGENT_EXECUTION_TIME.observe(time.time() - start)
                raise
        return wrapper
    return decorator
