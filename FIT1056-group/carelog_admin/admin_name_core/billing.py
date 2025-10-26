# admin_name_core/billing.py
from typing import List, Dict
from admin_name_utils.storage import next_id, now_iso

def create_invoice(db, patient_id: int, items: List[Dict]):
    inv_id = next_id(db["invoices"])
    total = sum(float(x["amount"]) for x in items)
    invoice = {
        "id": inv_id,
        "patient_id": patient_id,
        "items": items,
        "total": total,
        "paid": 0.0,
        "created_at": now_iso()
    }
    db["invoices"].append(invoice)
    return invoice

def add_payment(invoice: Dict, amount: float):
    invoice["paid"] = round(float(invoice.get("paid", 0.0)) + float(amount), 2)

def outstanding(invoice: Dict) -> float:
    return round(float(invoice["total"]) - float(invoice.get("paid", 0.0)), 2)
