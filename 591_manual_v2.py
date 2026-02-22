#!/usr/bin/env python3
"""
591 土地資料擷取 v2 - 讓使用者手動選擇地段後自動擷取
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan2_data.json"

def parse_land_data(text):
    """解析土地資料"""
    lands = []
    
    # 使用正則表達式匹配地段+地號
    # 格式: 冬山鄉 武淵二段123地號
    pattern = r'([^\s]+[鄉鎮市區])[\s]+([^地號]+段[^地號]*)地號(\S+)'
    matches = re.findall(pattern, text)
    
    for match in matches:
        township = match[0].strip()
        section = match[1].strip()
        land_num = match[2].strip()
        
        lands.append({
            "township": township,
            "section": section,
            "land_number": land_num
        })
    
    return lands

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        print("🌐 前往 591 土地地圖...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await page.wait_for_timeout(3000)
        
        print("\n" + "="*60)
        print("  🎯 請手動操作（瀏覽器會保持開啟）:")
        print("     1. 點擊「鄉鎮/地段/捷運」下拉選單")
        print("     2. 切換到「地段」標籤")  
        print("     3. 搜尋「武淵二段」並點擊選擇")
        print("     4. 點擊「確定」按鈕")
        print("     5. 等待地圖載入完成")
        print("\n  ⚠️  完成後切換回此終端機按 Enter 繼續")
        print("="*60 + "\n")
        
        # 等待使用者按 Enter
        try:
            input("  👀 等待你操作...按 Enter 開始擷取資料...")
        except:
            pass
        
        # 等待資料載入
        await page.wait_for_timeout(5000)
        
        print("\n📊 正在提取土地資料...")
        
        # 從頁面取得文字
        page_text = await page.inner_text("body")
        
        # 解析土地資料
        lands = parse_land_data(page_text)
        
        # 取得更詳細的資料 - 從清單項目中提取
        land_details = []
        
        # 嘗試從側邊欄取得資料
        try:
            # 找到所有土地列表項目
            items = await page.query_selector_all("[class*='land-item'], [class*='list-item'], .item")
            
            for item in items[:200]:  # 限制數量
                try:
                    text = await item.inner_text()
                    lines = text.split("\n")
                    
                    # 解析土地資訊
                    land_info = {}
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if "段" in line and "地號" in line:
                            # 這是地段資訊
                            match = re.search(r'([^\s]+[鄉鎮市區])?\s*(.+段.+地號)', line)
                            if match:
                                land_info["full_number"] = line
                        elif "坪" in line:
                            land_info["area"] = line
                        elif "萬/坪" in line or "元/坪" in line:
                            land_info["price"] = line
                    
                    if land_info:
                        land_details.append(land_info)
                except:
                    pass
        except Exception as e:
            print(f"   ⚠️ DOM 擷取錯誤: {e}")
        
        print(f"   找到 {len(lands)} 筆（正則解析）")
        print(f"   找到 {len(land_details)} 筆（DOM 解析）")
        
        # 顯示目前的 URL
        current_url = page.url
        print(f"   URL: {current_url}")
        
        # 檢查是否選中了武淵二段
        is_wuyuan2 = "武淵二段" in page_text
        print(f"   武淵二段: {'✅ 是' if is_wuyuan2 else '❌ 否'}")
        
        # 儲存結果
        result = {
            "source": "591 land map",
            "url": current_url,
            "wuyuan2_selected": is_wuyuan2,
            "lands_regex": lands,
            "lands_dom": land_details[:100],
            "page_text": page_text[:20000]
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已儲存至 {OUTPUT_FILE}")
        
        # 保持瀏覽器開啟，讓使用者確認
        print("\n🔔 瀏覽器保持開啟，按 Ctrl+C 結束...")
        
        # 持續監控
        try:
            while True:
                await asyncio.sleep(10)
                # 定期檢查是否有新資料
        except KeyboardInterrupt:
            pass
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
