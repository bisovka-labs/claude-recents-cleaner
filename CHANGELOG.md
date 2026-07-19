# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Detect Claude desktop session metadata in Linux Flatpak and Snap sandbox
  locations when the standard location is absent.

### Added

- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`.
- Bug-report and feature-request issue templates.
- Pull-request template.
- GitHub Actions CI: pyflakes lint + pytest matrix on macOS / Ubuntu / Windows
  for Python 3.8 and 3.12.
- Smoke test (`tests/test_smoke.py`) covering dry-run, stale-folder removal,
  age-based removal, and backup creation in a temporary sessions directory.
- `.github/FUNDING.yml`.

## [0.1.0] - 2026-05-23

### Added

- Initial release.
- Scans Claude desktop's `claude-code-sessions/` directory and removes session
  metadata whose `cwd` no longer exists.
- `--days N` flag to also remove sessions whose last activity is older than N
  days.
- `--dry-run` flag to preview without making changes.
- `--force` flag to skip the "Claude.app is running" guard.
- Automatic timestamped `.tar.gz` backup before any deletion, written to
  `$HOME`.
- Cross-platform: macOS, Linux, Windows.
- Homebrew install via `brew install bisovka-labs/tap/claude-recents-cleaner`.

[Unreleased]: https://github.com/bisovka-labs/claude-recents-cleaner/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/bisovka-labs/claude-recents-cleaner/releases/tag/v0.1.0
