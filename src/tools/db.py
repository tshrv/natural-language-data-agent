from loguru import logger

from utils.db import Database
from utils.json import dumps as json_dumps

from .models import GetTableSchemaParams, RunQueryParams, ValidateQueryParams


async def list_tables() -> str:
    """List names of all tables in the public schema."""
    async with Database.get_connection() as conn:
        try:
            result = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """)
            tables: list[str] = [record["table_name"] for record in result]
            logger.debug(f"Tables found in public schema [{len(tables)}]: {tables}")
            response = {"tables": tables}
        except Exception as e:
            logger.error(f"Error fetching tables: {e}")
            response = {"error": str(e)}
    return json_dumps(response)


async def get_table_schema(params: GetTableSchemaParams) -> str:
    """Get column names, data types, and foreign key relationships for a table."""
    async with Database.get_connection() as conn:
        try:
            # This queries information_schema.columns to get every column in the specified table. For each column it captures the name, data type, and whether it allows nulls. The $i placeholder is a parameterized query.
            col_result = await conn.fetch(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
                """,
                params.table_name,
            )
            columns = [
                {"name": row[0], "type": row[1], "nullable": row[2]}
                for row in col_result
            ]
            # This joins three information_schema views to discover which columns in the current table reference columns in other tables. For example, the customer table's c_nationkey column references nation.n_nationkey. This is the information the LLM needs to write correct JOIN conditions.
            fk_result = await conn.fetch(
                """
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                    AND tc.table_schema = ccu.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                    AND tc.table_name = $1
                """,
                params.table_name,
            )
            foreign_keys = [
                {"column": row[0], "references": f"{row[1]}.{row[2]}"}
                for row in fk_result
            ]
            response = {
                "table": params.table_name,
                "columns": columns,
                "foreign_keys": foreign_keys,
            }
        except Exception as e:
            logger.error(f"Error fetching table schema: {e}")
            response = {"error": str(e)}
        return json_dumps(response)


async def run_query(params: RunQueryParams) -> str:
    """Execute a SQL query and return results. Result is truncated to 50 rows."""
    try:
        async with Database.get_connection() as conn:
            LIMIT = 50
            safe_sql = f"SELECT * FROM ({params.sql}) AS user_stmt LIMIT $1"
            # TODO: use sqlglot to parse and ensure query is SELECT only
            records = await conn.fetch(safe_sql, LIMIT)
            if not len(records):
                raise ValueError("Query returned no records")
            columns: list[str] = list(records[0].keys())
            rows: list[list[str]] = [list(record.values()) for record in records]
            result = {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "note": f"Results are capped at {LIMIT} rows"
                if len(rows) == LIMIT
                else None,
            }
            logger.info(result)
    except Exception as e:
        result = {"error": str(e)}
        logger.info(result)
    return json_dumps(result)


async def validate_query(params: ValidateQueryParams) -> str:
    """Validate the sql query for forbidden statements before execution"""
    forbidden = ["insert", "update", "alter", "delete", "drop", "create", "truncate"]
    sql_lower = params.sql.lower()
    # valid by default unless forbidden keywords are found
    response = {"valid": True, "sql": params.sql}
    for keyword in forbidden:
        if sql_lower.startswith(keyword):
            response.update(
                valid=False,
                reason=f"{keyword.upper()} statements are not allowed, only SELECT queries are permitted",
            )
            logger.warning(response)
    return json_dumps(response)
