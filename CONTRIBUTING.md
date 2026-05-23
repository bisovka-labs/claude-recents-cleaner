# Contributing

Bug reports, feature requests, and pull requests are welcome.

## Bug reports

Use the bug-report issue template (it asks for the right details). At minimum:

- Your OS and version (macOS 14.5, Ubuntu 22.04, Windows 11, etc.)
- Claude desktop version (Help → About in the app)
- Output of `python3 clean-claude-recents.py --dry-run`
- Whether you ran with `--force` or with Claude.app running

If the script crashed, include the full traceback.

## Feature requests

Open an issue first to discuss the shape before writing code. The single-file,
stdlib-only constraint is deliberate — features that would require a dependency
usually belong in a separate companion script, not in this one.

## Pull requests

1. Lint locally: `python3 -m pyflakes clean-claude-recents.py`
2. Run the smoke tests: `python3 -m pytest tests/`
3. Keep the single-file, stdlib-only constraint. No new third-party packages.
4. Match existing code style (PEP 8, no docstring novels).
5. Add a manual-test note in the PR description: "Ran on macOS 14.5 against
   Claude desktop 1.8555.x, removed 12 stale sessions, restore from backup
   verified."
6. Bump `CHANGELOG.md` under an `## [Unreleased]` heading.

## Good first issues

Look for the [`good first issue`](https://github.com/bisovka-labs/claude-recents-cleaner/labels/good%20first%20issue)
label — those are scoped to ~30-60 minutes of work with pointers to the
relevant code.

## Maintainer

Eugene Bisovka — <eugene@saola.sg>
