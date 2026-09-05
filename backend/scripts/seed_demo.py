"""Seed fictional schools, teachers, and students for local development."""

from pathlib import Path
import sys

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.db import Base, SessionLocal, engine  # noqa: E402
from backend.app.models import School, Student, Teacher  # noqa: E402


SCHOOLS = [
    {
        "name": "Riverbend Public School",
        "district": "Northfield",
        "block": "Riverbend",
        "teachers": [
            ("TCH-001", "Asha Menon", "+15550101001"),
            ("TCH-002", "Daniel Brooks", "+15550101002"),
        ],
        "students": [
            ("STU-001", "Maya Patel"),
            ("STU-002", "Leo Carter"),
            ("STU-003", "Zoe Williams"),
            ("STU-004", "Arjun Shah"),
            ("STU-005", "Nora Wilson"),
            ("STU-011", "Aniket Malhotra"),
            # STU-011, Aniket Malhotra, SCH-002,Screenshot 2025-12-01 at 8.34.10 AM.png
        ],
    },
    {
        "name": "Pinecrest Community School",
        "district": "Northfield",
        "block": "Pinecrest",
        "teachers": [("TCH-003", "Priya Nair", "+15550101003")],
        "students": [
            ("STU-006", "Ethan Brown"),
            ("STU-007", "Isha Rao"),
            ("STU-008", "Oliver Smith"),
            ("STU-009", "Sara Khan"),
            ("STU-011", "Aniket Malhotra"),
            ("STU-010", "Lucas Martin"),
        ],
    },
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(School).limit(1)):
            print("Demo data already exists; nothing changed.")
            return
        for school_data in SCHOOLS:
            school = School(
                name=school_data["name"],
                district=school_data["district"],
                block=school_data["block"],
            )
            db.add(school)
            db.flush()
            for external_id, name, phone in school_data["teachers"]:
                db.add(
                    Teacher(
                        external_id=external_id,
                        name=name,
                        phone=phone,
                        school_id=school.id,
                    )
                )
            for external_id, name in school_data["students"]:
                db.add(
                    Student(
                        external_id=external_id,
                        name=name,
                        school_id=school.id,
                    )
                )
        db.commit()
    print("Seeded 2 fictional schools, 3 teachers, and 10 students.")


if __name__ == "__main__":
    seed()
