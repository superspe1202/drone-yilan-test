// Center on Yilan Dongshan
var map = L.map('map').setView([24.635, 121.785], 16);

// 1. Base Layer (Google Satellite)
var googleSat = L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',{
    maxZoom: 22,
    subdomains:['mt0','mt1','mt2','mt3']
}).addTo(map);

// 2. OSM Buildings & Landuse (The "Magic" Layer)
// We use Overpass API to fetch vector data in real-time!
// This fetches "farmland", "farm", "meadow", "grass" polygons.

var osmLayers = new L.FeatureGroup().addTo(map);

function loadOSMData() {
    var bounds = map.getBounds();
    var query = `
        [out:json];
        (
          way["landuse"="farmland"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
          way["landuse"="farm"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
          way["landuse"="grass"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
          relation["landuse"="farmland"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
        );
        out body;
        >;
        out skel qt;
    `;

    var url = 'https://overpass-api.de/api/interpreter?data=' + encodeURIComponent(query);

    // Show loading
    document.getElementById('areaDisplay').innerText = "載入中...";

    fetch(url)
        .then(res => res.json())
        .then(data => {
            // Convert OSM JSON to GeoJSON (Simplified logic for demo)
            // For a real app we'd use osmtogeojson library.
            // Here we just use a helper or assume we can parse ways.
            
            // Actually, without the library it's hard.
            // Let's use a pre-built WMS layer for OSM Landuse instead? 
            // Or just load the library from CDN.
            
            console.log("OSM Data Loaded:", data.elements.length);
            document.getElementById('areaDisplay').innerText = "0 分";
            
            // Note: Since we can't easily parse raw OSM XML/JSON to Leaflet without a heavy library here,
            // I will switch strategy to use a "WMS Tile Layer" that HIGHLIGHTS farmland.
            // But WMS is just images (can't click to get area).
            
            // So we MUST use GeoJSON.
            // I will inject osmtogeojson library.
        });
}

// Button to load OSM
var btn = L.control({position: 'topright'});
btn.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
    div.innerHTML = '<a href="#" title="載入農地框線" style="font-size: 20px; width: 40px; height: 40px; line-height: 40px;">🌾</a>';
    div.onclick = function(e) {
        e.preventDefault();
        alert("請稍等，正在從 OpenStreetMap 抓取農地資料...");
        loadOSMDataWithLib();
    };
    return div;
};
btn.addTo(map);

function loadOSMDataWithLib() {
    // Dynamically load osmtogeojson
    if (typeof osmtogeojson === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://unpkg.com/osmtogeojson@3.0.0/osmtogeojson.js';
        script.onload = runQuery;
        document.head.appendChild(script);
    } else {
        runQuery();
    }
}

function runQuery() {
    osmLayers.clearLayers();
    var bounds = map.getBounds();
    // Query for farmland
    var query = `
        [out:json];
        (
          way["landuse"="farmland"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
          way["landuse"="orchard"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
          way["landuse"="grass"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
        );
        out body;
        >;
        out skel qt;
    `;
    
    fetch('https://overpass-api.de/api/interpreter?data=' + encodeURIComponent(query))
        .then(res => res.json())
        .then(data => {
            var geojson = osmtogeojson(data);
            var layer = L.geoJSON(geojson, {
                style: { color: "#ffff00", weight: 2, opacity: 0.8, fillOpacity: 0.2 },
                onEachFeature: function(feature, layer) {
                    layer.on('click', function() {
                        // Calculate area
                        var areaSqm = L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
                        updateDisplay(areaSqm);
                        
                        // Highlight
                        osmLayers.eachLayer(l => l.setStyle({color: "#ffff00", fillOpacity: 0.2}));
                        layer.setStyle({color: "#ff0000", fillOpacity: 0.5});
                    });
                }
            }).addTo(osmLayers);
            
            if (layer.getLayers().length === 0) {
                alert("這裡在 OSM 上沒有標記農地... 還是得手動畫 😅");
            } else {
                alert("成功載入！點擊黃色框框即可算錢！💰");
            }
        });
}

// ... (Keep previous Draw/Locate/Calc logic) ...
// (I will append the rest of the file logic here when writing)