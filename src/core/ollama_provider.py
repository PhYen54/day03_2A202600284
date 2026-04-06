import os
from typing import List, Dict, Any, Generator
from ollama import Client
from llm_provider import LLMProvider
from dotenv import load_dotenv


class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name, api_key)
        self.client = Client(
            host="https://ollama.com",   # ← Important fix
            headers={'Authorization': f'Bearer {api_key}'}
        )
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        response = self.client.chat(
            model=self.model_name,
            messages=messages,
            stream=False
        )

        # response is a ChatResponse object or dict
        content = response.message.content if hasattr(response, 'message') else response.get('message', {}).get('content', '')

        return {
            "content": content,
            "usage": getattr(response, 'usage', None) or response.get('usage'),
            "provider": "ollama",
            "metadata": {}
        }

    def stream(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        for chunk in self.client.chat(
            model=self.model_name,
            messages=messages,
            stream=True
        ):
            # chunk has .message.content (recommended) or ['message']['content']
            if hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                content = chunk.message.content
            else:
                content = chunk.get('message', {}).get('content', '')

            if content:   # only yield non-empty chunks
                yield content

# ========== TEST ==========
if __name__ == "__main__":
    load_dotenv()
    api_key = os.environ.get("OLLAMA_API_KEY")
    if not api_key:
        raise ValueError("Set OLLAMA_API_KEY in .env")

    provider = OllamaProvider("gpt-oss:120b", api_key=api_key)   # or "gpt-oss:120b-cloud" if needed

    print("=== NON-STREAM ===")
    result = provider.generate("Write a short story about a fox.", "You are a creative assistant")
    print(result['content'])

    print("\n=== STREAM ===")
    for chunk in provider.stream("Write a short story about a fox.", "You are a creative assistant"):
        print(chunk, end="", flush=True)
    print()