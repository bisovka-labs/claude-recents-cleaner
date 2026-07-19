#!/usr/bin/env python3
"""Clear stale projects from Claude Code's "Recent" dropdown.

The Claude desktop app stores per-project session metadata under
its application support directory. Each session file records a `cwd`
(the project folder). The "Recent" dropdown is built from these files.

When you rename, move, or delete a project folder, the desktop keeps
showing the old name in Recent. This script removes session metadata
entries whose `cwd` no longer exists, so the dropdown reflects reality.

It is safe: the actual conversation transcripts live elsewhere
(`~/.claude/projects/`) and are not touched. Each run creates a
timestamped `.tar.gz` backup of every file it removes.

Usage:
    python3 clean-claude-recents.py             # remove sessions for missing folders
    python3 clean-claude-recents.py --dry-run   # show what would be removed
    python3 clean-claude-recents.py --days 30   # also remove sessions older than 30 days

Quit Claude.app fully (Cmd+Q on macOS) before running, then relaunch it after.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import tarfile
import time
from pathlib import Path

HOME = Path.home()
STAMP = time.strftime("%Y%m%d-%H%M%S")


def sessions_root() -> Path:
    """Return the Claude desktop's per-platform session metadata directory."""
    system = platform.system()
    if system == "Darwin":
        return HOME / "Library" / "Application Support" / "Claude" / "claude-code-sessions"
    if system == "Linux":
        candidates = [
            HOME / ".config" / "Claude" / "claude-code-sessions",
            HOME / ".var" / "app" / "com.anthropic.Claude" / "config" / "Claude" / "claude-code-sessions",
            HOME / "snap" / "claude" / "current" / ".config" / "Claude" / "claude-code-sessions",
        ]
        for candidate in candidates:
            if candidate.is_dir():
                return candidate
        return candidates[0]
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Claude" / "claude-code-sessions"
        return HOME / "AppData" / "Roaming" / "Claude" / "claude-code-sessions"
    raise SystemExit(f"Unsupported platform: {system}")


def claude_desktop_running() -> bool:
    """Best-effort check that Claude.app isn't currently running."""
    system = platform.system()
    try:
        if system == "Darwin":
            r = subprocess.run(["pgrep", "-x", "Claude"], capture_output=True, timeout=3)
            return r.returncode == 0
        if system == "Linux":
            r = subprocess.run(["pgrep", "-fa", "claude"], capture_output=True, timeout=3)
            # crude: match "Claude" or "claude" as a process running from /opt/Claude or similar
            return b"Claude" in r.stdout or b"/claude" in r.stdout
        if system == "Windows":
            r = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Claude.exe"],
                capture_output=True, timeout=5,
            )
            return b"Claude.exe" in r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove stale entries from Claude Code's Recent dropdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be removed; do not delete anything.",
    )
    parser.add_argument(
        "--days", type=float, default=None, metavar="N",
        help="Also remove sessions whose last activity is older than N days "
             "(default: only sessions whose folder no longer exists).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Skip the 'Claude.app is running' guard (not recommended).",
    )
    args = parser.parse_args()

    root = sessions_root()
    if not root.is_dir():
        print(f"Sessions directory not found: {root}")
        print("Nothing to clean. (Have you ever used Claude Code on this machine?)")
        return 0

    if claude_desktop_running() and not args.force and not args.dry_run:
        print("Claude.app appears to be running. Quit it fully first "
              "(Cmd+Q on macOS), then re-run this script.", file=sys.stderr)
        print("Use --dry-run to preview without quitting, or --force to override "
              "(the app may overwrite your cleanup).", file=sys.stderr)
        return 1

    session_files = list(root.rglob("local_*.json"))
    if not session_files:
        print("No session files found — nothing to clean.")
        return 0

    cutoff_ms = None
    if args.days is not None:
        cutoff_ms = (time.time() - args.days * 86400) * 1000

    stale_folder, stale_age, alive = [], [], []
    for f in session_files:
        try:
            with open(f) as fh:
                d = json.load(fh)
        except (OSError, json.JSONDecodeError):
            # Treat unreadable files as stale candidates — they can't appear
            # in Recent in any useful form anyway.
            stale_folder.append((f, None, "(unreadable)"))
            continue
        cwd = d.get("cwd")
        last = d.get("lastActivityAt") or d.get("createdAt") or 0
        title = d.get("title") or "(untitled)"
        if not cwd or not Path(cwd).exists():
            stale_folder.append((f, cwd, title))
        elif cutoff_ms is not None and last < cutoff_ms:
            stale_age.append((f, cwd, title))
        else:
            alive.append((f, cwd, title))

    to_remove = stale_folder + stale_age
    print(f"Scanned {len(session_files)} session files in {root}")
    print(f"  alive (kept):           {len(alive)}")
    print(f"  stale folder (remove):  {len(stale_folder)}")
    if args.days is not None:
        print(f"  older than {args.days:g}d (remove): {len(stale_age)}")
    print()

    if not to_remove:
        print("Recent dropdown is already clean.")
        return 0

    if args.dry_run:
        print("Dry run — would remove:")
        for _, cwd, title in to_remove[:40]:
            short = (cwd or "(no cwd)")
            print(f"  - {short}  —  {title}")
        if len(to_remove) > 40:
            print(f"  ... and {len(to_remove) - 40} more")
        print()
        print("Re-run without --dry-run to apply.")
        return 0

    tar_path = HOME / f"claude-recents-backup-{STAMP}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for f, _, _ in to_remove:
            tar.add(f, arcname=f.name)

    for f, _, _ in to_remove:
        try:
            f.unlink()
        except OSError as e:
            print(f"Warning: could not remove {f}: {e}", file=sys.stderr)

    print(f"Removed {len(to_remove)} stale session files.")
    print(f"Backup: {tar_path}")
    print()
    print("Relaunch Claude.app — the Recent dropdown should now show only "
          "existing projects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
