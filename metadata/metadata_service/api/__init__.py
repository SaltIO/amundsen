from enum import Enum
import inspect
import logging
from http import HTTPStatus
from typing import Any, Iterable, List, Mapping, Optional, Tuple, Union

from flask_restful import Resource, reqparse

from ddp_auth.flask_integration import require_auth
from metadata_service.exception import NotFoundException
from metadata_service.proxy import BaseProxy


LOGGER = logging.getLogger(__name__)


from flask import request
from flask_restful import reqparse, Resource

class BaseAPI(Resource):
    def __init__(
        self,
        schema: Any,
        str_type: str,
        client: BaseProxy,
        id_qstring_key: str = None
    ) -> None:
        self.schema = schema
        self.client = client
        self.str_type = str_type
        self.allow_empty_upload = False
        self.id_qstring_key = id_qstring_key

        # Accept id from query OR path; don't mark as required here.
        if self.id_qstring_key:
            self.parser = reqparse.RequestParser()
            self.parser.add_argument(
                self.id_qstring_key,
                type=str,
                location=["args", "view_args"],  # <-- key change
                required=False                    # <-- don't force here
            )

    def get(self, **kwargs: Optional[Any]) -> Iterable[Union[Mapping, int, None]]:
        """
        Gets a single or multiple objects
        """
        # Prefer path/view_args first, then query param
        if self.id_qstring_key:
            # Merge both sources without raising
            args = self.parser.parse_args()
            q_id = args.get(self.id_qstring_key)
            if q_id and 'id' not in kwargs:
                kwargs['id'] = q_id

        # If we are in "detail" mode but id is still missing, 400
        is_detail_request = ('id' in kwargs) or (self.id_qstring_key and request.args.get(self.id_qstring_key))
        if is_detail_request and not kwargs.get('id'):
            return {'message': {'id': 'Missing required parameter'}}, HTTPStatus.BAD_REQUEST

        # Normalize id type (keep strings like emails; convert numeric strings to int)
        if 'id' in kwargs:
            if kwargs['id'] is not None:
                val = str(kwargs['id'])
                kwargs['id'] = int(val) if val.isdigit() else val
            else:
                kwargs.pop('id', None)

        try:
            get_func = getattr(self.client, f'get_{self.str_type}')
            actual_func = inspect.unwrap(get_func)
            get_func_params = dict(inspect.signature(actual_func).parameters)
            get_func_params.pop('self', None)

            LOGGER.info(f'get_func={self.str_type}')
            LOGGER.info(f'kwargs={kwargs}')
            LOGGER.info(f'get_func_params={get_func_params}')

            if len(kwargs) == 0 and len(get_func_params) > 0:
                # collection
                get_func = getattr(self.client, f'get_{self.str_type}s')
                get_result = get_func()
            else:
                # detail
                get_result = get_func(**kwargs)

            if get_result is not None:
                dump = self.schema().dump(
                    get_result,
                    many=isinstance(get_result, list)
                ), HTTPStatus.OK
                return dump
            else:
                return None, HTTPStatus.NOT_FOUND

        except NotFoundException:
            return {'message': f'Not Found: {kwargs}'}, HTTPStatus.NOT_FOUND
        except ValueError as e:
            return {'message': f'exception:{e}'}, HTTPStatus.BAD_REQUEST
