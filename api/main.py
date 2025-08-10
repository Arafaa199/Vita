from fastapi import FastAPI, HTTPException, Depends, APIRouter, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, Text, TIMESTAMP, ForeignKey, text as SA_TEXT
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
STATIC_DIR  = os.path.normpath(os.path.join(BASE_DIR, "..", "site"))
os.makedirs(UPLOADS_DIR, exist_ok=True)




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.mount("/api/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")



router = APIRouter()

# --- Pydantic V2 ORM base ---
class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# --- Health Endpoints ---
@router.get("/health/ping")
def health_ping():
    return {"status": "ok"}

@router.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(SA_TEXT("SELECT 1"))
    return {"status": "ok"}

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

class ClientRead(ClientCreate, OrmBase):
    id: int
    created_at: datetime
    start_date: Optional[date]
    end_date: Optional[date]
    phone: Optional[str] = None
    height: Optional[float] = None


#api routes
@router.post("/clients/", response_model=ClientRead)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    db_client = Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.get("/clients/", response_model=List[ClientRead])
def read_clients(q: Optional[str] = None, active: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(Client)
    if q:
        like = f"%{q}%"
        query = query.filter((Client.full_name.ilike(like)) | (Client.email.ilike(like)) | (Client.phone.ilike(like)))
    if active is not None:
        query = query.filter(Client.membership_active == active)
    return query.order_by(Client.created_at.desc()).all()

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


class PlanOut(PlanIn, OrmBase):
    id: int
    created_at: datetime


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

class TrainingPlanOut(TrainingPlanIn, OrmBase):
    id: int
    created_at: datetime

class DietPlanIn(BaseModel):
    name: str
    description: Optional[str] = None
    structure: Optional[str] = None  # JSON string



class DietPlanOut(DietPlanIn, OrmBase):
    id: int
    created_at: datetime

# --- Programs (bundle training + diet) ---
class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    training_plan_id = Column(Integer, ForeignKey("training_plans.id", ondelete="SET NULL"), nullable=True)
    diet_plan_id = Column(Integer, ForeignKey("diet_plans.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class ProgramIn(BaseModel):
    name: str
    description: Optional[str] = None
    training_plan_id: Optional[int] = None
    diet_plan_id: Optional[int] = None

class ProgramOut(ProgramIn, OrmBase):
    id: int
    created_at: datetime


# --- Memberships ---
class Membership(Base):
    __tablename__ = "memberships"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    package_name = Column(String(100))
    price = Column(Float)
    status = Column(String(20), default="active")  # active|expired|cancelled
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    renewal_due_on = Column(Date, nullable=True)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

# --- Progress Metrics ---
class ProgressMetric(Base):
    __tablename__ = "progress_metrics"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, default=date.today)
    weight = Column(Float)
    body_fat_pct = Column(Float)
    chest = Column(Float)
    waist = Column(Float)
    hips = Column(Float)
    thigh = Column(Float)
    arm = Column(Float)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

# --- Workout Log ---
class WorkoutLog(Base):
    __tablename__ = "workout_log"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, default=date.today)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="SET NULL"), nullable=True)
    sets = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
    rpe = Column(Float)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

# --- Meal Plan Items ---
class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"
    id = Column(Integer, primary_key=True, index=True)
    diet_plan_id = Column(Integer, ForeignKey("diet_plans.id", ondelete="CASCADE"), nullable=False)
    meal_name = Column(String(100))
    food = Column(Text)
    qty = Column(Float)
    unit = Column(String(32))
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)
    notes = Column(Text)
    position = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

# --- Schemas: Memberships ---
class MembershipIn(BaseModel):
    client_id: int
    package_name: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = "active"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    renewal_due_on: Optional[date] = None
    notes: Optional[str] = None

class MembershipOut(MembershipIn, OrmBase):
    id: int
    created_at: datetime

# --- Schemas: Progress Metrics ---
class ProgressMetricIn(BaseModel):
    client_id: int
    date: Optional[date] = None
    weight: Optional[float] = None
    body_fat_pct: Optional[float] = None
    chest: Optional[float] = None
    waist: Optional[float] = None
    hips: Optional[float] = None
    thigh: Optional[float] = None
    arm: Optional[float] = None
    notes: Optional[str] = None

class ProgressMetricOut(ProgressMetricIn, OrmBase):
    id: int
    created_at: datetime

# --- Schemas: Workout Log ---
class WorkoutLogIn(BaseModel):
    client_id: int
    date: Optional[date] = None
    exercise_id: Optional[int] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    rpe: Optional[float] = None
    notes: Optional[str] = None

class WorkoutLogOut(WorkoutLogIn, OrmBase):
    id: int
    created_at: datetime

# --- Schemas: Meal Plan Items ---
class MealPlanItemIn(BaseModel):
    meal_name: Optional[str] = None
    food: Optional[str] = None
    qty: Optional[float] = None
    unit: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fats: Optional[float] = None
    notes: Optional[str] = None
    position: Optional[int] = 0

class MealPlanItemOut(MealPlanItemIn, OrmBase):
    id: int
    diet_plan_id: int
    created_at: datetime




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


# --- Programs CRUD ---
@router.post("/programs/", response_model=ProgramOut)
def create_program(p: ProgramIn, db: Session = Depends(get_db)):
    obj = Program(**p.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/programs/", response_model=List[ProgramOut])
def list_programs(db: Session = Depends(get_db)):
    return db.query(Program).order_by(Program.created_at.desc()).all()

@router.get("/programs/{program_id}", response_model=ProgramOut)
def get_program(program_id: int, db: Session = Depends(get_db)):
    obj = db.query(Program).filter(Program.id == program_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Program not found")
    return obj

@router.put("/programs/{program_id}", response_model=ProgramOut)
def update_program(program_id: int, payload: ProgramIn, db: Session = Depends(get_db)):
    obj = db.query(Program).filter(Program.id == program_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Program not found")
    for k, v in payload.dict().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/programs/{program_id}")
def delete_program(program_id: int, db: Session = Depends(get_db)):
    obj = db.query(Program).filter(Program.id == program_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Program not found")
    db.delete(obj)
    db.commit()
    return {"message": "Program deleted successfully"}

@router.get("/programs/{program_id}/full")
def get_program_full(program_id: int, db: Session = Depends(get_db)):
    prog = db.query(Program).filter(Program.id == program_id).first()
    if not prog:
        raise HTTPException(status_code=404, detail="Program not found")

    training = None
    if prog.training_plan_id:
        tp = db.query(TrainingPlan).filter(TrainingPlan.id == prog.training_plan_id).first()
        if tp:
            training = {"id": tp.id, "name": tp.name, "description": tp.description}

    diet = None
    if prog.diet_plan_id:
        dp = db.query(DietPlan).filter(DietPlan.id == prog.diet_plan_id).first()
        if dp:
            diet = {"id": dp.id, "name": dp.name, "description": dp.description}

    return {
        "program": {"id": prog.id, "name": prog.name, "description": prog.description, "created_at": prog.created_at},
        "training_plan": training,
        "diet_plan": diet,
    }



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


# --- Exercise, Workout, PlanWorkout Models, Schemas, and Endpoints ---
class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    primary_muscle = Column(String)
    equipment = Column(String)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class ExerciseIn(BaseModel):
    name: str
    primary_muscle: Optional[str] = None
    equipment: Optional[str] = None
    notes: Optional[str] = None

class ExerciseOut(ExerciseIn, OrmBase):
    id: int
    created_at: datetime

@router.post("/exercises/", response_model=ExerciseOut)
def create_exercise(ex: ExerciseIn, db: Session = Depends(get_db)):
    o = Exercise(**ex.dict())
    db.add(o)
    db.commit()
    db.refresh(o)
    return o

@router.get("/exercises/", response_model=List[ExerciseOut])
def list_exercises(q: Optional[str] = None, db: Session = Depends(get_db)):
    qry = db.query(Exercise)
    if q:
        like = f"%{q}%"
        qry = qry.filter((Exercise.name.ilike(like)) | (Exercise.primary_muscle.ilike(like)))
    return qry.order_by(Exercise.created_at.desc()).all()

@router.get("/exercises/{exercise_id}", response_model=ExerciseOut)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    o = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return o

@router.put("/exercises/{exercise_id}", response_model=ExerciseOut)
def update_exercise(exercise_id: int, data: ExerciseIn, db: Session = Depends(get_db)):
    o = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Exercise not found")
    for k, v in data.dict().items():
        setattr(o, k, v)
    db.commit()
    db.refresh(o)
    return o

@router.delete("/exercises/{exercise_id}")
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    o = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Exercise not found")
    db.delete(o)
    db.commit()
    return {"message": "Exercise deleted"}

class Workout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"
    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"))
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"))
    position = Column(Integer, default=0)
    sets = Column(Integer)
    reps = Column(Integer)
    rest_sec = Column(Integer)
    rir = Column(Integer)
    tempo = Column(String)

class WorkoutIn(BaseModel):
    name: str
    description: Optional[str] = None

class WorkoutOut(WorkoutIn, OrmBase):
    id: int
    created_at: datetime

class WorkoutExerciseItemIn(BaseModel):
    exercise_id: int
    position: int = 0
    sets: Optional[int] = None
    reps: Optional[int] = None
    rest_sec: Optional[int] = None
    rir: Optional[int] = None
    tempo: Optional[str] = None

class WorkoutExerciseItemOut(WorkoutExerciseItemIn):
    id: int

@router.post("/workouts/", response_model=WorkoutOut)
def create_workout(w: WorkoutIn, db: Session = Depends(get_db)):
    o = Workout(**w.dict())
    db.add(o)
    db.commit()
    db.refresh(o)
    return o

@router.get("/workouts/", response_model=List[WorkoutOut])
def list_workouts(db: Session = Depends(get_db)):
    return db.query(Workout).order_by(Workout.created_at.desc()).all()

@router.get("/workouts/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: int, db: Session = Depends(get_db)):
    o = db.query(Workout).filter(Workout.id == workout_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Workout not found")
    return o

@router.put("/workouts/{workout_id}", response_model=WorkoutOut)
def update_workout(workout_id: int, data: WorkoutIn, db: Session = Depends(get_db)):
    o = db.query(Workout).filter(Workout.id == workout_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Workout not found")
    for k, v in data.dict().items():
        setattr(o, k, v)
    db.commit()
    db.refresh(o)
    return o

@router.delete("/workouts/{workout_id}")
def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    o = db.query(Workout).filter(Workout.id == workout_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Workout not found")
    db.delete(o)
    db.commit()
    return {"message": "Workout deleted"}

@router.get("/workouts/{workout_id}/exercises", response_model=List[WorkoutExerciseItemOut])
def get_workout_items(workout_id: int, db: Session = Depends(get_db)):
    items = db.query(WorkoutExercise).filter(WorkoutExercise.workout_id == workout_id).order_by(WorkoutExercise.position.asc()).all()
    return items

@router.put("/workouts/{workout_id}/exercises", response_model=List[WorkoutExerciseItemOut])
def set_workout_items(workout_id: int, items: List[WorkoutExerciseItemIn], db: Session = Depends(get_db)):
    db.query(WorkoutExercise).filter(WorkoutExercise.workout_id == workout_id).delete()
    out = []
    for i, it in enumerate(items):
        rec = WorkoutExercise(
            workout_id=workout_id,
            exercise_id=it.exercise_id,
            position=it.position if it.position is not None else i,
            sets=it.sets,
            reps=it.reps,
            rest_sec=it.rest_sec,
            rir=it.rir,
            tempo=it.tempo,
        )
        db.add(rec)
        out.append(rec)
    db.commit()
    for rec in out:
        db.refresh(rec)
    return out

class PlanWorkout(Base):
    __tablename__ = "plan_workouts"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"))
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"))
    day_of_week = Column(Integer)  # 0-6
    position = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class PlanWorkoutMapIn(BaseModel):
    workout_id: int
    day_of_week: int
    position: Optional[int] = 0

class PlanScheduleIn(BaseModel):
    items: List[PlanWorkoutMapIn]

class PlanScheduleItemOut(BaseModel):
    id: int
    workout_id: int
    day_of_week: int
    position: int

@router.get("/plans/{plan_id}/workouts", response_model=List[PlanScheduleItemOut])
def get_plan_schedule(plan_id: int, db: Session = Depends(get_db)):
    rows = db.query(PlanWorkout).filter(PlanWorkout.plan_id == plan_id).order_by(PlanWorkout.day_of_week.asc(), PlanWorkout.position.asc()).all()
    return rows

@router.put("/plans/{plan_id}/workouts", response_model=List[PlanScheduleItemOut])
def set_plan_schedule(plan_id: int, payload: PlanScheduleIn, db: Session = Depends(get_db)):
    db.query(PlanWorkout).filter(PlanWorkout.plan_id == plan_id).delete()
    out = []
    for i, it in enumerate(payload.items):
        rec = PlanWorkout(plan_id=plan_id, workout_id=it.workout_id, day_of_week=it.day_of_week, position=(it.position or 0))
        db.add(rec)
        out.append(rec)
    db.commit()
    for rec in out:
        db.refresh(rec)
    return out


# --- Enriched plan payloads ---
@router.get("/plans/{plan_id}/workouts/full")
def get_plan_workouts_full(plan_id: int, db: Session = Depends(get_db)):
    sched = db.query(PlanWorkout).filter(PlanWorkout.plan_id == plan_id) \
             .order_by(PlanWorkout.day_of_week.asc(), PlanWorkout.position.asc()).all()
    workout_ids = [r.workout_id for r in sched]

    workouts = {}
    if workout_ids:
        for w in db.query(Workout).filter(Workout.id.in_(workout_ids)).all():
            workouts[w.id] = {"id": w.id, "name": w.name, "description": w.description}

    items = {}
    if workout_ids:
        for wi in workout_ids:
            rows = db.query(WorkoutExercise).filter(WorkoutExercise.workout_id == wi) \
                      .order_by(WorkoutExercise.position.asc()).all()
            out_rows = []
            for r in rows:
                ex = db.query(Exercise).filter(Exercise.id == r.exercise_id).first()
                out_rows.append({
                    "id": r.id,
                    "exercise_id": r.exercise_id,
                    "exercise_name": ex.name if ex else None,
                    "position": r.position,
                    "sets": r.sets,
                    "reps": r.reps,
                    "rest_sec": r.rest_sec,
                    "rir": r.rir,
                    "tempo": r.tempo,
                })
            items[wi] = out_rows

    return {
        "plan_id": plan_id,
        "schedule": [
            {
                "id": r.id,
                "workout_id": r.workout_id,
                "day_of_week": r.day_of_week,
                "position": r.position,
                "workout": workouts.get(r.workout_id),
                "exercises": items.get(r.workout_id, []),
            }
            for r in sched
        ],
    }

@router.get("/diet_plans/{plan_id}/full")
def get_diet_plan_full(plan_id: int, db: Session = Depends(get_db)):
    dp = db.query(DietPlan).filter(DietPlan.id == plan_id).first()
    if not dp:
        raise HTTPException(status_code=404, detail="Diet plan not found")
    items = db.query(MealPlanItem).filter(MealPlanItem.diet_plan_id == plan_id) \
             .order_by(MealPlanItem.position.asc(), MealPlanItem.id.asc()).all()
    return {
        "plan": {"id": dp.id, "name": dp.name, "description": dp.description},
        "items": [
            {
                "id": it.id,
                "meal_name": it.meal_name,
                "food": it.food,
                "qty": it.qty,
                "unit": it.unit,
                "calories": it.calories,
                "protein": it.protein,
                "carbs": it.carbs,
                "fats": it.fats,
                "notes": it.notes,
                "position": it.position,
            } for it in items
        ],
    }

# --- Client overview (for dashboards) ---
@router.get("/clients/{client_id}/overview")
def client_overview(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    latest_membership = (
        db.query(Membership)
          .filter(Membership.client_id == client_id)
          .order_by(Membership.created_at.desc())
          .first()
    )

    latest_generic = (
        db.query(ClientPlan, Plan)
          .join(Plan, ClientPlan.plan_id == Plan.id)
          .filter(ClientPlan.client_id == client_id)
          .order_by(ClientPlan.assigned_on.desc())
          .first()
    )

    latest_training = (
        db.query(ClientTrainingPlan, TrainingPlan)
          .join(TrainingPlan, ClientTrainingPlan.training_plan_id == TrainingPlan.id)
          .filter(ClientTrainingPlan.client_id == client_id)
          .order_by(ClientTrainingPlan.assigned_on.desc())
          .first()
    )

    latest_diet = (
        db.query(ClientDietPlan, DietPlan)
          .join(DietPlan, ClientDietPlan.diet_plan_id == DietPlan.id)
          .filter(ClientDietPlan.client_id == client_id)
          .order_by(ClientDietPlan.assigned_on.desc())
          .first()
    )

    return {
        "client": {
            "id": client.id,
            "full_name": client.full_name,
            "email": client.email,
            "phone": client.phone,
            "membership_active": client.membership_active,
        },
        "membership": (None if not latest_membership else {
            "id": latest_membership.id,
            "package_name": latest_membership.package_name,
            "price": latest_membership.price,
            "status": latest_membership.status,
            "start_date": latest_membership.start_date,
            "end_date": latest_membership.end_date,
            "renewal_due_on": latest_membership.renewal_due_on,
        }),
        "generic_plan": (None if not latest_generic else {
            "id": latest_generic[0].id,
            "assigned_on": latest_generic[0].assigned_on,
            "plan": {
                "id": latest_generic[1].id,
                "name": latest_generic[1].name,
                "type": latest_generic[1].type,
            }
        }),
        "training_plan": (None if not latest_training else {
            "id": latest_training[0].id,
            "assigned_on": latest_training[0].assigned_on,
            "plan": {
                "id": latest_training[1].id,
                "name": latest_training[1].name,
            }
        }),
        "diet_plan": (None if not latest_diet else {
            "id": latest_diet[0].id,
            "assigned_on": latest_diet[0].assigned_on,
            "plan": {
                "id": latest_diet[1].id,
                "name": latest_diet[1].name,
            }
        }),
    }

# --- Membership routes ---
@router.post("/memberships/", response_model=MembershipOut)
def create_membership(payload: MembershipIn, db: Session = Depends(get_db)):
    # ensure client exists
    if not db.query(Client).filter(Client.id == payload.client_id).first():
        raise HTTPException(status_code=404, detail="Client not found")
    obj = Membership(**payload.dict())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid membership payload")
    db.refresh(obj)
    return obj

@router.get("/memberships/{client_id}", response_model=List[MembershipOut])
def list_memberships(client_id: int, db: Session = Depends(get_db)):
    return db.query(Membership).filter(Membership.client_id == client_id).order_by(Membership.created_at.desc()).all()

@router.put("/memberships/{membership_id}", response_model=MembershipOut)
def update_membership(membership_id: int, payload: MembershipIn, db: Session = Depends(get_db)):
    obj = db.query(Membership).filter(Membership.id == membership_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Membership not found")
    for k, v in payload.dict().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/memberships/{membership_id}")
def delete_membership(membership_id: int, db: Session = Depends(get_db)):
    obj = db.query(Membership).filter(Membership.id == membership_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Membership not found")
    db.delete(obj)
    db.commit()
    return {"message": "Membership deleted"}

# --- Progress metrics ---
@router.post("/progress_metrics/", response_model=ProgressMetricOut)
def create_metric(payload: ProgressMetricIn, db: Session = Depends(get_db)):
    obj = ProgressMetric(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/progress_metrics/{client_id}", response_model=List[ProgressMetricOut])
def list_metrics(client_id: int, start: Optional[date] = None, end: Optional[date] = None, db: Session = Depends(get_db)):
    q = db.query(ProgressMetric).filter(ProgressMetric.client_id == client_id)
    if start:
        q = q.filter(ProgressMetric.date >= start)
    if end:
        q = q.filter(ProgressMetric.date <= end)
    return q.order_by(ProgressMetric.date.desc()).all()

@router.delete("/progress_metrics/{metric_id}")
def delete_metric(metric_id: int, db: Session = Depends(get_db)):
    obj = db.query(ProgressMetric).filter(ProgressMetric.id == metric_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Metric not found")
    db.delete(obj)
    db.commit()
    return {"message": "Metric deleted"}

# --- Workout log ---
@router.post("/workout_log/", response_model=WorkoutLogOut)
def create_log(payload: WorkoutLogIn, db: Session = Depends(get_db)):
    obj = WorkoutLog(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/workout_log/{client_id}", response_model=List[WorkoutLogOut])
def list_logs(client_id: int, start: Optional[date] = None, end: Optional[date] = None, db: Session = Depends(get_db)):
    q = db.query(WorkoutLog).filter(WorkoutLog.client_id == client_id)
    if start:
        q = q.filter(WorkoutLog.date >= start)
    if end:
        q = q.filter(WorkoutLog.date <= end)
    return q.order_by(WorkoutLog.date.desc()).all()

@router.delete("/workout_log/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    obj = db.query(WorkoutLog).filter(WorkoutLog.id == log_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Log not found")
    db.delete(obj)
    db.commit()
    return {"message": "Log deleted"}

# --- Diet plan items ---
@router.get("/diet_plans/{plan_id}/items", response_model=List[MealPlanItemOut])
def get_meal_items(plan_id: int, db: Session = Depends(get_db)):
    return db.query(MealPlanItem).filter(MealPlanItem.diet_plan_id == plan_id).order_by(MealPlanItem.position.asc(), MealPlanItem.id.asc()).all()

@router.put("/diet_plans/{plan_id}/items", response_model=List[MealPlanItemOut])
def set_meal_items(plan_id: int, items: List[MealPlanItemIn], db: Session = Depends(get_db)):
    db.query(MealPlanItem).filter(MealPlanItem.diet_plan_id == plan_id).delete()
    out = []
    for i, it in enumerate(items):
        rec = MealPlanItem(
            diet_plan_id=plan_id,
            meal_name=it.meal_name,
            food=it.food,
            qty=it.qty,
            unit=it.unit,
            calories=it.calories,
            protein=it.protein,
            carbs=it.carbs,
            fats=it.fats,
            notes=it.notes,
            position=it.position or i,
        )
        db.add(rec)
        out.append(rec)
    db.commit()
    for rec in out:
        db.refresh(rec)
    return out

@router.get("/stats/summary")
def stats_summary(db: Session = Depends(get_db)):
    return {
        "clients": db.query(func.count(Client.id)).scalar(),
        "plans": db.query(func.count(Plan.id)).scalar(),
        "training_plans": db.query(func.count(TrainingPlan.id)).scalar(),
        "diet_plans": db.query(func.count(DietPlan.id)).scalar(),
        "programs": db.query(func.count(Program.id)).scalar(),
    }

Base.metadata.create_all(bind=engine)
app.include_router(router, prefix="/api")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
