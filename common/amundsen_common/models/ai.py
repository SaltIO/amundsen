
from typing import Optional, List
from marshmallow3_annotations.ext.attrs import AttrsSchema
import attr

@attr.s(auto_attribs=True, kw_only=True)
class ChatMessage:
    role: str
    content: str

class ChatMessageSchema(AttrsSchema):
    class Meta:
        target = ChatMessage
        register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class ChatResponse:
    finish_reason: str
    message: Optional[ChatMessage] = None
    error_text: Optional[str] = None

class ChatResponseSchema(AttrsSchema):
    class Meta:
        target = ChatResponse
        register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class ColumnSearchHit:
    score: float
    key: str
    name: str
    table_key: str
    table_name: str

class ColumnSearchHitSchema(AttrsSchema):
    class Meta:
        target = ColumnSearchHit
        register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class ColumnSearchResponse:
    search_text: str
    hits: List[ColumnSearchHit]

class ColumnSearchResponseSchema(AttrsSchema):
    class Meta:
        target = ColumnSearchResponse
        register_as_scheme = True