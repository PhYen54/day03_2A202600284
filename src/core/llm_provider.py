import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Generator
import time
import requests
from dotenv import load_dotenv


class LLMProvider(ABC):
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None):
        pass

    @abstractmethod
    def stream(self, prompt: str, system_prompt: Optional[str] = None):
        pass


class OpenRouterProvider(LLMProvider):
    def __init__(self, model_name, api_key):
        super().__init__(model_name, api_key)
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt, system_prompt=None, enable_reasoning=False):
        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "messages": messages,
                "reasoning": {"enabled": enable_reasoning}
            }
        )

        # ✅ Check lỗi API
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")

        data = response.json()

        # ✅ Validate response
        if "choices" not in data:
            raise Exception(f"Invalid response: {data}")

        latency_ms = int((time.time() - start_time) * 1000)

        message = data["choices"][0]["message"]
        usage = data.get("usage", {})

        return {
            "content": message.get("content", ""),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
            "latency_ms": latency_ms,
            "provider": "openrouter",
            "metadata": {
                "reasoning": message.get("reasoning_details") if enable_reasoning else None
            }
        }

    def stream(self, prompt, system_prompt=None):
        yield "stream not implemented yet"


# ================= TEST =================
if __name__ == "__main__":
    load_dotenv()

    provider = OpenRouterProvider(
        model_name="qwen/qwen3.6-plus:free",
        api_key=os.getenv("LLM_API_KEY")  # ✅ sửa key
    )

    res = provider.generate(
        prompt="How many r are in the word 'strawberry'?",
        system_prompt="You are a careful reasoning assistant",
        enable_reasoning=False  # 🔥 default nên OFF
    )

    print("=== RESULT ===")
    print("Content:", res["content"])
    print("Usage:", res["usage"])
    print("Latency (ms):", res["latency_ms"])