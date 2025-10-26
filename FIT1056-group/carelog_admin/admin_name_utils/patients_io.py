# admin_name_utils/patients_io.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
from admin_name_utils.storage import (
    load_patients_file, save_patients_file, patients_file_to_app_list, patients_file_path
)

def list_patients() -> Dict[str, Dict[str, Any]]:
    """Return the strict dict from data/patients.json (plural)."""
    return load_patients_file()

def get_patient(key: str) -> Optional[Dict[str, Any]]:
    return list_patients().get(str(key))

def upsert_patient(rec: Dict[str, Any]) -> None:
    data = list_patients()
    key = rec.get("id") or rec.get("code")
    if not key:
        raise ValueError("Patient record must include 'id' (e.g., P000123).")
    data[str(key)] = rec
    save_patients_file(data)

def to_app_list() -> List[Dict[str, Any]]:
    return patients_file_to_app_list(list_patients())
