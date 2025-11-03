
from flask import Flask, send_from_directory
import os
from config import ADMIN_USERNAME, ADMIN_PASSWORD, OPENAI_API_KEY

app = Flask(__name__, static_folder='../public')

# Example usage of config variables (remove or use as needed)
print(f"Admin Username: {ADMIN_USERNAME}")
print(f"OpenAI API Key configured: {'Yes' if OPENAI_API_KEY else 'No'}")

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
