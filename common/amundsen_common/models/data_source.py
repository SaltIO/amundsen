# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional, Union

import attr

from enum import Enum

from amundsen_common.models.user import User
from amundsen_common.models.badge import Badge
from amundsen_common.models.tag import Tag
from marshmallow3_annotations.ext.attrs import AttrsSchema
from marshmallow import fields
import marshmallow


class DataLicense:
    def __init__(self, name: str, desc: str, alias: str = None):
        self.name = name
        self.alias = alias
        self.desc = desc

class DataLicenseType(Enum):
    CREATIVE_COMMONS_LICENSES = DataLicense(name="Creative Commons licenses", desc="A set of copyright licenses that allow creators to specify the conditions under which their work may be used, adapted, and distributed. There are several types of Creative Commons licenses, each with its own terms and conditions regarding attribution, commercial use, and derivative works.")
    OPEN_DATA_COMMONS_PUBLIC_DOMAIN_DEDICATION = DataLicense(name="Open Data Commons Public Domain Dedication and License", alias="PDDL", desc="A license that allows creators to waive all their copyright and related rights over a work worldwide, placing it in the public domain. Anyone can then freely use, modify, and distribute the work without restrictions.")
    OPEN_DATA_COMMONS_ATTRIBUTION_LICENSE = DataLicense(name="Open Data Commons Attribution License", alias="ODC-BY", desc="A license that requires users to attribute the data provider when using the data. Users are free to use, modify, and distribute the data, but they must provide appropriate credit to the original source.")
    OPEN_DATA_COMMONS_DATABASE_LICENSE = DataLicense(name="Open Data Commons Open Database License", alias="ODbL", desc="A license that allows users to share, adapt, and distribute the database, but any new work must also be shared under the same license. It requires attribution and share-alike conditions.")
    GNU_GENERAL_PUBLIC_LICENSE = DataLicense(name="GNU General Public License", alias="GPL", desc="A copyleft license primarily associated with software, but it can also be applied to data. It ensures that any derivative works are also open, meaning they must be licensed under the same terms.")
    MIT_LICENSE = DataLicense(name="MIT License", desc="A permissive software license that allows users to use, modify, and distribute the software with minimal restrictions. It grants users the freedom to do almost anything they want with the software, including using it for commercial purposes, without requiring them to share their modifications.")
    APACHE_LICENSE = DataLicense(name="Apache License", desc="A permissive software license that allows users to use, modify, and distribute the software with minimal restrictions. It includes patent grant clauses, which provide some protection to users against patent claims.")
    ODC_ATTRIBUTION_LICENSE = DataLicense(name="ODC Attribution License", alias="ODC-By", desc="A license that requires users to attribute the data provider when using the data. It allows users to use, modify, and distribute the data with attribution, but there is no share-alike requirement.")
    ODC_OPEN_DATABASE_LICENSE = DataLicense(name="ODC Open Database License", alias="ODbL", desc="A license that allows users to share, adapt, and distribute the database. However, any new work must also be shared under the same license, and attribution is required.")

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

@attr.s(auto_attribs=True, kw_only=True)
class DataProvider:
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    # tags: List[Tag] = []
    # badges: List[Badge] = []


class DataProviderSchema(AttrsSchema):
    class Meta:
        target = DataProvider
        register_as_scheme = True


class AwsS3DataLocationSchema(AttrsSchema):
    class Meta:
        target = AwsS3DataLocation
        register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class DataChannel:
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    license: Optional[DataLicenseType] = None
    type: Optional[str] = None
    url: Optional[str] = None
    dataProvider: Optional[DataProvider] = None

class DataChannelSchema(AttrsSchema):
    license = fields.Method(serialize="get_license", deserialize="set_license")

    # Define methods to handle serialization and deserialization for dataLocation
    def get_license(self, obj):
        if obj.license is None:
            return None
        elif isinstance(obj.license, DataLicenseType):
            return obj.license.name
        elif isinstance(obj.license, str):
            return obj.license
        else:
            raise ValueError("Unsupported license type")

    def set_license(self, value):
        # Implement deserialization logic for dataLocation
        if isinstance(value, dict):
            return DataLicenseType[value['license']].value.name
        elif isinstance(value, str):
            for license_type in DataLicenseType:
                # Check if the enum_value is the one you're looking for
                if value == license_type.value.name or (license_type.value.alias and value == license_type.value.alias):
                    return license_type.value.name
        else:
            raise ValueError("Invalid license format")

    class Meta:
        target = DataChannel
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
    dataChannel: Optional[DataChannel] = None
    fileTables: Optional[List[FileTable]] = None
    prospectusWaterfallSchemes: Optional[List[ProspectusWaterfallScheme]] = None
    tags: Optional[List[Tag]] = None
    owners: Optional[List[User]] = None
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
