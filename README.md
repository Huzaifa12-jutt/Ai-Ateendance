# AI-Powered Attendance System

A complete AI-powered attendance tracking system using face recognition, built with Flask, OpenCV, and MongoDB.

## Features

- ✅ **Face Recognition**: Real-time face detection and recognition
- ✅ **Web Dashboard**: Modern, responsive admin interface
- ✅ **Multi-Company Support**: SaaS architecture for multiple companies
- ✅ **Camera Integration**: Live camera monitoring with CCTV support
- ✅ **Reports**: Daily, Weekly, Monthly reports in CSV and PDF
- ✅ **Employee Management**: Add, view, and manage employees
- ✅ **Real-time Monitoring**: Live attendance marking
- ✅ **Secure Authentication**: Password-protected admin access

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```bash
python setup_db.py
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access the System
- Open browser: `http://localhost:5000`
- Register your company
- Login with admin credentials
- Add employees with photos
- Start camera recognition

## System Architecture

```
Camera → Face Detection → Face Recognition → Database → Reports
   ↓         ↓              ↓              ↓         ↓
OpenCV   face-recognition  Compare       MongoDB   CSV/PDF
```

## API Endpoints

- `GET /` - Dashboard
- `POST /login` - Admin login
- `POST /register_company` - Company registration
- `POST /add_employee` - Add new employee
- `GET /start_camera` - Start face recognition
- `GET /stop_camera` - Stop face recognition
- `GET /reports` - View reports
- `GET /download_report/<type>` - Download CSV reports
- `GET /download_pdf/<type>` - Download PDF reports

## Database Collections

- `companies` - Company/admin information
- `employees` - Employee data with face encodings
- `attendance_logs` - Attendance records

## Camera Setup

### For USB Camera
- Connect USB camera to computer
- System automatically detects (usually camera index 0)

### For IP Camera/CCTV
- Get RTSP stream URL from camera
- Add URL to configuration
- Example: `rtsp://192.168.1.100:554/stream`

## Report Types

1. **Daily Report**: Today's attendance
2. **Weekly Report**: Current week attendance
3. **Monthly Report**: Current month attendance

## Security Features

- Password hashing with bcrypt
- Session-based authentication
- Company isolation (multi-tenant)
- Face recognition with tolerance settings

## Troubleshooting

### Camera Not Working
- Check camera connection
- Verify camera drivers
- Test with different camera index

### Face Not Recognized
- Ensure good lighting
- Clear face photos during registration
- Adjust camera angle
- Check face detection tolerance

### Database Connection Issues
- Verify MongoDB connection string
- Check network connectivity
- Ensure MongoDB Atlas cluster is running

## Performance Tips

- Use SSD for better performance
- Ensure minimum 4GB RAM
- Good lighting for accurate recognition
- Regular camera angle adjustments

## Support

For technical support or customization:
- Email: support@aiattendance.com
- WhatsApp: +92-XXX-XXXXXXX

---

**Version**: 1.0
**Last Updated**: May 2026
**Developed by**: AI Solutions Team