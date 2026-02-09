// Center on Yilan Dongshan Basian Section (冬山鄉八仙段)
var map = L.map('map').setView([24.6185, 121.7510], 18);

// 1. Base Layers
var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OSM' });
var googleSat = L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
    maxZoom: 22,
    subdomains:['mt0','mt1','mt2','mt3'],
    attribution: '© Google'
});

// 2. Vector Layer (The Interactive Magic)
var vectorLayer = L.geoJSON(null, {
    style: {
        color: "#f1c40f", // Highlight color (Gold)
        weight: 3,
        opacity: 0.8,
        fillOpacity: 0.1
    },
    onEachFeature: function (feature, layer) {
        layer.on('click', function (e) {
            L.DomEvent.stopPropagation(e);
            
            // Selection effect
            vectorLayer.eachLayer(l => vectorLayer.resetStyle(l));
            layer.setStyle({ color: "#e74c3c", weight: 5, fillOpacity: 0.4 });
            
            // Area Calculation
            var latlngs = layer.getLatLngs();
            var areaSqm = L.GeometryUtil.geodesicArea(latlngs[0]);
            updateDisplay(areaSqm);
            
            // *** 顯示每一邊的長度 ***
            showEdgeLengths(layer);
            
            layer.bindPopup(`<b>地塊資訊</b><br>面積: ${Math.round(areaSqm)} m²<br>約 ${ (areaSqm * 0.3025).toFixed(1) } 坪`).openPopup();
        });
    }
}).addTo(map);

// 3. 邊長顯示邏輯
var edgeLabelGroup = L.layerGroup().addTo(map);

function showEdgeLengths(layer) {
    edgeLabelGroup.clearLayers();
    var latlngs = layer.getLatLngs();
    if (latlngs.length === 0) return;
    var rings = latlngs[0]; 
    if (!Array.isArray(rings[0])) rings = latlngs; // Handle single polygon vs nested arrays

    var pts = rings[0];
    for (var i = 0; i < pts.length; i++) {
        var p1 = pts[i];
        var p2 = pts[(i + 1) % pts.length];
        
        var distance = map.distance(p1, p2);
        if (distance > 2) {
            var midPoint = L.latLng((p1.lat + p2.lat) / 2, (p1.lng + p2.lng) / 2);
            L.marker(midPoint, {
                icon: L.divIcon({
                    className: 'edge-label',
                    html: `<span>${distance.toFixed(1)}m</span>`,
                    iconSize: [50, 20],
                    iconAnchor: [25, 10]
                }),
                interactive: false
            }).addTo(edgeLabelGroup);
        }
    }
}

// 4. Load Crack Test Data (Small Area Test)
fetch('basian_crack_test.json')
    .then(response => response.json())
    .then(data => {
        console.log("載入測試地塊中...");
        vectorLayer.addData(data);
    })
    .catch(err => console.log("載入測試檔失敗:", err));

// 5. Manual Draw & Controls
var drawnItems = new L.FeatureGroup().addTo(map);
new L.Control.Draw({
    draw: { polygon: true, polyline: false, circle: false, rectangle: true, marker: false, circlemarker: false },
    edit: { featureGroup: drawnItems }
}).addTo(map);

map.on(L.Draw.Event.CREATED, function (e) {
    drawnItems.clearLayers();
    var layer = e.layer;
    drawnItems.addLayer(layer);
    var areaSqm = L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
    updateDisplay(areaSqm);
    showEdgeLengths(layer);
});

// Controls
googleSat.addTo(map);
var baseMaps = { "衛星地圖": googleSat, "一般地圖": osm };
var overlayMaps = { "地籍互動層": vectorLayer, "手繪區域": drawnItems };
L.control.layers(baseMaps, overlayMaps).addTo(map);
L.control.locate({position: 'topleft'}).addTo(map);

// Price UI Sync
var pricePerFenInput = document.getElementById('pricePerFen');
var areaDisplay = document.getElementById('areaDisplay');
var areaSubDisplay = document.getElementById('areaSubDisplay');
var priceDisplay = document.getElementById('priceDisplay');
const SQM_TO_FEN = 0.00103102; 
const SQM_TO_PING = 0.3025;    

function updateDisplay(sqm) {
    var areaFen = sqm * SQM_TO_FEN;
    var areaPing = sqm * SQM_TO_PING;
    areaDisplay.innerText = areaFen.toFixed(2) + " 分";
    areaSubDisplay.innerText = "(" + Math.floor(areaPing) + " 坪)";
    var price = Math.ceil(areaFen * parseFloat(pricePerFenInput.value));
    priceDisplay.innerText = "$" + price.toLocaleString();
}

document.getElementById('locateBtn').addEventListener('click', function() {
    map.locate({setView: true, maxZoom: 18});
});

document.getElementById('clearBtn').addEventListener('click', function() {
    drawnItems.clearLayers();
    edgeLabelGroup.clearLayers();
    vectorLayer.eachLayer(l => vectorLayer.resetStyle(l));
    updateDisplay(0);
});
