import os
from dotenv import load_dotenv
import pathlib
from urllib.parse import urlencode
import webbrowser
from flask import Flask, request
import requests
import json

# Get the directory where this script is located
BASE_DIR = pathlib.Path(__file__).parent.absolute()

# Load the .env file from that directory
env_path = BASE_DIR / '.env'
print(f"Looking for .env file at: {env_path}")
load_dotenv(dotenv_path=env_path)

# Access variables
CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET")

print(f"CLIENT_ID found: {'Yes' if CLIENT_ID else 'No'}")
print(f"CLIENT_SECRET found: {'Yes' if CLIENT_SECRET else 'No'}")

# Add validation
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("LinkedIn API credentials not found in environment variables")

def get_access_token_manually():
    # Using only the w_member_social scope which is needed for posting
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri=http://localhost:8000/callback&scope=w_member_social%20r_basicprofile&state=random_state_string"
    
    print("\n\n" + "="*80)
    print("Step 1: Visit this URL in your browser and authorize your app:")
    print(auth_url)
    print("="*80 + "\n")
    
    print("Step 2: After authorization, you'll be redirected to a URL.")
    print("Copy ONLY the 'code' parameter value from the URL.")
    print("Example: If you see http://localhost:8000/callback?code=AQTdPuXg6_9d&state=random_state_string")
    print("        Just copy: AQTdPuXg6_9d")
    
    auth_code = input("\nPaste ONLY the code value here: ")
    
    # Step 3: Exchange code for token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": "http://localhost:8000/callback",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    print("\nExchanging code for access token...")
    response = requests.post(token_url, data=payload)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        print("\nSuccess! Your access token is:")
        print("="*80)
        print(access_token)
        print("="*80)
        print("\nSave this token for posting to LinkedIn.")
        return access_token
    else:
        print(f"\nError: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    get_access_token_manually()