"""Seed one customer for manual API testing."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.session import SessionLocal, init_db
from models import Customer


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Customer).first()
        if existing:
            print(f"Customer already exists: id={existing.id} name={existing.name!r}")
            return
        customer = Customer(name="Jane Doe", phone="+15550100")
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"Created customer id={customer.id} name={customer.name!r}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
