"""
Seed (or refresh) the synthetic demo workforce.

All people in data/demo_employees.json are fictional: names are random
combinations of common first and last names, emails use example.com.

The script is idempotent:
    * departments are created when missing
    * legacy department names are merged into their English counterparts
      (employees, shifts and rules are moved before the old row is removed)
    * employees are matched by email and created or updated

Usage:
    python -m app.scripts.seed_demo_data [--dry-run]
"""

import argparse
import json
from pathlib import Path

from app.database import SessionLocal
from app.models.department import Department
from app.models.employee import Employee
from app.models.shift import Shift
from app.models.shift_rule import ShiftRule

DATA_FILE = Path(__file__).parent / "data" / "demo_employees.json"

DEPARTMENTS = {
    "Engineering": "Product and platform engineering",
    "Operations": "Day-to-day operations and logistics",
    "Customer Service": "Customer support and success",
    "HR": "People operations and recruiting",
    "Finance": "Accounting and financial planning",
}

# Earlier versions of the demo data used Turkish department names
LEGACY_DEPARTMENTS = {
    "Muhendislik": "Engineering",
    "Operasyon": "Operations",
    "Musteri Hizmetleri": "Customer Service",
    "IK": "HR",
    "Finans": "Finance",
}

DAY_INDEX = {"sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4, "friday": 5, "saturday": 6}


def ensure_departments(db) -> dict:
    by_name = {d.name: d for d in db.query(Department).all()}

    for legacy, target in LEGACY_DEPARTMENTS.items():
        old = by_name.get(legacy)
        if not old:
            continue
        new = by_name.get(target)
        if new is None:
            old.name = target
            old.description = DEPARTMENTS[target]
            by_name[target] = old
            print(f"  renamed department {legacy!r} -> {target!r}")
        else:
            for model in (Employee, Shift, ShiftRule):
                moved = (
                    db.query(model)
                    .filter(model.department_id == old.id)
                    .update({model.department_id: new.id}, synchronize_session=False)
                )
                if moved:
                    print(f"  moved {moved} {model.__tablename__} from {legacy!r} to {target!r}")
            db.delete(old)
            print(f"  merged department {legacy!r} into {target!r}")
        by_name.pop(legacy, None)
    db.flush()

    for name, description in DEPARTMENTS.items():
        dept = by_name.get(name)
        if dept is None:
            dept = Department(name=name, description=description)
            db.add(dept)
            by_name[name] = dept
            print(f"  created department {name!r}")
        elif not dept.description:
            dept.description = description
    db.flush()
    return by_name


def seed(dry_run: bool = False) -> None:
    people = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        departments = ensure_departments(db)
        existing = {e.email: e for e in db.query(Employee).all()}
        created = updated = 0

        for person in people:
            preferences = {
                "preferred_shift": person["preferred_shift"],
                "weekly_off_day": DAY_INDEX[person["weekly_off_day"]],
                "work_model": person["work_model"],
            }
            values = dict(
                name=person["name"],
                role=person["role"],
                department_id=departments[person["department"]].id,
                preferences=preferences,
            )
            employee = existing.get(person["email"])
            if employee is None:
                db.add(Employee(email=person["email"], availability=[], weekly_working_limit=40.0,
                                overtime_limit=10.0, **values))
                created += 1
            else:
                for key, value in values.items():
                    setattr(employee, key, value)
                updated += 1

        if dry_run:
            db.rollback()
            print(f"Dry run: would create {created} and update {updated} employees.")
        else:
            db.commit()
            print(f"Seed completed: created {created}, updated {updated} employees.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the synthetic demo workforce.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without saving")
    seed(parser.parse_args().dry_run)
