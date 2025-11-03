from flask import Flask, send_from_directory, request, redirect, url_for, session, flash, render_template_string, jsonify
import os
import openai
from src.config import ADMIN_USERNAME, ADMIN_PASSWORD, OPENAI_API_KEY

app = Flask(__name__, static_folder='public')
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configure OpenAI for Coey
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Example usage of config variables (remove or use as needed)
print(f"Admin Username: {ADMIN_USERNAME}")
print(f"OpenAI API Key configured: {'Yes' if OPENAI_API_KEY else 'No'}")

@app.route('/')
def index():
    # Check if user is logged in, if not redirect to login
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/coey')
def coey():
    """Coey AI Assistant page"""
    if not session.get('logged_in'):
        flash('Please log in to access Coey AI Assistant.', 'error')
        return redirect(url_for('login'))
    
    return send_from_directory(app.static_folder, 'coey.html')

@app.route('/coey/chat', methods=['POST'])
def coey_chat():
    """Handle Coey AI chat requests"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get user context
        username = session.get('username', 'User')
        
        # Coey's system prompt with RizzosAI context
        system_prompt = f"""You are Coey, an AI business assistant for RizzosAI domain business owners. 
        You help users with:
        - Understanding their training guides and how to implement them
        - Business strategy advice for domain and referral marketing
        - Technical help with their backoffice and domain setup
        - Analytics and performance insights
        - Scaling their online business
        
        The user {username} has access to training guides based on their package:
        - Starter ($29): 5 Essential Success Guides
        - Pro ($99): 13 Advanced Business Guides  
        - Elite ($249): 20 Elite Strategy Guides
        - Empire ($499): 35 Empire Building Guides
        
        Be helpful, encouraging, and provide actionable advice. Keep responses concise but informative."""
        
        if OPENAI_API_KEY:
            # Use OpenAI for actual AI responses
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            coey_response = response.choices[0].message.content.strip()
        else:
            # Fallback responses when OpenAI is not configured
            fallback_responses = {
                'hello': f"Hello {username}! I'm Coey, your AI business assistant. I'm here to help you succeed with your RizzosAI domain business. What would you like to know?",
                'help': "I can help you with: 📊 Business analytics, 🎓 Guide implementation, 💡 Strategy advice, 🔧 Technical support, and 📈 Scaling your business. What specific area interests you?",
                'guides': "Your training guides are designed to take you from beginner to expert. Start with the foundational guides in your package, then move to more advanced strategies. Which guide would you like help with?",
                'default': f"Thanks for your question, {username}! I'd love to help you with that. Since I'm still learning, I recommend checking your training guides for detailed strategies, or feel free to ask me something more specific about your RizzosAI business."
            }
            
            # Simple keyword matching for demo
            message_lower = user_message.lower()
            if any(word in message_lower for word in ['hello', 'hi', 'hey']):
                coey_response = fallback_responses['hello']
            elif any(word in message_lower for word in ['help', 'what can you do']):
                coey_response = fallback_responses['help']
            elif any(word in message_lower for word in ['guide', 'training', 'learn']):
                coey_response = fallback_responses['guides']
            else:
                coey_response = fallback_responses['default']
        
        return jsonify({'response': coey_response})
        
    except Exception as e:
        print(f"Coey chat error: {str(e)}")
        return jsonify({'response': 'Sorry, I encountered an error. Please try again later.'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))
    
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        flash('Please log in to access the admin panel.', 'error')
        return redirect(url_for('login'))
    
    admin_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Dashboard - Rizzos Backoffice</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #28a745; }
            .nav-menu { display: flex; justify-content: center; gap: 20px; margin-bottom: 30px; }
            .nav-button { padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; }
            .nav-button:hover { background-color: #218838; }
            .alert { padding: 15px; margin-bottom: 20px; border-radius: 5px; }
            .alert-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .admin-section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔑 Admin Dashboard</h1>
                <p>Welcome, {{ username }}!</p>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <div class="nav-menu">
                <a href="/" class="nav-button">Public Dashboard</a>
                <a href="/coey" class="nav-button">🤖 Ask Coey</a>
                <a href="/domain-check" class="nav-button">Domain Check</a>
                <a href="/logout" class="nav-button">Logout</a>
            </div>

            <div class="admin-section">
                <h2>🔧 Admin Tools</h2>
                <p>You are now logged into the admin panel. Here you can:</p>
                <ul>
                    <li>Manage system settings</li>
                    <li>View user activity logs</li>
                    <li>Configure domain settings</li>
                    <li>Access advanced tools</li>
                </ul>
            </div>

            <div class="admin-section">
                <h2>📊 System Status</h2>
                <p>OpenAI API: {{ 'Connected' if openai_configured else 'Not Configured' }}</p>
                <p>Admin User: {{ username }}</p>
                <p>System: Online</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(admin_html, 
                                 username=session.get('username'),
                                 openai_configured=bool(OPENAI_API_KEY))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/privacy')
def privacy():
    return send_from_directory(app.static_folder, 'privacy.html')

@app.route('/terms')
def terms():
    return send_from_directory(app.static_folder, 'terms.html')

@app.route('/domain-check', methods=['GET', 'POST'])
def domain_check():
    if request.method == 'POST':
        domain = request.form.get('domain')
        # Here you would implement actual domain checking logic
        # For now, just return a simple response
        flash(f'Domain check requested for: {domain}', 'success')
        return redirect(url_for('domain_check'))
    
    return send_from_directory(app.static_folder, 'domain-check.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
