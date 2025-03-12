import logging
import requests
from metadata_service import config
from amundsen_common.models.auth import AuthToken
import jwt
from jwt import PyJWKClient
from functools import wraps
from flask import request, jsonify, current_app


LOGGER = logging.getLogger(__name__)


def get_token(client_id: str, client_secret: str) -> AuthToken:
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'audience': current_app.config['METADATA_API_AUTH0_API_AUDIENCE'],
    }

    response = requests.post(
        f'https://{current_app.config["METADATA_API_AUTH0_DOMAIN"]}/oauth/token',
        json=payload
    )

    if response.status_code != 200:
        return jsonify({'message': 'Invalid credentials', 'error': response.text}), 401

    token_data = response.json()

    auth_token = AuthToken(
        access_token=token_data['access_token'],
        expires_in=token_data['expires_in'],
        token_type=token_data['token_type']
    )
    return auth_token


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', None)
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            # Extract token from "Bearer " prefix
            token = token.split("Bearer ")[1]
            LOGGER.info(f"token={token}")

            # Get the signing key using PyJWKClient
            jwks_url = f"https://{current_app.config['METADATA_API_AUTH0_DOMAIN']}/.well-known/jwks.json"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            rsa_pem_key = signing_key.key  # Already in PEM format or key object
            LOGGER.info(f"Retrieved key with kid={signing_key.key_id}")

            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            LOGGER.info(f'unverified_payload={unverified_payload}')
            LOGGER.info(f"iss={unverified_payload.get('iss')}")
            LOGGER.info(f"METADATA_API_AUTH0_ISSUER={current_app.config['METADATA_API_AUTH0_ISSUER']}")


            # Decode the token
            payload = jwt.decode(
                token,
                rsa_pem_key,
                algorithms=current_app.config["METADATA_API_AUTH0_ALGORITHMS"],
                audience=current_app.config["METADATA_API_AUTH0_API_AUDIENCE"],
                issuer=current_app.config["METADATA_API_AUTH0_ISSUER"]
            )
            LOGGER.info(f"payload={payload}")
            request.auth_payload = payload

        except jwt.PyJWKClientError as e:
            LOGGER.exception("Failed to fetch or match key from JWKS")
            return jsonify({'message': 'Invalid token', 'error': 'No matching key found'}), 401
        except jwt.InvalidTokenError as e:
            LOGGER.exception("Token decoding failed")
            return jsonify({'message': 'Invalid token', 'error': str(e)}), 401
        except Exception as e:
            LOGGER.exception("Failed to auth")
            return jsonify({'message': 'Invalid token', 'error': str(e)}), 401

        LOGGER.info('TOKEN valid...calling function')
        return f(*args, **kwargs)
    return decorated