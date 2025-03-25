from enum import Enum
import inspect
import logging
from http import HTTPStatus
from typing import Any, Iterable, List, Mapping, Optional, Tuple, Union

from flask_restful import Resource, reqparse

from metadata_service.auth.auth import requires_auth
from metadata_service.exception import NotFoundException
from metadata_service.proxy import BaseProxy


LOGGER = logging.getLogger(__name__)


class BaseAPI(Resource):
    def __init__(
            self,
            schema: Any,
            str_type: str,
            client: BaseProxy,
            id_qstring_key: str = None) -> None:

        self.schema = schema
        self.client = client
        self.str_type = str_type
        self.allow_empty_upload = False
        self.id_qstring_key = id_qstring_key

        if self.id_qstring_key:
            self.parser = reqparse.RequestParser()
            self.parser.add_argument(self.id_qstring_key, type=str, location="args", required=True)

    def get(self, **kwargs: Optional[Any]) -> Iterable[Union[Mapping, int, None]]:
        """
        Gets a single or multiple objects
        """
        if self.id_qstring_key:
            args = self.parser.parse_args()
            id = args.get(self.id_qstring_key, None)
            if id:
                kwargs['id'] = id

        if 'id' in kwargs:
            if kwargs['id'] is not None:
                kwargs['id'] = int(kwargs['id']) if kwargs['id'].isdigit() else kwargs['id']
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

            get_result = None
            if len(kwargs) == 0 and len(get_func_params) > 0:
                get_func = getattr(self.client, f'get_{self.str_type}s')
                get_result = get_func()
            else:
                get_result = get_func(**kwargs)

            if get_result is not None:
                dump = self.schema().dump(
                    get_result,
                    many=(True if isinstance(get_result, list) else False)
                ), HTTPStatus.OK

                return dump
            else:
                return None, HTTPStatus.NOT_FOUND
        except NotFoundException as nfe:
            return {'message': f'Not Found: {kwargs}'}, HTTPStatus.NOT_FOUND
        except ValueError as e:
            return {'message': f'exception:{e}'}, HTTPStatus.BAD_REQUEST
