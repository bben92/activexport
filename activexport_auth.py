#!/usr/bin/env python3
"""
ActivExport - OAuth2 authentication
Handles initial authorization and automatic token refresh
Supports multiple providers: Strava and Decathlon Coach
"""

import argparse
import sys
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

from activexport_providers import (
    PROVIDERS,
    get_provider_config,
    get_authorization_url,
    exchange_code_for_token,
    save_tokens,
    get_valid_access_token,
    get_auth_headers,
)


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


def initial_authentication(provider):
    """
    Initial authentication process
    Opens browser and starts local server to retrieve the code
    """
    config = get_provider_config(provider)

    print("\n" + "="*60)
    print(f"{config['label'].upper()} AUTHENTICATION")
    print("="*60)

    # Generate authorization URL
    auth_url = get_authorization_url(provider)

    print(f"\n[1] Opening browser for {config['label']} authorization...")
    print(f"    URL: {auth_url}\n")

    # Open browser
    webbrowser.open(auth_url)

    print("[2] Local server started on http://localhost:8000")
    print("    Waiting for redirect...\n")

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
        token_data = exchange_code_for_token(provider, server.auth_code)

        # Save tokens
        save_tokens(provider, token_data)

        print("="*60)
        print("AUTHENTICATION SUCCESSFUL!")
        print("="*60)

        athlete = token_data.get('athlete')
        if athlete:
            print(f"\nAthlete: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
        print(f"Token expires at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(token_data['expires_at']))}")
        print(f"\nTokens saved to: {config['token_file']}")
        print("Tokens will be automatically refreshed when needed\n")

        return True

    except Exception as e:
        print(f"[X] Error during token exchange: {e}")
        return False


def test_api_connection(provider):
    """Tests API connection by fetching the user/athlete profile"""
    config = get_provider_config(provider)

    print("\n" + "="*60)
    print(f"{config['label'].upper()} API CONNECTION TEST")
    print("="*60 + "\n")

    access_token = get_valid_access_token(provider)

    if not access_token:
        print("[X] Unable to get valid token")
        return False

    headers = get_auth_headers(provider, access_token)

    try:
        # Fetch profile (athlete for Strava, me for Decathlon Coach)
        response = requests.get(f"{config['api_base']}/{config['profile_path']}", headers=headers)
        response.raise_for_status()
        profile = response.json()

        print("API connection successful!\n")
        print("Profile:")
        if provider == 'strava':
            print(f"   Name: {profile.get('firstname', '')} {profile.get('lastname', '')}")
            print(f"   City: {profile.get('city', 'N/A')}")
            print(f"   Country: {profile.get('country', 'N/A')}")
            print(f"   Weight: {profile.get('weight', 'N/A')} kg")
        else:
            print(f"   ID: {profile.get('id', 'N/A')}")
            print(f"   Country: {profile.get('country', 'N/A')}")
            print(f"   Language: {profile.get('language', 'N/A')}")
            print(f"   Birth date: {profile.get('birthDate', 'N/A')}")

        print(f"\nAPI ready to fetch your activities!")

        return True

    except Exception as e:
        print(f"[X] Error during API test: {e}")
        return False


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='ActivExport OAuth2 authentication (Strava or Decathlon Coach).'
    )
    parser.add_argument(
        'action',
        nargs='?',
        choices=['test'],
        default=None,
        help='Optional action: "test" to check API connection with saved tokens'
    )
    parser.add_argument(
        '--provider',
        choices=list(PROVIDERS),
        default='strava',
        help='Activity provider to authenticate with (default: strava)'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    if args.action == 'test':
        # Test mode: check if tokens exist and test connection
        if not test_api_connection(args.provider):
            sys.exit(1)
    else:
        # Initial authentication mode
        if initial_authentication(args.provider):
            print(f"\nNext step: python activexport_auth.py --provider {args.provider} test")
        else:
            print("\n[X] Authentication failed")
            sys.exit(1)
