from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date, timedelta
import sqlite3, os, random, string

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'washwise.db')
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key-for-production')


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def init_db():
    con = db()
    con.executescript('''
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_code TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'student', hostel TEXT NOT NULL DEFAULT 'Boys Hostel',
      block TEXT NOT NULL DEFAULT 'A', room TEXT NOT NULL DEFAULT '101', phone TEXT DEFAULT '',
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS machines (
      id INTEGER PRIMARY KEY AUTOINCREMENT, machine_code TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'Washer', status TEXT NOT NULL DEFAULT 'Available',
      location TEXT NOT NULL DEFAULT 'Laundry Room', last_updated TEXT NOT NULL,
      cycle_minutes INTEGER NOT NULL DEFAULT 45, image TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS bookings (
      id INTEGER PRIMARY KEY AUTOINCREMENT, booking_code TEXT UNIQUE NOT NULL,
      user_id INTEGER NOT NULL, machine_id INTEGER NOT NULL, booking_date TEXT NOT NULL,
      start_time TEXT NOT NULL, end_time TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Confirmed',
      created_at TEXT NOT NULL, checked_in INTEGER NOT NULL DEFAULT 0,
      FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(machine_id) REFERENCES machines(id)
    );
    CREATE TABLE IF NOT EXISTS complaints (
      id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_code TEXT UNIQUE NOT NULL,
      user_id INTEGER NOT NULL, machine_id INTEGER, issue TEXT NOT NULL, details TEXT DEFAULT '',
      status TEXT NOT NULL DEFAULT 'Pending', created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(machine_id) REFERENCES machines(id)
    );
    CREATE TABLE IF NOT EXISTS sensor_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT, machine_id INTEGER NOT NULL,
      old_status TEXT, new_status TEXT NOT NULL, source TEXT NOT NULL,
      event_time TEXT NOT NULL, FOREIGN KEY(machine_id) REFERENCES machines(id)
    );
    ''')
    if con.execute('SELECT COUNT(*) n FROM users').fetchone()['n'] == 0:
        now = datetime.now().isoformat(timespec='minutes')
        users = [
          ('STU-1001','Ankit Kumar','ankit@washwise.demo','student123','student','Boys Hostel','A','205',''),
          ('STU-1002','Priya Sharma','priya@washwise.demo','student123','student','Girls Hostel','B','112',''),
          ('STU-1003','Rahul Verma','rahul@washwise.demo','student123','student','Boys Hostel','C','308',''),
          ('ADM-0001','Laundry Admin','admin@washwise.demo','admin123','admin','Main Hostel','Admin','Office','')]
        for code,name,email,pw,role,hostel,block,room,phone in users:
            con.execute('INSERT INTO users(student_code,name,email,password,role,hostel,block,room,phone,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                        (code,name,email,generate_password_hash(pw),role,hostel,block,room,phone,now))
        machines = [
          ('WM-01','Front Load Washer 01','Washer','Available','Laundry Room - Ground Floor',45,'https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=700'),
          ('WM-02','Front Load Washer 02','Washer','Running','Laundry Room - Ground Floor',45,'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=700'),
          ('WM-03','Top Load Washer 03','Washer','Available','Laundry Room - Ground Floor',40,'https://images.unsplash.com/photo-1604335399105-a0c585fd81a1?w=700'),
          ('WM-04','Front Load Washer 04','Washer','Maintenance','Laundry Room - First Floor',45,'https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=700'),
          ('DR-01','Smart Dryer 01','Dryer','Available','Laundry Room - First Floor',35,'https://images.unsplash.com/photo-1635273720234-3f3f9f8a6e9b?w=700'),
          ('DR-02','Smart Dryer 02','Dryer','Running','Laundry Room - First Floor',35,'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=700')]
        for code,name,kind,status,loc,mins,img in machines:
            con.execute('INSERT INTO machines(machine_code,name,kind,status,location,last_updated,cycle_minutes,image) VALUES(?,?,?,?,?,?,?,?)',
                        (code,name,kind,status,loc,now,mins,img))
    con.commit(); con.close()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access is required for that page.', 'error')
            return redirect(url_for('dashboard'))
        return fn(*args, **kwargs)
    return wrapper


def current_user():
    if not session.get('user_id'): return None
    con=db(); row=con.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone(); con.close(); return row


def make_code(prefix):
    return prefix + '-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


@app.context_processor
def inject_globals():
    return {'current_user': current_user(), 'today': date.today().isoformat()}


@app.route('/')
def home():
    return redirect(url_for('dashboard') if session.get('user_id') else url_for('login'))


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        con=db(); user=con.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone(); con.close()
        if user and check_password_hash(user['password'],password):
            session.clear(); session['user_id']=user['id']; session['role']=user['role']; session['name']=user['name']
            return redirect(url_for('dashboard'))
        flash('Incorrect email or password. Please try again.','error')
    return render_template('login.html')


@app.route('/register', methods=['GET','POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name=request.form.get('name','').strip()
        email=request.form.get('email','').strip().lower()
        password=request.form.get('password','')
        hostel=request.form.get('hostel','').strip()
        block=request.form.get('block','').strip()
        room=request.form.get('room','').strip()
        if not all([name,email,password,hostel,block,room]):
            flash('Please fill in all required fields.','error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long.','error')
        else:
            con=db()
            try:
                code=make_code('STU')
                con.execute("INSERT INTO users(student_code,name,email,password,role,hostel,block,room,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                            (code,name,email,generate_password_hash(password),'student',hostel,block,room,datetime.now().isoformat(timespec='minutes')))
                con.commit()
                flash(f'Account created successfully! Your Student Code is {code}. Please sign in.','success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                con.rollback(); flash('This email is already registered. Please sign in instead.','error')
            finally:
                con.close()
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    con=db(); user=current_user()
    machines=con.execute('SELECT * FROM machines ORDER BY id').fetchall()
    counts={r['status'].lower():r['n'] for r in con.execute('SELECT status,COUNT(*) n FROM machines GROUP BY status').fetchall()}
    if user['role']=='admin':
        total_users=con.execute("SELECT COUNT(*) n FROM users WHERE role='student'").fetchone()['n']
        total_bookings=con.execute('SELECT COUNT(*) n FROM bookings').fetchone()['n']
        bookings=con.execute('''SELECT b.*,u.name,u.student_code,u.hostel,u.block,u.room,m.name machine_name,m.machine_code FROM bookings b JOIN users u ON u.id=b.user_id JOIN machines m ON m.id=b.machine_id ORDER BY b.id DESC LIMIT 8''').fetchall()
        my_bookings=[]
    else:
        total_users=0; total_bookings=0
        bookings=con.execute('''SELECT b.*,m.name machine_name,m.machine_code FROM bookings b JOIN machines m ON m.id=b.machine_id WHERE b.user_id=? ORDER BY b.booking_date DESC,b.start_time DESC LIMIT 5''',(user['id'],)).fetchall()
        my_bookings=bookings
    recent_events=con.execute('''SELECT e.*,m.machine_code FROM sensor_events e JOIN machines m ON m.id=e.machine_id ORDER BY e.id DESC LIMIT 5''').fetchall()
    con.close()
    return render_template('dashboard.html',machines=machines,counts=counts,bookings=bookings,my_bookings=my_bookings,total_users=total_users,total_bookings=total_bookings,recent_events=recent_events)


@app.route('/bookings', methods=['GET','POST'])
@login_required
def bookings():
    con=db(); user=current_user()
    if request.method=='POST':
        machine_id=request.form.get('machine_id'); bdate=request.form.get('booking_date'); start=request.form.get('start_time')
        try:
            start_dt=datetime.strptime(start,'%H:%M'); end_dt=start_dt+timedelta(minutes=45); end=end_dt.strftime('%H:%M')
            if datetime.strptime(bdate,'%Y-%m-%d').date() < date.today(): raise ValueError()
        except Exception:
            con.close(); flash('Please select a valid date and time.','error'); return redirect(url_for('bookings'))
        machine=con.execute('SELECT * FROM machines WHERE id=?',(machine_id,)).fetchone()
        if not machine or machine['status']=='Maintenance':
            con.close(); flash('This machine is not available for booking.','error'); return redirect(url_for('bookings'))
        overlap=con.execute('''SELECT COUNT(*) n FROM bookings WHERE machine_id=? AND booking_date=? AND status IN ('Confirmed','Checked In') AND NOT(end_time<=? OR start_time>=?)''',(machine_id,bdate,start,end)).fetchone()['n']
        if overlap:
            con.close(); flash('This time slot is already booked. Please choose another slot.','error'); return redirect(url_for('bookings'))
        code=make_code('WW'); now=datetime.now().isoformat(timespec='minutes')
        con.execute('INSERT INTO bookings(booking_code,user_id,machine_id,booking_date,start_time,end_time,status,created_at) VALUES(?,?,?,?,?,?,?,?)',(code,user['id'],machine_id,bdate,start,end,'Confirmed',now))
        con.commit(); con.close(); flash(f'Booking confirmed! Your booking code is {code}.','success'); return redirect(url_for('bookings'))
    if user['role']=='admin':
        rows=con.execute('''SELECT b.*,u.name,u.student_code,u.hostel,u.block,u.room,m.name machine_name,m.machine_code FROM bookings b JOIN users u ON u.id=b.user_id JOIN machines m ON m.id=b.machine_id ORDER BY b.booking_date DESC,b.start_time DESC''').fetchall()
    else:
        rows=con.execute('''SELECT b.*,m.name machine_name,m.machine_code FROM bookings b JOIN machines m ON m.id=b.machine_id WHERE b.user_id=? ORDER BY b.booking_date DESC,b.start_time DESC''',(user['id'],)).fetchall()
    machines=con.execute('SELECT * FROM machines ORDER BY name').fetchall(); con.close()
    return render_template('bookings.html',rows=rows,machines=machines)


@app.route('/booking/<int:booking_id>/cancel',methods=['POST'])
@login_required
def cancel_booking(booking_id):
    con=db(); row=con.execute('SELECT * FROM bookings WHERE id=?',(booking_id,)).fetchone()
    if row and (row['user_id']==session['user_id'] or session.get('role')=='admin') and row['status']=='Confirmed':
        con.execute("UPDATE bookings SET status='Cancelled' WHERE id=?",(booking_id,)); con.commit(); flash('Booking cancelled.','success')
    else: flash('Booking could not be cancelled.','error')
    con.close(); return redirect(request.referrer or url_for('bookings'))


@app.route('/booking/<int:booking_id>/checkin',methods=['POST'])
@login_required
def checkin(booking_id):
    con=db(); row=con.execute('SELECT * FROM bookings WHERE id=?',(booking_id,)).fetchone()
    if row and (row['user_id']==session['user_id'] or session.get('role')=='admin') and row['status']=='Confirmed':
        con.execute("UPDATE bookings SET status='Checked In',checked_in=1 WHERE id=?",(booking_id,)); con.commit(); flash('Check-in recorded successfully.','success')
    con.close(); return redirect(request.referrer or url_for('bookings'))


@app.route('/users')
@admin_required
def users():
    con=db(); rows=con.execute("SELECT u.*,COUNT(b.id) booking_count FROM users u LEFT JOIN bookings b ON b.user_id=u.id WHERE u.role='student' GROUP BY u.id ORDER BY u.id DESC").fetchall(); con.close()
    return render_template('users.html',rows=rows)


@app.route('/machines',methods=['GET','POST'])
@admin_required
def machines_page():
    con=db()
    if request.method=='POST':
        code=request.form.get('machine_code','').strip().upper(); name=request.form.get('name','').strip(); kind=request.form.get('kind','Washer'); location=request.form.get('location','Laundry Room')
        if code and name:
            try:
                con.execute('INSERT INTO machines(machine_code,name,kind,status,location,last_updated,cycle_minutes) VALUES(?,?,?,?,?,?,?)',(code,name,kind,'Available',location,datetime.now().isoformat(timespec='minutes'),45)); con.commit(); flash('Machine added.','success')
            except sqlite3.IntegrityError: flash('Machine code already exists.','error')
        else: flash('Enter machine code and name.','error')
    rows=con.execute('SELECT * FROM machines ORDER BY id').fetchall(); con.close(); return render_template('machines.html',rows=rows)


@app.route('/machine/<int:machine_id>/status',methods=['POST'])
@admin_required
def machine_status(machine_id):
    status=request.form.get('status'); allowed=['Available','Running','Maintenance','Reserved']
    if status not in allowed: flash('Invalid machine status.','error'); return redirect(url_for('machines_page'))
    con=db(); old=con.execute('SELECT status FROM machines WHERE id=?',(machine_id,)).fetchone()
    if old:
        now=datetime.now().isoformat(timespec='minutes'); con.execute('UPDATE machines SET status=?,last_updated=? WHERE id=?',(status,now,machine_id)); con.execute('INSERT INTO sensor_events(machine_id,old_status,new_status,source,event_time) VALUES(?,?,?,?,?)',(machine_id,old['status'],status,'Admin update',now)); con.commit(); flash('Machine status updated.','success')
    con.close(); return redirect(url_for('machines_page'))


@app.route('/iot/simulate',methods=['POST'])
@admin_required
def iot_simulate():
    con=db(); machines=con.execute('SELECT * FROM machines').fetchall(); choices=['Available','Running','Maintenance']
    if not machines: con.close(); return jsonify({'ok':False,'message':'No machines found'})
    machine=random.choice(machines); new=random.choice([s for s in choices if s != machine['status']]); now=datetime.now().isoformat(timespec='minutes')
    con.execute('UPDATE machines SET status=?,last_updated=? WHERE id=?',(new,now,machine['id']))
    con.execute('INSERT INTO sensor_events(machine_id,old_status,new_status,source,event_time) VALUES(?,?,?,?,?)',(machine['id'],machine['status'],new,'IoT Simulator',now)); con.commit(); con.close()
    return jsonify({'ok':True,'machine':machine['machine_code'],'status':new,'time':now,'message':'Simulated sensor event received'})


@app.route('/iot')
@admin_required
def iot_page():
    con=db(); events=con.execute('''SELECT e.*,m.machine_code,m.name FROM sensor_events e JOIN machines m ON m.id=e.machine_id ORDER BY e.id DESC LIMIT 30''').fetchall(); machines=con.execute('SELECT * FROM machines').fetchall(); con.close(); return render_template('iot.html',events=events,machines=machines)


@app.route('/complaints',methods=['GET','POST'])
@login_required
def complaints():
    con=db(); user=current_user()
    if request.method=='POST':
        issue=request.form.get('issue','').strip(); details=request.form.get('details','').strip(); mid=request.form.get('machine_id') or None
        if issue:
            code=make_code('TKT'); con.execute('INSERT INTO complaints(ticket_code,user_id,machine_id,issue,details,created_at) VALUES(?,?,?,?,?,?)',(code,user['id'],mid,issue,details,datetime.now().isoformat(timespec='minutes'))); con.commit(); flash(f'Complaint submitted. Ticket: {code}','success')
        con.close(); return redirect(url_for('complaints'))
    if user['role']=='admin': rows=con.execute('''SELECT c.*,u.name,u.student_code,m.machine_code FROM complaints c JOIN users u ON u.id=c.user_id LEFT JOIN machines m ON m.id=c.machine_id ORDER BY c.id DESC''').fetchall()
    else: rows=con.execute('''SELECT c.*,m.machine_code FROM complaints c LEFT JOIN machines m ON m.id=c.machine_id WHERE c.user_id=? ORDER BY c.id DESC''',(user['id'],)).fetchall()
    machines=con.execute('SELECT * FROM machines').fetchall(); con.close(); return render_template('complaints.html',rows=rows,machines=machines)


@app.route('/complaint/<int:cid>/status',methods=['POST'])
@admin_required
def complaint_status(cid):
    status=request.form.get('status')
    if status in ['Pending','In Progress','Resolved']:
        con=db(); con.execute('UPDATE complaints SET status=? WHERE id=?',(status,cid)); con.commit(); con.close(); flash('Complaint status updated.','success')
    return redirect(url_for('complaints'))


@app.route('/api/analytics')
@admin_required
def analytics_api():
    con=db(); status=con.execute('SELECT status,COUNT(*) n FROM machines GROUP BY status').fetchall(); booking=con.execute('SELECT booking_date,COUNT(*) n FROM bookings GROUP BY booking_date ORDER BY booking_date DESC LIMIT 7').fetchall(); con.close()
    return jsonify({'machine_labels':[r['status'] for r in status],'machine_values':[r['n'] for r in status],'booking_labels':[r['booking_date'] for r in reversed(booking)],'booking_values':[r['n'] for r in reversed(booking)]})


@app.route('/profile')
@login_required
def profile():
    con=db(); user=con.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone(); con.close(); return render_template('profile.html',user=user)


@app.route('/health')
def health(): return jsonify({'status':'ok','application':'WashWise','database':os.path.exists(DB_PATH)})


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1',port=5000,debug=True)
