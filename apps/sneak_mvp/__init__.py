"""SNEAK (So Now Every Agent Knows) Secure Ship MVP. Stdlib only."""
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
APP_DIR = pathlib.Path(__file__).resolve().parent
LOCAL_RUNS = REPO_ROOT / "local-runs"
