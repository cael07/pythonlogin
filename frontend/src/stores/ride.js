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
      // Find the base API URL correctly using the same env var as auth
      let base = import.meta.env.VITE_API_URL || 'https://pythonlogin-api.onrender.com';
      // If VITE_API_URL has /auth at the end, strip it
      if (base.endsWith('/auth')) {
        base = base.replace(/\/auth$/, '');
      }
      return base;
    },

    connectWebSocket() {
      const auth = useAuthStore()
      if (!auth.user) return

      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      let wsUrl = '';
      
      if (isLocal) {
        wsUrl = `ws://localhost:8000/ride/ws/${auth.user.id}`
      } else {
        const base = this.getApiHost();
        const wsHost = base.replace('http://', 'ws://').replace('https://', 'wss://');
        wsUrl = `${wsHost}/ride/ws/${auth.user.id}`
      }
      
      this.ws = new WebSocket(wsUrl)

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'new_booking') {
          this.bookings.push(data.booking)
        } else if (data.type === 'ride_accepted') {
          if (this.currentBooking && this.currentBooking.id === data.booking_id) {
            this.currentBooking.status = 'accepted'
            this.currentBooking.driver_id = data.driver_id
          }
        } else if (data.type === 'driver_location') {
          if (this.currentBooking && this.currentBooking.id === data.booking_id) {
            this.driverLocation = { lat: data.lat, lng: data.lng }
          }
        } else if (data.type === 'ride_cancelled') {
          if (this.currentBooking && this.currentBooking.id === data.booking_id) {
            this.currentBooking = null
            this.driverLocation = null
          }
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

    dismissBooking(bookingId) {
      this.bookings = this.bookings.filter(b => b.id !== bookingId)
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
        if (res.ok) {
          // Find booking and set as current
          const booking = this.bookings.find(b => b.id === bookingId)
          if (booking) {
            booking.status = 'accepted'
            booking.driver_id = auth.user.id
            this.currentBooking = booking
          }
          return true
        }
      } catch (err) {
        console.error("Failed to accept booking:", err)
      }
      return false
    }
  }
})
