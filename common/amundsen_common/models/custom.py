
from typing import Any, Dict, Optional, List, Union
from marshmallow import EXCLUDE, ValidationError, validates_schema
from marshmallow3_annotations.ext.attrs import AttrsSchema
import attr
from amundsen_common.models.util import UnionSchemaField


@attr.s(auto_attribs=True, kw_only=True)
class CustomMetadataNode:
    label: str
    name: str
    key: Optional[str] = None
    properties: Optional[Dict[str,Any]] = None

class CustomMetadataNodeSchema(AttrsSchema):
    class Meta:
        target = CustomMetadataNode
        register_as_scheme = True
        unknown = EXCLUDE

@attr.s(auto_attribs=True, kw_only=True)
class CustomMetadataNodeKey:
    label: str
    name: str

class CustomMetadataNodeKeySchema(AttrsSchema):
    class Meta:
        target = CustomMetadataNodeKey
        register_as_scheme = True
        unknown = EXCLUDE

# For Union support
CustomMetadataNodeKey.__marshmallow_schema__ = CustomMetadataNodeKeySchema


@attr.s(auto_attribs=True, kw_only=True)
class DefaultMetadataNodeKey:
    label: str
    key: str

class DefaultMetadataNodeKeySchema(AttrsSchema):
    class Meta:
        target = DefaultMetadataNodeKey
        register_as_scheme = True
        unknown = EXCLUDE

# For Union support
DefaultMetadataNodeKey.__marshmallow_schema__ = DefaultMetadataNodeKeySchema

@attr.s(auto_attribs=True, kw_only=True)
class CustomMetadataRelationship:
    type: str
    reverse_type: str
    properties: Optional[Dict[str,Any]] = None
    start_node: Union[CustomMetadataNodeKey,DefaultMetadataNodeKey]
    end_node: Union[CustomMetadataNodeKey,DefaultMetadataNodeKey]

class CustomMetadataRelationshipSchema(AttrsSchema):
    class Meta:
        target = CustomMetadataRelationship
        register_as_scheme = True
        unknown = EXCLUDE

    start_node = UnionSchemaField([CustomMetadataNodeKey, DefaultMetadataNodeKey])
    end_node = UnionSchemaField([CustomMetadataNodeKey, DefaultMetadataNodeKey])

@attr.s(auto_attribs=True, kw_only=True)
class CustomMetadata:
    nodes: Optional[List[CustomMetadataNode]] = None
    relationships: Optional[List[CustomMetadataRelationship]] = None

    @validates_schema
    def validate_one_of(self, data, **kwargs):
        if not data.get("nodes") and not data.get("relationships"):
            raise ValidationError("Either 'nodes' or 'relationships' must be provided.")

class CustomMetadataSchema(AttrsSchema):
    class Meta:
        target = CustomMetadata
        register_as_scheme = True
        unknown = EXCLUDE

