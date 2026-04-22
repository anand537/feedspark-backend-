# 🎉 Release Notes: Version 2.0.0 - Cloud Migration & Feature Pack

**Date:** [Date of Release]

This is a major foundational update to the Auto-Feedback Generator backend. We have migrated the entire database to a cloud platform, introduced several new real-time features, and established a professional CI/CD and testing workflow.

---

## 🚀 Highlights

*   **☁️ Cloud-First Architecture**: The backend has been successfully migrated from a local SQLite database to a scalable, production-ready **Supabase PostgreSQL** database. This enables team collaboration, automatic daily backups, and enterprise-grade performance.
*   **💬 Real-time Chat Groups**: Mentors can now create course-specific chat groups, allowing real-time communication with all enrolled students.
*   **📢 Announcement System**: A new system for broadcasting announcements to all users, specific roles, or individual courses, complete with scheduling capabilities.
*   **✅ Automated Testing & CI**: A full `pytest` test suite and a **GitHub Actions workflow** have been implemented. Tests now run automatically on every push, ensuring code quality and stability.

---

## ✨ New Features

### 🗣️ Communication & Collaboration
*   **Chat Groups**: Mentors can create dedicated, real-time chat groups for each course they manage. Students are automatically added upon enrollment.
*   **Announcements**: A full-featured announcement system allows mentors and admins to post important updates. Announcements can be targeted and scheduled for future publication.

### 🗓️ Meeting Management
*   **Automatic Link Generation**: Meetings created without a link will now automatically generate a unique, secure Jitsi Meet URL.
*   **Automated Attendance**: The system now tracks student attendance. Students who join a meeting are marked 'present'.
*   **Absence Processing**: A background job runs periodically to mark students as 'absent' for meetings that have ended, and automatically sends them a notification email.
*   **Attendance Reports**: Mentors automatically receive a CSV attendance report via email after a meeting concludes. They can also manually export reports in CSV or PDF format.
*   **Manual Correction**: Mentors can manually override the attendance status of any participant.

### 📝 Feedback & Submissions
*   **Feedback Version History**: AI-generated feedback now has a complete version history. Mentors can view past versions and revert to a previous one if needed.
*   **Regenerate with Instructions**: Mentors can now re-run the AI feedback generation with new, custom instructions to refine the output.
*   **Secure File Uploads**: Student submissions are now uploaded to Supabase Storage, and files are accessed via secure, expiring signed URLs instead of public links.

---

## ⚙️ Backend & Infrastructure Enhancements

*   **Database Migration**: The core of this update. The entire application now uses a robust PostgreSQL database hosted on Supabase.
*   **CI/CD Pipeline**: The new GitHub Actions workflow (`.github/workflows/ci.yml`) automates testing across Python 3.9 and 3.10 on every push and pull request to `main`, `master`, and `anand`.
*   **Code Refactoring**:
    *   All utility functions (`email_utils`, `storage_utils`, `validation`) have been consolidated into a clean `app/utils/` package.
    *   Redundant and legacy scripts have been removed.
*   **Performance Optimization**: Fixed a critical N+1 query issue in the feedback templates API, significantly improving its performance by using a database `JOIN`.
*   **Test Suite**:
    *   Introduced `pytest` with a `pytest.ini` configuration for automated testing.
    *   Consolidated manual verification scripts into a single, interactive tool (`tests/verify_system.py`).
    *   Created a unified functional test file (`tests/test_functional.py`) for automated CI runs.

---

## ⚠️ Important Notes for Developers

### 1. Environment Variables Update
Your `.env` file **must be updated**. The old SQLite configuration is no longer used.

*   **Action Required**: Copy the contents of `.env.example` to a new `.env` file.
*   **Action Required**: Add the `DATABASE_URL` for the new Supabase project. Please contact the team lead for the credentials.

### 2. Install New Dependencies
The project now requires the PostgreSQL driver.

*   **Action Required**: Run `pip install -r requirements.txt` to install `psycopg2-binary` and other updated packages.

### 3. Documentation
All documentation has been consolidated into the `docs/` folder. Please refer to `docs/MIGRATION_GUIDE.md` and `docs/AUTHENTICATION_GUIDE.md` for detailed information on the new architecture.

---

## 🚀 Getting Started

To get your local environment up and running with the new changes:

1.  **Pull the latest code:**
    ```bash
    git pull origin main # or your feature branch
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your environment:**
    *   Create a `.env` file from `.env.example`.
    *   Fill in the `DATABASE_URL` and other required keys.

4.  **Verify your connection (Optional but Recommended):**
    ```bash
    python tests/verify_system.py
    ```

5.  **Run the application:**
    ```bash
    python run.py
    ```

The application will now connect to the Supabase database. All features, including the new chat and announcement systems, are ready for use.

---

A huge thank you to everyone involved in this massive effort. This migration sets a solid foundation for the future growth and stability of our application.

Happy coding! 🚀