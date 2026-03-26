from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from core.database import get_db
from sqlalchemy.orm import Session
from core.models import Army, Profile

router = APIRouter()

class ProfileMinimal(BaseModel):
    id: int
    slug: str
    username: Optional[str]
    label: Optional[str]
    avatar_url: Optional[str]

class ArmyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#00f0ff"
    icon: Optional[str] = "swords"
    profile_ids: List[int] = []

class ArmyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    profile_ids: Optional[List[int]] = None

class ArmyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    icon: str
    profiles: List[ProfileMinimal] = []

@router.get("/", response_model=List[ArmyResponse])
@router.get("", response_model=List[ArmyResponse], include_in_schema=False)
def list_armies(db: Session = Depends(get_db)):
    armies = db.query(Army).all()
    out = []
    for a in armies:
        out.append(ArmyResponse(
            id=a.id,
            name=a.name,
            description=a.description,
            color=a.color,
            icon=a.icon,
            profiles=[ProfileMinimal(id=p.id, slug=p.slug, username=p.username, label=p.label, avatar_url=p.avatar_url) for p in a.profiles]
        ))
    return out

@router.post("/", response_model=ArmyResponse)
@router.post("", response_model=ArmyResponse, include_in_schema=False)
def create_army(schema: ArmyCreate, db: Session = Depends(get_db)):
    db_army = Army(
        name=schema.name,
        description=schema.description,
        color=schema.color,
        icon=schema.icon
    )
    if schema.profile_ids:
        profiles = db.query(Profile).filter(Profile.id.in_(schema.profile_ids)).all()
        db_army.profiles = profiles
        
    db.add(db_army)
    db.commit()
    db.refresh(db_army)
    
    return ArmyResponse(
        id=db_army.id,
        name=db_army.name,
        description=db_army.description,
        color=db_army.color,
        icon=db_army.icon,
        profiles=[ProfileMinimal(id=p.id, slug=p.slug, username=p.username, label=p.label, avatar_url=p.avatar_url) for p in db_army.profiles]
    )

@router.put("/{army_id}", response_model=ArmyResponse)
def update_army(army_id: int, schema: ArmyUpdate, db: Session = Depends(get_db)):
    db_army = db.query(Army).filter(Army.id == army_id).first()
    if not db_army:
        raise HTTPException(status_code=404, detail="Army not found")

    if schema.name is not None:
        db_army.name = schema.name
    if schema.description is not None:
        db_army.description = schema.description
    if schema.color is not None:
        db_army.color = schema.color
    if schema.icon is not None:
        db_army.icon = schema.icon
        
    if schema.profile_ids is not None:
        profiles = db.query(Profile).filter(Profile.id.in_(schema.profile_ids)).all()
        db_army.profiles = profiles

    db.commit()
    db.refresh(db_army)

    return ArmyResponse(
        id=db_army.id,
        name=db_army.name,
        description=db_army.description,
        color=db_army.color,
        icon=db_army.icon,
        profiles=[ProfileMinimal(id=p.id, slug=p.slug, username=p.username, label=p.label, avatar_url=p.avatar_url) for p in db_army.profiles]
    )

@router.delete("/{army_id}")
def delete_army(army_id: int, db: Session = Depends(get_db)):
    db_army = db.query(Army).filter(Army.id == army_id).first()
    if not db_army:
        raise HTTPException(status_code=404, detail="Army not found")
    
    db.delete(db_army)
    db.commit()
    return {"message": "Army deleted"}
