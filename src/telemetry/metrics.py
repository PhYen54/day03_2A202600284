import time
from typing import Dict, Any, List
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    
    # Bảng giá tham khảo (USD / 1 triệu token) - Có thể tùy biến thêm
    PRICING_TABLE = {
        "gemma-4-31b-it": {
            "prompt": 0.140, 
            "completion": 0.400,
            "cached": 0.450 # Thêm thông số cached từ ảnh nếu sau này bạn cần dùng
        }
    }

    def __init__(self):
        self.session_metrics: List[Dict[str, Any]] = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        cost = self._calculate_cost(model, usage)
        
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": cost
        }
        self.session_metrics.append(metric)
        
        logger.info(
            f"Tracked: {metric['total_tokens']} tokens | {latency_ms}ms | Model: {model}"
        )

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        Tính toán chi phí dựa trên số lượng token.
        """
        rates = self.PRICING_TABLE.get(model, self.PRICING_TABLE["gemma-4-31b-it"])
        
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        prompt_cost = (prompt_tokens / 1_000_000) * rates["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * rates["completion"]
        
        return prompt_cost + completion_cost

    def get_summary(self) -> Dict[str, Any]:
        """
        Tổng hợp toàn bộ metrics.
        """
        if not self.session_metrics:
            return {"status": "No metrics recorded yet."}

        total_requests = len(self.session_metrics)
        total_prompt_tokens = sum(m["prompt_tokens"] for m in self.session_metrics)
        total_completion_tokens = sum(m["completion_tokens"] for m in self.session_metrics)
        total_cost = sum(m["cost_estimate"] for m in self.session_metrics)
        avg_latency = sum(m["latency_ms"] for m in self.session_metrics) / total_requests

        return {
            "total_requests": total_requests,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "total_cost_usd": round(total_cost, 6),
            "avg_latency_ms": round(avg_latency, 2)
        }
        
    def print_summary(self):
        """
        In báo cáo thống kê.
        """
        summary = self.get_summary()
        if "status" in summary:
            print(f"\n[Telemetry] {summary['status']}")
            return

        print("\n" + "="*40)
        print("LLM PERFORMANCE SUMMARY")
        print("="*40)
        print(f" Requests Count    : {summary['total_requests']}")
        print(f" Avg Latency       : {summary['avg_latency_ms']} ms")
        print(f" Prompt Tokens     : {summary['total_prompt_tokens']:,}")
        print(f" Completion Tokens : {summary['total_completion_tokens']:,}")
        print(f" Total Tokens      : {summary['total_tokens']:,}")
        print(f" Estimated Cost    : ${summary['total_cost_usd']}")
        print("="*40 + "\n")

# Global tracker instance
tracker = PerformanceTracker()