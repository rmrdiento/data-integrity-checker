import pytest

import main
import seed


def counts(conn):
    return {r["file"]: r["count"] for r in main.run_checks(conn)}


def test_every_check_has_a_defect_type():
    assert {c["file"] for c in main.load_checks()} == set(seed.DEFAULT_DEFECTS)


def test_checks_find_exactly_the_injected_defects(conn, load):
    injected = load()
    assert injected == seed.DEFAULT_DEFECTS
    assert counts(conn) == injected


@pytest.mark.parametrize("defect", sorted(seed.DEFAULT_DEFECTS))
def test_single_defect_type_is_found_only_by_its_own_check(conn, load, defect):
    injected = load({defect: 7})
    assert injected[defect] == 7
    assert counts(conn) == injected


def test_clean_database_has_no_findings(conn, load):
    load({})
    results = main.run_checks(conn)
    assert [r for r in results if r["count"]] == []


def test_seed_is_deterministic():
    assert seed.build_sql() == seed.build_sql()


def test_seed_sizes(conn, load):
    load()
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == seed.CUSTOMERS
    assert conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0] == seed.CONTRACTS


def test_unknown_defect_type_is_rejected():
    with pytest.raises(ValueError):
        seed.generate({"typo": 1})


def test_docker_init_script_is_up_to_date():
    committed = (seed.ROOT / "docker" / "init.sql").read_text(encoding="utf-8")
    assert committed == seed.build_sql()[0]
