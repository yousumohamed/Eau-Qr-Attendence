# Student Login System - Complete Guide

## Overview
The system now supports **Student Login** with passwords and a dedicated Student Dashboard!

---

## 1. How to Create Students

### Method 1: Via Admin Panel (Recommended)

1. **Log in to Admin Panel**: Go to `http://127.0.0.1:8000/admin/` as `admin`/`admin`

2. **Create a User Account First**:
   - Click **"Users"** under "Authentication and Authorization"
   - Click **"+ Add User"**
   - Enter:
     - **Username**: e.g., `john_doe`
     - **Password**: e.g., `student123` (you set this!)
   - Click **"Save"**

3. **Create Student Profile**:
   - Go to **"Students"** under "Attendance"
   - Click **"+ Add Student"**
   - Fill in:
     - **User**: Select the user you just created (e.g., `john_doe`)
     - **Student ID**: e.g., `STU001`
     - **Name**: e.g., `John Doe`
     - **Email**: e.g., `john@example.com`
     - **Photo**: (Optional) Upload a profile picture
     - **Enrollment Date**: Select date
     - **Is Active**: Check this box
   - Click **"Save"**

### Method 2: Via Django Shell (Advanced)

```python
python manage.py shell

from django.contrib.auth.models import User
from attendance.models import Student

# Create user
user = User.objects.create_user(
    username='jane_doe',
    password='student456',  # This is the password!
    email='jane@example.com',
    first_name='Jane',
    last_name='Doe'
)

# Create student profile
student = Student.objects.create(
    user=user,
    student_id='STU002',
    name='Jane Doe',
    email='jane@example.com',
    enrollment_date='2025-01-01',
    is_active=True
)
```

---

## 2. Student Passwords

**Important**: Student passwords are set when you create the **User account** (Step 2 in Method 1 above).

- **Where to set**: In the Admin Panel when creating the User
- **How to change**: 
  1. Go to Admin Panel → Users
  2. Click on the student's username
  3. Click **"Change password"** link
  4. Enter new password twice
  5. Click **"Save"**

**Default Password**: There is NO default password. You must set it manually when creating each user.

---

## 3. Student Dashboard

### What Students See:
- **Profile Card**: Name, Student ID, and photo
- **Stats**: Total classes attended and attendance percentage
- **Recent Attendance**: List of last 10 sessions they attended
- **Quick Scan Button**: Link to scan QR codes

### How Students Access It:
1. Go to `http://127.0.0.1:8000/login/`
2. Enter their **username** and **password**
3. They will be automatically redirected to their dashboard

### Direct URL:
- `http://127.0.0.1:8000/student/`

---

## User Types Summary

| User Type | Login URL | Dashboard | Can Do |
|-----------|-----------|-----------|--------|
| **Admin** | `/login/` | Teacher Dashboard + Admin Panel | Everything |
| **Teacher** | `/login/` | Teacher Dashboard | Create sessions, view reports |
| **Student** | `/login/` | Student Dashboard | View own attendance |

---

## Quick Start Example

### Create Your First Student:

1. **Login as admin**: `http://127.0.0.1:8000/admin/`
2. **Create User**:
   - Username: `alice`
   - Password: `alice123`
3. **Create Student**:
   - User: `alice`
   - Student ID: `STU100`
   - Name: `Alice Smith`
   - Email: `alice@school.com`
4. **Test Login**:
   - Go to `http://127.0.0.1:8000/login/`
   - Login as `alice` / `alice123`
   - You should see the Student Dashboard!

---

## Notes

- **Old Students**: Existing students (created before this update) do NOT have user accounts. You need to create User accounts for them if you want them to log in.
- **Scanning**: Students can still scan QR codes WITHOUT logging in (just enter Student ID).
- **Photos**: Upload student photos in the Admin Panel to make the dashboard look better!

---

## Troubleshooting

**Q: Student can't log in?**
- Check that you created BOTH a User account AND a Student profile
- Verify the User is linked to the Student (check "User" field in Student)

**Q: Student sees "No student profile found"?**
- The User account exists but no Student profile is linked
- Create a Student profile and select this User

**Q: How do I reset a student's password?**
- Admin Panel → Users → Click username → "Change password"
