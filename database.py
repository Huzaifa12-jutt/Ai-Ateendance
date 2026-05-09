import pymongo
from datetime import datetime

# Cloud Connection String
CONNECTION_STRING = "mongodb+srv://admin:12345678910@cluster0.seddwbf.mongodb.net/?appName=Cluster0"

def connect_to_db():
    try:
        client = pymongo.MongoClient(CONNECTION_STRING, serverSelectionTimeoutMS=5000)
        # Database ka naam bilkul sahi hona chahiye
        db = client["AriaAttendance"] 
        return db
    except Exception as e:
        print(f"❌ Cloud Connection Error: {e}")
        return None

def mark_attendance(employee_name):
    db = connect_to_db()
    if db is not None:
        attendance_col = db["logs"]
        
        # Aaj ki date nikalna
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        # Check karna ke kya aaj is bande ki attendance lag chuki hai?
        already_exists = attendance_col.find_one({
            "name": employee_name,
            "time": {"$regex": f"^{today_date}"}
        })
        
        if not already_exists:
            entry = {
                "name": employee_name,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Present"
            }
            attendance_col.insert_one(entry)
            print(f"✅ Success! New attendance marked for: {employee_name}")
        else:
            print(f"ℹ️ {employee_name} is already marked for today.")
    else:
        print("❌ Cloud connection failed.")