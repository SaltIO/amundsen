from typing import (
    Iterator, Optional, Dict, Union, List
)
from enum import Enum
from abc import ABC, abstractmethod
import re

from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable
from databuilder.models.description_metadata import (  # noqa: F401
    DESCRIPTION_NODE_LABEL, DESCRIPTION_NODE_LABEL_VAL, DescriptionMetadata,
)
from databuilder.models.table_metadata import TagMetadata


# def convert_to_uri_safe_str(input_string: str) -> str:
#     return re.sub(r'\W+', '_', input_string).lower()

def _format_as_list(tags: Union[List, str, None]) -> List:
    if tags is None:
        tags = []
    if isinstance(tags, str):
        tags = list(filter(None, tags.split(',')))
    if isinstance(tags, list):
        tags = [tag.lower().strip() for tag in tags]
    return tags


class DataProvider(GraphSerializable):

    DATA_PROVIDER_NODE_LABEL = 'Data_Provider'
    DATA_PROVIDER_NODE_KEY = "data_provider://{name}"
    DATA_PROVIDER_NODE_ATTR_NAME = 'name'
    DATA_PROVIDER_NODE_ATTR_WEBSITE = 'website'
    # Should be broken out to a Description node
    DATA_PROVIDER_NODE_ATTR_DESC = 'desc'


    def __init__(self,
                 name: str,
                 website: str,
                 desc: str
                 ) -> None:

        self.name = name
        self.website = website
        self.desc = desc

        self._node_iter = self._create_node_iterator()

    def __repr__(self) -> str:
        return f'DataProvider({self.get_key()!r}, {self.name!r}, {self.website!r}, {self.desc!r})'

    def create_next_node(self) -> Optional[GraphNode]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        pass

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        yield GraphNode(
            key=self.get_key(),
            label=self.DATA_PROVIDER_NODE_LABEL,
            attributes={
                self.DATA_PROVIDER_NODE_ATTR_NAME: self.name,
                self.DATA_PROVIDER_NODE_ATTR_WEBSITE: self.website,
                self.DATA_PROVIDER_NODE_ATTR_DESC: self.desc
            }
        )

    def get_name_for_uri(self) -> str:
        # return convert_to_uri_safe_str(self.name)
        return self.name

    def get_key(self) -> str:
        return self.DATA_PROVIDER_NODE_KEY.format(name=self.get_name_for_uri())


class DataChannel(GraphSerializable):

    class DataChannelType(Enum):
        DATA_FEED = 'data_feed'
        DATA_SHARE = 'data_share'
        API = 'api'
        SFTP = 'sftp'


    DATA_CHANNEL_NODE_LABEL = 'Data_Channel'
    DATA_CHANNEL_NODE_KEY = "{data_provider_name}://{name}/{type}"
    DATA_CHANNEL_NODE_ATTR_NAME = 'name'
    DATA_CHANNEL_NODE_ATTR_TYPE = 'type'
    DATA_CHANNEL_NODE_ATTR_URL = 'url'
    # Should be broken out to a Description node
    DATA_CHANNEL_NODE_ATTR_DESC = 'desc'
    DATA_CHANNEL_NODE_ATTR_LICENSE = 'license'

    DATA_CHANNEL_RELATION_TYPE = 'DATA_CHANNEL'
    DATA_CHANNEL_OF_RELATION_TYPE = 'DATA_CHANNEL_OF'


    def __init__(self,
                 name: str,
                 type: DataChannelType,
                 url: str,
                 desc: str,
                 license: str,
                 data_provider: DataProvider
                 ) -> None:

        self.name = name
        self.type = type
        self.url = url
        self.desc = desc
        self.license = license

        self.data_provider = data_provider

        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()

    def __repr__(self) -> str:
        return f'DataChannel({self.get_key()!r}, {self.name!r}, {self.type.value!r}, {self.url!r}, {self.desc!r}, {self.license!r})'

    def create_next_node(self) -> Optional[GraphNode]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        yield GraphNode(
            key=self.get_key(),
            label=self.DATA_CHANNEL_NODE_LABEL,
            attributes={
                self.DATA_CHANNEL_NODE_ATTR_NAME: self.name,
                self.DATA_CHANNEL_NODE_ATTR_TYPE: self.type.value,
                self.DATA_CHANNEL_NODE_ATTR_URL: self.url,
                self.DATA_CHANNEL_NODE_ATTR_DESC: self.desc,
                self.DATA_CHANNEL_NODE_ATTR_LICENSE: self.license
            }
        )

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        yield GraphRelationship(
            start_label=self.data_provider.get_key(),
            start_key=DataProvider.DATA_PROVIDER_NODE_LABEL,
            end_label=self.DATA_CHANNEL_NODE_LABEL,
            end_key=self.get_key(),
            type=self.DATA_CHANNEL_RELATION_TYPE,
            reverse_type=self.DATA_CHANNEL_OF_RELATION_TYPE,
            attributes={}
        )

    def get_key(self) -> str:
        return self.DATA_CHANNEL_NODE_KEY.format(data_provider_name=self.data_provider.get_name_for_uri(),
                                                #  name=convert_to_uri_safe_str(self.name),
                                                 name=self.name,
                                                 type=self.type.value)


class DataLocation(GraphSerializable):

    class DataLocationType(Enum):
        FILESYSTEM = 'filesystem'
        AWS_S3 = 'aws_s3'
        SHAREPOINT = 'sharepoint'

    DATA_LOCATION_NODE_LABEL = 'Data_Location'
    DATA_LOCATION_ATTR_NAME = 'name'
    DATA_LOCATION_ATTR_TYPE = 'type'
    DATA_LOCATION_NODE_KEY = "{type}://{name}"

    DATA_LOCATION_RELATION_TYPE = 'DATA_LOCATION'
    DATA_LOCATION_OF_RELATION_TYPE = 'DATA_LOCATION_OF'


    def __init__(self,
                 name: str,
                 type: str) -> None:

        self.name = name
        self.type = type

        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()

    def __repr__(self) -> str:
        return f'Data_Location({self.name!r}, {self.type!r})'

    def create_next_node(self) -> Optional[GraphNode]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        yield GraphNode(
            key=self.get_key(),
            label=self.DATA_LOCATION_NODE_LABEL,
            attributes=self._get_node_attributes()
        )

    def _get_node_attributes(self) -> Dict[str,str]:
        return {
            self.DATA_LOCATION_ATTR_NAME: self.name,
            self.DATA_LOCATION_ATTR_TYPE: self.type
        }

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        # yield GraphRelationship(
        #     start_label=DataChannel.DATA_CHANNEL_NODE_LABEL,
        #     start_key=self.data_channel.get_key(),
        #     end_label=self.DATA_LOCATION_NODE_LABEL,
        #     end_key=self.get_key(),
        #     type=self.DATA_LOCATION_RELATION_TYPE,
        #     reverse_type=self.DATA_LOCATION_OF_RELATION_TYPE,
        #     attributes={}
        # )
        pass

    def get_key(self) -> str:
        return DataLocation.DataLocationType.DATA_LOCATION_NODE_KEY.format(
            # name=convert_to_uri_safe_str(self.name),
            name=self.name,
            type=self.type)

    def get_root(self) -> str:
        return 'NA'


class FilesystemDataLocation(DataLocation):

    FILESYSTEM_DATA_LOCATION_ATTR_DRIVE = "drive"
    DATA_LOCATION_NODE_KEY = f"{DataLocation.DATA_LOCATION_NODE_KEY}"+ "/{drive}"

    def __init__(self,
                 name: str,
                 drive: str
                 ) -> None:

        super().__init__(name=name, type='filesystem')

        self.drive = drive

    def _get_node_attributes(self) -> Dict[str,str]:
        return super()._get_node_attributes().update({
            self.FILESYSTEM_DATA_LOCATION_ATTR_DRIVE: self.drive
        })

    def get_key(self) -> str:
        return FilesystemDataLocation.DATA_LOCATION_NODE_KEY.format(
            # name=convert_to_uri_safe_str(self.name),
            name=self.name,
            type=self.type,
            drive=self.drive)
            # drive=convert_to_uri_safe_str(self.drive))

    def get_root(self) -> str:
        return self.drive


class AwsS3DataLocation(DataLocation):

    AWS_S3_DATA_LOCATION_ATTR_BUCKET = "bucket"
    DATA_LOCATION_NODE_KEY = f"{DataLocation.DATA_LOCATION_NODE_KEY}" + "/{bucket}"

    def __init__(self,
                 name: str,
                 bucket: str
                 ) -> None:

        super().__init__(name=name, type='aws_s3')

        self.bucket = bucket

    def _get_node_attributes(self) -> Dict[str,str]:
        return super()._get_node_attributes().update({
            self.AWS_S3_DATA_LOCATION_ATTR_BUCKET: self.bucket
        })

    def get_key(self) -> str:
        return AwsS3DataLocation.DATA_LOCATION_NODE_KEY.format(
            # name=convert_to_uri_safe_str(self.name),
            name=self.name,
            type=self.type,
            # bucket=convert_to_uri_safe_str(self.bucket))
            bucket=self.bucket)

    def get_root(self) -> str:
        return self.bucket

class SharepointDataLocation(DataLocation):

    SHAREPOINT_DATA_LOCATION_ATTR_DOCUMENT_LIBRARY = "document_library"
    DATA_LOCATION_NODE_KEY = f"{DataLocation.DATA_LOCATION_NODE_KEY}" + "/{document_library}"

    def __init__(self,
                 name: str,
                 document_library: str
                 ) -> None:

        super().__init__(name=name, type='sharepoint')

        self.document_library = document_library

    def _get_node_attributes(self) -> Dict[str,str]:
        return super()._get_node_attributes().update({
            self.SHAREPOINT_DATA_LOCATION_ATTR_DOCUMENT_LIBRARY: self.document_library
        })

    def get_key(self) -> str:
        return SharepointDataLocation.DATA_LOCATION_NODE_KEY.format(
            # name=convert_to_uri_safe_str(self.name),
            name=self.name,
            type=self.type,
            # document_library=convert_to_uri_safe_str(self.bucket))
            document_library=self.bucket)

    def get_root(self) -> str:
        return self.document_library


class File(GraphSerializable):

    FILE_NODE_LABEL = 'File'
    FILE_NODE_ATTR_NAME = 'name'
    FILE_NODE_ATTR_PATH = 'path'
    FILE_NODE_ATTR_TYPE = 'type'
    FILE_NODE_ATTR_CATEGORY = 'category'
    FILE_NODE_ATTR_IS_DIRECTORY= 'is_directory'

    FILE_RELATION_TYPE = 'FILE'
    FILE_OF_RELATION_TYPE = 'FILE_OF'

    FILE_DESCRIPTION_FORMAT = '{data_location_type}://{data_location_name}/{data_location_root}/{file_type}/{file_name}/_description'


    def __init__(self,
                 name: str,
                 type: str,
                 category: str,
                 path: str,
                 is_directory: bool,
                 description: Union[str, None] = None,
                 data_location: DataLocation = None,
                 data_channel: DataChannel = None,
                 tags: Union[List, str] = None) -> None:

        self.name = name
        if description:
            self.set_description(description=description)
        else:
            self.description = None
        self.type = type
        self.category = category
        self.path = path
        self.is_directory = is_directory

        self.data_location = data_location
        self.data_channel = data_channel

        self.tags = _format_as_list(tags)

        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()


    def __repr__(self) -> str:
        return f'File({self.name!r}, {self.description!r}, {self.type!r}, {self.category!r}, {self.path!r}, {self.is_directory!r})'

    def set_description(self, description: str):
        self.description = DescriptionMetadata.create_description_metadata(text=description)

    def create_next_node(self) -> Optional[GraphNode]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        yield GraphNode(
            key=self.get_key(),
            label=self.FILE_NODE_LABEL,
            attributes={
                self.FILE_NODE_ATTR_NAME: self.name,
                self.FILE_NODE_ATTR_TYPE: self.type,
                self.FILE_NODE_ATTR_CATEGORY: self.category,
                self.FILE_NODE_ATTR_PATH: self.path,
                self.FILE_NODE_ATTR_IS_DIRECTORY: self.is_directory
            }
        )

        if self.description:
            node_key = self._get_file_description_key(self.description)
            yield self.description.get_node(node_key)

        # Create the table tag nodes
        if self.tags:
            for tag in self.tags:
                tag_node = TagMetadata(tag).get_node()
                yield tag_node

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        if self.data_location:
            yield GraphRelationship(
                start_label=DataLocation.DATA_LOCATION_NODE_LABEL,
                start_key=self.data_location.get_key(),
                end_label=self.FILE_NODE_LABEL,
                end_key=self.get_key(),
                type=self.FILE_RELATION_TYPE,
                reverse_type=self.FILE_OF_RELATION_TYPE,
                attributes={}
            )

        if self.data_channel:
            yield GraphRelationship(
                start_label=DataLocation.DATA_CHANNEL_NODE_LABEL,
                start_key=self.data_channel.get_key(),
                end_label=self.FILE_NODE_LABEL,
                end_key=self.get_key(),
                type=self.FILE_RELATION_TYPE,
                reverse_type=self.FILE_OF_RELATION_TYPE,
                attributes={}
            )

        if self.description:
            yield self.description.get_relation(File.FILE_NODE_LABEL,
                                                self.get_key(),
                                                self._get_file_description_key(self.description))

        if self.tags:
            for tag in self.tags:
                tag_relationship = GraphRelationship(
                    start_label=File.FILE_NODE_LABEL,
                    start_key=self.get_key(),
                    end_label=TagMetadata.TAG_NODE_LABEL,
                    end_key=TagMetadata.get_tag_key(tag),
                    type=TagMetadata.ENTITY_TAG_RELATION_TYPE,
                    reverse_type=TagMetadata.TAG_ENTITY_RELATION_TYPE,
                    attributes={}
                )
                yield tag_relationship

    def _get_file_description_key(self, description: DescriptionMetadata) -> str:
        return File.FILE_DESCRIPTION_FORMAT.format(data_location_type=self.data_location.type,
                                                   data_location_name=self.data_location.name,
                                                   data_location_root=self.data_location.get_root(),
                                                   file_type=self.type,
                                                   file_name=self.name)
                                                #    data_location_name=convert_to_uri_safe_str(self.data_location.name),
                                                #    data_location_root=convert_to_uri_safe_str(self.data_location.get_root()),
                                                #    file_type=convert_to_uri_safe_str(self.type),
                                                #    file_name=convert_to_uri_safe_str(self.name))

    def get_key(self) -> str:
        # return f"{self.data_location.get_key()}/{convert_to_uri_safe_str(self.type)}/{convert_to_uri_safe_str(self.name)}"
        return f"{self.data_location.get_key()}/{self.type}/{self.name}"

class FileTable(GraphSerializable):

    FILE_TABLE_NODE_LABEL = 'File_Table'
    FILE_TABLE_NODE_ATTR_NAME = 'name'
    FILE_TABLE_NODE_ATTR_CONTENT = 'content'

    FILE_TABLE_RELATION_TYPE = 'FILE_TABLE'
    FILE_TABLE_OF_RELATION_TYPE = 'FILE_TABLE_OF'

    def __init__(self,
                 name: str,
                 content: str,
                 file: File,
                 ) -> None:

        self.name = name
        self.content = content
        self.file = file

        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()

    def __repr__(self) -> str:
        return f'FileTable({self.name!r}, {self.content!r})'

    def create_next_node(self) -> Optional[GraphNode]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        yield GraphNode(
            key=self.get_key(),
            label=self.FILE_TABLE_NODE_LABEL,
            attributes={
                self.FILE_TABLE_NODE_ATTR_NAME: self.name,
                self.FILE_TABLE_NODE_ATTR_CONTENT: self.content,
            }
        )

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        if self.file:
            yield GraphRelationship(
                start_label=File.FILE_NODE_LABEL,
                start_key=self.file.get_key(),
                end_label=self.FILE_TABLE_NODE_LABEL,
                end_key=self.get_key(),
                type=self.FILE_TABLE_RELATION_TYPE,
                reverse_type=self.FILE_TABLE_OF_RELATION_TYPE,
                attributes={}
            )

    def get_key(self) -> str:
        return f"{self.file.get_key()}/_filetable/{self.name}"

class ProspectusWaterfallScheme(GraphSerializable):

    PROSPECTUS_WATERFALL_SCHEME_NODE_LABEL = 'Prospectus_Waterfall_Scheme'
    PROSPECTUS_WATERFALL_SCHEME_NODE_ATTR_NAME = 'name'
    PROSPECTUS_WATERFALL_SCHEME_NODE_ATTR_SCHEME = 'scheme'

    PROSPECTUS_WATERFALL_SCHEME_RELATION_TYPE = 'PROSPECTUS_WATERFALL_SCHEME'
    PROSPECTUS_WATERFALL_SCHEME_OF_RELATION_TYPE = 'PROSPECTUS_WATERFALL_SCHEME_OF'

    def __init__(self,
                 name: str,
                 scheme: str,
                 file: File,
                 ) -> None:

        self.name = name
        self.scheme = scheme
        self.file = file

        self._node_iter = self._create_node_iterator()
        self._relation_iter = self._create_relation_iterator()

    def __repr__(self) -> str:
        return f'ProspectusWaterfallScheme({self.name!r}, {self.content!r})'

    def create_next_node(self) -> Optional[GraphNode]:
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        yield GraphNode(
            key=self.get_key(),
            label=self.PROSPECTUS_WATERFALL_SCHEME_NODE_LABEL,
            attributes={
                self.PROSPECTUS_WATERFALL_SCHEME_NODE_ATTR_NAME: self.name,
                self.PROSPECTUS_WATERFALL_SCHEME_NODE_ATTR_SCHEME: self.scheme,
            }
        )

    def _create_relation_iterator(self) -> Iterator[GraphRelationship]:
        if self.file:
            yield GraphRelationship(
                start_label=File.FILE_NODE_LABEL,
                start_key=self.file.get_key(),
                end_label=self.PROSPECTUS_WATERFALL_SCHEME_NODE_LABEL,
                end_key=self.get_key(),
                type=self.PROSPECTUS_WATERFALL_SCHEME_RELATION_TYPE,
                reverse_type=self.PROSPECTUS_WATERFALL_SCHEME_OF_RELATION_TYPE,
                attributes={}
            )

    def get_key(self) -> str:
        return f"{self.file.get_key()}/_prospectuswaterfallscheme/{self.name}"