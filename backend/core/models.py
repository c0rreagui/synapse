from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True) # e.g. "tiktok_profile_01" (legacy key) or "username"
    username = Column(String, unique=True, index=True)
    label = Column(String)
    icon = Column(String, default="👤")
    type = Column(String, default="cuts") # 'main' or 'cuts'
    active = Column(Boolean, default=True)
    avatar_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    
    # JSON columns for flexible data
    oracle_best_times = Column(JSON, default=list) # List of dicts
    last_seo_audit = Column(JSON, default=dict) # The BIG audit object
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Future relations
    # audits = relationship("Audit", back_populates="profile")

class Audit(Base):
    """
    Stores historical audits for trending/analytics over time.
    Separated from the main profile to keep history.
    """
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON) # The full audit result snapshot
    score = Column(Integer) # Quick access to total score

    # profile = relationship("Profile", back_populates="audits")

class ScheduleItem(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, index=True)
    profile_slug = Column(String, index=True) # Linking loosely to profile for now to ease migration
    video_path = Column(String)
    scheduled_time = Column(DateTime)
    status = Column(String, default="pending") # pending, posted, failed
    metadata_info = Column(JSON, default=dict) # Title, caption, tags
    
