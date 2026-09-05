from pathlib import Path

from datetime import date
from uuid import uuid4
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi import File, Form, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import AttendanceRecord, School, Student, Teacher
from .schemas import (
    AttendanceCreate,
    AttendanceRead,
    DashboardSummary,
    CaptureVerificationRequest,
    CaptureVerificationResponse,
    SchoolCreate,
    SchoolRead,
    StudentCreate,
    StudentRead,
    StudentSummary,
    TeacherRead,
    SyncRequest,
)

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_origin_regex=r"http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)


def require_api_key(x_api_key: str = Header(default="")) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/", include_in_schema=False)
def frontend() -> FileResponse:
    return FileResponse(Path(__file__).resolve().parents[2] / "frontend" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/schools", response_model=SchoolRead, dependencies=[Depends(require_api_key)])
def create_school(payload: SchoolCreate, db: Session = Depends(get_db)) -> School:
    school = School(**payload.model_dump())
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


@app.get("/api/schools", response_model=list[SchoolRead], dependencies=[Depends(require_api_key)])
def list_schools(db: Session = Depends(get_db)) -> list[School]:
    return list(db.scalars(select(School).order_by(School.name)).all())


@app.get("/api/teachers", response_model=list[TeacherRead], dependencies=[Depends(require_api_key)])
def list_teachers(db: Session = Depends(get_db)) -> list[Teacher]:
    return list(db.scalars(select(Teacher).order_by(Teacher.name)).all())


@app.post(
    "/api/attendance/verify-capture",
    response_model=CaptureVerificationResponse,
    dependencies=[Depends(require_api_key)],
)
def verify_capture(
    payload: CaptureVerificationRequest,
    db: Session = Depends(get_db),
) -> CaptureVerificationResponse:
    teacher = db.get(Teacher, payload.teacher_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    students = list(
        db.scalars(select(Student).where(Student.id.in_(payload.student_ids))).all()
    )
    valid = [student.id for student in students if student.school_id == teacher.school_id]
    valid_set = set(valid)
    rejected = [student_id for student_id in payload.student_ids if student_id not in valid_set]
    return CaptureVerificationResponse(
        valid_student_ids=valid,
        rejected_student_ids=rejected,
        school_id=teacher.school_id,
    )


@app.post(
    "/api/attendance/capture",
    response_model=AttendanceRead,
    dependencies=[Depends(require_api_key)],
)
def capture_attendance(
    teacher_id: int = Form(...),
    student_id: int = Form(...),
    capture: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> AttendanceRecord:
    if not capture.content_type or not capture.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Capture must be an image")
    teacher = db.get(Teacher, teacher_id)
    student = db.get(Student, student_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if teacher.school_id != student.school_id:
        raise HTTPException(
            status_code=403,
            detail="Student is not enrolled in the teacher's school",
        )
    record = AttendanceRecord(
        client_event_id=f"camera-{uuid4()}",
        student_id=student.id,
        attendance_date=date.today(),
        status="present",
        recorded_by=f"teacher:{teacher.id}",
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Attendance already recorded for this student today",
        ) from exc
    db.refresh(record)
    return record


@app.post("/api/students", response_model=StudentRead, dependencies=[Depends(require_api_key)])
def create_student(payload: StudentCreate, db: Session = Depends(get_db)) -> Student:
    if db.get(School, payload.school_id) is None:
        raise HTTPException(status_code=404, detail="School not found")
    student = Student(**payload.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="External student ID already exists") from exc
    db.refresh(student)
    return student


@app.get("/api/students", response_model=list[StudentSummary], dependencies=[Depends(require_api_key)])
def list_students(
    school_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[StudentSummary]:
    today = date.today()
    statement = select(Student)
    if school_id:
        statement = statement.where(Student.school_id == school_id)
    students = list(db.scalars(statement.order_by(Student.name)).all())
    statuses = {
        record.student_id: record.status
        for record in db.scalars(
            select(AttendanceRecord).where(AttendanceRecord.attendance_date == today)
        ).all()
    }
    return [
        StudentSummary.model_validate(student).model_copy(
            update={"attendance_status": statuses.get(student.id)}
        )
        for student in students
    ]


@app.get("/api/dashboard", response_model=DashboardSummary, dependencies=[Depends(require_api_key)])
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    today_records = list(
        db.scalars(
            select(AttendanceRecord).where(AttendanceRecord.attendance_date == date.today())
        ).all()
    )
    counts = {status: sum(record.status == status for record in today_records) for status in
              ("present", "absent", "late", "excused")}
    return DashboardSummary(
        total_schools=db.query(School).count(),
        total_students=db.query(Student).count(),
        present_today=counts["present"],
        absent_today=counts["absent"],
        late_today=counts["late"],
        excused_today=counts["excused"],
    )


@app.post("/api/attendance", response_model=AttendanceRead, dependencies=[Depends(require_api_key)])
def record_attendance(payload: AttendanceCreate, db: Session = Depends(get_db)) -> AttendanceRecord:
    if db.get(Student, payload.student_id) is None:
        raise HTTPException(status_code=404, detail="Student not found")
    record = AttendanceRecord(**payload.model_dump())
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Attendance event already recorded") from exc
    db.refresh(record)
    return record


@app.post("/api/attendance/sync", response_model=list[AttendanceRead], dependencies=[Depends(require_api_key)])
def sync_attendance(payload: SyncRequest, db: Session = Depends(get_db)) -> list[AttendanceRecord]:
    synced: list[AttendanceRecord] = []
    for event in payload.events:
        existing = db.scalar(select(AttendanceRecord).where(AttendanceRecord.client_event_id == event.client_event_id))
        if existing:
            synced.append(existing)
            continue
        if db.get(Student, event.student_id) is None:
            raise HTTPException(status_code=404, detail=f"Student {event.student_id} not found")
        record = AttendanceRecord(**event.model_dump())
        db.add(record)
        synced.append(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Sync contains a duplicate student/day record") from exc
    for record in synced:
        db.refresh(record)
    return synced


@app.get("/api/attendance", response_model=list[AttendanceRead], dependencies=[Depends(require_api_key)])
def list_attendance(
    attendance_date: str | None = Query(default=None),
    school_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AttendanceRecord]:
    statement = select(AttendanceRecord)
    if attendance_date:
        statement = statement.where(AttendanceRecord.attendance_date == attendance_date)
    if school_id:
        statement = statement.join(Student).where(Student.school_id == school_id)
    return list(db.scalars(statement.order_by(AttendanceRecord.attendance_date.desc())).all())
