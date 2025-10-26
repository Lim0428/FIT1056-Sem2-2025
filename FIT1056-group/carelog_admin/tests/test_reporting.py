# tests/test_reporting.py
from datetime import datetime
from admin_name_core.reporting import monthly_billing

def test_monthly_billing_sums_by_year_month(fake_db):
    db = fake_db
    db["invoices"] = [
        {"id":1, "total": 100.0, "created_at":"2025-01-15T10:00:00Z"},
        {"id":2, "total": 250.0, "created_at":"2025-01-30T10:00:00Z"},
        {"id":3, "total": 110.0, "created_at":"2025-02-01T10:00:00Z"},
        {"id":4, "total":  50.0, "created_at":"2024-12-31T23:00:00Z"},
    ]
    out = monthly_billing(db)
    assert out["2025-01"] == 350.0
    assert out["2025-02"] == 110.0
    assert out.get("2024-12") == 50.0
