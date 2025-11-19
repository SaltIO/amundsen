# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from http import HTTPStatus
from typing import Any, Iterable, Mapping, Optional, Union

from flask import request
from flask_restful import Resource
from flasgger import swag_from

from ddp_auth.api_keys import (
    APIKeyService,
    create_api_key_service,
    APIKeyCreateRequest,
    APIKeyResponse,
    APIKeyCreateResponse,
    get_service_name
)
from ddp_auth.flask_api_keys import require_bearer_auth

LOGGER = logging.getLogger(__name__)


def get_api_key_service() -> APIKeyService:
    """Get API key service instance."""
    try:
        return create_api_key_service()
    except Exception as e:
        LOGGER.error(f"Failed to create API key service: {e}")
        return None


class APIKeyCreateAPI(Resource):
    """API endpoint for creating API keys."""

    @require_bearer_auth("cmdrvl_metadata_search:admin")
    @swag_from('swagger_doc/api_key/create.yml')
    def post(self) -> Iterable[Union[Mapping, int, tuple, None]]:
        """Create a new API key for the configured service.

        Service name is automatically set from API_KEYS_SERVICE_NAME environment variable.
        """
        try:
            data = request.get_json(force=True) or {}
            if not data or 'name' not in data:
                return {'message': 'name is required'}, HTTPStatus.BAD_REQUEST

            # Get configured service name
            service_name = get_service_name()
            if not service_name:
                return {'message': 'API_KEYS_SERVICE_NAME not configured'}, HTTPStatus.INTERNAL_SERVER_ERROR

            api_key_service = get_api_key_service()
            if not api_key_service:
                return {'message': 'API key service unavailable'}, HTTPStatus.INTERNAL_SERVER_ERROR

            create_request = APIKeyCreateRequest(**data)
            current_user = request.user.get('sub', 'unknown')

            LOGGER.info(f"Creating API key '{create_request.name}' for service '{service_name}' by user {current_user}")

            response = api_key_service.create_api_key(create_request, service=service_name, created_by=current_user)

            LOGGER.info(f"API key created successfully: ID {response.id}")
            return response.model_dump(mode='json'), HTTPStatus.CREATED

        except Exception as e:
            LOGGER.error(f"Failed to create API key: {e}", exc_info=True)
            return {'message': f'Failed to create API key: {str(e)}'}, HTTPStatus.INTERNAL_SERVER_ERROR


class APIKeyListAPI(Resource):
    """API endpoint for listing API keys."""

    @require_bearer_auth("cmdrvl_metadata_search:admin")
    @swag_from('swagger_doc/api_key/list.yml')
    def get(self) -> Iterable[Union[Mapping, int, tuple, None]]:
        """List API keys for the configured service.

        Only returns keys for the service configured via API_KEYS_SERVICE_NAME.
        """
        try:
            # Get configured service name
            service_name = get_service_name()
            if not service_name:
                return {'message': 'API_KEYS_SERVICE_NAME not configured'}, HTTPStatus.INTERNAL_SERVER_ERROR

            current_user = request.user.get('sub', 'unknown')

            LOGGER.info(f"Listing API keys for service '{service_name}' by user {current_user}")

            api_key_service = get_api_key_service()
            if not api_key_service:
                return {'message': 'API key service unavailable'}, HTTPStatus.INTERNAL_SERVER_ERROR

            api_keys = api_key_service.list_api_keys(service=service_name)

            LOGGER.info(f"Found {len(api_keys)} API keys")
            return [key.model_dump(mode='json') for key in api_keys], HTTPStatus.OK

        except Exception as e:
            LOGGER.error(f"Failed to list API keys: {e}", exc_info=True)
            return {'message': f'Failed to list API keys: {str(e)}'}, HTTPStatus.INTERNAL_SERVER_ERROR


class APIKeyGetAPI(Resource):
    """API endpoint for getting a specific API key."""

    @require_bearer_auth("cmdrvl_metadata_search:admin")
    @swag_from('swagger_doc/api_key/get.yml')
    def get(self, key_id: int) -> Iterable[Union[Mapping, int, tuple, None]]:
        """Get a specific API key by ID for the configured service.

        Only returns keys for the service configured via API_KEYS_SERVICE_NAME.
        """
        try:
            # Get configured service name
            service_name = get_service_name()
            if not service_name:
                return {'message': 'API_KEYS_SERVICE_NAME not configured'}, HTTPStatus.INTERNAL_SERVER_ERROR

            current_user = request.user.get('sub', 'unknown')
            LOGGER.info(f"Getting API key {key_id} for service '{service_name}' by user {current_user}")

            api_key_service = get_api_key_service()
            if not api_key_service:
                return {'message': 'API key service unavailable'}, HTTPStatus.INTERNAL_SERVER_ERROR

            api_key = api_key_service.get_api_key(key_id, service=service_name)
            if not api_key:
                return {'message': f'API key with ID {key_id} not found for service \'{service_name}\''}, HTTPStatus.NOT_FOUND

            LOGGER.info(f"Found API key {key_id}: {api_key.name}")
            return api_key.model_dump(mode='json'), HTTPStatus.OK

        except Exception as e:
            LOGGER.error(f"Failed to get API key {key_id}: {e}", exc_info=True)
            return {'message': f'Failed to get API key: {str(e)}'}, HTTPStatus.INTERNAL_SERVER_ERROR


class APIKeyRevokeAPI(Resource):
    """API endpoint for revoking API keys."""

    @require_bearer_auth("cmdrvl_metadata_search:admin")
    @swag_from('swagger_doc/api_key/revoke.yml')
    def delete(self, key_id: int) -> Iterable[Union[Mapping, int, tuple, None]]:
        """Revoke (deactivate) an API key for the configured service.

        Only revokes keys for the service configured via API_KEYS_SERVICE_NAME.
        """
        try:
            # Get configured service name
            service_name = get_service_name()
            if not service_name:
                return {'message': 'API_KEYS_SERVICE_NAME not configured'}, HTTPStatus.INTERNAL_SERVER_ERROR

            current_user = request.user.get('sub', 'unknown')
            LOGGER.info(f"Revoking API key {key_id} for service '{service_name}' by user {current_user}")

            api_key_service = get_api_key_service()
            if not api_key_service:
                return {'message': 'API key service unavailable'}, HTTPStatus.INTERNAL_SERVER_ERROR

            success = api_key_service.revoke_api_key(key_id, service=service_name)
            if not success:
                return {'message': f'API key {key_id} not found'}, HTTPStatus.NOT_FOUND

            LOGGER.info(f"API key {key_id} revoked successfully")
            return {}, HTTPStatus.NO_CONTENT

        except Exception as e:
            LOGGER.error(f"Failed to revoke API key {key_id}: {e}", exc_info=True)
            return {'message': f'Failed to revoke API key: {str(e)}'}, HTTPStatus.INTERNAL_SERVER_ERROR


class APIKeyDeleteAPI(Resource):
    """API endpoint for permanently deleting API keys."""

    @require_bearer_auth("cmdrvl_metadata_search:admin")
    @swag_from('swagger_doc/api_key/delete.yml')
    def delete(self, key_id: int) -> Iterable[Union[Mapping, int, tuple, None]]:
        """Permanently delete an API key for the configured service.

        Only deletes keys for the service configured via API_KEYS_SERVICE_NAME.
        """
        try:
            # Get configured service name
            service_name = get_service_name()
            if not service_name:
                return {'message': 'API_KEYS_SERVICE_NAME not configured'}, HTTPStatus.INTERNAL_SERVER_ERROR

            current_user = request.user.get('sub', 'unknown')
            LOGGER.info(f"Permanently deleting API key {key_id} for service '{service_name}' by user {current_user}")

            api_key_service = get_api_key_service()
            if not api_key_service:
                return {'message': 'API key service unavailable'}, HTTPStatus.INTERNAL_SERVER_ERROR

            success = api_key_service.delete_api_key(key_id, service=service_name)
            if not success:
                return {'message': f'API key {key_id} not found'}, HTTPStatus.NOT_FOUND

            LOGGER.info(f"API key {key_id} deleted permanently")
            return {}, HTTPStatus.NO_CONTENT

        except Exception as e:
            LOGGER.error(f"Failed to delete API key {key_id}: {e}", exc_info=True)
            return {'message': f'Failed to delete API key: {str(e)}'}, HTTPStatus.INTERNAL_SERVER_ERROR


class APIKeyBulkDeleteAPI(Resource):
    """API endpoint for bulk deleting API keys."""

    @require_bearer_auth("cmdrvl_metadata_search:admin")
    @swag_from('swagger_doc/api_key/bulk_delete.yml')
    def delete(self) -> Iterable[Union[Mapping, int, tuple, None]]:
        """Bulk delete API keys for the configured service.

        Only deletes keys for the service configured via API_KEYS_SERVICE_NAME.
        """
        try:
            # Get configured service name
            service_name = get_service_name()
            if not service_name:
                return {'message': 'API_KEYS_SERVICE_NAME not configured'}, HTTPStatus.INTERNAL_SERVER_ERROR

            data = request.get_json(force=True) or {}
            key_ids = data.get('key_ids', [])
            permanent = data.get('permanent', False)

            current_user = request.user.get('sub', 'unknown')
            LOGGER.info(f"Bulk {'permanent' if permanent else 'soft'} delete request by user {current_user}: key_ids={key_ids}, service={service_name}")

            api_key_service = get_api_key_service()
            if not api_key_service:
                return {'message': 'API key service unavailable'}, HTTPStatus.INTERNAL_SERVER_ERROR

            deleted_count = 0

            if key_ids:
                # Delete specific keys (only for configured service)
                for key_id in key_ids:
                    if permanent:
                        success = api_key_service.delete_api_key(key_id, service=service_name)
                    else:
                        success = api_key_service.revoke_api_key(key_id, service=service_name)
                    if success:
                        deleted_count += 1
                        LOGGER.info(f"Deleted API key {key_id}")
                    else:
                        LOGGER.warning(f"Failed to delete API key {key_id} (may not belong to service '{service_name}')")

                return {
                    "message": "Bulk delete completed",
                    "deleted_count": deleted_count,
                    "requested_count": len(key_ids),
                    "permanent": permanent,
                    "service": service_name
                }, HTTPStatus.OK

            else:
                # Delete all keys for the configured service
                all_keys = api_key_service.list_api_keys(service=service_name)
                for key in all_keys:
                    if permanent:
                        success = api_key_service.delete_api_key(key.id, service=service_name)
                    else:
                        success = api_key_service.revoke_api_key(key.id, service=service_name)
                    if success:
                        deleted_count += 1

                return {
                    "message": f"Bulk delete completed for service '{service_name}'",
                    "deleted_count": deleted_count,
                    "total_keys": len(all_keys),
                    "permanent": permanent,
                    "service": service_name
                }, HTTPStatus.OK

        except Exception as e:
            LOGGER.error(f"Failed to bulk delete API keys: {e}", exc_info=True)
            return {'message': f'Failed to bulk delete API keys: {str(e)}'}, HTTPStatus.INTERNAL_SERVER_ERROR

