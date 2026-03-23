from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

class Apartment(Base):
    __tablename__ = 'apartments'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String)
    url = Column(String, unique=True)
    address = Column(String)
    warmmiete = Column(Float)
    kaltmiete = Column(Float)
    area_sqm = Column(Float)
    rooms = Column(Float)
    wbs_required = Column(Boolean)
    status = Column(String) # 'found', 'applied', 'failed_to_apply', 'invited', 'booked'
    found_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)

# Initialization function
def init_db(database_url="sqlite:///ai_home_hunter.db"):
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
