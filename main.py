import os
import shutil
from fastapi import FastAPI, Depends, Form, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Column, Integer, String, func
from typing import List, Dict
import json
from fastapi import WebSocket, Depends
from sqlalchemy.orm import Session
# from database import get_db

# ==========================================
# 1. INITIALIZE APP & FOLDERS
# ==========================================
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="2DA Tricycle Ride-Hailing API")

# ==========================================
# 2. DATABASE SETUP
# ==========================================
DATABASE_URL = "sqlite:///./2da.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 3. DATABASE MODELS
# ==========================================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)  # 'passenger' or 'driver'
    
    # Shared Fields
    full_name = Column(String)
    address = Column(String)
    whatsapp_number = Column(String)
    
    # Driver-Only Fields
    toda_number = Column(String, nullable=True)
    gcash_account = Column(String, nullable=True)
    toda_id_path = Column(String, nullable=True)

class RideRequest(Base):
    __tablename__ = "ride_requests"
    id = Column(Integer, primary_key=True, index=True)
    passenger_name = Column(String, index=True)
    pickup_location = Column(String)
    dropoff_location = Column(String)
    service_type = Column(String, nullable=True) 
    fare = Column(String, nullable=True)         
    status = Column(String, default="pending")
    driver_name = Column(String, nullable=True)

# Initialize Database
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 4. PYDANTIC SCHEMAS
# ==========================================
class LoginRequest(BaseModel):
    username: str
    password: str
    role: str = None

class RideRequestCreate(BaseModel):
    passenger_name: str
    pickup_location: str
    dropoff_location: str
    service_type: str = "PASSENGER"
    fare: str = "₱0.00"

class AcceptRideSchema(BaseModel):
    driver_name: str
    
# ==========================================
# ADMIN SYSTEM CONFIGURATION
# ==========================================
class SystemConfig(Base):
    __tablename__ = "system_config"
    id = Column(Integer, primary_key=True, index=True)
    pasundo_price = Column(Integer, default=50)
    pabili_price = Column(Integer, default=50)
    deliver_price = Column(Integer, default=50)
    platform_share = Column(Integer, default=17)
    katoda_share = Column(Integer, default=3)

# Force create the new table if it doesn't exist yet
SystemConfig.__table__.create(bind=engine, checkfirst=True)

@app.on_event("startup")
def initialize_config():
    db = SessionLocal()
    config = db.query(SystemConfig).first()
    if not config:
        new_config = SystemConfig()
        db.add(new_config)
        db.commit()
    db.close()

class ConfigUpdateSchema(BaseModel):
    pasundo_price: int
    pabili_price: int
    deliver_price: int
    platform_share: int
    katoda_share: int

@app.get("/api/admin/config")
def get_system_config(db: Session = Depends(get_db)):
    return db.query(SystemConfig).first()

@app.post("/api/admin/config")
def update_system_config(data: ConfigUpdateSchema, db: Session = Depends(get_db)):
    config = db.query(SystemConfig).first()
    if not config:
        config = SystemConfig()
        db.add(config)
        
    config.pasundo_price = data.pasundo_price
    config.pabili_price = data.pabili_price
    config.deliver_price = data.deliver_price
    config.platform_share = data.platform_share
    config.katoda_share = data.katoda_share
    db.commit()
    return {"status": "success", "message": "System configuration updated."}
    
# ==========================================
# 5. API ENDPOINTS
# ==========================================
@app.get("/")
def read_root():
    # FIXED: Removed /web
    return RedirectResponse(url="/booking.html")

@app.post("/api/login")
async def admin_login(request: LoginRequest):
    if request.username == "masterom" and request.password == "qZ82118@@":
        response = JSONResponse(content={
            "status": "success", 
            "redirect": "admin_dashboard.html"
        })
        response.set_cookie(key="admin_session", value="masterom_active")
        return response
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if username == "masterom" and password == "qZ82118@@":
        # FIXED: Removed /web
        response = RedirectResponse(url="/admin_dashboard.html", status_code=303)
        response.set_cookie(key="admin_session", value="masterom_active", httponly=False)
        return response

    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    # FIXED: Removed /web
    response = RedirectResponse(
        url="/driver_dashboard.html" if user.role == "driver" else "/booking.html", 
        status_code=303
    )
    
    display_name = user.full_name if user.full_name else user.username
    response.set_cookie(key="passenger_name", value=display_name)
    if user.role == "driver":
        response.set_cookie(key="driver_name", value=display_name)
        
    return response

@app.post("/register-account/")
def register_account(
    role: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    address: str = Form(...),
    whatsapp_number: str = Form(...),
    toda_number: str = Form(None),
    gcash_account: str = Form(None),
    toda_id: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    file_path = None
    if role == "driver" and toda_id:
        file_path = f"uploads/{username}_{toda_id.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(toda_id.file, buffer)

    new_user = User(
        username=username, 
        password=password, 
        role=role, 
        full_name=full_name,
        address=address,
        whatsapp_number=whatsapp_number,
        toda_number=toda_number,
        gcash_account=gcash_account,
        toda_id_path=file_path
    )
    db.add(new_user)
    db.commit()
    
    # FIXED: Removed /web
    return RedirectResponse(url="/login.html", status_code=303)

@app.post("/request-ride/")
def create_ride_request(request: RideRequestCreate, db: Session = Depends(get_db)):
    new_ride = RideRequest(
        passenger_name=request.passenger_name,
        pickup_location=request.pickup_location,
        dropoff_location=request.dropoff_location,
        service_type=request.service_type,
        fare=request.fare,
        status="pending"
    )
    db.add(new_ride)
    db.commit()
    db.refresh(new_ride)
    return {"message": "Ride requested successfully", "id": new_ride.id}

@app.post("/accept-ride/{ride_id}")
def accept_ride(ride_id: int, request: AcceptRideSchema, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    ride.status = "accepted"
    ride.driver_name = request.driver_name
    db.commit()
    db.refresh(ride)
    return {"message": "Ride accepted successfully!", "ride_id": ride.id}

@app.post("/complete-ride/{ride_id}")
def complete_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    ride.status = "completed"
    db.commit()
    return {"message": "Ride completed successfully", "id": ride.id}

@app.post("/pay-ride/{ride_id}")
def pay_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    ride.status = "paid"
    db.commit()
    return {"message": "Payment confirmed", "id": ride.id}

@app.get('/api/katoda/drivers')
def get_katoda_drivers(db: Session = Depends(get_db)):
    all_drivers = db.query(User).filter(User.role == 'driver').all()
    
    driver_list = []
    for driver in all_drivers:
        name = driver.full_name if driver.full_name else driver.username
        clean_name = name.strip().replace('"', '').replace("'", "")
        
        ride_count = db.query(RideRequest).filter(
            RideRequest.driver_name.ilike(f"%{clean_name}%"),
            RideRequest.status.in_(['completed', 'paid'])
        ).count()
        
        driver_list.append({
            "id": driver.id,
            "name": clean_name,
            "status": "online",
            "rating": 5.0,
            "totalRides": ride_count 
        })
        
    return driver_list

@app.get("/ride-status/{ride_id}")
def check_ride_status(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return {"status": ride.status, "driver_name": ride.driver_name}

@app.get("/pending-rides/")
def get_pending_rides(db: Session = Depends(get_db)):
    return db.query(RideRequest).all()

@app.get("/api/rides")
def get_available_rides(db: Session = Depends(get_db)):
    return db.query(RideRequest).all()
 @app.get("/api/chat/{ride_id}")
def get_chat_history(ride_id: int, db: Session = Depends(get_db)):
    # Fetch all messages for this ride, ordered from oldest to newest
    messages = db.query(ChatMessage).filter(ChatMessage.ride_id == ride_id).order_by(ChatMessage.timestamp.asc()).all()
    
    # Return them as a list of dictionaries
    return [{"sender": msg.sender, "text": msg.text} for msg in messages]   

# ==========================================
# 6. IN-APP TEXT CHAT (WEBSOCKETS)
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, ride_id: str):
        await websocket.accept()
        if ride_id not in self.active_connections:
            self.active_connections[ride_id] = []
        self.active_connections[ride_id].append(websocket)

    def disconnect(self, websocket: WebSocket, ride_id: str):
        if ride_id in self.active_connections:
            self.active_connections[ride_id].remove(websocket)
            if len(self.active_connections[ride_id]) == 0:
                del self.active_connections[ride_id]

    async def broadcast_to_ride(self, message: str, ride_id: str):
        if ride_id in self.active_connections:
            for connection in self.active_connections[ride_id]:
                await connection.send_text(message)

chat_manager = ConnectionManager()

@app.websocket("/ws/chat/{ride_id}")
async def websocket_chat_endpoint(websocket: WebSocket, ride_id: str):
    await chat_manager.connect(websocket, ride_id)
    try:
        while True:
            data = await websocket.receive_text()
            await chat_manager.broadcast_to_ride(data, ride_id)
            
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket, ride_id)
@app.websocket("/ws/chat/{ride_id}")
async def websocket_chat(websocket: WebSocket, ride_id: int, db: Session = Depends(get_db)):
    await manager.connect(websocket, ride_id)
    try:
        while True:
            # 1. Receive the message from the frontend
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 2. SAVE TO DATABASE BEFORE BROADCASTING
            new_message = ChatMessage(
                ride_id=ride_id,
                sender=message_data["sender"],
                text=message_data["text"]
            )
            db.add(new_message)
            db.commit()

            # 3. Broadcast it to the other person
            await manager.broadcast(data, ride_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, ride_id)     

# ==========================================
# KATODA Broadcast System Endpoints
# ==========================================
latest_broadcast = {"message": ""}

class BroadcastSchema(BaseModel):
    message: str

@app.post("/api/katoda/broadcast")
def send_broadcast(data: BroadcastSchema):
    global latest_broadcast
    latest_broadcast["message"] = data.message
    return {"status": "success", "message": "Broadcast sent to all drivers"}

@app.get("/api/driver/broadcast")
def get_driver_broadcast():
    return latest_broadcast

@app.get('/api/katoda/finances')
def get_katoda_finances(db: Session = Depends(get_db)):
    completed_rides = db.query(RideRequest).filter(
        RideRequest.status.in_(['completed', 'paid'])
    ).all()
    
    total_gross = 0.0
    for ride in completed_rides:
        if ride.fare:
            clean_fare = ride.fare.replace('₱', '').replace(',', '').strip()
            try:
                total_gross += float(clean_fare)
            except ValueError:
                pass
                
    katoda_share = total_gross * 0.03
    
    return {
        "today": katoda_share,
        "week": katoda_share,
        "month": katoda_share,
        "ytd": katoda_share
    }

# ==========================================
# 7. STATIC FILES MOUNT (MUST BE AT THE BOTTOM)
# ==========================================
# FIXED: Moved to the absolute bottom so it doesn't block your API routes!
app.mount("/", StaticFiles(directory="web", html=True), name="web")
