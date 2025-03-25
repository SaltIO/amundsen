from typing import Optional

import attr

from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class Database:
    key: Optional[str] = None
    name: str


class DatabaseSchema(AttrsSchema):
    class Meta:
        target = Database
        register_as_scheme = True

