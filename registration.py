import re
import random
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field, field_validator, ValidationInfo
import uvicorn

app = FastAPI(
    title="2DA Registration API",
    version="1.0.0",
    description="Backend API for passenger and tricycle driver registrations."
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== HELPER VALIDATORS ====================

def is_valid_ph_mobile(number: str) -> bool:
    """Validates 11-digit PH mobile numbers starting with 09."""
    pattern = r"^09\d{9}$"
    return bool(re.match(pattern, number.strip()))


# ==================== MOCK DATABASE ====================
# This temporarily stores OTPs in memory. 
# In production, this will be moved to Redis or PostgreSQL.
otp_storage: Dict[str, dict] = {}


# ==================== SCHEMAS ====================

class PassengerRegistrationSchema(BaseModel):
    full_name: str = Field(..., json_schema_extra={"example": "Juan Dela Cruz"})
    auth_type: str = Field(..., description="mobile or facebook", json_schema_extra={"example": "mobile"})
    contact_info: str = Field(..., json_schema_extra={"example": "09171234567"})
    barangay: Optional[str] = Field(None, json_schema_extra={"example": "Brgy. San Antonio, Pasig City"})

    @field_validator("contact_info")
    @classmethod
    def validate_contact(cls, v: str, info: ValidationInfo):
        auth_type = info.data.get("auth_type")
        if auth_type == "mobile" and not is_valid_ph_mobile(v):
            raise ValueError("Please provide a valid 11-digit PH mobile number starting with 09.")
        return v

class DriverRegistrationSchema(BaseModel):
    full_name: str = Field(..., json_schema_extra={"example": "Pedro Penduko"})
    mobile_number: str = Field(..., json_schema_extra={"example": "09181234567"})
    license_no: str = Field(..., json_schema_extra={"example": "A01-23-456789"})
    body_no: str = Field(..., json_schema_extra={"example": "042"})
    toda_name: str = Field(..., json_schema_extra={"example": "SANTODA Pasig"})
    payout_provider: str = Field(..., json_schema_extra={"example": "GCash"})
    payout_account: str = Field(..., json_schema_extra={"example": "09181234567"})

    @field_validator("mobile_number", "payout_account")
    @classmethod
    def validate_ph_numbers(cls, v: str):
        if not is_valid_ph_mobile(v):
            raise ValueError("Please enter a valid 11-digit Philippine mobile number starting with 09.")
        return v

# --- NEW OTP SCHEMAS ---
class OTPRequestSchema(BaseModel):
    mobile_number: str = Field(..., json_schema_extra={"example": "09171234567"})

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str):
        if not is_valid_ph_mobile(v):
            raise ValueError("Please enter a valid 11-digit Philippine mobile number.")
        return v

class OTPVerifySchema(BaseModel):
    mobile_number: str = Field(..., json_schema_extra={"example": "09171234567"})
    otp_code: str = Field(..., json_schema_extra={"example": "123456"})


# ==================== FRONTEND ENDPOINTS ====================

@app.get("/book", response_class=HTMLResponse)
async def serve_passenger_portal():
    """Serves the passenger booking dashboard."""
    try:
        return FileResponse("booking.html")
    except Exception:
        return "<h3>booking.html not found. Please create the file.</h3>"

@app.get("/driver-portal", response_class=HTMLResponse)
async def serve_driver_portal():
    """Serves the driver dashboard."""
    try:
        return FileResponse("driver.html")
    except Exception:
        return "<h3>driver.html not found. Please create the file.</h3>"


@app.get("/", response_class=HTMLResponse)
async def serve_home():
    """Serves the main registration page (index.html)."""
    try:
        return FileResponse("index.html")
    except Exception:
        return "<h3>index.html not found in current directory.</h3>"    


# ==================== API ENDPOINTS ====================

@app.post("/api/v1/auth/request-otp")
async def request_otp(data: OTPRequestSchema):
    """Generates a 6-digit OTP and simulates sending it via WhatsApp."""
    otp_code = str(random.randint(100000, 999999))
    expiry = datetime.now() + timedelta(minutes=5)
    
    # Store it in our temporary dictionary
    otp_storage[data.mobile_number] = {"code": otp_code, "expires": expiry}
    
    # In production, this is where you call the Meta WhatsApp Cloud API
    print(f"\n[WHATSAPP SIMULATION] Sending OTP {otp_code} to {data.mobile_number}\n")
    
    return {"status": "success", "message": "OTP generated and sent to WhatsApp."}

@app.post("/api/v1/auth/verify-otp")
async def verify_otp(data: OTPVerifySchema):
    """Verifies the OTP provided by the user."""
    record = otp_storage.get(data.mobile_number)
    
    if not record:
        raise HTTPException(status_code=400, detail="No OTP requested for this number.")
        
    if datetime.now() > record["expires"]:
        # Clean up expired code
        del otp_storage[data.mobile_number]
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
        
    if record["code"] != data.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code.")
        
    # Success! Clear the OTP so it can't be reused
    del otp_storage[data.mobile_number]
    return {"status": "success", "message": "Phone number verified successfully!"}

@app.post("/api/v1/register/passenger", status_code=status.HTTP_201_CREATED)
async def register_passenger(data: PassengerRegistrationSchema):
    """Registers a new passenger."""
    return {
        "status": "success",
        "role": "PASSENGER",
        "message": f"Welcome to 2DA, {data.full_name}! Your passenger registration is complete.",
        "data": data.model_dump()
    }

@app.post("/api/v1/register/driver", status_code=status.HTTP_201_CREATED)
async def register_driver(data: DriverRegistrationSchema):
    """Registers a new tricycle driver pending TODA verification."""
    return {
        "status": "success",
        "role": "DRIVER",
        "message": f"2DA application received for {data.full_name} ({data.toda_name} Body #{data.body_no}). Your account is pending verification.",
        "data": data.model_dump()
    }


# ==================== SERVER RUNNER ====================

if __name__ == "__main__":
    uvicorn.run("registration:app", host="0.0.0.0", port=8000, reload=True)
