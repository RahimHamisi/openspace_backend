import os
import requests
from requests.auth import HTTPBasicAuth

def send_sms(phone, message):
    url = "https://apisms.beem.africa/v1/send"

    data = {
        "source_addr": "OPENSPACE",  # Or any approved sender ID
        "encoding": 0,
        "message": message,
        "recipients": [
            {
                "recipient_id": 1,
                "dest_addr": phone  # Make sure phone format is correct e.g. '2557xxxxxxx'
            }
        ]
    }

    username = os.getenv("BEEM_API_KEY")
    password = os.getenv("BEEM_SECRET_KEY")

    try:
        response = requests.post(url, json=data, auth=HTTPBasicAuth(username, password))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print("HTTP error sending SMS:", e)
        raise
    except Exception as e:
        print("Unexpected error sending SMS:", e)
        raise
