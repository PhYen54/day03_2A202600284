# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Trần Vọng Triển
- **Student ID**: 2A202600320
- **Date**: 06/04/2026
---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: products_mockdata.json / products_mockdata.csv: dữ liệu mẫu chứa danh sách các sản phẩm (Laptop, Keyboard, Mouse) với đầy đủ các thuộc tính: id, name, price, discount_percent, performance_score, và stock. Đây là nền tảng dữ liệu để Agent truy vấn.

src/agent/agent.py: Triển khai lớp ReActAgent, thiết lập System Prompt chuyên biệt cho vai trò trợ lý mua sắm và quản lý logic của vòng lặp Thought-Action-Observation.

main.py (v.01): Xây dựng file thực thi chính để khởi tạo môi trường, nạp các công cụ (tools) và kích hoạt Agent để giải quyết truy vấn từ người dùng.
- **Code Highlights**: thiết kế System Prompt để ép Agent tuân thủ nghiêm ngặt định dạng ReAct, ngăn chặn việc mô hình tự ý trả về Markdown hoặc tự bịa đặt kết quả (hallucination) mà không gọi công cụ.Trong agent.py, triển khai vòng lặp while để điều phối luồng suy nghĩ. Hệ thống sẽ phân tách Action bằng Regex, thực thi công cụ và đưa kết quả ngược lại vào lịch sử hội thoại để Agent tiếp tục suy luận.
- **Documentation**: Hệ thống tương tác theo quy trình đóng kín:

Thought: Agent lập kế hoạch dựa trên ngân sách và ngưỡng hiệu năng.

Action: Gọi công cụ truy vấn dữ liệu từ mockdata.

Observation: Nhận dữ liệu thực tế (giá net, tồn kho) làm căn cứ duy nhất cho bước tiếp theo.

Final Answer: Tổng hợp bộ 3 sản phẩm tối ưu khi mọi điều kiện ràng buộc được thỏa mãn.
---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Dù người dùng yêu cầu combo gồm 1 laptop, 1 bàn phím và 2 chuột, Agent vẫn chỉ trả về kết quả có 1 chuột. Agent bị fix cứng bởi system promt và bỏ qua số lượng cụ thể trong câu hỏi.
- **Log Source**: input query:
 "Find a combination of laptop, keyboard, and two mouse
with total price under 15000000
and total performance above 120.
Check stock before selecting.
Then print the bill."

output: 
===== FINAL RESULT =====
The selected combination is:
Laptop: HP 245 Office (L0013) - 10,047,720đ
Keyboard: Logitech K120 V1 (K0009) - 287,100đ
Mouse: Logitech M170 SE (M0004) - 187,460đ
Total Price: 10,522,280đ
Total Performance: 150
Stock: Valid


- **Diagnosis**: Lỗi nằm ở System Prompt. Trong phần CORE TASK, hệ thống bị áp đặt quy tắc cứng: "Find a combination of EXACTLY 1 laptop, 1 keyboard, and 1 mouse". Khi LLM đối mặt với sự mâu thuẫn giữa câu hỏi (2 chuột) và quy tắc hệ thống (1 chuột), nó ưu tiên tuân thủ quy tắc hệ thống (System Prompt) hơn là yêu cầu nhất thời của người dùng.
- **Solution**: Cập nhật System Prompt để tăng tính linh hoạt, cho phép Agent tự điều chỉnh số lượng dựa trên truy vấn của khách hàng.

Update System Prompt:

Thay đổi từ: "CORE TASK: Find a combination of EXACTLY 1 laptop, 1 keyboard, and 1 mouse..."
Thành: "        CORE TASK:
        1. Parse Query: Identify requested products, quantities, budget, and performance threshold.
        2. Handle Defaults: 
           - If NO quantity is specified: Default to 1 for that category.
           - If NO budget is specified: Assume budget is infinite.
           - If NO performance threshold is specified: Default to 0.
        
        Your goal is to find a combination of products satisfying:
        - Total Net Price (After discount) <= User's Budget (if any).
        - Total Performance >= User's Threshold (if any).
        - All selected items MUST have Stock > 0.
---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Khối Thought giúp Agent lập kế hoạch từng bước và kiểm soát logic trước khi hành động, thay vì trả lời cảm tính như Chatbot.
2.  **Reliability**: Agent hoạt động kém hơn Chatbot khi gặp các yêu cầu cần sự linh hoạt tự nhiên hoặc khi System Prompt bị thiết lập quá máy móc.
3.  **Observation**: Kết quả thực tế từ Observation đóng vai trò là "mỏ neo" dữ liệu, buộc Agent phải điều chỉnh suy luận dựa trên thực tế thay vì dự đoán.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Tích hợp công cụ Web Scraping (như Selenium hoặc Playwright) cho phép Agent truy cập trực tiếp các website thương mại điện tử để lấy dữ liệu giá cả và tồn kho theo thời gian thực thay vì dùng dữ liệu tĩnh.
- **Safety**: Thiết lập cơ chế Human-in-the-loop tại bước cuối cùng, yêu cầu người dùng xác nhận lại danh sách sản phẩm trong giỏ hàng và phê duyệt thanh toán trước khi Agent thực hiện đặt hàng chính thức.
- **Performance**: Xây dựng quy trình tự động hóa các thao tác lặp lại như đăng nhập và thêm hàng vào giỏ (Add to Cart) giúp giảm độ trễ và tối ưu hóa trải nghiệm người dùng từ lúc tìm kiếm đến khi hoàn tất đơn hàng.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
