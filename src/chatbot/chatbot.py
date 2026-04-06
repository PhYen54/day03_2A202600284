#!/usr/bin/env python3
"""
Baseline Chatbot implementation for comparison with ReAct Agent.
This demonstrates the limitations of standard LLM prompting.
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.llm_provider import LLMProvider
from src.core.gemini_provider import GeminiProvider

class BaselineChatbot:
    """
    Simple chatbot that prompts the LLM directly.
    """
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm
    
    def chat(self, user_input: str) -> str:
        """
        Simple chat without tools - just direct LLM response.
        """
        system_prompt = """
        You are a helpful assistant. Answer the user's question clearly and directly.
        """
        
        result = self.llm.generate(user_input, system_prompt=system_prompt)
        return result['content']

def test_chatbot():
    """Test the baseline chatbot."""
    load_dotenv()
    
    provider = GeminiProvider(model_name="gemini-3-flash-preview", api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Initialize chatbot
    chatbot = BaselineChatbot(llm=provider)
    
    # Test queries that require multi-step reasoning
    test_queries = [
        "Tôi có 5 triệu, hãy lập kế hoạch mua laptop, chuột, bàn phím sao cho không vượt ngân sách."
    ]
    
    print("🤖 Chatbot vs ReAct Agent Comparison")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 30)
        
        # Chatbot response
        print("Chatbot Response:")
        try:
            chatbot_response = chatbot.chat(query)
            print(f"  {chatbot_response}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_chatbot()