# This is a backup of the original simple app.py before upgrading to the full backoffice system
# Backed up on November 4, 2025

from flask import Flask, send_from_directory, request, redirect, url_for, session, flash, render_template_string, jsonify
import os
import openai
from src.config import ADMIN_USERNAME, ADMIN_PASSWORD, OPENAI_API_KEY

app = Flask(__name__, static_folder='public')
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configure OpenAI for Coey - using newer client-based API
# OpenAI client is created in the chat function with the newer API

# Example usage of config variables (remove or use as needed)
print(f"Admin Username: {ADMIN_USERNAME}")
print(f"OpenAI API Key configured: {'Yes' if OPENAI_API_KEY else 'No'}")

# ... (rest of the original code was here)