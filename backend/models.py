from pydantic import BaseModel
from typing import Optional

class ComplainantDetails(BaseModel):
    name: Optional[str] = "Not provided"
    address: Optional[str] = "Not provided"
    contact: Optional[str] = "Not provided"

class AccusedDetails(BaseModel):
    name: Optional[str] = "Unknown person(s)"
    address: Optional[str] = "Not provided"

class FIRRequest(BaseModel):
    case_description: str
    complainant: ComplainantDetails
    accused: Optional[AccusedDetails] = None
    date_time_place: Optional[str] = "Not provided"
    
    # Official Details
    police_station: Optional[str] = "Not provided"
    fir_number: Optional[str] = "Not provided"
    registration_date: Optional[str] = "Not provided"
    officer_name: Optional[str] = "Not provided"
    officer_rank: Optional[str] = "Not provided"
