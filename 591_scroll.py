#!/usr/bin/env python3
"""
591 土地資料擷取 v5 - 滾動載入更多資料
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan2_data.json"

async def select_section(page, section_name: str):
    """選擇地段"""
    print("  🔍 點擊下拉選單...")
    try:
        dropdown = page.locator("p:has-text('鄉鎮/地段/捷運'), div:has-text('鄉鎮/地段/捷運')").first
        await dropdown.click(timeout=3000)
        await asyncio.sleep(1)
    except:
        pass
    
    print("  🔍 選擇地段標籤...")
    try:
        section_tab = page.locator("div:has-text('地段')").first
        await section_tab.click(timeout=3000)
        await asyncio.sleep(1)
    except:
        pass
    
    print(f"  🔍 輸入 {section_name}...")
    try:
        search = page.locator("input[type='text'], input.search-input").first
        await search.fill(section_name)
        await search.press("Enter")
        await asyncio.sleep(2)
    except:
        pass
    
    print("  🔍 點擊搜尋結果...")
    try:
        await asyncio.sleep(1)
        result = page.locator(f"text={section_name}").first
        await result.click(timeout=3000)
        await asyncio.sleep(1)
    except:
        pass
    
    print("  🔍 點擊確定...")
    try:
        confirm = page.locator("button:has-text('確定')").first
        await confirm.click(timeout=3000)
        await asyncio.sleep(3)
    except:
        pass

async def scroll_to_load_more(page, max_scrolls: int = 20):
    """滾動頁面載入更多資料"""
    print("\n  ⬇️  滾動載入更多資料...")
    
    lands = []
    prev_count = 0
    
    for i in range(max_scrolls):
        # 滾動
        await page.evaluate("window.scrollBy(0, 500)")
        await asyncio.sleep(1)
        
        # 提取當前可見的土地
        items = await page.query_selector_all("[class*='land'], [class*='item'], .list-item")
        
        current_count = len(items)
        
        if current_count > prev_count:
            print(f"    滾動 {i+1}: {current_count} 筆")
            prev_count = current_count
        
        # 提取資料
        for item in items:
            try:
                text = await item.inner_text()
                if "地號" in text and "段" in text:
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    
                    land_num = None
                    area = None
                    price = None
                    land_type = None
                    
                    for line in lines:
                        if "地號" in line and not land_num:
                            land_num = line
                        elif "坪" in line and not area:
                            area = line
                        elif ("萬/坪" in line or "元/坪" in line) and not price:
                            price = line
                        elif "都市" in line or "非都市" in line:
                            land_type = line
                    
                    if land_num:
                        # 避免重複
                        exists = any(l.get("land_number") == land_num for l in lands)
                        if not exists:
                            lands.append({
                                "land_number": land_num,
                                "area": area,
                                "price": price,
                                "land_type": land_type
                            })
            except:
                pass
        
        # 檢查是否已載入全部
        if current_count >= 100:  # 假設最多顯示約100筆
            break
    
    return lands

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        print("\n🌐 前往 591 土地地圖...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await page.wait_for_timeout(5000)
        
        print("\n🎯 選擇武淵二段...")
        await select_section(page, "武淵二段")
        
        # 等待初始載入
        await page.wait_for_timeout(5000)
        
        # 滾動載入更多
        lands = await scroll_to_load_more(page, max_scrolls=30)
        
        # 顯示結果
        page_text = await page.inner_text("body")
        is_wuyuan2 = "武淵二段" in page_text
        current_url = page.url
        
        print(f"\n📋 結果:")
        print(f"   URL: {current_url}")
        print(f"   武淵二段: {'✅' if is_wuyuan2 else '❌'}")
        print(f"   土地筆數: {len(lands)}")
        
        # 顯示前10筆
        if lands:
            print(f"\n   前 10 筆:")
            for i, land in enumerate(lands[:10]):
                print(f"     {i+1}. {land.get('land_number')} | {land.get('area')} | {land.get('price')}")
        
        # 儲存
        result = {
            "url": current_url,
            "wuyuan2_selected": is_wuyuan2,
            "total_lands": len(lands),
            "lands": lands
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已儲存至 {OUTPUT_FILE}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
