import json
import boto3

lex = boto3.client("lexv2-runtime")

BOT_ID = "FBQVMLUVTZ"
BOT_ALIAS_ID = "TSTALIASID"
LOCALE_ID = "en_US"

def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    messages = body.get("messages", [])
    user_text = messages[0]["unstructured"]["text"] if messages else ""

    session_id = event["requestContext"]["identity"]["sourceIp"]

# Get the usertext and session id from the values above
# and send this to Lex 
    lex_response = lex.recognize_text(
        botId=BOT_ID,
        botAliasId=BOT_ALIAS_ID,
        localeId=LOCALE_ID,
        sessionId=session_id,
        text=user_text,
    )

# We take the response from lex and convert it into the website's format
    bot_messages = []
    for m in lex_response.get("messages", []):
        bot_messages.append({"type": "unstructured", "unstructured": {"text": m["content"]}})

    response = {"messages": bot_messages}

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps(response)
    }