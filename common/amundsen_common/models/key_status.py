# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Optional, Dict

import attr
from marshmallow import EXCLUDE, ValidationError, validates_schema, pre_load
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class KeyStatus:
    key: str
    status: str


class KeyStatusSchema(AttrsSchema):
    class Meta:
        target = KeyStatus
        register_as_scheme = True