# counselor_name_app/services/notes.py
from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from counselor_name_app.repository import Repo

class NotesService:
    def __init__(self, repo: Optional[Repo]=None):
        self.repo = repo or Repo()

    # ---------- CRUD ----------
    def list_notes(self, patient_id: str) -> List[Dict]:
        db = self.repo.read()
        notes = [n for n in db.get("notes", {}).values() if n.get("patient_id") == patient_id]
        notes.sort(key=lambda x: (x.get("ts","")), reverse=True)
        return notes

    def get(self, note_id: str) -> Optional[Dict]:
        return self.repo.read().get("notes", {}).get(note_id)

    def create(self, patient_id: str, counselor_id: str, template: str, title: str, content: Dict, meta: Dict | None=None):
        db = self.repo.read()
        nid = "N-" + uuid4().hex[:8]
        now = datetime.now().isoformat(timespec="seconds")
        note = {
            "id": nid,
            "patient_id": patient_id,
            "counselor_id": counselor_id,
            "template": template,            # "SOAP" | "DARE"
            "title": title.strip() or f"{template} note",
            "content": content,              # dict of sections
            "meta": meta or {},              # encounter, tags, risk, etc.
            "ts": now,                       # created
            "updated_ts": now,
            "version": 1
        }
        db.setdefault("notes", {})[nid] = note
        db.setdefault("audit", []).append({"event":"note_create","note":nid,"patient":patient_id,"by":counselor_id})
        self.repo.write(db)
        return note

    def update(self, note_id: str, patch: Dict) -> Optional[Dict]:
        db = self.repo.read()
        note = db.get("notes", {}).get(note_id)
        if not note:
            return None
        # version bump
        note["version"] = int(note.get("version", 1)) + 1
        note["updated_ts"] = datetime.now().isoformat(timespec="seconds")
        # shallow merge for content/meta/title/template
        for k in ("title","template"):
            if k in patch: note[k] = patch[k]
        if "content" in patch and isinstance(patch["content"], dict):
            note["content"] = patch["content"]
        if "meta" in patch and isinstance(patch["meta"], dict):
            m = note.get("meta", {})
            m.update(patch["meta"])
            note["meta"] = m
        db["notes"][note_id] = note
        db.setdefault("audit", []).append({"event":"note_update","note":note_id})
        self.repo.write(db)
        return note

    def delete(self, note_id: str) -> bool:
        db = self.repo.read()
        if note_id in db.get("notes", {}):
            db["notes"].pop(note_id, None)
            db.setdefault("audit", []).append({"event":"note_delete","note":note_id})
            self.repo.write(db)
            return True
        return False

    def duplicate(self, note_id: str, counselor_id: str) -> Optional[Dict]:
        src = self.get(note_id)
        if not src: return None
        return self.create(
            patient_id=src["patient_id"],
            counselor_id=counselor_id,
            template=src["template"],
            title=f"{src['title']} (copy)",
            content=src["content"],
            meta=src.get("meta", {})
        )
