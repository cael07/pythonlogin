<template>
  <div class="driver-container">
    <header class="header">
      <h1>Driver Mode</h1>
      <button @click="$router.push('/dashboard')" class="btn-secondary">Back to Dashboard</button>
    </header>

    <div class="content-section">
      <div class="sidebar panel">
        <h3>Available Requests</h3>
        <button @click="rideStore.fetchBookings()" class="btn-secondary mt-2 mb-3 w-100">Refresh</button>
        
        <div v-if="rideStore.bookings.length === 0">
          <p class="text-muted">No rides available right now.</p>
        </div>
        
        <div v-for="booking in rideStore.bookings" :key="booking.id" class="booking-card">
          <div v-if="booking.status === 'pending'">
            <p><strong>Pickup:</strong> {{ booking.pickup_lat.toFixed(4) }}, {{ booking.pickup_lng.toFixed(4) }}</p>
            <p><strong>Dropoff:</strong> {{ booking.dropoff_lat.toFixed(4) }}, {{ booking.dropoff_lng.toFixed(4) }}</p>
            <button @click="acceptRide(booking)" class="btn-primary mt-2">Accept Ride</button>
          </div>
        </div>

        <div v-if="rideStore.currentBooking" class="active-ride-panel mt-4">
          <h3>Active Ride</h3>
          <p><strong>Status:</strong> Driving to passenger...</p>
          <p class="text-success blink">Simulating Movement...</p>
        </div>
      </div>

      <div class="map-container">
        <div id="driver-map" class="map"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import { useRideStore } from '../stores/ride'
import { useAuthStore } from '../stores/auth'

const rideStore = useRideStore()
const authStore = useAuthStore()
let map = null
let driverMarker = null
let passengerMarker = null
let animationInterval = null

// Initial dummy driver location
const driverLocation = ref({ lat: 14.5800, lng: 120.9700 })

onMounted(async () => {
  rideStore.connectWebSocket()
  await rideStore.fetchBookings()

  map = L.map('driver-map').setView([driverLocation.value.lat, driverLocation.value.lng], 13)
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map)

  const carIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
    iconSize: [25, 41], iconAnchor: [12, 41]
  })

  driverMarker = L.marker([driverLocation.value.lat, driverLocation.value.lng], { icon: carIcon })
    .addTo(map)
    .bindPopup('You are here')
})

onUnmounted(() => {
  if (map) map.remove()
  if (animationInterval) clearInterval(animationInterval)
})

const acceptRide = async (booking) => {
  const success = await rideStore.acceptBooking(booking.id)
  if (success) {
    const userIcon = L.icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
      iconSize: [25, 41], iconAnchor: [12, 41]
    })
    
    // Show passenger pickup
    passengerMarker = L.marker([booking.pickup_lat, booking.pickup_lng], { icon: userIcon })
      .addTo(map)
      .bindPopup('Passenger')
      .openPopup()
      
    // Re-center map to show both
    const bounds = L.latLngBounds([driverLocation.value.lat, driverLocation.value.lng], [booking.pickup_lat, booking.pickup_lng])
    map.fitBounds(bounds, { padding: [50, 50] })
    
    // Simulate movement
    startSimulation(booking)
  }
}

const startSimulation = (booking) => {
  const targetLat = booking.pickup_lat
  const targetLng = booking.pickup_lng
  
  // Total steps to reach destination
  const steps = 60
  let currentStep = 0
  
  const latStep = (targetLat - driverLocation.value.lat) / steps
  const lngStep = (targetLng - driverLocation.value.lng) / steps
  
  animationInterval = setInterval(() => {
    currentStep++
    driverLocation.value.lat += latStep
    driverLocation.value.lng += lngStep
    
    // Update marker on map
    if (driverMarker) {
      driverMarker.setLatLng([driverLocation.value.lat, driverLocation.value.lng])
    }
    
    // Send to websocket so passenger sees it
    rideStore.sendLocationUpdate(booking.id, booking.passenger_id, driverLocation.value.lat, driverLocation.value.lng)
    
    if (currentStep >= steps) {
      clearInterval(animationInterval)
      alert("Arrived at pickup location!")
    }
  }, 500) // Update every 500ms
}

</script>

<style scoped>
.driver-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.content-section {
  display: flex;
  gap: 20px;
  height: 600px;
}
.sidebar {
  width: 350px;
  overflow-y: auto;
}
.map-container {
  flex: 1;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  z-index: 1;
}
.map {
  width: 100%;
  height: 100%;
}
.panel {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.booking-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  border-left: 4px solid #3498db;
}
.w-100 { width: 100%; }
.mt-2 { margin-top: 10px; }
.mt-4 { margin-top: 20px; }
.mb-3 { margin-bottom: 15px; }
.text-muted { color: #7f8c8d; }
.text-success { color: #2ecc71; font-weight: bold; }
@keyframes blinker {
  50% { opacity: 0; }
}
.blink {
  animation: blinker 1s linear infinite;
}
</style>
