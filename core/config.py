import yaml
import os
from pydantic import BaseModel
from typing import List, Optional

class UserProfile(BaseModel):
    # Basic personal data
    first_name: str
    last_name: str
    email: str
    phone: str
    # Address components
    street: str
    street_number: str
    zip_code: str
    city: str
    address_addition: Optional[str] = None
    # Additional personal info
    salutation: Optional[str] = None  # Anrede (Herr/Frau)
    profession: Optional[str] = None
    pets: Optional[str] = None
    wbs_holder: Optional[str] = None
    # Custom message for application letters
    custom_message: Optional[str] = None
    # Application specific fields
    number_of_persons: Optional[int] = None
    request_for_self: Optional[str] = None
    mobile_number: Optional[str] = None

class SearchCriteria(BaseModel):
    city: str
    districts: List[str]
    max_warmmiete: int
    min_area_sqm: int
    min_rooms: int
    wbs_required: str

class PlatformCredentials(BaseModel):
    gmail_client_id: str
    gmail_client_secret: str
    openai_api_key: str

class AppConfig(BaseModel):
    user_profile: UserProfile
    search_criteria: SearchCriteria
    platform_credentials: PlatformCredentials

def load_config(config_path: str = "user_config.yaml") -> AppConfig:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    return AppConfig(**data)
