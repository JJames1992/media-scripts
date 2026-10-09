#!/usr/bin/env python3
"""
Sync bookmarks and browsing history from native Firefox profile to camofox profile.
Designed to run nightly via Hermes cron.
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta

# Native Firefox profile path
NATIVE_PROFILE = "C:/Users/jonat/AppData/Roaming/Mozilla/Firefox/Profiles/5v9wf193.default-release"
# Camofox profile path (inside the camofox Docker container volume)
CAMOFOX_PROFILE = "C:/Users/jonat/.camofox"

def sync_bookmarks():
    """Extract bookmarks from native Firefox profile."""
    db_path = os.path.join(NATIVE_PROFILE, "places.sqlite")
    
    if not os.path.exists(db_path):
        return {"bookmarks": 0, "history": 0, "error": "places.sqlite not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Extract bookmarks with their URLs
    cursor.execute("""
        SELECT b.title, p.url, b.dateAdded, b.type
        FROM moz_bookmarks b
        LEFT JOIN moz_places p ON p.id = b.fk
        WHERE b.title IS NOT NULL AND b.title != ''
        ORDER BY b.dateAdded DESC
    """)
    
    bookmarks = cursor.fetchall()
    conn.close()
    
    # Write bookmarks to a JSON file in camofox profile
    output_path = os.path.join(CAMOFOX_PROFILE, "firefox_bookmarks.json")
    output_data = []
    
    for title, url, dateAdded, btype in bookmarks:
        if url:  # Only bookmarks that point to URLs
            output_data.append({
                "title": title,
                "url": url,
                "dateAdded": dateAdded,
                "type": "folder" if btype == 2 else "bookmark"
            })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    return {"bookmarks": len(output_data)}

def sync_history():
    """Extract browsing history from native Firefox profile."""
    db_path = os.path.join(NATIVE_PROFILE, "places.sqlite")
    
    if not os.path.exists(db_path):
        return {"bookmarks": 0, "history": 0, "error": "places.sqlite not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get history from last 30 days
    cutoff = int((datetime.now() - timedelta(days=30)).timestamp() * 1_000_000)
    
    cursor.execute("""
        SELECT url, title, visit_count, last_visit_date
        FROM moz_places
        WHERE last_visit_date > ?
        ORDER BY last_visit_date DESC
        LIMIT 500
    """, (cutoff,))
    
    history = cursor.fetchall()
    conn.close()
    
    # Write history to JSON file in camofox profile
    output_path = os.path.join(CAMOFOX_PROFILE, "firefox_history.json")
    output_data = []
    
    for url, title, visit_count, last_visit_date in history:
        output_data.append({
            "url": url,
            "title": title,
            "visit_count": visit_count,
            "last_visit_date": last_visit_date
        })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    return {"history": len(output_data)}

if __name__ == "__main__":
    print(f"Starting Firefox profile sync at {datetime.now().isoformat()}")
    
    # Sync bookmarks
    bookmark_result = sync_bookmarks()
    print(f"Bookmarks: {bookmark_result}")
    
    # Sync history
    history_result = sync_history()
    print(f"History: {history_result}")
    
    print("Sync complete")
