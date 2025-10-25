from .data_store import DataStore

def log(action: str, target: str = "", extra: dict | None = None):
    DataStore().audit(action, target, extra)