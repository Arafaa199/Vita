from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from db import SessionLocal, Base, engine
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

router = APIRouter()

# SQLAlchemy model
class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    type = Column(String(20))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

# Create the table if not exists
Base.metadata.create_all(bind=engine)

# Pydantic models
class PlanIn(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = None

class PlanOut(PlanIn):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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