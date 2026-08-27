import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


def extended_serializer(obj):
    """Fallback handler for types not supported by default json.dumps."""
    if isinstance(obj, Decimal):
        return float(obj)  # Use str(obj) if exact financial precision is required
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    elif hasattr(obj, "__dict__"):
        return obj.__dict__

    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def dumps(obj, **kwargs) -> str:
    """Custom json.dumps wrapper with extended type support."""
    kwargs.setdefault("default", extended_serializer)
    return json.dumps(obj, **kwargs)


def loads(*args, **kwargs) -> dict:
    return json.loads(*args, **kwargs)
