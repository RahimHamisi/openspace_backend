import os
import requests
from requests.auth import HTTPBasicAuth

def send_sms(phone, message):
    url = "https://apisms.beem.africa/v1/send"

    data = {
        "source_addr": "OPENSPACE",  # use 'ARDHI UN' only if it's approved by Beem
        "encoding": 0,
        "message": message,
        "recipients": [
            {
                "recipient_id": 1,
                "dest_addr": phone  # should be decrypted and in format 2557XXXXXXX
            }
        ]
    }

    username = os.getenv("BEEM_API_KEY")
    password = os.getenv("BEEM_SECRET_KEY")

    print("BEEM_API_KEY:", username)
    print("Sending SMS to:", phone)
    print("Payload:", data)

    try:
        response = requests.post(url, json=data, auth=HTTPBasicAuth(username, password))
        print("Beem Response:", response.status_code, response.text)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print("HTTP error sending SMS:", e)
        raise
    except Exception as e:
        print("Unexpected error sending SMS:", e)
        raise
