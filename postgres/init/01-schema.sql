CREATE TABLE region (
    r_regionkey INTEGER PRIMARY KEY,
    r_name      VARCHAR(25),
    r_comment   VARCHAR(152)
);

CREATE TABLE nation (
    n_nationkey INTEGER PRIMARY KEY,
    n_name     VARCHAR(25),
    n_regionkey INTEGER NOT NULL,
    n_comment  VARCHAR(152),

    CONSTRAINT nation_region_fk
        FOREIGN KEY (n_regionkey)
        REFERENCES region(r_regionkey)
);

CREATE TABLE part (
    p_partkey     BIGINT PRIMARY KEY,
    p_name        VARCHAR(55),
    p_mfgr        VARCHAR(25),
    p_brand       VARCHAR(10),
    p_type        VARCHAR(25),
    p_size        INTEGER,
    p_container   VARCHAR(10),
    p_retailprice DECIMAL(15,2),
    p_comment     VARCHAR(23)
);

CREATE TABLE supplier (
    s_suppkey   BIGINT PRIMARY KEY,
    s_name      VARCHAR(25),
    s_address   VARCHAR(40),
    s_nationkey INTEGER NOT NULL,
    s_phone     VARCHAR(15),
    s_acctbal   DECIMAL(15,2),
    s_comment   VARCHAR(101),

    CONSTRAINT supplier_nation_fk
        FOREIGN KEY (s_nationkey)
        REFERENCES nation(n_nationkey)
);

CREATE TABLE partsupp (
    ps_partkey    BIGINT NOT NULL,
    ps_suppkey    BIGINT NOT NULL,
    ps_availqty   INTEGER,
    ps_supplycost DECIMAL(15,2),
    ps_comment    VARCHAR(199),

    PRIMARY KEY (ps_partkey, ps_suppkey),

    CONSTRAINT partsupp_part_fk
        FOREIGN KEY (ps_partkey)
        REFERENCES part(p_partkey),

    CONSTRAINT partsupp_supplier_fk
        FOREIGN KEY (ps_suppkey)
        REFERENCES supplier(s_suppkey)
);

CREATE TABLE customer (
    c_custkey    BIGINT PRIMARY KEY,
    c_name       VARCHAR(25),
    c_address    VARCHAR(40),
    c_nationkey  INTEGER NOT NULL,
    c_phone      VARCHAR(15),
    c_acctbal    DECIMAL(15,2),
    c_mktsegment VARCHAR(10),
    c_comment    VARCHAR(117),

    CONSTRAINT customer_nation_fk
        FOREIGN KEY (c_nationkey)
        REFERENCES nation(n_nationkey)
);

CREATE TABLE orders (
    o_orderkey      BIGINT PRIMARY KEY,
    o_custkey       BIGINT NOT NULL,
    o_orderstatus   CHAR(1),
    o_totalprice    DECIMAL(15,2),
    o_orderdate     DATE,
    o_orderpriority VARCHAR(15),
    o_clerk         VARCHAR(15),
    o_shippriority  INTEGER,
    o_comment       VARCHAR(79),

    CONSTRAINT orders_customer_fk
        FOREIGN KEY (o_custkey)
        REFERENCES customer(c_custkey)
);

CREATE TABLE lineitem (
    l_orderkey      BIGINT NOT NULL,
    l_partkey       BIGINT NOT NULL,
    l_suppkey       BIGINT NOT NULL,
    l_linenumber    INTEGER NOT NULL,
    l_quantity      DECIMAL(15,2),
    l_extendedprice DECIMAL(15,2),
    l_discount      DECIMAL(15,2),
    l_tax           DECIMAL(15,2),
    l_returnflag    CHAR(1),
    l_linestatus    CHAR(1),
    l_shipdate      DATE,
    l_commitdate    DATE,
    l_receiptdate   DATE,
    l_shipinstruct  VARCHAR(25),
    l_shipmode      VARCHAR(10),
    l_comment       VARCHAR(44),

    PRIMARY KEY (l_orderkey, l_linenumber),

    CONSTRAINT lineitem_order_fk
        FOREIGN KEY (l_orderkey)
        REFERENCES orders(o_orderkey),

    CONSTRAINT lineitem_part_fk
        FOREIGN KEY (l_partkey)
        REFERENCES part(p_partkey),

    CONSTRAINT lineitem_supplier_fk
        FOREIGN KEY (l_suppkey)
        REFERENCES supplier(s_suppkey)
);