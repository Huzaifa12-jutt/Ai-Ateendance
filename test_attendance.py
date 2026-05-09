import cv2
import face_recognition
import numpy as np
from pymongo import MongoClient
import pickle
from datetime import datetime
import time

# Connection
client = MongoClient("mongodb+srv://admin:12345678910@cluster0.seddwbf.mongodb.net/")
db = client["Aria_SaaS_Attendance"]

def run_recognition():
    print("🔄 SYNCING: Loading fresh data from Cloud...")
    employees = list(db.employees.find())
    
    if not employees:
        print("❌ ERROR: No employees registered. Register on Dashboard first.")
        return

    known_encodings = []
    known_names = []
    known_comp_ids = []

    for emp in employees:
        known_encodings.append(pickle.loads(emp['face_data']))
        known_names.append(emp['name'])
        # Ensure company_id is a plain string
        known_comp_ids.append(str(emp['company_id']))

    cap = cv2.VideoCapture(0)
    cooldown = {} 

    print("🚀 CAMERA ACTIVE: Recognition started...")

    while True:
        ret, frame = cap.read()
        if not ret: break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            
            if True in matches:
                idx = matches.index(True)
                name = known_names[idx]
                comp_id = known_comp_ids[idx]

                # 20 second cooldown
                if name not in cooldown or (time.time() - cooldown[name] > 20):
                    # SAVE TO DB
                    db.attendance_logs.insert_one({
                        "name": str(name),
                        "company_id": str(comp_id), # Clean String ID
                        "time": datetime.now(),
                        "status": "Present"
                    })
                    cooldown[name] = time.time()
                    print(f"✅ LOGGED: {name} for Company {comp_id}")

        cv2.imshow('Scanner - Press Q to Quit', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_recognition()