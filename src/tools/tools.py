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


# ================= TEST =================
if __name__ == "__main__":
    print("=== STOCK ===")
    print(check_stock("Akko 3068"))

    print("\n=== PRICE ===")
    print(get_price("Akko 3068"))