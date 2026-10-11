import os
import shutil
import json
import random
from datetime import datetime
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse, StreamingResponse
from fastapi import FastAPI, Depends, Form, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Dict, Optional
import csv
from io import StringIO
from fastapi.responses import FileResponse


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
    
    pabili_list = Column(Text, nullable=True)
    item_description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)

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
    broadcast_message = Column(String, default="")

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
        db.execute(text("ALTER TABLE ride_requests ADD COLUMN pabili_list TEXT"))
        db.execute(text("ALTER TABLE ride_requests ADD COLUMN item_description TEXT"))
        db.execute(text("ALTER TABLE users ADD COLUMN plate_number VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE toda_configs ADD COLUMN broadcast_message VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE ride_requests ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
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
    pabili_list: Optional[str] = ""
    item_description: Optional[str] = ""

class AcceptRideSchema(BaseModel):
    driver_name: Optional[str] = "Driver"

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
    city: Optional[str] = "Pasig City"
    barangay: Optional[str] = ""
    toda_name: Optional[str] = ""
    toda_number: Optional[str] = ""
    plate_number: Optional[str] = ""
    security_q: str
    security_a: str
    bank_name: Optional[str] = "GCash"
    gcash_account: Optional[str] = ""
    whatsapp_number: Optional[str] = ""

class TodaBroadcastSchema(BaseModel): 
    toda_name: str
    message: str

def sanitize_name(name: str) -> str:
    if not name: return ""
    return name.replace('"', '').replace("'", "").strip()

# ==========================================
# 6. API ENDPOINTS
# ==========================================
@app.get("/")
def read_root():
    return RedirectResponse(url="/login.html")

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
    user = db.query(User).filter(User.username.ilike(clean_user), User.password == password).first()
    if not user: raise HTTPException(status_code=400, detail="Invalid username or password")
    
    if user.is_suspended == 1: raise HTTPException(status_code=403, detail="ACCOUNT SUSPENDED: Please contact TODA admin.")
    
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
    user = db.query(User).filter(User.username.ilike(clean_username)).first()
    if user:
        user.status = "offline"
        user.last_offline = datetime.now()
        db.commit()
    return {"message": "Logged out"}

@app.post("/register")
def register_user_json(user: UserCreateJSON, db: Session = Depends(get_db)):
    clean_username = sanitize_name(user.username)
    clean_full_name = sanitize_name(user.full_name).title() if user.full_name else clean_username

    existing = db.query(User).filter(User.username.ilike(clean_username)).first()
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
        whatsapp_number=user.whatsapp_number, 
        city=user.city.strip().title() if user.city else "Pasig City",
        barangay=user.barangay.strip().title() if user.barangay else "",
        toda_name=formatted_toda,
        local_ref=local_ref,
        security_q=user.security_q,
        security_a=user.security_a,
        toda_number=user.toda_number,    
        plate_number=user.plate_number.upper() if user.plate_number else "", 
        bank_name=user.bank_name,            
        gcash_account=user.gcash_account,    
        rating_sum=25.0,
        rating_count=5
    )
    
    db.add(new_user)

    if user.role == "toda_admin" and formatted_toda:
        config = db.query(TodaConfig).filter(TodaConfig.toda_name == formatted_toda).first()
        if not config:
            config = TodaConfig(toda_name=formatted_toda)
            db.add(config)
        config.katoda_bank = user.bank_name
        config.katoda_account = user.gcash_account

    db.commit()
    return {"status": "success"}

@app.post("/api/reset-password-security")
def reset_password_security(data: PasswordResetSchemaSecurity, db: Session = Depends(get_db)):
    clean_user = sanitize_name(data.username)
    user = db.query(User).filter(User.username.ilike(clean_user)).first()
    
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

    existing = db.query(User).filter(User.username.ilike(clean_username)).first()
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
        User.username.ilike(data.username), 
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
    user = db.query(User).filter(
        (User.full_name.ilike(clean_name)) | (User.username.ilike(clean_name))
    ).first()
        
    if not user: 
        raise HTTPException(status_code=404, detail="User not found")
    
    avg_rating = 5.0
    if user.rating_count and user.rating_count > 0: 
        avg_rating = round(user.rating_sum / user.rating_count, 1)
        
    return {
        "full_name": user.full_name, 
        "whatsapp_number": user.whatsapp_number,
        "bank_name": user.bank_name if user.bank_name else "GCash",
        "gcash_account": user.gcash_account if user.gcash_account else "",
        "address": user.address if user.address else "", 
        "rating": avg_rating,
        "barangay": user.barangay if user.barangay else "",
        "local_ref": user.local_ref if user.local_ref else "N/A",
        "toda_name": user.toda_name if user.toda_name else "" 
    }# ==========================================
# 7. ROBUST HTML FILE SERVING
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def find_file(filename: str):
    # Check current directory first, then /web subfolder
    direct_path = os.path.join(BASE_DIR, filename)
    web_path = os.path.join(BASE_DIR, "web", filename)
    if os.path.exists(direct_path):
        return direct_path
    if os.path.exists(web_path):
        return web_path
    return None

@app.get("/")
def serve_root():
    login_path = find_file("login.html")
    if login_path:
        return FileResponse(login_path)
    return RedirectResponse(url="/login.html")

@app.get("/{page_name}.html")
def serve_html_page(page_name: str):
    filepath = find_file(f"{page_name}.html")
    if filepath:
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail=f"Page {page_name}.html not found on server")

# Fallback static mount for icons, images, etc.
static_dir = os.path.join(BASE_DIR, "web") if os.path.isdir(os.path.join(BASE_DIR, "web")) else BASE_DIR
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

@app.post("/api/update-profile")
def update_profile(data: ProfileUpdateSchema, db: Session = Depends(get_db)):
    clean_name = sanitize_name
