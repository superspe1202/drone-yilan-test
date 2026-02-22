#!/usr/bin/env python3
"""
591 土地資料擷取 v3 - 嘗試自動點擊選擇
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
        await page.wait_for_timeout(5000)
        
        print("\n🔍 嘗試自動選擇武淵二段...")
        
        try:
            # 點擊下拉選單 - 使用更精確的選擇器
            dropdown = page.locator("div.dropdown-text, .t5-dropdown").first
            await dropdown.click(timeout=5000)
            print("  ✅ 點擊下拉選單")
            await page.wait_for_timeout(2000)
            
            # 點擊「地段」標籤
            section_tab = page.locator("text=地段").first
            await section_tab.click(timeout=5000)
            print("  ✅ 點擊地段標籤")
            await page.wait_for_timeout(2000)
            
            # 搜尋框輸入
            search_input = page.locator("input[placeholder*='搜尋'], input.search-input").first
            await search_input.fill("武淵二段")
            print("  ✅ 輸入武淵二段")
            await page.wait_for_timeout(2000)
            
            # 點擊搜尋結果
            result = page.locator("text=武淵二段").first
            await result.click(timeout=5000)
            print("  ✅ 點擊搜尋結果")
            await page.wait_for_timeout(1000)
            
            # 點擊確定
            confirm_btn = page.locator("button:has-text('確定'), text=確定").first
            await confirm_btn.click(timeout=5000)
            print("  ✅ 點擊確定")
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"  ⚠️ 自動點擊失敗: {e}")
            print("  💡 請手動操作...")
        
        print("\n" + "="*60)
        print("  請確認是否已選擇「武淵二段」")
        print("  如果沒有，請手動選擇後，等待 10 秒")
        print("  然後回來按 Enter 繼續...")
        print("="*60 + "\n")
        
        try:
            input("  按 Enter 繼續擷取...")
        except:
            pass
        
        await page.wait_for_timeout(3000)
        
        # 擷取資料
        print("\n📊 提取資料...")
        
        # 從 DOM 提取
        items = await page.query_selector_all("[class*='land-item'], [class*='list-item'], .item, .land-item")
        
        lands = []
        for item in items[:200]:
            try:
                text = await item.inner_text()
                if "地號" in text:
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if lines:
                        lands.append({
                            "raw": text[:200],
                            "lines": lines
                        })
            except:
                pass
        
        print(f"   找到 {len(lands)} 筆土地")
        
        # 檢查是否有武淵二段
        page_text = await page.inner_text("body")
        has_wuyuan2 = "武淵二段" in page_text
        
        print(f"   武淵二段: {'✅' if has_wuyuan2 else '❌'}")
        
        # 儲存
        result = {
            "wuyuan2_selected": has_wuyuan2,
            "lands": lands,
            "url": page.url,
            "preview": page_text[:15000]
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 儲存至 {OUTPUT_FILE}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
