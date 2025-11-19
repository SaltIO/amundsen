# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from http import HTTPStatus
from typing import Any, Iterable, Mapping, Tuple, Union

from flasgger import swag_from
from flask import current_app as app, request
from flask_restful import Resource, fields, marshal

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.tag import Tag, TagSchema

from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client
from metadata_service.proxy.base_proxy import BaseProxy
from ddp_auth.flask_api_keys import require_auth


LOGGER = logging.getLogger(__name__)

tag_fields = {
    'tag_name': fields.String,
    'tag_count': fields.Integer
}

tag_usage_fields = {
    'tag_usages': fields.List(fields.Nested(tag_fields))
}


BADGE_TYPE = 'badge'


class TagAPI(Resource):
    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(TagAPI, self).__init__()

    @require_auth()
    @swag_from('swagger_doc/tag/tag_get.yml')
    def get(self) -> Iterable[Union[Mapping, int, None]]:
        """
        API to fetch all the existing tags with usage.
        """
        tag_usages = self.client.get_tags()
        return marshal({'tag_usages': tag_usages}, tag_usage_fields), HTTPStatus.OK

class TagPATCH(Resource):
    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(TagPATCH, self).__init__()

    @require_auth('write:metadata')
    @swag_from('swagger_doc/tag/tag_patch.yml')
    def patch(self) -> Iterable[Union[Mapping, int, None]]:
        """
        API to update a Tag
        """
        try:
            data = request.get_json(force=True)
            tag = self.client.update_tag(
                old_tag=data['old_tag'],
                new_tag=data['new_tag'],
                old_tag_type=data.get('old_tag_type', None),
                new_tag_type=data.get('new_tag_type', None)
            )

            result = TagSchema().dump(tag)

            return result, HTTPStatus.OK
        except NotFoundException as nfe:
            return {'message': f'Tag Not Found'}, HTTPStatus.NOT_FOUND
        except ValueError as ve:
            return {'message': f'exception:{ve}'}, HTTPStatus.BAD_REQUEST



class TagCommon:
    def __init__(self, client: BaseProxy) -> None:
        self.client = client

    def put(self, id: str, resource_type: ResourceType,
            tag: str, tag_type: str = 'default',
            published_tag: str = BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG) -> Tuple[Any, HTTPStatus]:
        """
        Method to add a tag to existing resource.

        :param id:
        :param resource_type:
        :param tag:
        :param tag_type:
        :return:
        """

        # whitelist_badges = app.config.get('WHITELIST_BADGES', [])
        if tag_type == BADGE_TYPE:
            return \
                {'message': 'Badges should be added using /badges/, tag_type=badge no longer valid'}, \
                HTTPStatus.NOT_ACCEPTABLE

        else:
            # for badge in whitelist_badges:
            #     if tag == badge.badge_name:
            #         return \
            #             {'message': 'The tag {} for id {} with type {} and resource_type {} '
            #                         'is not added successfully as tag '
            #                         'for it is reserved for badge'.format(tag,
            #                                                               id,
            #                                                               tag_type,
            #                                                               resource_type.name)}, \
            #             HTTPStatus.CONFLICT

            try:
                self.client.add_tag(id=id,
                                    tag=tag,
                                    tag_type=tag_type,
                                    resource_type=resource_type,
                                    published_tag=published_tag)
                return {'message': 'The tag {} for id {} with type {} and resource_type {} '
                                   'is added successfully'.format(tag,
                                                                  id,
                                                                  tag_type,
                                                                  resource_type.name)}, HTTPStatus.OK
            except NotFoundException:
                return \
                    {'message': 'The tag {} for table_uri {} with type {} and resource_type {} '
                                'is not added successfully'.format(tag,
                                                                   id,
                                                                   tag_type,
                                                                   resource_type.name)}, \
                    HTTPStatus.NOT_FOUND

    def delete(self, id: str, tag: str,
               resource_type: ResourceType, tag_type: str = 'default') -> Tuple[Any, HTTPStatus]:
        """
        Method to remove a association between a given tag and a resource.

        :param id:
        :param resource_type:
        :param tag:
        :param tag_type:
        :return:
        """

        try:
            self.client.delete_tag(id=id,
                                   tag=tag,
                                   tag_type=tag_type,
                                   resource_type=resource_type)
            return {'message': 'The tag {} for id {} with type {} and resource_type {} '
                               'is deleted successfully'.format(tag,
                                                                id,
                                                                tag_type,
                                                                resource_type.name)}, HTTPStatus.OK
        except NotFoundException:
            return \
                {'message': 'The tag {} for id {} with type {} and resource_type {} '
                            'is not deleted successfully'.format(tag,
                                                                 id,
                                                                 tag_type,
                                                                 resource_type.name)}, \
                HTTPStatus.NOT_FOUND
