"""
Module 8 Student Enrollment backend - refactored into layers.

This module orchestrates the enrollment system using:
- config: Constants and configuration
- database: SQLite database layer (EnrollmentDatabase)
- service: Business logic layer (EnrollmentService)
- utils: Utility functions

App idea:
    - a student opens a dashboard
    - the dashboard shows enrolled classes
    - the student enters an enrollment key to join another class
    - the database stores courses and enrollment records
    - a JSON snapshot is exported so students can inspect the seeded data

Focus:
    - student enrollment behavior
    - local SQLite database
    - enrollment keys
    - soft unenroll using status = "unenrolled"

Out of scope:
    - Streamlit UI
    - authentication/session state
    - caching
    - export formatting
    - production health checks

Run with:
    python enrollment_starter.py
"""

from config import CURRENT_STUDENT, SNAPSHOT_PATH
from database import EnrollmentDatabase
from service import EnrollmentService
from utils import export_database_snapshot


def main() -> None:
    """Main orchestration function."""
    # Initialize layers
    database = EnrollmentDatabase()
    service = EnrollmentService(database)

    # Set up database
    database.create_tables()
    database.seed_sample_data()

    user_id = CURRENT_STUDENT["user_id"]
    email = CURRENT_STUDENT["email"]

    print("Current student:")
    print(CURRENT_STUDENT)

    print("\nAvailable enrollment keys:")
    print(service.get_available_course_keys())

    print("\nInitial enrolled classes:")
    print(service.get_student_enrollments(user_id))

    print("\nStudent enters key DATA210-SPRING:")
    print(service.enroll_with_key(user_id, email, "DATA210-SPRING"))

    print("\nUpdated enrolled classes:")
    print(service.get_student_enrollments(user_id))

    print("\nStudent summary:")
    print(service.get_student_summary(user_id))

    export_database_snapshot(service.build_snapshot(CURRENT_STUDENT))
    print(f"\nDatabase snapshot written to: {SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
