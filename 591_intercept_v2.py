#!/usr/bin/env python3
"""
591 Land Map API Interceptor v2
自動攔截並儲存 API 回應
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan_data.json"
API_DATA_FILE = Path(__file__).parent / "591_api_data.json"

# 儲存所有攔截到的 API 資料
all_api_data = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 攔截回應
        async def handle_response(response):
            url = response.url
            # 只處理 591 的 API
            if "591.com.tw" in url and ("land" in url or "map" in url or "tenor" in url):
                try:
                    # 嘗試取得 JSON
                    json_data = await response.json()
                    print(f"✅ JSON: {response.status} {url}")
                    all_api_data.append({
                        "url": url,
                        "status": response.status,
                        "data": json_data
                    })
                except:
                    # 如果不是 JSON，嘗試取得文字
                    try:
                        text = await response.text()
                        if len(text) < 50000:
                            print(f"✅ Text: {response.status} {url[:80]}")
                            all_api_data.append({
                                "url": url,
                                "status": response.status,
                                "text": text[:5000]
                            })
                    except:
                        pass
        
        page.on("response", handle_response)
        
        # 導航
        print("🌐 前往 591...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await page.wait_for_timeout(5000)
        
        print("⏳ 等待載入 (30秒)...")
        await page.wait_for_timeout(30000)
        
        # 儲存
        print(f"\n💾 儲存 {len(all_api_data)} 個 API 回應")
        with open(API_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(all_api_data, f, ensure_ascii=False, indent=2)
        
        await browser.close()
        print(f"✅ 完成！儲存至 {API_DATA_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
