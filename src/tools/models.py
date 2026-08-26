from pydantic import BaseModel, Field


class GetTableSchemaParams(BaseModel):
    table_name: str = Field(description="Name of the table to fetch schema for")

class RunQueryParams(BaseModel):
    sql: str = Field(description="Query to execute, SELECT only")
