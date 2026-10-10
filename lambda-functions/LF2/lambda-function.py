import json
import os
import boto3
import urllib3

http = urllib3.PoolManager()
OS_ENDPOINT = os.environ["OS_ENDPOINT"]
OS_HEADERS = urllib3.make_headers(basic_auth=f"{os.environ['OS_USER']}:{os.environ['OS_PASS']}")
OS_HEADERS["Content-Type"] = "application/json"

# This table will represent our dynamodb where we can look up details
table = boto3.resource("dynamodb").Table("yelp-restaurants")

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["QUEUE_URL"]

ses = boto3.client("ses")
SENDER_EMAIL = os.environ["SENDER_EMAIL"]

def lambda_handler(event, context):
    resp = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=1)
    messages = resp.get("Messages", [])

    if not messages:
        print("Queue is empty")
        return

# First we get the msg and since msg["Body"] is a string
# we use json.loads to turn it into a dictionary (msg is a dictionary as well)
    msg = messages[0]
    request = json.loads(msg["Body"])
    print("Cuisine:", request["cuisine"])
    print("Email:", request["email"])

    query = {
        "size": 3,
        "query": {
            "function_score": {
                "query": {"term": {"Cuisine": request["cuisine"]}},
                "random_score": {}
            }
        }
    }

    r = http.request("POST", f"{OS_ENDPOINT}/restaurants/_search", body=json.dumps(query), headers=OS_HEADERS)
    result = json.loads(r.data)
    hits = result["hits"]["hits"]

    ids = []
    # The restaurant id that we're trying to send back are under the key _source
    # which has the restaurant id, cuisine, and type
    for hit in hits:
        ids.append(hit["_source"]["RestaurantID"])
    print("Restaurant IDs:", ids)

    restaurants = []
    for rid in ids:
        item = table.get_item(Key={"businessId": rid}).get("Item")
        if item:
            restaurants.append(item)

    for restaurant in restaurants:
        print(restaurant["name"], "-", restaurant["address"])

    
    email_body = (f"Hello! Here are my {request['cuisine'].title()} restaurant suggestions "
                  f"for {request['numberOfPeople']} people, for {request['diningDate']} at {request['diningTime']}:\n\n")
    for i, restaurant in enumerate(restaurants, start=1):
        email_body += f"{i}. {restaurant['name']}, located at {restaurant['address']}\n"
    email_body += "\nEnjoy your meal!"

    ses.send_email(
        Source=SENDER_EMAIL,
        Destination={"ToAddresses": [request["email"]]},
        Message={
            "Subject": {"Data": "Your restaurant suggestions"},
            "Body": {"Text": {"Data": email_body}},
        },
    )

    sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])
    print("Email sent to", request["email"])