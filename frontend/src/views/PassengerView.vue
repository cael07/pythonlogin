<template>
  <div class="passenger-layout">
    <!-- Fullscreen Map Background -->
    <div id="passenger-map" class="map-container"></div>

    <!-- Top Overlay Elements -->
    <div class="top-overlay">
      <button class="back-btn" @click="$router.push('/dashboard')">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
      </button>

      <!-- Routing Card -->
      <div class="route-card glass">
        <div class="route-header">
          <h3>Your JoyRide Route</h3>
        </div>
        
        <div class="route-inputs">
          <div class="input-row">
            <div class="dot pickup-dot"></div>
            <div class="input-content">
              <span class="label">Pickup</span>
              <span class="value" v-if="pickup.lat">{{ pickup.lat.toFixed(4) }}, {{ pickup.lng.toFixed(4) }} <span class="badge" v-if="isCurrentLocation">(Current)</span></span>
              <span class="value placeholder" v-else>Locating...</span>
            </div>
          </div>
          <div class="input-divider"></div>
          <div class="input-row">
            <div class="dot dropoff-dot"></div>
            <div class="input-content">
              <span class="label">Drop-off</span>
              <span class="value" v-if="dropoff">{{ dropoff.lat.toFixed(4) }}, {{ dropoff.lng.toFixed(4) }}</span>
              <span class="value placeholder blink" v-else>Tap map to set drop-off</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- GPS Center Button -->
    <button class="gps-btn" @click="centerOnUser" aria-label="Center Map">
      <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3c-.46-4.17-3.77-7.48-7.94-7.94V1h-2v2.06C6.83 3.52 3.52 6.83 3.06 11H1v2h2.06c.46 4.17 3.77 7.48 7.94 7.94V23h2v-2.06c4.17-.46 7.48-3.77 7.94-7.94H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z"/></svg>
    </button>

    <!-- Bottom Sheet -->
    <div class="bottom-sheet glass">
      <div class="drag-handle"></div>

      <div v-if="!rideStore.currentBooking">
        <h3 class="sheet-title">Choose your Ride</h3>
        <div class="ride-options">
          <div class="ride-option active">
            <div class="ride-icon">🛵</div>
            <div class="ride-details">
              <h4>MC Taxi</h4>
              <p>Beat the traffic</p>
            </div>
            <div class="ride-price">₱ 152</div>
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
        <h3 class="sheet-title">Status: <span :class="['status-badge', rideStore.currentBooking.status]">{{ rideStore.currentBooking.status }}</span></h3>
        
        <div class="status-content">
          <div v-if="rideStore.currentBooking.status === 'pending'" class="waiting">
            <div class="spinner"></div>
            <p>Finding you a driver...</p>
          </div>
          <div v-if="rideStore.currentBooking.status === 'accepted'" class="accepted">
            <div class="driver-info">
              <div class="driver-avatar">👨‍✈️</div>
              <div>
                <h4>Driver is on the way!</h4>
                <p>Arriving shortly</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import { useRideStore } from '../stores/ride'
import { useRouter } from 'vue-router'

const rideStore = useRideStore()
const router = useRouter()
let map = null
let pickupMarker = null
let dropoffMarker = null
let driverMarker = null
let watchId = null

const pickup = ref({ lat: 14.5995, lng: 120.9842 }) // default fallback
const dropoff = ref(null)
const isCurrentLocation = ref(false)

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
        pickup.value = { lat, lng }
        isCurrentLocation.value = true
        
        updatePickupMarker()
        
        // Only auto-center once initially
        if (!map.userHasMoved) {
          map.setView([lat, lng], 15)
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

  // Map click for dropoff
  map.on('click', (e) => {
    if (rideStore.currentBooking) return // lock if already booking

    dropoff.value = e.latlng
    if (dropoffMarker) {
      dropoffMarker.setLatLng(e.latlng)
    } else {
      dropoffMarker = L.marker(e.latlng, { icon: destIcon }).addTo(map)
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
  if (pickup.value.lat) {
    map.flyTo([pickup.value.lat, pickup.value.lng], 16, { animate: true, duration: 0.8 })
    map.userHasMoved = false
  }
}

const requestRide = async () => {
  if (!dropoff.value) return
  await rideStore.createBooking(pickup.value.lat, pickup.value.lng, dropoff.value.lat, dropoff.value.lng)
  
  // Center map to show both markers
  const bounds = L.latLngBounds([pickup.value.lat, pickup.value.lng], [dropoff.value.lat, dropoff.value.lng])
  map.flyToBounds(bounds, { padding: [50, 50], animate: true })
}

// Watch for driver location updates
watch(() => rideStore.driverLocation, (newLoc) => {
  if (!newLoc) return
  
  if (!driverMarker) {
    driverMarker = L.marker([newLoc.lat, newLoc.lng], { icon: carIcon }).addTo(map)
  } else {
    // Animate smoothly
    driverMarker.setLatLng([newLoc.lat, newLoc.lng])
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
  padding: 1.25rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  border: 1px solid rgba(0,0,0,0.05);
  color: #333;
  backdrop-filter: none; /* solid background for better readability over map */
}

.route-header h3 {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.route-inputs {
  display: flex;
  flex-direction: column;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 1rem;
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

.blink { animation: textBlink 1.5s infinite; }
@keyframes textBlink { 50% { opacity: 0.5; } }

/* GPS Button */
.gps-btn {
  position: absolute;
  right: 1rem;
  bottom: calc(200px + 2rem); /* Above bottom sheet */
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #fff;
  border: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  color: #333;
  cursor: pointer;
  transition: transform 0.2s;
}
.gps-btn:active { transform: scale(0.95); }

/* Bottom Sheet */
.bottom-sheet {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  border-radius: 24px 24px 0 0;
  padding: 1.5rem;
  z-index: 1000;
  box-shadow: 0 -8px 24px rgba(0,0,0,0.1);
  color: #333;
  backdrop-filter: none;
}

.drag-handle {
  width: 40px;
  height: 4px;
  background: #ddd;
  border-radius: 2px;
  margin: 0 auto 1.5rem auto;
}

.sheet-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 1rem;
  text-align: center;
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

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 99px;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.status-badge.pending { background: #fef08a; color: #854d0e; }
.status-badge.accepted { background: #bbf7d0; color: #166534; }

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
