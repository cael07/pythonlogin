from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
import json
from typing import Dict, List, Optional
from ..database import get_db
from ..auth.models import Booking, User
from pydantic import BaseModel

router = APIRouter(prefix="/ride", tags=["Ride"])

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        # Maps user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

class BookingCreate(BaseModel):
    passenger_id: int
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float

@router.post("/bookings")
async def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    new_booking = Booking(
        passenger_id=booking.passenger_id,
        pickup_lat=booking.pickup_lat,
        pickup_lng=booking.pickup_lng,
        dropoff_lat=booking.dropoff_lat,
        dropoff_lng=booking.dropoff_lng,
        status="pending"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    # Broadcast to all drivers that a new booking is available
    await manager.broadcast(json.dumps({
        "type": "new_booking",
        "booking": {
            "id": new_booking.id,
            "passenger_id": new_booking.passenger_id,
            "pickup_lat": new_booking.pickup_lat,
            "pickup_lng": new_booking.pickup_lng,
            "dropoff_lat": new_booking.dropoff_lat,
            "dropoff_lng": new_booking.dropoff_lng,
            "status": new_booking.status
        }
    }))
    
    return {"message": "Booking created successfully", "booking_id": new_booking.id}

@router.get("/bookings")
async def get_bookings(db: Session = Depends(get_db)):
    bookings = db.query(Booking).filter(Booking.status == "pending").all()
    return bookings

class AcceptBooking(BaseModel):
    driver_id: int

@router.post("/bookings/{booking_id}/accept")
async def accept_booking(booking_id: int, request: AcceptBooking, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.driver_id = request.driver_id
    booking.status = "accepted"
    db.commit()
    
    # Notify passenger that ride was accepted
    await manager.send_personal_message(json.dumps({
        "type": "ride_accepted",
        "booking_id": booking.id,
        "driver_id": request.driver_id
    }), booking.passenger_id)
    
    return {"message": "Booking accepted"}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "location_update":
                # Driver is updating their location
                booking_id = message.get("booking_id")
                passenger_id = message.get("passenger_id")
                lat = message.get("lat")
                lng = message.get("lng")
                
                # Send to the specific passenger
                await manager.send_personal_message(json.dumps({
                    "type": "driver_location",
                    "lat": lat,
                    "lng": lng,
                    "booking_id": booking_id
                }), passenger_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
