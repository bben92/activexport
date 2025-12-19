#!/usr/bin/env python3
"""
ActivExport - Strava OAuth2 authentication
Handles initial authorization and automatic token refresh
"""

import os
import json
import time
import webbrowser
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/callback'
TOKEN_FILE = 'activexport_tokens.json'

# Strava endpoints
AUTH_URL = 'https://www.strava.com/oauth/authorize'
TOKEN_URL = 'https://www.strava.com/oauth/token'


class CallbackHandler(BaseHTTPRequestHandler):
    """Handler to retrieve the authorization code"""

    def do_GET(self):
        """Handles OAuth redirect after authorization"""
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            self.server.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #FC4C02;">Authentication successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppresses HTTP server logs"""
        pass


def get_authorization_url():
    """Generates Strava authorization URL"""
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'read,activity:read_all,profile:read_all',
        'approval_prompt': 'auto'
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(auth_code):
    """Exchanges authorization code for access token"""
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code'
    }

    response = requests.post(TOKEN_URL, data=payload)
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token):
    """Refreshes expired access token"""
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    response = requests.post(TOKEN_URL, data=payload)
    response.raise_for_status()
    return response.json()


def save_tokens(token_data):
    """Saves tokens to JSON file"""
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)
    print(f"Tokens saved to {TOKEN_FILE}")


def load_tokens():
    """Loads tokens from JSON file"""
    if not os.path.exists(TOKEN_FILE):
        return None

    with open(TOKEN_FILE, 'r') as f:
        return json.load(f)


def get_valid_access_token():
    """
    Returns a valid access token
    Automatically refreshes if expired
    """
    tokens = load_tokens()

    if not tokens:
        print("[X] No token found. Run initial authentication first.")
        return None

    # Check if token is expired (with 5 min margin)
    if time.time() >= (tokens['expires_at'] - 300):
        print("Token expired, refreshing...")
        tokens = refresh_access_token(tokens['refresh_token'])
        save_tokens(tokens)
        print("Token successfully refreshed")

    return tokens['access_token']


def initial_authentication():
    """
    Initial authentication process
    Opens browser and starts local server to retrieve the code
    """
    print("\n" + "="*60)
    print("STRAVA AUTHENTICATION")
    print("="*60)

    # Generate authorization URL
    auth_url = get_authorization_url()

    print(f"\n[1] Opening browser for Strava authorization...")
    print(f"    URL: {auth_url}\n")

    # Open browser
    webbrowser.open(auth_url)

    print("[2] Local server started on http://localhost:8000")
    print("    Waiting for Strava redirect...\n")

    # Start local HTTP server
    server = HTTPServer(('localhost', 8000), CallbackHandler)
    server.auth_code = None

    # Wait for redirect (5 min timeout)
    timeout = time.time() + 300
    while not server.auth_code and time.time() < timeout:
        server.handle_request()

    if not server.auth_code:
        print("[X] Timeout: No authorization received after 5 minutes")
        return False

    print("[3] Authorization code received!")
    print("[4] Exchanging code for tokens...\n")

    try:
        # Exchange code for tokens
        token_data = exchange_code_for_token(server.auth_code)

        # Save tokens
        save_tokens(token_data)

        print("="*60)
        print("AUTHENTICATION SUCCESSFUL!")
        print("="*60)
        print(f"\nAthlete: {token_data['athlete']['firstname']} {token_data['athlete']['lastname']}")
        print(f"Token expires at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(token_data['expires_at']))}")
        print(f"\nTokens saved to: {TOKEN_FILE}")
        print("Tokens will be automatically refreshed when needed\n")

        return True

    except Exception as e:
        print(f"[X] Error during token exchange: {e}")
        return False


def test_api_connection():
    """Tests API connection by fetching athlete profile"""
    print("\n" + "="*60)
    print("STRAVA API CONNECTION TEST")
    print("="*60 + "\n")

    access_token = get_valid_access_token()

    if not access_token:
        print("[X] Unable to get valid token")
        return False

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        # Fetch athlete profile
        response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
        response.raise_for_status()
        athlete = response.json()

        print("API connection successful!\n")
        print("Athlete Profile:")
        print(f"   Name: {athlete['firstname']} {athlete['lastname']}")
        print(f"   City: {athlete.get('city', 'N/A')}")
        print(f"   Country: {athlete.get('country', 'N/A')}")
        print(f"   Weight: {athlete.get('weight', 'N/A')} kg")
        print(f"   Shoes: {athlete.get('shoes', [])}")

        # Count activities
        response = requests.get('https://www.strava.com/api/v3/athlete/activities',
                              headers=headers, params={'per_page': 1})
        print(f"\nAPI ready to fetch your activities!")
        print(f"   Limits: 100 req/15min, 1000 req/day (read)")

        return True

    except Exception as e:
        print(f"[X] Error during API test: {e}")
        return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test mode: check if tokens exist and test connection
        test_api_connection()
    else:
        # Initial authentication mode
        if initial_authentication():
            print("\nNext step: python activexport_auth.py test")
        else:
            print("\n[X] Authentication failed")
            sys.exit(1)
