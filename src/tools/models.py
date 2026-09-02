from pydantic import BaseModel, Field


class GetTableSchemaParams(BaseModel):
    table_name: str = Field(description="Name of the table to fetch schema for")


class RunQueryParams(BaseModel):
    sql: str = Field(description="Query to execute, do not add ';' at end")


class ValidateQueryParams(BaseModel):
    sql: str = Field(
        description="Check the sql query for forbidden statements before execution"
    )


class ValidateQueryResult(BaseModel):
    is_valid: bool = Field(
        default=False, description="Whether the query is valid or not"
    )
    errors: list[str] | None = Field(
        default=None, description="List of errors found in the query, empty if valid"
    )
    normalized_query: str | None = Field(
        default=None, description="Normalized version of the query, empty if invalid"
    )


class ExplainAnalyzeQueryParams(BaseModel):
    sql: str = Field(description="Query to explain analyze")
