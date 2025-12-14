# Uptime Kuma Sync Script

## Overview

This Python script synchronizes monitors and notifications from a primary Uptime Kuma instance to a secondary one. It fetches configurations from the primary server, clears existing items on the secondary, and recreates them to ensure consistency across instances. Ideal for maintaining mirrored setups in high-availability environments. Note: Not all features will replicate correctly; your mileage may vary.

**Key Features:**
- Supports common monitor types (Ping, Port, DNS, HTTP) with minimal essential fields.
- Handles notifications by type, preserving configs.
- Verbose logging for debugging.
- Error handling with graceful skips for unsupported types or fields.

## Prerequisites

- Python 3.6+ (tested with 3.12).
- `uptime_kuma_api` library: Install via `pip install uptime_kuma_api`.
- Access to two Uptime Kuma servers with API-enabled accounts (read/write permissions).

## Configuration

Edit the config variables at the top of `sync_kuma.py`:

```python
PRIMARY_URL = "http://primaryserver.fqdn:3001"    # Source server URL
SECONDARY_URL = "http://secondaryserver.fqdn:3001" # Target server URL
USERNAME = "username"                              # Shared API username
PASSWORD = "password"                              # Shared API password
```

Ensure both servers are reachable and credentials are valid for both systems.

## Usage

1. Save the script as `sync_kuma.py`.
2. Configure the variables as needed.
3. Run the script:

   ```bash
   python sync_kuma.py
   ```

   - Output includes verbose logs (prefixed with `[VERBOSE]`) and a summary of added/deleted items.
   - On success: "Sync complete! Check dashboards to verify."
   - On error: Full traceback and exit code 1.

Run periodically via cron/scheduler for ongoing syncs.

## What It Does

1. **Monitors Sync:**
   - Fetches all monitors from primary.
   - Deletes all monitors on secondary.
   - Adds monitors to secondary (skips unknown types or field mismatches).

2. **Notifications Sync:**
   - Fetches all notifications from primary.
   - Deletes all notifications on secondary.
   - Adds notifications to secondary (skips unknown types).

This is a one-way sync (primary → secondary); no status history or advanced settings (e.g., custom HTTP headers) are transferred—only essentials.

## Limitations

- **Minimal Fields:** Only core monitor data is synced to avoid API errors; enrich manually post-sync if needed.
- **Type Support:** Monitors limited to Ping/Port/DNS/HTTP; notifications require valid `NotificationType` enums.
- **No Idempotency:** Full delete/recreate—use with caution on production.
- **Error Recovery:** Skips failures but logs details; review verbose output for issues.
- **Dependencies:** Relies on `uptime_kuma_api`—update library for Uptime Kuma version compatibility.

## Troubleshooting

- **Login Failures:** Verify URLs, credentials, and server uptime.
- **TypeErrors:** Check monitor configs for unsupported fields; adjust `build_add_data` if extending.
- **Library Issues:** Ensure `uptime_kuma_api` is installed and up-to-date.
- Test on a staging setup first.

No formal license—use at your own risk.
