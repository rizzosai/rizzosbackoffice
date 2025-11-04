import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Admin credentials - these come from environment variables
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'rizzos2024')

# OpenAI API key for Coey AI assistant
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Flask secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'rizzos-secret-key-2024-secure')

# Database configuration (if needed later)
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Print configuration status (remove in production)
print(f"Config loaded - Admin user: {ADMIN_USERNAME}")
print(f"OpenAI configured: {'Yes' if OPENAI_API_KEY else 'No'}")