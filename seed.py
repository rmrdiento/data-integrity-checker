import argparse
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
SEED = 42
CUSTOMERS = 1500
CONTRACTS = 3000

DEFAULT_DEFECTS = {
    "duplicate_email": 15,
    "duplicate_contract_number": 20,
    "missing_customer_fields": 18,
    "missing_contract_fields": 25,
    "orphan_contracts": 22,
    "invalid_email": 30,
    "invalid_phone": 28,
    "invalid_date": 24,
    "end_before_start": 17,
    "negative_amount": 21,
}

FIRST_NAMES = ["Anna", "Boris", "Clara", "Dmitry", "Elena", "Felix", "Greta", "Hugo", "Irina", "Jonas"]
LAST_NAMES = ["Petrov", "Ivanova", "Smith", "Novak", "Keller", "Moreau", "Rossi", "Sidorov", "Weber", "Kim"]
DOMAINS = ["mail.com", "example.org", "corp.net", "post.io"]
BAD_PHONES = ["89001234567", "+7 900 123 45 67", "+7900123", "+7abc1234567", "n/a"]
BAD_DATE_FORMATS = ["%d.%m.%Y", "%Y/%m/%d", "%Y%m%d", "%d-%m-%Y", "TBD"]


def make_customer(rng, cid):
    first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
    return {
        "id": cid,
        "full_name": f"{first} {last}",
        "email": f"{first}.{last}{cid}@{rng.choice(DOMAINS)}".lower(),
        "phone": f"+79{rng.randrange(10**9):09d}",
    }


def make_contract(rng, cid, customers):
    start = date(2020, 1, 1) + timedelta(days=rng.randrange(1800))
    end = start + timedelta(days=rng.randint(30, 1095))
    return {
        "id": cid,
        "contract_number": f"C-{start.year}-{cid:06d}",
        "customer_id": rng.randint(1, customers),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "amount": round(rng.uniform(1000, 500000), 2),
    }


def take(pool, n):
    return [pool.pop() for _ in range(n)]


def inject(pool, n, mutate):
    for i, row in enumerate(take(pool, n)):
        mutate(row, i)


def inject_duplicates(pool, n, field):
    for row, original in zip(take(pool, n), take(pool, n)):
        value = original[field]
        row[field] = value.upper() if row["id"] % 2 else value


def generate(defects=DEFAULT_DEFECTS, customers=CUSTOMERS, contracts=CONTRACTS, seed=SEED):
    unknown = set(defects) - set(DEFAULT_DEFECTS)
    if unknown:
        raise ValueError(f"unknown defect types: {sorted(unknown)}")
    rng = random.Random(seed)
    people = [make_customer(rng, i) for i in range(1, customers + 1)]
    deals = [make_contract(rng, i, customers) for i in range(1, contracts + 1)]
    # Every defect gets its own rows, so each check sees exactly what was injected.
    people_pool = rng.sample(people, len(people))
    deals_pool = rng.sample(deals, len(deals))
    n = {name: defects.get(name, 0) for name in DEFAULT_DEFECTS}

    inject_duplicates(people_pool, n["duplicate_email"], "email")
    inject_duplicates(deals_pool, n["duplicate_contract_number"], "contract_number")

    def blank_customer_field(row, i):
        row[("full_name", "email", "phone")[i % 3]] = None if i % 2 == 0 else ""

    def blank_contract_field(row, i):
        row[("contract_number", "customer_id", "start_date", "amount")[i % 4]] = None

    def break_email(row, i):
        email = row["email"]
        row["email"] = [
            email.replace("@", ""),
            email.replace("@", " @"),
            email.replace("@", "@@"),
            email.rsplit(".", 1)[0],
        ][i % 4]

    def break_date(row, i):
        field = ("start_date", "end_date")[i % 2]
        row[field] = date.fromisoformat(row[field]).strftime(BAD_DATE_FORMATS[i % len(BAD_DATE_FORMATS)])

    def end_before_start(row, i):
        row["end_date"] = (date.fromisoformat(row["start_date"]) - timedelta(days=rng.randint(1, 365))).isoformat()

    inject(people_pool, n["missing_customer_fields"], blank_customer_field)
    inject(people_pool, n["invalid_email"], break_email)
    inject(people_pool, n["invalid_phone"], lambda row, i: row.update(phone=BAD_PHONES[i % len(BAD_PHONES)]))
    inject(deals_pool, n["missing_contract_fields"], blank_contract_field)
    inject(deals_pool, n["orphan_contracts"], lambda row, i: row.update(customer_id=customers + rng.randint(1, 1000)))
    inject(deals_pool, n["invalid_date"], break_date)
    inject(deals_pool, n["end_before_start"], end_before_start)
    inject(deals_pool, n["negative_amount"], lambda row, i: row.update(amount=-row["amount"]))
    return people, deals, n


def literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(value)


def insert_statements(table, columns, rows, batch=500):
    for start in range(0, len(rows), batch):
        values = ",\n".join(
            "(" + ", ".join(literal(row[c]) for c in columns) + ")" for row in rows[start:start + batch]
        )
        yield f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n{values};"


def build_sql(defects=DEFAULT_DEFECTS):
    people, deals, injected = generate(defects)
    parts = [
        (ROOT / "schema.sql").read_text(encoding="utf-8"),
        *insert_statements("customers", ["id", "full_name", "email", "phone"], people),
        *insert_statements(
            "contracts", ["id", "contract_number", "customer_id", "start_date", "end_date", "amount"], deals
        ),
    ]
    return "\n".join(parts) + "\n", injected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write the schema and seed data as one SQL script.")
    parser.add_argument("out", nargs="?", default="docker/init.sql")
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build_sql()[0].encode("utf-8"))
    print(f"wrote {args.out}")
