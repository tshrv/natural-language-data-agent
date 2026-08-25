-- Built-in Postgres role grants read-only access to all databases, tables, and schemas in your Postgres 17 instance.

-- create the user
CREATE USER sql_agent_user WITH PASSWORD 'sql_agent_password';

-- grant global read access
GRANT pg_read_all_data TO sql_agent_user;