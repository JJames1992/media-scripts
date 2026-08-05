
import json, urllib.request, os, re
BASE="http://localhost:20128"
d=json.load(urllib.request.urlopen(BASE+"/v1/models",timeout=90))["data"]
print("total models exposed:", len(d))
from collections import Counter
def vendor(mid):
    return mid.split("/")[0]
c=Counter(vendor(m["id"]) for m in d)
for k,v in c.most_common(): print(f"  {k:<20} {v}")
