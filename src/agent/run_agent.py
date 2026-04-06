from src.agent.agent import ReActAgent
from src.core.gemini_provider import GeminiProvider

from tools.budget_tools import (
    get_products_by_category,
    validate_combination,
    )
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

#  Cấu hình cho genai 
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Lỗi: Không tìm thấy GOOGLE_API_KEY trong file .env")
print("hello")
# Khởi tạo Gemini LLM
llm = GeminiProvider(model_name="gemma-4-31b-it")

tools = [
    {
        "name": "get_products_by_category",
        "description": "Lấy danh sách sản phẩm. Truyền vào 'laptop', 'keyboard', hoặc 'mouse'. Trả về ID, Giá Net, Hiệu năng và Tồn kho.",
        "func": get_products_by_category
    },
    {
        "name": "validate_combination",
        "description": "Kiểm tra combo bằng danh sách ID sản phẩm (ví dụ: 'L001, K002, M003'). Trả về tổng tiền, tổng hiệu năng và tình trạng kho.",
        "func": validate_combination
    }
]

# Tạo agent
agent = ReActAgent(llm=llm, tools=tools, max_steps=8)

# Query test
query = """
Find a combination of laptop, keyboard, and mouse
with total price under 15000000
and total performance above 80.
Check stock before selecting.
Then print the bill.
"""
# Run agent
result = agent.run(query)

print("\n===== FINAL RESULT =====")
print(result)