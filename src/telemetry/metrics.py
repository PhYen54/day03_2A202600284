import time
from typing import Dict, Any, List
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage) # Mock cost calculation
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        Calculate the cost based on the model and token usage.
        Pricing is based on current rates from providers (as of 2026).
        """
        # Pricing per 1M tokens (input/output)
        pricing = {
            # OpenAI models
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            # Gemini models
            "gemini-3-flash-preview": {"input": 0.50, "output": 3.00},
            "gemini-1.5-flash": {"input": 0.35, "output": 1.05},  # Approximate
            # Local models (no cost)
            "phi-3-mini-4k-instruct-q4.gguf": {"input": 0.0, "output": 0.0},
        }
        
        # Default pricing if model not found
        default_pricing = {"input": 0.01, "output": 0.02}
        
        model_pricing = pricing.get(model, default_pricing)
        
        input_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * model_pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1_000_000) * model_pricing["output"]
        
        return input_cost + output_cost

# Global tracker instance
tracker = PerformanceTracker()
