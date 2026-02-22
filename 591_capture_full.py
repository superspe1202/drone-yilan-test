#!/usr/bin/env python3
"""
591 - 完整攔截請求和回應
"""

import asyncio
import json
from playwright.async_api import async_playwright

OUTPUT_FILE = "/Users/superspe/.openclaw/workspace/591_full_capture.json"
captured = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        # 攔截請求
        async def handle_request(request):
            if "bff-business" in request.url and "land" in request.url:
                try:
                    # 嘗試取得 POST 資料
                    post_data = None
                    if request.method == "POST":
                        try:
                            post_data = await request.post_data
                            if post_data:
                                post_data = post_data.decode('utf-8')
                        except:
                            pass
                    
                    captured.append({
                        "type": "request",
                        "url": request.url,
                        "method": request.method,
                        "post_data": post_data
                    })
                    print(f"📤 {request.method} {request.url[:60]}...")
                except:
                    pass
        
        # 攔截回應
        async def handle_response(response):
            if "bff-business" in response.url and "land" in response.url:
                try:
                    data = await response.json()
                    captured.append({
                        "type": "response",
                        "url": response.url,
                        "status": response.status,
                        "data": data
                    })
                    print(f"📥 {response.status} {response.url[:60]}...")
                except:
                    pass
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        print("\n🌐 前往 591...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await asyncio.sleep(3)
        
        print("\n" + "="*50)
        print("請選擇武淵二段，然後點擊土地")
        print("我會持續監聽...")
        print("="*50)
        
        # 持續監聽
        for i in range(120):
            await asyncio.sleep(1)
            if i % 20 == 0:
                print(f"⏰ {i}秒, 已捕獲 {len(captured)} 個")
        
        # 儲存
        print(f"\n💾 儲存 {len(captured)} 個...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(captured, f, ensure_ascii=False, indent=2)
        
        print(f"✅ -> {OUTPUT_FILE}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
