# admin_name_core/reporting.py
from __future__ import annotations
from datetime import datetime
from collections import defaultdict
from typing import Any, Dict, Optional

def _parse_iso_any(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        # accept both "...Z" and local ISO
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

def monthly_billing(
    db: Dict[str, Any],
    *,
    only_paid: bool = False,
    use_paid_date: bool = False,
) -> Dict[str, float]:
    """
    Sum invoice totals per YYYY-MM month.

    - Looks for timestamps in this order (unless use_paid_date=True):
        created_at -> issued_at -> paid_at
      If use_paid_date=True, prefer paid_at first.
    - If only_paid=True, include only invoices that look paid:
        status == 'paid' OR paid == True OR has paid_at
    - Returns a dict sorted by YYYY-MM.
    """
    out = defaultdict(float)

    for inv in db.get("invoices", []):
        # Filter to paid, if requested
        if only_paid:
            status = (inv.get("status") or "").lower()
            paid_flag = bool(inv.get("paid"))
            paid_at = inv.get("paid_at")
            if status != "paid" and not paid_flag and not paid_at:
                continue

        # Choose a date for bucketing
        if use_paid_date:
            dt = (
                _parse_iso_any(inv.get("paid_at"))
                or _parse_iso_any(inv.get("created_at"))
                or _parse_iso_any(inv.get("issued_at"))
            )
        else:
            dt = (
                _parse_iso_any(inv.get("created_at"))
                or _parse_iso_any(inv.get("issued_at"))
                or _parse_iso_any(inv.get("paid_at"))
            )

        if not dt:
            continue

        key = f"{dt.year:04d}-{dt.month:02d}"
        try:
            amt = float(inv.get("total", 0) or 0)
        except Exception:
            amt = 0.0

        out[key] += amt

    # Return a normal dict with months sorted
    return dict(sorted(out.items()))
