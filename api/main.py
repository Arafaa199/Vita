from fastapi import FastAPI, HTTPException, Depends, APIRouter, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date
from .db import SessionLocal, Base, engine
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from fastapi.responses import JSONResponse
import shutil
import os

from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)



app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.mount("/api/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


router = APIRouter()

@router.get("/clients/{client_id}/photos")
def get_client_photos(client_id: int, db: Session = Depends(get_db)):
    photos = db.query(ClientPhoto).filter(ClientPhoto.client_id == client_id).all()
    return [
        {
            "label": photo.label,
            "image_url": photo.image_url,
            "uploaded_at": photo.uploaded_at.isoformat() if photo.uploaded_at else None
        }
        for photo in photos
    ]


@router.post("/upload_photo/")
async def upload_photo(
    client_id: int = Form(...),
    label: str = Form(...),  # 'before', 'after', 'progress', 'other'
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # ✅ Check if client exists before proceeding
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return JSONResponse(status_code=404, content={"error": "Client not found"})

    if label not in ["before", "after", "progress", "other"]:
        return JSONResponse(status_code=400, content={"error": "Invalid label"})

    # Create upload folder if it doesn't exist
    relative_dir = os.path.join("clients", str(client_id))
    folder = os.path.join(UPLOADS_DIR, relative_dir)
    os.makedirs(folder, exist_ok=True)

    # Timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{label}_{timestamp}.jpg"
    file_path = os.path.join(folder, filename)  # filesystem path

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Public URL served by StaticFiles mounted at /api/uploads
    public_url = f"/api/uploads/{relative_dir}/{filename}"

    # Save metadata to DB
    photo = ClientPhoto(client_id=client_id, label=label, image_url=public_url)
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return {
        "status": "success",
        "photo_id": photo.id,
        "image_url": public_url,
        "uploaded_at": photo.uploaded_at
    }







class ClientPhoto(Base):
    __tablename__ = "client_photos"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    label = Column(Text, nullable=False)
    image_url = Column(Text, nullable=False)
    uploaded_at = Column(DateTime(timezone=False), server_default=func.now())




# models
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

# schema
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


#api routes
@router.post("/clients/", response_model=ClientRead)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    db_client = Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.get("/clients/", response_model=List[ClientRead])
def read_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    return clients

@router.get("/clients/{client_id}", response_model=ClientRead)
def get_client_by_id(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, updated_client: ClientCreate, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    for key, value in updated_client.dict().items():
        setattr(db_client, key, value)

    db.commit()
    db.refresh(db_client)
    return db_client

@router.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    db.delete(client)
    db.commit()
    return {"detail": "Client deleted successfully"}

#sqlalchamy model
class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    type = Column(String(20))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

# models
class PlanIn(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = None


class PlanOut(PlanIn):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# --- Training & Diet Plan Models ---
class TrainingPlan(Base):
    __tablename__ = "training_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    # JSON as Text for SQLite compatibility (store serialized JSON: exercises, schedule, etc.)
    structure = Column(Text)  # e.g., {"days":[{"day":"Push","exercises":[...]}]}
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class DietPlan(Base):
    __tablename__ = "diet_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    # JSON as Text for SQLite compatibility (meals, macros, timing)
    structure = Column(Text)  # e.g., {"meals":[{"time":"08:00","items":[...]}]}
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

# --- Pydantic Schemas ---
class TrainingPlanIn(BaseModel):
    name: str
    description: Optional[str] = None
    structure: Optional[str] = None  # JSON string

class TrainingPlanOut(TrainingPlanIn):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

class DietPlanIn(BaseModel):
    name: str
    description: Optional[str] = None
    structure: Optional[str] = None  # JSON string

class DietPlanOut(DietPlanIn):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True




@router.post("/plans/", response_model=PlanOut)
def create_plan(plan: PlanIn, db: Session = Depends(get_db)):
    new_plan = Plan(**plan.dict())
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan

@router.get("/plans/", response_model=List[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    return db.query(Plan).order_by(Plan.created_at.desc()).all()

@router.get("/plans/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.put("/plans/{plan_id}", response_model=PlanOut)
def update_plan(plan_id: int, plan_data: PlanIn, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for field, value in plan_data.dict().items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan

@router.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return {"message": "Plan deleted successfully"}


# --- Training Plans CRUD ---
@router.post("/training_plans/", response_model=TrainingPlanOut)
def create_training_plan(plan: TrainingPlanIn, db: Session = Depends(get_db)):
    tp = TrainingPlan(**plan.dict())
    db.add(tp)
    db.commit()
    db.refresh(tp)
    return tp

@router.get("/training_plans/", response_model=List[TrainingPlanOut])
def list_training_plans(db: Session = Depends(get_db)):
    return db.query(TrainingPlan).order_by(TrainingPlan.created_at.desc()).all()

@router.get("/training_plans/{plan_id}", response_model=TrainingPlanOut)
def get_training_plan(plan_id: int, db: Session = Depends(get_db)):
    tp = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not tp:
        raise HTTPException(status_code=404, detail="Training plan not found")
    return tp

@router.put("/training_plans/{plan_id}", response_model=TrainingPlanOut)
def update_training_plan(plan_id: int, plan: TrainingPlanIn, db: Session = Depends(get_db)):
    tp = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not tp:
        raise HTTPException(status_code=404, detail="Training plan not found")
    for k, v in plan.dict().items():
        setattr(tp, k, v)
    db.commit()
    db.refresh(tp)
    return tp

@router.delete("/training_plans/{plan_id}")
def delete_training_plan(plan_id: int, db: Session = Depends(get_db)):
    tp = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not tp:
        raise HTTPException(status_code=404, detail="Training plan not found")
    db.delete(tp)
    db.commit()
    return {"message": "Training plan deleted successfully"}


# --- Diet Plans CRUD ---
@router.post("/diet_plans/", response_model=DietPlanOut)
def create_diet_plan(plan: DietPlanIn, db: Session = Depends(get_db)):
    dp = DietPlan(**plan.dict())
    db.add(dp)
    db.commit()
    db.refresh(dp)
    return dp

@router.get("/diet_plans/", response_model=List[DietPlanOut])
def list_diet_plans(db: Session = Depends(get_db)):
    return db.query(DietPlan).order_by(DietPlan.created_at.desc()).all()

@router.get("/diet_plans/{plan_id}", response_model=DietPlanOut)
def get_diet_plan(plan_id: int, db: Session = Depends(get_db)):
    dp = db.query(DietPlan).filter(DietPlan.id == plan_id).first()
    if not dp:
        raise HTTPException(status_code=404, detail="Diet plan not found")
    return dp

@router.put("/diet_plans/{plan_id}", response_model=DietPlanOut)
def update_diet_plan(plan_id: int, plan: DietPlanIn, db: Session = Depends(get_db)):
    dp = db.query(DietPlan).filter(DietPlan.id == plan_id).first()
    if not dp:
        raise HTTPException(status_code=404, detail="Diet plan not found")
    for k, v in plan.dict().items():
        setattr(dp, k, v)
    db.commit()
    db.refresh(dp)
    return dp

@router.delete("/diet_plans/{plan_id}")
def delete_diet_plan(plan_id: int, db: Session = Depends(get_db)):
    dp = db.query(DietPlan).filter(DietPlan.id == plan_id).first()
    if not dp:
        raise HTTPException(status_code=404, detail="Diet plan not found")
    db.delete(dp)
    db.commit()
    return {"message": "Diet plan deleted successfully"}



# --- Client Plan Models & Endpoints ---

from typing import List as TypingList, Optional as TypingOptional

# --- Client Training & Diet Assignments ---
class ClientTrainingPlan(Base):
    __tablename__ = "client_training_plans"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    training_plan_id = Column(Integer, ForeignKey("training_plans.id", ondelete="CASCADE"))
    assigned_on = Column(TIMESTAMP, default=datetime.utcnow)
    notes = Column(Text)

class ClientDietPlan(Base):
    __tablename__ = "client_diet_plans"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    diet_plan_id = Column(Integer, ForeignKey("diet_plans.id", ondelete="CASCADE"))
    assigned_on = Column(TIMESTAMP, default=datetime.utcnow)
    notes = Column(Text)

class ClientTrainingPlanIn(BaseModel):
    client_id: int
    training_plan_id: int
    notes: Optional[str] = None

class ClientDietPlanIn(BaseModel):
    client_id: int
    diet_plan_id: int
    notes: Optional[str] = None

class ClientTrainingPlanOut(BaseModel):
    id: int
    client_id: int
    training_plan_id: int
    assigned_on: datetime
    notes: Optional[str]
    class Config:
        orm_mode = True

class ClientDietPlanOut(BaseModel):
    id: int
    client_id: int
    diet_plan_id: int
    assigned_on: datetime
    notes: Optional[str]
    class Config:
        orm_mode = True

class ClientPlan(Base):
    __tablename__ = "client_plans"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"))
    assigned_on = Column(TIMESTAMP, default=datetime.utcnow)
    notes = Column(Text)

class ClientPlanIn(BaseModel):
    client_id: int
    plan_id: int
    notes: TypingOptional[str] = None

class ClientPlanOut(BaseModel):
    id: int
    client_id: int
    plan_id: int
    assigned_on: datetime
    notes: TypingOptional[str]

    class Config:
        orm_mode = True


@router.get("/client_plans/{client_id}")
def get_current_client_plan(client_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the most recently assigned plan for a given client, including plan details.
    """
    result = db.query(ClientPlan, Plan)\
        .join(Plan, ClientPlan.plan_id == Plan.id)\
        .filter(ClientPlan.client_id == client_id)\
        .order_by(ClientPlan.assigned_on.desc())\
        .first()

    if not result:
        raise HTTPException(status_code=404, detail="No plan assigned")

    cp, plan = result

    return {
        "id": cp.id,
        "client_id": cp.client_id,
        "plan_id": cp.plan_id,
        "assigned_on": cp.assigned_on,
        "notes": cp.notes,
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "type": plan.type,
            "description": plan.description,
            "created_at": plan.created_at
        }
    }



@router.post("/client_plans/", response_model=ClientPlanOut)
def assign_plan(data: ClientPlanIn, db: Session = Depends(get_db)):
    """
    Assign a plan to a client.
    """
    assignment = ClientPlan(**data.dict())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/client_plans/{client_id}/history", response_model=TypingList[ClientPlanOut])
def get_client_plan_history(client_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all plan assignments for a given client, ordered from newest to oldest.
    """
    results = db.query(ClientPlan, Plan)\
                .join(Plan, ClientPlan.plan_id == Plan.id)\
                .filter(ClientPlan.client_id == client_id)\
                .order_by(ClientPlan.assigned_on.desc())\
                .all()

    return [
        {
            "id": cp.id,
            "client_id": cp.client_id,
            "plan_id": cp.plan_id,
            "assigned_on": cp.assigned_on,
            "notes": cp.notes,
            "plan_name": plan.name,
            "plan_type": plan.type
        }
        for cp, plan in results

    ]

# --- Client Training Plan assign & history ---
@router.post("/client_training_plans/", response_model=ClientTrainingPlanOut)
def assign_training_plan(data: ClientTrainingPlanIn, db: Session = Depends(get_db)):
    obj = ClientTrainingPlan(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/client_training_plans/{client_id}/history", response_model=List[ClientTrainingPlanOut])
def get_training_history(client_id: int, db: Session = Depends(get_db)):
    rows = db.query(ClientTrainingPlan)\
             .filter(ClientTrainingPlan.client_id == client_id)\
             .order_by(ClientTrainingPlan.assigned_on.desc())\
             .all()
    return rows

# --- Client Diet Plan assign & history ---
@router.post("/client_diet_plans/", response_model=ClientDietPlanOut)
def assign_diet_plan(data: ClientDietPlanIn, db: Session = Depends(get_db)):
    obj = ClientDietPlan(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/client_diet_plans/{client_id}/history", response_model=List[ClientDietPlanOut])
def get_diet_history(client_id: int, db: Session = Depends(get_db)):
    rows = db.query(ClientDietPlan)\
             .filter(ClientDietPlan.client_id == client_id)\
             .order_by(ClientDietPlan.assigned_on.desc())\
             .all()
    return rows

Base.metadata.create_all(bind=engine)
app.include_router(router, prefix="/api")