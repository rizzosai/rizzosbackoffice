import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

NAMECHEAP_API_KEY = os.getenv('NAMECHEAP_API_KEY')
NAMECHEAP_USERNAME = os.getenv('NAMECHEAP_USERNAME')
NAMECHEAP_CLIENT_IP = os.getenv('NAMECHEAP_CLIENT_IP')
NAMECHEAP_API_URL = os.getenv('NAMECHEAP_API_URL')

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
STRIPE_PUBLISHER_KEY = os.getenv('STRIPE_PUBLISHER_KEY')
STRIPE_SECRET = os.getenv('STRIPE_SECRET')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
