<template>
  <div class="driver-layout">
    <!-- Fullscreen Map Background -->
    <div id="driver-map" class="map-container"></div>

    <!-- Top Overlay Elements -->
    <div class="top-overlay">
      <!-- Status Card -->
      <div class="route-card glass">
        <div class="route-header">
          <button class="back-btn-inline" @click="$router.push('/dashboard')">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
          </button>
          <div v-if="authStore.user?.face_image_base64" class="header-avatar">
            <img :src="authStore.user.face_image_base64" alt="Me" class="header-face-img" />
          </div>
          <h3 class="flex-1">Driver Mode</h3>
          <button @click="rideStore.fetchBookings()" class="refresh-btn">
             <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Bottom Sheet -->
    <div :class="['bottom-sheet', 'glass', { expanded: isSheetExpanded }]">
      <div class="sheet-header" @click="isSheetExpanded = !isSheetExpanded">
        <div class="drag-handle"></div>
        <h3 v-if="!rideStore.currentBooking" class="sheet-title">Incoming Requests ({{ rideStore.bookings.length }})</h3>
        <h3 v-else class="sheet-title">Active Ride</h3>
      </div>

      <div class="sheet-content-wrapper">
        <div v-if="!rideStore.currentBooking" class="h-100 flex-col">
          <div v-if="rideStore.bookings.length === 0" class="empty-state">
            <div class="radar-pulse">📡</div>
            <p>Looking for passengers...</p>
          </div>
          
          <div class="requests-list">
            <div v-for="booking in rideStore.bookings" :key="booking.id" class="booking-card">
              <div class="passenger-preview">
                <div v-if="booking.passenger_image" class="passenger-avatar-small">
                  <img :src="booking.passenger_image" class="passenger-face-img" />
                </div>
                <div v-else class="passenger-avatar-small">👤</div>
                <span class="passenger-name-small">{{ booking.passenger_name || 'Passenger' }}</span>
              </div>
              <div class="route-preview">
                <div class="loc-row">
                  <span class="dot pickup-dot"></span>
                  <span class="text-truncate">Pickup: {{ addressNames[booking.id]?.pickup || `${booking.pickup_lat.toFixed(4)}, ${booking.pickup_lng.toFixed(4)}` }}</span>
                </div>
                <div class="loc-row">
                  <span class="dot dropoff-dot"></span>
                  <span class="text-truncate">Dropoff: {{ addressNames[booking.id]?.dropoff || `${booking.dropoff_lat.toFixed(4)}, ${booking.dropoff_lng.toFixed(4)}` }}</span>
                </div>
              </div>
              <div class="d-flex gap-2 mt-2">
                <button @click="acceptRide(booking)" class="btn-primary flex-1">Accept</button>
                <button @click="rideStore.dismissBooking(booking.id)" class="btn-secondary flex-1">Dismiss</button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="status-panel">
          <div class="status-content">
            <div v-if="rideStore.currentBooking.status === 'accepted'" class="accepted">
              <div class="driver-info">
                <div v-if="rideStore.currentBooking.passenger_image" class="driver-avatar blink-fast">
                   <img :src="rideStore.currentBooking.passenger_image" class="passenger-face-img" />
                </div>
                <div v-else class="driver-avatar blink-fast">🚗</div>
                <div>
                  <h4>Driving to {{ rideStore.currentBooking.passenger_name || 'Passenger' }}</h4>
                  <p>Location updating live</p>
                </div>
              </div>
            </div>

            <div v-if="rideStore.currentBooking.status === 'arrived'" class="accepted arrived">
              <div class="driver-info highlight">
                <div v-if="rideStore.currentBooking.passenger_image" class="driver-avatar">
                   <img :src="rideStore.currentBooking.passenger_image" class="passenger-face-img" />
                </div>
                <div v-else class="driver-avatar">👤</div>
                <div>
                  <h4>Arrived for {{ rideStore.currentBooking.passenger_name || 'Passenger' }}</h4>
                  <p>Waiting for passenger...</p>
                </div>
              </div>
            </div>

            <div v-if="rideStore.currentBooking.status === 'started'" class="accepted in-progress">
              <div class="driver-info highlight">
                <div class="driver-avatar">🛵</div>
                <div>
                  <h4>Ride in Progress</h4>
                  <p>Heading to destination</p>
                </div>
              </div>
            </div>

            <!-- Manual Arrival Button (Only shown while en route) -->
            <button 
              v-if="rideStore.currentBooking.status === 'accepted'"
              class="btn-primary w-100 mt-3" 
              @click="rideStore.notifyArrived(rideStore.currentBooking.id)"
            >
              I Have Arrived
            </button>

            <!-- Start Ride Button -->
            <button 
              v-if="rideStore.currentBooking.status === 'arrived'"
              class="btn-primary w-100 mt-3" 
              @click="onStartRide"
            >
              Start Ride
            </button>

            <!-- Complete Ride Button -->
            <button 
              v-if="rideStore.currentBooking.status === 'started'"
              class="btn-success w-100 mt-3" 
              @click="onCompleteRide"
            >
              Complete Ride
            </button>

            <button v-if="rideStore.currentBooking.status !== 'started'" class="btn-secondary mt-3 w-100" @click="cancelRide">Cancel Ride</button>
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
import { useAuthStore } from '../stores/auth'

const rideStore = useRideStore()
const authStore = useAuthStore()
let map = null
let driverMarker = null
let passengerMarker = null
let animationInterval = null
let heartbeatInterval = null
let watchId = null
let routeLine = null

const isSheetExpanded = ref(false)
const addressNames = ref({})

const resolveAddress = async (lat, lng) => {
  try {
    // Nominatim policy: 1 request per second max.
    await new Promise(r => setTimeout(r, 1100)) 
    const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`, {
      headers: { 'User-Agent': 'JoyRide-App-PythonLogin-V1' }
    })
    
    if (res.status === 429) return `${lat.toFixed(4)}, ${lng.toFixed(4)}`

    const data = await res.json()
    if (data && data.display_name) {
      const parts = data.display_name.split(',')
      return parts.slice(0, 3).join(',')
    }
  } catch (err) {
    console.warn("Reverse geocoding suppressed")
  }
  return `${lat.toFixed(4)}, ${lng.toFixed(4)}`
}

watch(() => rideStore.bookings, async (newBookings) => {
  for (const b of newBookings) {
    if (!addressNames.value[b.id]) {
      // Prevents multiple fetches for the same ID
      addressNames.value[b.id] = { pickup: 'Resolving...', dropoff: 'Resolving...' }
      const pickup = await resolveAddress(b.pickup_lat, b.pickup_lng)
      const dropoff = await resolveAddress(b.dropoff_lat, b.dropoff_lng)
      addressNames.value[b.id] = { pickup, dropoff }
    }
  }
}, { deep: true, immediate: true })

// Real or fallback driver location
const driverLocation = ref({ lat: 14.5800, lng: 120.9700 })

const carIcon = L.divIcon({
  className: 'custom-map-marker',
  html: `<div class="marker-pin car-pin">🚗</div>`,
  iconSize: [40, 40],
  iconAnchor: [20, 20]
})

const userIcon = L.divIcon({
  className: 'custom-map-marker',
  html: `<div class="marker-pin pickup-pin">👤</div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15]
})

onMounted(async () => {
  rideStore.connectWebSocket()
  await rideStore.fetchActiveBooking() // Fetch if already in a ride
  await rideStore.fetchBookings()      // Fetch new requests

  map = L.map('driver-map', { zoomControl: false }).setView([driverLocation.value.lat, driverLocation.value.lng], 15)
  
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
  }).addTo(map)

  // Try Geolocating the driver
  if ("geolocation" in navigator) {
    watchId = navigator.geolocation.watchPosition(
      (position) => {
        driverLocation.value = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        }
        updateDriverMarker()
        // Send live GPS update if in a ride
        if (rideStore.currentBooking) {
          rideStore.updateLocation(rideStore.currentBooking.id, driverLocation.value.lat, driverLocation.value.lng)
        }
        if (!map.userHasMoved && !rideStore.currentBooking) {
          map.setView([driverLocation.value.lat, driverLocation.value.lng], 15)
        }
      },
      (error) => {
        console.error("Driver Geolocation Error:", error)
        updateDriverMarker()
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    )
  } else {
    updateDriverMarker()
  }

  map.on('dragstart', () => { map.userHasMoved = true })

  // Heartbeat to keep driver icon visible even when stationary
  heartbeatInterval = setInterval(() => {
    if (rideStore.currentBooking && driverLocation.value) {
      rideStore.updateLocation(rideStore.currentBooking.id, driverLocation.value.lat, driverLocation.value.lng)
    }
  }, 10000) // Every 10 seconds
})

onUnmounted(() => {
  if (map) map.remove()
  if (animationInterval) clearInterval(animationInterval)
  if (heartbeatInterval) clearInterval(heartbeatInterval)
  if (watchId && navigator.geolocation) navigator.geolocation.clearWatch(watchId)
})

const updateDriverMarker = () => {
  if (!driverMarker) {
    driverMarker = L.marker([driverLocation.value.lat, driverLocation.value.lng], { icon: carIcon }).addTo(map)
  } else {
    driverMarker.setLatLng([driverLocation.value.lat, driverLocation.value.lng])
  }
}

const fetchRoute = async (start, end) => {
  try {
    const res = await fetch(`https://router.project-osrm.org/route/v1/driving/${start.lng},${start.lat};${end.lng},${end.lat}?overview=full&geometries=geojson`)
    const data = await res.json()
    if (data.code === 'Ok' && data.routes.length > 0) {
      return data.routes[0].geometry.coordinates.map(c => ({ lat: c[1], lng: c[0] }))
    }
  } catch (err) {
    console.error("Routing error:", err)
  }
  return null
}

const drawRouteLine = (points) => {
  if (routeLine) map.removeLayer(routeLine)
  const latLngs = points.map(p => [p.lat, p.lng])
  routeLine = L.polyline(latLngs, {
    color: '#2e3192',
    weight: 6,
    opacity: 0.6,
    lineJoin: 'round',
    dashArray: '1, 10', // subtle dashed look
    dashOffset: '0'
  }).addTo(map)
  
  // Add a solid line underneath for better visibility
  L.polyline(latLngs, {
    color: '#2e3192',
    weight: 2,
    opacity: 0.3
  }).addTo(map)
}

const acceptRide = async (booking) => {
  const success = await rideStore.acceptBooking(booking.id)
  if (success) {
    // Send initial location immediately so passenger sees icon right away
    rideStore.updateLocation(booking.id, driverLocation.value.lat, driverLocation.value.lng)

    // Show passenger pickup
    passengerMarker = L.marker([booking.pickup_lat, booking.pickup_lng], { icon: userIcon }).addTo(map)
      
    // Fetch road route
    const points = await fetchRoute(driverLocation.value, { lat: booking.pickup_lat, lng: booking.pickup_lng })
    
    if (points) {
      drawRouteLine(points)
      // Re-center map to show the whole route
      const bounds = L.latLngBounds(points.map(p => [p.lat, p.lng]))
      map.flyToBounds(bounds, { padding: [50, 50], animate: true })
      startSimulation(booking, points)
    } else {
      // Fallback to straight line
      const bounds = L.latLngBounds([driverLocation.value.lat, driverLocation.value.lng], [booking.pickup_lat, booking.pickup_lng])
      map.flyToBounds(bounds, { padding: [50, 50], animate: true })
      startSimulation(booking)
    }
  }
}

const cancelRide = async () => {
  if (rideStore.currentBooking) {
    await rideStore.cancelBooking(rideStore.currentBooking.id)
  }
}

const onStartRide = async () => {
  const success = await rideStore.startRide(rideStore.currentBooking.id)
  if (success) {
    const booking = rideStore.currentBooking
    // Fetch route to destination
    const points = await fetchRoute(driverLocation.value, { lat: booking.dropoff_lat, lng: booking.dropoff_lng })
    if (points) {
      drawRouteLine(points)
      const bounds = L.latLngBounds(points.map(p => [p.lat, p.lng]))
      map.flyToBounds(bounds, { padding: [50, 50], animate: true })
      startSimulation(booking, points, true) // pass true to indicate to destination
    } else {
      // Fallback
      startSimulation(booking, null, true)
    }
  }
}

const onCompleteRide = async () => {
  if (confirm("Have you reached the destination?")) {
     await rideStore.completeRide(rideStore.currentBooking.id)
  }
}

// Watch for ride cancellation cleanup
watch(() => rideStore.currentBooking, (newVal, oldVal) => {
  if (!newVal && oldVal) {
    // Ride was cancelled or ended
    if (passengerMarker) {
      map.removeLayer(passengerMarker)
      passengerMarker = null
    }
    if (routeLine) {
      map.removeLayer(routeLine)
      routeLine = null
    }
    if (animationInterval) {
      clearInterval(animationInterval)
      animationInterval = null
    }
    // If it was cancelled by someone else, notify
    if (oldVal.status !== 'completed') {
       alert("Ride has been cancelled.")
    }
  }
})

const getDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371000 // Radius of the earth in m
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

const startSimulation = (booking, routePoints = null, toDestination = false) => {
  if (animationInterval) clearInterval(animationInterval)
  
  const targetLat = toDestination ? booking.dropoff_lat : booking.pickup_lat
  const targetLng = toDestination ? booking.dropoff_lng : booking.pickup_lng
  const activeStatus = toDestination ? 'started' : 'accepted'
  
  if (routePoints) {
    let currentStep = 0
    animationInterval = setInterval(async () => {
      // If status changed, stop simulation
      if (rideStore.currentBooking?.status !== activeStatus) {
        clearInterval(animationInterval)
        animationInterval = null
        return
      }

      if (currentStep >= routePoints.length) {
        clearInterval(animationInterval)
        animationInterval = null
        if (!toDestination) {
          await rideStore.notifyArrived(booking.id)
        }
        if (routeLine) map.removeLayer(routeLine)
        return
      }

      driverLocation.value = routePoints[currentStep]
      updateDriverMarker()
      
      // Update route line to show remaining path
      if (routeLine) {
        routeLine.setLatLngs(routePoints.slice(currentStep).map(p => [p.lat, p.lng]))
      }

      rideStore.updateLocation(booking.id, driverLocation.value.lat, driverLocation.value.lng)
      if (!map.userHasMoved) {
        map.panTo([driverLocation.value.lat, driverLocation.value.lng], { animate: true })
      }
      currentStep++
    }, 1000)
  } else {
    // Fallback: Straight line simulation
    const speedMetersPerStep = 25 
    animationInterval = setInterval(async () => {
      // If status changed, stop simulation
      if (rideStore.currentBooking?.status !== activeStatus) {
        clearInterval(animationInterval)
        animationInterval = null
        return
      }

      const dist = getDistance(driverLocation.value.lat, driverLocation.value.lng, targetLat, targetLng)
      if (dist < 30) {
        clearInterval(animationInterval)
        animationInterval = null
        driverLocation.value = { lat: targetLat, lng: targetLng }
        updateDriverMarker()
        if (!toDestination) {
           await rideStore.notifyArrived(booking.id)
        }
        return
      }
      const ratio = speedMetersPerStep / dist
      driverLocation.value.lat += (targetLat - driverLocation.value.lat) * ratio
      driverLocation.value.lng += (targetLng - driverLocation.value.lng) * ratio
      updateDriverMarker()
      rideStore.updateLocation(booking.id, driverLocation.value.lat, driverLocation.value.lng)
      if (!map.userHasMoved) {
        map.panTo([driverLocation.value.lat, driverLocation.value.lng], { animate: true })
      }
    }, 1500)
  }
}

</script>

<style scoped>
.driver-layout {
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

:deep(.custom-map-marker) { background: transparent; border: none; }
:deep(.marker-pin) {
  width: 30px; height: 30px;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
}
:deep(.car-pin) { background: #2e3192; border: 3px solid #fff; }
:deep(.pickup-pin) { background: #3498db; }

/* UI Overlays */
.top-overlay {
  position: absolute;
  top: 0; left: 0; right: 0;
  padding: 1rem;
  z-index: 1000;
  pointer-events: none;
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
.back-btn-inline:hover { background: #e5e7eb; }

.header-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  flex-shrink: 0;
}
.header-face-img, .passenger-face-img {
  width: 100%; height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.flex-1 { flex: 1; }

.route-card {
  pointer-events: auto;
  background: #fff;
  border-radius: 16px;
  padding: 1rem 1.25rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  border: 1px solid rgba(0,0,0,0.05);
  color: #333;
}

.route-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.route-header h3 {
  font-size: 1.1rem;
  font-weight: 700;
}

.refresh-btn {
  background: #f0f0f0;
  border: none;
  border-radius: 50%;
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}

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

.requests-list {
  overflow-y: auto;
  flex: 1;
}

.empty-state {
  text-align: center;
  padding: 2rem 0;
  color: #888;
}

.radar-pulse {
  font-size: 3rem;
  margin-bottom: 1rem;
  animation: radar 2s infinite;
}
@keyframes radar {
  0% { transform: scale(0.9); opacity: 1; }
  100% { transform: scale(1.2); opacity: 0.5; }
}

.booking-card {
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  margin-bottom: 1rem;
}

.passenger-preview {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #f0f0f0;
}

.passenger-avatar-small {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: #eee;
  overflow: hidden;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.9rem;
}

.passenger-name-small {
  font-weight: 600;
  font-size: 0.9rem;
  color: #2e3192;
}

.loc-row {
  display: flex; align-items: center; gap: 0.5rem;
  font-size: 0.85rem; color: #555; margin-bottom: 0.4rem;
}
.dot { width: 10px; height: 10px; border-radius: 50%; }
.pickup-dot { background: #3498db; }
.dropoff-dot { background: #9b59b6; }

.btn-primary {
  background: #2e3192;
  color: #fff;
  border: none;
  padding: 0.8rem;
  border-radius: 8px;
  font-weight: bold;
}
.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 0.8rem;
  border-radius: 8px;
  font-weight: bold;
}
.btn-success {
  background: #10b981;
  color: #fff;
  border: none;
  padding: 0.8rem;
  border-radius: 8px;
  font-weight: bold;
}
.d-flex { display: flex; }
.gap-2 { gap: 0.5rem; }
.flex-1 { flex: 1; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.w-100 { width: 100%; }

.driver-info {
  display: flex; align-items: center; justify-content: center; gap: 1rem;
  background: #f8f9fa; padding: 1rem; border-radius: 12px;
}
.driver-info.highlight {
  background: #ebf8ff;
  border: 2px solid #3498db;
}
.driver-avatar {
  font-size: 2rem; background: #fff;
  width: 60px; height: 60px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.blink-fast { animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0.6; } }
</style>
