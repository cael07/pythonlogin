<template>
  <div class="passenger-layout">
    <!-- Fullscreen Map Background -->
    <div id="passenger-map" class="map-container"></div>

    <!-- Top Overlay Elements -->
    <div class="top-overlay">
      <!-- Routing Card -->
      <div class="route-card glass">
        <div class="route-header">
          <button class="back-btn-inline" @click="$router.push('/dashboard')">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
          </button>
          <div v-if="auth.user?.face_image_base64" class="header-avatar">
            <img :src="auth.user.face_image_base64" alt="Me" class="header-face-img" />
          </div>
          <h3>Choose route</h3>
        </div>
        
        <div class="route-inputs">
          <div class="input-row relative" :class="{'active-row': activeSearchType === 'pickup'}">
            <div class="dot pickup-dot"></div>
            <div class="input-content w-100">
              <span class="label">Pickup <span class="badge" v-if="isCurrentLocation">(Current)</span></span>
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <input type="text" class="location-input" v-model="pickupText" @input="onInput('pickup')" @focus="activeSearchType = 'pickup'" placeholder="Enter Pickup Location" :disabled="rideStore.currentBooking" />
                <button v-if="!rideStore.currentBooking" class="gps-btn-inline" @click="centerOnUser" title="Current Location">
                   <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3c-.46-4.17-3.77-7.48-7.94-7.94V1h-2v2.06C6.83 3.52 3.52 6.83 3.06 11H1v2h2.06c.46 4.17 3.77 7.48 7.94 7.94V23h2v-2.06c4.17-.46 7.48-3.77 7.94-7.94H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z"/></svg>
                </button>
              </div>
              <ul class="suggestions-list" v-if="activeSearchType === 'pickup' && suggestions.length > 0">
                <li v-for="s in suggestions" :key="s.place_id" @click="selectSuggestion(s, 'pickup')">
                  {{ s.display_name }}
                </li>
              </ul>
            </div>
          </div>
          <div class="input-divider"></div>
          <div class="input-row relative" :class="{'active-row': activeSearchType === 'dropoff'}">
            <div class="dot dropoff-dot"></div>
            <div class="input-content w-100">
              <span class="label">Drop-off</span>
              <input type="text" class="location-input" v-model="dropoffText" @input="onInput('dropoff')" @focus="activeSearchType = 'dropoff'" placeholder="Tap map or search location" :disabled="rideStore.currentBooking" />
              <ul class="suggestions-list" v-if="activeSearchType === 'dropoff' && suggestions.length > 0">
                <li v-for="s in suggestions" :key="s.place_id" @click="selectSuggestion(s, 'dropoff')">
                  {{ s.display_name }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Sheet -->
    <div :class="['bottom-sheet', 'glass', { expanded: isSheetExpanded }]">
      <div class="sheet-header" @click="isSheetExpanded = !isSheetExpanded">
        <div class="drag-handle"></div>
        <h3 v-if="!rideStore.currentBooking" class="sheet-title">Choose your Ride</h3>
        <h3 v-else class="sheet-title">Status: <span :class="['status-badge', rideStore.currentBooking.status]">{{ rideStore.currentBooking.status }}</span></h3>
      </div>

      <div class="sheet-content-wrapper">
        <div v-if="!rideStore.currentBooking" class="h-100 flex-col">
          <div class="ride-options">
            <div class="ride-option active">
              <div class="ride-icon">🛵</div>
              <div class="ride-details">
                <h4>MC Taxi</h4>
                <p>Beat the traffic</p>
              </div>
              <div class="ride-price">₱ {{ ridePrice }}</div>
            </div>
          </div>

          <button 
            class="btn-primary btn-large book-btn" 
            @click="requestRide" 
            :disabled="!dropoff"
          >
            Book MC Taxi
          </button>
        </div>

        <div v-else class="status-panel">
          <div class="status-content">
            <div v-if="rideStore.currentBooking.status === 'pending'" class="waiting">
              <div class="spinner"></div>
              <p>Finding you a driver...</p>
            </div>
            <div v-if="rideStore.currentBooking.status === 'accepted'" class="accepted">
              <div class="driver-info">
                <div class="driver-avatar">👨‍✈️</div>
                <div>
                  <h4>{{ rideStore.currentBooking.driver_name || 'Driver' }} is on the way!</h4>
                  <p>Arriving shortly</p>
                </div>
              </div>
            </div>
            <div v-if="rideStore.currentBooking.status === 'arrived'" class="accepted arrived">
              <div class="driver-info highlight">
                <div class="driver-avatar blink-fast">🛵</div>
                <div>
                  <h4>{{ rideStore.currentBooking.driver_name || 'Driver' }} has arrived!</h4>
                  <p>Meet your driver at the pickup point</p>
                </div>
              </div>
            </div>
            <button class="btn-secondary mt-3 w-100" @click="cancelRide">Cancel Ride</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import { useRideStore } from '../stores/ride'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const rideStore = useRideStore()
const auth = useAuthStore()
const router = useRouter()
let map = null
let pickupMarker = null
let dropoffMarker = null
let driverMarker = null
let watchId = null

const pickup = ref({ lat: 14.5995, lng: 120.9842 }) // default fallback
const dropoff = ref(null)
const isCurrentLocation = ref(false)
const pickupText = ref('')
const dropoffText = ref('')
const activeSearchType = ref(null)
const suggestions = ref([])
let searchTimeout = null
const deviceLocation = ref(null)
const isSheetExpanded = ref(false)

const reverseGeocode = async (lat, lng, type) => {
  try {
    const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
    const data = await res.json()
    if (data && data.display_name) {
      const parts = data.display_name.split(',')
      const shortAddress = parts.slice(0, 2).join(',') // First two parts for brevity
      if (type === 'pickup') pickupText.value = shortAddress
      else dropoffText.value = shortAddress
    }
  } catch (err) {
    console.error("Reverse geocoding error:", err)
  }
}

const onInput = (type) => {
  activeSearchType.value = type
  if (type === 'pickup') {
    isCurrentLocation.value = false // Stop GPS from overwriting user typing
  }
  const query = type === 'pickup' ? pickupText.value : dropoffText.value
  
  clearTimeout(searchTimeout)
  if (!query || query.length < 3) {
    suggestions.value = []
    return
  }

  // Debounce API calls to prevent rate limiting
  searchTimeout = setTimeout(async () => {
    try {
      // Limit to 5 results for dropdown
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&countrycodes=ph`)
      const data = await res.json()
      suggestions.value = data || []
    } catch (err) {
      console.error("Geocoding autocomplete error:", err)
    }
  }, 500)
}

const selectSuggestion = (suggestion, type) => {
  const lat = parseFloat(suggestion.lat)
  const lon = parseFloat(suggestion.lon)
  const parts = suggestion.display_name.split(',')
  const shortAddress = parts.slice(0, 2).join(',')

  if (type === 'pickup') {
    pickupText.value = shortAddress
    pickup.value = { lat, lng: lon }
    isCurrentLocation.value = false
    updatePickupMarker()
    map.flyTo([lat, lon], 15)
  } else {
    dropoffText.value = shortAddress
    dropoff.value = { lat, lng: lon }
    if (dropoffMarker) {
      dropoffMarker.setLatLng([lat, lon])
    } else {
      dropoffMarker = L.marker([lat, lon], { icon: destIcon }).addTo(map)
    }
    map.flyTo([lat, lon], 15)
  }
  
  // Close suggestions
  suggestions.value = []
  activeSearchType.value = null
}

// Haversine distance calculation in km
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

const ridePrice = computed(() => {
  if (!pickup.value || !dropoff.value) return 50;
  const dist = calculateDistance(pickup.value.lat, pickup.value.lng, dropoff.value.lat, dropoff.value.lng);
  // Based on Northville to Monumento being ~152 PHP
  // Minimum fare 50 PHP
  return Math.max(50, Math.round(dist * 15.2));
})

// Custom modern icons
const userIcon = L.divIcon({
  className: 'custom-map-marker',
  html: `<div class="marker-pin pickup-pin"></div><div class="marker-pulse pickup-pulse"></div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15]
})

const destIcon = L.divIcon({
  className: 'custom-map-marker',
  html: `<div class="marker-pin dropoff-pin"></div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15]
})

const carIcon = L.divIcon({
  className: 'custom-map-marker',
  html: `<div class="marker-pin car-pin">🛵</div>`,
  iconSize: [40, 40],
  iconAnchor: [20, 20]
})

onMounted(() => {
  rideStore.connectWebSocket()

  // Initialize map fullscreen
  map = L.map('passenger-map', { zoomControl: false }).setView([pickup.value.lat, pickup.value.lng], 15)
  
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
  }).addTo(map)

  // Start Geolocating
  if ("geolocation" in navigator) {
    watchId = navigator.geolocation.watchPosition(
      (position) => {
        const lat = position.coords.latitude
        const lng = position.coords.longitude
        
        // Store the raw device location always
        deviceLocation.value = { lat, lng }
        
        // Only update text on first load or if user hasn't typed a custom one
        if (!pickupText.value || isCurrentLocation.value) {
           pickup.value = { lat, lng }
           isCurrentLocation.value = true
           reverseGeocode(lat, lng, 'pickup')
           updatePickupMarker()
           
           // Only auto-center once initially
           if (!map.userHasMoved) {
             map.setView([lat, lng], 15)
           }
        }
      },
      (error) => {
        console.error("Error getting location:", error)
        updatePickupMarker() // Use default
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    )
  } else {
    updatePickupMarker()
  }

  // Detect manual drag to stop auto-centering
  map.on('dragstart', () => {
    map.userHasMoved = true
  })

  // Map click for setting locations
  map.on('click', (e) => {
    if (rideStore.currentBooking) return // lock if already booking

    if (activeSearchType.value === 'pickup') {
      pickup.value = { lat: e.latlng.lat, lng: e.latlng.lng }
      isCurrentLocation.value = false
      updatePickupMarker()
      reverseGeocode(e.latlng.lat, e.latlng.lng, 'pickup')
    } else {
      // Default to dropoff if null or dropoff is focused
      dropoff.value = e.latlng
      if (dropoffMarker) {
        dropoffMarker.setLatLng(e.latlng)
      } else {
        dropoffMarker = L.marker(e.latlng, { icon: destIcon }).addTo(map)
      }
      reverseGeocode(e.latlng.lat, e.latlng.lng, 'dropoff')
      activeSearchType.value = 'dropoff'
    }
  })
})

onUnmounted(() => {
  if (map) map.remove()
  if (watchId && navigator.geolocation) navigator.geolocation.clearWatch(watchId)
})

const updatePickupMarker = () => {
  if (pickupMarker) {
    pickupMarker.setLatLng([pickup.value.lat, pickup.value.lng])
  } else {
    pickupMarker = L.marker([pickup.value.lat, pickup.value.lng], { icon: userIcon }).addTo(map)
  }
}

const centerOnUser = () => {
  if (deviceLocation.value) {
    const lat = deviceLocation.value.lat;
    const lng = deviceLocation.value.lng;
    pickup.value = { lat, lng }
    isCurrentLocation.value = true
    map.flyTo([lat, lng], 16, { animate: true, duration: 0.8 })
    map.userHasMoved = false
    updatePickupMarker()
    reverseGeocode(lat, lng, 'pickup')
  } else {
    alert("Still getting your location...")
  }
}

const requestRide = async () => {
  if (!dropoff.value) return
  await rideStore.createBooking(pickup.value.lat, pickup.value.lng, dropoff.value.lat, dropoff.value.lng)
  
  // Center map to show both markers
  const bounds = L.latLngBounds([pickup.value.lat, pickup.value.lng], [dropoff.value.lat, dropoff.value.lng])
  map.flyToBounds(bounds, { padding: [50, 50], animate: true })
}

const cancelRide = async () => {
  if (rideStore.currentBooking) {
    await rideStore.cancelBooking(rideStore.currentBooking.id)
  }
}

// Watch for ride cancellation cleanup
watch(() => rideStore.currentBooking, (newVal, oldVal) => {
  if (!newVal && oldVal) {
    // Ride was cancelled or ended
    if (driverMarker) {
      map.removeLayer(driverMarker)
      driverMarker = null
    }
    // If it was cancelled by someone else, notify
    if (oldVal.status !== 'completed') {
       alert("Ride has been cancelled.")
    }
  }
})

// Watch for driver location updates
watch(() => rideStore.driverLocation, (newLoc) => {
  if (!newLoc) return
  console.log("PassengerView: Updating driver marker to", newLoc)
  
  if (!driverMarker) {
    driverMarker = L.marker([newLoc.lat, newLoc.lng], { icon: carIcon }).addTo(map)
  } else {
    // Animate smoothly
    driverMarker.setLatLng([newLoc.lat, newLoc.lng])
  }

  // Auto-zoom to show both passenger and driver
  if (pickup.value && newLoc) {
    const bounds = L.latLngBounds([pickup.value.lat, pickup.value.lng], [newLoc.lat, newLoc.lng])
    map.flyToBounds(bounds, { padding: [100, 100], animate: true, duration: 1 })
  }
}, { deep: true })

</script>

<style scoped>
/* Mobile First Layout */
.passenger-layout {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #f0f0f0;
}

.map-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* Global Map Marker Styles (Leaflet generates these dynamically) */
:deep(.custom-map-marker) {
  background: transparent;
  border: none;
}
:deep(.marker-pin) {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}
:deep(.pickup-pin) { background: #3498db; }
:deep(.dropoff-pin) { background: #9b59b6; }
:deep(.car-pin) { background: #fff; border: 2px solid #2ecc71; }

:deep(.marker-pulse) {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  background: rgba(52, 152, 219, 0.4);
  border-radius: 50%;
  animation: pulse 2s infinite ease-out;
  z-index: 1;
}

@keyframes pulse {
  0% { transform: translate(-50%, -50%) scale(0.5); opacity: 1; }
  100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
}

/* UI Overlays */
.top-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 1rem;
  z-index: 1000;
  pointer-events: none; /* Let clicks pass through to map where transparent */
}

.back-btn {
  pointer-events: auto;
  background: #fff;
  border: none;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  margin-bottom: 1rem;
  color: #333;
  cursor: pointer;
}

.route-card {
  pointer-events: auto;
  background: #fff;
  border-radius: 16px;
  padding: 1rem 1.25rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  border: 1px solid rgba(0,0,0,0.05);
  color: #333;
  backdrop-filter: none; /* solid background for better readability over map */
}

.route-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.back-btn-inline {
  background: #f3f4f6;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #333;
  cursor: pointer;
  transition: background-color 0.2s;
}
.back-btn-inline:hover {
  background: #e5e7eb;
}

.header-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  flex-shrink: 0;
}
.header-face-img {
  width: 100%; height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.route-header h3 {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0;
}

.route-inputs {
  display: flex;
  flex-direction: column;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem;
  margin: -0.5rem;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.input-row.active-row {
  background-color: rgba(46, 49, 146, 0.05); /* subtle blue tint */
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 0 0 1px #ddd;
}
.pickup-dot { background: #3498db; }
.dropoff-dot { background: #9b59b6; }

.input-divider {
  width: 2px;
  height: 16px;
  background: #eee;
  margin-left: 5px;
  margin-top: 4px;
  margin-bottom: 4px;
}

.input-content {
  display: flex;
  flex-direction: column;
}

.label {
  font-size: 0.75rem;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.value {
  font-size: 0.9rem;
  font-weight: 600;
  color: #222;
}
.value.placeholder { color: #aaa; font-weight: 500; }
.badge { color: #3498db; font-size: 0.75rem; }

.location-input {
  border: none;
  background: transparent;
  font-size: 0.95rem;
  font-weight: 600;
  color: #222;
  width: 100%;
  padding: 0.25rem 0;
  outline: none;
  font-family: inherit;
}
.location-input::placeholder {
  color: #aaa;
  font-weight: 500;
}
.location-input:disabled {
  background: transparent;
  color: #666;
}

.relative { position: relative; }
.w-100 { width: 100%; }

.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  margin-top: 5px;
  padding: 0;
  list-style: none;
  max-height: 200px;
  overflow-y: auto;
  z-index: 2000;
  border: 1px solid #eee;
}

.suggestions-list li {
  padding: 0.75rem 1rem;
  font-size: 0.85rem;
  color: #333;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestions-list li:hover {
  background: #f8f9fa;
  color: #2e3192;
}

.suggestions-list li:last-child {
  border-bottom: none;
}

.blink { animation: textBlink 1.5s infinite; }
@keyframes textBlink { 50% { opacity: 0.5; } }

.gps-btn-inline {
  background: transparent;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3498db;
  cursor: pointer;
  transition: background-color 0.2s;
  flex-shrink: 0;
}
.gps-btn-inline:hover {
  background: rgba(52, 152, 219, 0.1);
}
.gps-btn-inline:active { transform: scale(0.9); }

/* Bottom Sheet */
.bottom-sheet {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: #fff;
  border-radius: 24px 24px 0 0;
  padding: 0;
  z-index: 1000;
  box-shadow: 0 -8px 24px rgba(0,0,0,0.1);
  color: #333;
  height: 55vh;
  display: flex; flex-direction: column;
  transform: translateY(calc(100% - 110px));
  transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.bottom-sheet.expanded {
  transform: translateY(0);
}

.sheet-header {
  padding: 1.25rem 1.5rem 0.75rem 1.5rem;
  cursor: pointer;
  flex-shrink: 0;
  border-bottom: 1px solid #f0f0f0;
}

.sheet-content-wrapper {
  padding: 0 1.5rem 1.5rem 1.5rem;
  overflow-y: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}
.bottom-sheet.expanded .sheet-content-wrapper {
  overflow-y: auto;
}
.h-100 { height: 100%; }
.flex-col { display: flex; flex-direction: column; }

.drag-handle {
  width: 40px; height: 4px;
  background: #ddd; border-radius: 2px;
  margin: 0 auto 0.75rem auto;
  flex-shrink: 0;
}

.sheet-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0;
  text-align: center;
  flex-shrink: 0;
  color: #2e3192;
}

.ride-options {
  margin-bottom: 1.5rem;
}

.ride-option {
  display: flex;
  align-items: center;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  transition: all 0.2s;
}
.ride-option.active {
  border-color: #2e3192; /* JoyRide Blue */
  background: rgba(46, 49, 146, 0.05);
}

.ride-icon { font-size: 2rem; margin-right: 1rem; }
.ride-details h4 { font-weight: 700; margin-bottom: 0.25rem; }
.ride-details p { font-size: 0.8rem; color: #666; }
.ride-price { margin-left: auto; font-weight: 700; font-size: 1.1rem; color: #2e3192; }

.btn-large {
  padding: 1rem;
  font-size: 1.1rem;
  border-radius: 12px;
  background: #2e3192; /* JoyRide Blue */
  width: 100%;
}
.btn-large:disabled { background: #ccc; }

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 0.8rem;
  border-radius: 8px;
  font-weight: bold;
}
.mt-3 { margin-top: 0.75rem; }

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 99px;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.status-badge.pending { background: #fef08a; color: #854d0e; }
.status-badge.accepted { background: #bbf7d0; color: #166534; }
.status-badge.arrived { background: #3498db; color: #fff; }

.status-content { margin-top: 1.5rem; text-align: center; }
.waiting {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: #666;
}
.driver-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 12px;
}
.driver-info.highlight {
  background: #ebf8ff;
  border: 2px solid #3498db;
}
.driver-avatar {
  font-size: 2.5rem;
  background: #fff;
  width: 60px; height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.blink-fast { animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0.6; } }

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #2e3192;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
