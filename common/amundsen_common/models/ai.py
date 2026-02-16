
from typing import Any, Dict, Optional, List, Union
from marshmallow import EXCLUDE
from marshmallow3_annotations.ext.attrs import AttrsSchema
import attr
from amundsen_common.models.util import UnionSchemaField

@attr.s(auto_attribs=True, kw_only=True)
class ChatMessage:
    role: str
    content: str

class ChatMessageSchema(AttrsSchema):
    class Meta:
        target = ChatMessage
        register_as_scheme = True
        unknown = EXCLUDE

@attr.s(auto_attribs=True, kw_only=True)
class ChatFunction:
    functions: List[Dict[Any,Any]]
    function_call: Union[str,Dict[Any,Any]]


class ChatFunctionSchema(AttrsSchema):
    class Meta:
        target = ChatFunction
        register_as_scheme = True
        unknown = EXCLUDE

    function_call = UnionSchemaField([str, dict])

# For Union support
ChatFunction.__marshmallow_schema__ = ChatFunctionSchema

@attr.s(auto_attribs=True, kw_only=True)
class ChatRequest:
    messages: List[ChatMessage]
    function: Optional[ChatFunction] = None

class ChatRequestSchema(AttrsSchema):
    class Meta:
        target = ChatRequest
        register_as_scheme = True
        unknown = EXCLUDE

@attr.s(auto_attribs=True, kw_only=True)
class ChatResponse:
    finish_reason: str
    message: Optional[ChatMessage] = None
    function_call: Optional[Dict[Any,Any]] = None
    error_text: Optional[str] = None

class ChatResponseSchema(AttrsSchema):
    class Meta:
        target = ChatResponse
        register_as_scheme = True
        unknown = EXCLUDE

@attr.s(auto_attribs=True, kw_only=True)
class ColumnSearchHit:
    score: float
    key: str
    name: str
    data_type: Optional[str] = None
    description: Optional[str] = None
    table_key: str
    table_name: str
    table_description: Optional[str] = None

class ColumnSearchHitSchema(AttrsSchema):
    class Meta:
        target = ColumnSearchHit
        register_as_scheme = True
        unknown = EXCLUDE

@attr.s(auto_attribs=True, kw_only=True)
class ColumnSearchResponse:
    search_text: str
    hits: List[ColumnSearchHit]

class ColumnSearchResponseSchema(AttrsSchema):
    class Meta:
        target = ColumnSearchResponse
        register_as_scheme = True
        unknown = EXCLUDE
