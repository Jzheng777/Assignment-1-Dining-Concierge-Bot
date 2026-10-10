import os
import json
import boto3
import requests

OS_ENDPOINT = os.environ["OS_ENDPOINT"]
auth = (os.environ["OS_USER"], os.environ["OS_PASS"])  # master user login

# We create the restaurants index.
mapping = {
    "mappings": {
        "properties": {
            "RestaurantID": {"type": "keyword"},
            "Cuisine": {"type": "keyword"},
            "type": {"type": "keyword"},
        }
    }
}
r = requests.put(f"{OS_ENDPOINT}/restaurants", auth=auth, json=mapping)
print("Create index:", r.status_code, r.text)

# We read every restaurant's ID and cuisine from DynamoDB.
table = boto3.resource("dynamodb", region_name="us-east-1").Table("yelp-restaurants")
items = []
resp = table.scan(ProjectionExpression="businessId, cuisine")
items.extend(resp["Items"])
while "LastEvaluatedKey" in resp:
    resp = table.scan(ProjectionExpression="businessId, cuisine",
                      ExclusiveStartKey=resp["LastEvaluatedKey"])
    items.extend(resp["Items"])
print("Read from DynamoDB:", len(items))

# Then we upload them all in one "bulk" request.
lines = []
for it in items:
    lines.append(json.dumps({"index": {"_index": "restaurants", "_id": it["businessId"]}}))
    lines.append(json.dumps({
        "RestaurantID": it["businessId"],
        "Cuisine": it["cuisine"],
        "type": "Restaurant",
    }))
body = "\n".join(lines) + "\n"

r = requests.post(f"{OS_ENDPOINT}/_bulk", auth=auth, data=body,
                  headers={"Content-Type": "application/x-ndjson"})
print("Bulk upload:", r.status_code, "errors:", r.json().get("errors"))