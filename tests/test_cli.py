import sqlite3
import subprocess
import sys

import pytest

import main
import seed


def make_db(path, defects):
    conn = sqlite3.connect(path)
    conn.executescript(seed.build_sql(defects)[0])
    conn.close()


def run(tmp_path, *args):
    return main.main([*args, "--report", str(tmp_path / "report.md")])


def test_exit_code_is_1_when_errors_found(tmp_path):
    db = tmp_path / "errors.db"
    make_db(db, {"negative_amount": 2})
    assert run(tmp_path, "--db", str(db)) == 1


def test_exit_code_is_0_when_only_warnings_found(tmp_path, capsys):
    db = tmp_path / "warnings.db"
    make_db(db, {"invalid_email": 3})
    assert run(tmp_path, "--db", str(db)) == 0
    assert "Invalid email format" in capsys.readouterr().out


def test_exit_code_is_0_and_report_empty_on_clean_database(tmp_path, capsys):
    db = tmp_path / "clean.db"
    make_db(db, {})
    assert run(tmp_path, "--db", str(db)) == 0
    assert "No issues found." in capsys.readouterr().out
    assert "No issues found." in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_report_lists_findings(tmp_path):
    db = tmp_path / "errors.db"
    make_db(db, {"orphan_contracts": 4})
    run(tmp_path, "--db", str(db))
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "| Contracts referencing a missing customer | error | 4 |" in report


def test_missing_database_without_seed_is_a_usage_error(tmp_path):
    with pytest.raises(SystemExit) as exc:
        run(tmp_path, "--db", str(tmp_path / "absent.db"))
    assert exc.value.code == 2


def test_seed_command_end_to_end(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(main.ROOT / "main.py"), "--seed", "--db", "demo.db", "--report", "report.md"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert proc.returncode == 1
    assert "Duplicate emails" in proc.stdout
    assert (tmp_path / "report.md").exists()


@pytest.mark.postgres
def test_postgres_mode_end_to_end(tmp_path, pg_dsn):
    assert run(tmp_path, "--dsn", pg_dsn, "--seed") == 1
