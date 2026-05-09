from pymongo import MongoClient

# MongoDB se connect karein
# (Yahan wahi link dalein jo database.py mein hai)
client = MongoClient("mongodb://localhost:27017/") 
db = client["AttendanceSystem"]
collection = db["attendance"]

# Saara data nikaalein
print("--- Database mein mojood Attendance Records ---")
records = collection.find()

count = 0
for data in records:
    print(f"Naam: {data['name']} | Time: {data['time']} | Status: {data['status']}")
    count += 1

if count == 0:
    print("Database khali hai! Abhi tak koi attendance nahi lagi.")
else:
    print(f"--- Total Records Found: {count} ---")