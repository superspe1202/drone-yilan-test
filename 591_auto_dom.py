#!/usr/bin/env python3
"""
591 土地資料擷取 v4 - 完全自動操作 DOM
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright, Page

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan2_data.json"

async def click_dropdown_and_select(page: Page, section_name: str):
    """點擊下拉選單並選擇地段"""
    
    print("  🔍 查找下拉選單...")
    
    # 方法1: 點擊包含文字的元素
    try:
        # 嘗試點擊 "鄉鎮/地段/捷運" 
        dropdown = page.locator("p:has-text('鄉鎮/地段/捷運'), div:has-text('鄉鎮/地段/捷運')").first
        await dropdown.click(timeout=3000)
        print("  ✅ 點擊下拉選單")
        await asyncio.sleep(1)
    except Exception as e:
        print(f"  ⚠️ 第一次嘗試失敗: {e}")
        try:
            # 方法2: 點擊任意 dropdown
            dropdown = page.locator(".t5-dropdown, .dropdown").first
            await dropdown.click(timeout=3000)
            print("  ✅ 點擊 dropdown")
            await asyncio.sleep(1)
        except:
            pass
    
    # 點擊 "地段" 標籤
    print("  🔍 選擇地段標籤...")
    try:
        section_tab = page.locator("div:has-text('地段'), .main-level-menu-item:has-text('地段')").first
        await section_tab.click(timeout=3000)
        print("  ✅ 點擊地段標籤")
        await asyncio.sleep(1)
    except Exception as e:
        print(f"  ⚠️ 點擊地段標籤失敗: {e}")
    
    # 輸入搜尋
    print("  🔍 輸入搜尋...")
    try:
        search_input = page.locator("input[placeholder*='搜尋'], input.search-input, input[type='text']").first
        await search_input.fill(section_name)
        await search_input.press("Enter")
        print(f"  ✅ 輸入 {section_name} 並按下 Enter")
        await asyncio.sleep(2)
    except Exception as e:
        print(f"  ⚠️ 輸入失敗: {e}")
    
    # 點擊搜尋結果
    print("  🔍 點擊搜尋結果...")
    try:
        # 等待結果出現
        await asyncio.sleep(1)
        result = page.locator(f"text={section_name}").first
        await result.click(timeout=3000)
        print(f"  ✅ 點擊 {section_name}")
        await asyncio.sleep(1)
    except Exception as e:
        print(f"  ⚠️ 點擊結果失敗: {e}")
    
    # 點擊確定
    print("  🔍 點擊確定...")
    try:
        confirm = page.locator("button:has-text('確定'), button.btn:has-text('確定'), .t5-button:has-text('確定')").first
        await confirm.click(timeout=3000)
        print("  ✅ 點擊確定")
        await asyncio.sleep(3)
    except Exception as e:
        print(f"  ⚠️ 點擊確定失敗: {e}")

async def extract_land_data(page: Page) -> dict:
    """從頁面提取土地資料"""
    
    lands = []
    
    # 方法1: 從 DOM 提取
    try:
        # 嘗試找到土地列表
        items = await page.query_selector_all(
            "[class*='land'], [class*='item'], .list-item, "
            "[class*='card'], [class*='land-item'], .land-item"
        )
        
        print(f"    找到 {len(items)} 個元素")
        
        for item in items[:300]:
            try:
                text = await item.inner_text()
                if "地號" in text and "段" in text:
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    
                    # 解析地段資訊
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
                        lands.append({
                            "land_number": land_num,
                            "area": area,
                            "price": price,
                            "land_type": land_type,
                            "raw": text[:300]
                        })
            except:
                pass
    except Exception as e:
        print(f"    ⚠️ DOM 提取錯誤: {e}")
    
    # 方法2: 從頁面文字提取
    try:
        page_text = await page.inner_text("body")
        
        # 使用正則表達式
        import re
        pattern = r'([^\s]{2,4}[鄉鎮市區])\s+([^段]+段[^\s]+地號[^\s]*)'
        matches = re.findall(pattern, page_text)
        
        for match in matches[:300]:
            township = match[0].strip()
            land_full = match[1].strip()
            
            # 避免重複
            existing = [l for l in lands if l.get("land_number") == land_full]
            if not existing:
                lands.append({
                    "township": township,
                    "land_number": land_full,
                    "raw": f"{township} {land_full}"
                })
    except Exception as e:
        print(f"    ⚠️ 正則提取錯誤: {e}")
    
    return lands

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        print("\n🌐 前往 591 土地地圖...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await page.wait_for_timeout(5000)
        
        print("\n🎯 開始自動操作...")
        
        # 嘗試選擇武淵二段
        await click_dropdown_and_select(page, "武淵二段")
        
        # 等待載入
        print("\n⏳ 等待資料載入...")
        await page.wait_for_timeout(8000)
        
        # 提取資料
        print("\n📊 提取土地資料...")
        lands = await extract_land_data(page)
        
        # 檢查是否為武淵二段
        page_text = await page.inner_text("body")
        is_wuyuan2 = "武淵二段" in page_text
        
        # 顯示 URL
        current_url = page.url
        
        print(f"\n📋 結果:")
        print(f"   URL: {current_url}")
        print(f"   武淵二段: {'✅ 是' if is_wuyuan2 else '❌ 否'}")
        print(f"   土地筆數: {len(lands)}")
        
        # 顯示前幾筆
        if lands:
            print(f"\n   前 5 筆:")
            for i, land in enumerate(lands[:5]):
                print(f"     {i+1}. {land.get('land_number', 'N/A')}")
        
        # 儲存
        result = {
            "url": current_url,
            "wuyuan2_selected": is_wuyuan2,
            "total_lands": len(lands),
            "lands": lands[:500],  # 限制數量
            "page_text": page_text[:10000]
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已儲存至 {OUTPUT_FILE}")
        
        # 讓使用者確認
        print("\n🔔 瀏覽器保持開啟，按 Ctrl+C 結束...")
        try:
            while True:
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            pass
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
