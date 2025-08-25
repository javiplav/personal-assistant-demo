from pathlib import Path

# repo_root/.../src/personal_assistant/tools/_paths.py
# DATA_DIR points to <repo_root>/data
DATA_DIR = Path(__file__).resolve().parents[3] / "data"

def data_path(name: str) -> Path:
    """Return an absolute, normalized path under the repo /data folder."""
    p = (DATA_DIR / name).resolve()
    # hard stop if traversal escapes /data
    if DATA_DIR not in p.parents and p != DATA_DIR:
        raise ValueError(f"Unsafe path outside /data: {p}")
    return p
