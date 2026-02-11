# Uptime Kuma Sync Script
# Takes your primary monitors and syncs them to another server

## Overview
This Python script synchronizes monitors and notifications from a primary Uptime Kuma instance to a secondary one in an **additive/update-only** manner - it never deletes anything on the secondary.

It is designed to keep a secondary instance in sync with a primary one (primary is the source of truth) while preserving any extra items created directly on the secondary.

**Key Features:**
- Notifications: Adds missing notifications and updates existing ones by name (no deletes).
- Monitors: Copies all monitor configurations using an explicit allowlist of supported fields for compatibility with Uptime Kuma v2. Reconstructs URL for HTTP/Keyword monitors if needed, maps notification IDs by name, adds new monitors or updates existing ones by name (no deletes).
- Status pages: Not currently synced (can be added later if required).
- Verbose logging for every step, including raw/final config keys for debugging.
- Robust connection handling with retries and timeouts.
- Uses `uptime-kuma-api-v2` for native Uptime Kuma v2 compatibility (no manual field stripping required in most cases).

## Prerequisites
- Python 3.8+ (tested with 3.11/3.12).
- `uptime-kuma-api-v2` library: `pip install uptime-kuma-api-v2`
- API access to both Uptime Kuma instances with read/write permissions on the same account.

## Configuration
Edit the top section of `sync_kuma.py` with the correct endpoints, username, and password:
```python
PRIMARY_URL = "http://primaryhost.local:3001"
SECONDARY_URL = "http://secondaryhost.local:3001"
USERNAME = "username"
PASSWORD = "password"
```

## Usage
```bash
python sync_kuma.py
```

- Run manually or via cron for periodic sync.
- Output includes detailed verbose logs and a final summary.
- On success: "Sync complete! All monitors should now be synced."
- On error: Full traceback + exit code 1.

## What It Does
1. Connects to both instances with retry logic.
2. Syncs notifications: add new, update existing by name.
3. Syncs monitors: add new, update existing by name. Uses allowlist to avoid v2-incompatible fields. Reconstructs HTTP/Keyword URLs safely.
4. No deletions on secondary - safe for production mirroring.

## Limitations
- One-way sync only (primary → secondary).
- Status pages, groups, tags, and some advanced monitor settings (e.g., custom headers, OAuth) may require manual handling or future script updates.
- Relies on monitor/notification names being unique.
- Uses `uptime-kuma-api-v2` - ensure it matches your Uptime Kuma version.

## Troubleshooting
- Connection hangs: Check network/WebSocket access between hosts (test with `wscat`).
- Field errors: The v2 library should handle them; check verbose output for config keys.
- Test on non-production first.

No formal license - use at your own risk.
