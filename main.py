import os
import shutil
import json
from datetime import datetime

from fastapi import FastAPI, Depends, Form, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Dict
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

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
    bank_name = Column(String, nullable=True, default="GCash")
    toda_id_path = Column(String, nullable=True)
    
    # Status & Timestamps
    status = Column(String, default="offline")
    last_online = Column(DateTime, nullable=True)
    last_offline = Column(DateTime, nullable=True)

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

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, index=True)
    sender = Column(String(50))
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Initialize Database
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 4. PYDANTIC SCHEMAS & CONFIG
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
    
class SystemConfig(Base):
    __tablename__ = "system_config"
    id = Column(Integer, primary_key=True, index=True)
    pasundo_price = Column(Integer, default=50)
    pabili_price = Column(Integer, default=50)
    deliver_price = Column(Integer, default=50)
    platform_share = Column(Integer, default=17)
    katoda_share = Column(Integer, default=3)
    katoda_bank = Column(String, default="GCash")
    katoda_account = Column(String, default="")  

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
    platform_share: float
    katoda_share: float
    katoda_bank: str = "GCash"
    katoda_account: str = ""  

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
    config.katoda_bank = data.katoda_bank
    config.katoda_account = data.katoda_account  
    db.commit()
    return {"status": "success", "message": "System configuration updated."}
    
# ==========================================
# 5. API ENDPOINTS
# ==========================================

@app.get("/")
def read_root():
    return RedirectResponse(url="/booking.html")

@app.post("/api/login")
async def admin_login(request: LoginRequest):
    if request.username == "masterom" and request.password == "qZ82118@@":
        response = JSONResponse(content={"status": "success", "redirect": "admin_dashboard.html"})
        response.set_cookie(key="admin_session", value="masterom_active")
        return response
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/login")
def login_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if username == "masterom" and password == "qZ82118@@":
        response = RedirectResponse(url="/admin_dashboard.html", status_code=303)
        response.set_cookie(key="admin_session", value="masterom_active", httponly=False)
        return response

    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    user.status = "online"
    user.last_online = datetime.now()
    db.commit()
    
    response = RedirectResponse(url="/driver_dashboard.html" if user.role == "driver" else "/booking.html", status_code=303)
    display_name = user.full_name if user.full_name else user.username
    response.set_cookie(key="passenger_name", value=display_name)
    if user.role == "driver":
        response.set_cookie(key="driver_name", value=display_name)
    return response

@app.post("/api/logout/{username}")
def logout_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user:
        user.status = "offline"
        user.last_offline = datetime.now()
        db.commit()
    return {"message": "Logged out"}

@app.post("/register-account/")
def register_account(
    role: str = Form(...), username: str = Form(...), password: str = Form(...),
    full_name: str = Form(...), address: str = Form(...), whatsapp_number: str = Form(...),
    toda_number: str = Form(None), gcash_account: str = Form(None), bank_name: str = Form("GCash"),
    toda_id: UploadFile = File(None), db: Session = Depends(get_db)
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
        username=username, password=password, role=role, full_name=full_name,
        address=address, whatsapp_number=whatsapp_number, toda_number=toda_number,
        gcash_account=gcash_account, bank_name=bank_name, toda_id_path=file_path
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login.html", status_code=303)

@app.post("/request-ride/")
def create_ride_request(request: RideRequestCreate, db: Session = Depends(get_db)):
    new_ride = RideRequest(
        passenger_name=request.passenger_name, pickup_location=request.pickup_location,
        dropoff_location=request.dropoff_location, service_type=request.service_type,
        fare=request.fare, status="pending"
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
        ride_count = db.query(RideRequest).filter(RideRequest.driver_name.ilike(f"%{clean_name}%"), RideRequest.status.in_(['completed', 'paid'])).count()
        
        display_id = driver.toda_number if driver.toda_number else driver.id
        gcash = driver.gcash_account if driver.gcash_account else "Not Provided"

        time_str = "--:--"
        if driver.status == 'online' and driver.last_online:
            time_str = driver.last_online.strftime("%I:%M %p")
        elif driver.status == 'offline' and driver.last_offline:
            time_str = driver.last_offline.strftime("%I:%M %p")

        driver_list.append({"id": display_id, "name": clean_name, "status": driver.status, "status_time": time_str, "gcash": gcash, "rating": 5.0, "totalRides": ride_count})
    return driver_list

@app.get("/api/admin/payout-summary")
def get_payout_summary(db: Session = Depends(get_db)):
    config = db.query(SystemConfig).first()
    platform_pct = (config.platform_share if config else 17) / 100
    katoda_pct = (config.katoda_share if config else 3) / 100
    driver_pct = 1.0 - (platform_pct + katoda_pct)

    unsettled_rides = db.query(RideRequest).filter(RideRequest.status == "paid").all()
    payouts = {}
    total_katoda = 0.0
    total_platform = 0.0

    for ride in unsettled_rides:
        if not ride.driver_name or not ride.fare: continue
            
        clean_fare = float(ride.fare.replace('₱', '').replace(',', '').strip())
        driver_name = ride.driver_name

        driver_cut = clean_fare * driver_pct
        katoda_cut = clean_fare * katoda_pct
        platform_cut = clean_fare * platform_pct

        total_katoda += katoda_cut
        total_platform += platform_cut

        if driver_name not in payouts:
            # FIX: Check BOTH username and full_name so it successfully matches!
            driver_user = db.query(User).filter(User.username == driver_name).first()
            if not driver_user:
                driver_user = db.query(User).filter(User.full_name == driver_name).first()

            if driver_user and driver_user.gcash_account:
                b_name = driver_user.bank_name if driver_user.bank_name else "GCash"
                acc_num = driver_user.gcash_account
            else:
                b_name = "--"
                acc_num = "Not Provided"
            
            payouts[driver_name] = {
                "driver_name": driver_name,
                "bank_name": b_name,            
                "account_number": acc_num,      
                "ride_count": 0,
                "total_gross": 0.0,
                "driver_share": 0.0,
                "katoda_share": 0.0,
                "platform_share": 0.0
            }

        payouts[driver_name]["ride_count"] += 1
        payouts[driver_name]["total_gross"] += clean_fare
        payouts[driver_name]["driver_share"] += driver_cut
        payouts[driver_name]["katoda_share"] += katoda_cut
        payouts[driver_name]["platform_share"] += platform_cut

    katoda_bank = config.katoda_bank if config and config.katoda_bank else "GCash"
    katoda_acct = config.katoda_account if config and config.katoda_account else "Not Configured"
    
    return {
        "drivers": list(payouts.values()),
        "total_katoda": total_katoda,
        "total_platform": total_platform,
        "katoda_bank": katoda_bank,
        "katoda_account": katoda_acct
    }   

@app.get("/api/admin/generate-bizlink-payout")
def generate_bizlink_payout(db: Session = Depends(get_db)):
    config = db.query(SystemConfig).first()
    platform_pct = (config.platform_share if config else 17) / 100
    katoda_pct = (config.katoda_share if config else 3) / 100
    driver_pct = 1.0 - (platform_pct + katoda_pct)

    unsettled_rides = db.query(RideRequest).filter(RideRequest.status == "paid").all()
    driver_payouts = {}
    total_katoda_payout = 0.0

    for ride in unsettled_rides:
        if not ride.driver_name or not ride.fare: continue
        clean_fare = float(ride.fare.replace('₱', '').replace(',', '').strip())
        driver_cut = clean_fare * driver_pct
        katoda_cut = clean_fare * katoda_pct
        
        if ride.driver_name in driver_payouts:
            driver_payouts[ride.driver_name] += driver_cut
        else:
            driver_payouts[ride.driver_name] = driver_cut
        total_katoda_payout += katoda_cut

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Destination Account Number", "Beneficiary Name", "Amount", "Remarks"])

    for driver_name, amount in driver_payouts.items():
        # FIX: Also added the fallback query to the BizLink CSV export!
        driver_user = db.query(User).filter(User.username == driver_name).first()
        if not driver_user:
            driver_user = db.query(User).filter(User.full_name == driver_name).first()

        account_number = driver_user.gcash_account if driver_user and driver_user.gcash_account else "MISSING_ACCOUNT"
        bank_provider = driver_user.bank_name if driver_user and driver_user.bank_name else "GCash"
        writer.writerow([account_number, driver_name, f"{amount:.2f}", f"2DA Payout ({bank_provider})"])

    if total_katoda_payout > 0:
        katoda_bank = config.katoda_bank if config and config.katoda_bank else "GCash"
        katoda_acct = config.katoda_account if config and config.katoda_account else "MISSING_KATODA_ACCOUNT"
        writer.writerow([katoda_acct, "KATODA Organization", f"{total_katoda_payout:.2f}", f"2DA Daily Katoda Share ({katoda_bank})"])
        
    output.seek(0)
    current_date = datetime.now().strftime("%Y-%m-%d")
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=BizLink_Payout_{current_date}.csv"})

@app.get("/pending-rides/")
def get_pending_rides(db: Session = Depends(get_db)):
    rides = db.query(RideRequest).all()
    return [{
        "id": r.id,
        "passenger_name": r.passenger_name,
        "pickup_location": r.pickup_location,
        "dropoff_location": r.dropoff_location,
        "service_type": r.service_type,
        "fare": r.fare,
        "status": r.status,
        "driver_name": r.driver_name
    } for r in rides]

@app.get("/api/rides")
def get_available_rides(db: Session = Depends(get_db)):
    rides = db.query(RideRequest).all()
    return [{
        "id": r.id,
        "passenger_name": r.passenger_name,
        "pickup_location": r.pickup_location,
        "dropoff_location": r.dropoff_location,
        "service_type": r.service_type,
        "fare": r.fare,
        "status": r.status,
        "driver_name": r.driver_name
    } for r in rides]

@app.get("/ride-status/{ride_id}")
def check_ride_status(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return {"status": ride.status, "driver_name": ride.driver_name}

# ==========================================
# 6. IN-APP TEXT CHAT & KATODA BROADCAST
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    async def connect(self, websocket: WebSocket, ride_id: str):
        await websocket.accept()
        if ride_id not in self.active_connections: self.active_connections[ride_id] = []
        self.active_connections[ride_id].append(websocket)
    def disconnect(self, websocket: WebSocket, ride_id: str):
        if ride_id in self.active_connections:
            if websocket in self.active_connections[ride_id]: self.active_connections[ride_id].remove(websocket)
            if len(self.active_connections[ride_id]) == 0: del self.active_connections[ride_id]
    async def broadcast_to_ride(self, message: str, ride_id: str):
        if ride_id in self.active_connections:
            for connection in self.active_connections[ride_id]: await connection.send_text(message)

chat_manager = ConnectionManager()

@app.get("/api/chat/{ride_id}")
def get_chat_history(ride_id: int, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.ride_id == ride_id).order_by(ChatMessage.timestamp.asc()).all()
    return [{"sender": msg.sender, "text": msg.text} for msg in messages]   

@app.websocket("/ws/chat/{ride_id}")
async def websocket_chat(websocket: WebSocket, ride_id: str, db: Session = Depends(get_db)):
    await chat_manager.connect(websocket, ride_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            new_message = ChatMessage(ride_id=int(ride_id), sender=message_data.get("sender", "Unknown"), text=message_data.get("text", ""))
            db.add(new_message)
            db.commit()
            await chat_manager.broadcast_to_ride(data, ride_id)
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket, ride_id)

latest_broadcast = {"message": ""}
class BroadcastSchema(BaseModel): message: str

@app.post("/api/katoda/broadcast")
def send_broadcast(data: BroadcastSchema):
    global latest_broadcast
    latest_broadcast["message"] = data.message
    return {"status": "success", "message": "Broadcast sent"}

@app.get("/api/driver/broadcast")
def get_driver_broadcast(): return latest_broadcast

@app.get('/api/katoda/finances')
def get_katoda_finances(db: Session = Depends(get_db)):
    completed_rides = db.query(RideRequest).filter(RideRequest.status.in_(['completed', 'paid'])).all()
    total_gross = 0.0
    for ride in completed_rides:
        if ride.fare:
            try: total_gross += float(ride.fare.replace('₱', '').replace(',', '').strip())
            except ValueError: pass
    katoda_share = total_gross * 0.03
    return {"today": katoda_share, "week": katoda_share, "month": katoda_share, "ytd": katoda_share}

# ==========================================
# 7. STATIC FILES MOUNT (MUST BE AT THE BOTTOM)
# ==========================================
app.mount("/", StaticFiles(directory="web", html=True), name="web")
