import os
import time
from datetime import datetime, timezone
from decimal import Decimal

import boto3
import requests

YELP_API_KEY = os.environ["YELP_API_KEY"]
SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
CUISINES = ["chinese", "italian", "japanese", "mexican", "indian"]

table = boto3.resource("dynamodb", region_name="us-east-1").Table("yelp-restaurants")
headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
seen_ids = set()

for cuisine in CUISINES:
    count = 0
    for offset in range(0, 240, 40):  # offsets 0, 40, 80, 120, 160, 200
        params = {
            "term": f"{cuisine} restaurants",
            "location": "Manhattan, NY",
            "limit": 40,
            "offset": offset,
        }
        resp = requests.get(SEARCH_URL, headers=headers, params=params)
        resp.raise_for_status()  # stop with a clear error if Yelp says no
        businesses = resp.json().get("businesses", [])

        for b in businesses:
            coords = b.get("coordinates") or {}
            if b["id"] in seen_ids or coords.get("latitude") is None:
                continue  # skip duplicates and restaurants with no location
            seen_ids.add(b["id"])

            item = {
                "businessId": b["id"],
                "name": b["name"],
                "cuisine": cuisine,
                "address": ", ".join(b["location"]["display_address"]),
                "zipCode": b["location"].get("zip_code", ""),
                "latitude": Decimal(str(coords["latitude"])),
                "longitude": Decimal(str(coords["longitude"])),
                "reviewCount": b.get("review_count", 0),
                "rating": Decimal(str(b.get("rating", 0))),
                "insertedAtTimestamp": datetime.now(timezone.utc).isoformat(),
            }
            table.put_item(Item=item)
            count += 1

        time.sleep(0.5)  # be polite to Yelp's servers
    print(f"{cuisine}: {count} restaurants saved")

print(f"Total: {len(seen_ids)} restaurants")