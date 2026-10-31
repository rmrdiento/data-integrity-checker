DROP TABLE IF EXISTS contracts;
DROP TABLE IF EXISTS customers;

-- No NOT NULL, UNIQUE or FOREIGN KEY constraints on purpose: this is the
-- raw layer the checks audit, so bad rows have to be loadable.
CREATE TABLE customers (
    id        INTEGER PRIMARY KEY,
    full_name TEXT,
    email     TEXT,
    phone     TEXT
);

CREATE TABLE contracts (
    id              INTEGER PRIMARY KEY,
    contract_number TEXT,
    customer_id     INTEGER,
    start_date      TEXT,
    end_date        TEXT,
    amount          NUMERIC(12, 2)
);
