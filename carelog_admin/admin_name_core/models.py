# admin_name_core/models.py
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class Staff:
    id: int
    name: str
    email: str
    role: str  # admin | doctor | nurse | staff
    specialization: Optional[str] = None
    qualifications: Optional[str] = None
    availability: Optional[str] = None  # e.g., "Mon-Fri 09:00-17:00"

@dataclass
class Patient:
    id: int
    name: str
    dob: str
    contact: str
    notes: Optional[str] = ""

@dataclass
class Room:
    id: int
    type: str
    occupied_by: Optional[int] = None  # patient id

@dataclass
class Appointment:
    id: int
    patient_id: int
    doctor_id: int
    start_iso: str
    end_iso: str
    status: str  # booked | cancelled | completed

@dataclass
class InvoiceItem:
    description: str
    amount: float

@dataclass
class Invoice:
    id: int
    patient_id: int
    items: List[InvoiceItem]
    total: float
    paid: float
    created_at: str
