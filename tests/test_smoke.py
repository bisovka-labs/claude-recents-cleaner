"""Smoke tests for clean-claude-recents.py.

Tests run the script as a subprocess with HOME pointed at a tmp_path, so the
script sees a fake `claude-code-sessions/` directory and writes its backup
tarball into the tmp dir. No real Claude install or user state is touched.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "clean-claude-recents.py"


def sessions_dir_for(home: Path) -> Path:
    """Mirror clean-claude-recents.py:sessions_root() for tests."""
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Claude" / "claude-code-sessions"
    if system == "Linux":
        return home / ".config" / "Claude" / "claude-code-sessions"
    if system == "Windows":
        # On Windows the script uses %APPDATA%; for tests we override it.
        return home / "AppData" / "Roaming" / "Claude" / "claude-code-sessions"
    raise RuntimeError(f"Unsupported platform: {system}")


def write_session(sessions_dir: Path, uuid: str, *, cwd: str, title: str,
                  last_activity_ms: float) -> Path:
    """Create a fake local_<uuid>.json file in a nested org/user subdir."""
    nested = sessions_dir / "org-fake" / "user-fake"
    nested.mkdir(parents=True, exist_ok=True)
    path = nested / f"local_{uuid}.json"
    path.write_text(json.dumps({
        "cwd": cwd,
        "title": title,
        "lastActivityAt": last_activity_ms,
        "createdAt": last_activity_ms,
        "model": "claude-opus-4-7",
    }))
    return path


def run_script(home: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "APPDATA": str(home / "AppData" / "Roaming")}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        env=env, capture_output=True, text=True, timeout=30,
    )


def test_no_sessions_dir(tmp_path: Path) -> None:
    """When the sessions directory doesn't exist, the script exits 0 cleanly."""
    r = run_script(tmp_path)
    assert r.returncode == 0
    assert "not found" in r.stdout.lower() or "nothing to clean" in r.stdout.lower()


def test_dry_run_identifies_stale_but_does_not_delete(tmp_path: Path) -> None:
    sessions = sessions_dir_for(tmp_path)
    sessions.mkdir(parents=True)
    now_ms = time.time() * 1000

    alive_dir = tmp_path / "alive-project"
    alive_dir.mkdir()
    alive = write_session(sessions, "alive", cwd=str(alive_dir),
                          title="alive", last_activity_ms=now_ms)
    ghost = write_session(sessions, "ghost", cwd=str(tmp_path / "ghost-project"),
                          title="ghost", last_activity_ms=now_ms)

    r = run_script(tmp_path, "--dry-run")
    assert r.returncode == 0, r.stderr
    assert "stale folder (remove):  1" in r.stdout
    # Both files still on disk after dry-run.
    assert alive.exists()
    assert ghost.exists()


def test_removes_stale_folder_session_and_keeps_alive(tmp_path: Path) -> None:
    sessions = sessions_dir_for(tmp_path)
    sessions.mkdir(parents=True)
    now_ms = time.time() * 1000

    alive_dir = tmp_path / "alive-project"
    alive_dir.mkdir()
    alive = write_session(sessions, "alive", cwd=str(alive_dir),
                          title="alive", last_activity_ms=now_ms)
    ghost = write_session(sessions, "ghost", cwd=str(tmp_path / "ghost-project"),
                          title="ghost", last_activity_ms=now_ms)

    r = run_script(tmp_path, "--force")
    assert r.returncode == 0, r.stderr
    assert alive.exists()
    assert not ghost.exists()
    # A backup tarball was created in HOME.
    tarballs = list(tmp_path.glob("claude-recents-backup-*.tar.gz"))
    assert len(tarballs) == 1, f"expected one backup, got {tarballs}"
    # And it contains the deleted file.
    with tarfile.open(tarballs[0]) as tar:
        names = tar.getnames()
    assert any(n.endswith("local_ghost.json") for n in names)


def test_days_flag_removes_old_sessions(tmp_path: Path) -> None:
    sessions = sessions_dir_for(tmp_path)
    sessions.mkdir(parents=True)
    now_ms = time.time() * 1000
    old_ms = now_ms - (60 * 86400 * 1000)  # 60 days ago

    alive_dir = tmp_path / "alive-project"
    alive_dir.mkdir()
    recent = write_session(sessions, "recent", cwd=str(alive_dir),
                           title="recent", last_activity_ms=now_ms)
    old = write_session(sessions, "old", cwd=str(alive_dir),
                        title="old", last_activity_ms=old_ms)

    r = run_script(tmp_path, "--days", "30", "--force")
    assert r.returncode == 0, r.stderr
    assert recent.exists()
    assert not old.exists()


def test_unreadable_session_is_treated_as_stale(tmp_path: Path) -> None:
    sessions = sessions_dir_for(tmp_path)
    sessions.mkdir(parents=True)
    nested = sessions / "org-fake" / "user-fake"
    nested.mkdir(parents=True)
    junk = nested / "local_broken.json"
    junk.write_bytes(b"\x00not valid json")

    r = run_script(tmp_path, "--force")
    assert r.returncode == 0, r.stderr
    assert not junk.exists()


def test_help_flag(tmp_path: Path) -> None:
    r = run_script(tmp_path, "--help")
    assert r.returncode == 0
    assert "--dry-run" in r.stdout
    assert "--days" in r.stdout


@pytest.mark.skipif(platform.system() == "Windows",
                    reason="HOME override only affects Path.home() on Unix.")
def test_dry_run_lists_titles(tmp_path: Path) -> None:
    sessions = sessions_dir_for(tmp_path)
    sessions.mkdir(parents=True)
    now_ms = time.time() * 1000
    write_session(sessions, "ghost1", cwd=str(tmp_path / "gone-a"),
                  title="My Old Project A", last_activity_ms=now_ms)
    write_session(sessions, "ghost2", cwd=str(tmp_path / "gone-b"),
                  title="My Old Project B", last_activity_ms=now_ms)

    r = run_script(tmp_path, "--dry-run")
    assert r.returncode == 0, r.stderr
    assert "My Old Project A" in r.stdout
    assert "My Old Project B" in r.stdout
