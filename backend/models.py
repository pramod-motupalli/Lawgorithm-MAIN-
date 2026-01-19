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
    officer_rank: Optional[str] = "Not provided"

class QuestionnaireRequest(BaseModel):
    fir_content: str
    case_description: str
    case_description: str

class ChargeSheetRequest(BaseModel):
    fir_content: str
    case_description: str
    plaintiff_answers: dict
    defendant_answers: dict
    investigation_summary: str = ""
    officer_name: str
    officer_rank: str
    police_station: str
    police_station: str

class VerdictRequest(BaseModel):
    charge_sheet_content: str
    case_description: str
    case_description: str
