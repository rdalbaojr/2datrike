from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
# Assuming you have a Base declarative model setup
# from database import Base 

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"), index=True) # Links to the specific ride
    sender = Column(String(50)) # 'Passenger Name' or 'Driver Name'
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
