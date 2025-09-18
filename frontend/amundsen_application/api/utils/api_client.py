import logging
from typing import Optional, Dict, Any
import requests
from flask import current_app
from http import HTTPStatus
import time
import threading

LOGGER = logging.getLogger(__name__)

# Module-level cache for tokens and expiry
_token_cache: Dict[str, Dict[str, Any]] = {}
_token_locks: Dict[str, threading.Lock] = {}

class APIClient:
    def __init__(self, api_name: str, base_url: Optional[str] = None, auth: bool = True):
        self.api_name = api_name
        self.base_url = base_url.rstrip('/') if base_url else self._get_base_url()
        self.auth = auth
        self.token: Optional[str] = None

    def _get_base_url(self) -> str:
        # Use Flask config to get the base URL for the API
        if self.api_name == 'metadata':
            return current_app.config.get('METADATASERVICE_BASE', '')
        elif self.api_name == 'search':
            return current_app.config.get('SEARCHSERVICE_BASE', '')
        elif self.api_name == 'reveal':
            return current_app.config.get('REVEAL_API_BASE', '')
        else:
            raise ValueError(f"Unknown API name: {self.api_name}")

    def _get_auth_token(self) -> str:
        global _token_cache, _token_locks
        cache_key = f"{self.api_name}_token"
        now = time.time()

        # Create a lock for this API if it doesn't exist
        if cache_key not in _token_locks:
            _token_locks[cache_key] = threading.Lock()
        lock = _token_locks[cache_key]

        # Double-checked locking pattern
        token_info = _token_cache.get(cache_key)
        if token_info and token_info.get('expires_at', 0) > now + 60:
            self.token = token_info['token']
            return self.token

        with lock:
            # Check again inside the lock
            token_info = _token_cache.get(cache_key)
            if token_info and token_info.get('expires_at', 0) > now + 60:
                self.token = token_info['token']
                return self.token

            # Fetch new token
            client_id = current_app.config.get('API_AUTH_CLIENT_ID')
            client_secret = current_app.config.get('API_AUTH_CLIENT_SECRET')
            if not client_id or not client_secret:
                raise Exception("API_AUTH_CLIENT_ID and API_AUTH_CLIENT_SECRET must be set in config")
            token_url = f"{self.base_url}/auth/token"
            payload = {
                "client_id": client_id,
                "client_secret": client_secret
            }
            try:
                resp = requests.post(token_url, json=payload, timeout=5)
                resp.raise_for_status()
                resp_json = resp.json()
                token = resp_json.get('access_token')
                expires_in = resp_json.get('expires_in', 3600)  # fallback to 1 hour
                if not token:
                    LOGGER.error(f"No access_token in response: {resp_json}")
                    raise Exception("No access_token in token response")
                expires_at = now + int(expires_in)
                _token_cache[cache_key] = {'token': token, 'expires_at': expires_at}
                self.token = token
                return token
            except Exception as e:
                LOGGER.error(f"Failed to get auth token from {token_url}: {e}")
                raise

    def _build_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = headers.copy() if headers else {}
        if self.auth:
            if not self.token:
                self.token = self._get_auth_token()
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _do_request(self, method: str, url: str, headers: dict, **kwargs) -> requests.Response:
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
        except Exception as e:
            LOGGER.error(f"Request error: {e}")
            raise
        return response

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        # If endpoint is already a full URL, use it as-is
        if endpoint.startswith(('http://', 'https://')):
            url = endpoint
        else:
            base_url = self.base_url.rstrip('/')
            endpoint_path = endpoint if endpoint.startswith('/') else '/' + endpoint
            url = f"{base_url}{endpoint_path}"

        # First attempt
        headers = self._build_headers(kwargs.pop("headers", None))
        response = self._do_request(method, url, headers, **kwargs)

        # If 401 and we have auth enabled, refresh token and try once more
        if response.status_code == HTTPStatus.UNAUTHORIZED and self.auth:
            LOGGER.warning("401 Unauthorized. Refreshing token and retrying...")
            cache_key = f"{self.api_name}_token"
            _token_cache.pop(cache_key, None)
            self.token = self._get_auth_token()

            # One more attempt with fresh token
            headers = self._build_headers(kwargs.pop("headers", None))
            response = self._do_request(method, url, headers, **kwargs)

        if response.status_code >= 400:
            LOGGER.error(f"API error: {response.status_code} {response.text}")

        return response

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        return self._request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        return self._request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self._request("DELETE", endpoint, **kwargs)