# QR-Based Student Attendance System

A comprehensive Django application that enables teachers to create attendance sessions with time-limited QR codes that students scan to mark their presence. The system prevents duplicate scans, provides role-based access control, and offers robust reporting with CSV export capabilities.

## Features

- ✅ **QR Code Generation**: Unique, time-limited QR codes for each attendance session
- ✅ **Mobile-First Design**: Responsive interface optimized for mobile devices
- ✅ **Duplicate Prevention**: Database-level constraints prevent duplicate attendance
- ✅ **Role-Based Access**: Teacher/admin-only session creation with proper permissions
- ✅ **HTML5 QR Scanner**: In-browser camera scanning with manual entry fallback
- ✅ **Real-Time Updates**: Live attendance count with auto-refresh
- ✅ **CSV Export**: Download attendance reports with flexible filtering
- ✅ **Session Management**: Time-limited sessions with manual close option
- ✅ **Comprehensive Reports**: Filter by date, session, student with quick presets
- ✅ **REST API**: Full API for programmatic access
- ✅ **Security**: CSRF protection, token expiration, IP logging

## Tech Stack

- **Backend**: Django 4.2, Django REST Framework
- **Frontend**: Bootstrap 5, HTML5 QR Code Scanner
- **Database**: SQLite (development), PostgreSQL/MySQL (production)
- **QR Generation**: python-qrcode with PIL

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or navigate to the project directory**:
   ```bash
   cd "c:\Users\yousu\OneDrive\Desktop\Qr Attendence"
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Update the values as needed (SECRET_KEY, DEBUG, etc.)

5. **Run database migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser** (admin account):
   ```bash
   python manage.py createsuperuser
   ```

7. **Load sample data** (optional):
   ```bash
   python manage.py loaddata fixtures/sample_data.json
   ```
   
   Sample credentials:
   - Admin: `admin` / `admin` (change in production!)
   - Teacher: `teacher1` / `teacher1`

8. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

9. **Access the application**:
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/
   - API: http://127.0.0.1:8000/api/

## Usage Guide

### For Teachers

1. **Login** at `/admin/login/` with your credentials
2. **Create a Session**:
   - Go to the Teacher Dashboard
   - Click "Create New Session"
   - Fill in session details (title, classroom, date)
   - Click "Create Session"
3. **Display QR Code**:
   - Click "View QR Code" on the session
   - Display the QR code to students (projector/screen)
   - Monitor live attendance count
4. **Close Session**:
   - Click "Close Session" when done
   - Or let it expire automatically after 2 hours

### For Students

1. **Scan QR Code**:
   - Open the QR scan URL on your phone
   - Allow camera access
   - Click "Start Camera" and scan the QR code
   - OR enter your Student ID manually
2. **Confirmation**:
   - You'll see a success message
   - Duplicate scans are prevented

### Generating Reports

1. Go to **Reports** page
2. Apply filters:
   - Select specific session
   - Choose date range (or use quick filters: Today/Week/Month)
   - Filter by student
3. Click **Export to CSV** to download

## API Documentation

### Authentication

Most endpoints require authentication. Use Django session authentication or token-based auth.

### Endpoints

#### Sessions

- `GET /api/sessions/` - List all sessions
- `POST /api/sessions/` - Create new session (teacher/admin only)
- `GET /api/sessions/{id}/` - Get session details
- `POST /api/sessions/{id}/close/` - Close session
- `GET /api/sessions/{id}/qr_code/` - Get QR code image
- `GET /api/sessions/{id}/attendance/` - Get attendance for session

#### Attendance

- `GET /api/attendance/` - List attendance records
  - Query params: `session`, `student`, `start_date`, `end_date`
- `GET /api/attendance/export_csv/` - Export to CSV
- `POST /scan/{token}/` - Mark attendance (public endpoint)

#### Students & Classrooms

- `GET /api/students/` - List students
- `GET /api/classrooms/` - List classrooms
- `GET /api/teachers/` - List teachers

### Example API Calls

**Create a session**:
```bash
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{
    "title": "Morning Lecture",
    "classroom": 1,
    "session_date": "2025-12-01"
  }'
```

**Mark attendance**:
```bash
curl -X POST http://localhost:8000/scan/{TOKEN}/ \
  -d "student_id=STU001"
```

## Running Tests

Run the comprehensive test suite:

```bash
# Run all tests
python manage.py test attendance

# Run specific test file
python manage.py test attendance.tests.test_models

# Run with verbosity
python manage.py test attendance --verbosity=2

# Run with coverage (install coverage first: pip install coverage)
coverage run --source='attendance' manage.py test attendance
coverage report
```

## Deployment

### Production Checklist

1. **Environment Variables**:
   - Set `DEBUG=False`
   - Generate strong `SECRET_KEY`
   - Configure `ALLOWED_HOSTS`

2. **Database**:
   - Switch to PostgreSQL or MySQL
   - Update `DATABASE_URL` in `.env`

3. **Static Files**:
   ```bash
   python manage.py collectstatic
   ```

4. **Security**:
   - Enable HTTPS
   - Configure CORS properly
   - Set up rate limiting
   - Regular backups

### Deployment Options

#### Heroku

```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set DEBUG=False

# Deploy
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

#### Railway

1. Connect your GitHub repository
2. Add PostgreSQL database
3. Set environment variables
4. Deploy automatically

#### VPS (Ubuntu)

1. Install dependencies: Python, PostgreSQL, Nginx, Gunicorn
2. Clone repository
3. Set up virtual environment
4. Configure Gunicorn and Nginx
5. Set up systemd service
6. Enable SSL with Let's Encrypt

## Project Structure

```
qr_attendance/
├── attendance/              # Main Django app
│   ├── models.py           # Database models
│   ├── views.py            # API and template views
│   ├── serializers.py      # DRF serializers
│   ├── permissions.py      # Custom permissions
│   ├── utils.py            # Utility functions
│   ├── admin.py            # Admin configuration
│   ├── urls.py             # App URL routing
│   └── tests/              # Test suite
│       ├── test_models.py
│       ├── test_views.py
│       └── test_utils.py
├── qr_attendance/          # Project settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL routing
│   └── wsgi.py
├── templates/              # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── teacher_dashboard.html
│   ├── session_qr.html
│   ├── scan_page.html
│   └── reports.html
├── static/                 # Static files
│   ├── css/
│   │   └── styles.css
│   └── js/
├── fixtures/               # Sample data
│   └── sample_data.json
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .gitignore
└── README.md
```

## Security Considerations

- **Token Expiration**: Sessions expire after 2 hours (configurable)
- **Duplicate Prevention**: Database constraints prevent duplicate attendance
- **CSRF Protection**: All forms protected with CSRF tokens
- **IP Logging**: Track IP addresses for audit trail
- **Permission Checks**: Role-based access for session management
- **Input Validation**: All inputs validated and sanitized

## Troubleshooting

### Common Issues

**QR Scanner not working**:
- Ensure HTTPS is enabled (camera requires secure context)
- Check browser camera permissions
- Use manual entry as fallback

**Database errors**:
- Run migrations: `python manage.py migrate`
- Check database connection in `.env`

**Static files not loading**:
- Run `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATIC_URL` settings

**Permission denied errors**:
- Ensure user has teacher profile or is staff/admin
- Check `IsTeacherOrAdmin` permission class

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Contact: admin@example.com

## Changelog

### Version 1.0.0 (2025-12-01)
- Initial release
- QR code generation and scanning
- Session management
- Attendance tracking with duplicate prevention
- CSV export
- Mobile-responsive UI
- Comprehensive test suite
