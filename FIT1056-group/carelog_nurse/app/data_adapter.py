# carelog_nurse/app/data_adapter.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

# ----------------- generic loaders / normalizers -----------------
def _load_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
            return obj if obj is not None else default
    except Exception:
        return default

def _to_list(obj) -> list:
    """Normalize dict-or-list JSON into a list (preserving values for dicts)."""
    if isinstance(obj, dict):
        # Stable order by key
        return [obj[k] for k in sorted(obj.keys())]
    if isinstance(obj, list):
        return obj
    return []

def _as_list_of_dicts(obj) -> list[dict]:
    """Return only dict items from a dict/list JSON payload."""
    return [x for x in _to_list(obj) if isinstance(x, dict)]

def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _parse_ts(ts: Any) -> datetime | None:
    """Parse many common timestamp shapes into a datetime (UTC)."""
    if not ts:
        return None
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(ts, str):
        s = ts.strip()
        try:
            # Accept 'Z' or '+00:00'
            if s.endswith("Z"):
                s = s.replace("Z", "+00:00")
            return datetime.fromisoformat(s).astimezone(timezone.utc)
        except Exception:
            # Try YYYY-MM-DD HH:MM or YYYY-MM-DD
            try:
                return datetime.strptime(ts[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except Exception:
                try:
                    return datetime.strptime(ts[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except Exception:
                    return None
    return None

def _local_date(dt_utc: datetime) -> datetime.date:
    # If you need strict Asia/Kuala_Lumpur handling, you could shift here.
    # For now treat system-local date; dt_utc is already UTC.
    return dt_utc.date()

# ----------------- adapter -----------------
class DataAdapter:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR

    # ---- raw collections (normalized to list[dict]) ----
    def patients(self) -> list[dict]:
        return _as_list_of_dicts(_load_json(self.data_dir / "patients.json", []))

    def doctors(self) -> list[dict]:
        return _as_list_of_dicts(_load_json(self.data_dir / "doctors.json", []))

    def encounters(self) -> list[dict]:
        return _as_list_of_dicts(_load_json(self.data_dir / "encounters.json", []))

    def messages(self) -> list[dict]:
        return _as_list_of_dicts(_load_json(self.data_dir / "messages.json", []))

    def tasks(self) -> list[dict]:
        return _as_list_of_dicts(_load_json(self.data_dir / "tasks.json", []))

    def notifications(self) -> list[dict]:
        return _as_list_of_dicts(_load_json(self.data_dir / "notifications.json", []))

    def vitals(self) -> list[dict]:
        return _as_list_of_dicts(_load_json(self.data_dir / "vitals.json", []))

    def mar(self) -> list[dict]:
        meds = _load_json(self.data_dir / "medications.json", [])
        return _as_list_of_dicts(meds)

    def notes(self) -> list[dict]:
        return _as_list_of_dicts(_load_json(self.data_dir / "notes.json", []))

    def appointments(self) -> list[dict]:
        """
        Load appointments from data/appointments.json (list or dict).
        Expected fields (tolerant):
          - patient_id
          - start or time (ISO); optional end
          - type (e.g., Consultation)
          - status (optional)
        """
        return _as_list_of_dicts(_load_json(self.data_dir / "appointments.json", []))

    # ---- analytics helpers (APPOINTMENTS-BASED) ----
    def appointments_monthly_series(self) -> list[tuple[str, int, str]]:
        """
        Returns [(YYYY-MM, count, Type)] from appointments.json.
        If no 'type', uses 'All'.
        """
        bucket = defaultdict(int)
        for a in self.appointments():
            ts = a.get("start") or a.get("time") or a.get("date")
            dt = _parse_ts(ts)
            if not dt:
                continue
            month = f"{dt.year:04d}-{dt.month:02d}"
            kind = (a.get("type") or "All").title()
            bucket[(month, kind)] += 1
        rows = [(m, c, t) for (m, t), c in bucket.items()]
        rows.sort(key=lambda x: x[0])
        return rows

    def today_appointments(self) -> list[dict]:
        """
        Appointments occurring today (by local date) from appointments.json.
        Keeps raw rows but guarantees keys: patient_id, start, type.
        """
        today = datetime.now().date()
        out = []
        for a in self.appointments():
            ts = a.get("start") or a.get("time") or a.get("date")
            dt = _parse_ts(ts)
            if not dt:
                continue
            if _local_date(dt) == today:
                row = dict(a)  # copy
                # normalize minimal fields for the dashboard table
                row.setdefault("patient_id", a.get("patient") or a.get("pid") or "")
                row.setdefault("start", ts)
                row.setdefault("type", a.get("type") or "Consultation")
                out.append(row)
        # sort by time
        out.sort(key=lambda r: r.get("start",""))
        return out

    def patient_list_today(self) -> list[dict]:
        """
        Unique patient list for today from appointments.json with first time.
        Returns [{'id': pid, 'name': ..., 'time': 'HH:MM'}]
        """
        pts = { (p.get("id") or p.get("patient_id")): p for p in self.patients() if isinstance(p, dict) }
        seen = {}
        for a in self.today_appointments():
            pid = a.get("patient_id") or a.get("pid") or ""
            ts = a.get("start") or a.get("time") or ""
            if not pid or not ts:
                continue
            if pid not in seen or ts < seen[pid]["raw"]:
                name = pts.get(pid, {}).get("name") or pts.get(pid, {}).get("full_name") or pid
                seen[pid] = {
                    "id": pid,
                    "name": name,
                    "time": (ts[11:16] if "T" in ts else ts[11:16] if len(ts) >= 16 else ts),
                    "raw": ts
                }
        return list(seen.values())

    # ---- legacy (kept for other parts that may still use encounters) ----
    def monthly_visit_series(self) -> list[tuple[str, int, str]]:
        """
        (Legacy) Encounters per month grouped by patient sex.
        """
        pts_list = self.patients()
        pts = {}
        for p in pts_list:
            pid = p.get("id") or p.get("patient_id")
            if pid:
                pts[pid] = p

        encs = self.encounters()
        bucket = defaultdict(int)  # (month, sex) -> count

        for e in encs:
            pid = e.get("patient_id") or e.get("pid") or e.get("id")
            ts = e.get("ts") or e.get("time") or e.get("date")
            dt = _parse_ts(ts)
            if not dt:
                continue
            month = f"{dt.year:04d}-{dt.month:02d}"
            sex = "Unknown"
            if pid in pts:
                sex = (pts[pid].get("gender") or pts[pid].get("sex") or "Unknown").title()
            bucket[(month, sex)] += 1

        rows = [(m, c, s) for (m, s), c in bucket.items()]
        rows.sort(key=lambda x: x[0])
        return rows

    # ---- KPI rollup for dashboards ----
    def counts_for_kpis(self) -> dict[str, int]:
        """
        Return a dict with common dashboard KPIs.

        Keys:
          - patients: total patients
          - tasks_pending: tasks with status 'pending' (or not completed)
          - unread_alerts: notifications/messages marked unread
          - recent_entries_7d: count of vitals/MAR/notes in last 7 days
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=7)

        # patients
        patients_cnt = len(self.patients())

        # tasks pending
        t_pending = 0
        for t in self.tasks():
            status = (t.get("status") or "").lower()
            if status in ("pending", "open", ""):
                t_pending += 1

        # unread alerts: from notifications + messages where read is False / "unread" / missing
        unread = 0
        for n in self.notifications():
            read = n.get("read")
            status = (n.get("status") or "").lower()
            if (read is False) or (status in ("new", "unread")) or (read is None and status == ""):
                unread += 1
        for m in self.messages():
            read = m.get("read")
            status = (m.get("status") or "").lower()
            if (read is False) or (status in ("new", "unread")):
                unread += 1

        # recent entries across clinical streams (vitals, MAR, notes)
        def _recent_count(rows: Iterable[dict]) -> int:
            c = 0
            for r in rows:
                dt = _parse_ts(r.get("ts") or r.get("time") or r.get("date") or r.get("taken_at"))
                if dt and dt >= cutoff:
                    c += 1
            return c

        recent = _recent_count(self.vitals()) + _recent_count(self.mar()) + _recent_count(self.notes())

        return {
            "patients": patients_cnt,
            "tasks_pending": t_pending,
            "unread_alerts": unread,
            "recent_entries_7d": recent,
        }

    # ---- Patient gender breakdown (used by donut) ----
    def patient_gender_breakdown(self) -> dict[str, int]:
        out = defaultdict(int)
        for p in self.patients():
            g = (p.get("gender") or p.get("sex") or "Unknown").title()
            out[g] += 1
        return dict(out)
