# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import distutils.util
import logging
import os
import ast
from typing import Any, Callable, Dict, List, Optional, Set  # noqa: F401

import boto3
from flask import Flask  # noqa: F401
import neo4j

from metadata_service.entity.badge import Badge

# PROXY configuration keys
PROXY_HOST = 'PROXY_HOST'
PROXY_PORT = 'PROXY_PORT'
PROXY_USER = 'PROXY_USER'
PROXY_PASSWORD = 'PROXY_PASSWORD'
PROXY_ENCRYPTED = 'PROXY_ENCRYPTED'
PROXY_VALIDATE_SSL = 'PROXY_VALIDATE_SSL'
PROXY_DATABASE_NAME = 'PROXY_DATABASE_NAME'
PROXY_CLIENT = 'PROXY_CLIENT'
PROXY_CLIENT_KWARGS = 'PROXY_CLIENT_KWARGS'

PROXY_CLIENTS = {
    'NEO4J': 'metadata_service.proxy.neo4j_proxy.Neo4jProxy',
    'NEO4J_FABRIC': 'metadata_service.proxy.neo4j_fabric_proxy.Neo4jFabricProxy',
}

IS_STATSD_ON = 'IS_STATSD_ON'
USER_OTHER_KEYS = 'USER_OTHER_KEYS'


class Config:
    LOG_FORMAT = '%(asctime)s.%(msecs)03d [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d (%(process)d:' \
                 '%(threadName)s) - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    LOG_LEVEL = 'INFO'

    # Path to the logging configuration file to be used by `fileConfig()` method
    # https://docs.python.org/3.7/library/logging.config.html#logging.config.fileConfig
    # LOG_CONFIG_FILE = 'metadata_service/logging.conf'
    LOG_CONFIG_FILE = None

    PROXY_USER = os.environ.get('CREDENTIALS_PROXY_USER', 'neo4j')
    PROXY_PASSWORD = os.environ.get('CREDENTIALS_PROXY_PASSWORD', 'test')

    PROXY_ENCRYPTED = True
    """Whether the connection to the proxy should use SSL/TLS encryption."""

    # Prior to enable PROXY_VALIDATE_SSL, you need to configure SSL.
    # https://neo4j.com/docs/operations-manual/current/security/ssl-framework/
    PROXY_VALIDATE_SSL = False
    """Whether the SSL/TLS certificate presented by the user should be validated against the system's trusted CAs."""

    PROXY_DATABASE_NAME = None

    IS_STATSD_ON = False

    # Configurable dictionary to influence format of column statistics displayed in UI
    STATISTICS_FORMAT_SPEC: Dict[str, Dict] = {}

    # whitelist badges
    # WHITELIST_BADGES: List[Badge] = []

    SWAGGER_ENABLED = os.environ.get('SWAGGER_ENABLED', True)

    USER_DETAIL_METHOD = None  # type: Optional[function]

    RESOURCE_REPORT_CLIENT = None  # type: Optional[function]

    # On User detail method, these keys will be added into amundsen_common.models.user.User.other_key_values
    USER_OTHER_KEYS = {'mode_user_id'}  # type: Set[str]

    # DEPRECATED (since version 3.6.0): Please use `POPULAR_RESOURCES_MINIMUM_READER_COUNT`
    # Number of minimum reader count to qualify for popular resources
    POPULAR_TABLE_MINIMUM_READER_COUNT = None
    POPULAR_RESOURCES_MINIMUM_READER_COUNT = 10  # type: int

    # List of regexes which will exclude certain parameters from appearing as Programmatic Descriptions
    PROGRAMMATIC_DESCRIPTIONS_EXCLUDE_FILTERS = []  # type: list

    # Custom kwargs that will be passed to proxy client. Can be used to fine-tune parameters like timeout
    # or num of retries
    PROXY_CLIENT_KWARGS: Dict = dict()

    # Initialize custom flask extensions and routes
    INIT_CUSTOM_EXT_AND_ROUTES = None  # type: Callable[[Flask], None]

    SWAGGER_TEMPLATE_PATH = os.path.join('api', 'swagger_doc', 'template.yml')
    SWAGGER = {
        'openapi': '3.0.2',
        'title': 'CMD+RVL Metadata API',
        'uiversion': 3
    }
    SWAGGER_URL_PREFIX = os.getenv('SWAGGER_URL_PREFIX', None)
    if SWAGGER_URL_PREFIX:
        SWAGGER['specs_route'] = SWAGGER_URL_PREFIX
    SWAGGER_VALIDATION = os.getenv("SWAGGER_VALIDATION", "true").lower() in ("true", "1", "yes")

    METADATA_API_AUTH0_DOMAIN = os.environ['METADATA_API_AUTH0_DOMAIN']      # e.g., your-domain.auth0.com
    METADATA_API_AUTH0_API_AUDIENCE = os.environ['METADATA_API_AUTH0_API_AUDIENCE']  # e.g., neo4j-api or https://neo4j-api.example.com
    METADATA_API_AUTH0_ISSUER = f'https://{METADATA_API_AUTH0_DOMAIN}/'
    METADATA_API_AUTH0_ALGORITHMS = os.environ['METADATA_API_AUTH0_ALGORITHMS']
    if METADATA_API_AUTH0_ALGORITHMS:
        METADATA_API_AUTH0_ALGORITHMS = ast.literal_eval(METADATA_API_AUTH0_ALGORITHMS)

    LOG_REQUESTS = os.environ['METADATA_API_LOG_REQUESTS']

    READ_ONLY_MODE = os.getenv('METADATA_SERVICE_READ_ONLY_MODE', 'false').lower() in ('1', 'true', 'yes')

class LocalConfig(Config):
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    LOCAL_HOST = '0.0.0.0'

    PROXY_HOST = os.environ.get('PROXY_HOST', f'bolt://{LOCAL_HOST}')
    PROXY_PORT = os.environ.get('PROXY_PORT', 7687)
    PROXY_DATABASE_NAME = os.environ.get('PROXY_DATABASE_NAME', neo4j.DEFAULT_DATABASE)
    proxy_client_key = os.environ.get('PROXY_CLIENT', 'NEO4J')
    PROXY_CLIENT = PROXY_CLIENTS[proxy_client_key if proxy_client_key != '' else 'NEO4J']
    PROXY_ENCRYPTED = bool(distutils.util.strtobool(os.environ.get(PROXY_ENCRYPTED, 'True')))
    PROXY_VALIDATE_SSL = bool(distutils.util.strtobool(os.environ.get(PROXY_VALIDATE_SSL, 'False')))

    IS_STATSD_ON = bool(distutils.util.strtobool(os.environ.get(IS_STATSD_ON, 'False')))

    SWAGGER_ENABLED = True


class LocalFederatedConfig(LocalConfig):
    PROXY_DATABASE_NAME = os.environ.get('PROXY_DATABASE_NAME', neo4j.DEFAULT_DATABASE)

