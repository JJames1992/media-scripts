import json

with open(r'C:\Users\jonat\.hermes_torrent_tracker.json') as f:
    d = json.load(f)

done = sum(1 for v in d.values() if v.get('status') == 'done')
pending = sum(1 for v in d.values() if v.get('status') == 'pending')
total = len(d)
print(f'Total tracker entries: {total}')
print(f'Done: {done}')
print(f'Pending: {pending}')
