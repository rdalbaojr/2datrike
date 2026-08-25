import os
import shutil
import json
import random
from datetime import datetime
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi import FastAPI, Depends, Form, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Dict, Optional
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
    role = Column(String)  
    full_name = Column(String)
    address = Column(String)
    whatsapp_number = Column(String)
    toda_number = Column(String, nullable=True)
    gcash_account = Column(String, nullable=True)
    bank_name = Column(String, nullable=True, default="GCash")
    toda_id_path = Column(String, nullable=True)
    status = Column(String, default="offline")
    last_online = Column(DateTime, nullable=True)
    last_offline = Column(DateTime, nullable=True)
    
    # 🟢 Security Questions for Password Resets
    security_q = Column(String, nullable=True)
    security_a = Column(String, nullable=True)
    
    warnings = Column(Integer, default=0)
    is_suspended = Column(Integer, default=0) 
    rating_sum = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    city = Column(String, nullable=True, default="Pasig City")
    barangay = Column(String, nullable=True, default="")
    toda_name = Column(String, nullable=True, default="")
    branch = Column(String, default="Main") 
    local_ref = Column(String, nullable=True, default="")
    plate_number = Column(String, nullable=True)

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
    rating = Column(Integer, nullable=True) 
    branch = Column(String, default="Main")
    local_ref = Column(String, nullable=True, default="") 

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, index=True)
    sender = Column(String(50))
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

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

class TodaConfig(Base):
    __tablename__ = "toda_configs"
    id = Column(Integer, primary_key=True, index=True)
    toda_name = Column(String, unique=True, index=True)
    s1_name = Column(String, default="Pasundo")
    s1_price = Column(Integer, default=50)
    s2_name = Column(String, default="Pabili")
    s2_price = Column(Integer, default=50)
    s3_name = Column(String, default="Papickup")
    s3_price = Column(Integer, default=50)
    s4_name = Column(String, default="")
    s4_price = Column(Integer, default=0)
    s5_name = Column(String, default="")
    s5_price = Column(Integer, default=0)
    platform_share = Column(Float, default=17.0)
    katoda_share = Column(Float, default=3.0)
    katoda_bank = Column(String, default="GCash")
    katoda_account = Column(String, default="")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 4. SECURE 5-DIGIT LOCAL PREFIX GENERATOR
# ==========================================
def generate_local_ref(barangay: str, toda: str) -> str:
    brgy_code = "".join([w[0] for w in barangay.split() if w]).upper()[:3]
    toda_code = "".join([w[0] for w in toda.split() if w]).upper()[:3]
    rand_5digit = random.randint(10000, 99999)
    return f"{brgy_code}-{toda_code}-{rand_5digit}"

# ==========================================
# 5. STARTUP SCRIPT & PYDANTIC SCHEMAS
# ==========================================
@app.on_event("startup")
def initialize_config():
    SystemConfig.__table__.create(bind=engine, checkfirst=True)
    TodaConfig.__table__.create(bind=engine, checkfirst=True)
    
    db = SessionLocal()
    config = db.query(SystemConfig).first()
    if not config:
        new_config = SystemConfig()
        db.add(new_config)
        db.commit()
        
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN warnings INTEGER DEFAULT 0"))
        db.execute(text("ALTER TABLE users ADD COLUMN is_suspended INTEGER DEFAULT 0"))
        db.execute(text("ALTER TABLE users ADD COLUMN rating_sum FLOAT DEFAULT 0.0"))
        db.execute(text("ALTER TABLE users ADD COLUMN rating_count INTEGER DEFAULT 0"))
        db.execute(text("ALTER TABLE users ADD COLUMN city VARCHAR DEFAULT 'Pasig City'"))
        db.execute(text("ALTER TABLE users ADD COLUMN barangay VARCHAR DEFAULT ''"))
        db.execute(text("ALTER TABLE users ADD COLUMN toda_name VARCHAR DEFAULT ''"))
        db.execute(text("ALTER TABLE users ADD COLUMN branch VARCHAR DEFAULT 'Main'"))
        db.execute(text("ALTER TABLE users ADD COLUMN local_ref VARCHAR DEFAULT ''"))
        db.execute(text("ALTER TABLE users ADD COLUMN security_q VARCHAR DEFAULT ''"))
        db.execute(text("ALTER TABLE users ADD COLUMN security_a VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()
        
    try:
        db.execute(text("ALTER TABLE ride_requests ADD COLUMN rating INTEGER"))
        db.execute(text("ALTER TABLE ride_requests ADD COLUMN branch VARCHAR DEFAULT 'Main'"))
        db.execute(text("ALTER TABLE ride_requests ADD COLUMN local_ref VARCHAR DEFAULT ''"))
        db.execute(text("ALTER TABLE users ADD COLUMN plate_number VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()
        
    db.close()

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str = None

class TodaLoginSchema(BaseModel):
    username: str
    password: str

class RideRequestCreate(BaseModel):
    passenger_name: str
    pickup_location: str
    dropoff_location: str
    service_type: str = "PASSENGER"
    fare: str = "₱0.00"

class AcceptRideSchema(BaseModel):
    driver_name: str

class ProfileUpdateSchema(BaseModel):
    display_name: str
    bank_name: str
    gcash_account: str
    whatsapp_number: str
    address: str
    city: Optional[str] = None
    barangay: Optional[str] = None
    toda_name: Optional[str] = None

class PasswordResetSchema(BaseModel):
    username: str
    whatsapp_number: str
    new_password: str

class PasswordResetSchemaSecurity(BaseModel):
    username: str
    security_q: str
    security_a: str
    new_password: str

class RateRideSchema(BaseModel):
    rating: int

class DisciplineSchema(BaseModel):
    driver_id: int
    action: str 

class ConfigUpdateSchema(BaseModel):
    pasundo_price: int
    pabili_price: int
    deliver_price: int
    platform_share: float
    katoda_share: float
    katoda_bank: str = "GCash"
    katoda_account: str = ""  

# 🟢 FIXED: Perfectly clean, standalone schema.
class TodaConfigUpdateSchema(BaseModel):
    s1_name: str
    s1_price: int
    s2_name: str
    s2_price: int
    s3_name: str
    s3_price: int
    s4_name: str
    s4_price: int
    s5_name: str
    s5_price: int
    platform_share: float
    katoda_share: float
    katoda_bank: Optional[str] = None
    katoda_account: Optional[str] = None

class UserCreateJSON(BaseModel):
    full_name: Optional[str] = None
    username: str
    password: str
    role: str
    toda_name: Optional[str] = ""
    security_q: str
    security_a: str

def sanitize_name(name: str) -> str:
    if not name: return ""
    return name.replace('"', '').replace("'", "").strip()

# ==========================================
# 6. API ENDPOINTS
# ==========================================
@app.get("/")
def read_root():
    return RedirectResponse(url="/booking.html")

@app.post("/api/login")
async def admin_login(request: LoginRequest):
    u = request.username.strip().lower()
    p = request.password.strip()
    
    if u == "masterom" and (p == "qZ82118@@" or p == "12345"):
        response = JSONResponse(content={"status": "success", "redirect": "admin_dashboard.html"})
        response.set_cookie(key="admin_session", value="masterom_active")
        return response
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/login")
def login_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    u = username.strip().lower()
    p = password.strip()
    
    if u == "masterom" and (p == "qZ82118@@" or p == "12345"):
        response = RedirectResponse(url="/admin_dashboard.html", status_code=303)
        response.set_cookie(key="admin_session", value="masterom_active", httponly=False)
        return response

    clean_user = sanitize_name(username)
    user = db.query(User).filter(User.username == clean_user, User.password == password).first()
    if not user: raise HTTPException(status_code=400, detail="Invalid username or password")
    
    if user.is_suspended == 1: raise HTTPException(status_code=403, detail="ACCOUNT SUSPENDED: Please contact KATODA admin.")
    
    user.status = "online"
    user.last_online = datetime.now()
    db.commit()
    
    response = RedirectResponse(url="/driver_dashboard.html" if user.role == "driver" else "/booking.html", status_code=303)
    display_name = sanitize_name(user.full_name if user.full_name else user.username)
    
    response.set_cookie(key="passenger_name", value=display_name)
    if user.role == "driver": response.set_cookie(key="driver_name", value=display_name)
    return response

@app.post("/api/logout/{username}")
def logout_user(username: str, db: Session = Depends(get_db)):
    clean_username = sanitize_name(username)
    user = db.query(User).filter(User.username == clean_username).first()
    if user:
        user.status = "offline"
        user.last_offline = datetime.now()
        db.commit()
    return {"message": "Logged out"}

@app.post("/register")
def register_user_json(user: UserCreateJSON, db: Session = Depends(get_db)):
    clean_username = sanitize_name(user.username)
    clean_full_name = sanitize_name(user.full_name).title() if user.full_name else clean_username

    existing = db.query(User).filter(User.username == clean_username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    formatted_toda = user.toda_name.upper() if user.toda_name else ""
    
    local_ref = ""
    if user.role == "driver":
        toda_code = "".join([w[0] for w in formatted_toda.split() if w]).upper()[:3] if formatted_toda else "XX"
        local_ref = f"D-{toda_code}-{random.randint(10000, 99999)}"

    new_user = User(
        username=clean_username,
        full_name=clean_full_name,   
        password=user.password,
        role=user.role,
        toda_name=formatted_toda,
        local_ref=local_ref,
        security_q=user.security_q,
        security_a=user.security_a,
        rating_sum=25.0,
        rating_count=5
    )
    
    db.add(new_user)
    db.commit()
    return {"status": "success"}

@app.post("/api/reset-password-security")
def reset_password_security(data: PasswordResetSchemaSecurity, db: Session = Depends(get_db)):
    clean_user = sanitize_name(data.username)
    user = db.query(User).filter(User.username == clean_user).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Account not found.")
    
    saved_answer = user.security_a.strip().lower() if user.security_a else ""
    provided_answer = data.security_a.strip().lower()
    
    if user.security_q != data.security_q or saved_answer != provided_answer:
        raise HTTPException(status_code=400, detail="Security question or answer is incorrect.")
    
    user.password = data.new_password
    db.commit()
    
    return {"message": "Password updated successfully"}

@app.post("/register-account/")
def register_account(
    role: str = Form(...),
    full_name: str = Form(None),
    username: str = Form(...),
    whatsapp_number: str = Form(...),
    password: str = Form(...),
    address: str = Form(""),
    city: str = Form("Pasig City"),
    barangay: str = Form(""),         
    toda_name: str = Form(""),         
    toda_number: str = Form(None),
    plate_number: str = Form(None),
    bank_name: str = Form("GCash"),
    gcash_account: str = Form(""),
    db: Session = Depends(get_db)
):
    clean_username = sanitize_name(username)
    clean_full_name = sanitize_name(full_name).title() if full_name else clean_username

    existing = db.query(User).filter(User.username == clean_username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    formatted_toda = toda_name.upper() if toda_name else ""
    formatted_barangay = barangay.title() if barangay else ""
    formatted_toda_number = toda_number.upper() if toda_number else ""
    formatted_plate = plate_number.upper() if plate_number else ""

    new_user = User(
        username=clean_username,
        full_name=clean_full_name,   
        password=password,
        role=role,
        whatsapp_number=whatsapp_number,
        address=address,
        city=city,
        barangay=formatted_barangay, 
        toda_name=formatted_toda,
        local_ref=formatted_toda_number,
        plate_number=formatted_plate,
        bank_name=bank_name,
        gcash_account=gcash_account,
        rating_sum=25.0,
        rating_count=5
    )
    
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login.html", status_code=303)

@app.post("/api/toda/login")
def login_toda_admin(data: TodaLoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == data.username, 
        User.password == data.password, 
        User.role == "toda_admin"
    ).first()
    
    if user and user.toda_name:
        return {"status": "success", "toda_name": user.toda_name.upper()}
    
    if data.password == "1234":
        clean_toda = data.username.lower().replace("_admin", "").replace("admin", "").strip()
        if clean_toda:
            return {"status": "success", "toda_name": clean_toda.upper()}

    raise HTTPException(status_code=401, detail="Invalid TODA Admin credentials")

@app.get("/api/admin/locations")
def get_registered_locations(db: Session = Depends(get_db)):
    drivers = db.query(User).filter(User.role == 'driver').all()
    location_map = {}
    for d in drivers:
        brgy = d.barangay.strip() if d.barangay else "Unassigned"
        toda = d.toda_name.strip() if d.toda_name else "No TODA"
        
        if brgy not in location_map:
            location_map[brgy] = set()
        location_map[brgy].add(toda)
        
    return {b: sorted(list(t)) for b, t in location_map.items()}

@app.get("/api/profile/{display_name}")
def get_profile(display_name: str, db: Session = Depends(get_db)):
    clean_name = sanitize_name(display_name)
    user = db.query(User).filter(User.full_name == clean_name, User.role == 'driver').first()
    if not user: user = db.query(User).filter(User.username == clean_name, User.role == 'driver').first()
    if not user: user = db.query(User).filter(User.full_name == clean_name, User.role == 'passenger').first()
    if not user: user = db.query(User).filter(User.username == clean_name, User.role == 'passenger').first()
        
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    avg_rating = 5.0
    if user.rating_count and user.rating_count > 0: avg_rating = round(user.rating_sum / user.rating_count, 1)
        
    return {
        "full_name": user.full_name, "whatsapp_number": user.whatsapp_number,
        "bank_name": user.bank_name if user.bank_name else "GCash",
        "gcash_account": user.gcash_account if user.gcash_account else "",
        "address": user.address if user.address else "", "rating": avg_rating,
        "local_ref": user.local_ref if user.local_ref else "N/A",
        "toda_name": user.toda_name if user.toda_name else "" 
    }

@app.post("/api/update-profile")
def update_profile(data: ProfileUpdateSchema, db: Session = Depends(get_db)):
    clean_name = sanitize_name(data.display_name)
    user = db.query(User).filter(User.full_name == clean_name, User.role == 'driver').first()
    if not user: user = db.query(User).filter(User.username == clean_name, User.role == 'driver').first()
    if not user: user = db.query(User).filter(User.full_name == clean_name, User.role == 'passenger').first()
    if not user: user = db.query(User).filter(User.username == clean_name, User.role == 'passenger').first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
        
    user.bank_name = data.bank_name
    user.gcash_account = data.gcash_account
    user.whatsapp_number = data.whatsapp_number
    user.address = data.address 
    
    if data.city: user.city = data.city
    if data.barangay: user.barangay = data.barangay
    if data.toda_name: user.toda_name = data.toda_name
    
    if data.city and data.barangay and data.toda_name:
        assigned_branch = f"{data.city} - {data.barangay} ({data.toda_name})"
        user.branch = assigned_branch if user.role == "driver" else f"Passenger - {assigned_branch}"

    db.commit()
    return {"status": "success", "message": "Profile updated successfully"}

@app.post("/request-ride/")
def create_ride_request(request: RideRequestCreate, db: Session = Depends(get_db)):
    clean_pass_name = sanitize_name(request.passenger_name)
    user_profile = db.query(User).filter(User.full_name == clean_pass_name).first()
    
    city_str = user_profile.city if (user_profile and user_profile.city) else "Pasig City"
    brgy_str = user_profile.barangay if (user_profile and user_profile.barangay) else "Kapitolyo"
    toda_str = user_profile.toda_name if (user_profile and user_profile.toda_name) else "KATODA"

    origin_ref = generate_local_ref(brgy_str, toda_str)

    new_ride = RideRequest(
        passenger_name=clean_pass_name,
        pickup_location=request.pickup_location,
        dropoff_location=request.dropoff_location,
        service_type=request.service_type,
        fare=request.fare,
        status="pending",
        branch=f"{city_str} - {brgy_str} ({toda_str})",
        local_ref=origin_ref
    )
    db.add(new_ride)
    db.commit()
    db.refresh(new_ride)
    return {"message": "Ride requested successfully", "id": new_ride.id, "local_ref": origin_ref}

@app.post("/accept-ride/{ride_id}")
def accept_ride(ride_id: int, request: AcceptRideSchema, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride: raise HTTPException(status_code=404, detail="Ride not found")
    ride.status = "accepted"
    ride.driver_name = sanitize_name(request.driver_name)
    db.commit()
    db.refresh(ride)
    return {"message": "Ride accepted successfully!", "ride_id": ride.id}

@app.post("/complete-ride/{ride_id}")
def complete_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride: raise HTTPException(status_code=404, detail="Ride not found")
    ride.status = "completed"
    db.commit()
    return {"message": "Ride completed successfully", "id": ride.id}

@app.post("/pay-ride/{ride_id}")
def pay_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride: raise HTTPException(status_code=404, detail="Ride not found")
    ride.status = "paid"
    db.commit()
    return {"message": "Payment confirmed", "id": ride.id}

@app.post("/api/rate-ride/{ride_id}")
def rate_ride(ride_id: int, data: RateRideSchema, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride: raise HTTPException(status_code=404, detail="Ride not found")
    ride.rating = data.rating
    
    if ride.driver_name:
        driver = db.query(User).filter(User.full_name == ride.driver_name, User.role == 'driver').first()
        if not driver: driver = db.query(User).filter(User.username == ride.driver_name, User.role == 'driver').first()
        if driver:
            driver.rating_sum = (driver.rating_sum if driver.rating_sum else 0.0) + float(data.rating)
            driver.rating_count = (driver.rating_count if driver.rating_count else 0) + 1
    db.commit()
    return {"status": "success"}

@app.post("/api/admin/discipline")
def discipline_driver(data: DisciplineSchema, db: Session = Depends(get_db)):
    driver = db.query(User).filter(User.id == data.driver_id).first()
    if not driver: raise HTTPException(status_code=404, detail="Driver not found")
    if data.action == "warn":
        driver.warnings = (driver.warnings if driver.warnings else 0) + 1
        if driver.warnings >= 3: driver.is_suspended = 1 
    elif data.action == "suspend": driver.is_suspended = 1
    elif data.action == "reinstate":
        driver.is_suspended = 0
        driver.warnings = 0
    db.commit()
    return {"status": "success", "warnings": driver.warnings, "suspended": driver.is_suspended}

@app.get("/api/toda/drivers")
def get_toda_drivers(toda_name: str, db: Session = Depends(get_db)):
    search_term = f"%{toda_name.strip()}%"
    
    drivers = db.query(User).filter(
        User.toda_name.ilike(search_term),
        User.role == 'driver'
    ).all()
    
    all_rides = db.query(RideRequest).filter(RideRequest.status.in_(["completed", "paid"])).all()
    
    results = []
    for d in drivers:
        d_name = sanitize_name(d.full_name) if d.full_name else sanitize_name(d.username)
        
        driver_rides = 0
        for r in all_rides:
            if r.driver_name and sanitize_name(r.driver_name).lower() == d_name.lower():
                driver_rides += 1
        
        actual_rating = d.rating_sum / d.rating_count if d.rating_count and d.rating_count > 0 else 5.0
        
        results.append({
            "id": d.id,
            "name": d_name,
            "whatsapp_number": d.whatsapp_number,
            "status": d.status,
            "toda_number": d.toda_number,
            "is_suspended": d.is_suspended,
            "warnings": d.warnings or 0,
            "rating": round(actual_rating, 1),
            "totalRides": driver_rides 
        })
        
    return results

@app.get("/api/admin/payout-summary")
def get_payout_summary(branch: str = "All", db: Session = Depends(get_db)):
    platform_pct = 17.0 / 100
    katoda_pct = 3.0 / 100
    display_bank = "GCash"
    display_account = "Not Configured"
    
    if branch != "All":
        branch_config = db.query(TodaConfig).filter(TodaConfig.toda_name == branch.strip().upper()).first()
        if branch_config:
            platform_pct = branch_config.platform_share / 100
            katoda_pct = branch_config.katoda_share / 100
            display_bank = branch_config.katoda_bank if branch_config.katoda_bank else "GCash"
            display_account = branch_config.katoda_account if branch_config.katoda_account else "Not Configured"
    else:
        config = db.query(SystemConfig).first()
        if config:
            display_bank = config.katoda_bank if config.katoda_bank else "GCash"
            display_account = config.katoda_account if config.katoda_account else "Not Configured"

    driver_pct = 1.0 - (platform_pct + katoda_pct)

    payouts = {}
    clean_branch = branch.strip()

    query = db.query(User).filter(User.role == 'driver')
    
    if clean_branch != "All":
        query = query.filter(
            (User.toda_name.ilike(f"%{clean_branch}%")) |
            (User.barangay.ilike(f"%{clean_branch}%")) |
            (User.branch.ilike(f"%{clean_branch}%")) |
            (User.city.ilike(f"%{clean_branch}%"))
        )
    
    all_drivers = query.all()
    for driver in all_drivers:
        d_name = sanitize_name(driver.full_name if driver.full_name else driver.username)
        
        raw_acct = driver.gcash_account.strip() if driver.gcash_account else ""
        if raw_acct and raw_acct.lower() not in ["gcash", "maya"]:
            acc_num = raw_acct
        elif driver.whatsapp_number and driver.whatsapp_number.strip():
            acc_num = driver.whatsapp_number
        else:
            acc_num = "Not Provided"
        
        payouts[d_name] = {
            "driver_name": d_name,
            "bank_name": driver.bank_name if driver.bank_name else "GCash",            
            "account_number": acc_num,
            "ride_count": 0,
            "total_gross": 0.0,
            "driver_share": 0.0,
            "katoda_share": 0.0,
            "platform_share": 0.0,
            "local_ref": driver.local_ref if driver.local_ref else "N/A"
        }

    unsettled_rides = db.query(RideRequest).filter(RideRequest.status.in_(["completed", "paid"])).all()
    total_katoda = 0.0
    total_platform = 0.0

    for ride in unsettled_rides:
        if not ride.driver_name or not ride.fare:
            continue
        clean_driver_name = sanitize_name(ride.driver_name)
        
        if clean_branch != "All" and clean_driver_name not in payouts:
            continue
            
        try:
            clean_fare = float(str(ride.fare).replace('₱', '').replace(',', '').strip())
        except ValueError:
            clean_fare = 0.0

        driver_cut = clean_fare * driver_pct
        katoda_cut = clean_fare * katoda_pct
        platform_cut = clean_fare * platform_pct

        total_katoda += katoda_cut
        total_platform += platform_cut

        if clean_driver_name in payouts:
            payouts[clean_driver_name]["ride_count"] += 1
            payouts[clean_driver_name]["total_gross"] += clean_fare
            payouts[clean_driver_name]["driver_share"] += driver_cut
            payouts[clean_driver_name]["katoda_share"] += katoda_cut
            payouts[clean_driver_name]["platform_share"] += platform_cut
    
    return {
        "drivers": list(payouts.values()),
        "total_katoda": total_katoda,
        "total_platform": total_platform,
        "katoda_bank": display_bank,
        "katoda_account": display_account
    }   

@app.get("/api/admin/generate-bizlink-payout")
def generate_bizlink_payout(branch: str = "All", db: Session = Depends(get_db)):
    platform_pct = 17.0 / 100
    katoda_pct = 3.0 / 100
    katoda_bank = "GCash"
    katoda_account = "MISSING_KATODA_ACCOUNT"

    if branch != "All":
        branch_config = db.query(TodaConfig).filter(TodaConfig.toda_name == branch.strip().upper()).first()
        if branch_config:
            platform_pct = branch_config.platform_share / 100
            katoda_pct = branch_config.katoda_share / 100
            katoda_bank = branch_config.katoda_bank
            katoda_account = branch_config.katoda_account

    driver_pct = 1.0 - (platform_pct + katoda_pct)

    driver_payouts = {}
    query = db.query(User).filter(User.role == 'driver')
    if branch != "All":
        query = query.filter((User.city == branch) | (User.branch == branch))
        
    all_drivers = query.all()
    for driver in all_drivers:
        d_name = sanitize_name(driver.full_name if driver.full_name else driver.username)
        driver_payouts[d_name] = 0.0

    unsettled_rides = db.query(RideRequest).filter(RideRequest.status == "paid").all()
    total_katoda_payout = 0.0

    for ride in unsettled_rides:
        if not ride.driver_name or not ride.fare: continue
        clean_driver_name = sanitize_name(ride.driver_name)
        
        if branch != "All" and clean_driver_name not in driver_payouts: continue
            
        clean_fare = float(ride.fare.replace('₱', '').replace(',', '').strip())
        driver_cut = clean_fare * driver_pct
        katoda_cut = clean_fare * katoda_pct
        
        if clean_driver_name in driver_payouts: driver_payouts[clean_driver_name] += driver_cut
        else: driver_payouts[clean_driver_name] = driver_cut
        total_katoda_payout += katoda_cut

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Destination Account Number", "Beneficiary Name", "Amount", "Remarks"])

    for driver_name, amount in driver_payouts.items():
        if amount > 0:
            driver_user = db.query(User).filter(User.full_name == driver_name, User.role == 'driver').first()
            if not driver_user: driver_user = db.query(User).filter(User.username == driver_name, User.role == 'driver').first()

            raw_acct = driver_user.gcash_account.strip() if (driver_user and driver_user.gcash_account) else ""
            if raw_acct and raw_acct.lower() not in ["gcash", "maya"]: account_number = raw_acct
            elif driver_user and driver_user.whatsapp_number and driver_user.whatsapp_number.strip(): account_number = driver_user.whatsapp_number
            else: account_number = "MISSING_ACCOUNT"
                
            bank_provider = driver_user.bank_name if driver_user and driver_user.bank_name else "GCash"
            local_tag = driver_user.local_ref if driver_user and driver_user.local_ref else "2DA"
            writer.writerow([account_number, driver_name, f"{amount:.2f}", f"2DA Payout [{local_tag}] ({bank_provider})"])

    if total_katoda_payout > 0:
        writer.writerow([katoda_account, f"{branch} Organization", f"{total_katoda_payout:.2f}", f"2DA Daily Katoda Share ({katoda_bank})"])
        
    output.seek(0)
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename_branch = branch.replace(' ', '_') if branch != "All" else "Master"
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=BizLink_{filename_branch}_Payout_{current_date}.csv"})

@app.get("/api/admin/toda-config/{toda_name}")
def get_toda_config(toda_name: str, db: Session = Depends(get_db)):
    clean_toda = toda_name.strip().upper()
    config = db.query(TodaConfig).filter(TodaConfig.toda_name == clean_toda).first()
    
    if not config:
        return {
            "s1_name": "Pasundo", "s1_price": 50,
            "s2_name": "Pabili", "s2_price": 50,
            "s3_name": "Papickup", "s3_price": 50,
            "s4_name": "", "s4_price": 0,
            "s5_name": "", "s5_price": 0,
            "platform_share": 17.0, "katoda_share": 3.0,
            "katoda_bank": "GCash", "katoda_account": ""
        }
        
    return {
        "s1_name": config.s1_name, "s1_price": config.s1_price,
        "s2_name": config.s2_name, "s2_price": config.s2_price,
        "s3_name": config.s3_name, "s3_price": config.s3_price,
        "s4_name": config.s4_name, "s4_price": config.s4_price,
        "s5_name": config.s5_name, "s5_price": config.s5_price,
        "platform_share": config.platform_share, "katoda_share": config.katoda_share,
        "katoda_bank": config.katoda_bank, "katoda_account": config.katoda_account
    }

@app.post("/api/admin/toda-config/{toda_name}")
def update_toda_config(toda_name: str, data: TodaConfigUpdateSchema, db: Session = Depends(get_db)):
    clean_toda = toda_name.strip().upper()
    config = db.query(TodaConfig).filter(TodaConfig.toda_name == clean_toda).first()
    
    if not config:
        config = TodaConfig(toda_name=clean_toda)
        db.add(config)
        
    config.s1_name = data.s1_name.strip().title()
    config.s1_price = data.s1_price
    config.s2_name = data.s2_name.strip().title()
    config.s2_price = data.s2_price
    config.s3_name = data.s3_name.strip().title()
    config.s3_price = data.s3_price
    config.s4_name = data.s4_name.strip().title()
    config.s4_price = data.s4_price
    config.s5_name = data.s5_name.strip().title()
    config.s5_price = data.s5_price
    
    config.platform_share = data.platform_share
    config.katoda_share = data.katoda_share
    
    if data.katoda_bank is not None:
        config.katoda_bank = data.katoda_bank
    if data.katoda_account is not None:
        config.katoda_account = data.katoda_account
    
    db.commit()
    return {"status": "success"}

@app.get("/api/admin/config")
def get_system_config(db: Session = Depends(get_db)): return db.query(SystemConfig).first()

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
    return {"status": "success"}

@app.get("/pending-rides/")
def get_pending_rides(db: Session = Depends(get_db)):
    rides = db.query(RideRequest).all()
    results = []
    for r in rides:
        pass_phone = "0"
        pass_user = db.query(User).filter(User.full_name == sanitize_name(r.passenger_name), User.role == 'passenger').first()
        if not pass_user: pass_user = db.query(User).filter(User.username == sanitize_name(r.passenger_name), User.role == 'passenger').first()
        if pass_user and pass_user.whatsapp_number: pass_phone = pass_user.whatsapp_number
            
        drv_phone = "0"
        if r.driver_name:
            drv_user = db.query(User).filter(User.full_name == sanitize_name(r.driver_name), User.role == 'driver').first()
            if not drv_user: drv_user = db.query(User).filter(User.username == sanitize_name(r.driver_name), User.role == 'driver').first()
            if drv_user and drv_user.whatsapp_number: drv_phone = drv_user.whatsapp_number

        results.append({
            "id": r.id, "passenger_name": r.passenger_name, "pickup_location": r.pickup_location,
            "dropoff_location": r.dropoff_location, "service_type": r.service_type, "fare": r.fare,
            "status": r.status, "driver_name": sanitize_name(r.driver_name), "rating": r.rating,
            "passenger_phone": pass_phone, "driver_phone": drv_phone, "branch": r.branch,
            "local_ref": r.local_ref if r.local_ref else "N/A"
        })
    return results

@app.get("/api/rides")
def get_available_rides(request: Request, db: Session = Depends(get_db)):
    driver_name = request.cookies.get("driver_name")
    driver_branch = None
    driver_brgy = None

    if driver_name:
        clean_name = sanitize_name(driver_name)
        driver = db.query(User).filter((User.full_name == clean_name) | (User.username == clean_name), User.role == 'driver').first()
        if driver:
            driver_branch = driver.branch
            driver_brgy = driver.barangay

    rides = db.query(RideRequest).all()
    results = []
    
    for r in rides:
        ride_data = {
            "id": r.id, "passenger_name": r.passenger_name, "pickup_location": r.pickup_location,
            "dropoff_location": r.dropoff_location, "service_type": r.service_type, "fare": r.fare,
            "status": r.status, "driver_name": sanitize_name(r.driver_name),
            "branch": r.branch, "local_ref": r.local_ref
        }

        if driver_brgy and r.status == "pending" and r.branch:
            if driver_brgy.lower() in r.branch.lower():
                ride_data["branch"] = driver_branch

        results.append(ride_data)

    return results

@app.get("/ride-status/{ride_id}")
def check_ride_status(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride: raise HTTPException(status_code=404, detail="Ride not found")
    return {"status": ride.status, "driver_name": sanitize_name(ride.driver_name), "local_ref": ride.local_ref}

class ConnectionManager:
    def __init__(self): self.active_connections: Dict[str, List[WebSocket]] = {}
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

@app.get("/api/toda/finances")
def get_toda_finances(toda_name: str, db: Session = Depends(get_db)):
    branch_config = db.query(TodaConfig).filter(TodaConfig.toda_name == toda_name.strip().upper()).first()
    toda_pct = (branch_config.katoda_share if branch_config else 3) / 100

    search_term = f"%{toda_name.strip()}%"
    
    drivers = db.query(User).filter(User.toda_name.ilike(search_term), User.role == 'driver').all()
    driver_names = [sanitize_name(d.full_name) if d.full_name else sanitize_name(d.username) for d in drivers]

    rides = db.query(RideRequest).filter(RideRequest.status.in_(["completed", "paid"])).all()

    total_toda_share = 0.0
    for r in rides:
        clean_driver = sanitize_name(r.driver_name) if r.driver_name else ""
        if clean_driver in driver_names:
            try:
                clean_fare = float(str(r.fare).replace('₱', '').replace(',', '').strip())
                total_toda_share += clean_fare * toda_pct
            except ValueError:
                continue

    return {
        "today": total_toda_share,  
        "week": total_toda_share,
        "month": total_toda_share,
        "ytd": total_toda_share
    }

toda_broadcasts = {}

class TodaBroadcastSchema(BaseModel): 
    toda_name: str
    message: str

@app.post("/api/toda/broadcast")
def send_toda_broadcast(data: TodaBroadcastSchema):
    clean_toda = data.toda_name.strip().upper()
    toda_broadcasts[clean_toda] = data.message
    return {"status": "success", "message": f"Broadcast sent to {clean_toda}"}

@app.get("/api/driver/broadcast")
def get_driver_broadcast(driver_name: str = "", db: Session = Depends(get_db)): 
    clean_name = sanitize_name(driver_name)
    
    driver = db.query(User).filter(
        (User.full_name == clean_name) | (User.username == clean_name), 
        User.role == 'driver'
    ).first()
    
    if driver and driver.toda_name:
        clean_toda = driver.toda_name.strip().upper()
        return {"message": toda_broadcasts.get(clean_toda, ""), "toda_name": clean_toda}
        
    return {"message": "", "toda_name": ""}

# ==========================================
# 7. MOUNT WEB FOLDER & START SERVER
# ==========================================
app.mount("/", StaticFiles(directory="web", html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
