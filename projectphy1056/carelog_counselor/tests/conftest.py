# tests/conftest.py
import sys
from pathlib import Path
import pytest

# --- Make the project importable ------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from counselor_name_app.repository import Repo, DATA_FILE  # noqa


@pytest.fixture(autouse=True)
def patch_repo_to_tmp(monkeypatch, tmp_path):
    """
    Force ALL Repo() instances to read/write under a temp folder:
      <tmp>/FIT1056-GROUP/data/counselor_data.json

    We replace Repo.__init__ so we don't rely on any private root-finding.
    """
    fake_root = tmp_path / "FIT1056-GROUP"
    data_dir = fake_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Keep references to original methods we still need
    orig_seed = Repo._seed
    orig_load = Repo._load

    def fake_init(self, *args, **kwargs):
        self.base = fake_root
        self.data_dir = data_dir
        self.file = self.data_dir / DATA_FILE
        if not self.file.exists():
            orig_seed(self)
        self._cache = orig_load(self)

    monkeypatch.setattr(Repo, "__init__", fake_init, raising=False)
    yield  # tests run with patched Repo
    # teardown: monkeypatch fixture will auto-restore


@pytest.fixture
def tmp_repo() -> Repo:
    """Returns a fresh Repo that points at the patched temp root."""
    return Repo()


@pytest.fixture
def ids():
    return {"counselor": "C0001", "patient": "P0001"}
