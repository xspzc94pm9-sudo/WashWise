# WashWise — Smart Hostel Laundry & Resource Booker

A Flask + SQLite demo application with student/admin roles, hostel profiles, machine inventory, booking conflict checks, check-in/cancellation, complaints, admin analytics and an IoT event simulator.

## Run on macOS / Windows / Linux

1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Open Terminal in VS Code and run:

```bash
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
# On Windows PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

4. Open https://xspzc94pm9-sudo.github.io/WashWise/ in your browser.

## Demo logins

**Student**
- Email: `ankit@washwise.demo`
- Password: `student123`

**Admin**
- Email: `admin@washwise.demo`
- Password: `admin123`

Additional seeded student: `priya@washwise.demo` / `student123` and `rahul@washwise.demo` / `student123`.

## Main features

- Role-based student and admin login
- Student ID / unique user code, hostel, block and room number
- Machine photo cards with Available, Running, Reserved and Maintenance states
- Slot booking with server-side overlap/conflict validation
- Booking history, cancellation and demo check-in
- Admin student directory and machine inventory/status management
- Complaint tickets and admin resolution workflow
- Admin analytics charts (Chart.js)
- IoT monitor with clearly labelled software-generated sensor simulation and event log
- Responsive interface for desktop and mobile

## IoT explanation for your presentation

The included **IoT Simulator** is software-only and does not connect to a physical washing machine. Click **IoT Monitor → Simulate sensor event** while logged in as admin. The app changes a machine state and writes a sensor event to SQLite. This demonstrates the data flow from a machine-side sensor/ESP32 through Wi-Fi/API or MQTT to the backend and dashboard.

For a physical prototype, use an ESP32 and an approved isolated, non-invasive sensing design selected and installed under qualified supervision. The ESP32 can send a small JSON status message to a protected backend endpoint or MQTT broker. Do not connect student-built circuits to mains wiring or open/modify the washing machine electrical system.

## Important demo notes

- Seeded users and machine records are sample/demo data. Replace them with approved project data before a real pilot.
- Machine images are loaded from Unsplash URLs, so internet access is needed to display them. The dashboard and app logic run locally.
- Chart.js and Google Fonts are loaded from CDNs; charts/fonts need internet access.
- This is an academic prototype, not a production-ready campus identity or payment system. Before real deployment add secure secret management, HTTPS, CSRF protection, password reset, stronger admin controls, backups, audit logging and institutional approval.
- The default Flask debug server is for local development only. Do not expose it to the public internet.

## Reset demo database

Stop the app, delete `washwise.db`, then run `python app.py` again. The demo database and sample records will be recreated automatically.

## One-command launch scripts

- macOS: in Terminal run `./run_mac.sh` (or `bash run_mac.sh`).
- Windows: double-click `run_windows.bat`.

Booking codes also render as QR codes in the booking list (the QR library is loaded from a CDN, so internet is required for that visual feature).
