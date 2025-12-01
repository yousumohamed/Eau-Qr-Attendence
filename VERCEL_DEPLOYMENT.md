# Vercel Deployment Guide

## Prerequisites
- A Vercel account
- Git repository connected to Vercel

## Environment Variables to Set in Vercel

Go to your Vercel project settings → Environment Variables and add:

```
SECRET_KEY=your-production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=.vercel.app,your-custom-domain.com
CSRF_TRUSTED_ORIGINS=https://your-app.vercel.app,https://your-custom-domain.com
SESSION_EXPIRY_HOURS=2
```

### Optional (for PostgreSQL database):
```
DATABASE_URL=postgresql://user:password@host:port/database
```

## Deployment Steps

1. **Push your code to GitHub/GitLab/Bitbucket**
   ```bash
   git add .
   git commit -m "Configure for Vercel deployment"
   git push
   ```

2. **Import Project in Vercel**
   - Go to https://vercel.com/new
   - Import your repository
   - Vercel will auto-detect the framework

3. **Configure Environment Variables**
   - Add all the environment variables listed above
   - Make sure to set `DEBUG=False` for production

4. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete

## Important Notes

- **Database**: By default, the app uses SQLite in development. For production on Vercel, you should use a PostgreSQL database (like Vercel Postgres, Supabase, or Neon).
- **Static Files**: WhiteNoise is configured to serve static files efficiently.
- **Media Files**: For user uploads, consider using cloud storage (AWS S3, Cloudinary) as Vercel's filesystem is ephemeral.

## Troubleshooting

### Build Fails
- Check that all dependencies are in `requirements.txt`
- Verify Python version compatibility

### 500 Errors
- Check environment variables are set correctly
- Review Vercel function logs
- Ensure `DEBUG=False` and `ALLOWED_HOSTS` includes `.vercel.app`

### Static Files Not Loading
- Run `python manage.py collectstatic` locally to test
- Verify `STATIC_ROOT` is set correctly
- Check WhiteNoise middleware is in the correct position
