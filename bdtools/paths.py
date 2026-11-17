"""Where things live in the repository."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
# The instructor can preview a library built elsewhere by setting these environment variables.
REFERENCE_DIR = Path(os.environ.get("BDTOOLS_REFERENCE_DIR", DATA_DIR / "references"))
MODEL_DIR = Path(os.environ.get("BDTOOLS_MODEL_DIR", DATA_DIR / "models"))
TOY_DIR = DATA_DIR / "toy"
INDICES_FILE = DATA_DIR / "indices.yaml"
BANDS_FILE = DATA_DIR / "bands.yaml"
FIELD_GUIDE_DIR = REPO_ROOT / "field_guide"
