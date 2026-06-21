import random
import time

# Mock Amazon Product Advertising API Client
class AmazonPAAPI:
    def __init__(self):
        # Database mapping internal hardware names to primary and fallback ASINs
        self.hardware_database = {
            "RoundWoodBase": {
                "primary": {"asin": "B07XYZ123R", "name": "Minimalist Round Wood LED Base", "expected_price": 15.00},
                "fallback": {"asin": "B08ABC456R", "name": "Basic Round LED Puck Light", "expected_price": 18.50}
            },
            "SquareWoodBase": {
                "primary": {"asin": "B07XYZ123S", "name": "Square Wood LED Base 100mm", "expected_price": 15.00},
                "fallback": {"asin": "B08ABC456S", "name": "Geometric LED Wood Stand", "expected_price": 20.00}
            },
            "DarkWoodBase": {
                "primary": {"asin": "B07XYZ123D", "name": "Walnut Finish LED Base", "expected_price": 17.00},
                "fallback": {"asin": "B08ABC456D", "name": "Dark Oak Display Stand", "expected_price": 19.50}
            },
            "TiffanyDesk": {
                "primary": {"asin": "B07XYZ123T", "name": "Vintage Bronze Desk Lamp Base", "expected_price": 45.00},
                "fallback": {"asin": "B08ABC456T", "name": "Antique Finish Table Lamp Base", "expected_price": 52.00}
            },
            "TiffanyFloor": {
                "primary": {"asin": "B07XYZ123F", "name": "Tall Bronze Floor Lamp Base", "expected_price": 85.00},
                "fallback": {"asin": "B08ABC456F", "name": "Classic Torchiere Floor Base", "expected_price": 105.00}
            }
        }

    def get_price_and_availability(self, hardware_name: str):
        """
        Mocks a call to the Amazon PA-API to check live stock and pricing.
        Simulates primary item being out of stock ~20% of the time.
        """
        if hardware_name not in self.hardware_database:
            return {"error": "Hardware not found"}

        data = self.hardware_database[hardware_name]
        
        # Simulate API latency
        time.sleep(0.3)
        
        # Simulate live stock check (20% chance primary is OOS)
        primary_in_stock = random.random() > 0.20
        
        if primary_in_stock:
            return {
                "status": "in_stock",
                "asin": data["primary"]["asin"],
                "name": data["primary"]["name"],
                "price": data["primary"]["expected_price"],
                "is_fallback": False
            }
        else:
            print(f"AMAZON API WARN: Primary ASIN {data['primary']['asin']} out of stock. Failing over to fallback.")
            return {
                "status": "fallback_in_stock",
                "asin": data["fallback"]["asin"],
                "name": data["fallback"]["name"],
                "price": data["fallback"]["expected_price"],
                "is_fallback": True
            }

amazon_client = AmazonPAAPI()
