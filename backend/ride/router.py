from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
import sqlalchemy as sa
import json
from typing import Dict, List, Optional
from ..database import get_db
from ..auth.models import Booking, User
from ..auth.service import get_user_by_id
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

@router.get("/active/{user_id}")
async def get_active_booking(user_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(
        sa.or_(
            Booking.passenger_id == user_id,
            Booking.driver_id == user_id
        ),
        Booking.status.in_(["pending", "accepted", "arrived", "started"])
    ).order_by(Booking.id.desc()).first()
    
    if not booking:
        return None
        
    passenger = get_user_by_id(db, booking.passenger_id)
    driver = get_user_by_id(db, booking.driver_id) if booking.driver_id else None
    
    return {
        "id": booking.id,
        "passenger_id": booking.passenger_id,
        "passenger_name": passenger.full_name if passenger else "Passenger",
        "passenger_image": getattr(passenger, "face_image_base64", None),
        "driver_id": booking.driver_id,
        "driver_name": driver.full_name if driver else None,
        "driver_image": getattr(driver, "face_image_base64", None),
        "pickup_lat": booking.pickup_lat,
        "pickup_lng": booking.pickup_lng,
        "dropoff_lat": booking.dropoff_lat,
        "dropoff_lng": booking.dropoff_lng,
        "status": booking.status
    }

@router.post("/bookings")
async def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    # Check for existing active booking first
    active = db.query(Booking).filter(
        Booking.passenger_id == booking.passenger_id,
        Booking.status.in_(["pending", "accepted", "arrived", "started"])
    ).first()
    
    if active:
        return {"message": "Active booking exists", "booking_id": active.id, "already_exists": True}

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
    passenger = get_user_by_id(db, new_booking.passenger_id)
    await manager.broadcast(json.dumps({
        "type": "new_booking",
        "booking": {
            "id": new_booking.id,
            "passenger_id": new_booking.passenger_id,
            "passenger_name": passenger.full_name if passenger else "Passenger",
            "passenger_image": getattr(passenger, "face_image_base64", None),
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
    results = []
    for b in bookings:
        passenger = get_user_by_id(db, b.passenger_id)
        results.append({
            "id": b.id,
            "passenger_id": b.passenger_id,
            "passenger_name": passenger.full_name if passenger else "Passenger",
            "passenger_image": getattr(passenger, "face_image_base64", None),
            "pickup_lat": b.pickup_lat,
            "pickup_lng": b.pickup_lng,
            "dropoff_lat": b.dropoff_lat,
            "dropoff_lng": b.dropoff_lng,
            "status": b.status
        })
    return results

class AcceptBooking(BaseModel):
    driver_id: int

@router.post("/bookings/{booking_id}/accept")
async def accept_booking(booking_id: int, request: AcceptBooking, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status != "pending":
        raise HTTPException(status_code=400, detail=f"Ride is already {booking.status}")
    
    booking.driver_id = request.driver_id
    booking.status = "accepted"
    db.commit()
    
    driver = get_user_by_id(db, request.driver_id)
    
    # Notify passenger that ride was accepted
    accept_msg = json.dumps({
        "type": "ride_accepted",
        "booking_id": booking.id,
        "driver_id": request.driver_id,
        "driver_name": driver.full_name if driver else "Driver",
        "driver_image": getattr(driver, "face_image_base64", None)
    })
    await manager.send_personal_message(accept_msg, booking.passenger_id)
    
    # Notify all other drivers to remove this from their list
    await manager.broadcast(json.dumps({
        "type": "booking_taken",
        "booking_id": booking.id
    }))
    
    passenger = get_user_by_id(db, booking.passenger_id)
    return {
        "message": "Booking accepted",
        "booking": {
            "id": booking.id,
            "passenger_id": booking.passenger_id,
            "passenger_name": passenger.full_name if passenger else "Passenger",
            "passenger_image": getattr(passenger, "face_image_base64", None),
            "pickup_lat": booking.pickup_lat,
            "pickup_lng": booking.pickup_lng,
            "dropoff_lat": booking.dropoff_lat,
            "dropoff_lng": booking.dropoff_lng,
            "status": booking.status
        }
    }

@router.post("/bookings/{booking_id}/arrived")
async def notify_arrived(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = "arrived"
    db.commit()
    
    # Notify passenger
    msg = json.dumps({
        "type": "ride_arrived",
        "booking_id": booking.id
    })
    await manager.send_personal_message(msg, booking.passenger_id)
    
    # Notify driver too so their UI updates
    if booking.driver_id:
        await manager.send_personal_message(msg, booking.driver_id)
        
    return {"message": "Arrival notification sent to all parties"}

@router.post("/bookings/{booking_id}/start")
async def start_ride(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = "started"
    db.commit()
    
    # Notify parties
    msg = json.dumps({
        "type": "ride_started",
        "booking_id": booking.id
    })
    await manager.send_personal_message(msg, booking.passenger_id)
    
    # Notify driver
    if booking.driver_id:
        await manager.send_personal_message(msg, booking.driver_id)
        
    return {"message": "Ride started"}

@router.post("/bookings/{booking_id}/complete")
async def complete_ride(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = "completed"
    db.commit()
    
    # Notify parties
    msg = json.dumps({
        "type": "ride_completed",
        "booking_id": booking.id
    })
    await manager.send_personal_message(msg, booking.passenger_id)

    # Notify driver
    if booking.driver_id:
        await manager.send_personal_message(msg, booking.driver_id)
        
    return {"message": "Ride completed"}

@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = "cancelled"
    db.commit()
    
    # Notify everyone that this ride is cancelled
    cancel_msg = json.dumps({
        "type": "ride_cancelled",
        "booking_id": booking.id
    })
    
    # Broadcast to all connected users (drivers and passengers)
    # This ensures all drivers remove it from their "Incoming Requests" list
    await manager.broadcast(cancel_msg)
        
    return {"message": "Booking cancelled"}

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
