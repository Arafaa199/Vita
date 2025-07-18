from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from db import SessionLocal, Base, engine

# model
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String)
    age = Column(Integer)
    weight = Column(Float)
    goal = Column(String)
    notes = Column(String, default="")
    membership_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    start_date = Column(Date, default=date.today)
    end_date = Column(Date, nullable=True)
    phone = Column(String)
    height = Column(Float)

#schema
class ClientCreate(BaseModel):
    full_name: str
    email: str
    age: int
    weight: float
    goal: str
    notes: str = ""
    membership_active: bool = True
    start_date: Optional[date] = date.today()
    end_date: Optional[date] = None
    phone: Optional[str] = None
    height: Optional[float] = None

class ClientRead(ClientCreate):
    id: int
    created_at: datetime
    start_date: Optional[date]
    end_date: Optional[date]
    phone: Optional[str] = None
    height: Optional[float] = None

    class Config:
        orm_mode = True

# fastapi
app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# tables
Base.metadata.create_all(bind=engine)

# routes
@app.post("/api/clients/", response_model=ClientRead)
def create_client(client: ClientCreate):
    db = SessionLocal()
    db_client = Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    db.close()
    return db_client

@app.get("/api/clients/", response_model=List[ClientRead])
def read_clients():
    db = SessionLocal()
    clients = db.query(Client).all()
    db.close()
    return clients

@app.get("/api/clients/{client_id}", response_model=ClientRead)
def get_client_by_id(client_id: int):
    db = SessionLocal()
    client = db.query(Client).filter(Client.id == client_id).first()
    db.close()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@app.put("/api/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, updated_client: ClientCreate):
    db = SessionLocal()
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        db.close()
        raise HTTPException(status_code=404, detail="Client not found")

    for key, value in updated_client.dict().items():
        setattr(db_client, key, value)

    db.commit()
    db.refresh(db_client)
    db.close()
    return db_client
@app.delete("/api/clients/{client_id}")
def delete_client(client_id: int):
    db = SessionLocal()
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        db.close()
        raise HTTPException(status_code=404, detail="Client not found")

    db.delete(client)
    db.commit()
    db.close()
    return {"detail": "Client deleted successfully"}