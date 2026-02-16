# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

import attr

from marshmallow import EXCLUDE
from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class AuthToken:
    access_token: str
    expires_in: int
    token_type: str

class AuthTokenSchema(AttrsSchema):
    class Meta:
        target = AuthToken
        register_as_scheme = True
        unknown = EXCLUDE