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
    PROPRIETARY_LICENSE = DataLicense(name="Proprietary License", alias="PROP", desc="This type of license is created by an organization to govern the use and distribution of its data within the confines of the organization or with specified external parties. The terms of a proprietary license are not public and are designed to restrict access, use, duplication, and distribution of the data to authorized users only.")
    PUBLIC_DOMAIN_DEDICATION = DataLicense(name="Public Domain Dedication", alias="CCO", desc="A public domain dedication tool that allows licensors to waive all their copyright and related rights, effectively placing their work in the public domain.")
    CREATIVE_COMMONS_LICENSE_BY_ATTRIBUTION = DataLicense(name="Creative Commons License By Attribution", alias="CC BY", desc="Allows users to distribute, remix, adapt, and build upon the material in any medium or format, as long as attribution is given to the creator.")
    CREATIVE_COMMONS_LICENSE_BY_ATTRIBUTION_SHARE_ALIKE = DataLicense(name="Creative Commons License By Attribution-ShareAlike", alias="CC BY-SA", desc="Allows users to distribute, remix, adapt, and build upon the material in any medium or format, as long as attribution is given to the creator, but requires adaptations of the work to be released under the same license.")
    CREATIVE_COMMONS_LICENSE_BY_ATTRIBUTION_NO_DERIVATIVES = DataLicense(name="Creative Commons License By Attribution-NoDerivatives", alias="CC BY-ND", desc="Allows for redistribution, commercial and non-commercial, as long as it is passed along unchanged and in whole, with credit to the creator.")
    CREATIVE_COMMONS_LICENSE_BY_ATTRIBUTION_NON_COMMERCIAL = DataLicense(name="Creative Commons License By Attribution-NonCommercial", alias="CC BY-NC", desc="Allows others to remix, tweak, and build upon the work non-commercially, and although their new works must also acknowledge the creator and be non-commercial, they don’t have to license their derivative works on the same terms.")
    OPEN_DATA_COMMONS_ATTRIBUTION_LICENSE = DataLicense(name="Open Data Commons Attribution License", alias="ODC-BY", desc="Allows users to use the data in any way, as long as they attribute the source of the data.")
    OPEN_DATA_COMMONS_DATABASE_LICENSE = DataLicense(name="Open Data Commons Open Database License", alias="ODC-ODbL", desc="Users are free to share, modify, and use the database while keeping the resulting databases open.")
    GNU_GENERAL_PUBLIC_LICENSE = DataLicense(name="GNU General Public License", alias="GPL", desc="A copyleft license primarily associated with software, but it can also be applied to data. It ensures that any derivative works are also open, meaning they must be licensed under the same terms.")
    MIT_LICENSE = DataLicense(name="MIT License", alias="MIT", desc="A permissive free software license originating at the Massachusetts Institute of Technology (MIT). It has minimal restrictions on how the software can be redistributed, allowing for both private and commercial use, distribution, modification, and private modification without conditions.")
    APACHE_LICENSE = DataLicense(name="Apache License", alias="Apache 2.0", desc="A permissive free software license written by the Apache Software Foundation. It allows users to freely use, modify, and distribute their own versions of the work, even in proprietary projects, provided that they include a copy of the license and notices that any changes have been made.")
    BSD_LICENSE = DataLicense(name="BSD License", alias="BSD", desc="A permissive free software licenses. The original versions require minimal restrictions on redistribution. This permits users to use portions of the code in proprietary products.")

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

@attr.s(auto_attribs=True, kw_only=True)
class DataChannel:
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    license: Optional[DataLicenseType] = None
    type: Optional[str] = None
    url: Optional[str] = None

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
class DataProvider:
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    data_channels: Optional[List[DataChannel]] = None
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
    category: Optional[str] = None
    path: str = None
    is_directory: bool = None
    dataLocation: Optional[Union[FilesystemDataLocation, AwsS3DataLocation, DataLocation]] = None
    dataProvider: Optional[DataProvider] = None
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
