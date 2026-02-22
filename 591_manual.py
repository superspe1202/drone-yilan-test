#!/usr/bin/env python3
"""
591 土地資料擷取 - 讓使用者手動選擇地段後自動擷取
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan2_data.json"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        print("🌐 前往 591 土地地圖...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await page.wait_for_timeout(3000)
        
        print("\n" + "="*50)
        print("請手動操作：")
        print("1. 點擊「鄉鎮/地段/捷運」")
        print("2. 選擇「地段」標籤")
        print("3. 搜尋並選擇「武淵二段」")
        print("4. 點擊「確定」")
        print("="*50)
        print("\n完成後直接關閉瀏覽器，或等待自動擷取...")
        
        # 等待一段時間讓使用者操作
        await page.wait_for_timeout(45)
        
        # 嘗試從頁面提取土地資料
        print("\n📊 正在提取土地資料...")
        
        # 方法1: 從頁面文字提取
        page_text = await page.inner_text("body")
        
        # 解析土地列表
        lands = []
        lines = page_text.split("\n")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # 檢測是否為地段名稱 (包含 "段" 且後面有 "地號")
            if "段" in line and i+1 < len(lines):
                next_line = lines[i+1].strip()
                if "地號" in next_line:
                    land_number = next_line.replace("地號", "").strip()
                    # 嘗試取得更多資訊
                    area = None
                    price = None
                    
                    # 向後尋找面積和價格
                    for j in range(i+2, min(i+10, len(lines))):
                        if "坪" in lines[j]:
                            area = lines[j].strip()
                        if "萬/坪" in lines[j] or "元/坪" in lines[j]:
                            price = lines[j].strip()
                    
                    lands.append({
                        "section": line,
                        "land_number": land_number,
                        "area": area,
                        "price": price
                    })
            i += 1
        
        print(f"   找到 {len(lands)} 筆土地資料 (初步解析)")
        
        # 方法2: 嘗試從 DOM 提取更詳細的資料
        try:
            # 嘗試找到土地列表元素
            land_items = await page.query_selector_all("[class*='land'], [class*='item'], .list-item")
            print(f"   DOM 找到 {len(land_items)} 個元素")
        except:
            pass
        
        # 方法3: 嘗試從側邊欄提取
        try:
            sidebar = await page.query_selector(".side-list, .land-list, [class*='side']")
            if sidebar:
                sidebar_text = await sidebar.inner_text()
                print(f"   側邊欄長度: {len(sidebar_text)} 字元")
        except:
            pass
        
        # 儲存結果
        result = {
            "source": "591 land map",
            "region": "宜蘭縣",
            "section": "武淵二段",
            "extracted_lands": lands[:100],  # 限制數量
            "page_text_preview": page_text[:10000]
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已儲存至 {OUTPUT_FILE}")
        print(f"   土地筆數: {len(lands)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
