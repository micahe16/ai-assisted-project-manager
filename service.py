"""Service layer for enrollment business logic."""

from __future__ import annotations

from typing import Any, Optional

from config import STATUS_ENROLLED, STATUS_UNENROLLED
from database import EnrollmentDatabase


class EnrollmentService:
    """Handles enrollment business rules and orchestration."""

    def __init__(self, database: EnrollmentDatabase) -> None:
        self.database = database

    def is_valid_email(self, email: str) -> bool:
        """Check if an email is valid (basic validation)."""
        return "@" in email and email.strip() == email

    def get_available_course_keys(self) -> list[dict[str, Any]]:
        """Get all available courses."""
        return self.database.get_available_course_keys()

    def get_course_by_key(self, enrollment_key: str) -> Optional[dict[str, Any]]:
        """Validate and retrieve a course by enrollment key."""
        if not enrollment_key:
            return None

        normalized_key = enrollment_key.strip().upper()
        return self.database.find_course_by_key(normalized_key)

    def get_student_enrollment_history(self, user_id: str) -> list[dict[str, Any]]:
        """Get complete enrollment history (all records) for a student."""
        if not user_id:
            return []

        return self.database.get_student_enrollment_history(user_id)

    def get_student_enrollments(self, user_id: str) -> list[dict[str, Any]]:
        """Get currently enrolled courses for a student (status='enrolled')."""
        return [
            record
            for record in self.get_student_enrollment_history(user_id)
            if record["status"] == STATUS_ENROLLED
        ]

    def get_student_course_record(
        self,
        user_id: str,
        course_id: str,
    ) -> Optional[dict[str, Any]]:
        """Get a specific enrollment record for a student and course."""
        if not user_id or not course_id:
            return None

        return self.database.get_student_course_record(user_id, course_id)

    def enroll_with_key(
        self,
        user_id: str,
        email: str,
        enrollment_key: str,
    ) -> Optional[dict[str, Any]]:
        """Enroll a student in a course using an enrollment key."""
        if not user_id or not email or not self.is_valid_email(email) or not enrollment_key:
            return None

        course = self.get_course_by_key(enrollment_key)
        if not course:
            return None

        self.database.save_enrollment(
            user_id=user_id,
            email=email,
            course_id=course["course_id"],
            status=STATUS_ENROLLED,
        )

        return self.get_student_course_record(user_id, course["course_id"])

    def soft_unenroll_student(self, user_id: str, course_id: str) -> bool:
        """Unenroll a student from a course (marks status as 'unenrolled')."""
        if not user_id or not course_id:
            return False

        return self.database.update_enrollment_status(
            user_id=user_id,
            course_id=course_id,
            status=STATUS_UNENROLLED,
        )

    def get_student_summary(self, user_id: str) -> dict[str, int]:
        """Get enrollment summary counts for a student."""
        summary = {
            "total_records": 0,
            STATUS_ENROLLED: 0,
            STATUS_UNENROLLED: 0,
        }

        for record in self.get_student_enrollment_history(user_id):
            summary["total_records"] += 1
            status = record["status"]
            if status in summary:
                summary[status] += 1

        return summary

    def build_snapshot(self, current_student: dict[str, Any]) -> dict[str, Any]:
        """Build a complete snapshot of the current enrollment state."""
        return {
            "current_student": current_student,
            "available_course_keys": self.get_available_course_keys(),
            "enrollment_table": self.database.get_all_enrollment_records(),
        }
