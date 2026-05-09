#!/usr/bin/env python3
"""
AI Attendance System - Test Script
Tests face recognition functionality
"""

import cv2
import face_recognition
import numpy as np
from pymongo import MongoClient
import pickle
from datetime import datetime
import time

# MongoDB Connection
CONNECTION_STRING = "mongodb+srv://admin:12345678910@cluster0.seddwbf.mongodb.net/?appName=Cluster0"
client = MongoClient(CONNECTION_STRING)
db = client["Aria_SaaS_Attendance"]

def test_face_recognition():
    """Test face recognition with camera"""
    print("🔄 LOADING EMPLOYEE DATA...")

    # Load all employees
    employees = list(db.employees.find())
    if not employees:
        print("❌ No employees found. Please add employees first via web interface.")
        return

    known_encodings = []
    known_names = []
    known_comp_ids = []

    for emp in employees:
        try:
            known_encodings.append(pickle.loads(emp['face_data']))
            known_names.append(emp['name'])
            known_comp_ids.append(str(emp['company_id']))
            print(f"✅ Loaded: {emp['name']}")
        except Exception as e:
            print(f"❌ Error loading {emp['name']}: {e}")

    if not known_encodings:
        print("❌ No valid face data found.")
        return

    print(f"\n🚀 STARTING CAMERA TEST... ({len(known_names)} employees loaded)")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access camera. Check camera connection.")
        return

    cooldown = {}
    test_duration = 30  # Test for 30 seconds

    start_time = time.time()

    while time.time() - start_time < test_duration:
        ret, frame = cap.read()
        if not ret:
            print("❌ Camera read error")
            break

        # Resize for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)

            if True in matches:
                idx = matches.index(True)
                name = known_names[idx]
                comp_id = known_comp_ids[idx]

                current_time = time.time()
                if name not in cooldown or (current_time - cooldown[name] > 10):  # 10 second cooldown for testing
                    print(f"✅ RECOGNIZED: {name} (Company: {comp_id}) at {datetime.now().strftime('%H:%M:%S')}")

                    # Check if already marked today
                    today = datetime.now().date()
                    existing = db.attendance_logs.find_one({
                        "name": str(name),
                        "company_id": str(comp_id),
                        "time": {"$gte": datetime(today.year, today.month, today.day)}
                    })

                    if not existing:
                        # Mark attendance
                        db.attendance_logs.insert_one({
                            "name": str(name),
                            "company_id": str(comp_id),
                            "time": datetime.now(),
                            "status": "Present"
                        })
                        print(f"✅ ATTENDANCE MARKED for {name}")
                        cooldown[name] = current_time
                    else:
                        print(f"ℹ️ {name} already marked present today")

        # Display camera feed
        cv2.putText(frame, f"Testing... {int(test_duration - (time.time() - start_time))}s left", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Employees: {len(known_names)} | Faces detected: {len(face_locations)}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow('AI Attendance System - TEST MODE', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    print("🎯 TEST COMPLETED!")
    print(f"📊 Summary:")
    print(f"   - Employees loaded: {len(known_names)}")
    print(f"   - Test duration: {test_duration} seconds")
    print(f"   - Check database for attendance logs")

def test_database_connection():
    """Test MongoDB connection"""
    try:
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")

        # Check collections
        collections = db.list_collection_names()
        print(f"✅ Collections found: {collections}")

        # Count documents
        companies = db.companies.count_documents({})
        employees = db.employees.count_documents({})
        logs = db.attendance_logs.count_documents({})

        print(f"📊 Database Stats:")
        print(f"   - Companies: {companies}")
        print(f"   - Employees: {employees}")
        print(f"   - Attendance Logs: {logs}")

        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🤖 AI ATTENDANCE SYSTEM - TEST SUITE")
    print("=" * 50)

    # Test database first
    if not test_database_connection():
        print("❌ Database test failed. Cannot proceed.")
        exit(1)

    print("\n" + "=" * 50)

    # Ask user what to test
    print("Select test option:")
    print("1. Face Recognition Test (30 seconds)")
    print("2. Exit")

    choice = input("Enter choice (1-2): ").strip()

    if choice == "1":
        print("\n" + "=" * 50)
        test_face_recognition()
    else:
        print("👋 Goodbye!")

    print("\n" + "=" * 50)
    print("Test completed. Check the web interface at http://localhost:5000")