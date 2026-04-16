import os

import pandas as pd
import streamlit as st

from admin_utils import (
    add_user,
    change_password,
    get_security_question,
    reset_password_if_correct,
    validate_password_strength,
    verify_login,
)
from streamlit_core import (
    dataframe_to_excel_bytes,
    ensure_directories,
    get_attendance_files,
    get_dashboard_stats,
    get_opencv_status,
    get_today_attendance_file,
    list_registered_users,
    load_attendance_dataframe,
    recognize_and_mark_attendance,
    sanitize_person_name,
    save_face_sample,
    train_model_from_dataset,
    count_face_samples,
)

st.set_page_config(
    page_title="Face Recognition Attendance",
    page_icon="attendance",
    layout="wide",
)

ensure_directories()
OPENCV_OK, OPENCV_MESSAGE = get_opencv_status()

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f7fb;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.2rem;
    }
    .mini-card {
        background: white;
        border: 1px solid #d8e0ea;
        border-radius: 12px;
        padding: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _init_session_state():
    defaults = {
        "authenticated": False,
        "username": "",
        "reset_question": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_session_state()


def _render_opencv_banner():
    if OPENCV_OK:
        return

    st.error(
        "OpenCV failed to import in this deployment environment. "
        "Face registration/training/attendance features will not work until dependency is fixed."
    )
    st.code(OPENCV_MESSAGE)


def _render_login_page():
    left, right = st.columns([1.15, 1])

    with left:
        st.title("Face Recognition Attendance")
        st.caption("Web Deployment (Streamlit)")
        st.write("Use this interface to manage users, train model, and mark attendance.")

        with st.container(border=True):
            st.subheader("Quick Attendance (No Login)")
            _render_take_attendance_panel(prefix="public")

    with right:
        st.subheader("Admin Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_submit = st.form_submit_button("Login", use_container_width=True)

        if login_submit:
            if verify_login(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username.strip()
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid username or password")

        with st.expander("Forgot Password"):
            reset_user = st.text_input("Username", key="forgot_username")

            if st.button("Load Security Question", key="load_security_question"):
                question = get_security_question(reset_user)
                if question:
                    st.session_state.reset_question = question
                    st.success("Security question loaded")
                else:
                    st.session_state.reset_question = ""
                    st.error("Username not found")

            if st.session_state.reset_question:
                st.info(st.session_state.reset_question)

            answer = st.text_input("Security Answer", key="forgot_answer")
            new_password = st.text_input("New Password", type="password", key="forgot_new_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="forgot_confirm_password")

            if st.button("Reset Password", key="reset_password_button"):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    valid, reason = validate_password_strength(new_password)
                    if not valid:
                        st.error(reason)
                    else:
                        ok = reset_password_if_correct(reset_user, answer, new_password)
                        if ok:
                            st.success("Password reset successful")
                        else:
                            st.error("Incorrect security answer or invalid username")


def _render_dashboard_page():
    stats = get_dashboard_stats()

    st.subheader("Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registered Users", stats["users"])
    c2.metric("Face Samples", stats["samples"])
    c3.metric("Attendance Files", stats["attendance_files"])
    c4.metric("Latest Records", stats["latest_records"])

    if stats["latest_file"]:
        st.caption(f"Latest file: {os.path.basename(stats['latest_file'])}")

    st.info(
        "Recommended flow: Register Face -> Train Model -> Take Attendance -> View Attendance"
    )


def _render_register_face_page():
    st.subheader("Register Face")

    name = st.text_input("Person Name", placeholder="Example: aaryan")
    safe_name = sanitize_person_name(name)
    if name and not safe_name:
        st.warning("Use letters, numbers, spaces, or underscore only.")

    cam_col, upload_col = st.columns(2)

    with cam_col:
        st.markdown("#### Camera Capture")
        camera_image = st.camera_input("Capture Sample", key="register_camera")

        if st.button("Save Camera Sample", key="save_camera_sample", use_container_width=True):
            if not name.strip():
                st.error("Enter person name first")
            elif camera_image is None:
                st.error("Capture an image first")
            else:
                result = save_face_sample(name, camera_image)
                if result["success"]:
                    st.success(result["message"])
                else:
                    st.error(result["message"])

    with upload_col:
        st.markdown("#### Upload Images")
        uploaded_files = st.file_uploader(
            "Upload face images",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="register_uploads",
        )

        if st.button("Save Uploaded Samples", key="save_uploaded_samples", use_container_width=True):
            if not name.strip():
                st.error("Enter person name first")
            elif not uploaded_files:
                st.error("Upload at least one image")
            else:
                success_count = 0
                failed = []

                for uploaded in uploaded_files:
                    result = save_face_sample(name, uploaded)
                    if result["success"]:
                        success_count += 1
                    else:
                        failed.append(f"{uploaded.name}: {result['message']}")

                if success_count:
                    st.success(f"Saved {success_count} sample(s)")
                if failed:
                    st.warning("Some files failed:")
                    for item in failed:
                        st.write(f"- {item}")

    st.markdown("#### Registered Users")
    users = list_registered_users()
    if not users:
        st.info("No users registered yet.")
    else:
        user_df = pd.DataFrame(
            {
                "User": users,
                "Samples": [count_face_samples(user) for user in users],
            }
        )
        st.dataframe(user_df, use_container_width=True, hide_index=True)


def _render_train_model_page():
    st.subheader("Train Model")
    st.write("Train recognizer using all samples in `faces/`.")

    if st.button("Start Training", type="primary"):
        with st.spinner("Training model..."):
            result = train_model_from_dataset()

        if result["success"]:
            st.success(result["message"])
            st.write(f"Users: {result['users']}")
            st.write(f"Samples: {result['samples']}")
            if isinstance(result.get("labels"), pd.DataFrame):
                st.dataframe(result["labels"], use_container_width=True, hide_index=True)
        else:
            st.error(result["message"])


def _render_take_attendance_panel(prefix="private"):
    source = st.radio(
        "Image Source",
        ["Camera", "Upload Image"],
        horizontal=True,
        key=f"{prefix}_attendance_source",
    )
    threshold = st.slider(
        "Confidence Threshold (lower is stricter)",
        min_value=40,
        max_value=120,
        value=80,
        step=1,
        key=f"{prefix}_attendance_threshold",
    )

    image_input = None

    if source == "Camera":
        image_input = st.camera_input("Capture Attendance Frame", key=f"{prefix}_attendance_camera")
    else:
        image_input = st.file_uploader(
            "Upload image for attendance",
            type=["jpg", "jpeg", "png"],
            key=f"{prefix}_attendance_upload",
        )

    if st.button("Recognize and Mark Attendance", key=f"{prefix}_attendance_run", use_container_width=True):
        if image_input is None:
            st.error("Provide image input first")
        else:
            with st.spinner("Running recognition..."):
                result = recognize_and_mark_attendance(image_input, threshold)

            if not result["success"]:
                st.error(result["message"])
            else:
                st.success(result["message"])
                st.image(result["annotated_rgb"], caption="Recognition Result", use_container_width=True)

                if result["detections"]:
                    det_df = pd.DataFrame(result["detections"])
                    st.dataframe(det_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No faces detected.")

                if result["marked_names"]:
                    st.success("Marked: " + ", ".join(result["marked_names"]))
                if result["already_marked_names"]:
                    st.info("Already marked today: " + ", ".join(result["already_marked_names"]))

                st.caption(f"Attendance file: {os.path.basename(result['attendance_file'])}")



def _render_take_attendance_page():
    st.subheader("Take Attendance")
    _render_take_attendance_panel(prefix="private")

    st.markdown("#### Today Attendance")
    today_file = get_today_attendance_file()
    today_df = load_attendance_dataframe(today_file)

    if today_df.empty:
        st.info("No attendance marked today.")
    else:
        st.dataframe(today_df, use_container_width=True, hide_index=True)

        csv_bytes = today_df.to_csv(index=False).encode("utf-8")
        excel_bytes = dataframe_to_excel_bytes(today_df)

        c1, c2 = st.columns(2)
        c1.download_button(
            "Download Today CSV",
            data=csv_bytes,
            file_name=os.path.basename(today_file),
            mime="text/csv",
            use_container_width=True,
        )
        c2.download_button(
            "Download Today Excel",
            data=excel_bytes,
            file_name=os.path.basename(today_file).replace(".csv", ".xlsx"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def _render_view_attendance_page():
    st.subheader("View Attendance")

    attendance_files = get_attendance_files()
    if not attendance_files:
        st.info("No attendance files found.")
        return

    options = {os.path.basename(path): path for path in attendance_files}
    selected_label = st.selectbox("Select Attendance File", list(options.keys()))
    selected_file = options[selected_label]

    df = load_attendance_dataframe(selected_file)
    if df.empty:
        st.warning("Selected file has no readable attendance rows.")
        return

    search_col, date_col = st.columns([2, 1])
    search_value = search_col.text_input("Search", placeholder="Name, date, time")

    unique_dates = sorted(
        [d for d in df["Date"].astype(str).unique().tolist() if d and d != "-"]
    )
    date_filter = date_col.selectbox("Date Filter", ["All Dates"] + unique_dates)

    filtered = df.copy()

    if search_value.strip():
        query = search_value.strip().lower()
        mask = (
            filtered["Name"].astype(str).str.lower().str.contains(query, na=False)
            | filtered["Date"].astype(str).str.lower().str.contains(query, na=False)
            | filtered["Time"].astype(str).str.lower().str.contains(query, na=False)
        )
        filtered = filtered[mask]

    if date_filter != "All Dates":
        filtered = filtered[filtered["Date"].astype(str) == date_filter]

    st.dataframe(filtered.reset_index(drop=True), use_container_width=True, hide_index=True)

    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    excel_bytes = dataframe_to_excel_bytes(filtered)

    c1, c2 = st.columns(2)
    c1.download_button(
        "Download Filtered CSV",
        data=csv_bytes,
        file_name=selected_label,
        mime="text/csv",
        use_container_width=True,
    )
    c2.download_button(
        "Download Filtered Excel",
        data=excel_bytes,
        file_name=selected_label.replace(".csv", ".xlsx"),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


def _render_admin_page():
    st.subheader("Admin Settings")

    left, right = st.columns(2)

    with left:
        st.markdown("#### Add New Admin")
        with st.form("add_admin_form"):
            new_user = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            security_question = st.text_input("Security Question")
            security_answer = st.text_input("Security Answer")
            create_submit = st.form_submit_button("Create Admin", use_container_width=True)

        if create_submit:
            safe_user = sanitize_person_name(new_user)
            if not safe_user:
                st.error("Enter a valid username")
            else:
                valid, reason = validate_password_strength(new_password)
                if not valid:
                    st.error(reason)
                else:
                    ok = add_user(safe_user, new_password, security_question, security_answer)
                    if ok:
                        st.success(f"Admin created: {safe_user}")
                    else:
                        st.error("Failed to create admin (username may already exist)")

    with right:
        st.markdown("#### Change Password")
        with st.form("change_password_form"):
            cp_user = st.text_input("Username", key="cp_username")
            cp_old = st.text_input("Current Password", type="password")
            cp_new = st.text_input("New Password", type="password")
            cp_submit = st.form_submit_button("Update Password", use_container_width=True)

        if cp_submit:
            valid, reason = validate_password_strength(cp_new)
            if not valid:
                st.error(reason)
            else:
                ok = change_password(cp_user, cp_old, cp_new)
                if ok:
                    st.success("Password updated successfully")
                else:
                    st.error("Failed to update password")


def _render_main_app():
    st.sidebar.title("Face Attendance")
    st.sidebar.caption(f"Logged in as: {st.session_state.username}")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Register Face",
            "Train Model",
            "Take Attendance",
            "View Attendance",
            "Admin Settings",
        ],
    )

    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

    if page == "Dashboard":
        _render_dashboard_page()
    elif page == "Register Face":
        _render_register_face_page()
    elif page == "Train Model":
        _render_train_model_page()
    elif page == "Take Attendance":
        _render_take_attendance_page()
    elif page == "View Attendance":
        _render_view_attendance_page()
    elif page == "Admin Settings":
        _render_admin_page()


if not st.session_state.authenticated:
    _render_opencv_banner()
    _render_login_page()
else:
    _render_opencv_banner()
    _render_main_app()
