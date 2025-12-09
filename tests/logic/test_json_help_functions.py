import json
from pathlib import Path
from unittest.mock import patch
import pytest

from scheduler.logic.json_help_functions import _load_json, _save_json_with_lock


def test_load_json_reads_file(tmp_path):
    p = tmp_path / "config.json"
    p.write_text('{"a": 1}', encoding="utf-8")

    result = _load_json(p)
    assert result == {"a": 1}


def test_load_json_missing_file_raises(tmp_path):
    p = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        _load_json(p)


def test_save_json_with_lock_writes_and_replaces(tmp_path):
    p = tmp_path / "data.json"

    with patch("portalocker.lock"), patch("portalocker.unlock"):
        _save_json_with_lock(p, {"x": 2})

    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data == {"x": 2}


def test_save_json_creates_backup_if_exists(tmp_path):
    p = tmp_path / "config.json"
    p.write_text('{"old": 1}', encoding="utf-8")

    with patch("portalocker.lock"), patch("portalocker.unlock"):
        _save_json_with_lock(p, {"new": 2})

    backups = list(tmp_path.glob("config.json.bak-*"))
    assert len(backups) == 1

    data = json.loads(p.read_text(encoding="utf-8"))
    assert data == {"new": 2}
