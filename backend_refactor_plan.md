Refactor Plan
1. Define the target layers
Database layer
Keep it focused on SQLite: connection management, raw SQL queries, inserts, updates, and row-to-dict conversion.
No business rules here beyond basic query parameters.
Service layer
Keep business meaning here: enrollment-key validation, enrollment status rules, dashboard semantics, summary counting, and student actions.
Use database methods to fetch or persist data.
Orchestration/presentation
main() or UI entrypoints should only wire together service + database, not contain business logic or raw SQL.
2. Map existing functions into the layers
Database layer methods:
connect()
create_tables()
seed_sample_data()
get_available_course_keys()
get_course_by_key()
get_student_enrollment_history()
get_student_course_record()
get_all_enrollment_records()
soft_unenroll_student() (update-only)
rows_to_dicts()
Service layer methods:
get_student_enrollments() should call DB history and filter status == enrolled
enroll_with_key() should validate input, resolve key via DB, and then persist via DB method
get_student_summary() should accept enrollment records and count statuses
export_database_snapshot() should assemble snapshot data from DB/service results and write JSON
main() becomes orchestration only
3. Move business rules out of SQL methods
get_course_by_key() should not be considered a service if it does more than simple lookup; instead, have a DB method like find_course_by_enrollment_key() and a service method like validate_enrollment_key().
get_student_enrollments() should be service logic built from a raw DB fetch plus business rule filtering.
get_available_course_keys() belongs to DB if it just returns rows; service can decide what “available” means.
get_student_summary() should not call the DB directly; it should compute counts over records passed in.
4. Introduce object-oriented structure
Consider:
EnrollmentDatabase class for SQLite access
EnrollmentService class for business rules
Example responsibilities:
EnrollmentDatabase:
connect(), create_tables(), seed_sample_data()
fetch_courses(), fetch_course_by_key()
fetch_enrollments_for_student(), fetch_enrollment_record()
save_enrollment(), update_enrollment_status()
EnrollmentService:
enroll_student_with_key(user_id, email, enrollment_key)
get_current_enrollments(user_id)
get_enrollment_summary(user_id)
soft_unenroll_student(user_id, course_id)
build_snapshot()
5. Clean up state and globals
Keep constants like DB_PATH, SNAPSHOT_PATH, statuses, and sample data in config or DB setup.
Pass user_id, email, and course_id explicitly into service methods rather than relying on globals.
If CURRENT_STUDENT is only for demo, treat it as example input rather than hard-coded state.
6. Preserve SQLite focus and make the service layer testable
Database methods should return plain data structures (dict, list[dict]) from rows.
Service methods should operate on those structures and not execute SQL directly.
This makes service logic easier to test separately from the database.
What to do next
Approve this plan.
Then use the implementation prompt below to actually refactor.
Implementation prompt to use after approval
Refactor enrollment_starter.py into a layered backend design with two main classes:

EnrollmentDatabase for SQLite access and raw row queries/updates only.
EnrollmentService for enrollment-key validation, dashboard semantics, summary counting, and student actions.
Keep business rules out of raw SQL methods. Move status filtering and validation into service methods. Keep main() as orchestration only. Preserve current behavior and keep the database layer focused on SQLite row queries and updates.