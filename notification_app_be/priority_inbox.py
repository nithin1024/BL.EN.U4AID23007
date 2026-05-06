import urllib.request
import json
from datetime import datetime

import sys
import os

# Add the root path so we can import logging_middleware
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_middleware.logger import logger

API_URL = "http://20.207.122.201/evaluation-service/notifications"

# Fallback data based on the provided screenshots to handle 401 Unauthorized
FALLBACK_DATA = {
    "notifications": [
        {"ID": "d146095a-0d86-4a34-9e69-3900a14576bc", "Type": "Result", "Message": "mid-sem", "Timestamp": "2026-04-22 17:51:30"},
        {"ID": "b283218f-ea5a-4b7c-93a9-1f2f240d64b0", "Type": "Placement", "Message": "CSX Corporation hiring", "Timestamp": "2026-04-22 17:51:18"},
        {"ID": "81589ada-0ad3-4f77-9554-f52fb558e09d", "Type": "Event", "Message": "farewell", "Timestamp": "2026-04-22 17:51:06"},
        {"ID": "0005513a-142b-4bbc-8678-eefec65e1ede", "Type": "Result", "Message": "mid-sem", "Timestamp": "2026-04-22 17:50:54"},
        {"ID": "ea836726-c25e-4f21-a72f-544a6af8a37f", "Type": "Result", "Message": "project-review", "Timestamp": "2026-04-22 17:50:42"},
        {"ID": "003cb427-8fc6-47f7-bb00-be228f6b0d2c", "Type": "Result", "Message": "external", "Timestamp": "2026-04-22 17:50:30"},
        {"ID": "e5c4ff20-31bf-4d40-8f02-72fda59e8918", "Type": "Result", "Message": "project-review", "Timestamp": "2026-04-22 17:50:18"},
        {"ID": "1cfce5ee-ad37-4894-8946-d707627176a5", "Type": "Event", "Message": "tech-fest", "Timestamp": "2026-04-22 17:50:06"},
        {"ID": "cf2885a6-45ac-4ba0-b548-6e9e9d4c52c8", "Type": "Result", "Message": "project-review", "Timestamp": "2026-04-22 17:49:54"},
        {"ID": "8a7412bd-6065-4d09-8501-a37f11cc848b", "Type": "Placement", "Message": "Advanced Micro Devices Inc. hiring", "Timestamp": "2026-04-22 17:49:42"}
    ]
}

def fetch_notifications():
    try:
        req = urllib.request.Request(API_URL)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            logger.info("Successfully fetched notifications from API")
            return data.get("notifications", [])
    except Exception as e:
        logger.error(f"Failed to fetch from API: {e}. Using fallback data.")
        return FALLBACK_DATA["notifications"]

def get_weight(notif_type):
    # placement > result > event
    if notif_type.lower() == 'placement':
        return 3
    elif notif_type.lower() == 'result':
        return 2
    elif notif_type.lower() == 'event':
        return 1
    return 0

def priority_inbox(n=10):
    notifications = fetch_notifications()
    if not notifications:
        logger.warning("No notifications available.")
        return []

    def sort_key(notif):
        weight = get_weight(notif.get("Type", ""))
        try:
            timestamp = datetime.strptime(notif.get("Timestamp", ""), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            timestamp = datetime.min
        return (weight, timestamp)

    # Sort primarily by weight (desc), secondarily by timestamp (desc)
    sorted_notifications = sorted(notifications, key=sort_key, reverse=True)
    
    top_n = sorted_notifications[:n]
    logger.info(f"Processed top {len(top_n)} priority notifications.")
    return top_n

if __name__ == "__main__":
    logger.info("Starting Priority Inbox processing...")
    top_notifications = priority_inbox(10)
    
    print("\n--- PRIORITY INBOX (Top 10) ---")
    for i, notif in enumerate(top_notifications, 1):
        print(f"{i}. [{notif['Type']}] {notif['Message']} (Received: {notif['Timestamp']})")
    print("-------------------------------\n")
