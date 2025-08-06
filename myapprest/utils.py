from cryptography.fernet import Fernet
from django.conf import settings

def decrypt_phone_number(encrypted_number):
    fernet = Fernet(settings.FERNET_KEY)
    return fernet.decrypt(encrypted_number.encode()).decode()
