from collections.abc import Callable

from pydantic import BaseModel

from .db import (
    explain_analyze_query,
    explain_query,
    get_table_schema,
    list_tables,
    run_query,
    validate_query,
)
from .models import (
    ExplainAnalyzeQueryParams,
    ExplainQueryParams,
    GetTableSchemaParams,
    RunQueryParams,
    ValidateQueryParams,
)
from .schema import get_tool_schema

_AVAILABLE_TOOLS = {
    "list_tables": {"function": list_tables, "params_cls": None},
    "get_table_schema": {
        "function": get_table_schema,
        "params_cls": GetTableSchemaParams,
    },
    "run_query": {"function": run_query, "params_cls": RunQueryParams},
    "validate_query": {"function": validate_query, "params_cls": ValidateQueryParams},
    "explain_analyze_query": {
        "function": explain_analyze_query,
        "params_cls": ExplainAnalyzeQueryParams,
    },
    "explain_query": {
        "function": explain_query,
        "params_cls": ExplainQueryParams,
    },
}


def get_tools_schemas() -> list[dict]:
    """Get schemas of all available tools"""
    return [
        get_tool_schema(v.get("function"), v.get("params_cls"))
        for k, v in _AVAILABLE_TOOLS.items()
    ]


def get_tool(key: str) -> tuple[Callable, BaseModel]:
    """Get the tool function by the key"""
    tool_obj = _AVAILABLE_TOOLS.get(key, None)
    if tool_obj is None:
        return (None, None)
    else:
        return (tool_obj.get("function"), tool_obj.get("params_cls"))


__all__ = ["get_tool", "get_tools_schemas"]
