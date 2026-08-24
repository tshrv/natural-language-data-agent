-- This script runs in DuckDB and loads the TPC-H data into a PostgreSQL database.

INSTALL postgres;
LOAD postgres;

ATTACH 'host=postgres port=5432 dbname=tpch user=postgres password=postgres'
    AS pg (TYPE postgres);

INSERT INTO pg.public.region
SELECT *
FROM read_parquet('/data/region.parquet');

INSERT INTO pg.public.nation
SELECT *
FROM read_parquet('/data/nation.parquet');

INSERT INTO pg.public.part
SELECT *
FROM read_parquet('/data/part.parquet');

INSERT INTO pg.public.supplier
SELECT *
FROM read_parquet('/data/supplier.parquet');

INSERT INTO pg.public.partsupp
SELECT *
FROM read_parquet('/data/partsupp.parquet');

INSERT INTO pg.public.customer
SELECT *
FROM read_parquet('/data/customer.parquet');

INSERT INTO pg.public.orders
SELECT *
FROM read_parquet('/data/orders.parquet');

INSERT INTO pg.public.lineitem
SELECT *
FROM read_parquet('/data/lineitem.parquet');

DETACH pg;