from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class School(Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    district: Mapped[str] = mapped_column(String(100), index=True)
    block: Mapped[str] = mapped_column(String(100), index=True)
    students: Mapped[list["Student"]] = relationship(back_populates="school")
    teachers: Mapped[list["Teacher"]] = relationship(back_populates="school")


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    role: Mapped[str] = mapped_column(String(30), default="teacher")
    school: Mapped[School] = relationship(back_populates="teachers")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    school: Mapped[School] = relationship(back_populates="students")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("student_id", "attendance_date", name="uq_student_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    client_event_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    attendance_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(20))
    absence_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    recorded_by: Mapped[str] = mapped_column(String(100))
    correction_status: Mapped[str] = mapped_column(String(20), default="none")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
