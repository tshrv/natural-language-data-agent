# Autonomous, Schema-Aware SQL Agent with Groq

This is a command-line SQL agent that translates natural language questions into live PostgreSQL queries. You type a question, and the agent figures out which tables to inspect, writes the SQL, runs it, and hands back a plain-English answer.

An intelligent, autonomous SQL Agent designed to interface directly with a relational PostgreSQL database. Powered by Groq's high-speed inference engine, this agent does not rely on rigid hardcoded queries; instead, it dynamically discovers database topologies, resolves complex multi-table joins, and executes safe, sandboxed queries to answer unstructured natural language questions.

## 🚀 Architectural Overview

Unlike traditional "one-shot" LLM text generation, this system operates on an active **Agentic Loop**. The agent is equipped with custom-built python tools that act as its "hands," allowing it to inspect and query database environments on demand.

```
       ┌────────────────────────┐
       │   User Prompt (NL)     │
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │  agent.py (Controller) │◄──────────┐
       └───────────┬────────────┘           │
                   ▼                        │
       ┌────────────────────────┐           │ (Iterative loop:
       │  Groq Inference API    │           │  Decides to call tool
       └───────────┬────────────┘           │  or render final answer)
                   ▼                        │
       ┌───────────────────────────┐        │
       │ Tool Execution Intercept  │        │
       │   (db_tools.py)           ├────────┘
       └───────────┬───────────────┘
                   ▼
       ┌────────────────────────┐
       │  PostgreSQL Database   │
       └────────────────────────┘
```

---

## 🛠️ System Components & Tools

The architecture is divided into two highly cohesive modules:

### 1. The Autonomous Controller (`agent.py`)
This module acts as the orchestrator of the conversational state and tool-calling execution loops:
* **The Agentic Loop:** Executes an iterative state machine (capped by a maximum execution limit to prevent infinite run-cost loops). It continuously formats the prompt, sends history to the LLM, parses requested function parameters, and updates memory with tool responses.
* **JSON-Schema Tool Mapping:** Exposes python utility functions to the Groq model using structured JSON declarations, explicitly detailing required parameters and structural constraints.

### 2. Database Utility Sandbox (`tools/db.py`)
A suite of native Python database interfaces built using `asyncpg` to provide sandboxed database actions:
* **Topology Discovery (`list_tables`):** Allows the agent to query database catalog tables (`information_schema.tables`) to inspect the active database state and list available relations.
* **Schema Awareness & Join Resolution (`get_table_schema`):** Resolves columns, data types, and primary-foreign key relationships from `information_schema.columns` and key usage schemas. This informs the model of the exact joining relationships across tables, preventing "hallucinated" column joins.
* **Sandboxed Query Executor (`run_query`):** Handles execution of generated read-only SQL queries with built-in safety boundaries:
  * **Memory Cap:** Enforces a rigid 50-row maximum result threshold using safe cursor fetches to avoid memory overflow during query execution on large datasets.
  * **Feedback Error Handling:** Catches execution syntax exceptions and forwards PostgreSQL engine errors back to the agent loop, prompting the model to automatically rewrite and heal its queries.

---

## 🔄 Conceptual Execution Flow

When a user submits a natural language question (e.g., *"What are the top 5 nations by revenue?"*):

1. **Initialization:** The agent client spins up with the user question and the core System Instructions.
2. **Metadata Discovery:** Sensing a complex query, the agent recognizes it does not know the database topology and initiates a `list_tables` call.
3. **Relation Inspection:** After locating tables (such as `orders`, `lineitem`, and `customer`), the agent calls `get_table_schema` on the target tables to inspect their structures and identify foreign key constraints.
4. **Execution Strategy:** Utilizing the discovered schema, the agent writes a precise multi-table JOIN query, submitting it via `run_query`.
5. **Auto-Correction (Self-Healing):** If the initial query returns an engine error, the agent processes the error string, modifies the query syntax, and re-executes.
6. **Formatting:** Once the query successfully returns sandboxed results, the agent synthesizes the raw tabular data into a polished, human-readable summary.

---

## 🔒 Safety and Design Guardrails

* **SQL Injection Mitigation:** Parametric database calls are implemented across the metadata discovery tools to ensure safe query separation.
* **Resource Optimization:** Iteration caps on the model loop protect API rate limits, while row limits inside SQL cursors prevent database resource exhaustion.
* **Read-Only Enforcements:** The execution layer is designed to handle queries returning tabular descriptions, deterring hazardous table-altering SQL execution.


## Run Logs
1. Features to notice: tool use, query validation, retry on failure
```sh
2026-08-28 19:29:28 | INFO     | __main__:main:20 - SQL Agent ready. Ask questions about the TPC-H database.
2026-08-28 19:29:28 | INFO     | agent:run_agent:31 - User question: Show me parts with a supply cost over 900 from European suppliers
2026-08-28 19:29:28 | INFO     | agent:run_agent:32 - --------------------------------------------------
2026-08-28 19:29:28 | INFO     | agent:run_agent:41 - Iteration 0/10
2026-08-28 19:29:29 | INFO     | agent:run_agent:56 - Tool : list_tables()
2026-08-28 19:29:29 | INFO     | agent:run_agent:69 - Intermediate result: {"tables": ["customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"]}
2026-08-28 19:29:29 | INFO     | agent:run_agent:41 - Iteration 1/10
2026-08-28 19:29:30 | INFO     | agent:run_agent:56 - Tool : get_table_schema({'table_name': 'part'})
2026-08-28 19:29:30 | INFO     | agent:run_agent:69 - Intermediate result: {"table": "part", "columns": [{"name": "p_partkey", "type": "bigint", "nullable": "NO"}, {"name": "p_name", "type": "character varying", "nullable": "YES"}, {"name": "p_mfgr", "type": "character varyi
2026-08-28 19:29:30 | INFO     | agent:run_agent:56 - Tool : get_table_schema({'table_name': 'partsupp'})
2026-08-28 19:29:30 | INFO     | agent:run_agent:69 - Intermediate result: {"table": "partsupp", "columns": [{"name": "ps_partkey", "type": "bigint", "nullable": "NO"}, {"name": "ps_suppkey", "type": "bigint", "nullable": "NO"}, {"name": "ps_availqty", "type": "integer", "nu
2026-08-28 19:29:30 | INFO     | agent:run_agent:56 - Tool : get_table_schema({'table_name': 'supplier'})
2026-08-28 19:29:30 | INFO     | agent:run_agent:69 - Intermediate result: {"table": "supplier", "columns": [{"name": "s_suppkey", "type": "bigint", "nullable": "NO"}, {"name": "s_name", "type": "character varying", "nullable": "YES"}, {"name": "s_address", "type": "characte
2026-08-28 19:29:30 | INFO     | agent:run_agent:56 - Tool : get_table_schema({'table_name': 'nation'})
2026-08-28 19:29:30 | INFO     | agent:run_agent:69 - Intermediate result: {"table": "nation", "columns": [{"name": "n_nationkey", "type": "integer", "nullable": "NO"}, {"name": "n_name", "type": "character varying", "nullable": "YES"}, {"name": "n_regionkey", "type": "integ
2026-08-28 19:29:30 | INFO     | agent:run_agent:56 - Tool : get_table_schema({'table_name': 'region'})
2026-08-28 19:29:30 | INFO     | agent:run_agent:69 - Intermediate result: {"table": "region", "columns": [{"name": "r_regionkey", "type": "integer", "nullable": "NO"}, {"name": "r_name", "type": "character varying", "nullable": "YES"}, {"name": "r_comment", "type": "charact
2026-08-28 19:29:30 | INFO     | agent:run_agent:41 - Iteration 2/10
2026-08-28 19:29:31 | INFO     | agent:run_agent:56 - Tool : validate_query({'sql': "SELECT p.p_partkey, p.p_name, p.p_mfgr, p.p_brand, p.p_size, p.p_retailprice,\n       s.s_name, s.s_nationkey, n.n_name, ps.ps_supplycost\nFROM partsupp ps\nJOIN part p ON p.p_partkey = ps.ps_partkey\nJOIN supplier s ON s.s_suppkey = ps.s_suppkey\nJOIN nation n ON n.n_nationkey = s.s_nationkey\nJOIN region r ON r.r_regionkey = n.n_regionkey\nWHERE ps.ps_supplycost > 900\n  AND r.r_name = 'EUROPE'\nORDER BY ps.ps_supplycost DESC\nLIMIT 20"})
2026-08-28 19:29:31 | INFO     | agent:run_agent:69 - Intermediate result: {"valid": true, "sql": "SELECT p.p_partkey, p.p_name, p.p_mfgr, p.p_brand, p.p_size, p.p_retailprice,\n       s.s_name, s.s_nationkey, n.n_name, ps.ps_supplycost\nFROM partsupp ps\nJOIN part p ON p.p_
2026-08-28 19:29:31 | INFO     | agent:run_agent:41 - Iteration 3/10
2026-08-28 19:29:32 | INFO     | agent:run_agent:56 - Tool : run_query({'sql': "SELECT p.p_partkey, p.p_name, p.p_mfgr, p.p_brand, p.p_size, p.p_retailprice,\n       s.s_name, s.s_nationkey, n.n_name, ps.ps_supplycost\nFROM partsupp ps\nJOIN part p ON p.p_partkey = ps.ps_partkey\nJOIN supplier s ON s.s_suppkey = ps.s_suppkey\nJOIN nation n ON n.n_nationkey = s.s_nationkey\nJOIN region r ON r.r_regionkey = n.n_regionkey\nWHERE ps.ps_supplycost > 900\n  AND r.r_name = 'EUROPE'\nORDER BY ps.ps_supplycost DESC\nLIMIT 20"})
2026-08-28 19:29:32 | INFO     | tools.db:run_query:108 - {'error': 'Some error occured in run_query'} # explicitly raised to vet retry behaviour
2026-08-28 19:29:32 | INFO     | agent:run_agent:69 - Intermediate result: {"error": "Some error occured in run_query"}
2026-08-28 19:29:32 | INFO     | agent:run_agent:41 - Iteration 4/10
2026-08-28 19:29:41 | INFO     | agent:run_agent:56 - Tool : run_query({'sql': "SELECT p.p_partkey, p.p_name, p.p_mfgr, p.p_brand, p.p_size, p.p_retailprice,\n       s.s_name, s.s_nationkey, n.n_name, ps.ps_supplycost\nFROM partsupp ps\nJOIN part p ON p.p_partkey = ps.ps_partkey\nJOIN supplier s ON s.s_suppkey = ps.s_suppkey\nJOIN nation n ON n.n_nationkey = s.s_nationkey\nJOIN region r ON r.r_regionkey = n.n_regionkey\nWHERE ps.ps_supplycost > 900\n  AND r.r_name = 'EUROPE'\nORDER BY ps.ps_supplycost DESC\nLIMIT 20"})
2026-08-28 19:29:41 | INFO     | tools.db:run_query:108 - {'error': 'Some error occured in run_query'} # explicitly raised to vet retry behaviour
2026-08-28 19:29:41 | INFO     | agent:run_agent:69 - Intermediate result: {"error": "Some error occured in run_query"}
2026-08-28 19:29:41 | INFO     | agent:run_agent:41 - Iteration 5/10
2026-08-28 19:30:02 | INFO     | agent:run_agent:56 - Tool : run_query({'sql': "SELECT p.p_partkey, p.p_name, p.p_mfgr, p.p_brand, p.p_size, ps.ps_supplycost\nFROM partsupp ps\nJOIN part p ON p.p_partkey = ps.ps_partkey\nJOIN supplier s ON s.s_suppkey = ps.s_suppkey\nJOIN nation n ON n.n_nationkey = s.s_nationkey\nJOIN region r ON r.r_regionkey = n.n_regionkey\nWHERE ps.ps_supplycost > 900\n  AND r.r_name = 'EUROPE'\nLIMIT 20"})
2026-08-28 19:30:02 | INFO     | tools.db:run_query:108 - {'error': 'column ps.s_suppkey does not exist\nHINT:  Perhaps you meant to reference the column "ps.ps_suppkey" or the column "s.s_suppkey".'} # actual error in the generated query
2026-08-28 19:30:02 | INFO     | agent:run_agent:69 - Intermediate result: {"error": "column ps.s_suppkey does not exist\nHINT:  Perhaps you meant to reference the column \"ps.ps_suppkey\" or the column \"s.s_suppkey\"."}
2026-08-28 19:30:02 | INFO     | agent:run_agent:41 - Iteration 6/10
2026-08-28 19:30:16 | INFO     | agent:run_agent:56 - Tool : run_query({'sql': "SELECT p.p_partkey, p.p_name, p.p_mfgr, p.p_brand, p.p_size, ps.ps_supplycost\nFROM partsupp ps\nJOIN part p ON p.p_partkey = ps.ps_partkey\nJOIN supplier s ON s.s_suppkey = ps.ps_suppkey\nJOIN nation n ON n.n_nationkey = s.s_nationkey\nJOIN region r ON r.r_regionkey = n.n_regionkey\nWHERE ps.ps_supplycost > 900\n  AND r.r_name = 'EUROPE'\nLIMIT 20"})
2026-08-28 19:30:16 | INFO     | tools.db:run_query:105 - {'columns': ['p_partkey', 'p_name', 'p_mfgr', 'p_brand', 'p_size', 'ps_supplycost'], 'rows': [[24, 'seashell coral metallic midnight floral', 'Manufacturer#5', 'Brand#52', 20,Decimal('905.41')], [85, 'dim deep aquamarine smoke pale', 'Manufacturer#5', 'Brand#55', 16, Decimal('917.83')], [92, 'blush magenta ghost tomato rose', 'Manufacturer#2', 'Brand#22', 35, Decimal('985.03')], [100, 'cyan orchid indian cornflower saddle', 'Manufacturer#3', 'Brand#33', 4, Decimal('929.57')], [103, 'navy sky spring orchid forest', 'Manufacturer#2', 'Brand#25', 45, Decimal('905.88')], [109, 'lemon black indian cornflower pale', 'Manufacturer#3', 'Brand#33', 11, Decimal('992.21')], [109, 'lemon black indian cornflower pale', 'Manufacturer#3', 'Brand#33', 11, Decimal('936.60')], [139, 'floral steel burlywood navy cream', 'Manufacturer#3', 'Brand#32', 7, Decimal('972.23')], [147, 'honeydew orange dodger linen lace', 'Manufacturer#1', 'Brand#11', 29, Decimal('939.14')], [175, 'magenta blue chartreusetan green', 'Manufacturer#1', 'Brand#11', 45, Decimal('978.56')], [181, 'antique plum smoke pink dodger', 'Manufacturer#2', 'Brand#24', 19, Decimal('938.29')], [188, 'moccasin steel rosy drab white', 'Manufacturer#5', 'Brand#54', 9, Decimal('920.20')], [189, 'dodger moccasin lemon purple thistle', 'Manufacturer#2', 'Brand#22', 13, Decimal('946.07')], [192, 'thistle puff pink cream orange', 'Manufacturer#3', 'Brand#34', 17, Decimal('916.16')], [196, 'pale peru linen hot maroon', 'Manufacturer#3', 'Brand#33', 3, Decimal('966.01')], [222, 'aquamarine puff antique drab beige', 'Manufacturer#3', 'Brand#33', 35, Decimal('926.10')], [3799, 'turquoise beige wheat deep chiffon', 'Manufacturer#3', 'Brand#34', 33, Decimal('990.42')], [229, 'orchid misty cornsilk chartreuse medium', 'Manufacturer#1', 'Brand#15', 19, Decimal('984.71')], [231, 'bisque blush beige honeydew slate', 'Manufacturer#5', 'Brand#51', 17, Decimal('971.24')], [244, 'seashell ghost cyan burlywood thistle', 'Manufacturer#5', 'Brand#51', 48, Decimal('978.74')]], 'row_count': 20, 'note': None}
2026-08-28 19:30:16 | INFO     | agent:run_agent:69 - Intermediate result: {"columns": ["p_partkey", "p_name", "p_mfgr", "p_brand", "p_size", "ps_supplycost"], "rows": [[24, "seashell coral metallic midnight floral", "Manufacturer#5", "Brand#52", 20, 905.41], [85, "dim deep 
2026-08-28 19:30:16 | INFO     | agent:run_agent:41 - Iteration 7/10
2026-08-28 19:30:45 | INFO     | agent:run_agent:79 - Result: Here are 20 parts with a supply cost over 900 from European suppliers:

| Part Key | Name | Manufacturer | Brand | Size | Supply Cost |
|----------|------|--------------|-------|------|-------------|
| 109 | lemon black indian cornflower pale | Manufacturer#3 | Brand#33 | 11 | 992.21 |
| 3799 | turquoise beige wheat deep chiffon | Manufacturer#3 | Brand#34 | 33 | 990.42 |
| 109 | lemon black indian cornflower pale | Manufacturer#3 | Brand#33 | 11 | 936.60 |
| 92 | blush magenta ghost tomato rose | Manufacturer#2 | Brand#22 | 35 | 985.03 |
| 229 | orchid misty cornsilk chartreuse medium | Manufacturer#1 | Brand#15 | 19 | 984.71 |
| 175 | magenta blue chartreuse tan green | Manufacturer#1 | Brand#11 | 45 | 978.56 |
| 244 | seashell ghost cyan burlywood thistle | Manufacturer#5 | Brand#51 | 48 | 978.74 |
| 139 | floral steel burlywood navy cream | Manufacturer#3 | Brand#32 | 7 | 972.23 |
| 231 | bisque blush beige honeydew slate | Manufacturer#5 | Brand#51 | 17 | 971.24 |
| 196 | pale peru linen hot maroon | Manufacturer#3 | Brand#33 | 3 | 966.01 |
| 189 | dodger moccasin lemon purple thistle | Manufacturer#2 | Brand#22 | 13 | 946.07 |
| 147 | honeydew orange dodger linen lace | Manufacturer#1 | Brand#11 | 29 | 939.14 |
| 181 | antique plum smoke pink dodger | Manufacturer#2 | Brand#24 | 19 | 938.29 |
| 100 | cyan orchid indian cornflower saddle | Manufacturer#3 | Brand#33 | 4 | 929.57 |
| 222 | aquamarine puff antique drab beige | Manufacturer#3 | Brand#33 | 35 | 926.10 |
| 188 | moccasin steel rosy drab white | Manufacturer#5 | Brand#54 | 9 | 920.20 |
| 85 | dim deep aquamarine smoke pale | Manufacturer#5 | Brand#55 | 16 | 917.83 |
| 192 | thistle puff pink cream orange | Manufacturer#3 | Brand#34 | 17 | 916.16 |
| 103 | navy sky spring orchid forest | Manufacturer#2 | Brand#25 | 45 | 905.88 |
| 24 | seashell coral metallic midnight floral | Manufacturer#5 | Brand#52 | 20 | 905.41 |

Key observations:
- **Highest supply cost:** Part #109 ("lemon black indian cornflower pale") at **$992.21**, from a European supplier.
- **Most common manufacturer among these:** Manufacturer#3 (appears 6 times).
- Parts span a range of sizes (3–48) and all manufacturers (1–5).
- Note that part #109 appears twice with different supply costs, indicating it's supplied by two different European suppliers.

Let me know if you'd like to see supplier names/nations, adjust the cost threshold, or widen the result set!
2026-08-28 19:30:45 | INFO     | agent:run_agent:80 - Reached conclusion in 8 iterations
```
2. To notice: explain analize query
```sh
2026-08-28 19:59:21 | INFO     | __main__:main:19 - SQL Agent ready. Ask questions about the TPC-H database.
2026-08-28 19:59:21 | INFO     | agent:run_agent:35 - User question: What are the top 5 nations by total revenue? explain the query as well
2026-08-28 19:59:21 | INFO     | agent:run_agent:36 - --------------------------------------------------
2026-08-28 19:59:21 | INFO     | agent:run_agent:45 - Iteration 0/10
2026-08-28 19:59:21 | INFO     | agent:run_agent:60 - Tool : list_tables()
2026-08-28 19:59:21 | INFO     | agent:run_agent:73 - Intermediate result: {"tables": ["customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"]}
2026-08-28 19:59:21 | INFO     | agent:run_agent:45 - Iteration 1/10
2026-08-28 19:59:22 | INFO     | agent:run_agent:60 - Tool : get_table_schema({'table_name': 'lineitem'})
2026-08-28 19:59:22 | INFO     | agent:run_agent:73 - Intermediate result: {"table": "lineitem", "columns": [{"name": "l_orderkey", "type": "bigint", "nullable": "NO"}, {"name": "l_partkey", "type": "bigint", "nullable": "NO"}, {"name": "l_suppkey", "type": "bigint", "nullab
2026-08-28 19:59:22 | INFO     | agent:run_agent:60 - Tool : get_table_schema({'table_name': 'nation'})
2026-08-28 19:59:22 | INFO     | agent:run_agent:73 - Intermediate result: {"table": "nation", "columns": [{"name": "n_nationkey", "type": "integer", "nullable": "NO"}, {"name": "n_name", "type": "character varying", "nullable": "YES"}, {"name": "n_regionkey", "type": "integ
2026-08-28 19:59:22 | INFO     | agent:run_agent:60 - Tool : get_table_schema({'table_name': 'region'})
2026-08-28 19:59:22 | INFO     | agent:run_agent:73 - Intermediate result: {"table": "region", "columns": [{"name": "r_regionkey", "type": "integer", "nullable": "NO"}, {"name": "r_name", "type": "character varying", "nullable": "YES"}, {"name": "r_comment", "type": "charact
2026-08-28 19:59:22 | INFO     | agent:run_agent:45 - Iteration 2/10
2026-08-28 19:59:23 | INFO     | agent:run_agent:60 - Tool : get_table_schema({'table_name': 'supplier'})
2026-08-28 19:59:23 | INFO     | agent:run_agent:73 - Intermediate result: {"table": "supplier", "columns": [{"name": "s_suppkey", "type": "bigint", "nullable": "NO"}, {"name": "s_name", "type": "character varying", "nullable": "YES"}, {"name": "s_address", "type": "characte
2026-08-28 19:59:23 | INFO     | agent:run_agent:45 - Iteration 3/10
2026-08-28 19:59:24 | INFO     | agent:run_agent:60 - Tool : validate_query({'sql': 'SELECT n.n_name AS nation,\n   SUM(li.l_extendedprice * (1 - li.l_discount)) AS total_revenue\nFROM lineitem li\nJOIN supplier s ON s.s_suppkey = li.l_suppkey\nJOIN nation n ON n.n_nationkey = s.s_nationkey\nGROUP BY n.n_name\nORDER BY total_revenue DESC\nLIMIT5'})
2026-08-28 19:59:24 | INFO     | agent:run_agent:73 - Intermediate result: {"valid": true, "sql": "SELECT n.n_name AS nation,\n       SUM(li.l_extendedprice * (1 - li.l_discount)) AS total_revenue\nFROM lineitem li\nJOIN supplier s ON s.s_suppkey = li.l_suppkey\nJOIN nation 
2026-08-28 19:59:24 | INFO     | agent:run_agent:45 - Iteration 4/10
2026-08-28 19:59:28 | INFO     | agent:run_agent:60 - Tool : run_query({'sql': 'SELECT n.n_name AS nation,\n       SUM(li.l_extendedprice * (1 - li.l_discount)) AS total_revenue\nFROM lineitem li\nJOIN supplier s ON s.s_suppkey = li.l_suppkey\nJOIN nation n ON n.n_nationkey = s.s_nationkey\nGROUP BY n.n_name\nORDER BY total_revenue DESC\nLIMIT 5'})
2026-08-28 19:59:45 | INFO     | tools.db:run_query:106 - {'columns': ['nation', 'total_revenue'], 'rows': [['CANADA', Decimal('88742904918.1909')], ['IRAQ', Decimal('88603870239.2692')], ['INDIA', Decimal('88599438093.2672')], ['GERMANY', Decimal('88541902444.3566')], ['KENYA', Decimal('88070358728.3384')]], 'row_count': 5, 'note': None}
2026-08-28 19:59:45 | INFO     | agent:run_agent:73 - Intermediate result: {"columns": ["nation", "total_revenue"], "rows": [["CANADA", 88742904918.1909], ["IRAQ", 88603870239.2692], ["INDIA", 88599438093.2672], ["GERMANY", 88541902444.3566], ["KENYA", 88070358728.3384]], "r
2026-08-28 19:59:45 | INFO     | agent:run_agent:45 - Iteration 5/10
2026-08-28 19:59:48 | INFO     | agent:run_agent:60 - Tool : explain_analyze_query({'sql': 'SELECT n.n_name AS nation,\n       SUM(li.l_extendedprice * (1 - li.l_discount)) AS total_revenue\nFROM lineitem li\nJOIN supplier s ON s.s_suppkey = li.l_suppkey\nJOIN nation n ON n.n_nationkey = s.s_nationkey\nGROUP BY n.n_name\nORDER BY total_revenue DESC\nLIMIT 5'})
2026-08-28 20:00:02 | INFO     | tools.db:explain_analyze_query:144 - {'columns': ['QUERY PLAN'], 'rows': [['Limit  (cost=1712048.13..1712048.15 rows=5 width=100) (actual time=14712.047..14715.637 rows=5 loops=1)'], ['  ->  Sort  (cost=1712048.13..1712048.61 rows=190 width=100) (actual time=14586.706..14590.295 rows=5 loops=1)'], ["        Sort Key: (sum((li.l_extendedprice * ('1'::numeric - li.l_discount)))) DESC"], ['        Sort Method: top-N heapsort  Memory:25kB'], ['        ->  Finalize GroupAggregate  (cost=1711995.42..1712044.98 rows=190 width=100) (actual time=14586.638..14590.259 rows=25 loops=1)'], ['              Group Key: n.n_name'], ['              ->  Gather Merge  (cost=1711995.42..1712039.75 rows=380 width=100) (actual time=14586.617..14590.218 rows=75 loops=1)'], ['                    Workers Planned: 2'], ['                    Workers Launched: 2'], ['                    ->  Sort  (cost=1710995.39..1710995.87 rows=190 width=100) (actual time=14572.462..14572.466 rows=25 loops=3)'], ['                          Sort Key: n.n_name'], ['                          Sort Method: quicksort  Memory: 27kB'], ['                          Worker 0:  Sort Method: quicksort  Memory: 27kB'], ['                          Worker 1:  Sort Method: quicksort  Memory: 27kB'], ['                          ->  Partial HashAggregate  (cost=1710985.83..1710988.20 rows=190 width=100) (actual time=14572.409..14572.417 rows=25 loops=3)'], ['                                Group Key: n.n_name'], ['                      Batches: 1  Memory Usage: 48kB'], ['                                Worker 0:  Batches: 1  Memory Usage: 48kB'], ['                                Worker 1:  Batches: 1  Memory Usage: 48kB'], ['              ->  Hash Join  (cost=3537.81..1461050.86 rows=24993497 width=80) (actual time=113.021..8021.309 rows=19995351 loops=3)'], ['                                      Hash Cond: (s.s_nationkey = n.n_nationkey)'], ['                            ->  Parallel Hash Join  (cost=3523.54..1393965.21 rows=24993497 width=16) (actual time=10.937..5765.812 rows=19995351 loops=3)'], ['                                            Hash Cond: (li.l_suppkey = s.s_suppkey)'], ['                                            ->  Parallel Seq Scan on lineitem li  (cost=0.00..1324830.97 rows=24993497 width=20) (actual time=0.440..1719.239 rows=19995351 loops=3)'], ['           ->  Parallel Hash  (cost=2788.24..2788.24 rows=58824 width=12) (actual time=10.160..10.160 rows=33333 loops=3)'], ['                                                  Buckets: 131072  Batches: 1  Memory Usage: 5728kB'], ['                                                ->  Parallel Seq Scan on supplier s  (cost=0.00..2788.24 rows=58824 width=12) (actual time=0.012..13.335 rows=100000 loops=1)'], ['                                      ->  Hash  (cost=11.90..11.90 rows=190 width=72) (actual time=102.051..102.051 rows=25 loops=3)'], ['          Buckets: 1024  Batches: 1  Memory Usage: 10kB'], ['                                            ->  Seq Scan on nation n  (cost=0.00..11.90 rows=190 width=72) (actual time=102.037..102.040 rows=25 loops=3)'], ['Planning Time: 0.263 ms'], ['JIT:'], ['  Functions: 73'], ['  Options: Inlining true, Optimization true, Expressions true, Deforming true'], ['  Timing: Generation 2.608 ms (Deform 1.145 ms), Inlining 132.463 ms, Optimization 173.271 ms, Emission 125.776 ms, Total 434.118 ms'], ['Execution Time: 14716.398 ms']], 'row_count': 36}
2026-08-28 20:00:02 | INFO     | agent:run_agent:73 - Intermediate result: {"columns": ["QUERY PLAN"], "rows": [["Limit  (cost=1712048.13..1712048.15 rows=5 width=100) (actual time=14712.047..14715.637 rows=5 loops=1)"], ["  ->  Sort (cost=1712048.13..1712048.61 rows=190 wi
2026-08-28 20:00:02 | INFO     | agent:run_agent:45 - Iteration 6/10
2026-08-28 20:00:26 | INFO     | agent:run_agent:83 - Result: ## Query Execution Explanation

Here's a plain-English breakdown of the EXPLAIN ANALYZE plan:

### Overall structure
The query runs **in parallel with 2 worker processes** ("Workers Planned: 2 / Launched: 2") and finished in **~14.7 seconds** total. There are no index scans or nested-loop joins — everything is driven by **hash joins** fed by **sequential scans**, which is expected for this full-table aggregation.

### Scans (all sequential, no indexes used)
- **`lineitem`** — Parallel Seq Scan, ~**20 million rows** (19,995,351). This is the dominant cost; scanning the entire `lineitem` table is the bulk of the execution time (~1.7s per worker).
- **`supplier`** — Seq Scan, 100,000 rows, loaded into a hash table (~5.7 MB memory).
- **`nation`** — Seq Scan, only **25 rows**. Tiny table, scanned repeatedly (loops=3).

### Joins (both hash joins)
1. **`lineitem` ⟕ `supplier`** (`l_suppkey = s_suppkey`) — a **Parallel Hash Join**. The small `supplier` table is hashed, and each of the 20M line items is probed against it. Estimated 25M rows → actual ~20M rows (estimate was slightly high).
2. **result ⟕ `nation`** (`s_nationkey = n_nationkey`) — a regular **Hash Join**. The 25-row `nation` table is hashed and the 20M intermediate rows are probed against it.

### Aggregation (two-phase, parallel)
- **Partial HashAggregate** — each of the 3 parallel processes locally aggregates its share into **25 nation groups** (25 rows each).
- **Gather Merge** + **Finalize GroupAggregate** — the 25 groups from each process are merged into a single final aggregation (still 25 total nations).

### Final sort & limit
- A **top-N heapsort** (only ~25 rows, 25 kB memory) sorts the 25 nations by revenue descending.
- **Limit** returns just the **top 5**.

### Cost/estimate highlights
- The planner estimated **25,000,000** line-item join rows; actual was **19,995,351** — a minor overestimate, so theplan was well-tuned.
- The small dimension tables (`nation`, `supplier`) were correctly identified as hash-build sides, keeping the expensive hash tables small.
- **JIT compilation** kicked in (~0.43 s) because the query is compute and JIT was enabled.

**Key takeaway:** This is a textbook "scan the big fact table (lineitem) and hash-join two small dimension tables, then aggregate" plan. The wall-clock cost (~14.7 s) is driven almost entirely by the sequential read of the 20M-row `lineitem` table; the joins, aggregation, and top-N sort are comparatively cheap because the dimension tables are tiny and the final result set is small.
2026-08-28 20:00:26 | INFO     | agent:run_agent:84 - Reached conclusion in 7 iterations
2026-08-28 20:00:26 | INFO     | __main__:main:30 - --------------------------------------------------
2026-08-28 20:00:26 | INFO     | __main__:main:31 - USER QUESTION: What are the top 5 nations by total revenue? explain the query as well
2026-08-28 20:00:26 | INFO     | __main__:main:32 - AGENT RESPONSE: ## Query Execution Explanation

Here's a plain-English breakdown of the EXPLAIN ANALYZE plan:

### Overall structure
The query runs **in parallel with 2 worker processes** ("Workers Planned: 2 / Launched: 2") and finished in **~14.7 seconds** total. There are no index scans or nested-loop joins — everything is driven by **hash joins** fed by **sequential scans**, which is expected for this full-table aggregation.

### Scans (all sequential, no indexes used)
- **`lineitem`** — Parallel Seq Scan, ~**20 million rows** (19,995,351). This is the dominant cost; scanning the entire `lineitem` table is the bulk of the execution time (~1.7s per worker).
- **`supplier`** — Seq Scan, 100,000 rows, loaded into a hash table (~5.7 MB memory).
- **`nation`** — Seq Scan, only **25 rows**. Tiny table, scanned repeatedly (loops=3).

### Joins (both hash joins)
1. **`lineitem` ⟕ `supplier`** (`l_suppkey = s_suppkey`) — a **Parallel Hash Join**. The small `supplier` table is hashed, and each of the 20M line items is probed against it. Estimated 25M rows → actual ~20M rows (estimate was slightly high).
2. **result ⟕ `nation`** (`s_nationkey = n_nationkey`) — a regular **Hash Join**. The 25-row `nation` table is hashed and the 20M intermediate rows are probed against it.

### Aggregation (two-phase, parallel)
- **Partial HashAggregate** — each of the 3 parallel processes locally aggregates its share into **25 nation groups** (25 rows each).
- **Gather Merge** + **Finalize GroupAggregate** — the 25 groups from each process are merged into a single final aggregation (still 25 total nations).

### Final sort & limit
- A **top-N heapsort** (only ~25 rows, 25 kB memory) sorts the 25 nations by revenue descending.
- **Limit** returns just the **top 5**.

### Cost/estimate highlights
- The planner estimated **25,000,000** line-item join rows; actual was **19,995,351** — a minor overestimate, so theplan was well-tuned.
- The small dimension tables (`nation`, `supplier`) were correctly identified as hash-build sides, keeping the expensive hash tables small.
- **JIT compilation** kicked in (~0.43 s) because the query is compute and JIT was enabled.

**Key takeaway:** This is a textbook "scan the big fact table (lineitem) and hash-join two small dimension tables, then aggregate" plan. The wall-clock cost (~14.7 s) is driven almost entirely by the sequential read of the 20M-row `lineitem` table; the joins, aggregation, and top-N sort are comparatively cheap because the dimension tables are tiny and the final result set is small.
2026-08-28 20:00:26 | INFO     | __main__:main:33 - ==================================================
```

## Example questions
- How many customers do we have?
- In how many regions do we operate?
- In how many countries do we operate?
- What are the top 5 nations by total revenue?
