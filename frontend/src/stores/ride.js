import { defineStore } from 'pinia'
import { useAuthStore } from './auth'

export const useRideStore = defineStore('ride', {
  state: () => ({
    ws: null,
    bookings: [],
    currentBooking: null,
    driverLocation: null, // { lat, lng }
    passengerLocation: null, // { lat, lng }
  }),

  actions: {
    getApiHost() {
      // Use the actual production URL as default for Render
      const productionHost = 'https://pythonlogin-api.onrender.com';
      let base = import.meta.env.VITE_API_URL || productionHost;
      // If VITE_API_URL has /auth at the end, strip it
      if (base.endsWith('/auth')) {
        base = base.replace(/\/auth$/, '');
      }
      return base;
    },

    connectWebSocket() {
      if (this.ws) return
      const auth = useAuthStore()
      if (!auth.user) {
        console.warn("WS: No auth user found")
        return
      }

      const base = this.getApiHost();
      const wsHost = base.replace('http://', 'ws://').replace('https://', 'wss://');
      const wsUrl = `${wsHost}/ride/ws/${auth.user.id}`
      
      console.log("WS: Connecting to", wsUrl)
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        console.log("WS: Connection opened")
      }

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'new_booking') {
          console.log("WS: New booking received", data.booking)
          this.bookings.push(data.booking)
        } else if (data.type === 'ride_accepted') {
          console.log("DEBUG: Ride Accepted Message Data ->", data)
          if (this.currentBooking && this.currentBooking.id === data.booking_id) {
            // Reassign the whole object to ensure Vue detects the change
            this.currentBooking = {
              ...this.currentBooking,
              status: 'accepted',
              driver_id: data.driver_id,
              driver_name: data.driver_name,
              driver_image: data.driver_image
            }
          }
        } else if (data.type === 'ride_arrived') {
          console.log("WS: Driver has arrived", data)
          if (this.currentBooking && this.currentBooking.id === data.booking_id) {
            this.currentBooking = {
              ...this.currentBooking,
              status: 'arrived'
            }
          }
        } else if (data.type === 'driver_location') {
          console.log("WS: Received driver location", data)
          // Using == instead of === for loose type matching just in case
          if (this.currentBooking && this.currentBooking.id == data.booking_id) {
            this.driverLocation = { lat: data.lat, lng: data.lng }
          }
        } else if (data.type === 'ride_cancelled') {
          if (this.currentBooking && this.currentBooking.id === data.booking_id) {
            this.currentBooking = null
            this.driverLocation = null
          }
          this.bookings = this.bookings.filter(b => b.id !== data.booking_id)
        } else if (data.type === 'booking_taken') {
          // Another driver accepted the ride, remove it from my list
          this.bookings = this.bookings.filter(b => b.id !== data.booking_id)
        }
      }
      
      this.ws.onclose = () => {
        console.log("WebSocket connection closed")
        setTimeout(() => this.connectWebSocket(), 3000) // reconnect
      }
    },

    disconnectWebSocket() {
      if (this.ws) {
        this.ws.close()
        this.ws = null
      }
    },

    sendLocationUpdate(bookingId, passengerId, lat, lng) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'location_update',
          booking_id: bookingId,
          passenger_id: passengerId,
          lat: lat,
          lng: lng
        }))
      }
    },

    updateLocation(bookingId, lat, lng) {
      if (!this.currentBooking) return
      this.sendLocationUpdate(bookingId, this.currentBooking.passenger_id, lat, lng)
    },

    dismissBooking(bookingId) {
      this.bookings = this.bookings.filter(b => b.id !== bookingId)
    },

    async notifyArrived(bookingId) {
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const host = isLocal ? 'http://localhost:8000' : this.getApiHost();
      
      try {
        await fetch(`${host}/ride/bookings/${bookingId}/arrived`, {
          method: 'POST'
        })
      } catch (err) {
        console.error("Failed to notify arrival:", err)
      }
    },

    async fetchActiveBooking() {
      const auth = useAuthStore()
      if (!auth.user) return
      
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const host = isLocal ? 'http://localhost:8000' : this.getApiHost();
      
      try {
        const res = await fetch(`${host}/ride/active/${auth.user.id}`)
        if (res.ok) {
          const booking = await res.json()
          if (booking) {
            this.currentBooking = booking
            this.passengerLocation = { lat: booking.pickup_lat, lng: booking.pickup_lng }
          }
        }
      } catch (err) {
        console.error("Failed to fetch active booking:", err)
      }
    },

    async cancelBooking(bookingId) {
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const host = isLocal ? 'http://localhost:8000' : this.getApiHost();
      
      try {
        const res = await fetch(`${host}/ride/bookings/${bookingId}/cancel`, {
          method: 'POST'
        })
        if (res.ok) {
          this.currentBooking = null
          this.driverLocation = null
          this.bookings = this.bookings.filter(b => b.id !== bookingId)
          return true
        }
      } catch (err) {
        console.error("Failed to cancel booking:", err)
      }
      return false
    },

    async fetchBookings() {
      const auth = useAuthStore()
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const host = isLocal ? 'http://localhost:8000' : this.getApiHost();
      
      try {
        const res = await fetch(`${host}/ride/bookings`)
        if (res.ok) {
          this.bookings = await res.json()
        }
      } catch (err) {
        console.error("Failed to fetch bookings:", err)
      }
    },

    async createBooking(pickupLat, pickupLng, dropoffLat, dropoffLng) {
      const auth = useAuthStore()
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const host = isLocal ? 'http://localhost:8000' : this.getApiHost();

      try {
        const res = await fetch(`${host}/ride/bookings`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            passenger_id: auth.user.id,
            pickup_lat: pickupLat,
            pickup_lng: pickupLng,
            dropoff_lat: dropoffLat,
            dropoff_lng: dropoffLng
          })
        })
        const data = await res.json()
        if (res.ok) {
          this.currentBooking = {
            id: data.booking_id,
            passenger_id: auth.user.id,
            status: 'pending',
            pickup_lat: pickupLat,
            pickup_lng: pickupLng,
            dropoff_lat: dropoffLat,
            dropoff_lng: dropoffLng
          }
          this.passengerLocation = { lat: pickupLat, lng: pickupLng }
          return data.booking_id
        }
      } catch (err) {
        console.error("Failed to create booking:", err)
      }
      return null
    },

    async acceptBooking(bookingId) {
      const auth = useAuthStore()
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const host = isLocal ? 'http://localhost:8000' : this.getApiHost();

      try {
        const res = await fetch(`${host}/ride/bookings/${bookingId}/accept`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ driver_id: auth.user.id })
        })
        const data = await res.json()
        if (res.ok) {
          // Find booking and set as current
          const booking = this.bookings.find(b => b.id === bookingId)
          if (booking) {
            booking.status = 'accepted'
            booking.driver_id = auth.user.id
            this.currentBooking = booking
          }
          return true
        } else {
          // Handle case where ride is already cancelled or taken
          alert(data.detail || "This ride is no longer available.")
          this.bookings = this.bookings.filter(b => b.id !== bookingId)
          return false
        }
      } catch (err) {
        console.error("Failed to accept booking:", err)
      }
      return false
    }
  }
})
