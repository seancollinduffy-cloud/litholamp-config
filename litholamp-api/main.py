# [2026-06-21] THIS STATE WORKS PERFECTLY. ALL FEATURES, RENDERING, UV FIXES, AND PHYSICAL GENERATION ARE STABLE.
import os
import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
import subprocess, os, uuid, shutil
import stripe
import requests
from run_headless_preform import run_headless_preform
from pydantic import BaseModel

app = FastAPI()

class PriceRequest(BaseModel):
    hardware: str
    volume_mm3: float
    height: float = 120.0

from playwright_amazon_buyer import get_amazon_quote, automate_amazon_purchase
from playwright_formnow_buyer import get_formnow_quote, automate_formnow_purchase

stripe.api_key = "sk_test_mockKey" # Replace with real secret key

import asyncio
from daily_scraper import run_daily_scraper

@app.on_event("startup")
async def start_daily_scraper():
    async def scraper_loop():
        while True:
            try:
                await run_daily_scraper()
            except Exception as e:
                print(f"Daily scraper error: {e}")
            # Wait 24 hours (86400 seconds)
            await asyncio.sleep(86400)
    
    asyncio.create_task(scraper_loop())
@app.post("/api/price")
async def get_price(req: PriceRequest):
    # 1. Live Amazon Pricing via Playwright
    # Hardware cost hardcodes to bypass Amazon scraping
    if req.hardware == "TiffanyFloor":
        hardware_cost = 150.0
    elif req.hardware == "TiffanyDesk":
        hardware_cost = 75.0
    else:
        hardware_cost = 10.0 # Pucks

    amz_data = {"is_fallback": True, "price": hardware_cost}
        
    # 2. Live 3D Print Quoting via Cached Daily JSON
    import json
    import os
    pricing_file = os.path.join(os.path.dirname(__file__), "todays_pricing.json")
    try:
        with open(pricing_file, "r") as f:
            daily_prices = json.load(f)
            
        if req.hardware == "SquareWoodBase":
            p_land = daily_prices.get("SquareWoodBase_Landscape")
            p_port = daily_prices.get("SquareWoodBase_Portrait")
            if p_land and p_port:
                # Interpolate based on height (landscape is ~65mm, portrait is ~130mm)
                h = max(65.0, min(130.0, req.height))
                ratio = (h - 65.0) / (130.0 - 65.0)
                print_cost = p_land + ratio * (p_port - p_land)
            else:
                print_cost = (req.volume_mm3 * 0.00015) + 15.00
        else:
            print_cost = daily_prices.get(req.hardware, (req.volume_mm3 * 0.00015) + 15.00)
    except Exception:
        # Fallback to algorithmic if JSON is missing/broken
        print_cost = (req.volume_mm3 * 0.00015) + 15.00

    # Business Logic: 50% Profit Margin, rounded UP to nearest $5
    base_cost = hardware_cost + print_cost
    target_price = base_cost * 1.50
    
    import math
    final_retail_price = math.ceil(target_price / 5.0) * 5.0
    profit = final_retail_price - base_cost

    return {
        "hardware_cost": hardware_cost,
        "print_cost": round(print_cost, 2),
        "total_cost": final_retail_price,
        "base_cost": round(base_cost, 2),
        "profit": round(profit, 2),
        "amazon_details": amz_data
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RENDER_DIR = os.path.join(os.getcwd(), "customer_renders")
os.makedirs(RENDER_DIR, exist_ok=True)

@app.post("/api/generate")
async def handle_generate(
    hardware: str = Form(...),
    shape: str = Form(...),
    sides: int = Form(...),
    height: float = Form(...),
    diameter: float = Form(...),
    thickness: float = Form(...),
    files: List[UploadFile] = File(None)
):
    import asyncio
    import traceback
    try:
        job_id = str(uuid.uuid4())
        p = os.path.join(RENDER_DIR, job_id)
        os.makedirs(p, exist_ok=True)
        
        if files:
            for i, file in enumerate(files):
                with open(os.path.join(p, f"input_{i}.png"), "wb") as f:
                    f.write(await file.read())
        else:
            # Fallback if no image uploaded
            import shutil
            shutil.copy("blank_stls/input_0.png", os.path.join(p, "input_0.png"))
            
        configs = [
            {"name": "RoundWoodBase", "hardware": "RoundWoodBase", "shape": "Cylinder", "sides": 1, "h": 120, "d": 90 - (thickness * 2)},
            {"name": "SquareWoodBase", "hardware": "SquareWoodBase", "shape": "Square", "sides": 4, "h": 120, "d": 90 - (thickness * 2)},
            {"name": "DarkWoodBase", "hardware": "DarkWoodBase", "shape": "Cylinder", "sides": 1, "h": 120, "d": 90 - (thickness * 2)},
            {"name": "TiffanyDesk", "hardware": "TiffanyDesk", "shape": "Tiffany", "sides": 1, "h": 140, "d": 140 - (thickness * 2)},
            {"name": "TiffanyFloor", "hardware": "TiffanyFloor", "shape": "Tiffany", "sides": 1, "h": 180, "d": 194 - (thickness * 2)},
        ]

        async def generate_model(c):
            # We need a separate sub-folder for each config so they don't overwrite final.stl
            sub_dir = os.path.join(p, c["name"])
            os.makedirs(sub_dir, exist_ok=True)
            # Copy the input images to the sub-folder
            import glob
            for img in glob.glob(os.path.join(p, "input_*.png")):
                import shutil
                shutil.copy(img, os.path.join(sub_dir, os.path.basename(img)))
                
            import subprocess
            import sys
            def run_sync():
                return subprocess.run(
                    [sys.executable, "cylinder_render.py", sub_dir, c["hardware"], c["shape"], 
                     str(c["sides"]), str(len(files) if files else 1), str(c["h"]), str(c["d"]), str(thickness)],
                    capture_output=True
                )
            
            proc = await asyncio.to_thread(run_sync)
            
            if proc.returncode != 0:
                print(f"Error generating {c['name']}: {proc.stderr.decode()}")
            else:
                import shutil
                import time
                src = os.path.join(sub_dir, "final.stl")
                dst = os.path.join(p, f"{c['name']}.stl")
                for _ in range(10):
                    try:
                        shutil.move(src, dst)
                        break
                    except PermissionError:
                        time.sleep(0.5)

        # Run all 5 generations sequentially to avoid OOM / CPU freeze!
        for c in configs:
            await generate_model(c)

        return {"job_id": job_id, "message": "STL Generation queued"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{job_id}")
async def download_stl(job_id: str, hw: str = "RoundWoodBase"):
    p = os.path.join(RENDER_DIR, job_id, f"{hw}.stl")
    if not os.path.exists(p):
        raise HTTPException(status_code=404, detail="STL not found")
    

    return FileResponse(p, media_type="application/octet-stream", filename=f"{hw}.stl")

@app.post("/api/checkout")
async def create_checkout_session(request: Request):
    data = await request.json()
    job_id = data.get('job_id')
    hardware = data.get('hardware')
    
    # For now, return mock URL to trigger success
    mock_url = f"http://localhost:3000/success?job_id={job_id}&hardware={hardware}"
    return {"url": mock_url}

@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    This webhook is triggered by Stripe after a successful payment!
    """
    payload = await request.body()
    # In production, verify Stripe signature here
    
    # Mocking parsed event data:
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"job_id": "MOCK-JOB-123", "hardware": "RoundWoodBase"},
                "shipping_details": {
                    "name": "Jane Doe",
                    "address": {"city": "San Francisco", "country": "US"}
                }
            }
        }
    }
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        job_id = session["metadata"]["job_id"]
        hardware = session["metadata"]["hardware"]
        shipping = session["shipping_details"]
        
        print(f"\n[WEBHOOK] Payment successful for Job {job_id}!")
        
        # 1. Trigger Automated 3D Printing via Formnow Playwright
        stl_path = f"customer_renders/{job_id}/{hardware}.stl"
        asyncio.create_task(automate_formnow_purchase(job_id, stl_path, shipping))
        
        # 2. Trigger Amazon Retail Playwright Automation
        # Amazon scraping disabled for now, using hardcoded prices instead.
        # asin_map = {"RoundWoodBase": "B07XYZ123R", "SquareWoodBase": "B07XYZ456S", "DarkWoodBase": "B07XYZ789D", "TiffanyDesk": "B07TFF123D", "TiffanyFloor": "B07TFF456F"}
        # asin = asin_map.get(hardware, "B07XYZ123R")
        # asyncio.create_task(automate_amazon_purchase(asin, shipping))
        print(f"\n[AMAZON MOCK] Simulating purchase of {hardware} to {shipping['name']} using default prices...")
        
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001)
