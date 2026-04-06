def get_price(item_name: str) -> str:
    """Get the price of an item."""
    # Mock data in VND
    prices = {
        "laptop": 4000000,
        "mouse": 200000,
        "keyboard": 250000,
        "tai nghe": 500000,
        "chuột": 200000,
        "bàn phím": 250000
    }
    item = item_name.lower()
    if item in prices:
        return f"Price for {item_name}: {prices[item]:,} VND"
    return f"Item '{item_name}' not found in inventory"