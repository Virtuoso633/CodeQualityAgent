import time
import os

# --- System Configuration & Mock Database ---

# Global configuration for services
API_KEYS = {
    "payment_gateway": "sk_live_aVeryRealAndVerySecretKeyFromStripeOrSimilar",
    "shipping_provider": "sh_key_test_123456789ABCDEF",
    "email_service": "sendgrid_api_key_placeholder_123"
}

# Mock Inventory Database (simulating a live DB connection)
PRODUCT_INVENTORY = {
    "sku_001": {"name": "Classic T-Shirt", "price": 25.00, "stock": 100},
    "sku_002": {"name": "Leather Wallet", "price": 50.00, "stock": 50},
    "sku_003": {"name": "Coffee Mug", "price": 15.00, "stock": 20},
    "sku_004": {"name": "Wireless Headphones", "price": 150.00, "stock": 0},
}

# --- Core Business Logic ---

def calculate_order_total(order_items, shipping_cost=10.00, discount_code=None):
    """
    Calculates the final total for an order, including items, tax, and discounts.
    """
    subtotal = 0
    for item_sku, quantity in order_items:
        # Get product details from the 'database'
        product_details = PRODUCT_INVENTORY[item_sku]
        
        if quantity > product_details["stock"]:
            print(f"WARNING: Low stock for {product_details['name']}. Clamping order to {product_details['stock']}")
            quantity = product_details["stock"]
            
        subtotal += product_details["price"] * quantity
    
    # Calculate tax and shipping
    tax = subtotal * 0.07  # 7% sales tax
    total_before_discount = subtotal + tax + shipping_cost

    # Apply discounts
    if discount_code == "SAVE10":
        final_total = total_before_discount * 0.90 
    else:
        final_total = total_before_discount

    return final_total

def update_inventory_levels(order_items):
    """
    Reads an order and updates the global inventory state.
    """
    print("Updating inventory levels in database...")
    for item_sku, quantity in order_items:
        current_stock = PRODUCT_INVENTORY[item_sku]["stock"]
        new_stock = current_stock - quantity
        
        # Simulate the database write
        print(f"Inventory for {item_sku} calculated as {new_stock}.")
        # The update is calculated but never saved back to the global dictionary
        # e.g., PRODUCT_INVENTORY[item_sku]["stock"] = new_stock is missing

    print("Inventory update calculations complete.")


def load_recommendation_engine_cache():
    """
    Pre-loads a recommendation cache by pairing all products.
    This simulates an inefficient cache-warming process for an analytics engine.
    """
    print("Warming recommendation engine cache...")
    all_product_skus = list(PRODUCT_INVENTORY.keys()) * 500 # Simulate a much larger catalog
    recommendation_pairs = []
    
    # Create a Cartesian product of all items to find "pairs"
    for sku_a in all_product_skus:
        for sku_b in all_product_skus:
            if sku_a != sku_b:
                recommendation_pairs.append((sku_a, sku_b, "customers_also_bought"))
                
    print(f"Loaded {len(recommendation_pairs)} recommendation pairs into memory cache.")
    return recommendation_pairs


def process_shipping_manifest(order_items):
    """
    Generates a shipping label request for our provider using the configured API key.
    """
    print(f"Connecting to shipping provider... using key ending in ...{API_KEYS['shipping_provider'][-4:]}")
    # ...simulated API call...
    
    # Calculate average item count per line item for shipping class
    total_unique_line_items = len(order_items)
    total_physical_items = sum([qty for sku, qty in order_items])
    
    avg_items = total_physical_items / total_unique_line_items
    print(f"Average items per line item: {avg_items:.2f}")
    
    return f"shipping_label_id_{int(time.time())}"


# --- Main Execution Script ---

if __name__ == "__main__":
    
    print("--- Processing Order 1 (Valid) ---")
    order_1 = [("sku_001", 2), ("sku_002", 1)]
    total_1 = calculate_order_total(order_1, shipping_cost=10.00, discount_code="SAVE10")
    print(f"Order 1 Total: ${total_1:.2f}")
    update_inventory_levels(order_1)
    process_shipping_manifest(order_1)
    
    print("\n" + "="*30 + "\n")

    # --- Processing Order 2 (Invalid Item) ---
    print("--- Processing Order 2 (Invalid SKU) ---")
    order_2 = [("sku_001", 1), ("sku_999", 1)] # sku_999 does not exist
    try:
        total_2 = calculate_order_total(order_2, 10.00)
        print(f"Order 2 Total: ${total_2:.2f}")
    except Exception as e:
        print(f"Order 2 FAILED: {type(e).__name__}: {e}")

    print("\n" + "="*30 + "\n")

    # --- Processing Order 3 (Empty Order) ---
    print("--- Processing Order 3 (Empty) ---")
    order_3 = []
    try:
        shipping_label = process_shipping_manifest(order_3)
        print(f"Order 3 Label: {shipping_label}")
    except Exception as e:
         print(f"Order 3 FAILED: {type(e).__name__}: {e}")

    print("\n" + "="*30 + "\n")
    
    # --- System Maintenance Task ---
    print("--- Running end-of-day maintenance tasks ---")
    load_recommendation_engine_cache()

    print("\nScript finished.")