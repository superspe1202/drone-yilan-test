#!/usr/bin/env python3
"""
591 Land Map - 直接從頁面提取數據
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_land_data.json"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        print("🌐 前往 591 土地地圖...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        
        # 等待地圖載入
        await page.wait_for_timeout(3000)
        
        print("📍 嘗試選擇區域...")
        
        # 點擊區域選擇器
        try:
            # 點擊 "鄉鎮/地段/捷運" 下拉選單
            await page.click("text=鄉鎮/地段/捷運")
            await page.wait_for_timeout(1000)
            
            # 選擇區域標籤
            await page.click("text=區域")
            await page.wait_for_timeout(500)
            
            # 點擊宜蘭縣 (需要找到正確的 selector)
            # 先嘗試點擊第一個區域
            regions = await page.query_selector_all(".location-select-item")
            if regions:
                for i, r in enumerate(regions):
                    text = await r.inner_text()
                    print(f"  發現: {text}")
                    if "宜蘭" in text:
                        await r.click()
                        break
            
            await page.wait_for_timeout(2000)
            
            # 選擇地段標籤
            await page.click("text=地段")
            await page.wait_for_timeout(1000)
            
            # 輸入武淵二段
            await page.fill("input[placeholder*='搜尋']", "武淵二段")
            await page.wait_for_timeout(1000)
            
            # 點擊搜尋結果
            suggestions = await page.query_selector_all(".location-select-item")
            for s in suggestions:
                text = await s.inner_text()
                if "武淵二段" in text:
                    await s.click()
                    break
            
            await page.wait_for_timeout(1000)
            
            # 點擊確定
            await page.click("text=確定")
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"⚠️ 操作錯誤: {e}")
        
        # 等待資料載入
        print("⏳ 等待資料載入...")
        await page.wait_for_timeout(10000)
        
        # 嘗試取得頁面資料
        print("📊 嘗試提取資料...")
        
        # 取得 URL
        current_url = page.url
        print(f"   URL: {current_url}")
        
        # 嘗試從 localStorage 取得資料
        land_data = await page.evaluate("""
            () => {
                const data = {};
                // 檢查 localStorage
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key.includes('land') || key.includes('map')) {
                        try {
                            data[key] = JSON.parse(localStorage.getItem(key));
                        } catch(e) {
                            data[key] = localStorage.getItem(key);
                        }
                    }
                }
                return data;
            }
        """)
        
        if land_data:
            print(f"   找到 {len(land_data)} 個 localStorage 項目")
        
        # 取得頁面文字內容
        page_text = await page.inner_text("body")
        print(f"   頁面內容長度: {len(page_text)} 字元")
        
        # 儲存
        result = {
            "url": current_url,
            "land_data": land_data,
            "page_text": page_text[:5000]
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 儲存至 {OUTPUT_FILE}")
        
        # 保持瀏覽器開啟，讓使用者查看
        print("\n🔔 按 Enter 關閉瀏覽器...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
