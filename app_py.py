"""Streamlit UI for the Student Enrollment Manager."""

import streamlit as st
from config import CURRENT_STUDENT, STATUS_ENROLLED, STATUS_UNENROLLED
from database import EnrollmentDatabase
from service import EnrollmentService


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Student Enrollment Manager", layout="wide")


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
def init_session_state() -> None:
    if "student" not in st.session_state:
        st.session_state.student = CURRENT_STUDENT
        st.session_state.role = "student"
        st.session_state.current_page = "dashboard"
        st.session_state.selected_course = None
        st.session_state.search_query = ""
        st.session_state.search_results = []
        st.session_state.enrollment_message = None
        st.session_state.unenroll_message = None
        st.session_state.confirm_unenroll = {
            "active": False,
            "course_id": None,
            "course_name": None,
        }


init_session_state()


# ---------------------------------------------------------------------------
# Role check
# ---------------------------------------------------------------------------
if st.session_state.role != "student":
    st.error("Access denied. This interface is for students only.")
    st.stop()


# ---------------------------------------------------------------------------
# Backend setup (runs once per session)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_service() -> EnrollmentService:
    db = EnrollmentDatabase()
    db.create_tables()
    db.seed_sample_data()
    return EnrollmentService(db)


service = get_service()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def go_to_course(course: dict) -> None:
    st.session_state.selected_course = course
    st.session_state.current_page = "course_detail"
    st.session_state.search_query = ""
    st.session_state.search_results = []


def go_to_dashboard() -> None:
    st.session_state.current_page = "dashboard"
    st.session_state.selected_course = None
    st.session_state.search_query = ""
    st.session_state.search_results = []


def format_date(raw: str) -> str:
    """Return a friendlier date string from a SQLite timestamp."""
    try:
        from datetime import datetime
        return datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%b %d, %Y")
    except Exception:
        return raw


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def show_sidebar() -> None:
    st.sidebar.title("📋 Enrollment Manager")

    if st.sidebar.button("🏠 Home Dashboard", use_container_width=True):
        go_to_dashboard()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("🔍 Search Courses")

    query = st.sidebar.text_input(
        "Search by course name",
        value=st.session_state.search_query,
        placeholder="e.g., Python, Data...",
        label_visibility="collapsed",
    )

    # Update results whenever the query changes
    if query != st.session_state.search_query:
        st.session_state.search_query = query

    if query:
        all_courses = service.get_available_course_keys()
        st.session_state.search_results = [
            c for c in all_courses
            if query.lower() in c["course_name"].lower()
        ]
    else:
        st.session_state.search_results = []

    if query and not st.session_state.search_results:
        st.sidebar.caption("No courses found.")

    for course in st.session_state.search_results:
        label = f"📚 {course['course_id']} – {course['course_name']}"
        if st.sidebar.button(label, key=f"search_{course['course_id']}", use_container_width=True):
            go_to_course(course)
            st.rerun()


# ---------------------------------------------------------------------------
# Page 1: Dashboard
# ---------------------------------------------------------------------------
def show_dashboard() -> None:
    user_id = st.session_state.student["user_id"]
    email = st.session_state.student["email"]
    name = st.session_state.student["name"]

    # Breadcrumb
    st.markdown("📍 **Dashboard** › **My Classes**")

    # Welcome banner
    summary = service.get_student_summary(user_id)
    total = len(service.get_available_course_keys())
    enrolled_count = summary.get(STATUS_ENROLLED, 0)
    st.info(f"👋 Welcome back, **{name}**!  |  📚 Enrolled in **{enrolled_count}** of **{total}** available courses")

    # Pending messages
    if st.session_state.unenroll_message:
        st.success(st.session_state.unenroll_message)
        st.session_state.unenroll_message = None

    if st.session_state.enrollment_message:
        msg = st.session_state.enrollment_message
        if msg.startswith("❌"):
            st.error(msg)
        else:
            st.success(msg)
        st.session_state.enrollment_message = None

    st.divider()

    left_col, right_col = st.columns([2, 1])

    # ---- My Current Classes ------------------------------------------------
    with left_col:
        st.subheader("📚 My Current Classes")

        enrolled = service.get_student_enrollments(user_id)

        if not enrolled:
            st.info("🚀 No classes yet! Search for a course or use an enrollment key to get started.")
        else:
            sort_by = st.selectbox(
                "Sort by:",
                ["Course ID", "Course Name", "Enrollment Date"],
                key="sort_select",
            )
            if sort_by == "Course ID":
                enrolled = sorted(enrolled, key=lambda c: c["course_id"])
            elif sort_by == "Course Name":
                enrolled = sorted(enrolled, key=lambda c: c["course_name"])
            else:
                enrolled = sorted(enrolled, key=lambda c: c["enrolled_at"])

            # Render cards in rows of 3
            cols_per_row = 3
            for i in range(0, len(enrolled), cols_per_row):
                cols = st.columns(cols_per_row)
                for col, course in zip(cols, enrolled[i:i + cols_per_row]):
                    cid = course["course_id"]
                    with col:
                        with st.container():
                            st.markdown(f"### 📚 {cid}")
                            st.markdown(f"**{course['course_name']}**")
                            st.markdown(f"👤 {course['instructor']}")
                            st.markdown(f"✅ Enrolled  |  Since: {format_date(course['enrolled_at'])}")

                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.button("Go to Class", key=f"goto_{cid}"):
                                    go_to_course(course)
                                    st.rerun()
                            with btn_col2:
                                if st.button("Unenroll", key=f"unenroll_{cid}"):
                                    st.session_state.confirm_unenroll = {
                                        "active": True,
                                        "course_id": cid,
                                        "course_name": course["course_name"],
                                    }
                                    st.rerun()

    # ---- Enroll in a new class ---------------------------------------------
    with right_col:
        st.subheader("➕ Enroll in a New Class")
        st.caption("📌 Enrollment key examples: `MISY350-SPRING`, `DATA210-SPRING`, `WEB220-SPRING`")

        key_input = st.text_input(
            "Enter Enrollment Key",
            placeholder="e.g., MISY350-SPRING",
            key="enroll_key_input",
        )

        if st.button("Enroll", type="primary"):
            if not key_input.strip():
                st.error("❌ Please enter an enrollment key.")
            else:
                result = service.enroll_with_key(user_id, email, key_input.strip())
                if result:
                    course_name = service.get_course_by_key(key_input.strip())
                    name_str = course_name["course_name"] if course_name else key_input
                    st.session_state.enrollment_message = (
                        f"✨ Successfully enrolled in **{name_str}**! 🎉"
                    )
                else:
                    st.session_state.enrollment_message = (
                        "❌ Enrollment failed. Please check the enrollment key and try again."
                    )
                st.rerun()

    # ---- Unenroll confirmation dialog --------------------------------------
    cfg = st.session_state.confirm_unenroll
    if cfg["active"]:
        st.divider()
        st.warning(
            f"⚠️ **Confirm Unenrollment**\n\n"
            f"Are you sure you want to unenroll from "
            f"**{cfg['course_id']} – {cfg['course_name']}**?\n\n"
            f"This will mark the course as unenrolled but keep it in your history."
        )
        cancel_col, confirm_col = st.columns([1, 1])
        with cancel_col:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_unenroll = {
                    "active": False, "course_id": None, "course_name": None
                }
                st.rerun()
        with confirm_col:
            if st.button("✅ Confirm Unenroll", use_container_width=True, type="primary"):
                service.soft_unenroll_student(user_id, cfg["course_id"])
                st.session_state.unenroll_message = (
                    f"✨ You have been unenrolled from **{cfg['course_name']}**."
                )
                st.session_state.confirm_unenroll = {
                    "active": False, "course_id": None, "course_name": None
                }
                st.rerun()


# ---------------------------------------------------------------------------
# Page 2: Course Detail
# ---------------------------------------------------------------------------
def show_course_detail() -> None:
    course = st.session_state.selected_course

    # Guard: no course selected
    if not course:
        st.warning("🔍 No course information found. Please return to the dashboard.")
        if st.button("← Back to Dashboard"):
            go_to_dashboard()
            st.rerun()
        return

    user_id = st.session_state.student["user_id"]
    email = st.session_state.student["email"]
    cid = course["course_id"]

    # Breadcrumb
    st.markdown(f"📍 **Dashboard** › **My Classes** › **{course['course_name']}**")

    if st.button("← Back to Dashboard"):
        go_to_dashboard()
        st.rerun()

    st.title(f"📚 {course['course_name']}")

    # Course info
    info_col, status_col = st.columns([2, 1])
    with info_col:
        st.markdown(f"**Course ID:** {cid}")
        st.markdown(f"**Instructor:** 👤 {course['instructor']}")
        st.markdown(f"**Enrollment Key:** `{course['enrollment_key']}`")

    # Check live enrollment status from the service layer
    record = service.get_student_course_record(user_id, cid)
    is_enrolled = record is not None and record.get("status") == STATUS_ENROLLED
    was_enrolled = record is not None and record.get("status") == STATUS_UNENROLLED

    with status_col:
        if is_enrolled:
            st.markdown(f"**Status:** ✅ Enrolled")
            st.markdown(f"**Since:** {format_date(record['enrolled_at'])}")
        elif was_enrolled:
            st.markdown(f"**Status:** ⏱️ Previously Unenrolled")
        else:
            st.markdown(f"**Status:** ⭕ Not Yet Enrolled")

    st.divider()

    # Enrollment action
    if is_enrolled:
        st.success("✅ You are currently enrolled in this course.")
    else:
        hint = " (re-enroll)" if was_enrolled else ""
        if st.button(f"Enroll in This Course{hint}", type="primary"):
            result = service.enroll_with_key(user_id, email, course["enrollment_key"])
            if result:
                st.success(f"✨ Successfully enrolled in **{course['course_name']}**! 🎉")
                st.rerun()
            else:
                st.error("❌ Enrollment failed. Please try again.")


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------
with st.sidebar:
    show_sidebar()

if st.session_state.current_page == "dashboard":
    show_dashboard()
elif st.session_state.current_page == "course_detail":
    show_course_detail()
