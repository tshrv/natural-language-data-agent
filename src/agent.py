from tools import TOOL_SCHEMAS, TOOLS

SYSTEM_PROMPT = """You are a SQL agent that answers questions about a PostgreSQL database.
The database contains TPC-H benchmark data.
Use the available tools to discover the schema and run queries to answer the user's question.
Format your final answer as a clear, human-readable response."""

# Safety limit to prevent infinite loops
MAX_ITERATIONS = 10