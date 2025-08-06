import africastalking
import os
from cryptography.fernet import Fernet # type: ignore

# Initialize Africa's Talking
africastalking.initialize(os.getenv("AT_USERNAME"), os.getenv("AT_API_KEY"))
sms = africastalking.SMS

# Decrypt phone number
FERNET_KEY = os.getenv("FERNET_KEY")
fernet = Fernet(FERNET_KEY)

def send_confirmation_sms(encrypted_phone_number, reference_number):
    try:
        phone_number = fernet.decrypt(encrypted_phone_number.encode()).decode()
        print(f"[DEBUG] Decrypted phone number: {phone_number}")

        message = f"Your report with reference number {reference_number} has been confirmed and processed. Thank you!"
        print(f"[DEBUG] Sending SMS: '{message}' to {phone_number}")

        response = sms.send(message, [phone_number])
        print(f"[DEBUG] Africa's Talking Response: {response}")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to send SMS: {e}")
        return False
