import json
import os
import time
from dotenv import load_dotenv
from src.agent.agent import ReActAgent
from src.core.openai_provider import OpenAIProvider
from src.tools.budget_tools import (
    calculate_total,
    check_discount,
    check_stock,
    get_price,
    get_products_by_category,
    validate_combination,
)
import google.generativeai as genai

# Load test cases
with open('budget_agent_test_cases.json', 'r', encoding='utf-8') as f:
    test_cases = json.load(f)

# Load environment variables
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

agent = ReActAgent(llm=llm, tools=tools, max_steps=10)

results = []

for tc in test_cases:
    print(f"\n=== Running Test Case: {tc['test_id']} - {tc['title']} ===")
    
    # Run agent
    start_time = time.time()
    result = agent.run(tc['user_input'])
    end_time = time.time()
    
    # Find latest trace file
    trace_files = [f for f in os.listdir('logs') if f.startswith('trace_') and f.endswith('.json')]
    trace_files.sort(reverse=True)
    if trace_files:
        with open(f'logs/{trace_files[0]}', 'r', encoding='utf-8') as f:
            trace = json.load(f)
        
        # Extract tool calls from trace
        tool_calls = []
        for step in trace['steps']:
            if 'thought_action' in step:
                import re
                match = re.search(r"Action:\s*(\w+)\((.*)\)", step['thought_action'])
                if match:
                    tool_calls.append({
                        "tool": match.group(1),
                        "args": match.group(2).strip().strip('"').strip("'")
                    })
        
        actual_output = {
            "final_answer": trace.get('final_answer', result),
            "tool_calls": tool_calls,
            "steps": len(trace['steps']),
            "total_time_ms": trace['total_time_ms'],
            "termination_reason": trace['termination_reason']
        }
    else:
        actual_output = {
            "final_answer": result,
            "tool_calls": [],
            "steps": 0,
            "total_time_ms": int((end_time - start_time) * 1000),
            "termination_reason": "unknown"
        }
    
    # Compare with expected
    evaluation = {
        "test_id": tc['test_id'],
        "passed": False,  # Will evaluate manually
        "actual": actual_output,
        "expected": tc['expected_output'],
        "criteria_check": []  # Manual check
    }
    
    results.append(evaluation)
    
    print(f"Result: {result}")
    print(f"Tool calls: {len(actual_output['tool_calls'])}")
    print(f"Steps: {actual_output['steps']}")
    print(f"Time: {actual_output['total_time_ms']}ms")

# Save results
with open('test_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\nTest results saved to test_results.json")