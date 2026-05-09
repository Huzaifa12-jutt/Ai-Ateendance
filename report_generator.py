# Report Generation Module
# Handles CSV and PDF report generation

import pandas as pd
import os
from datetime import datetime, timedelta
from pymongo import MongoClient

# MongoDB Connection
CONNECTION_STRING = "mongodb+srv://admin:12345678910@cluster0.seddwbf.mongodb.net/?appName=Cluster0"
client = MongoClient(CONNECTION_STRING)
db = client["Aria_SaaS_Attendance"]

def generate_daily_report(company_id, date=None):
    """Generate daily attendance report"""
    if date is None:
        date = datetime.now().date()

    start_datetime = datetime(date.year, date.month, date.day)
    end_datetime = start_datetime + timedelta(days=1)

    logs = list(db.attendance_logs.find({
        "company_id": str(company_id),
        "time": {"$gte": start_datetime, "$lt": end_datetime}
    }).sort("time", 1))

    return logs

def generate_weekly_report(company_id, week_start=None):
    """Generate weekly attendance report"""
    if week_start is None:
        # Get current week start (Monday)
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())

    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)

    logs = list(db.attendance_logs.find({
        "company_id": str(company_id),
        "time": {"$gte": week_start, "$lt": week_end}
    }).sort("time", 1))

    return logs

def generate_monthly_report(company_id, month=None, year=None):
    """Generate monthly attendance report"""
    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year

    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)

    logs = list(db.attendance_logs.find({
        "company_id": str(company_id),
        "time": {"$gte": month_start, "$lt": month_end}
    }).sort("time", 1))

    return logs

def get_attendance_summary(company_id, logs):
    """Get attendance summary statistics"""
    total_employees = db.employees.count_documents({"company_id": str(company_id)})
    present_count = len(logs)

    # Get unique employees who attended
    unique_employees = set()
    for log in logs:
        unique_employees.add(log['name'])

    unique_present = len(unique_employees)
    absent_count = total_employees - unique_present

    return {
        'total_employees': total_employees,
        'present_count': unique_present,
        'absent_count': absent_count,
        'attendance_rate': round((unique_present / total_employees * 100), 2) if total_employees > 0 else 0
    }

print('Report Generator Module Ready ✅')