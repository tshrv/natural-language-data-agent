import json

from loguru import logger

from utils.db import get_db_connection


async def list_tables() -> str:
    """
    List all tables in the public schema.
    """
    async with get_db_connection() as conn:
        try:
            result = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """)
            tables: list[str] = [record['table_name'] for record in result]
            logger.debug(f"Tables found in public schema [{len(tables)}]: {tables}")
            response = {"tables": tables}
        except Exception as e:
            logger.error(f"Error fetching tables: {e}")
            response = {"error": str(e)}
    return json.dumps(response)


async def get_table_schema(table_name: str) -> str:
    """
    Get column names, data types, and foreign key relationships for a table.
    """
    async with get_db_connection() as conn:
        try:
            # This queries information_schema.columns to get every column in the specified table. For each column it captures the name, data type, and whether it allows nulls. The $i placeholder is a parameterized query. 
            col_result = await conn.fetch(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
                """,
                table_name
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
                table_name
            )
            foreign_keys = [
                {"column": row[0], "references": f"{row[1]}.{row[2]}"}
                for row in fk_result
            ]
            response = {"table": table_name, "columns": columns, "foreign_keys": foreign_keys}
        except Exception as e:
            logger.error(f"Error fetching table schema: {e}")
            response = {"error": str(e)}
        return json.dumps(response)
