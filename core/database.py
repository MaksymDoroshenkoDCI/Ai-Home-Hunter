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

class EmailContact(Base):
    __tablename__ = 'email_contacts'
    id = Column(Integer, primary_key=True)
    company_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    website = Column(String, nullable=True)
    last_contacted = Column(DateTime, nullable=True)
    status = Column(String, default='not_sent')  # not_sent, sent, replied, bounced

    def __repr__(self):
        return f"<EmailContact {self.company_name} {self.email}>"

def init_db(database_url="sqlite:///ai_home_hunter.db"):
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
