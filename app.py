from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify, send_file
from pymongo import MongoClient
import face_recognition
import pickle
from bson.binary import Binary
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import csv
from io import StringIO, BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import cv2
import threading
import time
import os
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# MongoDB Connection
client = MongoClient(config.MONGODB_CONNECTION_STRING)
db = client[config.DATABASE_NAME]

# Global variables for camera
camera_active = {}
camera_threads = {}
camera_source = config.CAMERA_INDEX  # Default camera source, can be overridden per company


def parse_camera_source(source):
    if isinstance(source, str):
        source = source.strip()
        if source.isdigit():
            return int(source)
    return source


def get_company_camera_source(company_id):
    company = db.companies.find_one({"_id": ObjectId(company_id)})
    if company and company.get("camera_source"):
        return parse_camera_source(company["camera_source"])
    return config.CAMERA_INDEX


def get_employee_info(name, comp_id):
    return db.employees.find_one({"name": name, "company_id": comp_id})


def create_attendance_record(employee, company_id, status="Present", detection_method="camera"):
    record = {
        "name": employee.get("name", "Unknown"),
        "employee_id": employee.get("employee_id", "N/A"),
        "department": employee.get("department", "N/A"),
        "company_id": company_id,
        "time": datetime.now(),
        "status": status,
        "detection_method": detection_method
    }
    db.attendance_logs.insert_one(record)
    return record


def load_employee_data(company_id=None):
    query = {"company_id": company_id} if company_id else {}
    employees = list(db.employees.find(query))
    known_encodings = []
    known_names = []

    for emp in employees:
        try:
            known_encodings.append(pickle.loads(emp['face_data']))
            known_names.append(emp['name'])
        except:
            continue

    return known_encodings, known_names


def camera_recognition_thread(company_id, source):
    print(f"🎥 Starting camera recognition thread for company {company_id}...")

    known_encodings, known_names = load_employee_data(company_id)
    cooldown = {}
    frame_count = 0

    try:
        cap = cv2.VideoCapture(parse_camera_source(source))
        if not cap.isOpened():
            print(f"❌ ERROR: Cannot open camera source '{source}' for company {company_id}!")
            camera_active[company_id] = False
            return

        print(f"✅ Camera opened successfully using source: {source} for company {company_id}")

        while camera_active.get(company_id, False):
            ret, frame = cap.read()
            if not ret:
                print(f"❌ ERROR: Cannot read frame from camera source '{source}' for company {company_id}!")
                break

            frame_count += 1
            # Skip frames for performance
            if frame_count % config.FRAME_SKIP != 0:
                continue

            # Resize for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Detect faces
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            if face_locations:
                print(f"👤 Detected {len(face_locations)} face(s) in frame {frame_count}")

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=config.FACE_TOLERANCE)

                if True in matches:
                    idx = matches.index(True)
                    name = known_names[idx]

                    # Check cooldown
                    current_time = time.time()
                    if name not in cooldown or (current_time - cooldown[name] > config.COOLDOWN_SECONDS):
                        today = datetime.now().date()
                        employee_info = get_employee_info(name, company_id) or {
                            "name": str(name),
                            "employee_id": "N/A",
                            "department": "N/A"
                        }
                        existing = db.attendance_logs.find_one({
                            "employee_id": employee_info.get("employee_id", "N/A"),
                            "company_id": company_id,
                            "time": {"$gte": datetime(today.year, today.month, today.day)}
                        })

                        if not existing:
                            create_attendance_record(employee_info, company_id, detection_method="camera")
                            cooldown[name] = current_time
                            print(f"✅ ATTENDANCE MARKED: {name} for Company {company_id} at {datetime.now().strftime('%H:%M:%S')}")
                        else:
                            print(f"ℹ️ {name} already marked present today")
                else:
                    print("⚠️ Unknown face detected - not adding new employee (only admin can add employees)")

            time.sleep(0.1)  # Small delay to prevent excessive CPU usage

    except Exception as e:
        print(f"❌ ERROR in camera thread: {str(e)}")
    finally:
        if 'cap' in locals():
            cap.release()
        print("📷 Camera thread stopped and resources released")
        camera_active[company_id] = False


def gen_frames():
    if 'company_id' not in session:
        return

    comp_id = str(session['company_id'])
    source = get_company_camera_source(comp_id)
    cap = cv2.VideoCapture(parse_camera_source(source))
    if not cap.isOpened():
        print(f"❌ Preview cannot open source '{source}' for company {comp_id}.")
        return

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()

@app.route('/video_feed')
def video_feed():
    if 'company_id' not in session:
        return redirect(url_for('login'))
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def home():
    if 'company_id' not in session:
        return redirect(url_for('login'))

    comp_id = str(session['company_id'])
    employees = list(db.employees.find({"company_id": comp_id}))
    today = datetime.now().date()
    logs = list(db.attendance_logs.find({
        "company_id": comp_id,
        "time": {"$gte": datetime(today.year, today.month, today.day)}
    }).sort("time", -1).limit(20))

    company = db.companies.find_one({"_id": ObjectId(comp_id)})
    company_camera_source = company.get("camera_source", config.CAMERA_INDEX) if company else config.CAMERA_INDEX
    company_camera_active = camera_active.get(comp_id, False)

    # Get today's attendance count and status for each employee
    today = datetime.now().date()
    today_logs = list(db.attendance_logs.find({
        "company_id": comp_id,
        "time": {"$gte": datetime(today.year, today.month, today.day)}
    }))

    present_ids = {log.get("employee_id") for log in today_logs if log.get("employee_id")}
    employee_status = []
    for emp in employees:
        emp_id = emp.get("employee_id", "N/A")
        status = "Present" if emp_id in present_ids else "Absent"
        employee_status.append({
            "name": emp.get("name", "Unknown"),
            "employee_id": emp_id,
            "department": emp.get("department", "N/A"),
            "status": status
        })

    # Get weekly attendance data for chart
    weekly_data = []
    for i in range(7):
        day = datetime.now() - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        count = db.attendance_logs.count_documents({
            "company_id": comp_id,
            "time": {"$gte": day_start, "$lt": day_end}
        })
        weekly_data.append({
            "date": day.strftime("%a"),
            "count": count
        })
    weekly_data.reverse()  # Oldest to newest

    present_count = len([e for e in employee_status if e["status"] == "Present"])
    absent_count = len(employee_status) - present_count

    return render_template('dashboard.html', employees=employees, logs=logs,
                           today_count=present_count,
                           absent_count=absent_count,
                           employee_status=employee_status,
                           camera_active=company_camera_active,
                           company_camera_source=company_camera_source,
                           weekly_data=weekly_data)
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        company = db.companies.find_one({"admin_email": email})

        if company and check_password_hash(company['password'], password):
            session['company_id'] = str(company['_id'])
            session['company_name'] = company['name']
            return redirect(url_for('home'))
        flash("Invalid Credentials!")
    return render_template('login.html')

@app.route('/register_company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = generate_password_hash(request.form.get('password'))

        if not db.companies.find_one({"admin_email": email}):
            db.companies.insert_one({
                "name": name,
                "admin_email": email,
                "password": password,
                "camera_source": config.CAMERA_INDEX
            })
            flash("Company registered successfully! Please login.")
            return redirect(url_for('login'))
        flash("Email already registered!")
    return render_template('register.html')

@app.route('/update_camera_source', methods=['POST'])
def update_camera_source():
    if 'company_id' not in session:
        return redirect(url_for('login'))

    source = request.form.get('camera_source', '').strip()
    if not source:
        flash("❌ Camera source cannot be empty.")
        return redirect(url_for('home'))

    comp_id = str(session['company_id'])
    db.companies.update_one({"_id": ObjectId(comp_id)}, {"$set": {"camera_source": source}})
    flash(f"✅ Camera/CCTV source updated to '{source}'. Start recognition to apply changes.")
    return redirect(url_for('home'))

@app.route('/add_employee', methods=['POST'])
def add_employee():
    if 'company_id' not in session:
        return redirect(url_for('login'))

    name = request.form.get('name')
    employee_id = request.form.get('employee_id')
    department = request.form.get('department')
    image_file = request.files.get('photo')

    if not all([name, employee_id, department, image_file]):
        flash("❌ All fields are required (Name, Employee ID, Department, Photo)!")
        return redirect(url_for('home'))

    try:
        print(f"📸 Processing photo for employee: {name}")

        # Load and process image
        img = face_recognition.load_image_file(image_file)
        encodings = face_recognition.face_encodings(img)

        if not encodings:
            flash("❌ No face detected in the image. Please upload a clear, front-facing photo!")
            return redirect(url_for('home'))

        if len(encodings) > 1:
            flash("⚠️ Multiple faces detected. Please upload a photo with only one person!")
            return redirect(url_for('home'))

        # Check if employee ID already exists
        comp_id = str(session['company_id'])
        existing = db.employees.find_one({
            "employee_id": employee_id,
            "company_id": comp_id
        })

        if existing:
            flash(f"❌ Employee ID '{employee_id}' already exists!")
            return redirect(url_for('home'))

        # Save employee data
        employee_data = {
            "name": name.strip(),
            "employee_id": employee_id.strip(),
            "department": department.strip(),
            "company_id": comp_id,
            "face_data": Binary(pickle.dumps(encodings[0])),
            "created_at": datetime.now(),
            "status": "active"
        }

        result = db.employees.insert_one(employee_data)

        if result.inserted_id:
            # Reload face data for recognition for current company only
            load_employee_data(comp_id)
            flash(f"✅ Employee '{name}' added successfully! Face data processed and ready for recognition.")
            print(f"✅ Employee added: {name} (ID: {employee_id})")
        else:
            flash("❌ Failed to save employee data!")

    except Exception as e:
        flash(f"❌ Error processing employee data: {str(e)}")
        print(f"❌ Error adding employee: {str(e)}")

    return redirect(url_for('home'))

@app.route('/start_camera')
def start_camera():
    if 'company_id' not in session:
        return redirect(url_for('login'))

    comp_id = str(session['company_id'])
    camera_source = get_company_camera_source(comp_id)

    if not camera_active.get(comp_id, False):
        try:
            camera_active[comp_id] = True
            camera_thread = threading.Thread(target=camera_recognition_thread, args=(comp_id, camera_source), name=f"CameraThread-{comp_id}")
            camera_thread.daemon = True
            camera_threads[comp_id] = camera_thread
            camera_thread.start()
            flash(f"✅ Camera started successfully using source '{camera_source}'! Face recognition is now active.")
            print(f"🚀 Camera recognition started for company {comp_id} with source {camera_source}")
        except Exception as e:
            camera_active[comp_id] = False
            flash(f"❌ Error starting camera: {str(e)}")
            print(f"❌ Error starting camera: {str(e)}")
    else:
        flash("ℹ️ Camera is already running for your company!")

    return redirect(url_for('home'))

@app.route('/stop_camera')
def stop_camera():
    if 'company_id' not in session:
        return redirect(url_for('login'))

    comp_id = str(session['company_id'])
    if camera_active.get(comp_id, False):
        camera_active[comp_id] = False
        thread = camera_threads.pop(comp_id, None)
        if thread and thread.is_alive():
            thread.join(timeout=1)
        flash("🛑 Camera stopped successfully!")
        print(f"🛑 Camera recognition stopped for company {comp_id}")
    else:
        flash("ℹ️ Camera is not running for your company!")

    return redirect(url_for('home'))

@app.route('/clear_today_attendance')
def clear_today_attendance():
    if 'company_id' not in session:
        return redirect(url_for('login'))

    comp_id = str(session['company_id'])
    today = datetime.now().date()
    result = db.attendance_logs.delete_many({
        "company_id": comp_id,
        "time": {"$gte": datetime(today.year, today.month, today.day)}
    })
    flash(f"🧹 Cleared {result.deleted_count} attendance records for today.")
    return redirect(url_for('home'))

@app.route('/clear_all_attendance')
def clear_all_attendance():
    if 'company_id' not in session:
        return redirect(url_for('login'))

    comp_id = str(session['company_id'])
    # Clear all attendance logs for this company
    attendance_result = db.attendance_logs.delete_many({"company_id": comp_id})
    # Clear all employees for this company
    employee_result = db.employees.delete_many({"company_id": comp_id})
    flash(f"🧹 Cleared {attendance_result.deleted_count} attendance records and {employee_result.deleted_count} employees for your company.")
    return redirect(url_for('home'))

@app.route('/reports')
def reports():
    if 'company_id' not in session:
        return redirect(url_for('login'))

    comp_id = str(session['company_id'])
    report_type = request.args.get('type', 'daily')

    if report_type == 'daily':
        today = datetime.now().date()
        logs = list(db.attendance_logs.find({
            "company_id": comp_id,
            "time": {"$gte": datetime(today.year, today.month, today.day)}
        }).sort("time", -1))
    elif report_type == 'weekly':
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        logs = list(db.attendance_logs.find({
            "company_id": comp_id,
            "time": {"$gte": week_start}
        }).sort("time", -1))
    elif report_type == 'monthly':
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        logs = list(db.attendance_logs.find({
            "company_id": comp_id,
            "time": {"$gte": month_start}
        }).sort("time", -1))

    return render_template('reports.html', logs=logs, report_type=report_type)

@app.route('/download_report/<report_type>')
def download_report(report_type):
    if 'company_id' not in session:
        return redirect(url_for('login'))

    comp_id = str(session['company_id'])

    if report_type == 'daily':
        today = datetime.now().date()
        logs = list(db.attendance_logs.find({
            "company_id": comp_id,
            "time": {"$gte": datetime(today.year, today.month, today.day)}
        }).sort("time", -1))
        filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.csv"
    elif report_type == 'weekly':
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        logs = list(db.attendance_logs.find({
            "company_id": comp_id,
            "time": {"$gte": week_start}
        }).sort("time", -1))
        filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.csv"
    elif report_type == 'monthly':
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        logs = list(db.attendance_logs.find({
            "company_id": comp_id,
            "time": {"$gte": month_start}
        }).sort("time", -1))
        filename = f"monthly_report_{datetime.now().strftime('%Y%m%d')}.csv"

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Employee Name', 'Employee ID', 'Department', 'Date', 'Time', 'Status'])

    for log in logs:
        employee = db.employees.find_one({"name": log['name'], "company_id": comp_id})
        emp_id = employee.get('employee_id', 'N/A') if employee else 'N/A'
        dept = employee.get('department', 'N/A') if employee else 'N/A'
        writer.writerow([
            log['name'],
            emp_id,
            dept,
            log['time'].strftime('%Y-%m-%d'),
            log['time'].strftime('%H:%M:%S'),
            log.get('status', 'Present')
        ])

    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv',
                   headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.route('/download_pdf/<report_type>')
def download_pdf(report_type):
    if 'company_id' not in session:
        return redirect(url_for('login'))

    comp_id = str(session['company_id'])

    if report_type == 'daily':
        today = datetime.now().date()
        logs = list(db.attendance_logs.find({
            "company_id": comp_id,
            "time": {"$gte": datetime(today.year, today.month, today.day)}
        }).sort("time", -1))
        title = f"Daily Attendance Report - {datetime.now().strftime('%Y-%m-%d')}"
    elif report_type == 'weekly':
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        logs = list(db.attendance_logs.find({
            "company_id": comp_id,
            "time": {"$gte": week_start}
        }).sort("time", -1))
        title = f"Weekly Attendance Report - {week_start.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}"
    elif report_type == 'monthly':
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        logs = list(db.attendance_logs.find({
            "company_id": comp_id,
            "time": {"$gte": month_start}
        }).sort("time", -1))
        title = f"Monthly Attendance Report - {datetime.now().strftime('%B %Y')}"

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))

    # Company info
    company = db.companies.find_one({"_id": ObjectId(comp_id)})
    if company:
        elements.append(Paragraph(f"Company: {company['name']}", styles['Normal']))
        elements.append(Spacer(1, 12))

    # Create table data
    data = [['Employee Name', 'Employee ID', 'Department', 'Date', 'Time', 'Status']]
    total_employees = db.employees.count_documents({"company_id": comp_id})
    present_count = len(logs)

    for log in logs:
        employee = db.employees.find_one({"name": log['name'], "company_id": comp_id})
        emp_id = employee.get('employee_id', 'N/A') if employee else 'N/A'
        dept = employee.get('department', 'N/A') if employee else 'N/A'
        data.append([
            log['name'],
            emp_id,
            dept,
            log['time'].strftime('%Y-%m-%d'),
            log['time'].strftime('%H:%M:%S'),
            log.get('status', 'Present')
        ])

    # Add summary
    elements.append(Paragraph(f"Total Employees: {total_employees}", styles['Normal']))
    elements.append(Paragraph(f"Present Today: {present_count}", styles['Normal']))
    elements.append(Paragraph(f"Absent Today: {total_employees - present_count}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.route('/delete_employee/<employee_id>')
def delete_employee(employee_id):
    if 'company_id' not in session:
        return redirect(url_for('login'))

    comp_id = str(session['company_id'])
    db.employees.delete_one({"_id": ObjectId(employee_id), "company_id": comp_id})
    db.attendance_logs.delete_many({"name": {"$regex": f"^{employee_id}"}, "company_id": comp_id})
    flash("Employee deleted successfully!")

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    comp_id = session.get('company_id')
    if comp_id and camera_active.get(comp_id, False):
        camera_active[comp_id] = False
        thread = camera_threads.pop(comp_id, None)
        if thread and thread.is_alive():
            thread.join(timeout=1)
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/camera_status')
def camera_status():
    if 'company_id' not in session:
        return jsonify({
            "active": False,
            "employees_loaded": 0,
            "camera_source": None,
            "last_updated": datetime.now().isoformat()
        })

    comp_id = str(session['company_id'])
    return jsonify({
        "active": camera_active.get(comp_id, False),
        "employees_loaded": db.employees.count_documents({"company_id": comp_id}),
        "camera_source": get_company_camera_source(comp_id),
        "last_updated": datetime.now().isoformat()
    })

@app.route('/test_camera')
def test_camera():
    if 'company_id' not in session:
        return redirect(url_for('login'))

    try:
        comp_id = str(session['company_id'])
        source = get_company_camera_source(comp_id)
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                flash(f"✅ Camera test successful for source '{source}'! Camera is working properly.")
            else:
                flash(f"❌ Camera opened but cannot read frames from source '{source}'. Check CCTV/stream settings.")
        else:
            flash(f"❌ Cannot access camera source '{source}'. Check camera permissions and connections.")
    except Exception as e:
        flash(f"❌ Camera test failed: {str(e)}")

    return redirect(url_for('home'))

if __name__ == '__main__':
    load_employee_data()
    app.run(debug=config.FLASK_DEBUG, host=config.FLASK_HOST, port=config.FLASK_PORT)