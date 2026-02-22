#!/usr/bin/env python3
"""
591 - 正確攔截 API 回應
"""

import asyncio
import json
from playwright.async_api import async_playwright

OUTPUT_FILE = "/Users/superspe/.openclaw/workspace/591_wuyuan_api.json"
results = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        async def handle_route(route):
            request = route.request
            
            # 只攔截目標 API
            if "land-transcript/map/s" in request.url:
                print(f"📤 攔截: {request.url[:50]}...")
                
                # 繼續請求
                try:
                    response = await route.continue_()
                    
                    # 取得回應內容
                    body = await response.text()
                    try:
                        data = json.loads(body)
                        if data.get("data"):
                            print(f"   ✅ 有資料! Keys: {list(data['data'].keys())[:5]}")
                            results.append({
                                "url": request.url,
                                "data": data["data"]
                            })
                    except:
                        pass
                except Exception as e:
                    print(f"   ❌ 錯誤: {e}")
            else:
                await route.continue_()
        
        await page.route("**/*", handle_route)
        
        print("\n🌐 前往 591...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await asyncio.sleep(3)
        
        print("\n" + "="*50)
        print("請選擇武淵二段，點擊土地項目")
        print("我會抓取 API 回應")
        print("="*50)
        
        for i in range(180):
            await asyncio.sleep(1)
            if i % 30 == 0 and i > 0:
                print(f"⏰ {i}秒, 已抓取 {len(results)} 個回應")
        
        # 儲存
        print(f"\n💾 儲存 {len(results)} 個回應...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 顯示結果
        print("\n📊 結果:")
        for r in results[:3]:
            print(f"  - Keys: {list(r['data'].keys())}")
        
        print(f"\n✅ -> {OUTPUT_FILE}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
