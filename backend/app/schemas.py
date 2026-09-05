from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SchoolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    district: str
    block: str


class SchoolRead(SchoolCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class TeacherRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    external_id: str
    name: str
    phone: str
    school_id: int
    role: str


class StudentCreate(BaseModel):
    external_id: str
    name: str
    school_id: int


class StudentRead(StudentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class StudentSummary(StudentRead):
    attendance_status: str | None = None


class AttendanceCreate(BaseModel):
    client_event_id: str = Field(min_length=1, max_length=100)
    student_id: int
    attendance_date: date
    status: str = Field(pattern="^(present|absent|late|excused)$")
    absence_reason: str | None = None
    recorded_by: str = "system"


class AttendanceRead(AttendanceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    correction_status: str
    created_at: datetime


class DashboardSummary(BaseModel):
    total_schools: int
    total_students: int
    present_today: int
    absent_today: int
    late_today: int
    excused_today: int


class CaptureVerificationRequest(BaseModel):
    teacher_id: int
    student_ids: list[int] = Field(max_length=500)


class CaptureVerificationResponse(BaseModel):
    valid_student_ids: list[int]
    rejected_student_ids: list[int]
    school_id: int


class SyncRequest(BaseModel):
    events: list[AttendanceCreate] = Field(max_length=500)
