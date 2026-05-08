# Streamlit UI Plan: Student Enrollment Manager (Revised - Final)

## Overview
A two-page Streamlit application for students to view their enrolled classes, search for courses by name, enroll in courses, and manage their enrollments. The student "Marcie" is pre-logged in (no authentication system).

**Key Layout**: Persistent sidebar with home button + search bar on left; main content area displays either dashboard or course detail pages. Search filters all available courses by course name in real-time. Clicking any course (enrolled or search result) navigates to course detail page, which shows enrollment status and options.

---

## Architecture & Session State Management

### Session State Structure
Store the following in `st.session_state`:
```python
st.session_state.student = {
    "user_id": "u100",
    "name": "Marcie",
    "email": "marcie.example@edu"
}
st.session_state.role = "student"  # Role check (always "student" for this UI)
st.session_state.current_page = "dashboard"  # "dashboard" or "course_detail"
st.session_state.selected_course = None  # dict with course info when viewing course detail
st.session_state.search_query = ""  # Current search text in sidebar
st.session_state.search_results = []  # List of courses matching search query
st.session_state.enrollment_message = None  # Success/failure message from enrollment attempt
st.session_state.unenroll_message = None  # Soft unenroll confirmation message
st.session_state.confirm_unenroll = {  # Confirmation dialog state
    "active": False,
    "course_id": None,
    "course_name": None
}
```

### Backend Layer Dependencies
- **config.py**: `CURRENT_STUDENT`, `STATUS_ENROLLED`, `STATUS_UNENROLLED`
- **database.py**: `EnrollmentDatabase` class (for setup/connection)
- **service.py**: `EnrollmentService` class with these key methods:
  - `get_student_enrollments(user_id)` - Get currently enrolled classes
  - `get_student_enrollment_history(user_id)` - Get all records (for reference)
  - `get_available_course_keys()` - Get all courses in system
  - `get_course_by_key(enrollment_key)` - Lookup course by key
  - `enroll_with_key(user_id, email, enrollment_key)` - Enroll student
  - `soft_unenroll_student(user_id, course_id)` - Mark as unenrolled (keep DB record)
  - `get_student_summary(user_id)` - Get enrollment counts
  - `build_snapshot(current_student)` - For testing/export

---

## Page 1: Home Dashboard

### Layout
```
┌────────────────────────────────────────┐
│ 👋 Welcome back, Marcie!               │
│ 📚 You're enrolled in 2 of 3 courses   │
├────────────────────────────────────────┤
│                                        │
│ 📚 MY CURRENT CLASSES                  │
│                                        │
│ ┌─────────────────────┐                │
│ │ MISY350             │                │
│ │ Python for BA       │ ← clickable    │
│ │ Dr. Rivera          │                │
│ │ ✅ Enrolled         │                │
│ │ Since: Mar 15, 2024 │                │
│ │ [Go to Class]       │                │
│ │ [Unenroll]          │                │
│ └─────────────────────┘                │
│                                        │
│ ┌─────────────────────┐                │
│ │ DATA210             │                │
│ │ Data Storytelling   │                │
│ │ Prof. Morgan        │                │
│ │ ✅ Enrolled         │                │
│ │ Since: Mar 15, 2024 │                │
│ │ [Go to Class]       │                │
│ │ [Unenroll]          │                │
│ └─────────────────────┘                │
│                                        │
│ [Empty state if no classes]            │
│ 🚀 No classes yet! Search for a       │
│    course or use an enrollment key.   │
├────────────────────────────────────────┤
│ ➕ ENROLL IN A NEW CLASS                │
│                                        │
│ Enter Enrollment Key:                  │
│ [MISY350-SPRING.....................]  │
│ [Enroll Button]                        │
│                                        │
│ [Message - success/failure]            │
└────────────────────────────────────────┘
```

### Components

#### Welcome Banner
- Display at top: 
  - `f"👋 Welcome back, {student_name}!"`
  - `f"📚 You're enrolled in {enrolled_count} of {total_available_count} available courses"`
- Use `st.info()` or styled container

#### My Current Classes Section
- **Header**: `st.subheader("📚 MY CURRENT CLASSES")`
- **Fetch enrolled classes**: Call `service.get_student_enrollments(user_id)`
- **Display as cards** in a responsive grid (columns):
  - Each class card shows:
    - Course ID (large, bold)
    - Course Name
    - Instructor
    - Status badge: `✅ Enrolled` (green)
    - Enrollment date: `"Since: Mar 15, 2024"`
    - **[Go to Class]** button:
      - On click: Sets `st.session_state.selected_course = course_dict`, sets `current_page = "course_detail"`, triggers rerun
    - **[Unenroll]** button:
      - On click: Shows confirmation dialog (see below)

##### Unenroll Confirmation Dialog
- When user clicks [Unenroll]:
  - Display warning modal:
    ```
    ⚠️ Confirm Unenrollment
    Are you sure you want to unenroll from "MISY350 - Python for Business Analytics"?
    This will mark the course as unenrolled but keep it in your history.
    [Cancel]  [Confirm Unenroll]
    ```
  - Set `st.session_state.confirm_unenroll = {"active": True, "course_id": course_id, "course_name": course_name}`
  - **[Cancel]**: Clear confirmation, no action
  - **[Confirm Unenroll]**: 
    - Call `service.soft_unenroll_student(user_id, course_id)`
    - Set `st.session_state.unenroll_message = f"✨ You have been unenrolled from {course_name}."`
    - Clear confirmation state
    - Refresh dashboard; class disappears from cards

##### Empty State
- If no classes enrolled:
  - Display: `st.info("🚀 No classes yet! Search for a course or use an enrollment key to get started.")`

#### Enroll in New Class Section
- **Header**: `st.subheader("➕ ENROLL IN A NEW CLASS")`
- **Enrollment Key Input**:
  - `enrollment_key = st.text_input("Enter Enrollment Key", placeholder="e.g., MISY350-SPRING")`
- **Enroll Button**:
  - `st.button("Enroll")`
  - On click:
    - Call `service.enroll_with_key(user_id, email, enrollment_key)`
    - If successful:
      - Display: `st.success(f"✨ Successfully enrolled in [Course Name]! 🎉")`
      - Clear enrollment_key input
      - Refresh "My Current Classes" section
    - If failed:
      - Display: `st.error("❌ Enrollment failed. Please check the enrollment key.")`

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  SIDEBAR (Left)              │ MAIN CONTENT (Right)        │
├────────────────────────────────────────────────────────────┤
│ st.radio("Select View"):     │ st.title("My Classes")      │
│  ○ View My Classes           │ Welcome back, Marcie!       │
│  ○ Find & Enroll             │                             │
│                              │ [IF View My Classes]        │
│ [IF "View My Classes"]       │ Class Details:              │
│ st.radio("Select Class"):    │ - Course Name               │
│  ○ Class 1 (MISY350)         │ - Instructor                │
│  ○ Class 2 (DATA210)         │ - Enrollment Key            │
│  ○ Class 3 (WEB220)          │ - Status: Enrolled          │
│                              │ - Enrolled At: [Date]       │
│                              │                             │
│                              │ [Go to Class] [Unenroll]    │
│                              │                             │
│ [IF "Find & Enroll"]         │ [IF "Find & Enroll"]        │
│ Text Input:                  │ Search Results:             │
│ Enter enrollment key...      │ - Course Info               │
│ [Search Button]              │ - Instructor                │
│                              │ - [Enroll Button]           │
│                              │ - Status: (if applicable)   │
│                              │                             │
│                              │ [Message]                   │
└────────────────────────────────────────────────────────────┘
```

### Sidebar Components

#### Home Dashboard Button
- `st.button("🏠 Home Dashboard")`
- On click:
  - Sets `st.session_state.current_page = "dashboard"`
  - Clears `st.session_state.selected_course`
  - Clears search query: `st.session_state.search_query = ""`
  - Triggers rerun to display dashboard page

#### Search Bar
- `search_query = st.text_input("🔍 Search Courses", placeholder="e.g., Python, Data...")`
- On input change (every keystroke):
  - Update `st.session_state.search_query = search_query`
  - If search_query is not empty:
    - Call `service.get_available_course_keys()` to get all courses
    - Filter courses by matching search_query against `course_name` (case-insensitive substring match)
    - Store filtered results: `st.session_state.search_results = filtered_courses`
  - If search_query is empty:
    - Clear search_results: `st.session_state.search_results = []`

#### Search Results Display
- Display clickable results below search input:
  - For each course in `st.session_state.search_results`:
    - Create clickable item using `st.button()` or custom container: `f"{course['course_id']} - {course['course_name']}"`
    - On click:
      - Set `st.session_state.selected_course = course` (include all course fields)
      - Set `st.session_state.current_page = "course_detail"`
      - Clear search_query: `st.session_state.search_query = ""`
      - Trigger rerun to navigate to course detail page
  - If no results found and search_query is not empty:
    - Display: "No courses found"
  - If search_query is empty:
    - Display nothing (clean sidebar)

### Main Content Area (Dashboard Mode)

#### Breadcrumb Navigation
- Display at top: `"Dashboard > My Classes"` or `"Dashboard > Find & Enroll"`
- Use simple text or clickable links to navigate between modes
- Format: `st.markdown("📍 **Dashboard** > **My Classes**")` or similar

#### Welcome Banner (Mode 1 & 2)
- Display student greeting with emoji: `f"👋 Welcome back, {student_name}!"`
- Show enrollment stats: `f"📚 You're enrolled in {enrolled_count} of {total_available_count} available courses"`
- Use `st.info()` or custom styled container

#### Mode 1: "View My Classes" - Class Cards Display

##### Sorting Control
- Add sort options above class cards: `st.selectbox("Sort by:", ["Course ID", "Course Name", "Enrollment Date"])`
- Sort enrolled_classes list based on selection:
  - "Course ID": sort by `course_id`
  - "Course Name": sort by `course_name`
  - "Enrollment Date": sort by `enrolled_at`

##### Empty State
- **If no classes enrolled:**
  - `st.info("🚀 No classes yet! Enter an enrollment key in Find & Enroll to get started.")`
  - Display empty state message with icon

##### Class Cards
- **Layout**: Display as columns or cards in a grid (e.g., 2-3 cards per row)
- **Use `st.container()` with `st.columns()` to create card effect:**
  - Card for each enrolled class:
    ```
    ┌──────────────────────┐
    │ 📚 MISY350           │
    │ Python for...        │
    │ Dr. Rivera           │
    │ ✅ Enrolled          │
    │ Since: Mar 15, 2024  │
    │                      │
    │ [Go to Class]        │
    │ [Unenroll]           │
    └──────────────────────┘
    ```
  
- **Card Content for Each Class:**
  - Course emoji + Course ID (large, bold)
  - Course Name (subtitle)
  - Instructor: `Dr. Rivera`
  - Status badge: `✅ Enrolled` (green) | `⏱️ Unenrolled` (gray)
  - Enrollment date: `"Since: Mar 15, 2024"`
  
- **Card Interactions:**
  - Click card to select it (highlight/border changes)
  - **[Go to Class]** button:
    - Sets `st.session_state.selected_class = selected_course_dict`
    - Changes `st.session_state.current_page = "class_detail"`
    - Triggers rerun
  - **[Unenroll]** button:
    - Shows confirmation dialog (see below)

##### Unenroll Confirmation Dialog
- When user clicks [Unenroll] button:
  - Display modal/confirmation: 
    ```
    ⚠️ Confirm Unenrollment
    Are you sure you want to unenroll from "MISY350 - Python for Business Analytics"?
    This will mark the course as unenrolled but keep it in your history.
    [Cancel]  [Confirm Unenroll]
    ```
  - Use `st.warning()` + `st.columns([1,1])` for buttons
  - **[Cancel]**: Clear confirmation state, no action
  - **[Confirm Unenroll]**: 
    - Call `service.soft_unenroll_student(user_id, course_id)`
    - Set `st.session_state.unenroll_message = f"✨ You have been unenrolled from {course_name}."`
    - Refresh dashboard; class disappears from cards (status now = "unenrolled")

#### Mode 2: "Find & Enroll" - Search Results Display

##### Search Input & Button
- **Search Input**: 
  - `enrollment_key = st.text_input("Enter enrollment key", placeholder="e.g., MISY350-SPRING")`
  - Show hint: `"📌 Enrollment key example: MISY350-SPRING"`
- **Search Button**: 
  - `st.button("🔍 Search")`
  - On click: Call `service.get_course_by_key(enrollment_key)`
  - Stores result in session state: `st.session_state.search_result = course` (or None if not found)

##### Search Results Display
- **If search_result exists (course found):**
  - Display as a card or highlighted container:
    ```
    ┌────────────────────────────┐
    │ 📚 DATA210                 │
    │ Data Storytelling          │
    │ Prof. Morgan               │
    │ 🔑 Key: DATA210-SPRING     │
    │                            │
    │ Status: Not Yet Enrolled   │
    │ [Enroll Now]               │
    └────────────────────────────┘
    ```
  - Show status indicator:
    - If already enrolled: `✅ Already Enrolled`
    - If unenrolled before: `⏱️ Previously Unenrolled (can re-enroll)`
    - If not enrolled: `⭕ Not Yet Enrolled`
  - **[Enroll Now]** button:
    - Calls `service.enroll_with_key(user_id, email, enrollment_key)`
    - If successful:
      - Display success animation: `st.success(f"✨ Successfully enrolled in {course_name}! 🎉")`
      - Clear search input
      - Show option to "Go to Class" or "Search Another"
      - Auto-switch to "View My Classes" mode to show updated class list
    - If failed:
      - Display error: `st.error("❌ Enrollment failed. Please check the enrollment key.")`

- **If search_result is None (course not found):**
  - Display warning: `st.warning("🔍 No course found with that enrollment key. Please check and try again.")`

- **If no search has been performed yet:**
  - Display placeholder: `st.info("🔍 Enter an enrollment key above and click Search to find courses.")`

#### Messages
- Display any pending `st.session_state.enrollment_message` (success with ✨ emoji)
- Display any pending `st.session_state.unenroll_message` (info with confirmation)
- Use `st.success()` with emoji for enrollment success
- Use `st.error()` with emoji for enrollment failure
- Use `st.warning()` for confirmations/alerts
- Use `st.info()` for informational messages
- Clear message after display (or persist for one rerun)

---

## Page 2: Class Detail

### Triggered By
- User clicks **[Go to Class]** button from dashboard class card
- Successfully enrolls in a class and auto-navigates (optional)
- User searches for a class by enrollment key (optional future feature)

### Layout
```
┌─────────────────────────────────────────────────┐
│ 📍 Dashboard > My Classes > [Course Name]       │
├─────────────────────────────────────────────────┤
│ [← Back to Dashboard]                           │
│                                                 │
│ st.title("Course Name Here")                    │
│                                                 │
│ Course ID: MISY350                              │
│ Instructor: Dr. Rivera                          │
│ Enrollment Key: MISY350-SPRING                  │
│ Status: ✅ Enrolled                             │
│ Enrolled At: [Date]                             │
│                                                 │
│ [Future: class content here]                    │
└─────────────────────────────────────────────────┘
```

### Components

#### Breadcrumb Navigation
- Display at top: `"📍 Dashboard > My Classes > [Course Name]"`
- Use `st.markdown()` for breadcrumb styling
- Clickable or informational (informational is fine for now)

#### Back Button
- `st.button("← Back to Dashboard")`
- Clears `st.session_state.selected_class`
- Sets `st.session_state.current_page = "dashboard"`
- Triggers rerun

#### Class Header
- `st.title()` with course name from `st.session_state.selected_class`
- Display large, prominent course title with emoji: `f"📚 {selected_class['course_name']}"`

#### Class Information
Display all course details:
- **Course ID**: `selected_class["course_id"]`
- **Course Name**: Already in title
- **Instructor**: `selected_class["instructor"]` with icon
- **Enrollment Key**: `selected_class["enrollment_key"]`
- **Your Enrollment Status**: `selected_class["status"]` (with color badge: ✅ Enrolled = green, ⏱️ Unenrolled = gray)
- **Enrolled At**: `selected_class["enrolled_at"]` formatted nicely

#### No Course Warning
- If `st.session_state.selected_class` is None or course lookup fails:
  - `st.warning("🔍 No course information found. Please return to the dashboard.")`
  - Show back button

#### Future Content
- Placeholder for course materials, assignments, discussion boards, etc.

---

## Data Flow & Service Layer Integration

### Search Flow (Sidebar)
1. User types in search bar
2. UI updates `st.session_state.search_query`
3. UI calls `service.get_available_course_keys()` to get all courses
4. UI filters courses by substring match on `course_name` (case-insensitive)
5. Store filtered results in `st.session_state.search_results`
6. Display filtered courses as clickable buttons
7. User clicks a search result:
   - Store course: `st.session_state.selected_course = course`
   - Navigate: `st.session_state.current_page = "course_detail"`
   - Clear search: `st.session_state.search_query = ""`
   - Rerun to display course detail page

### Enrollment Flow (from Enrollment Key on Dashboard)
1. User enters enrollment key on dashboard "Enroll in New Class" section
2. UI calls `service.enroll_with_key(user_id, email, enrollment_key)`
3. Service validates, checks key, inserts record
4. Returns enrollment record or None
5. UI displays success/failure message
6. If successful, refresh "My Current Classes" section
7. Clear enrollment key input

### Enrollment Flow (from Course Detail Page)
1. User clicks [Enroll in This Course] on course detail page
2. UI calls `service.enroll_with_key(user_id, email, selected_course["enrollment_key"])`
3. Service validates, checks key, inserts record
4. Returns enrollment record or None
5. UI displays success/failure message
6. If successful, update course status on page to show "Enrolled"

### Unenrollment Flow (Soft Delete)
1. User clicks [Unenroll] on class card
2. UI shows confirmation dialog
3. User confirms
4. UI calls `service.soft_unenroll_student(user_id, course_id)`
5. Service updates status to "unenrolled"
6. UI stores message: `st.session_state.unenroll_message`
7. Dashboard refreshes; unenrolled class disappears from cards

### Course Detail Navigation
1. User clicks [Go to Class] from card OR clicks search result
2. UI stores course: `st.session_state.selected_course = course_dict`
3. Sets `st.session_state.current_page = "course_detail"`
4. Rerun; displays course detail page
5. UI checks if user is enrolled (using `service.get_student_course_record()` or enrollment list)
6. Displays appropriate status and buttons

---

## Session 1 Reference: Files & Methods

### Files Created (from Session 1)
- **config.py**: Constants (CURRENT_STUDENT, STATUS_ENROLLED, STATUS_UNENROLLED, DB_PATH, SNAPSHOT_PATH)
- **database.py**: EnrollmentDatabase class (SQLite operations)
- **service.py**: EnrollmentService class (business logic)
- **utils.py**: Helper functions (export_database_snapshot)
- **main.py**: Demo/testing orchestration

### EnrollmentService Methods Used in UI
```python
service = EnrollmentService(database)

# Get enrolled classes
enrolled = service.get_student_enrollments(user_id)

# Get all available courses
courses = service.get_available_course_keys()

# Check if enrolled in specific course
record = service.get_student_course_record(user_id, course_id)

# Enroll in course
result = service.enroll_with_key(user_id, email, enrollment_key)

# Unenroll from course (soft delete)
success = service.soft_unenroll_student(user_id, course_id)

# Get summary counts
summary = service.get_student_summary(user_id)
```

---

## UI File Structure (Recommended)

### File: `streamlit_app.py` or `app.py`
```python
import streamlit as st
from config import CURRENT_STUDENT, STATUS_ENROLLED, STATUS_UNENROLLED
from database import EnrollmentDatabase
from service import EnrollmentService

# Page config
st.set_page_config(page_title="Student Enrollment Manager", layout="wide")

# Initialize session state
def init_session_state():
    if "student" not in st.session_state:
        st.session_state.student = CURRENT_STUDENT
        st.session_state.role = "student"
        st.session_state.current_page = "dashboard"
        st.session_state.selected_course = None
        st.session_state.search_query = ""
        st.session_state.search_results = []
        st.session_state.enrollment_message = None
        st.session_state.unenroll_message = None
        st.session_state.confirm_unenroll = {"active": False, "course_id": None, "course_name": None}

init_session_state()

# Initialize backend
database = EnrollmentDatabase()
database.create_tables()
database.seed_sample_data()
service = EnrollmentService(database)

# Main layout with sidebar
with st.sidebar:
    show_sidebar(service)

# Main content based on current page
if st.session_state.current_page == "dashboard":
    show_dashboard(service)
elif st.session_state.current_page == "course_detail":
    show_course_detail(service)

# Helper functions:
def show_sidebar(service):
    # Home button
    # Search bar
    # Search results
    pass

def show_dashboard(service):
    # Welcome banner
    # My current classes (cards with Go to Class, Unenroll)
    # Enroll by key section
    pass

def show_course_detail(service):
    # Breadcrumb
    # Back button
    # Course info
    # Enroll button (if not enrolled) or enrolled message (if enrolled)
    pass
```

---

## Key Design Decisions

1. **No Authentication**: Student "Marcie" is hardcoded and pre-logged in.
2. **Persistent Sidebar**: Home button + search bar always visible; main content changes based on navigation.
3. **Search by Course Name**: Search filters available courses by substring match on course name (not enrollment key).
4. **Flexible Course Access**: Students can navigate to course detail from:
   - Clicking [Go to Class] on enrolled class card
   - Clicking search result from sidebar
   - Both show appropriate enrollment status and actions
5. **Session State for Navigation**: `current_page` and `selected_course` drive which page displays; `search_query` and `search_results` manage sidebar.
6. **Service Layer Only**: UI calls service methods only, never raw SQL or database methods directly.
7. **Soft Unenroll**: Records stay in database with status='unenrolled'; only enrolled classes appear in "My Current Classes".
8. **Minimal Refactoring**: No changes to database.py, service.py, or config.py; all UI logic is in Streamlit app.
9. **Visual Polish & Personal Touches**:
   - **Class Cards**: Interactive card-based UI showing course ID, name, instructor, status badge, enrollment date
   - **Color-Coded Status Badges**: ✅ Green for enrolled, ⭕ Blue for not yet enrolled
   - **Emojis & Icons**: 📚 for classes, 🔍 for search, ✅ for enrolled, ⭕ for not enrolled, ✨ for success
   - **Success Animations**: Enrollment success shows `✨ Successfully enrolled in [Course]! 🎉`
   - **Welcome Banner**: Display greeting with enrollment stats at top of dashboard
   - **Breadcrumb Navigation**: Show user location: "Dashboard > Course Name"
   - **Empty State Message**: Friendly message when no classes enrolled: "🚀 No classes yet! Search for a course or use an enrollment key."
10. **Confirmation Dialog**: Before unenrollment, show modal with warning and [Cancel] / [Confirm Unenroll] buttons.

---

## Future Enhancements (Out of Scope)
- Course detail page with syllabus, assignments, discussion forums
- Admin/instructor view (different dashboard)
- Real authentication and session management
- Caching to reduce database queries
- Student transcript and grade export
- Course search filters (by instructor, by department, etc.)
- Waitlist functionality
- Course recommendations

### Class Detail Navigation
1. User clicks [Go to Class] button from selected enrolled class
2. UI stores course data: `st.session_state.selected_class = {...course_dict...}`
3. Sets `st.session_state.current_page = "class_detail"`
4. Rerun triggers; main layout branch displays class detail page
5. User sees course information on dedicated page
6. User clicks [← Back to Dashboard] button; clears selected_class, resets page to "dashboard"

---

## Session 1 Reference: Files & Methods

### Files Created (from Session 1)
- **config.py**: Constants (CURRENT_STUDENT, STATUS_ENROLLED, STATUS_UNENROLLED, DB_PATH, SNAPSHOT_PATH)
- **database.py**: EnrollmentDatabase class (SQLite operations)
- **service.py**: EnrollmentService class (business logic)
- **utils.py**: Helper functions (export_database_snapshot)
- **main.py**: Demo/testing orchestration

### EnrollmentService Methods Used in UI
```python
service = EnrollmentService(database)

# Get enrolled classes
enrolled = service.get_student_enrollments(user_id)

# Get all available courses
courses = service.get_available_course_keys()

# Search for course by key
course = service.get_course_by_key(enrollment_key)

# Enroll in course
result = service.enroll_with_key(user_id, email, enrollment_key)

# Unenroll from course (soft delete)
success = service.soft_unenroll_student(user_id, course_id)

# Get summary counts
summary = service.get_student_summary(user_id)
```

### EnrollmentDatabase Methods (called by service, not directly by UI)
- `connect()`, `create_tables()`, `seed_sample_data()`
- `find_course_by_key()`, `get_student_enrollment_history()`
- `save_enrollment()`, `update_enrollment_status()`

---

## UI File Structure (Recommended)

### File: `streamlit_app.py` or `app.py`
```python
import streamlit as st
from config import CURRENT_STUDENT, STATUS_ENROLLED, STATUS_UNENROLLED
from database import EnrollmentDatabase
from service import EnrollmentService

# Initialize session state
if "student" not in st.session_state:
    st.session_state.student = CURRENT_STUDENT
    st.session_state.role = "student"
    st.session_state.current_page = "dashboard"
    st.session_state.selected_class = None
    st.session_state.enrollment_message = None
    st.session_state.unenroll_message = None

# Initialize backend
database = EnrollmentDatabase()
database.create_tables()
database.seed_sample_data()
service = EnrollmentService(database)

# Main page routing
if st.session_state.current_page == "dashboard":
    show_dashboard(service)
elif st.session_state.current_page == "class_detail":
    show_class_detail(service)

# Helper functions:
def show_dashboard(service):
    # Sidebar
    # Main content: enrolled classes, enroll form, messages
    pass

def show_class_detail(service):
    # Back button
    # Class information
    # Warning if not found
    pass
```

---

## Key Design Decisions

1. **No Authentication**: Student "Marcie" is hardcoded and pre-logged in.
2. **Sidebar Radio Navigation**: Two distinct modes via radio buttons:
   - "View My Classes": Shows enrolled classes as interactive cards; clicking a card highlights it and shows options
   - "Find & Enroll": Search interface for discovering and enrolling in new courses by enrollment key
3. **Search Scope**: Search looks through **all available courses in the system** (not just enrolled ones), enabling students to find and enroll in any course with a valid enrollment key.
4. **Session State for Navigation**: `current_page` and `selected_class` drive which page displays; `view_mode`, `selected_enrolled_class_index`, and `search_result` manage sidebar/main content state.
5. **Service Layer Only**: UI calls service methods only, never raw SQL or database methods directly.
6. **Soft Unenroll**: Records stay in database with status='unenrolled'; only enrolled classes appear in class cards.
7. **Minimal Refactoring**: No changes to database.py, service.py, or config.py; all UI logic is in Streamlit app.
8. **Visual Polish & Personal Touches**:
   - **Class Cards**: Interactive card-based UI instead of plain radio buttons; cards show course ID, name, instructor, status badge, enrollment date
   - **Color-Coded Status Badges**: ✅ Green for enrolled, ⏱️ Gray for unenrolled, ⭕ Blue for not yet enrolled
   - **Emojis & Icons**: 📚 for classes, 🔍 for search, ✅ for enrolled, ⏱️ for unenrolled, ✨ for success
   - **Success Animations**: Enrollment success shows `✨ Successfully enrolled in [Course]! 🎉` with st.success()
   - **Welcome Banner**: Display greeting with enrollment stats at top of dashboard
   - **Breadcrumb Navigation**: Show user location: "Dashboard > My Classes" or "Dashboard > My Classes > Course Name"
   - **Empty State Message**: Friendly message when no classes enrolled: "🚀 No classes yet! Enter an enrollment key in Find & Enroll to get started."
   - **Sorting**: Sort class cards by Course ID, Course Name, or Enrollment Date
9. **Confirmation Dialog**: Before unenrollment, show modal with warning and [Cancel] / [Confirm Unenroll] buttons to prevent accidental unenrollment.
10. **Status Indicators**: Search results show whether a course is already enrolled, previously unenrolled, or new.

---

## Future Enhancements (Out of Scope)
- Class detail page with syllabus, assignments, grades
- Search results page showing all classes matching a term
- Admin/instructor view (different page)
- Real authentication and session management
- Caching to reduce database queries
- Export student transcript/summary
