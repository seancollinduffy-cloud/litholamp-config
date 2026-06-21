import random
import time

class ManufacturingBidder:
    def __init__(self):
        self.services = ["Xometry API", "Hubs API", "Protolabs API", "Craftcloud API"]

    def get_quotes(self, stl_path: str, volume_mm3: float) -> list:
        """
        Simulates uploading an STL to multiple manufacturing APIs and waiting for their quotes.
        """
        print(f"[PROCUREMENT] Uploading {stl_path} to {len(self.services)} manufacturing networks...")
        time.sleep(1) # Simulate upload & processing time

        quotes = []
        base_cost = (volume_mm3 / 1000) * 0.15 # Approx base resin cost
        
        for service in self.services:
            # Simulate different pricing algorithms and markup strategies
            markup = random.uniform(1.8, 3.5)
            shipping = random.uniform(5.0, 15.0)
            total = (base_cost * markup) + shipping
            
            quotes.append({
                "service": service,
                "price": round(total, 2),
                "lead_time_days": random.randint(3, 10)
            })

        return quotes

    def place_order(self, job_id: str, hardware: str, stl_path: str, volume_mm3: float):
        """
        Runs the bidding process and automatically dispatches to the lowest bidder.
        """
        print(f"\n--- INITIATING AUTOMATED BIDDING FOR JOB {job_id} ---")
        quotes = self.get_quotes(stl_path, volume_mm3)
        
        # Sort by price ascending
        quotes.sort(key=lambda x: x["price"])
        
        print("[PROCUREMENT] Received Quotes:")
        for q in quotes:
            print(f"  - {q['service']}: ${q['price']} ({q['lead_time_days']} days)")
            
        winning_bid = quotes[0]
        print(f"[PROCUREMENT] => WINNING BID: {winning_bid['service']} for ${winning_bid['price']}")
        print(f"[PROCUREMENT] Dispatching STL payload to {winning_bid['service']}...")
        time.sleep(0.5)
        print("[PROCUREMENT] Order Confirmed. Manufacturer tracking ID generated.")
        
        return winning_bid

procurement = ManufacturingBidder()
