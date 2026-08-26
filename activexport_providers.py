#!/usr/bin/env python3
"""
ActivExport - Multi-provider configuration and shared OAuth2 helpers
Supports Strava and Decathlon Coach (Sports Tracking Data API)
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

REDIRECT_URI = 'http://localhost:8000/callback'

# Provider configuration registry.
# 'token_style' controls how the authorization code / refresh token is
# exchanged with the token endpoint:
#   'form'  -> parameters sent as POST form data (Strava)
#   'query' -> parameters sent as URL query string (Decathlon Coach)
PROVIDERS = {
    'strava': {
        'label': 'Strava',
        'auth_url': 'https://www.strava.com/oauth/authorize',
        'token_url': 'https://www.strava.com/oauth/token',
        'api_base': 'https://www.strava.com/api/v3',
        'scope': 'read,activity:read_all,profile:read_all',
        'client_id_env': 'STRAVA_CLIENT_ID',
        'client_secret_env': 'STRAVA_CLIENT_SECRET',
        'token_file': 'activexport_tokens_strava.json',
        'token_style': 'form',
        'profile_path': 'athlete',
    },
    'decathcoach': {
        'label': 'Decathlon Coach',
        'auth_url': 'https://api.decathlon.net/connect/oauth/authorize',
        'token_url': 'https://api.decathlon.net/connect/oauth/token',
        'api_base': 'https://api.decathlon.net/sportstrackingdata/v2',
        'scope': 'profile openid email sports_tracking_data',
        'client_id_env': 'DECATHLON_CLIENT_ID',
        'client_secret_env': 'DECATHLON_CLIENT_SECRET',
        'api_key_env': 'DECATHLON_API_KEY',
        'token_file': 'activexport_tokens_decathcoach.json',
        'token_style': 'query',
        'profile_path': 'me',
    },
}


def get_provider_config(provider):
    """Returns the configuration dict for the given provider name"""
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Choices: {list(PROVIDERS)}")
    return PROVIDERS[provider]


def get_client_credentials(provider):
    """Reads client_id/client_secret from environment for the given provider"""
    config = get_provider_config(provider)
    client_id = os.getenv(config['client_id_env'])
    client_secret = os.getenv(config['client_secret_env'])
    return client_id, client_secret


def get_authorization_url(provider):
    """Generates the OAuth2 authorization URL for the given provider"""
    config = get_provider_config(provider)
    client_id, _ = get_client_credentials(provider)

    from urllib.parse import urlencode

    params = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': config['scope'],
    }

    if provider == 'strava':
        params['approval_prompt'] = 'auto'
    elif provider == 'decathcoach':
        params['locale'] = 'fr_FR'
        params['state'] = '123454'

    return f"{config['auth_url']}?{urlencode(params)}"


def _post_token_request(provider, payload):
    """Sends the token request using the provider's expected style"""
    config = get_provider_config(provider)
    if config['token_style'] == 'query':
        response = requests.post(config['token_url'], params=payload)
    else:
        response = requests.post(config['token_url'], data=payload)
    response.raise_for_status()
    return response.json()


def exchange_code_for_token(provider, auth_code):
    """Exchanges authorization code for access token"""
    client_id, client_secret = get_client_credentials(provider)
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    }
    return _normalize_token_data(_post_token_request(provider, payload))


def refresh_access_token(provider, refresh_token):
    """Refreshes expired access token"""
    client_id, client_secret = get_client_credentials(provider)
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }
    return _normalize_token_data(_post_token_request(provider, payload))


def _normalize_token_data(token_data):
    """Ensures 'expires_at' (unix timestamp) is always present"""
    if 'expires_at' not in token_data and 'expires_in' in token_data:
        token_data['expires_at'] = int(time.time()) + int(token_data['expires_in'])
    return token_data


def save_tokens(provider, token_data):
    """Saves tokens to the provider's JSON file"""
    config = get_provider_config(provider)
    with open(config['token_file'], 'w') as f:
        json.dump(token_data, f, indent=2)
    print(f"Tokens saved to {config['token_file']}")


def load_tokens(provider):
    """Loads tokens from the provider's JSON file"""
    config = get_provider_config(provider)
    token_file = config['token_file']

    # Backward compatibility: migrate the legacy single-provider token file
    # (used before multi-provider support) to the new Strava-specific file.
    legacy_file = 'activexport_tokens.json'
    if provider == 'strava' and not os.path.exists(token_file) and os.path.exists(legacy_file):
        os.rename(legacy_file, token_file)

    if not os.path.exists(token_file):
        return None
    with open(token_file, 'r') as f:
        return json.load(f)


def get_valid_access_token(provider):
    """
    Returns a valid access token for the given provider
    Automatically refreshes if expired
    """
    tokens = load_tokens(provider)

    if not tokens:
        print("[X] No token found. Run initial authentication first.")
        return None

    # Check if token is expired (with 5 min margin)
    if time.time() >= (tokens['expires_at'] - 300):
        print("Token expired, refreshing...")
        tokens = refresh_access_token(provider, tokens['refresh_token'])
        save_tokens(provider, tokens)
        print("Token successfully refreshed")

    return tokens['access_token']


def get_auth_headers(provider, access_token):
    """Builds the HTTP headers required to call the provider's API"""
    headers = {'Authorization': f'Bearer {access_token}'}
    config = get_provider_config(provider)
    if 'api_key_env' in config:
        api_key = os.getenv(config['api_key_env'])
        if api_key:
            headers['x-api-key'] = api_key
    return headers
