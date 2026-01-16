import urllib.request
import urllib.error
import json
import sys

def create_admin(name, email, password):
    url = 'http://localhost:5000/api/auth/register'
    payload = {
        'name': name,
        'email': email,
        'password': password,
        'role': 'admin'
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 201:
                print(f"SUCCESS: Admin user '{email}' created successfully!")
                print(f"You can now login at http://localhost:3000/login with these credentials.")
            else:
                print(f"Response: {response.read().decode()}")
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        if e.code == 400 and 'already exists' in error_body:
            print(f"INFO: User '{email}' already exists.")
            print("If this user is not an admin, you may need to manually update the role in MongoDB.")
        else:
            print(f"ERROR: Failed to create admin. Status: {e.code}")
            print(f"Response: {error_body}")
    except urllib.error.URLError as e:
        print(f"ERROR: Could not connect to backend. Make sure it is running at http://localhost:5000")
        print(f"Reason: {e.reason}")

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        create_admin(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("--- Create Admin Account ---")
        try:
            name = input("Enter Name: ").strip()
            email = input("Enter Email: ").strip()
            password = input("Enter Password: ").strip()
            
            if not name or not email or not password:
                print("Error: All fields are required.")
            else:
                create_admin(name, email, password)
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
