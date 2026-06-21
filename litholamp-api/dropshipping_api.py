import asyncio

class DropshippingFulfillmentAPI:
    def __init__(self):
        # Maps our internal hardware ID to the supplier's SKU
        self.sku_mapping = {
            "RoundWoodBase": "SKU-WOOD-RND-100",
            "SquareWoodBase": "SKU-WOOD-SQR-100",
            "DarkWoodBase": "SKU-WOOD-DRK-100",
            "TiffanyDesk": "SKU-TFF-DSK-01",
            "TiffanyFloor": "SKU-TFF-FLR-01"
        }

    async def place_order(self, hardware: str, shipping_details: dict):
        """
        Mocks placing an order with an official B2B dropshipping supplier (e.g., AliExpress, CJ Dropshipping, Spocket).
        This is secure, reliable, and meant for production e-commerce.
        """
        sku = self.sku_mapping.get(hardware, "UNKNOWN-SKU")
        
        print(f"\n[DROPSHIPPER] Sending B2B API request to fulfillment partner for SKU: {sku}...")
        
        # Simulate network latency for API request
        await asyncio.sleep(1)
        
        print(f"[DROPSHIPPER] Received Shipping Payload: {shipping_details['name']}, {shipping_details['address'].get('city', 'Unknown')}")
        
        # Simulate successful order placement
        order_number = f"DS-{random.randint(10000, 99999)}"
        
        print(f"[DROPSHIPPER] SUCCESS! Order {order_number} placed via API. Supplier will blind-ship to customer.")
        return {"status": "success", "supplier_order_id": order_number}

import random
dropshipper = DropshippingFulfillmentAPI()
