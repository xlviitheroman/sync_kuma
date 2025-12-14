#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from uptime_kuma_api import UptimeKumaApi, MonitorType, NotificationType
import traceback
import sys

# Config: Your creds
PRIMARY_URL = "http://primaryserver.fqdn:3001"
SECONDARY_URL = "http://secondaryserver.fqdn:3001"
USERNAME = "username"
PASSWORD = "password"

def verbose_print(msg):
    print(f"[VERBOSE] {msg}")

def build_add_data(mon):
    type_str = mon['type'].upper()
    if hasattr(MonitorType, type_str):
        monitor_type = getattr(MonitorType, type_str)
    else:
        return None
    
    # Minimal data - only essentials to avoid TypeError
    add_data = {
        'type': monitor_type,
        'name': mon['name'],
        'interval': mon.get('interval', 60),
        'timeout': mon.get('timeout', 30),
    }
    
    # Type-specific essentials
    if type_str == 'PING':
        add_data['hostname'] = mon.get('hostname', mon['url'])
    elif type_str == 'PORT':
        add_data['hostname'] = mon.get('hostname', mon['url'])
        add_data['port'] = mon.get('port', 80)
    elif type_str == 'DNS':
        add_data['hostname'] = mon.get('hostname', '')
        add_data['dnsResolveType'] = mon.get('dnsResolveType', 'A')
    elif type_str == 'HTTP':
        add_data['url'] = mon.get('url', '')  # Already in common
        add_data['httpMethod'] = mon.get('httpMethod', 'GET')
    
    verbose_print(f"  Built minimal add_data for '{mon['name']}': {add_data}")
    return add_data

def sync_monitors():
    verbose_print("=== Syncing Monitors ===")
    # Primary
    verbose_print("Step 1: Connecting to primary...")
    api_primary = UptimeKumaApi(PRIMARY_URL)
    try:
        verbose_print("  Logging in to primary...")
        result = api_primary.login(USERNAME, PASSWORD)
        verbose_print(f"  Login result: {result}")
        primary_monitors = api_primary.get_monitors()
        verbose_print(f"  Fetched {len(primary_monitors)} monitors from primary.")
    except Exception as e:
        verbose_print(f"  Primary login or fetch error: {e}")
        traceback.print_exc()
        raise
    finally:
        api_primary.disconnect()

    # Secondary
    verbose_print("Step 2: Connecting to secondary...")
    api_secondary = UptimeKumaApi(SECONDARY_URL)
    try:
        verbose_print("  Logging in to secondary...")
        result = api_secondary.login(USERNAME, PASSWORD)
        verbose_print(f"  Login result: {result}")
        secondary_monitors = api_secondary.get_monitors()
        verbose_print(f"  Fetched {len(secondary_monitors)} monitors from secondary. Deleting all...")
        deleted = 0
        for mon in secondary_monitors:
            try:
                api_secondary.delete_monitor(mon['id'])
                verbose_print(f"  Deleted '{mon['name']}' (ID: {mon['id']})")
                deleted += 1
            except Exception as e:
                verbose_print(f"  Delete error for '{mon['name']}': {e}")
        verbose_print(f"  Deleted {deleted}/{len(secondary_monitors)} monitors.")
    except Exception as e:
        verbose_print(f"  Secondary login or delete error: {e}")
        traceback.print_exc()
        raise
    finally:
        api_secondary.disconnect()

    # Add to secondary
    verbose_print("Step 3: Adding monitors to secondary...")
    added = 0
    skipped = 0
    api_secondary = UptimeKumaApi(SECONDARY_URL)
    try:
        api_secondary.login(USERNAME, PASSWORD)
        for mon in primary_monitors:
            add_data = build_add_data(mon)
            if add_data is None:
                verbose_print(f"  Skipping '{mon['name']}' (unknown type)")
                skipped += 1
                continue
            try:
                verbose_print(f"  Calling add_monitor for '{mon['name']}'...")
                result = api_secondary.add_monitor(**add_data)
                new_id = result.get('monitorId', 'N/A') if isinstance(result, dict) else str(result)
                verbose_print(f"    Success: Added '{mon['name']}' (New ID: {new_id})")
                added += 1
            except TypeError as e:
                verbose_print(f"    TypeError on '{mon['name']}': {e} - skipping (field mismatch)")
                skipped += 1
            except Exception as e:
                verbose_print(f"    Error adding '{mon['name']}': {e}")
                traceback.print_exc()
                skipped += 1
        verbose_print(f"  Added {added}/{len(primary_monitors)} monitors. Skipped {skipped}.")
    except Exception as e:
        verbose_print(f"  Secondary add error: {e}")
        traceback.print_exc()
        raise
    finally:
        api_secondary.disconnect()

def sync_notifications():
    verbose_print("=== Syncing Notifications ===")
    # Primary
    verbose_print("Step 4: Connecting to primary for notifications...")
    api_primary = UptimeKumaApi(PRIMARY_URL)
    try:
        api_primary.login(USERNAME, PASSWORD)
        primary_notifs = api_primary.get_notifications()
        verbose_print(f"  Fetched {len(primary_notifs)} notifications from primary.")
    except Exception as e:
        verbose_print(f"  Primary notifs error: {e}")
        traceback.print_exc()
        raise
    finally:
        api_primary.disconnect()

    # Secondary
    verbose_print("Step 5: Connecting to secondary for notifications...")
    api_secondary = UptimeKumaApi(SECONDARY_URL)
    try:
        api_secondary.login(USERNAME, PASSWORD)
        secondary_notifs = api_secondary.get_notifications()
        verbose_print(f"  Fetched {len(secondary_notifs)} notifications from secondary. Deleting all...")
        deleted = 0
        for notif in secondary_notifs:
            try:
                api_secondary.delete_notification(notif['id'])
                verbose_print(f"  Deleted '{notif['name']}' (ID: {notif['id']})")
                deleted += 1
            except Exception as e:
                verbose_print(f"  Delete error for '{notif['name']}': {e}")
        verbose_print(f"  Deleted {deleted}/{len(secondary_notifs)} notifications.")
    except Exception as e:
        verbose_print(f"  Secondary notifs error: {e}")
        traceback.print_exc()
        raise
    finally:
        api_secondary.disconnect()

    # Add to secondary
    verbose_print("Step 6: Adding notifications to secondary...")
    added = 0
    skipped = 0
    api_secondary = UptimeKumaApi(SECONDARY_URL)
    try:
        api_secondary.login(USERNAME, PASSWORD)
        for notif in primary_notifs:
            try:
                type_str = notif['type'].replace('-', '_').upper()
                if hasattr(NotificationType, type_str):
                    notif_type = getattr(NotificationType, type_str)
                else:
                    verbose_print(f"  Skipping unknown type '{type_str}' for '{notif['name']}'")
                    skipped += 1
                    continue
                
                add_data = {
                    'type': notif_type,
                    'name': notif['name'],
                    'config': notif.get('config', {}),
                }
                
                verbose_print(f"  Adding '{notif['name']}' (type: {notif['type']})...")
                result = api_secondary.add_notification(**add_data)
                new_id = result.get('id', 'N/A') if isinstance(result, dict) else str(result)
                verbose_print(f"    Success: Added '{notif['name']}' (New ID: {new_id})")
                added += 1
            except Exception as e:
                verbose_print(f"    Error adding '{notif['name']}': {e}")
                traceback.print_exc()
                skipped += 1
        verbose_print(f"  Added {added}/{len(primary_notifs)} notifications. Skipped {skipped}.")
    except Exception as e:
        verbose_print(f"  Secondary add error: {e}")
        traceback.print_exc()
        raise
    finally:
        api_secondary.disconnect()

if __name__ == "__main__":
    try:
        import uptime_kuma_api
        verbose_print(f"Library path: {uptime_kuma_api.__file__}")
    except:
        verbose_print("Library version: Unknown")
    print("Starting Uptime Kuma sync (Primary -> Secondary)")
    try:
        sync_monitors()
        sync_notifications()
        print("Sync complete! Check dashboards to verify.")
    except Exception as e:
        print(f"Fatal error during sync: {e}")
        traceback.print_exc()
        sys.exit(1)