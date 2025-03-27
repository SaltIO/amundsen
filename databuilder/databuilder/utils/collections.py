
class CaseInsensitiveSet(set):
    """A case-insensitive set where all values are stored in lowercase."""

    def __init__(self, iterable=None):
        """Initialize set with lowercase values."""
        if iterable:
            super().__init__(item.lower() for item in iterable)
        else:
            super().__init__()

    def add(self, value):
        """Add a value to the set (converted to lowercase)."""
        super().add(value.lower())

    def remove(self, value):
        """Remove a value from the set (converted to lowercase)."""
        super().remove(value.lower())

    def discard(self, value):
        """Remove a value if it exists (converted to lowercase)."""
        super().discard(value.lower())

    def __contains__(self, value):
        """Check if a value exists (case insensitive)."""
        return super().__contains__(value.lower())

    def update(self, *args):
        """Update the set with multiple case-insensitive values."""
        for iterable in args:
            for item in iterable:
                self.add(item.lower())

    def difference(self, *args):
        """Case-insensitive difference operation."""
        return CaseInsensitiveSet(super().difference(*(set(a.lower() for a in arg) for arg in args)))

    def intersection(self, *args):
        """Case-insensitive intersection operation."""
        return CaseInsensitiveSet(super().intersection(*(set(a.lower() for a in arg) for arg in args)))

    def union(self, *args):
        """Case-insensitive union operation."""
        return CaseInsensitiveSet(super().union(*(set(a.lower() for a in arg) for arg in args)))


class CaseInsensitiveDict(dict):
    def __setitem__(self, key, value):
        """Store keys in lowercase to ensure case-insensitivity."""
        super().__setitem__(key.lower(), value)

    def __getitem__(self, key):
        """Retrieve values using lowercase keys."""
        return super().__getitem__(key.lower())

    def __contains__(self, key):
        """Ensure 'key in dict' is case insensitive."""
        return super().__contains__(key.lower())

    def get(self, key, default=None):
        """Get method with case insensitivity."""
        return super().get(key.lower(), default)

    def items(self):
        """Override items() to always return lowercase keys."""
        return ((k.lower(), v) for k, v in super().items())