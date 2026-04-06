import json
import os
from typing import List, Dict, Any

# ============================================================
# 1️⃣ QUẢN LÝ DỮ LIỆU SẢN PHẨM
# ============================================================

DATA_PATH = "products_mockdata.json"

def load_products() -> List[Dict[str, Any]]:
    """Load dữ liệu sản phẩm từ file JSON"""
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================
# 2️⃣ LỌC VÀ HIỂN THỊ SẢN PHẨM
# ============================================================

def get_products_by_category(category: str = None) -> str:
    """
    Lấy danh sách sản phẩm theo category: laptop, keyboard, mouse
    Trả về chuỗi: ID, Name, Giá Net, Hiệu năng, Stock
    """
    products = load_products()
    filtered = [p for p in products if category is None or p["category"].lower() == category.lower()]

    if not filtered:
        return f"Không tìm thấy sản phẩm trong danh mục: {category}"

    output = []
    for p in filtered:
        final_price = int(p["price"] * (1 - p.get("discount_percent", 0) / 100))
        output.append(f"ID: {p['id']} | Name: {p['name']} | Net Price: {final_price:,}đ | Perf: {p['performance_score']} | Stock: {p['stock']}")
    
    return "\n".join(output)


def check_stock(product_name: str) -> Dict[str, Any]:
    """Kiểm tra tồn kho dựa theo tên sản phẩm"""
    products = load_products()
    for p in products:
        if product_name.lower() in p["name"].lower():
            return {
                "id": p["id"],
                "name": p["name"],
                "in_stock": p["stock"] > 0,
                "stock": p["stock"]
            }
    return {"error": "Product not found"}


def get_price(product_name: str) -> Dict[str, Any]:
    """Lấy giá gốc, giảm giá và giá cuối của sản phẩm theo tên"""
    products = load_products()
    for p in products:
        if product_name.lower() in p["name"].lower():
            discount = p.get("discount_percent", 0)
            final_price = int(p["price"] * (1 - discount / 100))
            return {
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "discount_percent": discount,
                "final_price": final_price
            }
    return {"error": "Item not found"}


def check_discount(product_name: str) -> Any:
    """Trả về % giảm giá của sản phẩm"""
    products = load_products()
    for p in products:
        if product_name.lower() in p["name"].lower():
            return p.get("discount_percent", 0)
    return "product not found"

# ============================================================
# 3️⃣ TÍNH TOÁN GIỎ HÀNG / COMBO
# ============================================================

def calculate_total(item_ids: List[str]) -> Dict[str, Any]:
    """Tính tổng tiền và liệt kê sản phẩm trong giỏ hàng"""
    products = load_products()
    total_amount = 0
    calculated_items = []
    errors = []

    for item_id in item_ids:
        item = next((x for x in products if x["id"] == item_id), None)
        if not item:
            errors.append(f"Mã sản phẩm {item_id} không tồn tại.")
            continue
        if item["stock"] <= 0:
            errors.append(f"Sản phẩm {item['name']} ({item_id}) đã hết hàng.")
            continue
        final_price = int(item["price"] * (1 - item.get("discount_percent", 0)/100))
        total_amount += final_price
        calculated_items.append(f"{item['name']} ({final_price}đ)")

    return {
        "status": "success" if not errors else "partial_success_or_error",
        "total_amount": total_amount,
        "items_included": calculated_items,
        "warnings": errors
    }


def validate_combination(item_ids_str: str) -> str:
    """
    Kiểm tra combo sản phẩm: tồn kho, tổng tiền, tổng hiệu năng
    Trả về chuỗi báo cáo chi tiết
    """
    try:
        id_list = [i.strip() for i in item_ids_str.replace("[", "").replace("]", "").split(",")]
        products = load_products()
        selected = [p for p in products if p["id"] in id_list]

        if len(selected) != len(id_list):
            return "Lỗi: Một hoặc nhiều mã sản phẩm không tồn tại."

        total_price = 0
        total_perf = 0
        out_of_stock = []
        bill_lines = []

        for p in selected:
            final_price = int(p["price"] * (1 - p.get("discount_percent", 0) / 100))
            total_price += final_price
            total_perf += p["performance_score"]
            bill_lines.append(f"- {p['name']} ({p['id']}): {final_price:,}đ [Perf: {p['performance_score']}]")
            if p["stock"] <= 0:
                out_of_stock.append(p["name"])

        status = "Hợp lệ" if not out_of_stock else f"Hết hàng ({', '.join(out_of_stock)})"
        return "\n".join([
            "--- KẾT QUẢ KIỂM TRA COMBO ---",
            "\n".join(bill_lines),
            f"Tổng tiền: {total_price:,}đ",
            f"Tổng hiệu năng: {total_perf}",
            f"Trạng thái kho: {status}",
            "----------------------------"
        ])
    except Exception as e:
        return f"Lỗi xử lý dữ liệu: {str(e)}"

# ============================================================
# 4️⃣ DANH SÁCH TOOLS CHO AGENT
# ============================================================

TOOLS_LIST = [
    {"name": "get_products_by_category", "description": "Lấy sản phẩm theo danh mục", "func": get_products_by_category},
    {"name": "check_stock", "description": "Kiểm tra tồn kho theo tên", "func": check_stock},
    {"name": "get_price", "description": "Lấy giá sản phẩm theo tên", "func": get_price},
    {"name": "check_discount", "description": "Lấy % giảm giá sản phẩm", "func": check_discount},
    {"name": "calculate_total", "description": "Tính tổng giỏ hàng theo danh sách ID", "func": calculate_total},
    {"name": "validate_combination", "description": "Kiểm tra combo sản phẩm theo danh sách ID", "func": validate_combination}
]

# ============================================================
# 5️⃣ TEST NHANH
# ============================================================

if __name__ == "__main__":
    print("=== PRODUCTS BY CATEGORY ===")
    print(get_products_by_category("keyboard"))

    print("\n=== STOCK CHECK ===")
    print(check_stock("Akko 3068"))

    print("\n=== PRICE CHECK ===")
    print(get_price("Akko 3068"))

    print("\n=== DISCOUNT CHECK ===")
    print(check_discount("Akko 3068 Pro"))