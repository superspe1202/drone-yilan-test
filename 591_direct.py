#!/usr/bin/env python3
"""
591 Land Map - 使用 URL 參數直接載入
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan2_data.json"
API_RESPONSES = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        # 攔截 API 回應
        async def handle_response(response):
            url = response.url
            if "bff-business" in url and "land" in url:
                try:
                    data = await response.json()
                    print(f"📥 {response.status} {url[:60]}...")
                    if data.get("data"):
                        API_RESPONSES.append({"url": url, "data": data})
                except:
                    pass
        
        page.on("response", handle_response)
        
        # 嘗試不同的 URL 格式
        urls_to_try = [
            "https://land.591.com.tw/map?region_id=21&section=武淵二段&mode=tenor",
            "https://land.591.com.tw/map?region_id=21&section_id=武淵二段&mode=tenor", 
            "https://land.591.com.tw/map?region=21&section=武淵二段&mode=tenor",
        ]
        
        for url in urls_to_try:
            print(f"\n🌐 嘗試: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(5000)
            
            # 檢查 API 回應
            if API_RESPONSES:
                print(f"   ✅ 找到 {len(API_RESPONSES)} 個 API 回應!")
                break
        
        # 如果還是沒有，嘗試點擊
        if not API_RESPONSES:
            print("\n🔧 嘗試點擊操作...")
            await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor", wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            # 點擊區域選擇
            try:
                await page.click("div.dropdown-text:has-text('鄉鎮/地段/捷運')", timeout=5000)
                await page.wait_for_timeout(2000)
            except:
                pass
        
        # 儲存結果
        print(f"\n💾 儲存 {len(API_RESPONSES)} 個 API 回應")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(API_RESPONSES, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 完成! -> {OUTPUT_FILE}")
        
        print("\n🔔 瀏覽器將保持開啟 60 秒，請手動操作選擇武淵二段...")
        await page.wait_for_timeout(60000)
        
        # 再次儲存
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(API_RESPONSES, f, ensure_ascii=False, indent=2)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
