from pydantic import BaseModel, Field


class GetTableSchemaParams(BaseModel):
    table_name: str = Field(description="Name of the table to fetch schema for")


class RunQueryParams(BaseModel):
    sql: str = Field(description="Query to execute, do not add ';' at end")


class ValidateQueryParams(BaseModel):
    sql: str = Field(
        description="Check the sql query for forbidden statements before execution"
    )


class ExplainAnalyzeQueryParams(BaseModel):
    sql: str = Field(description="Query to explain analyze")
