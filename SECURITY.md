# Security policy

## Scope

`claude-recents-cleaner` is a local-only utility:

- It reads JSON files under the Claude desktop application-support directory:
  - macOS: `~/Library/Application Support/Claude/claude-code-sessions/`
  - Linux: `~/.config/Claude/claude-code-sessions/`
  - Windows: `%APPDATA%\Claude\claude-code-sessions\`
- It writes a `.tar.gz` backup into `$HOME` before deleting anything.
- It deletes session metadata files (the ones whose `cwd` no longer exists, or
  optionally those older than `--days N`).

It does **not** make any network requests. It does **not** modify
`~/.claude/projects/` (your actual conversation transcripts) or
`~/.claude.json` (per-project settings).

## Reporting a vulnerability

Email <eugene@saola.sg> with subject `claude-recents-cleaner security`.

Please include:

- What the script does on your machine that you consider a vulnerability.
- The exact command you ran.
- Your OS, Python version, and the script version (`git log -1 --format=%h`).

Expect an initial reply within 5 business days. Coordinated disclosure
preferred — please don't open a public issue with exploit details before the
fix is published.

## Threat model (what we worry about)

- Path-traversal / symlink attacks where a malicious session JSON file points
  `cwd` at a path designed to break out of the sessions directory. The script
  only `unlink()`s files under the sessions directory itself, not the path
  named by `cwd`, so this is bounded by the sessions-directory contents.
- Archive (`tarfile`) extraction is not part of the script's run path; restore
  is done by the user with `tar -xzf` manually.
- Race conditions with Claude.app rewriting metadata mid-run — mitigated by
  the `pgrep` guard. `--force` bypasses it explicitly.

If you find a way to make this script delete or overwrite anything outside
`claude-code-sessions/` or write the backup tarball anywhere but `$HOME`,
that's a bug — please report it.
