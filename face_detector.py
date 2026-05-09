import cv2
import face_recognition
import os
import numpy as np
from database import mark_attendance

# 1. Load Known Faces
known_face_encodings = []
known_face_names = []

def load_known_faces():
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        print("Uploads folder created. Please add photos!")
        return

    for filename in os.listdir("uploads"):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            image = face_recognition.load_image_file(f"uploads/{filename}")
            encodings = face_recognition.face_encodings(image)
            if len(encodings) > 0:
                known_face_encodings.append(encodings[0])
                known_face_names.append(filename.split(".")[0])
    print(f"Loaded {len(known_face_names)} faces from uploads.")

# 2. Start Camera and Recognize
def start_recognition():
    video_capture = cv2.VideoCapture(0) 
    load_known_faces()

    print("Camera starting... Press 'q' to stop.")
    
    # Taake har frame par database update na ho (thori dair baad ho)
    already_marked = []

    while True:
        ret, frame = video_capture.read()
        if not ret: break
        
        # Speed fast karne ke liye resize
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                
                # Agar is session mein abhi attendance nahi lagi toh lagayein
                if name not in already_marked:
                    mark_attendance(name)
                    already_marked.append(name)

            print(f"Detected: {name}")

        cv2.imshow('Aria AI Attendance System', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_recognition()