TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Check if a product is in stock by its name",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product to check stock"
                    }
                },
                "required": ["product_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "Get price and discount information of a product",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product to get price"
                    }
                },
                "required": ["product_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_total",
            "description": "Tính tổng tiền của giỏ hàng dựa trên danh sách ID sản phẩm, có tính đến tình trạng kho và giảm giá.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_ids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Danh sách các mã định danh (ID) của sản phẩm để tính tổng tiền."
                    }
                },
                "required": ["item_ids"]
            }
        }
    }
]