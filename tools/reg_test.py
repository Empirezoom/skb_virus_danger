import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skb.settings')
import django
django.setup()

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile

def run_test():
    client = Client()
    data = {
        'first_name': 'Auto',
        'middle_name': 'T',
        'last_name': 'Tester',
        'email': 'autotest@example.com',
        'country_code': '+1',
        'phone': '5551234567',
        'ssn': '123-45-6789',
        'username': 'autotest_user_1',
        'password': 'Password123',
        'confirm_password': 'Password123',
        'id_type': 'passport',
    }

    files = {
        'id_front': SimpleUploadedFile('front.txt', b'front-file', content_type='text/plain'),
        'id_back': SimpleUploadedFile('back.txt', b'back-file', content_type='text/plain'),
    }

    print('Posting to /register/')
    resp = client.post('/register/', data=data, files=files, follow=True)
    print('Status code:', resp.status_code)
    print('Redirect chain:', resp.redirect_chain)
    body = resp.content.decode(errors='ignore')
    print('Body snippet:')
    print(body[:800])

if __name__ == '__main__':
    run_test()
