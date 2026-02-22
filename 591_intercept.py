#!/usr/bin/env python3
"""
591 Land Map API Interceptor
使用 Playwright 攔截 591 土地地圖的 API 請求
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan_data.json"

async def main():
    captured_data = []
    
    async with async_playwright() as p:
        # 啟動瀏覽器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 攔截 API 請求
        async def handle_request(request):
            url = request.url
            # 捕捉可能的土地 API
            if "land" in url.lower() or "map" in url.lower() or "tenor" in url.lower():
                print(f"📡 Request: {request.method} {url}")
                
        async def handle_response(response):
            url = response.url
            # 只處理包含 land/map/tenor 的回應
            if any(keyword in url.lower() for keyword in ["land", "tenor", "map"]):
                try:
                    body = await response.text()
                    if body and len(body) < 50000:  # 避免過大的回應
                        print(f"✅ Response: {response.status} {url}")
                        captured_data.append({
                            "url": url,
                            "status": response.status,
                            "body": body[:10000]  # 限制大小
                        })
                except Exception as e:
                    print(f"⚠️ Error: {e}")
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # 導航到 591 土地地圖
        print("🌐 前往 591 土地地圖...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        
        # 等待頁面載入
        await page.wait_for_timeout(3000)
        
        print("⏳ 等待載入土地資料... (請在手動操作後按 Enter)")
        print("   請選擇：區域 → 宜蘭縣 → 武淵二段")
        
        # 讓使用者手動操作
        input("   完成操作後按 Enter 繼續...")
        
        # 等待一段時間讓 API 請求完成
        await page.wait_for_timeout(5000)
        
        # 儲存結果
        print(f"\n💾 儲存 {len(captured_data)} 個 API 回應到 {OUTPUT_FILE}")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(captured_data, f, ensure_ascii=False, indent=2)
        
        await browser.close()
        print("✅ 完成！")

if __name__ == "__main__":
    asyncio.run(main())
