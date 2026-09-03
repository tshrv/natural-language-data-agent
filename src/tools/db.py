from typing import Any

import sqlglot
from aiocache import cached
from sqlglot.errors import OptimizeError, ParseError, SchemaError, TokenError
from sqlglot.optimizer.qualify import qualify

from config import settings
from utils.db import Database
from utils.json import dumps as json_dumps
from utils.json import loads as json_loads
from utils.logging import logger

from .cache import tool_key_builder
from .models import (
    ExplainAnalyzeQueryParams,
    ExplainQueryParams,
    GetTableSchemaParams,
    QueryPlanReport,
    RunQueryParams,
    ValidateQueryParams,
    ValidateQueryResult,
)


@cached(ttl=settings.cache_ttl_seconds, key_builder=tool_key_builder)
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


@cached(ttl=settings.cache_ttl_seconds, key_builder=tool_key_builder)
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


@cached(ttl=settings.cache_ttl_seconds, key_builder=tool_key_builder)
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


@cached(ttl=settings.cache_ttl_seconds)
async def _get_all_tables_schema() -> dict[str, dict[str, str]]:
    """Build a dictionary of table schemas for all tables in the public schema. The key is the table name, and the value is a dictionary of column names and their data types."""
    tables_schema: dict[str, dict[str, str]] = {}
    tables = json_loads(await list_tables())
    for table_name in tables.get("tables", []):
        table_schema = json_loads(
            await get_table_schema(GetTableSchemaParams(table_name=table_name))
        )
        if "error" in table_schema:
            logger.error(
                f"Error fetching schema for table {table_name}: {table_schema['error']}"
            )
            continue
        columns = {col["name"]: col["type"] for col in table_schema.get("columns", [])}
        tables_schema[table_name] = columns
    return tables_schema


@cached(ttl=settings.cache_ttl_seconds, key_builder=tool_key_builder)
async def validate_query(params: ValidateQueryParams) -> str:
    """Validate the sql query for forbidden statements, columns, tablenames, etc. before execution"""
    # TODO: the llm does not always run the validation before execution. Enforce validation inside the run_query function as well.
    errors: list[str] = []
    tables_schema = await _get_all_tables_schema()
    try:
        # parse statements for postgres dialect
        statements = [
            stmt
            for stmt in sqlglot.parse(params.sql, read="postgres")
            if stmt is not None
        ]
    except (ParseError, TokenError) as e:
        # invalid sql syntax
        return ValidateQueryResult(
            is_valid=False,
            errors=[f"SQL parsing error: {e!s}"],
        ).model_dump_json()

    # check for multiple statements
    if len(statements) != 1:
        return ValidateQueryResult(
            is_valid=False,
            errors=["Only one SQL statement is allowed"],
        ).model_dump_json()

    # check for non-SELECT statement
    expression = statements[0]
    if not isinstance(expression, sqlglot.exp.Select):
        return ValidateQueryResult(
            is_valid=False,
            errors=["Only SELECT statements are allowed"],
        ).model_dump_json()

    # check for hallucinated or missing table references
    known_tables = {table_name.lower() for table_name in tables_schema}
    referenced_tables = {
        table.name.lower() for table in expression.find_all(sqlglot.exp.Table)
    }
    if not referenced_tables:
        errors.append("No table references found in the query")

    unknown_tables = referenced_tables - known_tables
    if unknown_tables:
        errors.append(f"Unknown table(s) referenced: {', '.join(unknown_tables)}")
    if errors:
        return ValidateQueryResult(
            is_valid=False,
            errors=errors,
        ).model_dump_json()

    # qualify
    try:
        qualified_expression = qualify(
            expression=expression,
            dialect="postgres",
            schema=tables_schema,
            validate_qualify_columns=True,
            quote_identifiers=False,
            identify=False,
            sql=params.sql,
        )
    except (OptimizeError, SchemaError, TokenError, ParseError) as e:
        return ValidateQueryResult(
            is_valid=False,
            errors=[f"SQL validation error: {e!s}"],
        ).model_dump_json()

    return ValidateQueryResult(
        is_valid=True,
        errors=[],
        normalized_query=qualified_expression.sql(dialect="postgres"),
    ).model_dump_json()


@cached(ttl=settings.cache_ttl_seconds, key_builder=tool_key_builder)
async def explain_analyze_query(params: ExplainAnalyzeQueryParams) -> str:
    """Run EXPLAIN ANALYZE on a sql query and return the execution plan"""
    try:
        async with Database.get_connection() as conn:
            explain_sql = f"EXPLAIN ANALYZE {params.sql}"
            records = await conn.fetch(explain_sql)
            if not len(records):
                raise ValueError("Query returned no records")
            columns: list[str] = list(records[0].keys())
            rows: list[list[str]] = [list(record.values()) for record in records]
            result = {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
            }
            logger.info(result)
    except Exception as e:
        result = {"error": str(e)}
        logger.error(result)
    return json_dumps(result)


def _walk_plan(node: dict[str, Any]) -> list[dict[str, Any]]:
    """Recursively walk the query plan tree and return a list of nodes"""
    nodes = [node]
    for child in node.get("Plans", []):
        nodes.extend(_walk_plan(child))
    return nodes


@cached(ttl=settings.cache_ttl_seconds, key_builder=tool_key_builder)
async def explain_query(params: ExplainQueryParams) -> str:
    """Run EXPLAIN on a sql query and return the execution plan, this does and estimation of the cost and rows but does not run the query"""
    try:
        async with Database.get_connection() as conn:
            explain_sql = f"EXPLAIN (FORMAT JSON) {params.sql}"
            records = await conn.fetch(explain_sql)
            if not len(records):
                raise ValueError("Query returned no EXPLAIN result")

            plan = json_loads(records[0]["QUERY PLAN"])[0]
            root = plan["Plan"]

            row_warning = settings.plan_rows_warning
            cost_warning = settings.plan_cost_warning
            root_rows = int(root.get("Plan Rows", 0))
            total_cost = float(root.get("Total Cost", 0.0))
            risks: list[str] = []

            if root_rows >= row_warning:
                risks.append(
                    f"Estimated output is {root_rows:,} rows, above {row_warning:,}."
                )
            if total_cost >= cost_warning:
                risks.append(
                    f"Estimated total cost is {total_cost:,.2f}, above {cost_warning:,.2f}."
                )

            # The walker checks every node for a Seq Scan operation.
            # Large scans receive a warning when their estimated rows reach the configured threshold.
            # The warning names the affected relation when PostgreSQL includes it.
            # A sequential-scan warning is a prompt for review. Statistics or query shape can make the scan reasonable.
            for node in _walk_plan(root):
                if node.get("Node Type") == "Seq Scan":
                    estimated_rows = int(node.get("Plan Rows", 0))
                    if estimated_rows >= row_warning:
                        relation = node.get("Relation Name", "unknown relation")
                        risks.append(
                            f"Large sequential scan estimated on {relation}: "
                            f"{estimated_rows:,} rows."
                        )

            result = QueryPlanReport(
                root_node=str(root.get("Node Type", "Unknown")),
                plan_rows=root_rows,
                total_cost=total_cost,
                risks=risks,
                plan=plan,
            ).model_dump_json()
            logger.info(result)

    except Exception as e:
        result = {"error": f"{e.__class__.__name__}: {str(e)}"}
        logger.error(result)

    return json_dumps(result)
