"""
Middleware to check database configuration on Vercel
"""
import os
from django.http import HttpResponse
from django.conf import settings


class DatabaseCheckMiddleware:
    """
    Middleware to ensure database is properly configured in production
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.is_vercel = os.environ.get('VERCEL', False)
        self.has_database = bool(
            os.environ.get('DATABASE_URL') or 
            os.environ.get('POSTGRES_URL')
        )

    def __call__(self, request):
        # Only check on Vercel and skip static/media files
        if self.is_vercel and not self.has_database:
            if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
                return HttpResponse(
                    """
                    <html>
                    <head><title>Database Not Configured</title></head>
                    <body style="font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5;">
                        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h1 style="color: #e74c3c;">⚠️ Database Not Configured</h1>
                            <p>This application requires a PostgreSQL database to function.</p>
                            <h2>To fix this:</h2>
                            <ol>
                                <li>Go to your <a href="https://vercel.com/dashboard" target="_blank">Vercel Dashboard</a></li>
                                <li>Navigate to your project</li>
                                <li>Click on the <strong>Storage</strong> tab</li>
                                <li>Create a new <strong>Postgres</strong> database</li>
                                <li>Connect it to this project</li>
                                <li>Redeploy the application</li>
                            </ol>
                            <p style="margin-top: 20px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107;">
                                <strong>Note:</strong> Vercel will automatically add the required environment variables 
                                (POSTGRES_URL) when you connect the database.
                            </p>
                        </div>
                    </body>
                    </html>
                    """,
                    status=503,
                    content_type='text/html'
                )
        
        response = self.get_response(request)
        return response
