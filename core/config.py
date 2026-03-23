import yaml
import os
from pydantic import BaseModel
from typing import List, Optional

class UserProfile(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    current_address: str
    net_income: int
    household_size: int
    profession: str
    pets: str
    wbs_holder: str

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
