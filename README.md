# CarePoint — Doctor Appointment System

A full-stack-style Doctor Appointment System built with **Streamlit + SQLite**. It is designed for a student web-development project and can be pushed to GitHub and deployed on Streamlit Community Cloud.

## Features

- Patient registration and login
- Role-based patient, doctor, and admin dashboards
- Browse active doctors and specialties
- Book appointments with date, time, and reason
- Basic slot-conflict prevention
- Patients can view and cancel appointments
- Doctors can approve, reject, and complete appointments
- Admin can view users and appointments, update appointment status, add doctors, and enable/disable doctor profiles
- SQLite database with password hashing

## Run locally

1. Install Python 3.10 or newer.
2. Extract this ZIP and open the folder in VS Code.
3. Open a terminal in the project folder.
4. Create and activate a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   # Windows:
   .venv\\Scripts\\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Start the app:

   ```bash
   streamlit run app.py
   ```

## Demo login accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@carepoint.demo | Admin123! |
| Doctor | doctor@carepoint.demo | Doctor123! |
| Patient | patient@carepoint.demo | Patient123! |

Change/remove demo credentials before any public deployment.

## Upload to GitHub

1. Create a new repository on GitHub.
2. Extract this ZIP.
3. Open the extracted folder in VS Code.
4. Run:

   ```bash
   git init
   git add .
   git commit -m "Add CarePoint doctor appointment system"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   git push -u origin main
   ```

## Deploy on Streamlit Community Cloud

1. Push the project to GitHub.
2. Sign in at https://share.streamlit.io/ using GitHub.
3. Choose **Create app**.
4. Select your repository and branch (`main`).
5. Set the main file path to `app.py`.
6. Click **Deploy**.

## Database and deployment note

The app uses a local SQLite file (`carepoint.db`) created automatically on first run. Some hosted environments may not guarantee persistence of local files across rebuilds/redeployments. For a real multi-user production system, use a managed database such as PostgreSQL, add email verification/password reset, stronger authorization controls, audit logs, backups, HTTPS, and privacy/security review.

This is an educational demo, not a certified medical-record system. Do not enter real patient medical information.
