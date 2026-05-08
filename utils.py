"""Utility functions for the enrollment manager."""

import json
from pathlib import Path
from typing import Any

from config import SNAPSHOT_PATH


def export_database_snapshot(snapshot: dict[str, Any], path: Path = SNAPSHOT_PATH) -> None:
    """Export enrollment snapshot to JSON file."""
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
