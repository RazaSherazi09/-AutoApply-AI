import requests
import sys

base = 'http://localhost:8000/api'

# Register a test user
test_user = {'email': 'testupload@example.com', 'password': 'password123', 'full_name': 'Test Upload'}
requests.post(f'{base}/auth/register', json=test_user)

# Login
r = requests.post(f'{base}/auth/token', json={'email': 'testupload@example.com', 'password': 'password123'})
if r.status_code != 200:
    print('Failed to login:', r.text)
    sys.exit(1)

token = r.json()['access_token']

# Create dummy PDF
with open('dummy.pdf', 'wb') as f:
    f.write(b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF')

# Upload
print('Uploading...')
try:
    r2 = requests.post(
        f'{base}/resumes/upload', 
        files={'file': open('dummy.pdf', 'rb')}, 
        headers={'Authorization': f'Bearer {token}'}
    )
    print(r2.status_code, r2.text)
except requests.exceptions.ConnectionError:
    print('ConnectionError! The server dropped the connection (Likely a segfault/crash).')
