#!/usr/bin/env python3

from uptime_kuma_api import UptimeKumaApi, MonitorType, NotificationType
import traceback
import time
import sys

# ============================================================
# CONFIG
# ============================================================

PRIMARY_URL = "http://primaryhost.local:3001"
SECONDARY_URL = "http://secondaryhost.local:3001"
USERNAME = "username"
PASSWORD = "password"

TIMEOUT = 300
RETRIES = 10
RETRY_DELAY = 10

# ============================================================

def verbose(msg):
    print(f"[VERBOSE] {msg}")

def login_api(url, label):
    for attempt in range(1, RETRIES + 1):
        try:
            verbose(f"Attempt {attempt}/{RETRIES}: Connecting to {label} ({url})...")
            api = UptimeKumaApi(url, timeout=TIMEOUT)
            api.login(USERNAME, PASSWORD)
            verbose(f"SUCCESS: Connected to {label}")
            return api
        except Exception as e:
            verbose(f"Attempt {attempt} failed: {e}")
            time.sleep(RETRY_DELAY)
    raise RuntimeError(f"Failed to connect to {label}")

# ============================================================
# NOTIFICATIONS
# ============================================================

def sync_notifications(api_primary, api_secondary):
    verbose("=== Syncing Notifications ===")

    pri = api_primary.get_notifications()
    sec = api_secondary.get_notifications()

    sec_by_name = {n["name"]: n["id"] for n in sec}

    added = updated = skipped = 0

    for n in pri:
        try:
            notif_type = getattr(
                NotificationType,
                n["type"].replace("-", "_").upper()
            )

            data = {
                "type": notif_type,
                "name": n["name"],
                "config": n.get("config", {}),
                "active": n.get("active", True),
                "isDefault": n.get("isDefault", False),
            }

            if n["name"] in sec_by_name:
                api_secondary.edit_notification(sec_by_name[n["name"]], **data)
                updated += 1
            else:
                api_secondary.add_notification(**data)
                added += 1

        except Exception:
            verbose(f"Notification error: {n['name']}")
            traceback.print_exc()
            skipped += 1

    verbose(f"Notifications: Added {added}, Updated {updated}, Skipped {skipped}")
    return pri

# ============================================================
# MONITORS
# ============================================================

# Explicit allowlist — this prevents ALL future v2 breakage
ALLOWED_MONITOR_FIELDS = {
    "name",
    "type",
    "url",
    "hostname",
    "port",
    "interval",
    "retryInterval",
    "maxretries",
    "timeout",
    "keyword",
    "ignoreTls",
    "upsideDown",
    "notificationIDList",
    "method",
    "headers",
    "body",
}

def sync_monitors(api_primary, api_secondary, primary_notifications):
    verbose("=== Syncing Monitors ===")

    pri = api_primary.get_monitors()
    sec = api_secondary.get_monitors()

    sec_by_name = {m["name"]: m["id"] for m in sec}

    pri_notif_id_to_name = {n["id"]: n["name"] for n in primary_notifications}
    sec_notifs = api_secondary.get_notifications()
    sec_notif_name_to_id = {n["name"]: n["id"] for n in sec_notifs}

    added = updated = skipped = 0

    for mon in pri:
        try:
            config = {
                k: mon[k]
                for k in ALLOWED_MONITOR_FIELDS
                if k in mon and mon[k] is not None
            }

            config["type"] = getattr(MonitorType, mon["type"].upper())

            # HTTP / HTTPS / KEYWORD — trust v2 URL
            if mon["type"] in ("http", "keyword"):
                if mon.get("url"):
                    config["url"] = mon["url"]

            # Map notifications
            if "notificationIDList" in config:
                mapped = []
                for nid in config["notificationIDList"]:
                    name = pri_notif_id_to_name.get(nid)
                    if name in sec_notif_name_to_id:
                        mapped.append(sec_notif_name_to_id[name])
                config["notificationIDList"] = mapped

            name = mon["name"]

            if name in sec_by_name:
                api_secondary.edit_monitor(sec_by_name[name], **config)
                verbose(f"Updated monitor '{name}'")
                updated += 1
            else:
                api_secondary.add_monitor(**config)
                verbose(f"Added monitor '{name}'")
                added += 1

        except Exception:
            verbose(f"Error syncing monitor '{mon['name']}'")
            traceback.print_exc()
            skipped += 1

    verbose(f"Monitors: Added {added}, Updated {updated}, Skipped {skipped}")

# ============================================================
# MAIN
# ============================================================

def main():
    print("Starting Uptime Kuma sync using uptime-kuma-api-v2 (final stable)")

    api_primary = login_api(PRIMARY_URL, "primary")
    api_secondary = login_api(SECONDARY_URL, "secondary")

    try:
        primary_notifications = sync_notifications(api_primary, api_secondary)
        sync_monitors(api_primary, api_secondary, primary_notifications)
        print("Sync complete! All monitors should now be synced.")
    finally:
        api_primary.disconnect()
        api_secondary.disconnect()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
