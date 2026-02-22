#!/usr/bin/env python3
"""
591 土地 - 攔截點擊時的 API 請求
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_api_intercept.json"

api_calls = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        # 攔截所有 API 請求
        async def handle_request(request):
            url = request.url
            if "591" in url or "bff" in url:
                print(f"📡 {request.method} {url[:80]}")
        
        async def handle_response(response):
            url = response.url
            if "bff" in url or "land" in url:
                try:
                    data = await response.json()
                    if data.get("data"):
                        print(f"✅ {response.status} {url[:60]}... -> 有資料")
                        api_calls.append({
                            "url": url,
                            "status": response.status,
                            "data": data
                        })
                except:
                    pass
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        url = "https://land.591.com.tw/map?region_id=21&mode=tenor&keyword=%E6%AD%A6%E6%B7%B5%E4%BA%8C%E6%AE%B5"
        
        print("\n🌐 前往...")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        print("\n📋 點擊土地...")
        
        # 點擊土地
        try:
            first = page.locator("[class*='land'], .item").first
            await first.click()
            await asyncio.sleep(3)
        except Exception as e:
            print(f"點擊失敗: {e}")
        
        # 滾動點擊更多
        for i in range(5):
            await page.evaluate("window.scrollBy(0, 200)")
            await asyncio.sleep(1)
            try:
                item = page.locator("[class*='land'], .item").nth(i)
                await item.click()
                await asyncio.sleep(2)
            except:
                pass
        
        print(f"\n📊 共攔截 {len(api_calls)} 個有資料的 API")
        
        # 顯示
        for i, call in enumerate(api_calls[:5]):
            print(f"\n--- API {i+1} ---")
            print(f"URL: {call['url'][:100]}")
            # 只顯示部分資料
            d = call.get("data", {})
            if isinstance(d, dict):
                keys = list(d.keys())[:3]
                print(f"Keys: {keys}")
        
        # 儲存
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(api_calls, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 儲存至 {OUTPUT_FILE}")
        
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
