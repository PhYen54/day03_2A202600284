from src.agent.agent import ReActAgent
from src.core.gemini_provider import GeminiProvider

from src.tools.budget_tools import (
    calculate_total,
    check_discount,
    check_stock,
    get_price,
    get_products_by_category,
    validate_combination,
    )
import os
from dotenv import load_dotenv
import google.generativeai as genai
from src.telemetry.metrics import tracker

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
    {"name": "get_products_by_category", "description": "Lấy sản phẩm theo danh mục", "func": get_products_by_category},
    {"name": "check_stock", "description": "Kiểm tra tồn kho theo tên", "func": check_stock},
    {"name": "get_price", "description": "Lấy giá sản phẩm theo tên", "func": get_price},
    {"name": "check_discount", "description": "Lấy % giảm giá sản phẩm", "func": check_discount},
    {"name": "calculate_total", "description": "Tính tổng giỏ hàng theo danh sách ID", "func": calculate_total},
    {"name": "validate_combination", "description": "Kiểm tra combo sản phẩm theo danh sách ID", "func": validate_combination}
]

# Tạo agent
agent = ReActAgent(llm=llm, tools=tools, max_steps=4)

# Query test
query = """
Find a combination of laptop, keyboard
with total price under 15000000.
Check stock before selecting.
Then print the bill.
"""
# Run agent
result = agent.run(query)

print("\n===== FINAL RESULT =====")
print(result)

tracker.print_summary()