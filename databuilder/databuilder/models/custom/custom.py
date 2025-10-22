# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import re
from typing import (
    Any, Dict, Iterator, Optional, Union,
)

from databuilder.models.description_metadata import DescriptionMetadata
from databuilder.models.graph_node import GraphNode
from databuilder.models.graph_relationship import GraphRelationship
from databuilder.models.graph_serializable import GraphSerializable


class CustomMetadataNode(GraphSerializable):

    CUSTOM_METADATA_NODE_KEY_FORMAT = "custom://{label}/{name}"

    def __init__(
        self,
        label: str,
        name: str,
        properties: Optional[Dict[str,Any]] = None,
        rel_node_label: Optional[str] = None,
        rel_node_key: Optional[str] = None,
        rel_type: Optional[str] = None,
        rel_reverse_type: Optional[str] = None,
        rel_properties: Optional[Dict[str,Any]] = None,
        **kwargs: Any
    ) -> None:

        self.label = label
        self.name = name
        self.key = CustomMetadataNode.CUSTOM_METADATA_NODE_KEY_FORMAT.format(label=self.label, name=self.name)
        self.properties = properties

        self.rel_node_label = rel_node_label
        self.rel_node_key = rel_node_key
        self.rel_type = rel_type
        self.rel_reverse_type = rel_reverse_type
        self.rel_properties = rel_properties

        self._node_iterator = self._create_node_iterator()
        self._relation_iterator = None

    def create_next_node(self) -> Union[GraphNode, None]:
        try:
            return next(self._node_iterator)
        except StopIteration:
            return None

    def create_next_relation(self) -> Optional[GraphRelationship]:
        try:
            if self._relation_iterator is None:
                self._relation_iterator = self._create_relation_iterator()
            return next(self._relation_iterator)
        except StopIteration:
            self._relation_iterator = None
            return None

    def _create_node_iterator(self) -> Iterator[GraphNode]:
        attributes = {
            "name": self.name
        }
        if self.properties:
            for k, v in self.properties.items():
                if k not in attributes:
                    attributes[k] = v

        yield GraphNode(
            key=self.key,
            label=self.label,
            attributes=attributes
        )

    def _create_relation_iterator(self) -> Iterator[GraphNode]:
        yield GraphRelationship(
            start_label='CustomMetadataRoot',
            end_label=self.label,
            start_key='GLOBAL_CUSTOM_ROOT',
            end_key=self.key,
            type='HAS_CUSTOM',
            reverse_type='CUSTOM',
            attributes={}
        )

        if self.rel_node_label and self.rel_node_key and self.rel_type and self.rel_reverse_type:
            yield GraphRelationship(
                start_label=self.rel_node_label,
                end_label=self.label,
                start_key=self.rel_node_key,
                end_key=self.key,
                type=self.rel_type,
                reverse_type=self.rel_reverse_type,
                attributes={}
            )

# class CustomMetadataRelationship(GraphSerializable):

#     def __init__(
#         self,
#         custom_metadata_node: CustomMetadataNode,
#         rel_node_label: str,
#         rel_node_key: str,
#         rel_type: str,
#         rel_reverse_type: str,
#         rel_properties: Optional[Dict[str,Any]] = None,
#         **kwargs: Any
#     ) -> None:

#         self.custom_metadata_node = custom_metadata_node
#         self.rel_node_label = rel_node_label
#         self.rel_node_key = rel_node_key

#         self.rel_properties = rel_properties

#         self.rel_type = rel_type
#         self.rel_reverse_type = rel_reverse_type

#         self._rel_iterator = self._create_rel_iterator()

#     def create_next_node(self) -> Union[GraphNode, None]:
#         return None

#     def create_next_relation(self) -> Optional[GraphRelationship]:
#         try:
#             return next(self._rel_iterator)
#         except StopIteration:
#             return None

#     def _create_rel_iterator(self) -> Iterator[GraphNode]:
#         yield GraphRelationship(
#             start_label=self.custom_metadata_node.label,
#             end_label=self.rel_node_label,
#             start_key=self.custom_metadata_node.key,
#             end_key=self.rel_node_key,
#             type=self.rel_type,
#             reverse_type=self.rel_reverse_type,
#             attributes=self.rel_properties if self.rel_properties else {}
#         )