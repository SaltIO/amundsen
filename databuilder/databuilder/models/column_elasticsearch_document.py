# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

from databuilder.models.elasticsearch_document import ElasticsearchDocument


class ColumnESDocument(ElasticsearchDocument):
    """
    Schema for the Search index document
    """

    def __init__(self,
                 name: str,
                 key: str,
                 description: str,
                 tags: List[str],
                 table_name: str,
                 table_key: str,
                 table_description: str,
                 table_tags: List[str],
                 badges: Optional[List[str]] = None,
                 table_badges: Optional[List[str]] = None,
                 ) -> None:
        self.name = name
        self.key = key
        self.description = description
        self.tags = tags
        self.badges = badges
        self.table_name = table_name
        self.table_key = table_key
        self.table_description = table_description
        self.table_tags = table_tags
        self.table_badges = table_badges
