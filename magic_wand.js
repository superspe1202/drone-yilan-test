
class MagicWand {
    constructor(map) {
        this.map = map;
        this.enabled = false;
        this.busy = false;
        // Adjust this URL to match your actual 591 layer URL logic or verify against script.js
        this.layerUrl = '/api/proxy?z={z}&x={x}&y={y}'; 
        this.polyLayer = L.layerGroup().addTo(map);
        
        this.button = null;
        this._initControl();
    }

    _initControl() {
        const Control = L.Control.extend({
            options: { position: 'topleft' },
            onAdd: () => {
                const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                this.button = L.DomUtil.create('a', 'magic-wand-btn', container);
                this.button.href = '#';
                this.button.title = '魔術棒選取 (Magic Wand)';
                this.button.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i>';
                this.button.style.backgroundColor = 'white';
                this.button.style.width = '34px';
                this.button.style.height = '34px';
                this.button.style.lineHeight = '34px';
                this.button.style.textAlign = 'center';
                this.button.style.cursor = 'pointer';
                this.button.style.textDecoration = 'none';
                this.button.style.color = '#333';
                this.button.style.fontSize = '16px';

                L.DomEvent.on(this.button, 'click', (e) => {
                    L.DomEvent.stop(e);
                    this.toggle();
                });
                
                // Prevent map clicks propagating to map when clicking button
                L.DomEvent.disableClickPropagation(container);

                return container;
            }
        });
        this.map.addControl(new Control());
    }

    toggle() {
        this.enabled = !this.enabled;
        if (this.enabled) {
            this.button.style.backgroundColor = '#4caf50';
            this.button.style.color = 'white';
            L.DomUtil.addClass(this.map.getContainer(), 'cursor-crosshair');
            this.map.on('click', this._onClick, this);
            console.log('Magic Wand Enabled');
        } else {
            this.button.style.backgroundColor = 'white';
            this.button.style.color = '#333';
            L.DomUtil.removeClass(this.map.getContainer(), 'cursor-crosshair');
            this.map.off('click', this._onClick, this);
            console.log('Magic Wand Disabled');
        }
    }

    async _onClick(e) {
        if (this.busy) return;
        this.busy = true;
        const originalCursor = this.map.getContainer().style.cursor;
        this.map.getContainer().style.cursor = 'wait';

        try {
            await this._processClick(e.latlng);
        } catch (err) {
            console.error('Magic Wand Error:', err);
            alert('選取失敗 (請確保已載入 OpenCV 且地圖圖層正常)');
        } finally {
            this.busy = false;
            this.map.getContainer().style.cursor = originalCursor;
        }
    }

    async _processClick(latlng) {
        // Use z=20 for high resolution analysis
        const zoom = 20; 
        const point = this.map.project(latlng, zoom);
        const tileSize = 256;
        
        const tileX = Math.floor(point.x / tileSize);
        const tileY = Math.floor(point.y / tileSize);
        
        const offsetX = Math.floor(point.x % tileSize);
        const offsetY = Math.floor(point.y % tileSize);

        console.log(`MagicWand: Click at z${zoom} tile(${tileX}, ${tileY}) offset(${offsetX}, ${offsetY})`);

        // Load Tile Image
        const url = this.layerUrl.replace('{z}', zoom).replace('{x}', tileX).replace('{y}', tileY);
        
        let img;
        try {
            img = await this._loadImage(url);
        } catch (e) {
            console.error("Failed to load tile", url);
            alert("無法載入地籍圖塊，請檢查網路或縮放層級");
            return;
        }

        // Process with OpenCV
        const coords = this._findRegion(img, offsetX, offsetY, tileX, tileY, zoom);

        if (coords && coords.length > 2) {
            // Simplify geometry if needed? 
            // Leaflet Draw usually handles L.Polygon nicely.
            
            const polygon = L.polygon(coords, {
                color: '#ff0000',
                fillColor: '#ff0000',
                fillOpacity: 0.3,
                weight: 2
            }).addTo(this.polyLayer);
            
            // Add to the main "drawnItems" FeatureGroup if it exists (standard Leaflet Draw integration)
            if (window.drawnItems) {
                window.drawnItems.addLayer(polygon);
                // Trigger area update if the function exists
                if (typeof window.updateAreaStats === 'function') {
                    window.updateAreaStats();
                }
            } else {
                console.warn("window.drawnItems not found, polygon added to local layer only.");
            }
            
            console.log(`MagicWand: Polygon created with ${coords.length} points.`);
        } else {
            console.warn("MagicWand: No closed region found.");
            // Optional: Provide feedback like a toast
        }
    }

    _loadImage(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'Anonymous';
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = url;
        });
    }

    _findRegion(img, startX, startY, tileX, tileY, zoom) {
        if (typeof cv === 'undefined') {
            alert("OpenCV.js 尚未載入完成，請稍候");
            return null;
        }

        const src = cv.imread(img);
        const rows = src.rows;
        const cols = src.cols;

        // Convert to Gray
        const gray = new cv.Mat();
        cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY, 0);

        // Edge Detection
        const edges = new cv.Mat();
        // Adjust thresholds based on the visual properties of the "Red Lines"
        // If lines are very clear, 50-200 is standard.
        cv.Canny(gray, edges, 50, 150, 3, false);
        
        // Dilate to close gaps in lines
        const kernel = cv.Mat.ones(3, 3, cv.CV_8U);
        const dilated = new cv.Mat();
        cv.dilate(edges, dilated, kernel, new cv.Point(-1, -1), 1, cv.BORDER_CONSTANT, cv.morphologyDefaultBorderValue());

        // Prepare Mask for FloodFill (H+2, W+2)
        const mask = new cv.Mat.zeros(rows + 2, cols + 2, cv.CV_8UC1);
        
        // Copy edges (dilated) into the mask's ROI corresponding to the image
        // FloodFill stops at non-zero mask pixels.
        const maskArea = mask.roi(new cv.Rect(1, 1, cols, rows));
        dilated.copyTo(maskArea); 
        maskArea.delete(); 

        // FloodFill
        // Use a dummy image since we are using MASK_ONLY mode
        const floodDummy = new cv.Mat.zeros(rows, cols, cv.CV_8UC1);
        const seed = new cv.Point(startX, startY);
        // Check if seed hits a wall (optional optimization)
        
        // Flags: 4-connectivity + Mask Only + Fill Value (255)
        const flags = 4 | cv.FLOODFILL_MASK_ONLY | (255 << 8);
        
        try {
            cv.floodFill(floodDummy, mask, seed, new cv.Scalar(255), new cv.Scalar(0), new cv.Scalar(0), flags);
        } catch(e) {
            console.error("FloodFill failed", e);
            return null;
        }

        // Extract result from mask
        // The filled area is now 255 in the mask (along with original edges)
        const filled = mask.roi(new cv.Rect(1, 1, cols, rows));
        
        // Find Contours
        const contours = new cv.MatVector();
        const hierarchy = new cv.Mat();
        cv.findContours(filled, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);

        let resultCoords = [];

        // Find the contour that contains the seed point? 
        // Or just the largest one. Usually the filled area is one large blob.
        if (contours.size() > 0) {
            let maxArea = 0;
            let maxIdx = -1;
            for (let i = 0; i < contours.size(); i++) {
                const area = cv.contourArea(contours.get(i));
                if (area > maxArea) {
                    maxArea = area;
                    maxIdx = i;
                }
            }

            if (maxIdx !== -1) {
                const contour = contours.get(maxIdx);
                const data = contour.data32S;
                
                // Convert to Leaflet LatLng
                // Optimization: Don't take every point if too dense? 
                // Leaflet can handle it, but maybe skip every other if needed.
                for (let i = 0; i < data.length; i += 2) {
                    const px = data[i];
                    const py = data[i+1];
                    
                    const globalX = tileX * 256 + px;
                    const globalY = tileY * 256 + py;
                    
                    const latlng = this.map.unproject(L.point(globalX, globalY), zoom);
                    resultCoords.push(latlng);
                }
            }
        }

        // Clean up
        src.delete(); gray.delete(); edges.delete(); kernel.delete(); dilated.delete();
        mask.delete(); floodDummy.delete(); filled.delete(); contours.delete(); hierarchy.delete();

        return resultCoords;
    }
}

// Global init function
window.initMagicWand = function(map) {
    return new MagicWand(map);
};
