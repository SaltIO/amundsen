# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from http import HTTPStatus
import json
from typing import Dict
import logging

import requests
from flask import current_app as app, jsonify, make_response

import traceback


LOGGER = logging.getLogger(__name__)

AUTH_TOKEN_ENDPOINT = '/auth/token'
AUTH_TOKEN = None


def get_query_param(args: Dict, param: str, error_msg: str = None) -> str:
    value = args.get(param)
    if value is None:
        msg = 'A {0} parameter must be provided'.format(param) if error_msg is None else error_msg
        raise Exception(msg)
    return value


def request_metadata(*,     # type: ignore
                     url: str,
                     method: str = 'GET',
                     headers=None,
                     timeout_sec: int = 0,
                     data=None,
                     json=None,
                     auth: bool = True):
    """
    Helper function to make a request to metadata service.
    Sets the client and header information based on the configuration
    :param headers: Optional headers for the request, e.g. specifying Content-Type
    :param method: DELETE | GET | POST | PUT
    :param url: The request URL
    :param timeout_sec: Number of seconds before timeout is triggered.
    :param data: Optional request payload
    :return:
    """
    if headers is None:
        headers = {}

    if app.config['REQUEST_HEADERS_METHOD']:
        headers.update(app.config['REQUEST_HEADERS_METHOD'](app))
    elif app.config['METADATASERVICE_REQUEST_HEADERS']:
        headers.update(app.config['METADATASERVICE_REQUEST_HEADERS'])
    return request_wrapper(method=method,
                           url=url,
                           client=app.config['METADATASERVICE_REQUEST_CLIENT'],
                           headers=headers,
                           timeout_sec=timeout_sec,
                           data=data,
                           json=json,
                           auth=auth)


def request_search(*,     # type: ignore
                   url: str,
                   method: str = 'GET',
                   headers=None,
                   timeout_sec: int = 0,
                   data=None,
                   json=None,
                   auth: bool = False):
    """
    Helper function to make a request to search service.
    Sets the client and header information based on the configuration
    :param headers: Optional headers for the request, e.g. specifying Content-Type
    :param method: DELETE | GET | POST | PUT
    :param url: The request URL
    :param timeout_sec: Number of seconds before timeout is triggered.
    :param data: Optional request payload
    :return:
    """
    if headers is None:
        headers = {}

    if app.config['REQUEST_HEADERS_METHOD']:
        headers.update(app.config['REQUEST_HEADERS_METHOD'](app))
    elif app.config['SEARCHSERVICE_REQUEST_HEADERS']:
        headers.update(app.config['SEARCHSERVICE_REQUEST_HEADERS'])

    return request_wrapper(method=method,
                           url=url,
                           client=app.config['SEARCHSERVICE_REQUEST_CLIENT'],
                           headers=headers,
                           timeout_sec=timeout_sec,
                           data=data,
                           json=json,
                           auth=auth)


def _get_auth_token():
    global AUTH_TOKEN

    LOGGER.info("_get_auth_token")

    try:
        url = app.config['METADATASERVICE_BASE'] + AUTH_TOKEN_ENDPOINT
        payload = {
            'client_id': app.config['METADATA_API_AUTH_CLIENT_ID'],
            'client_secret': app.config['METADATA_API_AUTH_CLIENT_SECRET']
        }

        response = request_metadata(
            method="POST",
            url=url,
            json=json.dumps(payload),
            auth=False)
        status_code = response.status_code

        if status_code == HTTPStatus.OK:
            message = 'Success'
            AUTH_TOKEN = response.json().get('access_token')
            LOGGER.info("Successfully retreived Auth Token")
        else:
            raise Exception('Auth Token Service Unavailable')
    except Exception as e:
        LOGGER.exception("Failed to retreive Auth Token")
        raise e

# TODO: Define an interface for envoy_client
def request_wrapper(method: str, url: str, client, headers, timeout_sec: int, data=None, json=None, auth: bool = True):  # type: ignore
    """
    Wraps a request to use Envoy client and headers, if available
    :param method: DELETE | GET | POST | PUT
    :param url: The request URL
    :param client: Optional Envoy client
    :param headers: Optional Envoy request headers
    :param timeout_sec: Number of seconds before timeout is triggered. Not used with Envoy
    :param data: Optional request payload
    :return:
    """
    global AUTH_TOKEN

    stack = traceback.format_stack()
    LOGGER.info(f'request_wrapper API: \n url={url} \n auth={auth}\n headers={headers} \n AUTH_TOKEN={AUTH_TOKEN}\n {"".join(stack)}')

    if auth and auth == True:
        if not AUTH_TOKEN:
            _get_auth_token()

        if not headers:
            headers = {}

        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

    # If no timeout specified, use the one from the configurations.
    timeout_sec = timeout_sec or app.config['REQUEST_SESSION_TIMEOUT_SEC']

    LOGGER.info(f'Calling API: \n url={url}\n headers={headers}')

    attempts = 0
    while(attempts < 3):
        response = None
        if client is not None:
            if method == 'DELETE':
                response = client.delete(url, headers=headers, raw_response=True, data=data, json=json)
            elif method == 'GET':
                response = client.get(url, headers=headers, raw_response=True)
            elif method == 'POST':
                response = client.post(url, headers=headers, raw_response=True, raw_request=True, data=data, json=json)
            elif method == 'PUT':
                response = client.put(url, headers=headers, raw_response=True, raw_request=True, data=data, json=json)
            else:
                raise Exception('Method not allowed: {}'.format(method))
        else:
            with build_session() as s:
                if method == 'DELETE':
                    response = s.delete(url, headers=headers, timeout=timeout_sec, data=data, json=json)
                elif method == 'GET':
                    response = s.get(url, headers=headers, timeout=timeout_sec)
                elif method == 'POST':
                    response = s.post(url, headers=headers, timeout=timeout_sec, data=data, json=json)
                elif method == 'PUT':
                    response = s.put(url, headers=headers, timeout=timeout_sec, data=data, json=json)
                else:
                    raise Exception('Method not allowed: {}'.format(method))

        LOGGER.info(f'Response: \n url={url}\n code={response.status_code}\n json={response.json()}')

        if auth and response and response.status_code == 401:
            LOGGER.warning("Metadata Service Request Failed (401).  Retrieving new Auth Token")
            _get_auth_token()
        else:
            return response

        attempts = attempts + 1

def build_session() -> requests.Session:
    session = requests.Session()

    cert = app.config.get('MTLS_CLIENT_CERT')
    key = app.config.get('MTLS_CLIENT_KEY')
    if cert is not None and key is not None:
        session.cert = (cert, key)

    return session
