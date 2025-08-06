import os
import requests
from requests.auth import HTTPBasicAuth

def send_sms(phone, message):
    url = 'https://apisms.beem.africa/v1/send'

    payload = {
        "source_addr": "OPENSPACE",  # or your approved sender name
        "schedule_time": "",
        "encoding": 0,
        "message": message,
        "recipients": [
            {"recipient_id": 1, "dest_addr": phone}
        ]
    }

    username = os.getenv("BEEM_API_KEY")
    password = os.getenv("BEEM_SECRET_KEY")

    try:
        response = requests.post(url, json=payload, auth=HTTPBasicAuth(username, password))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("SMS sending failed:", e)
        return None
