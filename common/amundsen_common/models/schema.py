# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

import attr

from amundsen_common.models.user import User
from amundsen_common.models.badge import Badge
from amundsen_common.models.tag import Tag
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class Schema:
    key: Optional[str] = None
    name: str


class SchemaSchema(AttrsSchema):
    class Meta:
        target = Schema
        register_as_scheme = True

