import pymongo

# Cloud Connection String
CONNECTION_STRING = "mongodb+srv://admin:12345678910@cluster0.seddwbf.mongodb.net/?appName=Cluster0"

def initialize_pro_database():
    try:
        client = pymongo.MongoClient(CONNECTION_STRING)
        # Naya Professional Database Name
        db = client["Aria_SaaS_Attendance"]
        
        # 1. Companies Collection (Table)
        # Ismein har company ka admin aur timings hongi
        if "companies" not in db.list_collection_names():
            db.create_collection("companies")
            print("✅ 'companies' collection created.")

        # 2. Employees Collection
        # Ismein face data aur company link hoga
        if "employees" not in db.list_collection_names():
            db.create_collection("employees")
            print("✅ 'employees' collection created.")

        # 3. Attendance Logs Collection
        # Ismein daily attendance records honge
        if "attendance_logs" not in db.list_collection_names():
            db.create_collection("attendance_logs")
            print("✅ 'attendance_logs' collection created.")

        print("\n🚀 PRO Database Structure is Ready!")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")

if __name__ == "__main__":
    initialize_pro_database()