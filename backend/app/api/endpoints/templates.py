from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import PromptTemplate
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    content: str
    category: str = "General"

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_favorite: Optional[bool] = None

class TemplateResponse(BaseModel):
    id: int
    name: str
    content: str
    category: str
    is_favorite: bool
    created_at: datetime

    class Config:
        orm_mode = True

@router.get("/list", response_model=List[TemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    return db.query(PromptTemplate).order_by(PromptTemplate.created_at.desc()).all()

@router.post("/create", response_model=TemplateResponse)
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    try:
        db_template = PromptTemplate(
            name=template.name, 
            content=template.content, 
            category=template.category
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
    except Exception as e:
        print(f"ERROR CREATING TEMPLATE: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{template_id}", response_model=TemplateResponse)
def update_template(template_id: int, update_data: TemplateUpdate, db: Session = Depends(get_db)):
    db_template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(db_template, key, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    db_template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(db_template)
    db.commit()
    return {"message": "Template deleted"}
