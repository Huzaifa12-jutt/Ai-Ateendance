#!/usr/bin/env python3
"""
Camera Test Script for AI Attendance System
Tests camera functionality and face detection
"""

import cv2
import sys
import time

def test_camera_basic():
    """Basic camera test"""
    print("🔍 Testing basic camera functionality...")

    try:
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("❌ Cannot open camera!")
            return False

        print("✅ Camera opened successfully")

        # Test reading a few frames
        for i in range(5):
            ret, frame = cap.read()
            if not ret:
                print(f"❌ Cannot read frame {i+1}")
                cap.release()
                return False
            print(f"✅ Frame {i+1} read successfully (size: {frame.shape})")
            time.sleep(0.1)

        cap.release()
        print("✅ Basic camera test passed!")
        return True

    except Exception as e:
        print(f"❌ Camera test failed: {str(e)}")
        return False

def test_face_detection():
    """Test face detection in camera feed"""
    print("\n🔍 Testing face detection...")

    try:
        import face_recognition
        print("✅ face_recognition library loaded")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera for face detection test")
            return False

        print("📹 Testing face detection for 5 seconds...")
        print("Please look at the camera...")

        start_time = time.time()
        faces_detected = 0

        while time.time() - start_time < 5:
            ret, frame = cap.read()
            if not ret:
                continue

            # Convert to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect faces
            face_locations = face_recognition.face_locations(rgb_frame)

            if face_locations:
                faces_detected += 1
                print(f"👤 Face detected! ({len(face_locations)} face(s))")

            time.sleep(0.5)  # Check every half second

        cap.release()

        if faces_detected > 0:
            print(f"✅ Face detection test passed! Detected faces {faces_detected} times")
            return True
        else:
            print("⚠️ No faces detected. Make sure you're in front of the camera with good lighting")
            return False

    except ImportError:
        print("❌ face_recognition library not found. Please run: pip install face-recognition")
        return False
    except Exception as e:
        print(f"❌ Face detection test failed: {str(e)}")
        return False

def main():
    print("🤖 AI ATTENDANCE SYSTEM - CAMERA TEST")
    print("=" * 50)

    # Test 1: Basic camera
    if not test_camera_basic():
        print("\n❌ Camera test failed. Please check:")
        print("   - Camera is not being used by another application")
        print("   - Camera drivers are installed")
        print("   - Camera permissions are granted")
        sys.exit(1)

    # Test 2: Face detection
    if not test_face_detection():
        print("\n⚠️ Face detection test inconclusive. This might be normal if no one is in front of camera.")
        print("   - Try running the test again while looking at the camera")
        print("   - Ensure good lighting")
        print("   - Make sure your face is clearly visible")

    print("\n" + "=" * 50)
    print("🎯 Camera test completed!")
    print("If both tests passed, your camera is ready for the attendance system.")
    print("Run 'python app.py' to start the web interface.")

if __name__ == "__main__":
    main()