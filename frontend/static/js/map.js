/**
 * CityFix Leaflet Map Helper
 */

const CityFixMap = {
    map: null,
    currentMarker: null,
    issueMarkers: [],
    onPickerLocationSelected: null,

    init(elementId = "map", center = [12.9716, 77.5946], zoom = 13) {
        if (!document.getElementById(elementId)) return null;
        if (typeof L === "undefined") {
            console.warn("Leaflet library not loaded yet.");
            return null;
        }

        this.map = L.map(elementId).setView(center, zoom);

        // OpenStreetMap tile layer (Free, no API key needed)
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19,
        }).addTo(this.map);

        return this.map;
    },

    enableLocationPicker(onLocationSelected) {
        if (!this.map) return;
        this.onPickerLocationSelected = onLocationSelected;

        this.map.on("click", (e) => {
            const { lat, lng } = e.latlng;
            this.setPickerLocation(lat, lng);
            if (this.onPickerLocationSelected) {
                this.onPickerLocationSelected(lat, lng);
            }
        });
    },

    setPickerLocation(lat, lng) {
        if (this.currentMarker) {
            this.currentMarker.setLatLng([lat, lng]);
        } else {
            this.currentMarker = L.marker([lat, lng], { draggable: true }).addTo(this.map);
            this.currentMarker.on("dragend", () => {
                const position = this.currentMarker.getLatLng();
                if (this.onPickerLocationSelected) {
                    this.onPickerLocationSelected(position.lat, position.lng);
                }
            });
        }
        this.map.panTo([lat, lng]);
    },

    getUserLocation(onSuccess, onError) {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    if (this.map) {
                        this.setPickerLocation(lat, lng);
                        this.map.setView([lat, lng], 15);
                    }
                    if (onSuccess) onSuccess(lat, lng);
                },
                (err) => {
                    console.warn("Geolocation permission denied or unavailable:", err);
                    if (onError) onError(err);
                }
            );
        } else {
            if (onError) onError(new Error("Geolocation is not supported by your browser."));
        }
    },

    renderIssueMarkers(issues) {
        if (!this.map) return;
        
        // Clear previous markers
        this.issueMarkers.forEach(m => this.map.removeLayer(m));
        this.issueMarkers = [];

        issues.forEach(issue => {
            if (!issue.latitude || !issue.longitude) return;

            const marker = L.marker([issue.latitude, issue.longitude]);
            const popupContent = `
                <div class="p-2 min-w-[200px]">
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-xs font-bold text-blue-600">${issue.tracking_number}</span>
                        <span class="text-xs px-2 py-0.5 rounded font-semibold uppercase ${
                            issue.severity === 'critical' ? 'bg-red-100 text-red-700' :
                            issue.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                            'bg-amber-100 text-amber-700'
                        }">${issue.severity}</span>
                    </div>
                    <h4 class="font-bold text-sm text-slate-800">${issue.title}</h4>
                    <p class="text-xs text-slate-500 mt-1">${issue.category}</p>
                    <p class="text-xs text-slate-600 mt-1 line-clamp-2">${issue.description}</p>
                    <div class="mt-2 pt-2 border-t flex justify-between items-center text-xs">
                        <span class="capitalize font-medium text-slate-600">Status: <b>${issue.status}</b></span>
                        <a href="/explore?id=${issue.id}" class="text-blue-600 hover:underline font-semibold">View</a>
                    </div>
                </div>
            `;
            marker.bindPopup(popupContent);
            marker.addTo(this.map);
            this.issueMarkers.push(marker);
        });
    }
};
