# AI Attendance System Configuration
# Edit these settings according to your requirements

# Camera Settings
CAMERA_INDEX = 0  # 0 for default laptop camera, 1 for external camera
# For IP Camera/CCTV, use: "rtsp://192.168.1.100:554/stream"

# Face Recognition Settings
FACE_TOLERANCE = 0.45  # Lower = more strict, Higher = more lenient (0.4-0.6 recommended)
FRAME_SKIP = 1  # Process every frame for better detection (set to 2 for performance)

# Attendance Settings
COOLDOWN_SECONDS = 30  # Minimum seconds between attendance marks for same person
WORKING_HOURS_START = 9  # Work start hour (24-hour format)
WORKING_HOURS_END = 18  # Work end hour (24-hour format)

# Database Settings (MongoDB Atlas)
MONGODB_CONNECTION_STRING = "mongodb+srv://admin:12345678910@cluster0.seddwbf.mongodb.net/?appName=Cluster0"
DATABASE_NAME = "Aria_SaaS_Attendance"

# Flask Settings
FLASK_HOST = "0.0.0.0"  # 0.0.0.0 for all interfaces, 127.0.0.1 for localhost only
FLASK_PORT = 5000
FLASK_DEBUG = True  # Set to False in production

# Report Settings
REPORTS_FOLDER = "reports"
UPLOADS_FOLDER = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size

# Security Settings
SECRET_KEY = "aria_pro_786_secure"  # Change this in production
SESSION_TIMEOUT = 3600  # 1 hour in seconds

# Logging Settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "attendance_system.log"