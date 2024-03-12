# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional, Union

import attr

from amundsen_common.models.badge import Badge
from amundsen_common.models.tag import Tag
from marshmallow3_annotations.ext.attrs import AttrsSchema
from marshmallow import fields
import marshmallow


@attr.s(auto_attribs=True, kw_only=True)
class DataLocation:
    name: str
    key: Optional[str] = None
    type: Optional[str] = None


class DataLocationSchema(AttrsSchema):
    class Meta:
        target = DataLocation
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class FilesystemDataLocation(DataLocation):
    drive: Optional[str] = None


class FilesystemDataLocationSchema(AttrsSchema):
    class Meta:
        target = FilesystemDataLocation
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class AwsS3DataLocation(DataLocation):
    bucket: Optional[str] = None


class AwsS3DataLocationSchema(AttrsSchema):
    class Meta:
        target = AwsS3DataLocation
        register_as_scheme = True

# class DataLocationUnion(fields.Field):
#     def __init__(self,
#                  **kwargs):

#         self._candidate_fields = [FilesystemDataLocation, AwsS3DataLocation, DataLocation]
#         super().__init__(**kwargs)


#     def _serialize(self, value, attr, obj, **kwargs):
#         error_store = kwargs.pop("error_store", marshmallow.error_store.ErrorStore())
#         fields = self._candidate_fields
#         if self._reverse_serialize_candidates:
#             fields = list(reversed(fields))

#         for candidate_field in fields:

#             try:
#                 # pylint: disable=protected-access
#                 return candidate_field._serialize(
#                     value, attr, obj, error_store=error_store, **kwargs
#                 )
#             except (TypeError, ValueError) as e:
#                 error_store.store_error({attr: e})

#         raise marshmallow.exceptions.ValidationError(message=error_store.errors, field_name=attr)
#         # raise ExceptionGroup("All serializers raised exceptions.\n", error_store.errors)

#     def _deserialize(self, value, attr, data, **kwargs):
#         errors = []
#         for candidate_field in self._candidate_fields:
#             try:
#                 return candidate_field.deserialize(value, attr, data, **kwargs)
#             except marshmallow.exceptions.ValidationError as exc:
#                 errors.append(exc.messages)
#         raise marshmallow.exceptions.ValidationError(message=errors, field_name=attr)

# class DataLocationUnionSchema(AttrsSchema):
#     class Meta:
#         target = DataLocationUnion
#         register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class DataChannel:
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    license: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    data_locations: Optional[List[DataLocation]]


class DataChannelSchema(AttrsSchema):
    class Meta:
        target = DataChannel
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class DataProvider:
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    data_channels: List[DataChannel]
    # tags: List[Tag] = []
    # badges: List[Badge] = []


class DataProviderSchema(AttrsSchema):
    class Meta:
        target = DataProvider
        register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class FileTable:
    name: str
    content: str

class FileTableSchema(AttrsSchema):
    class Meta:
        target = FileTable
        register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class ProspectusScheme:
    shortName: str
    details: str

class ProspectusSchemeSchema(AttrsSchema):
    class Meta:
        target = ProspectusScheme
        register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class ProspectusWaterfallScheme:
    name: str
    scheme: List[ProspectusScheme]

class ProspectusWaterfallSchemeSchema(AttrsSchema):
    class Meta:
        target = ProspectusWaterfallScheme
        register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class File:
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    type: str = None
    category: str = None
    path: str = None
    is_directory: bool = None
    dataLocation: Optional[Union[FilesystemDataLocation, AwsS3DataLocation, DataLocation]] = None
    fileTables: Optional[List[FileTable]] = None
    prospectusWaterfallSchemes: Optional[List[ProspectusWaterfallScheme]] = None
    tags: Optional[List[Tag]] = None
    # badges: List[Badge] = []


class FileSchema(AttrsSchema):
    dataLocation = fields.Method(serialize="get_data_location", deserialize="set_data_location")

    # Define methods to handle serialization and deserialization for dataLocation
    def get_data_location(self, obj):
        if obj.dataLocation is None:
            return None
        elif isinstance(obj.dataLocation, FilesystemDataLocation):
            return FilesystemDataLocationSchema().dump(obj.dataLocation)
        elif isinstance(obj.dataLocation, AwsS3DataLocation):
            return AwsS3DataLocationSchema().dump(obj.dataLocation)
        elif isinstance(obj.dataLocation, DataLocation):
            return DataLocationSchema().dump(obj.dataLocation)
        else:
            raise ValueError("Unsupported data location type")

    def set_data_location(self, value):
        # Implement deserialization logic for dataLocation
        if isinstance(value, dict):
            if 'filesystem' == value['type']:
                return FilesystemDataLocationSchema().load(value)
            if 'aws_s3' == value['type']:
                return AwsS3DataLocationSchema().load(value)
            else:
                return DataLocationSchema().load(value)
        else:
            raise ValueError("Invalid data location format")

    class Meta:
        target = File
        register_as_scheme = True


# this is a temporary hack to satisfy mypy. Once https://github.com/python/mypy/issues/6136 is resolved, use
# `attr.converters.default_if_none(default=False)`
def default_if_none(arg: Optional[bool]) -> bool:
    return arg or False
