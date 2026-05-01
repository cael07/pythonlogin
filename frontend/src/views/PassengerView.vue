<template>
  <div class="passenger-container">
    <header class="header">
      <h1>Passenger Mode</h1>
      <button @click="$router.push('/dashboard')" class="btn-secondary">Back to Dashboard</button>
    </header>

    <div class="map-section">
      <div id="passenger-map" class="map"></div>
      
      <div class="controls panel">
        <div v-if="!rideStore.currentBooking">
          <h3>Request a Ride</h3>
          <p>Click on the map to set your destination.</p>
          <div v-if="dropoff" class="location-info">
            Destination set: {{ dropoff.lat.toFixed(4) }}, {{ dropoff.lng.toFixed(4) }}
            <button @click="requestRide" class="btn-primary mt-2">Book Ride</button>
          </div>
        </div>
        
        <div v-else class="status-panel">
          <h3>Ride Status: <span :class="rideStore.currentBooking.status">{{ rideStore.currentBooking.status }}</span></h3>
          <p v-if="rideStore.currentBooking.status === 'pending'">Waiting for a driver to accept...</p>
          <p v-if="rideStore.currentBooking.status === 'accepted'">Driver is on the way!</p>
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

const pickup = ref({ lat: 14.5995, lng: 120.9842 }) // Manila default
const dropoff = ref(null)

onMounted(() => {
  rideStore.connectWebSocket()

  // Initialize map
  map = L.map('passenger-map').setView([pickup.value.lat, pickup.value.lng], 13)
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map)

  // Custom icons
  const userIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
    iconSize: [25, 41], iconAnchor: [12, 41]
  })
  
  const destIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    iconSize: [25, 41], iconAnchor: [12, 41]
  })

  // Set pickup marker
  pickupMarker = L.marker([pickup.value.lat, pickup.value.lng], { icon: userIcon }).addTo(map)
    .bindPopup('You are here').openPopup()

  // Map click for dropoff
  map.on('click', (e) => {
    if (rideStore.currentBooking) return // lock if already booking

    dropoff.value = e.latlng
    if (dropoffMarker) {
      dropoffMarker.setLatLng(e.latlng)
    } else {
      dropoffMarker = L.marker(e.latlng, { icon: destIcon }).addTo(map).bindPopup('Destination')
    }
  })
})

onUnmounted(() => {
  if (map) map.remove()
})

const requestRide = async () => {
  if (!dropoff.value) return
  await rideStore.createBooking(pickup.value.lat, pickup.value.lng, dropoff.value.lat, dropoff.value.lng)
}

// Watch for driver location updates
watch(() => rideStore.driverLocation, (newLoc) => {
  if (!newLoc) return
  
  const carIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
    iconSize: [25, 41], iconAnchor: [12, 41]
  })

  if (!driverMarker) {
    driverMarker = L.marker([newLoc.lat, newLoc.lng], { icon: carIcon }).addTo(map).bindPopup('Your Driver')
  } else {
    // Simple animation by moving marker smoothly could be added, here we just setLatLng
    driverMarker.setLatLng([newLoc.lat, newLoc.lng])
  }
}, { deep: true })

</script>

<style scoped>
.passenger-container {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.map-section {
  display: flex;
  gap: 20px;
  height: 600px;
}
.map {
  flex: 1;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  z-index: 1;
}
.panel {
  width: 300px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.mt-2 { margin-top: 15px; }
.location-info {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 8px;
  font-size: 0.9em;
  margin-top: 10px;
}
.status-panel h3 { margin-bottom: 10px; }
.pending { color: #f39c12; }
.accepted { color: #2ecc71; }
</style>
