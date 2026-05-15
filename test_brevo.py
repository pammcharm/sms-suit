#!/usr/bin/env python
"""
Test script to verify Brevo API integration
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sms_project.settings')
django.setup()

from django.conf import settings
from core.views import send_brevo_email

def test_brevo_connection():
    """Test Brevo API connection"""
    print("Testing Brevo API connection...")
    print(f"BREVO_API_KEY from settings: {settings.BREVO_API_KEY[:10]}..." if settings.BREVO_API_KEY else "No API key found")
    
    # Test sending an email
    try:
        result = send_brevo_email(
            to_email="test@example.com",
            subject="Test Email from SMS Suite",
            html_content="<p>This is a test email from the SMS Suite application.</p>",
            plain_content="This is a test email from the SMS Suite application."
        )
        
        if result:
            print("SUCCESS: Brevo email sent successfully!")
            return True
        else:
            print("ERROR: Failed to send Brevo email")
            return False
            
    except Exception as e:
        print(f"ERROR testing Brevo API: {e}")
        return False

if __name__ == "__main__":
    success = test_brevo_connection()
    sys.exit(0 if success else 1)