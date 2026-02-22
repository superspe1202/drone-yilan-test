#!/usr/bin/env python3
"""
591 Land Map API Interceptor v3 - Headless
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_api_data.json"

async def main():
    all_data = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 設置較長的超時
        page.set_default_timeout(60000)
        
        async def handle_response(response):
            url = response.url
            if "bff-business.591.com.tw" in url and "land" in url:
                try:
                    json_data = await response.json()
                    print(f"📥 {response.status} - {url[:100]}")
                    all_data.append({"url": url, "data": json_data})
                except:
                    pass
        
        page.on("response", handle_response)
        
        print("🌐 Loading 591...")
        await page.goto("https://land.591.com.tw/map?region_id=21&section=武淵二段&mode=tenor", wait_until="networkidle")
        
        print("⏳ Waiting for API...")
        await asyncio.sleep(15)
        
        print(f"\n💾 Saving {len(all_data)} responses...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        await browser.close()
        print(f"✅ Done! -> {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
