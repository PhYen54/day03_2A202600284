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

