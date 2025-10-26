# counselor_name_app/repository.py
from __future__ import annotations
import json, os, time, shutil
from pathlib import Path
from typing import Any, Dict
from tempfile import NamedTemporaryFile

DATA_FILE = "counselor_data.json"

def _project_root() -> Path:
    # repository.py lives at: <project>/counselor_name_app/repository.py
    # project root should be two levels up from here
    return Path(__file__).resolve().parents[2]

def _preferred_data_dir() -> Path:
    # 1) Environment override
    env = os.environ.get("CARELOG_DATA_DIR")
    if env:
        return Path(env)

    # 2) Use a /data folder inside your project (stable + not synced by OneDrive by default)
    return _project_root() / "data"

def _possible_legacy_paths() -> list[Path]:
    # Try to detect the legacy OneDrive Pictures\data path that caused the lock
    home = Path.home()
    candidates = []
    # Common OneDrive naming patterns; harmless if they don't exist
    candidates.append(home / "OneDrive - Sunway Education Group" / "Pictures" / "data")
    candidates.append(home / "OneDrive" / "Pictures" / "data")
    candidates.append(home / "Pictures" / "data")
    return candidates

class Repo:
    """
    JSON-backed repo with safe atomic-ish writes and Windows-friendly retries.

    Data layout (single file):
    {
      "users": {...},
      "patients": {...},
      "appointments": {...},
      "notes": {...},
      "safety_plans": {...},
      "messages": {...},   # threads
      "consent": {...},
      "assessments": {...},
      "audit": []
    }
    """
    def __init__(self):
        self.data_dir = _preferred_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file = self.data_dir / DATA_FILE

        # One-time migration from legacy locations (e.g., OneDrive Pictures/data) if needed
        if not self.file.exists():
            for legacy_dir in _possible_legacy_paths():
                legacy_file = legacy_dir / DATA_FILE
                if legacy_file.exists():
                    try:
                        legacy_dir.mkdir(parents=True, exist_ok=True)  # ensure path ok
                        shutil.copy2(legacy_file, self.file)
                        break
                    except Exception:
                        # If copy fails, we'll just seed a new file below
                        pass

        if not self.file.exists():
            self._seed()

        self._cache: Dict[str, Any] = self._load()

    # ---------------- internal helpers ----------------
    def _seed(self):
        seed = {
            "users": {
                # Default counselor account
                "C0001": {
                    "id": "C0001", "role": "counselor",
                    "name": "Aisha Wong", "email": "aisha@medilink.example",
                    "license": "CN-45821", "specialties": ["Anxiety", "Depression"],
                    "hours": "Mon–Fri 09:00–17:00", "contact": "+60 12-345 6789",
                    "password": "password123", "failed": 0, "locked": False
                },
                # Staff directory (for messaging)
                "A0001": {"id":"A0001","role":"admin","name":"Clinic Admin","email":"admin@carelog.example","password":"admin"},
                "N0001": {"id":"N0001","role":"nurse","name":"Nurse Farah","email":"farah@carelog.example","password":"nurse"},
                "D0001": {"id":"D0001","role":"doctor","name":"Dr. Kumar","email":"kumar@carelog.example","password":"doctor"},
                "M0001": {"id":"M0001","role":"medstaff","name":"Med Tech Lim","email":"lim@carelog.example","password":"medstaff"},
            },
            "patients": {
                "P0001": {
                    "id":"P0001","name":"Nicole Tan","dob":"1960-02-19",
                    "assigned_counselor":"C0001","language":"EN",
                    "risk_flags":["falls"], "allergies":["Penicillin"]
                }
            },
            "appointments": {},
            "notes": {},
            "safety_plans": {},
            "messages": {},           # {thread_id:{title, members, items, reads}}
            "consent": {"P0001":{"C0001": True}},
            "assessments": {},
            "audit": []
        }
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.file, "w", encoding="utf-8", newline="\n") as f:
            json.dump(seed, f, indent=2)

    def _load(self) -> Dict[str, Any]:
        with open(self.file, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---------------- public API ----------------
    def read(self) -> Dict[str, Any]:
        # return cached object (mutated by services), which we persist via write()
        return self._cache

    def write(self, data: Dict[str, Any]):
        """
        Robust Windows-safe write:
        - Write to a NamedTemporaryFile in the same directory
        - Flush + fsync
        - Retry os.replace up to N times to bypass OneDrive locks
        """
        # 1) Write to temp file in same directory
        with NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=self.data_dir, delete=False) as tmp:
            json.dump(data, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)

        # 2) Try replacing with retries (handles transient locks)
        attempts = 10
        last_err: Exception | None = None
        for i in range(attempts):
            try:
                # On Windows, os.replace is atomic and can overwrite existing files
                os.replace(str(tmp_path), str(self.file))
                last_err = None
                break
            except PermissionError as e:
                last_err = e
                time.sleep(0.25)  # brief backoff
            except OSError as e:
                # Other transient errors (e.g., antivirus/OneDrive scanning)
                last_err = e
                time.sleep(0.25)

        # Clean up temp file if replace didn’t happen
        if tmp_path.exists():
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                # ignore cleanup failure
                pass

        if last_err is not None:
            # As a final fallback, write directly (non-atomic) — better than losing data
            try:
                with open(self.file, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(data, f, indent=2)
                last_err = None
            except Exception as e:
                last_err = e

        if last_err is not None:
            # Bubble up with a clearer hint
            raise PermissionError(
                f"Unable to write data file at {self.file}. "
                f"If this path is inside OneDrive, set CARELOG_DATA_DIR to a local folder (e.g., your project/data). "
                f"Root cause: {last_err}"
            )

        # 3) Update in-memory cache
        self._cache = data
