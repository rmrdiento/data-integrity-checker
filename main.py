import argparse
import re
import sqlite3
import sys
from pathlib import Path

import seed

ROOT = Path(__file__).parent
CHECKS = ROOT / "checks"
HEADER = re.compile(r"--\s*check:\s*(.+?)\s*\|\s*severity:\s*(error|warning)\s*$")
SAMPLES = 5


def connect(dsn, db):
    if dsn:
        import psycopg

        return psycopg.connect(dsn)
    return sqlite3.connect(db)


def apply_script(conn, sql):
    if hasattr(conn, "executescript"):
        conn.executescript(sql)
    else:
        conn.execute(sql)
    conn.commit()


def load_checks(checks_dir=CHECKS):
    checks = []
    for path in sorted(Path(checks_dir).glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        match = HEADER.match(sql.splitlines()[0])
        if not match:
            raise ValueError(f"{path.name}: first line must be '-- check: <name> | severity: error|warning'")
        checks.append({"file": path.stem, "name": match[1], "severity": match[2], "sql": sql})
    return checks


def run_checks(conn, checks_dir=CHECKS):
    results = []
    for check in load_checks(checks_dir):
        rows = conn.execute(check["sql"]).fetchall()
        results.append({
            "file": check["file"],
            "name": check["name"],
            "severity": check["severity"],
            "count": len(rows),
            "samples": [(str(row[0]), str(row[1])) for row in rows[:SAMPLES]],
        })
    return results


def format_table(findings):
    header = ("Check", "Severity", "Count", "Example ids")
    rows = [
        (f["name"], f["severity"], str(f["count"]), ", ".join(i for i, _ in f["samples"])) for f in findings
    ]
    widths = [max(len(r[k]) for r in [header, *rows]) for k in range(len(header))]

    def line(cells):
        return "  ".join(cell.ljust(width) for cell, width in zip(cells, widths)).rstrip()

    return "\n".join([line(header), line(["-" * w for w in widths]), *map(line, rows)])


def format_markdown(results, findings):
    lines = ["# Data Integrity Report", "", f"{len(results)} checks run, {len(findings)} with findings.", ""]
    if not findings:
        return "\n".join([*lines, "No issues found.", ""])
    lines += ["| Check | Severity | Count | Example ids |", "| --- | --- | ---: | --- |"]
    for f in findings:
        ids = ", ".join(f"`{i}`" for i, _ in f["samples"])
        lines.append(f"| {f['name']} | {f['severity']} | {f['count']} | {ids} |")
    for f in findings:
        lines += ["", f"## {f['name']}", ""]
        lines += [f"- id {i}: {detail}" for i, detail in f["samples"]]
    return "\n".join([*lines, ""])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run SQL data-integrity checks and report problem rows.")
    parser.add_argument("--dsn", help="PostgreSQL connection string; SQLite is used when omitted")
    parser.add_argument("--db", default="integrity.db", help="SQLite database file (default: %(default)s)")
    parser.add_argument("--seed", action="store_true", help="(re)create schema and load synthetic data first")
    parser.add_argument("--report", default="report.md", help="Markdown report path (default: %(default)s)")
    args = parser.parse_args(argv)
    if not (args.dsn or args.seed or Path(args.db).exists()):
        parser.error(f"{args.db} not found; run with --seed to create it")

    conn = connect(args.dsn, args.db)
    if args.seed:
        sql, injected = seed.build_sql()
        apply_script(conn, sql)
        print(f"Seeded {seed.CUSTOMERS} customers and {seed.CONTRACTS} contracts "
              f"with {sum(injected.values())} injected defects.\n")
    results = run_checks(conn)
    conn.close()

    findings = [r for r in results if r["count"]]
    print(format_table(findings) if findings else "No issues found.")
    Path(args.report).write_text(format_markdown(results, findings), encoding="utf-8")
    print(f"\n{len(results)} checks run, {len(findings)} with findings. Report: {args.report}")
    return 1 if any(f["severity"] == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
