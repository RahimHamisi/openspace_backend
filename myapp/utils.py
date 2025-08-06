from sightengine.client import SightengineClient # type: ignore
from django.conf import settings
import os

# client = SightengineClient('159894964', 'hN3ySs6WQRKxENgNXgGmZF82RmPxpoLe')

# def is_explicit_image(file_path):
#     full_path = os.path.join(settings.MEDIA_ROOT, file_path)
#     result = client.check('nudity').set_file(full_path)

#     nudity_data = result.get('nudity', {})
#     raw_score = nudity_data.get('raw', 0)

#     return raw_score > 0.5


client = SightengineClient('159894964', 'hN3ySs6WQRKxENgNXgGmZF82RmPxpoLe')

def is_explicit_image(file_path):
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if not os.path.exists(full_path):
        print("[⚠️ Warning] File not found:", full_path)
        return False

    result = client.check('nudity').set_file(full_path)
    nudity_data = result.get('nudity', {})
    raw_score = nudity_data.get('raw', 0)
    
    print(f"[Explicit Check] File: {file_path} | Raw Nudity Score: {raw_score}")

    return raw_score > 0.5

def is_inappropriate_text(text):
    result = client.check('profanity,personal,insult').set_text(text)
    
    profanity_matches = result.get('profanity', {}).get('matches', [])
    insult_matches = result.get('insult', {}).get('matches', [])
    personal_matches = result.get('personal', {}).get('matches', [])

    print(f"[Text Check] Inappropriate matches - Profanity: {profanity_matches}, Insults: {insult_matches}, Personal: {personal_matches}")

    return bool(profanity_matches or insult_matches or personal_matches)

