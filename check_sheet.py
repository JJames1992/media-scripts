import csv
import json
import os
import sys
import urllib.request

# Read sheet from URL
url = "https://docs.google.com/spreadsheets/d/1UJXLIPlgflXCVEOsOAT0AJJUHNdZKC1chvtaCRCeRks/export?format=csv&gid=0"
response = urllib.request.urlopen(url)
csv_content = response.read().decode('utf-8')

sheet_items = []
reader = csv.DictReader(csv_content.splitlines())
for row in reader:
    title = row['Title'].strip()
    year = row['Year'].strip()
    sheet_items.append({'title': title, 'year': year})

print(f"Sheet items: {len(sheet_items)}")

# Read disk movies
movie_dir = "J:/Media-Archive/Movies"
tv_dir = "J:/Media-Archive/TV Shows"
disk_movies = set()
if os.path.exists(movie_dir):
    for d in os.listdir(movie_dir):
        disk_movies.add(d.strip())
disk_tv = set()
if os.path.exists(tv_dir):
    for d in os.listdir(tv_dir):
        disk_tv.add(d.strip())

print(f"Disk movies: {len(disk_movies)}")
print(f"Disk TV: {len(disk_tv)}")

# Read tracker
tracker_done = set()
tracker_pending = set()
tracker_path = os.path.expanduser("~/.hermes_torrent_tracker.json")
try:
    with open(tracker_path, 'r') as f:
        tracker = json.load(f)
    for key, val in tracker.items():
        if val.get('status') == 'done':
            tracker_done.add(val.get('title', '').strip())
        else:
            tracker_pending.add(val.get('title', '').strip())
except Exception as e:
    print(f"Tracker read error: {e}")

print(f"Tracker done: {len(tracker_done)}")
print(f"Tracker pending: {len(tracker_pending)}")

# Check each sheet item
on_disk = 0
in_tracker_done = 0
pending = 0
pending_items = []

for item in sheet_items:
    title = item['title']
    year = item['year']
    
    # Check disk - try multiple name formats
    found_on_disk = False
    for disk_item in disk_movies | disk_tv:
        # Simple check - if title is in disk folder name
        if title.lower() in disk_item.lower():
            found_on_disk = True
            break
    
    if found_on_disk:
        on_disk += 1
        continue
    
    # Check tracker done
    if title in tracker_done:
        in_tracker_done += 1
        continue
    
    # Check if any tracker done entry contains this title
    found_in_tracker = False
    for done_title in tracker_done:
        if title.lower() in done_title.lower() or done_title.lower() in title.lower():
            found_in_tracker = True
            break
    
    if found_in_tracker:
        in_tracker_done += 1
        continue
    
    pending += 1
    pending_items.append(f"{title} ({year})")

print(f"\nOn disk: {on_disk}")
print(f"In tracker done: {in_tracker_done}")
print(f"Pending: {pending}")
print(f"\nPending items:")
for p in pending_items:
    print(f"  {p}")