# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from typing import Dict, Any, Literal
from http import HTTPStatus

from flask import current_app as app
from .api_client import APIClient

LOGGER = logging.getLogger(__name__)


def get_query_param(args: Dict, param: str, error_msg: str = None) -> str:
    """
    Extracts a required query parameter from the request arguments
    :param args: The request arguments
    :param param: The parameter to extract
    :param error_msg: Optional error message to return if parameter is missing
    :return: The parameter value
    """
    value = args.get(param)
    if value is None:
        msg = 'A {0} parameter must be provided'.format(param) if error_msg is None else error_msg
        raise Exception(msg)
    return value


def request_metadata(
    *,     # type: ignore
    url: str,
    method: str = 'GET',
    headers=None,
    timeout_sec: int = 0,
    data=None,
    json=None,
    auth: bool = True
):
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
    client = APIClient('metadata')

    # Handle timeout
    kwargs = {}
    if timeout_sec > 0:
        kwargs['timeout'] = timeout_sec

    # Handle headers
    if headers:
        kwargs['headers'] = headers

    # Handle data/json
    if data:
        kwargs['data'] = data
    if json:
        kwargs['json'] = json

    # Make the request
    if method == 'GET':
        return client.get(url, **kwargs)
    elif method == 'POST':
        return client.post(url, **kwargs)
    elif method == 'PUT':
        return client.put(url, **kwargs)
    elif method == 'DELETE':
        return client.delete(url, **kwargs)
    else:
        raise ValueError(f"Unsupported method: {method}")


def request_search(
    *,     # type: ignore
    url: str,
    method: str = 'GET',
    headers=None,
    timeout_sec: int = 0,
    data=None,
    json=None,
    auth: bool = True
):
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
    client = APIClient('search')

    # Handle timeout
    kwargs = {}
    if timeout_sec > 0:
        kwargs['timeout'] = timeout_sec

    # Handle headers
    if headers:
        kwargs['headers'] = headers

    # Handle data/json
    if data:
        kwargs['data'] = data
    if json:
        kwargs['json'] = json

    # Make the request
    if method == 'GET':
        return client.get(url, **kwargs)
    elif method == 'POST':
        return client.post(url, **kwargs)
    elif method == 'PUT':
        return client.put(url, **kwargs)
    elif method == 'DELETE':
        return client.delete(url, **kwargs)
    else:
        raise ValueError(f"Unsupported method: {method}")
