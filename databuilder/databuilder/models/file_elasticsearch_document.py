# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

from databuilder.models.elasticsearch_document import ElasticsearchDocument


class FileESDocument(ElasticsearchDocument):
    """
    Schema for the Search index document
    """

    def __init__(self,
                 name: str,
                 key: str,
                 description: str,
                 type: str,
                 category: Optional[str],
                 path: str,
                 is_directory: bool,
                 data_location_type: Optional[str],
                 data_location_name: Optional[str],
                 data_channel_type: Optional[str],
                 data_channel_name: Optional[str],
                 data_channel_license: Optional[str],
                 data_provider_name: Optional[str],
                 last_updated_timestamp: Optional[int],
                 tags: Optional[List[str]],
                #  badges: Optional[List[str]] = None,
                 ) -> None:
        self.name = name
        self.key = key
        self.description = description
        self.type = type
        self.path = path
        self.is_directory = is_directory
        self.last_updated_timestamp = int(last_updated_timestamp) if last_updated_timestamp else None
        self.data_location_type = data_location_type
        self.data_location_name = data_location_name
        self.data_channel_type = data_channel_type
        self.data_channel_name = data_channel_name
        self.data_channel_license = data_channel_license
        self.data_provider_name = data_provider_name
        self.tags = tags
        # self.badges = badges
