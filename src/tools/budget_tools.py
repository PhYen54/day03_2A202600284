import json
import os
from typing import List, Dict, Any

# Đường dẫn file dữ liệu
DATA_PATH = "products_mockdata.json"

def load_products() -> List[Dict[str, Any]]:
    """
    Hàm bổ trợ để load dữ liệu từ JSON.
    """
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================
# TOOLS CHO AGENT (Sẽ được khai báo trong Agent.tools)
# ============================================================

def get_products_by_category(category: str = None) -> str:
    """
    Lấy danh sách sản phẩm theo danh mục (laptop, keyboard, mouse).
    Trả về chuỗi chứa đầy đủ thông tin: ID, Giá gốc, % Giảm giá, Hiệu năng, Tồn kho.
    """
    products = load_products()
    if category:
        filtered = [p for p in products if p["category"].lower() == category.lower()]
    else:
        filtered = products

    if not filtered:
        return f"Không tìm thấy sản phẩm nào trong danh mục: {category}"

    output = []
    for p in filtered:
        # Tính toán giá sau giảm để Agent dễ so sánh
        final_price = int(p["price"] * (1 - p.get("discount_percent", 0) / 100))
        info = (f"ID: {p['id']} | Name: {p['name']} | "
                f"Net Price: {final_price:,}đ | "
                f"Perf: {p['performance_score']} | Stock: {p['stock']}")
        output.append(info)
    
    return "\n".join(output)

def validate_combination(item_ids_str: str) -> str:
    """
    Nhận vào chuỗi ID các sản phẩm (cách nhau bởi dấu phẩy), ví dụ: "L0002, K0009, M0007".
    Kiểm tra tồn kho, tính tổng tiền và tổng hiệu năng.
    """
    try:
        id_list = [i.strip() for i in item_ids_str.replace("[", "").replace("]", "").split(",")]
        products = load_products()
        selected = [p for p in products if p["id"] in id_list]

        if len(selected) != len(id_list):
            return "Lỗi: Một hoặc nhiều mã sản phẩm không tồn tại trong hệ thống."

        total_price = 0
        total_perf = 0
        out_of_stock = []
        bill_lines = []

        for p in selected:
            final_p = int(p["price"] * (1 - p.get("discount_percent", 0) / 100))
            total_price += final_p
            total_perf += p["performance_score"]
            bill_lines.append(f"- {p['name']} ({p['id']}): {final_p:,}đ [Perf: {p['performance_score']}]")
            
            if p["stock"] <= 0:
                out_of_stock.append(p["name"])

        # Tạo báo cáo chi tiết cho Agent
        status = "Hợp lệ" if not out_of_stock else f"Hết hàng ({', '.join(out_of_stock)})"
        
        result = [
            "--- KẾT QUẢ KIỂM TRA COMBO ---",
            "\n".join(bill_lines),
            f"Tổng tiền: {total_price:,}đ",
            f"Tổng hiệu năng: {total_perf}",
            f"Trạng thái kho: {status}",
            "----------------------------"
        ]
        return "\n".join(result)

    except Exception as e:
        return f"Lỗi xử lý dữ liệu: {str(e)}"

# ============================================================
# ĐỊNH NGHĨA DANH SÁCH TOOL ĐỂ TRUYỀN VÀO AGENT
# ============================================================
TOOLS_LIST = [
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