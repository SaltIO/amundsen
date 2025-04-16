from http import HTTPStatus
import logging
from typing import Tuple
import jose
import requests
from metadata_service import config
from amundsen_common.models.auth import AuthToken
import jwt
from jwt import PyJWKClient
from jose import jwt as JWT
from functools import wraps
from flask import request, jsonify, current_app


LOGGER = logging.getLogger(__name__)

READ_PERMISSION = 'read:metadata'
WRITE_PERMISSION = 'write:metadata'

def get_token(client_id: str, client_secret: str) -> Tuple[AuthToken, HTTPStatus]:

    if client_id != current_app.config.get('FLASK_OIDC_CLIENT_ID'):
        return {'message': 'Invalid client_id'}, HTTPStatus.UNAUTHORIZED

    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'audience': current_app.config['METADATA_API_AUTH0_API_AUDIENCE']
    }

    response = requests.post(
        f'{current_app.config["METADATA_API_AUTH0_ISSUER"]}oauth/token/', # Trailing slash part of config entry
        json=payload
    )

    if response.status_code != HTTPStatus.OK:
        return {'message': 'Invalid credentials', 'error': response.text}, HTTPStatus.UNAUTHORIZED

    token_data = response.json()

    auth_token = AuthToken(
        access_token=token_data['access_token'],
        expires_in=token_data['expires_in'],
        token_type=token_data['token_type']
    )

    return auth_token, HTTPStatus.OK

def requires_auth(required_permission: str = READ_PERMISSION):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization', None)
            if not token:
                return {'message': 'Token is missing'}, HTTPStatus.UNAUTHORIZED

            try:
                # Extract token from "Bearer " prefix
                token = token.split("Bearer ")[1]

                # Get the signing key using PyJWKClient
                jwks_url = f"{current_app.config['METADATA_API_AUTH0_ISSUER']}.well-known/jwks.json" # Trailing slash part of config entry
                jwks_client = PyJWKClient(jwks_url)
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                rsa_pem_key = signing_key.key  # Already in PEM format or key object

                # Decode the token
                payload = JWT.decode(
                    token,
                    rsa_pem_key,
                    algorithms=current_app.config["METADATA_API_AUTH0_ALGORITHMS"],
                    audience=current_app.config["METADATA_API_AUTH0_API_AUDIENCE"],
                    issuer=current_app.config["METADATA_API_AUTH0_ISSUER"],
                )

                # Validate the client_id in the payload
                client_id = payload.get('azp')
                LOGGER.info(f"payload={payload}")
                LOGGER.info(f"client_id={client_id}")
                LOGGER.info(f"FLASK_OIDC_CLIENT_ID={current_app.config.get('FLASK_OIDC_CLIENT_ID')}")
                if client_id != current_app.config.get('FLASK_OIDC_CLIENT_ID'):
                    return {'message': 'Token created from invalid client_id'}, HTTPStatus.UNAUTHORIZED

                # Authorize
                token_scopes = None
                unverified_claims = JWT.get_unverified_claims(token)
                if unverified_claims.get("scope"):
                    token_scopes = unverified_claims["scope"].split()

                LOGGER.info(f"required_permission={required_permission}")
                LOGGER.info(f"token_scopes={token_scopes}")

                if not token_scopes:
                    return {'message': 'No authentication token_scopes'}, HTTPStatus.FORBIDDEN

                # Check if the required permission is in the scope
                if required_permission is not None and (not token_scopes or required_permission not in token_scopes):
                    return {'message': 'Forbidden: Insufficient permissions'}, HTTPStatus.FORBIDDEN

                # LOGGER.info(f"READ_ONLY_MODE={current_app.config.get('READ_ONLY_MODE', False)}")
                if current_app.config.get('READ_ONLY_MODE', False) and required_permission != READ_PERMISSION:
                    return {
                        "message": "API is in read-only mode. Write operations are not allowed."
                    }, HTTPStatus.FORBIDDEN

            except jwt.PyJWKClientError as e:
                LOGGER.exception("Failed to fetch or match key from JWKS")
                return {'message': 'Invalid token', 'error': 'No matching key found'}, HTTPStatus.UNAUTHORIZED
            except jose.exceptions.ExpiredSignatureError as e:
                LOGGER.exception("Token Expired")
                return {'message': 'Token Expired', 'error': str(e)}, HTTPStatus.UNAUTHORIZED
            except jwt.exceptions.ExpiredSignatureError as e:
                LOGGER.exception("Token Expired")
                return {'message': 'Token Expired', 'error': str(e)}, HTTPStatus.UNAUTHORIZED
            except jwt.InvalidTokenError as e:
                LOGGER.exception("Token decoding failed")
                return {'message': 'Invalid token', 'error': str(e)}, HTTPStatus.UNAUTHORIZED
            except Exception as e:
                LOGGER.exception("Failed to auth")
                return {'message': 'Invalid token', 'error': str(e)}, HTTPStatus.UNAUTHORIZED

            LOGGER.info('TOKEN valid...calling function')
            return f(*args, **kwargs)

        return decorated_function
    return decorator