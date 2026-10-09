from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
# Assuming Base is imported from your database configuration, e.g.:
# from database import Base 

class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    passenger_name = Column(String(100), index=True)
    driver_name = Column(String(100), nullable=True)
    pickup_location = Column(String(255))
    dropoff_location = Column(String(255))
    service_type = Column(String(100))
    fare = Column(String(50))
    status = Column(String(50), default="pending")
    local_ref = Column(String(50), nullable=True)
    
    # 🟢 ADD THESE TWO COLUMNS FOR PABILI & PAPICKUP
    pabili_list = Column(Text, nullable=True)
    item_description = Column(Text, nullable=True)
    
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"), index=True) # Links to the specific ride
    sender = Column(String(50)) # 'Passenger Name' or 'Driver Name'
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
