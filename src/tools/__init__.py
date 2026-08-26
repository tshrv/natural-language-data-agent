from .db import get_table_schema, list_tables, run_query
from .schema import (
    get_table_schema_tool_schema,
    list_tables_tool_schema,
    run_query_tool_schema,
)

TOOLS = {
    "get_table_schema": get_table_schema,
    "list_tables": list_tables,
    "run_query": run_query
}

TOOL_SCHEMAS = [
    get_table_schema_tool_schema,
    list_tables_tool_schema,
    run_query_tool_schema,
]

__all__ = ["TOOLS", "TOOL_SCHEMAS"]