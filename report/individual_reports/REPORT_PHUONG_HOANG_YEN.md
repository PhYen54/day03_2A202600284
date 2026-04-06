# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phương Hoàng Yến
- **Student ID**: 2A202600284
- **Date**: 6/4/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: src/telemetry/langsmith_tracer.py src/telemetry/metrics.py src/telemetry/main.py src/core/gemini_provider.py src/tools/tools.py
- **Modules Implemented**: `src/telemetry/langsmith_tracer.py`, `src/telemetry/metrics.py`, `src/telemetry/main.py`, `src/core/gemini_provider.py`, `src/tools/tools.py`

- **Code Highlights**:

  **1. Tích hợp Telemetry tự động vào LLM Provider (`src/core/gemini_provider.py`)**
  Thay vì viết code đếm token rải rác khắp nơi, bộ đếm (tracker) được nhúng sâu vào ngay lớp giao tiếp API. Mọi request đều được tự động đo lường:
  ```python
  # Trích xuất metadata từ Gemini API và tự động ghi log
  usage = {
      "prompt_tokens": response.usage_metadata.prompt_token_count,
      "completion_tokens": response.usage_metadata.candidates_token_count,
      "total_tokens": response.usage_metadata.total_token_count
  }
  
  # Đẩy dữ liệu vào Tracker chạy ngầm
  tracker.track_request(
      provider="google", 
      model=self.model_name, 
      usage=usage, 
      latency_ms=latency_ms
  )
  ```
  **2. Ghi log chuẩn Production (JSON Format) (`src/telemetry/metrics.py`)**
Đảm bảo tính dễ dàng truy xuất và phân tích sau này (tích hợp tốt với ELK stack, Datadog...) bằng cách ghi log dạng JSON thay vì text thuần:
```python
def log_session_summary(self):
    """Lưu toàn bộ báo cáo tổng kết của Agent session vào file log JSON."""
    summary = self.get_summary()
    if "status" not in summary:
        from src.telemetry.logger import logger
        logger.log_event("AGENT_SESSION_SUMMARY", summary)

```
  **3. Cấu trúc Schema công cụ linh hoạt (`src/tools/tools.py`)**
Sử dụng format chuẩn Function Calling với mô tả chi tiết, giúp Agent dễ dàng hiểu ngữ cảnh:
```python
{
    "name": "calculate_total",
    "description": "Tính tổng tiền của giỏ hàng dựa trên danh sách ID sản phẩm, có tính đến tình trạng kho và giảm giá.",
    "parameters": { 
        "type": "object", 
        "properties": { 
            "item_ids": { 
                "type": "array", 
                "items": { "type": "string" } 
            } 
        }, 
        "required": ["item_ids"] 
    }
}
```
  **Documentation**
```text
  Hệ thống được thiết kế theo kiến trúc Module hóa (Modular Architecture), tương tác trực tiếp với vòng lặp ReAct (Reasoning and Acting) qua 3 giai đoạn chính:

Giai đoạn Suy nghĩ & Hành động (Thought & Action - src/core/gemini_provider.py): Mỗi khi vòng lặp ReAct cần phân tích bước tiếp theo, nó gọi đến GeminiProvider. Tại đây, model LLM (gemma-4-31b-it) phân tích lịch sử hội thoại để đưa ra quyết định gọi Tool. Xuyên suốt quá trình này, module metrics.py và langsmith_tracer.py đóng vai trò "người quan sát thầm lặng" (silent observer), tự động ghi lại số lượng token tiêu thụ, độ trễ (latency) và ước tính chi phí API mà không làm gián đoạn luồng xử lý chính.

Giai đoạn Quan sát (Observation - src/tools/tools.py): Khi ReAct loop nhận được yêu cầu gọi hàm từ LLM, nó sẽ thực thi các logic nghiệp vụ (như calculate_total, check_discount hoặc validate_combination) từ file tools. Kết quả trả về (bao gồm cả lỗi nếu có, ví dụ như "hết hàng") được format dưới dạng cấu trúc JSON/Dict và nạp ngược lại vào Prompt để LLM nhận thức được vấn đề, từ đó tự sửa sai hoặc tiếp tục suy luận bước tiếp theo.

Giai đoạn Kết thúc (Finish/Termination - src/telemetry/main.py): Khi ReAct loop tìm ra câu trả lời cuối cùng cho người dùng hoặc chạm ngưỡng giới hạn an toàn (ví dụ: max_steps=8), vòng lặp dừng lại. Ngay lúc này, PerformanceTracker sẽ tự động kích hoạt hàm tổng hợp để xuất AGENT_SESSION_SUMMARY dạng JSON ra file log, cung cấp cái nhìn toàn cảnh về hiệu năng và chi phí của toàn bộ phiên làm việc.
```


---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

### Case 1: Lỗi "Schema Drift" (Sai lệch cấu trúc dữ liệu)
- **Problem Description**: Khi được yêu cầu tính tổng tiền, Agent đã truyền một payload JSON không hoàn chỉnh vào hàm `calculate_total()`. Cụ thể, nó chỉ gửi tên sản phẩm mà bỏ quên các trường bắt buộc (mandatory fields) như `price` và `quantity`, gây ra lỗi Runtime (crash backend) khi Python cố gắng truy xuất dữ liệu.
- **Log Source**: Trích từ `logs/trace_execution.json`:
  ```json
  {
    "step": 3,
    "attempted_action": "calculate_total",
    "payload_sent": {"items": [{"name": "laptop_gaming"}]},
    "system_observation": "Fatal Error: KeyError 'price' at line 42 in tools.py"
  }
- **Diagnosis**: Lỗi này xảy ra do LLM bị "ảo giác cấu trúc" (Schema Hallucination). Model đã tự suy diễn (abstract) rằng hệ thống backend sẽ tự động biết giá tiền nếu chỉ cần cung cấp tên sản phẩm. Nguyên nhân sâu xa là System Prompt thiếu sự ràng buộc chặt chẽ về định dạng kiểu dữ liệu (Strict Typing) cho các object phức tạp nhiều tầng.

- **Solution**:

Phía Prompt (Cải thiện LLM): Bổ sung định nghĩa cấu trúc JSON bắt buộc vào System Prompt, kèm theo một Few-Shot Example mô phỏng chính xác chuỗi tư duy: Thought -> Action -> Correct Action Input.

Phía Backend (Defensive Programming): Bọc logic của tool bằng khối try-except. Thay vì để hệ thống crash, tool sẽ bắt lỗi KeyError và trả ngược lại cho Agent một Observation (vd: "INVALID_INPUT: Bạn quên truyền trường 'price' cho sản phẩm laptop_gaming"), giúp Agent có cơ hội tự sửa sai (self-correct) ở bước tiếp theo.
---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1. **Reasoning (Khả năng suy luận)**: 
   Khối `Thought` hoạt động như một cơ chế "độc thoại nội tâm" (Internal Monologue) dựa trên phương pháp Chain-of-Thought. Khác với Chatbot truyền thống thường cố gắng đưa ra đáp án ngay lập tức (Zero-shot inference) dẫn đến tính toán sai lệch, khối `Thought` ép Agent phải "chia để trị" (Divide and Conquer). Ví dụ: Đối mặt với bài toán ngân sách 15 triệu, Agent không đoán bừa mà tư duy tuần tự: *"Bước 1: Tìm giá Laptop -> Bước 2: Tìm giá Chuột -> Bước 3: Tính tổng xem có vượt ngân sách không"*. Điều này giúp triệt tiêu gần như hoàn toàn ảo giác trong các bài toán logic nhiều bước.

2. **Reliability (Độ tin cậy)**: 
   Tuy nhiên, Agent lại thể hiện hiệu năng **kém hơn hẳn** Chatbot trong các tác vụ hỏi đáp thông thường (Chit-chat) hoặc định nghĩa đơn giản (e.g., *"Laptop gaming là gì?"*). Hội chứng "Over-engineering" (làm phức tạp hóa vấn đề) khiến Agent cố gắng tìm kiếm một Tool để trả lời cho những câu hỏi mà bản thân LLM đã có sẵn kiến thức. Kết quả là độ trễ (Latency) tăng vọt, tiêu tốn Token vô ích, và đôi khi rơi vào lỗi nếu không có Tool nào phù hợp với câu hỏi giao tiếp thông thường.

3. **Observation (Quan sát môi trường)**: 
   Phản hồi từ `Observation` chính là mỏ neo "Grounding" (kéo AI về thực tại) không thể thiếu. Chatbot truyền thống là một hệ thống "mù", nó sẽ tự tin tư vấn người dùng mua một món đồ đã hết hàng. Ngược lại, nhờ `Observation`, Agent nhận được các feedback thời gian thực (ví dụ: *"Error: Out of stock"* hoặc *"KeyError: price"*). Dựa vào đây, Agent có khả năng **Tự phục hồi (Self-correction)**, thay đổi dòng `Thought` tiếp theo thành: *"Món hàng này không khả dụng, tôi không thể dùng nó. Tôi cần tìm một sản phẩm khác thay thế"*.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability (Khả năng mở rộng)**:
  - **Asynchronous Tool Execution (Xử lý bất đồng bộ):** Chuyển đổi kiến trúc gọi hàm sang `async/await` hoặc sử dụng Message Queue (như Celery/RabbitMQ). Điều này cho phép Agent kiểm tra tồn kho của 10 sản phẩm cùng một lúc thay vì phải đợi gọi tuần tự từng cái, giảm đáng kể thời gian phản hồi (Response Time).
  
- **Safety (An toàn & Bảo mật)**:
  - **Supervisor Architecture & HITL:** Áp dụng mô hình Đa tác nhân (Multi-Agent). Một Agent giám sát (Supervisor) nhỏ và nhanh sẽ kiểm duyệt các Action của ReAct Agent trước khi chạy. Đối với các hành động nhạy cảm (như trừ tiền, thanh toán), bắt buộc phải có cơ chế **Human-in-the-Loop (HITL)** để người dùng bấm xác nhận cuối cùng.
  - **Circuit Breakers (Aptomat tự ngắt):** Thiết lập giới hạn cứng về chi phí (Budget Cap) trên hệ thống Telemetry. Nếu Agent vượt quá $0.5 cho một session do kẹt vòng lặp, hệ thống sẽ tự động ngắt kết nối (Kill switch) để bảo vệ tài chính.

- **Performance (Tối ưu Hiệu suất)**:
  - **RAG for Tools (Dynamic Tool Retrieval):** Khi hệ thống mở rộng lên hàng trăm công cụ, việc nhét tất cả Schema vào System Prompt sẽ làm quá tải Context Window. Giải pháp là dùng Vector Database để lưu trữ Tools. Khi người dùng hỏi, hệ thống chỉ trích xuất (Retrieve) top 3 công cụ phù hợp nhất để đưa cho Agent.
  - **Semantic Caching:** Sử dụng Redis Cache kết hợp với Vector Search. Nếu truy vấn hiện tại có ý nghĩa tương đồng 95% với một truy vấn cũ (vd: *"Tìm laptop 15 củ"* vs *"Gợi ý laptop mười lăm triệu"*), hệ thống sẽ trả luôn kết quả cũ thay vì kích hoạt lại vòng lặp ReAct, tiết kiệm 100% chi phí LLM cho lượt đó.
---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
