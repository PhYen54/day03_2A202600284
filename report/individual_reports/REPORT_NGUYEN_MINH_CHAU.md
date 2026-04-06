# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Minh Châu
- **Student ID**: 2A202600179
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/tools/tools.py`, `src/chatbot/chatbot.py`, `src/core/gemini_provider.py`, `budget_agent_test_cases.json`, `test_case_validate.py`.
- **Code Highlights**: 
    - Viết Class `BaselineChatbot` và hàm `test_chatbot` để gọi và thực thi chatbot.
    - Tạo file `budget_agent_test_cases.json` bao gồm các test case để thử nghiệm.
    - Viết file `test_case_validate` để validate các trường hợp test case.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Agent trả về kết quả sai do truyền tham số không đúng định dạng vào tool calculate_total(), cụ thể là truyền None hoặc thiếu field price trong danh sách sản phẩm, dẫn đến lỗi runtime khi tính toán tổng chi phí.
- **Log Source**: logs/trace_*.json
```
{
  "step": 3,
  "action": "calculate_total",
  "action_input": {"items": [{"name": "laptop"}]},
  "observation": "Error: KeyError 'price'"
}
```
- **Diagnosis**: Nguyên nhân đến từ việc LLM không hiểu rõ schema của input cho tool, đặc biệt là yêu cầu mỗi item phải có đầy đủ name, price, và quantity. Prompt chưa cung cấp ví dụ cụ thể về format input hợp lệ, dẫn đến việc agent "hallucinate" cấu trúc input không đúng.
- **Solution**:
    - Cập nhật system prompt để mô tả rõ schema của từng tool (input/output).
    - Thêm ví dụ Thought → Action → Action Input đúng format để guide LLM.
    - Bổ sung validation trong tool (try/except + default values) để tránh crash.
    - Logging thêm lỗi dạng INVALID_INPUT để dễ debug và cải thiện prompt sau này.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: ReAct Agent có khả năng chia nhỏ bài toán thông qua các bước Thought, giúp phân tích rõ ràng từng bước như chọn sản phẩm, kiểm tra stock, và tính toán ngân sách. Trong khi đó, Chatbot thường đưa ra câu trả lời trực tiếp nên dễ bị sai logic hoặc bỏ sót constraint.
2.  **Reliability**: Agent hoạt động kém hơn Chatbot trong các trường hợp:
    - Tool bị lỗi hoặc input không hợp lệ.
    - Prompt không đủ rõ ràng về cách sử dụng tool. Khi đó agent có thể bị loop hoặc trả về lỗi, trong khi chatbot vẫn có thể "ước lượng" và trả lời tương đối hợp lý.
3.  **Observation**: Observation đóng vai trò rất quan trọng vì nó cung cấp feedback từ môi trường (tool execution). Agent có thể dựa vào đó để điều chỉnh bước tiếp theo, ví dụ:
    - Nếu check_stock() trả về hết hàng → agent chọn sản phẩm khác.
    - Nếu calculate_total() vượt budget → agent giảm số lượng hoặc chọn item rẻ hơn.
Điều này giúp agent có khả năng iterative reasoning tốt hơn chatbot.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Áp dụng vector database để retrieve tool phù hợp khi số lượng tools lớn (tool retrieval thay vì hardcode).
- **Safety**: Validate input/output của tool chặt chẽ hơn để tránh lỗi và injection.
- **Performance**:
    - Cache kết quả của các tool calls phổ biến để giảm latency.
    - Giảm số bước reasoning bằng cách fine-tune model với pattern sử dụng tool.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
