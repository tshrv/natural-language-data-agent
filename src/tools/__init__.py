from .db import get_table_schema, list_tables, run_query
from .models import GetTableSchemaParams, RunQueryParams
from .schema import (
    get_table_schema_tool_schema,
    list_tables_tool_schema,
    run_query_tool_schema,
)

TOOLS = {
    "get_table_schema": get_table_schema,
    "list_tables": list_tables,
    "run_query": run_query,
}

TOOL_SCHEMAS = [
    get_table_schema_tool_schema,
    list_tables_tool_schema,
    run_query_tool_schema,
]

TOOL_PARAMS_CLS = {
    "get_table_schema": GetTableSchemaParams,
    "run_query": RunQueryParams,
    "list_tables": None,
}

assert set(TOOLS.keys()) == set(TOOL_PARAMS_CLS.keys()), (
    "TOOLS and TOOL_PARAMS_CLS are out of sync"
)

__all__ = ["TOOLS", "TOOL_PARAMS_CLS", "TOOL_SCHEMAS"]
