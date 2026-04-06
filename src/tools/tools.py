import json

# 🔥 1. Hàm load data dùng chung
def load_products() -> list:
    with open("products_mockdata.json", "r", encoding="utf-8") as f:
        return json.load(f)


# 🔥 2. Check stock
def check_stock(product_name: str) -> dict:
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

def get_price(product_name: str) -> dict:
    products = load_products()

    for p in products:
        if product_name.lower() in p["name"].lower():
            price = p["price"]
            discount = p.get("discount_percent", 0)

            return {
                "id": p["id"],
                "name": p["name"],
                "price": price,
                "discount_percent": discount,
                "final_price": int(price * (1 - discount / 100))
            }

    return {"error": "Item not found"}

def calculate_total(item_ids: list) -> dict:
    """
    Tính tổng tiền của giỏ hàng dựa trên danh sách ID sản phẩm.
    """
    data = load_products()
    total_amount = 0
    calculated_items = []
    errors = []

    for item_id in item_ids:
        # Tìm sản phẩm trong database dựa vào ID
        item = next((x for x in data if x["id"] == item_id), None)
        
        if not item:
            errors.append(f"Mã sản phẩm {item_id} không tồn tại.")
            continue
            
        if item["stock"] <= 0:
            errors.append(f"Sản phẩm {item['name']} ({item_id}) đã hết hàng, không thể thêm vào tổng.")
            continue

        # Tính giá đã giảm
        base_price = item["price"]
        discount = item.get("discount_percent", 0)
        final_price = int(base_price * (1 - discount / 100))
        
        total_amount += final_price
        calculated_items.append(f"{item['name']} ({final_price}đ)")

    # Trả về một Dictionary chi tiết để Agent đọc và hiểu (Observation)
    result = {
        "status": "success" if not errors else "partial_success_or_error",
        "total_amount": total_amount,
        "items_included": calculated_items,
        "warnings": errors
    }

    return result

def check_discount(product_name: str) -> str:
    """
    check product name and and return discount
    """
    try:
        with open("products_mockdata.json", 'r', encoding='utf-8') as file:
            products = json.load(file)  
            for product in products:
                if product["name"] == product_name:
                    print(product["discount_percent"])
                    return product["discount_percent"]

            return "product not found"
    except FileNotFoundError:
        print("wrong file")


# ================= TEST =================
if __name__ == "__main__":
    print("=== STOCK ===")
    print(check_stock("Akko 3068"))

    print("\n=== PRICE ===")
    print(get_price("Akko 3068"))

    print(f"There is a {check_discount('Akko 3068 Pro')}% discount for Akko 3068 Pro")