
from flask import Flask, send_from_directory
import os
from config import NAMECHEAP_API_KEY, ADMIN_USERNAME, STRIPE_SECRET

app = Flask(__name__, static_folder='../public')

# Example usage of config variables (remove or use as needed)
print(f"Namecheap API Key: {NAMECHEAP_API_KEY}")
print(f"Admin Username: {ADMIN_USERNAME}")
print(f"Stripe Secret: {STRIPE_SECRET}")

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
