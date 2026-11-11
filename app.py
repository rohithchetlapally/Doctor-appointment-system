
import streamlit as st
import pandas as pd
from datetime import date, time, datetime, timedelta

from database import init_db, get_conn, seed_data
from auth import login_user, register_user, logout_user

# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="CarePoint | Doctor Appointment System",
    page_icon="🩺",
    layout="wide"
)

init_db()
seed_data()

# ==========================================
# CUSTOM CSS
# ==========================================

st.markdown("""
<style>
.main {
    background-color: #f7f9fc;
}

.block-container {
    padding-top: 1.5rem;
    max-width: 1200px;
}

.hero {
    padding: 30px;
    border-radius: 18px;
    background: linear-gradient(120deg, #0f766e, #2563eb);
    color: white;
}

div[data-testid="stMetric"] {
    background: white;
    padding: 15px;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# DATABASE FUNCTIONS
# ==========================================

def query_df(sql, params=()):
    with get_conn() as conn:
        return pd.read_sql_query(
            sql,
            conn,
            params=params
        )


def execute(sql, params=()):
    with get_conn() as conn:
        conn.execute(sql, params)
        conn.commit()


# ==========================================
# LOGIN AND REGISTRATION
# ==========================================

def show_login():

    st.markdown("""
    <div class="hero">
        <h1>🩺 CarePoint</h1>
        <p>Your simple, reliable doctor appointment portal</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Sign in")

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Sign in",
            type="primary",
            use_container_width=True
        ):

            user = login_user(email, password)

            if user:
                st.session_state.user = user
                st.rerun()

            else:
                st.error("Invalid email or password.")

    with col2:

        st.subheader("Create patient account")

        name = st.text_input(
            "Full name",
            key="reg_name"
        )

        email2 = st.text_input(
            "Email address",
            key="reg_email"
        )

        phone = st.text_input(
            "Phone number",
            key="reg_phone"
        )

        password2 = st.text_input(
            "Create password",
            type="password",
            key="reg_password"
        )

        if st.button(
            "Register",
            use_container_width=True
        ):

            if not name or not email2 or not password2:
                st.warning("Please fill all required fields.")

            elif len(password2) < 8:
                st.warning("Password must contain at least 8 characters.")

            else:

                success, message = register_user(
                    name,
                    email2,
                    phone,
                    password2
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.info("""
    Demo Accounts:

    Admin: admin@carepoint.demo / Admin123!

    Doctor: doctor@carepoint.demo / Doctor123!

    Patient: patient@carepoint.demo / Patient123!
    """)


# ==========================================
# PATIENT: BOOK APPOINTMENT
# ==========================================

def book_appointment(user):

    st.subheader("Book an appointment")

    doctors = query_df("""
        SELECT id, name, specialty, fee
        FROM doctors
        WHERE active=1
        ORDER BY name
    """)

    if doctors.empty:
        st.warning("No doctors are available.")
        return

    doctor_labels = {
        f"Dr. {r['name']} - {r['specialty']} (₹{r['fee']:.0f})": int(r["id"])
        for _, r in doctors.iterrows()
    }

    with st.form("booking_form"):

        choice = st.selectbox(
            "Choose doctor",
            list(doctor_labels.keys())
        )

        appointment_date = st.date_input(
            "Appointment date",
            min_value=date.today(),
            value=date.today() + timedelta(days=1)
        )

        appointment_time = st.selectbox(
            "Preferred time",
            [
                time(h, m).strftime("%I:%M %p")
                for h in range(9, 18)
                for m in (0, 30)
            ]
        )

        reason = st.text_area(
            "Reason for visit"
        )

        submit = st.form_submit_button(
            "Confirm appointment",
            type="primary"
        )

    if submit:

        if not reason.strip():
            st.error("Please enter the reason for your visit.")
            return

        doctor_id = doctor_labels[choice]

        existing = query_df("""
            SELECT id
            FROM appointments
            WHERE doctor_id=?
            AND appointment_date=?
            AND appointment_time=?
            AND status!='Cancelled'
        """, (
            doctor_id,
            str(appointment_date),
            appointment_time
        ))

        if not existing.empty:

            st.error("This time slot is already booked.")

        else:

            execute("""
                INSERT INTO appointments
                (
                    patient_id,
                    doctor_id,
                    appointment_date,
                    appointment_time,
                    reason,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, 'Pending', ?)
            """, (
                user["id"],
                doctor_id,
                str(appointment_date),
                appointment_time,
                reason.strip(),
                datetime.now().isoformat(timespec="seconds")
            ))

            st.success("Appointment booked successfully!")
            st.rerun()


# ==========================================
# PATIENT DASHBOARD
# ==========================================

def patient_page(user):

    st.title("👤 Patient Dashboard")

    st.write(f"Welcome, **{user['name']}**")

    upcoming = query_df("""
        SELECT a.*, d.name AS doctor_name, d.specialty
        FROM appointments a
        JOIN doctors d ON d.id = a.doctor_id
        WHERE a.patient_id=?
        AND a.appointment_date>=?
        AND a.status!='Cancelled'
        ORDER BY a.appointment_date, a.appointment_time
    """, (
        user["id"],
        str(date.today())
    ))

    total = len(query_df(
        "SELECT id FROM appointments WHERE patient_id=?",
        (user["id"],)
    ))

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Appointments", total)
    c2.metric("Upcoming Appointments", len(upcoming))

    approved = (
        int((upcoming["status"] == "Approved").sum())
        if not upcoming.empty else 0
    )

    c3.metric("Approved Appointments", approved)

    tab1, tab2 = st.tabs([
        "📅 Book Appointment",
        "📋 My Appointments"
    ])

    with tab1:
        book_appointment(user)

    with tab2:

        appointments = query_df("""
            SELECT
                a.id,
                a.appointment_date,
                a.appointment_time,
                a.reason,
                a.status,
                d.name AS doctor,
                d.specialty
            FROM appointments a
            JOIN doctors d ON d.id=a.doctor_id
            WHERE a.patient_id=?
            ORDER BY a.appointment_date DESC
        """, (user["id"],))

        if appointments.empty:

            st.info("No appointments found.")

        else:

            st.dataframe(
                appointments,
                use_container_width=True,
                hide_index=True
            )

            cancellable = appointments[
                appointments.status.isin(["Pending", "Approved"])
            ]

            if not cancellable.empty:

                appointment_id = st.selectbox(
                    "Select appointment to cancel",
                    cancellable.id.tolist()
                )

                if st.button("Cancel Appointment"):

                    execute("""
                        UPDATE appointments
                        SET status='Cancelled'
                        WHERE id=? AND patient_id=?
                    """, (
                        int(appointment_id),
                        user["id"]
                    ))

                    st.success("Appointment cancelled.")
                    st.rerun()


# ==========================================
# DOCTOR DASHBOARD
# ==========================================

def doctor_page(user):

    st.title("🩺 Doctor Dashboard")

    st.write(f"Welcome, Dr. **{user['name']}**")

    doctor = query_df("""
        SELECT *
        FROM doctors
        WHERE user_id=?
    """, (user["id"],))

    if doctor.empty:

        st.warning("Doctor profile not found.")
        return

    doctor_id = int(doctor.iloc[0]["id"])

    appointments = query_df("""
        SELECT
            a.id,
            a.appointment_date,
            a.appointment_time,
            a.reason,
            a.status,
            u.name AS patient,
            u.phone
        FROM appointments a
        JOIN users u ON u.id=a.patient_id
        WHERE a.doctor_id=?
        ORDER BY a.appointment_date, a.appointment_time
    """, (doctor_id,))

    st.metric(
        "Total Assigned Appointments",
        len(appointments)
    )

    if appointments.empty:

        st.info("No appointments assigned yet.")
        return

    st.subheader("Patient Appointments")

    st.dataframe(
        appointments,
        use_container_width=True,
        hide_index=True
    )

    pending = appointments[
        appointments.status == "Pending"
    ]

    if not pending.empty:

        st.subheader("Review Appointment Requests")

        appointment_id = st.selectbox(
            "Select appointment",
            pending.id.tolist(),
            format_func=lambda x: f"Appointment #{x}"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Approve Appointment",
                type="primary"
            ):

                execute("""
                    UPDATE appointments
                    SET status='Approved'
                    WHERE id=?
                """, (int(appointment_id),))

                st.success("Appointment approved.")
                st.rerun()

        with col2:

            if st.button("Reject Appointment"):

                execute("""
                    UPDATE appointments
                    SET status='Rejected'
                    WHERE id=?
                """, (int(appointment_id),))

                st.warning("Appointment rejected.")
                st.rerun()

    approved = appointments[
        appointments.status == "Approved"
    ]

    if not approved.empty:

        st.subheader("Complete Appointment")

        appointment_id2 = st.selectbox(
            "Choose appointment",
            approved.id.tolist(),
            key="complete_appointment"
        )

        if st.button("Mark as Completed"):

            execute("""
                UPDATE appointments
                SET status='Completed'
                WHERE id=?
            """, (int(appointment_id2),))

            st.success("Appointment completed.")
            st.rerun()


# ==========================================
# ADMIN DASHBOARD
# ==========================================

def admin_page():

    st.title("🛡️ Admin Dashboard")

    st.subheader("Hospital Overview")

    users_count = int(query_df(
        "SELECT COUNT(*) AS n FROM users"
    ).iloc[0]["n"])

    doctors_count = int(query_df(
        "SELECT COUNT(*) AS n FROM doctors WHERE active=1"
    ).iloc[0]["n"])

    appointments_count = int(query_df(
        "SELECT COUNT(*) AS n FROM appointments"
    ).iloc[0]["n"])

    pending_count = int(query_df(
        "SELECT COUNT(*) AS n FROM appointments WHERE status='Pending'"
    ).iloc[0]["n"])

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Users", users_count)
    c2.metric("Active Doctors", doctors_count)
    c3.metric("Appointments", appointments_count)
    c4.metric("Pending Requests", pending_count)

    tab1, tab2, tab3 = st.tabs([
        "📅 Manage Appointments",
        "🩺 Manage Doctors",
        "👥 Manage Users"
    ])

    # MANAGE APPOINTMENTS

    with tab1:

        st.subheader("All Appointments")

        appointments = query_df("""
            SELECT
                a.id,
                a.appointment_date,
                a.appointment_time,
                a.status,
                a.reason,
                p.name AS patient,
                d.name AS doctor
            FROM appointments a
            JOIN users p ON p.id=a.patient_id
            JOIN doctors d ON d.id=a.doctor_id
            ORDER BY a.created_at DESC
        """)

        if appointments.empty:

            st.info("No appointments found.")

        else:

            st.dataframe(
                appointments,
                use_container_width=True,
                hide_index=True
            )

            appointment_id = st.selectbox(
                "Select Appointment ID",
                appointments.id.tolist()
            )

            status = st.selectbox(
                "Update Status",
                [
                    "Pending",
                    "Approved",
                    "Rejected",
                    "Cancelled",
                    "Completed"
                ]
            )

            if st.button("Update Appointment"):

                execute("""
                    UPDATE appointments
                    SET status=?
                    WHERE id=?
                """, (
                    status,
                    int(appointment_id)
                ))

                st.success("Appointment updated.")
                st.rerun()

    # MANAGE DOCTORS

    with tab2:

        st.subheader("Doctor List")

        doctors = query_df("""
            SELECT id, name, specialty, fee, active
            FROM doctors
            ORDER BY name
        """)

        st.dataframe(
            doctors,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Add New Doctor")

        with st.form("add_doctor_form"):

            name = st.text_input("Doctor Name")

            specialty = st.text_input("Specialization")

            fee = st.number_input(
                "Consultation Fee",
                min_value=0.0,
                value=500.0,
                step=50.0
            )

            email = st.text_input("Doctor Email")

            password = st.text_input(
                "Temporary Password",
                type="password"
            )

            create = st.form_submit_button("Create Doctor")

        if create:

            if not all([
                name.strip(),
                specialty.strip(),
                email.strip(),
                password
            ]):

                st.error("Please complete all fields.")

            elif len(password) < 8:

                st.error("Password must have at least 8 characters.")

            else:

                from auth import hash_password

                try:

                    execute("""
                        INSERT INTO users
                        (name,email,phone,password_hash,role)
                        VALUES(?,?,?,?, 'doctor')
                    """, (
                        name.strip(),
                        email.strip().lower(),
                        "",
                        hash_password(password)
                    ))

                    doctor_user_id = int(query_df(
                        "SELECT id FROM users WHERE email=?",
                        (email.strip().lower(),)
                    ).iloc[0]["id"])

                    execute("""
                        INSERT INTO doctors
                        (user_id,name,specialty,fee,active)
                        VALUES(?,?,?,?,1)
                    """, (
                        doctor_user_id,
                        name.strip(),
                        specialty.strip(),
                        fee
                    ))

                    st.success("Doctor account created successfully.")
                    st.rerun()

                except Exception:

                    st.error(
                        "Could not create doctor. Email may already exist."
                    )

        # ACTIVATE OR DEACTIVATE DOCTORS

        if not doctors.empty:

            st.subheader("Doctor Availability")

            doctor_id = st.selectbox(
                "Select doctor",
                doctors.id.tolist(),
                format_func=lambda x:
                    f"Doctor #{x} - {doctors[doctors.id == x].iloc[0]['name']}"
            )

            availability = st.selectbox(
                "Availability",
                ["Active", "Inactive"]
            )

            if st.button("Save Availability"):

                execute("""
                    UPDATE doctors
                    SET active=?
                    WHERE id=?
                """, (
                    1 if availability == "Active" else 0,
                    int(doctor_id)
                ))

                st.success("Doctor availability updated.")
                st.rerun()

    # MANAGE USERS

    with tab3:

        st.subheader("Registered Users")

        users = query_df("""
            SELECT
                id,
                name,
                email,
                phone,
                role,
                created_at
            FROM users
            ORDER BY id DESC
        """)

        st.dataframe(
            users,
            use_container_width=True,
            hide_index=True
        )


# ==========================================
# MAIN APPLICATION
# ==========================================

def main():

    if "user" not in st.session_state:

        show_login()
        return

    user = st.session_state.user

    # --------------------------------------
    # SIDEBAR AND DASHBOARD SWITCHER
    # --------------------------------------

    with st.sidebar:

        st.markdown("## 🩺 CarePoint")

        st.write(f"Welcome, **{user['name']}**")

        st.caption(
            f"Current Role: {user['role'].title()}"
        )

        st.divider()

        st.subheader("🔄 Switch Dashboard")

        demo_accounts = {
            "Patient Dashboard": "patient@carepoint.demo",
            "Doctor Dashboard": "doctor@carepoint.demo",
            "Admin Dashboard": "admin@carepoint.demo"
        }

        role_dashboard = {
            "patient": "Patient Dashboard",
            "doctor": "Doctor Dashboard",
            "admin": "Admin Dashboard"
        }

        current_dashboard = role_dashboard.get(
            user["role"],
            "Patient Dashboard"
        )

        dashboard_options = list(demo_accounts.keys())

        selected_dashboard = st.selectbox(
            "Choose Dashboard",
            dashboard_options,
            index=dashboard_options.index(current_dashboard),
            key="dashboard_switcher"
        )

        if st.button(
            "Switch Dashboard",
            type="primary",
            use_container_width=True
        ):

            selected_email = demo_accounts[selected_dashboard]

            selected_user = query_df("""
                SELECT *
                FROM users
                WHERE lower(email)=lower(?)
            """, (selected_email,))

            if not selected_user.empty:

                st.session_state.user = (
                    selected_user.iloc[0].to_dict()
                )

                st.rerun()

            else:

                st.error("Demo account not found.")

        st.caption(
            "Demo mode: switching changes the active demo account."
        )

        st.divider()

        if st.button(
            "🚪 Log out",
            use_container_width=True
        ):

            logout_user()

    # --------------------------------------
    # DISPLAY SELECTED DASHBOARD
    # --------------------------------------

    user = st.session_state.user

    if user["role"] == "patient":

        patient_page(user)

    elif user["role"] == "doctor":

        doctor_page(user)

    elif user["role"] == "admin":

        admin_page()

    else:

        st.error("Unknown user role.")


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    main()
