"""
Test script for Face Recognition API.
Tests registration, verification, and recognition endpoints.
"""

import requests
import os
import sys

# Configuration
BASE_URL = 'http://localhost:5000'
TEST_EMAIL = 'test_face@example.com'
TEST_PASSWORD = 'password123'
TEST_NAME = 'Face Test User'

# Photo paths (update these with your actual photo paths)
REGISTRATION_PHOTOS = [
    'test_photos/photo1.jpg',
    'test_photos/photo2.jpg',
    'test_photos/photo3.jpg',
    'test_photos/photo4.jpg',
    'test_photos/photo5.jpg'
]
VERIFICATION_PHOTO = 'test_photos/verify.jpg'


def print_response(title, response):
    """Print formatted response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(response.json())
    print(f"{'='*60}\n")


def test_face_recognition_api():
    """Test face recognition API endpoints."""
    
    print("Starting Face Recognition API Tests...")
    
    # Step 1: Register user
    print("\n[1/6] Registering user...")
    register_response = requests.post(f'{BASE_URL}/api/auth/register', json={
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'name': TEST_NAME,
        'role': 'student'
    })
    
    if register_response.status_code == 201:
        print_response("User Registration", register_response)
        token = register_response.json()['data']['access_token']
        user_id = register_response.json()['data']['user']['user_id']
    elif register_response.status_code == 400 and 'already registered' in register_response.json()['message']:
        print("User already exists, logging in...")
        login_response = requests.post(f'{BASE_URL}/api/auth/login', json={
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD
        })
        print_response("User Login", login_response)
        token = login_response.json()['data']['access_token']
        user_id = login_response.json()['data']['user']['user_id']
    else:
        print_response("Registration Failed", register_response)
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Step 2: Check initial face status
    print("\n[2/6] Checking initial face status...")
    status_response = requests.get(f'{BASE_URL}/api/face/status', headers=headers)
    print_response("Initial Face Status", status_response)
    
    # Step 3: Register face with multiple photos
    print("\n[3/6] Registering face with multiple photos...")
    
    # Check if photos exist
    existing_photos = [p for p in REGISTRATION_PHOTOS if os.path.exists(p)]
    
    if len(existing_photos) < 3:
        print(f"ERROR: Need at least 3 photos. Found only {len(existing_photos)} photos.")
        print("Please update REGISTRATION_PHOTOS paths in the script.")
        print("\nSkipping face registration test...")
    else:
        files = [('photos', open(photo, 'rb')) for photo in existing_photos[:5]]
        
        try:
            register_face_response = requests.post(
                f'{BASE_URL}/api/face/register',
                headers=headers,
                files=files
            )
            print_response("Face Registration", register_face_response)
        finally:
            # Close files
            for _, f in files:
                f.close()
        
        # Step 4: Check face status after registration
        print("\n[4/6] Checking face status after registration...")
        status_response = requests.get(f'{BASE_URL}/api/face/status', headers=headers)
        print_response("Face Status After Registration", status_response)
        
        # Step 5: Verify face
        print("\n[5/6] Verifying face...")
        
        if os.path.exists(VERIFICATION_PHOTO):
            with open(VERIFICATION_PHOTO, 'rb') as f:
                verify_response = requests.post(
                    f'{BASE_URL}/api/face/verify',
                    headers=headers,
                    files={'photo': f}
                )
            print_response("Face Verification", verify_response)
        else:
            print(f"Verification photo not found: {VERIFICATION_PHOTO}")
            print("Skipping verification test...")
        
        # Step 6: Recognize face
        print("\n[6/6] Recognizing face...")
        
        if os.path.exists(VERIFICATION_PHOTO):
            with open(VERIFICATION_PHOTO, 'rb') as f:
                recognize_response = requests.post(
                    f'{BASE_URL}/api/face/recognize',
                    headers=headers,
                    files={'photo': f}
                )
            print_response("Face Recognition", recognize_response)
        else:
            print("Skipping recognition test...")
    
    # Cleanup option
    print("\n" + "="*60)
    cleanup = input("Delete test user and face registration? (y/n): ")
    
    if cleanup.lower() == 'y':
        # Delete face registration
        delete_face_response = requests.delete(
            f'{BASE_URL}/api/face/delete',
            headers=headers
        )
        print_response("Delete Face Registration", delete_face_response)
        
        # Note: User deletion requires admin privileges
        print("\nNote: User account deletion requires admin privileges.")
        print(f"Test user email: {TEST_EMAIL}")
    
    print("\nTests completed!")


if __name__ == '__main__':
    # Check if server is running
    try:
        health_response = requests.get(f'{BASE_URL}/health', timeout=5)
        if health_response.status_code == 200:
            print(f"✓ Server is running at {BASE_URL}")
            test_face_recognition_api()
        else:
            print(f"✗ Server returned status {health_response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to server at {BASE_URL}")
        print("Please make sure the Flask server is running:")
        print("  cd backend")
        print("  python app.py")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)
