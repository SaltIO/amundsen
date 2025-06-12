from typing import Dict
from marshmallow import fields, ValidationError
from marshmallow.base import FieldABC
from collections.abc import Mapping


class UnionSchemaField(fields.Field):
    def __init__(self, union_types, **kwargs):
        super().__init__(**kwargs)
        self._schemas = []

        for typ in union_types:
            schema_cls = getattr(typ, "__marshmallow_schema__", None)
            if schema_cls:
                self._schemas.append((typ, schema_cls()))
            elif typ is str:
                self._schemas.append((typ, fields.String()))
            elif typ in (dict, Dict, Mapping):
                self._schemas.append((typ, fields.Dict()))
            elif typ is int:
                self._schemas.append((typ, fields.Integer()))
            elif typ is float:
                self._schemas.append((typ, fields.Float()))
            elif typ is bool:
                self._schemas.append((typ, fields.Boolean()))
            else:
                raise ValueError(f"No schema registered for type {typ}")

    def _deserialize(self, value, attr, data, **kwargs):
        errors = []
        for typ, schema in self._schemas:
            try:
                if isinstance(schema, FieldABC):
                    return schema.deserialize(value, attr, data, **kwargs)
                else:
                    return schema.load(value)
            except ValidationError as err:
                errors.append(err.messages)
        raise ValidationError({"union": errors})

    def _serialize(self, value, attr, obj, **kwargs):
        for typ, schema in self._schemas:
            if isinstance(value, typ):
                if isinstance(schema, FieldABC):
                    return schema.serialize(attr, {"dummy": value})
                else:
                    return schema.dump(value)
        raise ValidationError(f"Value {value} does not match any known type")
