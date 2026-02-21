#!/usr/bin/env python3
"""
八仙段土地邊界偵測 script
從 OSM 衛星圖磚偵測土地邊界
"""

import os
import math
import json
import requests
from io import BytesIO
from PIL import Image
import cv2
import numpy as np
from pathlib import Path

# 八仙段中心座標
CENTER_LAT = 24.6185
CENTER_LON = 121.7510
ZOOM = 19

# 偵測範圍（米）
RADIUS_METERS = 500

OUTPUT_FILE = "drone-app/baxian_boundaries.json"

def lat_lon_to_tile(lat, lon, zoom):
    """轉換經緯度到圖磚座標"""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y

def tile_to_lat_lon(x, y, zoom):
    """轉換圖磚座標到經緯度"""
    n = 2.0 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon

def get_tile_bbox(x, y, zoom):
    """取得圖磚的邊界座標"""
    lat1, lon1 = tile_to_lat_lon(x, y)
    lat2, lon2 = tile_to_lat_lon(x + 1, y + 1)
    return lon1, lat2, lon2, lat1  # min_lon, max_lat, max_lon, min_lat

def meters_to_tile_offset(meters, lat, zoom):
    """將米轉換為圖磚偏移量"""
    # 1 degree latitude ≈ 111,320 meters
    tiles_per_meter = (2**zoom) / (111320 * math.cos(math.radians(lat)) * 360)
    return meters * tiles_per_meter

def download_tile(x, y, zoom):
    """下載單個圖磚"""
    # 使用 OSM 衛星圖
    url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"下載圖磚 ({x},{y}) 失敗: {e}")
    
    # 備用：OSM 標準地圖
    try:
        url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
        headers = {'User-Agent': 'OpenClaw/1.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"備用下載失敗: {e}")
    
    return None

def detect_boundaries(image):
    """使用 OpenCV 偵測土地邊界"""
    # 轉灰階
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 高斯模糊去噪
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Canny 邊緣偵測
    edges = cv2.Canny(blur, 50, 150)
    
    # 膨脹連接邊緣
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    
    # 找輪廓
    contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"偵測到 {len(contours)} 個輪廓")
    
    # 過濾太小的輪廓
    min_area = 500  # 像素面積
    valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]
    
    print(f"過濾後剩 {len(valid_contours)} 個有效輪廓")
    
    return valid_contours, image.shape[:2]

def contours_to_geojson(contours, img_shape, min_lon, min_lat, max_lon, max_lat):
    """將輪廓轉換為 GeoJSON"""
    features = []
    
    h, w = img_shape
    lon_per_pixel = (max_lon - min_lon) / w
    lat_per_pixel = (max_lat - min_lat) / h
    
    for i, contour in enumerate(contours):
        coords = []
        for point in contour:
            px, py = point[0]
            # 轉換像素座標到經緯度
            lon = min_lon + px * lon_per_pixel
            lat = max_lat - py * lat_per_pixel  # Y 軸反向
            coords.append([lon, lat])
        
        # 閉合多邊形
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            },
            "properties": {
                "id": i,
                "area_pixels": cv2.contourArea(contour)
            }
        }
        features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

def main():
    print("=== 八仙段土地邊界偵測 ===")
    
    # 計算中心點的圖磚座標
    center_x, center_y = lat_lon_to_tile(CENTER_LAT, CENTER_LON, ZOOM)
    print(f"中心點圖磚: x={center_x}, y={center_y}")
    
    # 計算範圍（以圖磚為單位）
    offset = meters_to_tile_offset(RADIUS_METERS, CENTER_LAT, ZOOM)
    print(f"偵測半徑: {RADIUS_METERS}m = {offset:.2f} tiles")
    
    # 下載 3x3 區域的圖磚
    tiles = []
    rows, cols = 3, 3
    
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            tx = center_x + dx
            ty = center_y + dy
            print(f"下載圖磚: ({tx}, {ty})")
            tile = download_tile(tx, ty, ZOOM)
            if tile is not None:
                tiles.append((dx + 1, dy + 1, tile))
    
    if not tiles:
        print("無法下載任何圖磚！")
        return
    
    # 拼接圖磚
    print("拼接圖磚...")
    merged = np.zeros((rows * 256, cols * 256, 3), dtype=np.uint8)
    
    for dx, dy, tile in tiles:
        # tile 是 256x256
        # dx, dy 是位置 (0,1,2)
        x_start = dx * 256
        y_start = dy * 256
        merged[y_start:y_start+256, x_start:x_start+256] = tile
    
    print(f"合併後圖片大小: {merged.shape}")
    
    # 偵測邊界
    print("偵測邊界...")
    contours, shape = detect_boundaries(merged)
    
    # 計算地理範圍
    # 左上角圖磚
    min_lat, min_lon = tile_to_lat_lon(center_x - 1, center_y - 1, ZOOM)
    # 右下角圖磚  
    max_lat, max_lon = tile_to_lat_lon(center_x + 2, center_y + 2, ZOOM)
    
    print(f"地理範圍: lon {min_lon:.6f} ~ {max_lon:.6f}, lat {min_lat:.6f} ~ {max_lat:.6f}")
    
    # 轉 GeoJSON
    geojson = contours_to_geojson(contours, shape, min_lon, min_lat, max_lon, max_lat)
    
    # 儲存
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    
    print(f"完成！")
    print(f"總共偵測到: {len(geojson['features'])} 塊")
    print(f"已儲存到: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
