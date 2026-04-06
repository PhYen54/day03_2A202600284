# Báo Cáo Cá Nhân: Lab 3 - Chatbot vs ReAct Agent

- **Tên Sinh Viên**: Vũ Tiến Thành
- **Mã Sinh Viên**: 2A202600443
- **Ngày**: 06/04/2026

---

## I. Đóng Góp Kỹ Thuật (15 Điểm)

*Mô tả đóng góp cụ thể của bạn vào codebase (ví dụ: implement tool, fix parser, v.v.).*

- **Modules Đã Implement**: `src/tools/budget_tools.py`, `src/agent/agent.py`, `src/telemetry/metrics.py`
- **Code Highlights**:
  - Tools: Hàm `get_products_by_category()`, `validate_combination()`, `calculate_total()`, `check_stock()` để xử lý logic budget và stock checking, tích hợp vào agent workflow.
  - Agent: Enhanced ReAct loop với logging, error handling (parser, hallucination), và execution traces để track tool calls và reasoning steps.
  - Metrics: Hàm `_calculate_cost()` với pricing cho OpenAI/Gemini, track token efficiency và latency.
- **Documentation**: Tools cung cấp environment feedback cho agent ReAct, kết hợp với logging để monitor tool execution và optimize agent performance trong budget optimization tasks.

---

## II. Case Study Debug (10 Điểm)

*Phân tích một sự kiện lỗi cụ thể bạn gặp phải trong lab sử dụng hệ thống logging.*

- **Mô Tả Vấn Đề**: Agent gọi tool không tồn tại (hallucination) như "Action: optimize_budget(None)", dẫn đến TOOL_EXECUTION_ERROR.
- **Nguồn Log**: logs/trace_*.json - "observation": "Error: Tool 'optimize_budget' not found. Available tools: [list]"
- **Chẩn Đoán**: LLM hallucinate tool name không có trong tools list, hoặc prompt không rõ ràng về available tools.
- **Giải Pháp**: Cập nhật system prompt với danh sách TOOLS đầy đủ, thêm HALLUCINATION_ERROR logging trong _execute_tool để agent học từ lỗi.

---

## III. Nhận Xét Cá Nhân: Chatbot vs ReAct (10 Điểm)

*Suy ngẫm về sự khác biệt khả năng reasoning.*

1.  **Reasoning**: Khối Thought cho phép agent phân tích task thành các bước tuần tự, tránh hallucination trực tiếp như chatbot, giúp agent lập kế hoạch dựa trên thông tin có sẵn.
2.  **Reliability**: Agent hoạt động tệ hơn khi tools fail hoặc prompt mơ hồ - chatbot có thể "đoán" tốt hơn nhưng không thể verify được.
3.  **Observation**: Phản hồi từ environment (kết quả tools) giúp agent tự điều chỉnh, như lọc sản phẩm stock > 0 hoặc tính lại budget dựa trên giá sau discount.
4. **Cost**: Sử dụng API KEY free vì vậy không có tính toán được cost tuy nhiên thì dựa vào số lần gọi và tokens in/out thì đánh giá là agent xem log để so sánh agent với baseline. Từ log trace, agent thực hiện 5 steps với 4 tool calls, tổng tokens ~3739 (gấp ~4-7 lần so với chatbot baseline ~500-1000 tokens cho direct answer). 
---

## IV. Cải Tiến Tương Lai (5 Điểm)

*Làm thế nào để scale cho hệ thống AI agent production-level?*

- **Scalability**: Async tool calls với queue để parallel execution, vector DB cho tool retrieval khi có nhiều tools.
- **Safety**: Supervisor LLM audit tool calls trước execution, rate limiting cho tools.
- **Performance**: Cache tool results, fine-tune agent trên tool usage patterns để giảm tool call errors.

---

> [!NOTE]
> Submit bằng cách đổi tên file thành `REPORT_[TÊN_CỦA_BẠN].md` và đặt vào folder này.
