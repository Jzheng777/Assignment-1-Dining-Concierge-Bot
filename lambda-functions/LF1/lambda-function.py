import json
import os
import boto3

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["QUEUE_URL"]

def lambda_handler(event, context):
    print(event)
    intent = event["sessionState"]["intent"]
    name = intent["name"]

    # We check which intent it is and then the message is set accordingly
    if name == "GreetingIntent":
        message = "Hi there, how can I help?"
    elif name == "ThankYouIntent":
        message = "You're welcome!"
    elif name == "DiningSuggestionsIntent":
        if event["invocationSource"] == "DialogCodeHook":
            slots = intent["slots"]

            # This is to check if the location input is correct or not
            if slots["Location"] is not None:
                location = slots["Location"]["value"]["interpretedValue"]
                if location.lower() not in ["manhattan", "nyc", "new york", "new york city"]:
                    slots["Location"] = None
                    return {
                        "sessionState": {
                            "dialogAction": {"type": "ElicitSlot", "slotToElicit": "Location"},
                            "intent": intent,
                        },
                        "messages": [{"contentType": "PlainText",
                                      "content": f"Sorry, I can't fulfill requests for {location}. Please enter a valid location."}],
                    }

            # This is to check if the cuisine input is correct or not
            if slots["Cuisine"] is not None:
                cuisine = slots["Cuisine"]["value"]["interpretedValue"]
                if cuisine.lower() not in ["chinese", "japanese", "italian", "mexican", "indian"]:
                    slots["Cuisine"] = None
                    return {
                        "sessionState": {
                            "dialogAction": {"type": "ElicitSlot", "slotToElicit": "Cuisine"},
                            "intent": intent,
                        },
                        "messages": [{"contentType": "PlainText",
                                      "content": f"Sorry, I can't fulfill requests for {cuisine}. Please enter a valid cuisine."}],
                    }

            # This is to check if the number of people input is correct or not
            if slots["NumberofPeople"] is not None:
                number = slots["NumberofPeople"]["value"]["interpretedValue"]
                if not 1 <= int(float(number)) <= 20:
                    slots["NumberofPeople"] = None
                    return {
                        "sessionState": {
                            "dialogAction": {"type": "ElicitSlot", "slotToElicit": "NumberofPeople"},
                            "intent": intent,
                        },
                        "messages": [{"contentType": "PlainText",
                                      "content": f"Sorry, I can't fulfill requests for {number}. Please enter a valid number of people."}],
                    }

            return {"sessionState": {"dialogAction": {"type": "Delegate"}, "intent": intent}}

        slots = intent["slots"]
        location = slots["Location"]["value"]["interpretedValue"]
        cuisine = slots["Cuisine"]["value"]["interpretedValue"]
        people = slots["NumberofPeople"]["value"]["interpretedValue"]
        date = slots["DiningDate"]["value"]["interpretedValue"]
        time = slots["DiningTime"]["value"]["interpretedValue"]
        email = slots["Email"]["value"]["interpretedValue"]

        request = {
            "location": location,
            "cuisine": cuisine.lower(),
            "numberOfPeople": people,
            "diningDate": date,
            "diningTime": time,
            "email": email,
        }

        sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(request))
        message = "You’re all set. Expect my suggestions shortly by email! Have a good day."
    else:
        message = "I'm not sure what you mean."

    intent["state"] = "Fulfilled"
    return {
        "sessionState": {"dialogAction": {"type": "Close"}, "intent": intent},
        "messages": [{"contentType": "PlainText", "content": message }],
    }
