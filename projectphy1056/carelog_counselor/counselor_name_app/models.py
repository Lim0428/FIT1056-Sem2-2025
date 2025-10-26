from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Counselor:
    id: str
    name: str
    email: str
    license: str
    specialties: List[str]
    hours: str
    contact: str

@dataclass
class Patient:
    id: str
    name: str
    dob: str
    assigned_counselor: Optional[str] = None
    language: str = "EN"
    risk_flags: List[str] = field(default_factory=list)
