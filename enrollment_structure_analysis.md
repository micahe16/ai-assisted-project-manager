Looking at your analysis, I see some productive tensions between what you marked and what you noted in Design. Let me reflect what I'm seeing:

Key Differences Between Us
Where I differed:

You marked most query functions (get_course_by_key, get_student_enrollments, get_available_course_keys) as Database, but noted "Design: Service Class". I marked them as Mixed because I saw the service logic (filtering by status, validation) already embedded in the query functions.
You marked SQLite SELECT/INSERT/UPDATE as Service, which is backwards from convention. I think you meant these operations should be isolated so they can be called by service functions—not that raw SQL is service logic.
You correctly caught that enroll_with_key and get_student_summary are Mixed (Cross Layer), while I lumped them together without the nuance that they need splitting.
What I Agree With Strongly
Your state/data reflection is excellent and reveals the real design problem:

"Requires Passing State" functions (enroll_with_key, export_database_snapshot, main) are doing orchestration work—they're calling multiple things and stitching results.
"Self-Contained" functions are pure fetches (no business decision).
"Reads Global State" (seed_sample_data, soft_unenroll_student) are tightly coupled to constants.
This is more precise than "Database vs Service" because it exposes why the layers are tangled.

Risks & Structure Problems
The Design-vs-Mark Mismatch: You marked query functions as Database but noted they belong in Service Class. This suggests the code structure disagrees with what should happen. That's the core problem—you're seeing where things should go but the current code puts them where they're convenient.

Validation & Business Rules Are Scattered:

get_course_by_key() validates the key exists (business rule: "key must match a course")
get_student_enrollments() filters by status (business rule: "enrolled means status='enrolled'")
enroll_with_key() validates email format (business rule: "email must be valid")
These should live in one service layer, not spread across database functions.

"Mixed (Same Layer)" vs "Mixed (Cross Layer)": Your distinction is crucial:

seed_sample_data is Mixed within the same layer (reads global constants, does database work)
get_student_summary, export_database_snapshot, main are Mixed across layers (fetch data, then transform/format it)
The cross-layer ones are the real design risk because they violate separation of concerns.

State Passing vs Embedding: Notice:

get_student_summary() calls get_student_enrollment_history() internally—it can't be tested in isolation
export_database_snapshot() calls get_available_course_keys() and get_all_enrollment_records()—same problem
Compare to main(), which receives state and passes it around—it's more testable (even though it's procedural)
The SQLite Operations Problem: You marked raw SQL as Service. I think what you're sensing is that the SQL should be wrapped in database methods that service functions call. Right now they're mixed into get_* functions. You don't have a true database abstraction—just functions that happen to contain SQL.

What This Means for Layer Design
Your current code has three logical concerns mixed together:

Database I/O (SQLite connection, SQL execution)
Data Fetching (queries with WHERE clauses)
Business Logic (filtering by status, validating keys, counting, formatting)
A cleaner layer design would separate these:

Database layer: raw connection, raw queries (just execute SQL, return rows)
Service layer: uses database layer to fetch, applies business rules, returns domain objects
Presentation layer (main/UI): calls service layer, orchestrates flow
The risk right now: if you need to add "students can only enroll in 3 courses max," where does that go? Into every function that calls enroll? Or into one service method? The mixed layer design makes it unclear.

Your "Needs Splitting" Functions
get_student_summary and export_database_snapshot are your canaries. They correctly show what needs splitting:

get_student_summary: should receive data (from DB layer), count it (service), return counts
export_database_snapshot: should receive data collections (from DB layer), format them (presentation), write them (I/O)
Right now they do fetch + transform, which means they can't be tested separately from the database.

Does this frame help clarify the structural tension you were feeling?