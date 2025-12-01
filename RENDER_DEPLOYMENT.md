# Render Deployment Guide

## Quick Setup (5 minutes)

### 1. Create Render Account
- Go to https://render.com
- Sign up with your GitHub account (free)

### 2. Create PostgreSQL Database
- Click "New +" → "PostgreSQL"
- Name: `qr-attendance-db`
- Choose Free tier
- Click "Create Database"
- **Copy the "Internal Database URL"** (you'll need this)

### 3. Create Web Service
- Click "New +" → "Web Service"
- Connect your GitHub repository: `Eau-Qr-Attendence`
- Configure:
  - **Name**: `qr-attendance`
  - **Environment**: `Python 3`
  - **Build Command**: `./build_render.sh`
  - **Start Command**: `gunicorn qr_attendance.wsgi:application`
  - **Plan**: Free

### 4. Add Environment Variables
Click "Advanced" and add these environment variables:

```
SECRET_KEY=your-secret-key-here-make-it-long-and-random
DEBUG=False
DATABASE_URL=[paste the Internal Database URL from step 2]
ALLOWED_HOSTS=.onrender.com
CSRF_TRUSTED_ORIGINS=https://qr-attendance.onrender.com
```

### 5. Deploy
- Click "Create Web Service"
- Wait 5-10 minutes for first deployment
- Your app will be live at: `https://qr-attendance.onrender.com`

### 6. Create Admin User
After deployment, go to the Render dashboard:
- Click on your web service
- Go to "Shell" tab
- Run: `python manage.py createsuperuser`
- Follow the prompts

## Done! 🎉

Your app will be live with:
- ✅ PostgreSQL database (automatic backups)
- ✅ HTTPS enabled
- ✅ Auto-deploy on git push
- ✅ Free tier available

---

## Alternative: Railway (Even Easier)

If you prefer Railway:

1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect Django and set everything up
6. Add environment variables in the dashboard
7. Done!

Railway automatically provisions a PostgreSQL database for you.
