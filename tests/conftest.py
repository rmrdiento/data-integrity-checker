import os
import sqlite3

import pytest

import main
import seed

PG_DSN = os.environ.get("TEST_PG_DSN", "postgresql://checker:checker@localhost:5432/checker")


@pytest.fixture(scope="session")
def pg_dsn():
    try:
        import psycopg

        psycopg.connect(PG_DSN, connect_timeout=3).close()
    except Exception as exc:
        pytest.skip(f"PostgreSQL unavailable ({exc.__class__.__name__}); start it with: docker compose up -d db")
    return PG_DSN


@pytest.fixture(params=["sqlite", pytest.param("postgres", marks=pytest.mark.postgres)])
def conn(request):
    if request.param == "sqlite":
        connection = sqlite3.connect(":memory:")
    else:
        import psycopg

        connection = psycopg.connect(request.getfixturevalue("pg_dsn"))
    yield connection
    connection.close()


@pytest.fixture
def load(conn):
    def _load(defects=seed.DEFAULT_DEFECTS):
        sql, injected = seed.build_sql(defects)
        main.apply_script(conn, sql)
        return injected

    return _load
