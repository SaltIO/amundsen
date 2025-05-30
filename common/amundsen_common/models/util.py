from marshmallow import fields, ValidationError

class UnionSchemaField(fields.Field):
    def __init__(self, union_types, **kwargs):
        super().__init__(**kwargs)
        self._schemas = []
        for typ in union_types:
            schema_cls = getattr(typ, "__marshmallow_schema__", None)
            if schema_cls is None:
                raise ValueError(f"No schema registered for type {typ}")
            self._schemas.append((typ, schema_cls()))

    def _deserialize(self, value, attr, data, **kwargs):
        errors = []
        for typ, schema in self._schemas:
            try:
                return schema.load(value)
            except ValidationError as err:
                errors.append(err.messages)
        raise ValidationError({"union": errors})

    def _serialize(self, value, attr, obj, **kwargs):
        for typ, schema in self._schemas:
            if isinstance(value, typ):
                return schema.dump(value)
        raise ValidationError(f"Value {value} does not match any known type")
