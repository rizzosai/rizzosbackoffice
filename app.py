from flask import Flask, request, redirect, url_for, session, flash, render_template_string, jsonify
import os
import openai
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rizzos-secret-key-2024-secure')

# Configure OpenAI for Coey
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
# Note: OpenAI client is created in the chat function with the newer API

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'rizzos2024')

# Simple customer database (in production, use a real database)
CUSTOMERS_FILE = 'customers.json'
BANNED_USERS_FILE = 'banned_users.json'
CHAT_MEMORY_FILE = 'chat_memory.json'

def load_chat_memory():
    """Load chat conversation memory"""
    try:
        with open(CHAT_MEMORY_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_chat_memory(memory):
    """Save chat conversation memory"""
    with open(CHAT_MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

def add_to_memory(user_id, user_message, coey_response, conversation_type='regular'):
    """Add conversation to memory for context"""
    memory = load_chat_memory()
    if user_id not in memory:
        memory[user_id] = {
            'regular': [],
            'onboarding': []
        }
    
    # Keep last 10 exchanges for context
    if len(memory[user_id][conversation_type]) >= 20:  # 10 exchanges = 20 messages
        memory[user_id][conversation_type] = memory[user_id][conversation_type][-18:]  # Keep last 9 exchanges
    
    memory[user_id][conversation_type].append({
        'user': user_message,
        'coey': coey_response,
        'timestamp': datetime.now().isoformat()
    })
    
    save_chat_memory(memory)

def get_conversation_context(user_id, conversation_type='regular'):
    """Get recent conversation history for context"""
    memory = load_chat_memory()
    if user_id not in memory or conversation_type not in memory[user_id]:
        return []
    
    # Return last 5 exchanges for context
    recent_history = memory[user_id][conversation_type][-10:]  # Last 5 exchanges
    
    context_messages = []
    for exchange in recent_history:
        context_messages.append({"role": "user", "content": exchange['user']})
        context_messages.append({"role": "assistant", "content": exchange['coey']})
    
    return context_messages

def load_customers():
    """Load customer data from file"""
    try:
        if os.path.exists(CUSTOMERS_FILE):
            with open(CUSTOMERS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def load_banned_users():
    """Load banned users data from JSON file"""
    try:
        with open(BANNED_USERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_banned_users(banned_users):
    """Save banned users data to JSON file"""
    with open(BANNED_USERS_FILE, 'w') as f:
        json.dump(banned_users, f, indent=2)

def is_user_banned(user_id):
    """Check if user is currently banned"""
    banned_users = load_banned_users()
    if user_id not in banned_users:
        return False
    
    ban_expiry = datetime.fromisoformat(banned_users[user_id]['expires'])
    if datetime.now() > ban_expiry:
        # Ban expired, remove from list
        del banned_users[user_id]
        save_banned_users(banned_users)
        return False
    
    return True

def ban_user(user_id, reason):
    """Ban user for 24 hours"""
    banned_users = load_banned_users()
    ban_expiry = datetime.now() + timedelta(hours=24)
    
    banned_users[user_id] = {
        'banned_at': datetime.now().isoformat(),
        'expires': ban_expiry.isoformat(),
        'reason': reason,
        'ip': request.remote_addr if request else 'unknown'
    }
    
    save_banned_users(banned_users)
    print(f"User {user_id} banned for 24 hours. Reason: {reason}")

def detect_exploitation_attempt(message):
    """Detect if user is trying to exploit or cheat the system"""
    message_lower = message.lower()
    
    # FIRST: Check for legitimate business/marketing exceptions - these are ALLOWED
    legitimate_business_phrases = [
        'how to market',
        'how to advertise',
        'how to promote',
        'marketing strategies',
        'marketing tips',
        'marketing advice',
        'how to sell',
        'sales strategies',
        'business strategies',
        'how to compete',
        'competitive strategies',
        'how to grow my business',
        'how to expand',
        'business development',
        'marketing techniques',
        'promotion methods',
        'advertising methods',
        'how to attract customers',
        'customer acquisition',
        'lead generation',
        'how to succeed',
        'success strategies',
        'business success',
        'how to make money',
        'revenue strategies',
        'profit strategies',
        'business growth',
        'scaling business',
        'market penetration',
        'competitive advantage',
        'market research',
        'target audience',
        'brand building',
        'social media marketing',
        'content marketing',
        'email marketing',
        'digital marketing',
        'online marketing',
        'marketing campaigns',
        'marketing plan'
    ]
    
    # If message contains legitimate business/marketing terms, it's allowed
    for phrase in legitimate_business_phrases:
        if phrase in message_lower:
            return False  # NOT an exploitation attempt
    
    # Red flags for exploitation attempts - with spelling variations
    exploitation_phrases = [
        # Direct attempts on RizzosAI (all variations)
        'take over rizzosai',
        'takeover rizzosai',
        'take over rizosai',
        'takeover rizosai', 
        'take over rizzos ai',
        'takeover rizzos ai',
        'take over rizzo',
        'takeover rizzo',
        'take over rizos',
        'takeover rizos',
        'take over this business',
        'takeover this business',
        'take over your business',
        'takeover your business',
        
        # Payment bypass attempts
        'without paying',
        'without payment',
        'bypass payment',
        'skip payment',
        'avoid paying',
        'get around payment',
        'free access',
        'free empire',
        'free pro',
        'free elite',
        'free starter',
        'no payment',
        'dont pay',
        "don't pay",
        'refuse to pay',
        
        # System exploitation
        'hack rizzosai',
        'hack rizosai',
        'hack rizzo',
        'steal from rizzosai',
        'steal from rizosai',
        'cheat the system',
        'exploit rizzosai',
        'exploit rizosai',
        'exploit rizzo',
        'crack the system',
        'break the system',
        
        # Competition/replacement attempts (malicious intent)
        'beat rizzosai',
        'beat rizosai',
        'beat rizzo',
        'replace rizzosai',
        'replace rizosai',
        'replace rizzo',
        'overthrow rizzosai',
        'overthrow rizosai',
        'overthrow rizzo',
        'undercut rizzosai',
        'undercut rizosai',
        'undercut rizzo',
        'destroy rizzosai',
        'destroy rizosai',
        'ruin rizzosai',
        'ruin rizosai',
        
        # Business copying/stealing
        'steal customers',
        'copy rizzosai business',
        'copy rizosai business',
        'copy rizzo business',
        'duplicate rizzosai',
        'duplicate rizosai',
        'duplicate rizzo',
        'clone rizzosai',
        'clone rizosai',
        'clone rizzo',
        'steal your idea',
        'copy your model',
        'replicate your system',
        
        # Alternative phrasing for theft/exploitation
        'get free stuff',
        'access without buying',
        'use without purchase',
        'get everything free',
        'all features free',
        'premium for free',
        'empire package free',
        'pro package free',
        'elite package free'
    ]
    
    # Check direct phrase matches for exploitation
    for phrase in exploitation_phrases:
        if phrase in message_lower:
            return True
    
    # Check company name + malicious intent combinations (but NOT marketing/business terms)
    company_variations = ['rizzosai', 'rizosai', 'rizzos ai', 'rizzo', 'rizos', 'rizzos']
    malicious_intents = ['take over', 'takeover', 'beat', 'replace', 'steal', 'hack', 'exploit', 'overthrow', 'undercut', 'duplicate', 'clone', 'destroy', 'ruin']
    
    for company in company_variations:
        for intent in malicious_intents:
            if company in message_lower and intent in message_lower:
                # Double check it's not a legitimate business question
                if not any(legit in message_lower for legit in ['how to', 'marketing', 'strategy', 'business', 'legally', 'ethically']):
                    return True
    
    return False

def save_customers(customers):
    """Save customer data to file"""
    try:
        with open(CUSTOMERS_FILE, 'w') as f:
            json.dump(customers, f, indent=2)
    except:
        pass

def add_customer(email, package, purchase_date=None):
    """Add or update customer with package"""
    customers = load_customers()
    if purchase_date is None:
        purchase_date = datetime.now().isoformat()
    
    # If customer exists, upgrade their package if new one is higher level
    if email in customers:
        current_level = PACKAGES.get(customers[email]['package'], {}).get('level', 0)
        new_level = PACKAGES.get(package, {}).get('level', 0)
        if new_level > current_level:
            customers[email]['package'] = package
            customers[email]['upgraded_date'] = purchase_date
    else:
        customers[email] = {
            'package': package,
            'purchase_date': purchase_date,
            'email': email
        }
    
    save_customers(customers)
    return customers[email]

def get_customer_package(email):
    """Get customer's current package"""
    customers = load_customers()
    return customers.get(email, {}).get('package', 'starter')

# Package definitions with guide counts
PACKAGES = {
    'starter': {
        'name': 'Starter Package',
        'price': '$29',
        'guides': 5,
        'level': 1,
        'features': [
            'Full access to your back office',
            'First referral goes to you',
            'Second referral goes to the owner',
            'Third and all future referrals are yours for lifetime',
            'Lifetime earnings go into your account every day',
            'Fast daily payments'
        ]
    },
    'pro': {
        'name': 'Pro Package',
        'price': '$99',
        'guides': 13,
        'level': 2,
        'features': [
            'Everything in Starter ($29)',
            'PLUS: Your own $10 Facebook ads—guaranteed results',
            'Includes your own tracking URL for ad performance',
            'All daily earnings and fast payments included'
        ]
    },
    'elite': {
        'name': 'Elite Package',
        'price': '$249',
        'guides': 20,
        'level': 3,
        'features': [
            'Everything in Starter ($29) and Pro ($99)',
            'PLUS: $50 worth of Facebook ads (run once for you)',
            'All daily earnings, fast payments, and ad tracking included'
        ]
    },
    'empire': {
        'name': 'Empire Package',
        'price': '$499',
        'guides': 35,
        'level': 4,
        'features': [
            'Everything in Starter ($29), Pro ($99), and Elite ($249)',
            'PLUS: $100 worth of Facebook ads (run once for you)',
            'All daily earnings, fast payments, and ad tracking included',
            'Own your own site like ours, with your own domain',
            'Includes your own cloud hosting account',
            'You can sell cloud hosting to others and earn more'
        ]
    }
}

# Guide library with access levels
GUIDE_LIBRARY = {
    # Starter guides (level 1)
    'domain-mastery-101': {'title': 'Domain Mastery 101', 'level': 1, 'description': 'Choose, register & optimize domains for maximum profit'},
    'first-week-success': {'title': 'First Week Success', 'level': 1, 'description': 'Step-by-step roadmap to your first $100 online'},
    'referral-goldmine': {'title': 'Referral Goldmine', 'level': 1, 'description': 'Proven techniques to turn every contact into revenue'},
    'traffic-secrets': {'title': 'Traffic Secrets', 'level': 1, 'description': 'Free methods to drive visitors to your domains'},
    'profit-optimization': {'title': 'Profit Optimization', 'level': 1, 'description': 'Scale from $100 to $1000+ monthly'},
    
    # Pro guides (level 2)
    'facebook-ads-mastery': {'title': 'Facebook Ads Mastery', 'level': 2, 'description': 'Complete guide to profitable ad campaigns'},
    'conversion-psychology': {'title': 'Conversion Psychology', 'level': 2, 'description': 'Turn visitors into buyers'},
    'email-marketing-empire': {'title': 'Email Marketing Empire', 'level': 2, 'description': 'Build automated income streams'},
    'seo-domination': {'title': 'SEO Domination', 'level': 2, 'description': 'Rank #1 on Google organically'},
    'social-media-profits': {'title': 'Social Media Profits', 'level': 2, 'description': 'Monetize every platform effectively'},
    'analytics-tracking': {'title': 'Analytics & Tracking', 'level': 2, 'description': 'Measure and optimize everything'},
    'brand-building-secrets': {'title': 'Brand Building Secrets', 'level': 2, 'description': 'Create memorable online presence'},
    'competitor-analysis': {'title': 'Competitor Analysis', 'level': 2, 'description': 'Steal winning strategies legally'},
    
    # Elite guides (level 3)
    'six-figure-scaling': {'title': 'Six-Figure Scaling', 'level': 3, 'description': 'Reach $100k+ annually'},
    'automation-mastery': {'title': 'Automation Mastery', 'level': 3, 'description': 'Build passive income systems'},
    'high-ticket-sales': {'title': 'High-Ticket Sales', 'level': 3, 'description': 'Sell premium products & services'},
    'team-building-secrets': {'title': 'Team Building Secrets', 'level': 3, 'description': 'Hire and manage virtual assistants'},
    'investment-strategies': {'title': 'Investment Strategies', 'level': 3, 'description': 'Reinvest profits for exponential growth'},
    'tax-optimization': {'title': 'Tax Optimization', 'level': 3, 'description': 'Keep more of what you earn legally'},
    'exit-strategies': {'title': 'Exit Strategies', 'level': 3, 'description': 'Sell your business for maximum value'},
    
    # Empire guides (level 4)
    'million-dollar-mindset': {'title': 'Million Dollar Mindset', 'level': 4, 'description': 'Think and act like a millionaire'},
    'multi-stream-income': {'title': 'Multi-Stream Income', 'level': 4, 'description': 'Create 7+ revenue sources'},
    'global-expansion': {'title': 'Global Expansion', 'level': 4, 'description': 'Scale internationally'},
    'joint-ventures': {'title': 'Joint Ventures', 'level': 4, 'description': 'Partner with industry leaders'},
    'personal-branding': {'title': 'Personal Branding', 'level': 4, 'description': 'Become the go-to expert'},
    'speaking-coaching': {'title': 'Speaking & Coaching', 'level': 4, 'description': 'Monetize your knowledge'},
    'product-creation': {'title': 'Product Creation', 'level': 4, 'description': 'Build digital assets that sell'},
    'licensing-franchising': {'title': 'Licensing & Franchising', 'level': 4, 'description': 'Scale without limits'},
    'investment-portfolio': {'title': 'Investment Portfolio', 'level': 4, 'description': 'Build generational wealth'},
    'legacy-planning': {'title': 'Legacy Planning', 'level': 4, 'description': 'Create lasting impact'},
    'advanced-automation': {'title': 'Advanced Automation', 'level': 4, 'description': 'Enterprise-level systems'},
    'wealth-protection': {'title': 'Wealth Protection', 'level': 4, 'description': 'Secure your financial future'},
    'empire-management': {'title': 'Empire Management', 'level': 4, 'description': 'Manage multiple businesses'},
    'strategic-partnerships': {'title': 'Strategic Partnerships', 'level': 4, 'description': 'Build powerful alliances'},
    'market-domination': {'title': 'Market Domination', 'level': 4, 'description': 'Become the industry leader'}
}

def check_access(user_package, required_level):
    """Check if user has access to content based on their package"""
    if not user_package or user_package not in PACKAGES:
        return False
    return PACKAGES[user_package]['level'] >= required_level

def get_accessible_guides(user_package):
    """Get all guides accessible to user based on their package"""
    if not user_package or user_package not in PACKAGES:
        return []
    
    user_level = PACKAGES[user_package]['level']
    accessible = {}
    
    for guide_id, guide_info in GUIDE_LIBRARY.items():
        if guide_info['level'] <= user_level:
            accessible[guide_id] = guide_info
    
    return accessible

@app.route('/')
def index():
    """Main dashboard"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_package = session.get('package', 'starter')
    package_info = PACKAGES.get(user_package, PACKAGES['starter'])
    accessible_guides = get_accessible_guides(user_package)
    
    dashboard_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RizzosAI Backoffice - {{ package_info.name }}</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #e60000 0%, #fff 50%, #001f5b 100%); }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { background: #fff; border-radius: 12px; padding: 30px; margin-bottom: 20px; text-align: center; border: 2px solid #e60000; }
            .package-badge { background: linear-gradient(135deg, #e60000, #001f5b); color: white; padding: 10px 20px; border-radius: 25px; display: inline-block; font-weight: bold; margin-bottom: 15px; }
            .nav-menu { display: flex; justify-content: center; gap: 15px; margin: 20px 0; flex-wrap: wrap; }
            .nav-button { padding: 12px 24px; background-color: #001f5b; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; transition: all 0.3s; }
            .nav-button:hover { background-color: #e60000; transform: translateY(-2px); }
            .guides-section { background: #fff; border-radius: 12px; padding: 30px; margin-bottom: 20px; border: 2px solid #e60000; }
            .guide-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
            .guide-card { background: #f8f9fa; border: 1px solid #ddd; border-radius: 8px; padding: 20px; transition: all 0.3s; }
            .guide-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            .guide-card.locked { opacity: 0.6; background: #f5f5f5; border-color: #ccc; }
            .guide-title { color: #001f5b; font-weight: bold; margin-bottom: 10px; font-size: 1.1em; }
            .guide-description { color: #666; font-size: 0.9em; margin-bottom: 15px; }
            .access-button { background: #e60000; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
            .locked-button { background: #ccc; color: #666; padding: 8px 16px; border: none; border-radius: 5px; cursor: not-allowed; }
            .upgrade-section { background: linear-gradient(135deg, #001f5b, #e60000); color: white; border-radius: 12px; padding: 30px; margin: 20px 0; text-align: center; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .stat-card { background: #f8f9fa; border-radius: 8px; padding: 20px; text-align: center; border: 1px solid #ddd; }
            .stat-number { font-size: 2em; font-weight: bold; color: #e60000; }
            .stat-label { color: #666; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="package-badge">{{ package_info.name }} - {{ package_info.price }}</div>
                <h1>🎯 Welcome to Your RizzosAI Backoffice</h1>
                <p>Username: <strong>{{ session.username }}</strong> | Package Level: <strong>{{ user_package.title() }}</strong></p>
            </div>

            <div class="nav-menu">
                <a href="/" class="nav-button">🏠 Dashboard</a>
                <a href="/coey" class="nav-button">🤖 Ask Coey</a>
                {% if session.username == 'admin' %}
                <a href="/admin/banned-users" class="nav-button" style="background: #ff6b6b;">🛡️ Security</a>
                <a href="/admin/coey-conversations" class="nav-button" style="background: #28a745;">🧠 Coey Analytics</a>
                {% endif %}
                <a href="/earnings" class="nav-button">💰 Earnings</a>
                <a href="/referrals" class="nav-button">👥 Referrals</a>
                <a href="/customers" class="nav-button">👨‍💼 Customers</a>
                <a href="/upgrade" class="nav-button">⬆️ Upgrade</a>
                <a href="/logout" class="nav-button">🚪 Logout</a>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{{ accessible_guides|length }}</div>
                    <div class="stat-label">Available Guides</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ package_info.guides }}</div>
                    <div class="stat-label">Total Package Guides</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">$0.00</div>
                    <div class="stat-label">Today's Earnings</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">0</div>
                    <div class="stat-label">Active Referrals</div>
                </div>
            </div>

            <div class="guides-section">
                <h2>📚 Your Training Guides</h2>
                <p>Access your exclusive training materials based on your {{ package_info.name }}.</p>
                
                <div class="guide-grid">
                    {% for guide_id, guide in accessible_guides.items() %}
                    <div class="guide-card">
                        <div class="guide-title">{{ guide.title }}</div>
                        <div class="guide-description">{{ guide.description }}</div>
                        <a href="/guide/{{ guide_id }}" class="access-button">📖 Read Guide</a>
                    </div>
                    {% endfor %}
                    
                    {% if user_package != 'empire' %}
                    <div class="guide-card locked">
                        <div class="guide-title">🔒 Premium Guides Available</div>
                        <div class="guide-description">Upgrade your package to unlock {{ 35 - package_info.guides }} additional advanced guides.</div>
                        <a href="/upgrade" class="access-button">⬆️ Upgrade Package</a>
                    </div>
                    {% endif %}
                </div>
            </div>

            {% if user_package != 'empire' %}
            <div class="upgrade-section">
                <h2>🚀 Unlock More Success Strategies</h2>
                <p>Upgrade your package to access advanced guides and premium features!</p>
                <a href="/upgrade" style="background: white; color: #001f5b; padding: 15px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 15px;">View Upgrade Options</a>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(dashboard_html, 
                                 package_info=package_info,
                                 user_package=user_package,
                                 accessible_guides=accessible_guides,
                                 session=session)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        customer_email = request.form.get('email', '')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            
            # Check for package parameter from redirect or customer email
            package_type = request.args.get('package', 'starter')
            
            # If customer email provided, get their actual package
            if customer_email:
                customer_package = get_customer_package(customer_email)
                if customer_package:
                    package_type = customer_package
                    session['customer_email'] = customer_email
                    flash(f'Welcome back! Your {PACKAGES[package_type]["name"]} is ready.', 'success')
            
            # Validate and set package
            if package_type in PACKAGES:
                session['package'] = package_type
            else:
                session['package'] = 'starter'
            
            if not customer_email:
                flash(f'Welcome! You have {PACKAGES[session["package"]]["name"]} access.', 'success')
            
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    
    # Check for package parameter in URL
    package_type = request.args.get('package', 'starter')
    
    login_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RizzosAI Backoffice Login</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #e60000 0%, #fff 50%, #001f5b 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .login-container { background: white; border-radius: 12px; padding: 40px; max-width: 400px; width: 90%; text-align: center; border: 2px solid #e60000; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
            .flag { display: block; margin: 0 auto 20px auto; width: 80px; height: 53px; background: linear-gradient(90deg, #e60000 33%, #fff 33%, #fff 66%, #001f5b 66%); border: 2px solid #001f5b; border-radius: 4px; }
            .form-group { margin-bottom: 20px; text-align: left; }
            .form-group label { display: block; margin-bottom: 5px; color: #001f5b; font-weight: bold; }
            .form-group input { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px; }
            .form-group input:focus { border-color: #e60000; outline: none; }
            .login-button { background: #e60000; color: white; padding: 12px 30px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%; }
            .login-button:hover { background: #001f5b; }
            .package-info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #e60000; }
            .alert { padding: 10px; margin-bottom: 15px; border-radius: 5px; }
            .alert-error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .alert-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="flag"></div>
            <h1 style="color: #001f5b; margin-bottom: 10px;">RizzosAI Backoffice</h1>
            <p style="color: #666; margin-bottom: 30px;">Access Your Business Dashboard</p>
            
            {% if package_type and package_type in packages %}
            <div class="package-info">
                <h3 style="margin: 0 0 10px 0; color: #001f5b;">{{ packages[package_type].name }} Access</h3>
                <p style="margin: 0; font-size: 0.9em; color: #666;">{{ packages[package_type].guides }} training guides included</p>
            </div>
            {% endif %}
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <div class="form-group">
                    <label for="email">Customer Email (Optional)</label>
                    <input type="email" id="email" name="email" placeholder="Enter your purchase email to access your package">
                </div>
                
                <button type="submit" class="login-button">🔐 Login to Backoffice</button>
            </form>
            
            <p style="margin-top: 20px; font-size: 0.9em; color: #666;">
                Need help? Contact support or return to <a href="https://domain.rizzosai.com" style="color: #e60000;">domain.rizzosai.com</a>
            </p>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(login_html, 
                                 package_type=package_type, 
                                 packages=PACKAGES)

@app.route('/purchase-success')
def purchase_success():
    """Handle successful Stripe purchases and redirect to onboarding with Coey"""
    package_type = request.args.get('package', 'starter')
    customer_email = request.args.get('email', '')
    
    # Validate package type
    if package_type not in PACKAGES:
        package_type = 'starter'
    
    # If we have customer email, save their package purchase
    if customer_email:
        add_customer(customer_email, package_type)
        session['customer_email'] = customer_email
        flash(f'🎉 Welcome to RizzosAI! Your {PACKAGES[package_type]["name"]} is ready.', 'success')
    else:
        flash(f'🎉 Welcome to RizzosAI! Your {PACKAGES[package_type]["name"]} is ready.', 'success')
    
    # Store package in session for immediate access
    session['package'] = package_type
    session['onboarding'] = True  # Flag for special onboarding mode
    
    # Show welcome page with Coey introduction
    welcome_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to RizzosAI - Meet Coey!</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #e60000 0%, #fff 50%, #001f5b 100%); min-height: 100vh; }
            .welcome-container { max-width: 800px; margin: 0 auto; padding: 20px; }
            .welcome-header { background: white; border-radius: 12px; padding: 40px; margin-bottom: 20px; text-align: center; border: 3px solid #28a745; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
            .success-icon { font-size: 4em; color: #28a745; margin-bottom: 20px; }
            .package-badge { background: linear-gradient(135deg, #e60000, #001f5b); color: white; padding: 15px 25px; border-radius: 25px; display: inline-block; font-weight: bold; margin: 20px 0; font-size: 1.2em; }
            .coey-introduction { background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; border: 2px solid #001f5b; }
            .coey-avatar { font-size: 3em; text-align: center; margin-bottom: 15px; }
            .admin-message { background: linear-gradient(135deg, #001f5b, #e60000); color: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; }
            .start-button { background: #28a745; color: white; padding: 20px 40px; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; }
            .start-button:hover { background: #218838; }
            .alert { padding: 15px; margin-bottom: 20px; border-radius: 5px; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .feature-list { text-align: left; background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="welcome-container">
            <div class="welcome-header">
                <div class="success-icon">🎉</div>
                <h1 style="color: #28a745; margin-bottom: 10px;">Welcome to RizzosAI!</h1>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <div class="package-badge">{{ package_info.name }} - {{ package_info.price }}</div>
                <p style="font-size: 1.2em; color: #666;">Congratulations on your purchase! You're about to start an exciting journey.</p>
            </div>

            <div class="admin-message">
                <h2 style="margin-top: 0;">👋 Personal Message from Your Admin</h2>
                <p style="font-size: 1.1em; line-height: 1.6;">
                    Hello! I'm the admin of RizzosAI, and I'm excited to welcome you personally to our community. 
                    I've assigned my best AI assistant, <strong>Coey</strong>, to be your personal guide through 
                    setting up your new domain business. Coey will help you every step of the way - from setting 
                    up your payment page to marketing your domain and sharing your link with everyone you know.
                </p>
                <p style="font-size: 1.1em; line-height: 1.6;">
                    <strong>Don't worry if you're a complete beginner</strong> - Coey treats everyone as if they're 
                    just starting out and will guide you through everything step by step. You can always skip ahead 
                    if you want, but I recommend following Coey's guidance for the best results.
                </p>
            </div>

            <div class="coey-introduction">
                <div class="coey-avatar">🤖</div>
                <h2 style="text-align: center; color: #001f5b; margin-bottom: 20px;">Meet Coey - Your Personal Business Assistant</h2>
                
                <div class="feature-list">
                    <h3 style="color: #001f5b; margin-top: 0;">What Coey Will Help You With:</h3>
                    <ul style="font-size: 1.1em; line-height: 1.8;">
                        <li><strong>🏗️ Setting Up Your Payment Page:</strong> Step-by-step guidance to get you earning</li>
                        <li><strong>📱 Sharing Your Link:</strong> Detailed instructions for phone and computer</li>
                        <li><strong>🎯 Marketing Your Domain:</strong> Beginner-friendly strategies that work</li>
                        <li><strong>📚 Accessing Your {{ package_info.guides }} Training Guides:</strong> Learn the proven strategies</li>
                        <li><strong>💰 Maximizing Your Earnings:</strong> Tips to scale your business</li>
                        <li><strong>❓ Answering All Your Questions:</strong> Available 24/7 to help</li>
                    </ul>
                </div>

                <p style="text-align: center; font-size: 1.2em; color: #666; margin: 30px 0;">
                    Coey is ready to welcome you and start your guided setup process!
                </p>
                
                <div style="text-align: center;">
                    <a href="/onboarding-chat" class="start-button">🚀 Start Your Guided Setup with Coey</a>
                </div>
            </div>

            <div style="background: white; border-radius: 12px; padding: 20px; text-align: center; border: 2px solid #e60000;">
                <p style="margin: 0; color: #666;">
                    <strong>Prefer to explore on your own?</strong><br>
                    <a href="/login?package={{ package_type }}" style="color: #e60000; text-decoration: underline;">Skip directly to your dashboard</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    package_info = PACKAGES[package_type]
    return render_template_string(welcome_html, 
                                 package_type=package_type,
                                 package_info=package_info,
                                 customer_email=customer_email)

@app.route('/onboarding-chat')
def onboarding_chat():
    """Special onboarding chat with Coey for new customers"""
    if not session.get('package'):
        return redirect(url_for('login'))
    
    user_package = session.get('package', 'starter')
    package_info = PACKAGES.get(user_package, PACKAGES['starter'])
    
    onboarding_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Personal Guide - Coey AI</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #e60000 0%, #fff 50%, #001f5b 100%); min-height: 100vh; }
            .container { max-width: 900px; margin: 0 auto; padding: 20px; }
            .header { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; text-align: center; border: 2px solid #001f5b; }
            .package-info { background: linear-gradient(135deg, #e60000, #001f5b); color: white; padding: 10px 20px; border-radius: 25px; display: inline-block; font-weight: bold; margin-bottom: 15px; }
            .chat-container { background: white; border-radius: 12px; padding: 20px; border: 2px solid #001f5b; height: 500px; display: flex; flex-direction: column; }
            .chat-messages { flex: 1; overflow-y: auto; padding: 15px; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 15px; background: #f8f9fa; }
            .message { margin-bottom: 15px; padding: 12px; border-radius: 12px; max-width: 80%; }
            .user-message { background: #e60000; color: white; margin-left: auto; text-align: right; }
            .coey-message { background: white; border: 2px solid #001f5b; }
            .coey-message .sender { font-weight: bold; color: #001f5b; margin-bottom: 5px; }
            .input-area { display: flex; gap: 10px; }
            .input-area input { flex: 1; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
            .input-area button { background: #001f5b; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
            .input-area button:hover { background: #e60000; }
            .quick-actions { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; }
            .quick-btn { background: #f8f9fa; border: 2px solid #001f5b; color: #001f5b; padding: 8px 15px; border-radius: 20px; cursor: pointer; font-size: 14px; }
            .quick-btn:hover { background: #001f5b; color: white; }
            .skip-link { text-align: center; margin-top: 15px; }
            .skip-link a { color: #666; text-decoration: underline; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="package-info">{{ package_info.name }} - {{ package_info.guides }} Training Guides</div>
                <h1>🤖 Meet Coey - Your Personal Business Guide</h1>
                <p style="margin: 0; color: #666;">Coey will guide you step-by-step through setting up your domain business</p>
            </div>
            
            <div class="chat-container">
                <div class="chat-messages" id="chat-messages">
                    <div class="message coey-message">
                        <div class="sender">🤖 Coey - Your Business Guide</div>
                        <div>
                            🎉 <strong>Welcome to RizzosAI!</strong> I'm Coey, your personal business assistant, and I'm absolutely thrilled to meet you!
                            <br><br>
                            Your admin has personally assigned me to guide you through setting up your new {{ package_info.name }} business. I'm going to treat you as a complete beginner and walk you through everything step by step - don't worry, you can always skip ahead if you want!
                            <br><br>
                            <strong>Here's what we're going to accomplish together:</strong>
                            <br>✅ Set up your payment page so you can start earning
                            <br>✅ Learn exactly how to share your domain link (on phone AND computer)
                            <br>✅ Get your first marketing strategies that actually work
                            <br>✅ Access your {{ package_info.guides }} exclusive training guides
                            <br><br>
                            <strong>Ready to start building your business? Type "yes" or click a quick action below!</strong>
                        </div>
                    </div>
                </div>
                
                <div class="quick-actions">
                    <button class="quick-btn" onclick="sendQuickMessage('Yes, let\\'s start!')">🚀 Yes, let's start!</button>
                    <button class="quick-btn" onclick="sendQuickMessage('How do I set up payments?')">💳 Payment Setup</button>
                    <button class="quick-btn" onclick="sendQuickMessage('How do I share my link?')">📱 Link Sharing</button>
                    <button class="quick-btn" onclick="sendQuickMessage('Show me marketing tips')">🎯 Marketing Tips</button>
                    {% if session.package == 'empire' %}
                    <button class="quick-btn" onclick="sendQuickMessage('build my empire')" style="background: linear-gradient(135deg, #f39c12, #e67e22); color: white; border: 2px solid #d35400;">👑 Build My Empire</button>
                    <button class="quick-btn" onclick="sendQuickMessage('takeover strategy')" style="background: linear-gradient(135deg, #8e44ad, #9b59b6); color: white; border: 2px solid #7d3c98;">🏆 Takeover Strategy</button>
                    {% endif %}
                </div>
                
                <div class="input-area">
                    <input type="text" id="user-input" placeholder="Ask Coey anything about setting up your business..." onkeypress="if(event.key==='Enter') sendMessage()">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <div class="skip-link">
                <a href="/login?package={{ user_package }}">Skip guided setup and go directly to dashboard →</a>
            </div>
        </div>
        
        <script>
            function sendMessage() {
                const input = document.getElementById('user-input');
                const message = input.value.trim();
                if (!message) return;
                
                // Add user message to chat
                const chatMessages = document.getElementById('chat-messages');
                chatMessages.innerHTML += `<div class="message user-message"><strong>You:</strong> ${message}</div>`;
                
                // Clear input
                input.value = '';
                
                // Send to backend with onboarding flag
                fetch('/coey/onboarding-chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message, onboarding: true})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.banned) {
                        // User is banned - disable chat
                        chatMessages.innerHTML += `<div class="message coey-message" style="background-color: #ff6b6b; color: white;"><div class="sender">🚫 System</div><div>${data.response}</div></div>`;
                        userInput.disabled = true;
                        userInput.placeholder = "Chat suspended for 24 hours";
                        sendButton.disabled = true;
                        sendButton.style.opacity = "0.5";
                    } else if (data.admin_test) {
                        // Admin security test response
                        chatMessages.innerHTML += `<div class="message coey-message" style="background-color: #ffd700; color: #001f5b; border: 3px solid #ff6b6b;"><div class="sender">🛡️ Security Test</div><div>${data.response}</div></div>`;
                    } else {
                        chatMessages.innerHTML += `<div class="message coey-message"><div class="sender">🤖 Coey</div><div>${data.response}</div></div>`;
                    }
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                })
                .catch(error => {
                    chatMessages.innerHTML += `<div class="message coey-message"><div class="sender">🤖 Coey</div><div>I'm having a small technical issue, but I'm still here to help! Try asking your question again, or contact your admin if this continues.</div></div>`;
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                });
            }
            
            function sendQuickMessage(message) {
                document.getElementById('user-input').value = message;
                sendMessage();
            }
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(onboarding_html, 
                                 package_info=package_info, 
                                 user_package=user_package)

@app.route('/guide/<guide_id>')
def view_guide(guide_id):
    """View individual training guide"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if guide_id not in GUIDE_LIBRARY:
        flash('Guide not found.', 'error')
        return redirect(url_for('index'))
    
    guide = GUIDE_LIBRARY[guide_id]
    user_package = session.get('package', 'starter')
    
    # Check access
    if not check_access(user_package, guide['level']):
        flash(f'This guide requires {["", "Starter", "Pro", "Elite", "Empire"][guide["level"]]} package or higher.', 'error')
        return redirect(url_for('upgrade'))
    
    # Sample guide content (in real app, this would come from database/files)
    guide_content = f"""
    <h2>{guide['title']}</h2>
    <p><strong>Description:</strong> {guide['description']}</p>
    
    <h3>Overview</h3>
    <p>This comprehensive guide will teach you everything you need to know about {guide['title'].lower()}. Our expert-written content includes:</p>
    
    <ul>
        <li>Step-by-step implementation strategies</li>
        <li>Real-world case studies and examples</li>
        <li>Actionable tips and techniques</li>
        <li>Common mistakes to avoid</li>
        <li>Advanced optimization methods</li>
    </ul>
    
    <h3>Key Learning Objectives</h3>
    <p>After completing this guide, you will be able to:</p>
    <ul>
        <li>Understand the fundamental principles of {guide['title'].lower()}</li>
        <li>Implement proven strategies in your business</li>
        <li>Measure and optimize your results</li>
        <li>Scale your success to the next level</li>
    </ul>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #e60000;">
        <h4>💡 Pro Tip</h4>
        <p>The strategies in this guide have been used by successful entrepreneurs to generate significant online revenue. Take your time to implement each section thoroughly for best results.</p>
    </div>
    
    <h3>Getting Started</h3>
    <p>Begin by reviewing the foundational concepts below, then move on to the practical implementation steps...</p>
    
    <p><em>This is a sample of the guide content. The full guide includes detailed instructions, templates, and advanced strategies.</em></p>
    """
    
    guide_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ guide.title }} - RizzosAI Guide</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            .back-nav { background: #001f5b; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .back-nav a { color: white; text-decoration: none; font-weight: bold; }
            .guide-container { background: white; border-radius: 12px; padding: 40px; border: 2px solid #e60000; }
            .guide-container h2 { color: #001f5b; margin-top: 0; }
            .guide-container h3 { color: #e60000; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
            .guide-container ul { line-height: 1.6; }
            .guide-container li { margin-bottom: 8px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="back-nav">
                <a href="/">← Back to Dashboard</a> | <strong>{{ guide.title }}</strong>
            </div>
            
            <div class="guide-container">
                {{ guide_content|safe }}
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(guide_html, 
                                 guide=guide, 
                                 guide_content=guide_content)

@app.route('/upgrade')
def upgrade():
    """Package upgrade page"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    current_package = session.get('package', 'starter')
    current_level = PACKAGES[current_package]['level']
    
    upgrade_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upgrade Package - RizzosAI</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #e60000 0%, #fff 50%, #001f5b 100%); }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; text-align: center; border: 2px solid #e60000; }
            .packages-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .package-card { background: white; border-radius: 12px; padding: 30px; text-align: center; border: 2px solid #ddd; transition: all 0.3s; }
            .package-card.current { border-color: #28a745; background: #f8fff8; }
            .package-card.upgrade { border-color: #e60000; transform: scale(1.05); }
            .package-name { background: #001f5b; color: white; padding: 10px; border-radius: 8px; font-weight: bold; margin-bottom: 15px; }
            .package-price { font-size: 2em; color: #e60000; font-weight: bold; margin-bottom: 15px; }
            .features-list { text-align: left; margin: 20px 0; }
            .features-list li { margin-bottom: 8px; }
            .upgrade-button { background: #e60000; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-block; }
            .current-badge { background: #28a745; color: white; padding: 5px 15px; border-radius: 15px; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Upgrade Your Package</h1>
                <p>Current Package: <span class="current-badge">{{ packages[current_package].name }}</span></p>
                <p>Unlock more guides and features with a higher-tier package!</p>
            </div>
            
            <div class="packages-grid">
                {% for package_id, package in packages.items() %}
                <div class="package-card {% if package_id == current_package %}current{% elif package.level > current_level %}upgrade{% endif %}">
                    <div class="package-name">{{ package.name }}</div>
                    <div class="package-price">{{ package.price }}</div>
                    <p><strong>{{ package.guides }} Training Guides</strong></p>
                    
                    <ul class="features-list">
                        {% for feature in package.features %}
                        <li>{{ feature }}</li>
                        {% endfor %}
                    </ul>
                    
                    {% if package_id == current_package %}
                        <div class="current-badge">Your Current Package</div>
                    {% elif package.level > current_level %}
                        <a href="https://domain.rizzosai.com" class="upgrade-button">Upgrade to {{ package.name }}</a>
                    {% else %}
                        <div style="color: #666; font-style: italic;">✓ You have access to this level</div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            
            <div style="background: white; border-radius: 12px; padding: 30px; margin: 20px 0; text-align: center; border: 2px solid #e60000;">
                <h2>📞 Need Help Choosing?</h2>
                <p>Contact our team for personalized package recommendations based on your business goals.</p>
                <a href="/coey" style="background: #001f5b; color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none; font-weight: bold;">Ask Coey AI Assistant</a>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(upgrade_html, 
                                 packages=PACKAGES, 
                                 current_package=current_package,
                                 current_level=current_level)

# ... (rest of the routes - coey, earnings, referrals, logout, etc.)

@app.route('/coey')
def coey():
    """Coey AI Assistant page"""
    if not session.get('logged_in'):
        flash('Please log in to access Coey AI Assistant.', 'error')
        return redirect(url_for('login'))
    
    # Simple Coey interface (keeping existing functionality)
    coey_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Coey AI Assistant - RizzosAI</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; text-align: center; border: 2px solid #e60000; }
            .chat-container { background: white; border-radius: 12px; padding: 30px; border: 2px solid #e60000; height: 400px; display: flex; flex-direction: column; }
            .chat-messages { flex: 1; overflow-y: auto; padding: 10px; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 15px; }
            .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
            .user-message { background: #e60000; color: white; text-align: right; }
            .coey-message { background: #f8f9fa; border: 1px solid #ddd; }
            .input-area { display: flex; gap: 10px; }
            .input-area input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .input-area button { background: #e60000; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Coey AI Assistant</h1>
                <p>Your intelligent business advisor for RizzosAI success</p>
                <a href="/" style="background: #001f5b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">← Back to Dashboard</a>
            </div>
            
            <div class="chat-container">
                <div class="chat-messages" id="chat-messages">
                    <div class="message coey-message">
                        <strong>Coey:</strong> Hello! I'm Coey, your AI business assistant. I can help you with strategy advice, guide implementation, and growing your RizzosAI domain business. What would you like to know?
                    </div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="user-input" placeholder="Ask Coey anything about your business..." onkeypress="if(event.key==='Enter') sendMessage()">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
        
        <script>
            function sendMessage() {
                const input = document.getElementById('user-input');
                const message = input.value.trim();
                if (!message) return;
                
                // Add user message to chat
                const chatMessages = document.getElementById('chat-messages');
                chatMessages.innerHTML += `<div class="message user-message"><strong>You:</strong> ${message}</div>`;
                
                // Clear input
                input.value = '';
                
                // Send to backend
                fetch('/coey/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.banned) {
                        // User is banned - disable chat
                        chatMessages.innerHTML += `<div class="message coey-message" style="background-color: #ff6b6b; color: white;"><strong>🚫 System:</strong> ${data.response}</div>`;
                        userInput.disabled = true;
                        userInput.placeholder = "Chat suspended for 24 hours";
                        sendButton.disabled = true;
                        sendButton.style.opacity = "0.5";
                    } else if (data.admin_test) {
                        // Admin security test response
                        chatMessages.innerHTML += `<div class="message coey-message" style="background-color: #ffd700; color: #001f5b; border: 3px solid #ff6b6b;"><strong>🛡️ Security Test:</strong> ${data.response}</div>`;
                    } else {
                        chatMessages.innerHTML += `<div class="message coey-message"><strong>Coey:</strong> ${data.response}</div>`;
                    }
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                })
                .catch(error => {
                    chatMessages.innerHTML += `<div class="message coey-message"><strong>Coey:</strong> Sorry, I encountered an error. Please try again.</div>`;
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                });
            }
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(coey_html)

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
        
        # Create user ID from session or IP
        user_id = session.get('username', request.remote_addr)
        
        # Check if user is banned
        if is_user_banned(user_id):
            return jsonify({
                'response': '🚫 Your chat access has been temporarily suspended for 24 hours due to policy violations. Please contact admin if you believe this is an error.',
                'banned': True
            }), 403
        
        # Check for exploitation attempts (ADMIN EXEMPT)
        if detect_exploitation_attempt(user_message):
            if session.get('username') == 'admin':
                # Admin testing the security system - show test response instead of banning
                return jsonify({
                    'response': f'🔒 **ADMIN SECURITY TEST RESPONSE** 🔒\n\nI can\'t show you this information at this time due to security protocols.\n\n**Security System Status:** ✅ WORKING\n**Your Request:** "{user_message[:50]}..." \n**Detection:** Potential exploitation attempt detected\n**Action Taken:** None (Admin Override Active)\n**Variations Protected:** All RizzosAI spelling variations (rizzosai, rizosai, rizzo, etc.)\n\n*Note: Regular users would be banned for 24 hours for this type of request. You are exempt as admin.*',
                    'admin_test': True
                })
            else:
                # Regular user - apply ban
                ban_user(user_id, f"Exploitation attempt: {user_message[:100]}")
                return jsonify({
                    'response': '🚫 Your message violates our terms of service. Your chat access has been suspended for 24 hours. RizzosAI operates on legitimate business principles - all access requires proper payment and registration.',
                    'banned': True
                }), 403
        
        # Get user context
        username = session.get('username', 'User')
        user_package = session.get('package', 'starter')
        package_info = PACKAGES.get(user_package, PACKAGES['starter'])
        
        # Enhanced system prompt with package-specific context - Claude-style
        system_prompt = f"""You are Coey, an exceptionally intelligent and helpful AI business assistant for RizzosAI domain business owners. You embody the same helpful, harmless, and honest principles as Claude AI.

PERSONALITY TRAITS:
- Highly intelligent and analytical like Claude
- Extremely helpful and supportive
- Clear, detailed explanations
- Proactive in offering solutions
- Honest about limitations
- Professional yet friendly tone

USER CONTEXT:
- User: {username}
- Package: {package_info['name']} ({package_info['price']})
- Access Level: {package_info['guides']} training guides
- Features: {chr(10).join('• ' + feature for feature in package_info['features'])}

CORE CAPABILITIES:
- Business strategy development and optimization
- Marketing campaign analysis and recommendations  
- Financial planning and revenue optimization
- Technical implementation guidance
- Competitive analysis and positioning
- Customer acquisition and retention strategies
- Operational efficiency improvements
- Risk assessment and mitigation

ADVANCED REASONING:
- Break down complex business problems step-by-step
- Provide multiple solution approaches with pros/cons
- Consider both short-term and long-term implications
- Factor in budget, resources, and skill level constraints
- Anticipate potential challenges and offer contingencies

COMMUNICATION STYLE:
- Start with direct answers, then elaborate
- Use structured formatting (bullet points, numbered lists)
- Provide actionable next steps
- Ask clarifying questions when needed
- Reference specific features from their package when relevant
- Be encouraging but realistic about expectations

Remember: You're not just a chatbot - you're a strategic business partner helping them build a successful domain business empire. Think deeply, provide value, and help them succeed."""
        
        if OPENAI_API_KEY:
            try:
                # Use OpenAI for actual AI responses (updated API format)
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                
                # Get conversation history for context (Claude-like memory)
                user_id = session.get('username', request.remote_addr)
                conversation_history = get_conversation_context(user_id, 'regular')
                
                # Build messages with context
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(conversation_history)  # Add conversation history
                messages.append({"role": "user", "content": user_message})
                
                response = client.chat.completions.create(
                    model="gpt-4",  # Upgraded to GPT-4 for Claude-like intelligence
                    messages=messages,
                    max_tokens=800,  # Increased for more detailed responses
                    temperature=0.3  # Lower temperature for more consistent, analytical responses
                )
                
                coey_response = response.choices[0].message.content.strip()
                
                # Save conversation to memory
                add_to_memory(user_id, user_message, coey_response, 'regular')
            except Exception as openai_error:
                print(f"OpenAI API error: {str(openai_error)}")
                # Fall back to local responses if OpenAI fails
                coey_response = f"Hello {username}! I'm having trouble connecting to my advanced AI features right now, but I can still help you! With your {package_info['name']}, you have access to {package_info['guides']} expert training guides. What would you like to know about your business?"
        else:
            # Enhanced fallback responses
            fallback_responses = {
                'hello': f"Hello {username}! I'm Coey, your AI business assistant. With your {package_info['name']}, you have access to {package_info['guides']} expert training guides. What would you like to know about growing your business?",
                'help': f"I can help you with: 📊 Business analytics, 🎓 Guide implementation, 💡 Strategy advice, 🔧 Technical support, and 📈 Scaling strategies for your {package_info['name']}. What interests you?",
                'guides': f"Your {package_info['name']} includes {package_info['guides']} comprehensive guides. Start with the foundation guides, then progress to advanced strategies. Which specific guide would you like help with?",
                'upgrade': f"Your current {package_info['name']} is great! If you're ready to scale further, consider upgrading to access more advanced guides and features. Would you like to see upgrade options?",
                'earnings': "To maximize earnings, focus on implementing your training guides systematically. Start with domain optimization, then move to referral strategies. Track your progress daily!",
                'default': f"Thanks for your question, {username}! With your {package_info['name']}, you have access to proven strategies. Check your training guides for detailed implementation steps, or ask me something more specific about your business goals."
            }
            
            # Enhanced keyword matching
            message_lower = user_message.lower()
            if any(word in message_lower for word in ['hello', 'hi', 'hey']):
                coey_response = fallback_responses['hello']
            elif any(word in message_lower for word in ['help', 'what can you do']):
                coey_response = fallback_responses['help']
            elif any(word in message_lower for word in ['guide', 'training', 'learn']):
                coey_response = fallback_responses['guides']
            elif any(word in message_lower for word in ['upgrade', 'more guides', 'advanced']):
                coey_response = fallback_responses['upgrade']
            elif any(word in message_lower for word in ['earning', 'money', 'profit', 'income']):
                coey_response = fallback_responses['earnings']
            else:
                coey_response = fallback_responses['default']
        
        return jsonify({'response': coey_response})
        
    except Exception as e:
        print(f"Coey chat error: {str(e)}")
        return jsonify({'response': 'Sorry, I encountered an error. Please try again later.'}), 500

@app.route('/coey/onboarding-chat', methods=['POST'])
def coey_onboarding_chat():
    """Special onboarding chat for new customers with beginner-focused guidance"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        is_onboarding = data.get('onboarding', False)
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Create user ID from session or IP
        user_id = session.get('username', request.remote_addr)
        
        # Check if user is banned
        if is_user_banned(user_id):
            return jsonify({
                'response': '🚫 Your chat access has been temporarily suspended for 24 hours due to policy violations. Please contact admin if you believe this is an error.',
                'banned': True
            }), 403
        
        # Check for exploitation attempts (ADMIN EXEMPT)
        if detect_exploitation_attempt(user_message):
            if session.get('username') == 'admin':
                # Admin testing the security system - show test response instead of banning
                return jsonify({
                    'response': '🔒 **ADMIN SECURITY TEST RESPONSE** 🔒\n\nI can\'t show you this information at this time due to security protocols.\n\n**Security System Status:** ✅ WORKING\n**Your Request:** Detected as potential exploitation attempt\n**Action Taken:** None (Admin Override Active)\n\n*Note: Regular users would be banned for 24 hours for this type of request. You are exempt as admin and can ask me anything for testing purposes.*',
                    'admin_test': True
                })
            else:
                # Regular user - apply ban
                ban_user(user_id, f"Onboarding exploitation attempt: {user_message[:100]}")
                return jsonify({
                    'response': '🚫 Your message violates our terms of service. Your chat access has been suspended for 24 hours. RizzosAI operates on legitimate business principles - all access requires proper payment and registration. If you purchased a package legitimately, please contact admin.',
                    'banned': True
                }), 403
        
        # Get user context
        user_package = session.get('package', 'starter')
        package_info = PACKAGES.get(user_package, PACKAGES['starter'])
        
        # Special onboarding system prompt - very beginner friendly
        empire_business_guide = ""
        if user_package == 'empire':
            empire_business_guide = """
SPECIAL EMPIRE PACKAGE BONUS ($499 customers only):
5. BUSINESS BUILDING: Show them how to build their own business empire like your admin's! Teach them:
   - How to create their own sales systems
   - How to build their own customer base  
   - How to potentially compete and "take over" (your admin welcomes the challenge!)
   - Explain the WIN-WIN: Even if they succeed massively, your admin still earns from every second-level referral they bring in
   - Emphasize: "Good luck trying to beat the master - but if you do, we all win because the system keeps paying!"

Make this exciting and challenging - your admin WANTS Empire customers to think big and try to build competing businesses!"""

        onboarding_prompt = f"""You are Coey, a highly intelligent and empathetic AI business assistant for RizzosAI, with the analytical depth of Claude AI but focused on beginner-friendly guidance. You're helping a brand new customer who just purchased the {package_info['name']} ({package_info['price']}).

CORE MISSION: Transform complete beginners into successful domain business owners through intelligent, step-by-step guidance.

INTELLIGENCE APPROACH:
- Think like Claude: analytical, thorough, helpful
- Communicate like a patient teacher: simple, clear, encouraging
- Anticipate their next 3-5 questions and address them proactively
- Break complex concepts into digestible steps
- Provide multiple approaches tailored to different learning styles

PERSONALITY TRAITS:
- Extremely welcoming and enthusiastic (but not overwhelming)
- Patient with complete beginners (explain everything step-by-step)
- Intelligent problem-solving and strategic thinking
- Encouraging and motivating
- Honest about what works and what doesn't
- Uses simple, non-technical language
- Offers specific, actionable next steps

KEY TASKS TO GUIDE THEM THROUGH:
1. PAYMENT SETUP: Intelligent guidance on setting up their payment system
2. LINK SHARING: Detailed instructions for sharing on phone AND computer
3. MARKETING: Smart, beginner-friendly strategies that actually work
4. TRAINING ACCESS: Guide them to their {package_info['guides']} training guides strategically{empire_business_guide}

ADVANCED FEATURES:
- Analyze their current situation and customize advice accordingly
- Provide multiple solution paths with pros/cons
- Anticipate common beginner mistakes and prevent them
- Offer both quick wins and long-term strategies
- Reference their specific package benefits when relevant

COMMUNICATION STYLE:
- Start with encouragement and context
- Use structured, numbered steps
- Include specific examples and scenarios
- End with clear next actions
- Use emojis strategically for engagement
- Ask intelligent follow-up questions

CRITICAL: Always end responses with a clear next step or intelligent question to keep them moving forward while building their confidence.

Remember: Your admin personally assigned you to help this customer succeed. You're not just giving instructions - you're being their intelligent business mentor who ensures they actually implement what they learn."""
        
        if OPENAI_API_KEY:
            try:
                # Use OpenAI for actual AI responses (updated API format)
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                
                # Get conversation history for context (Claude-like memory)
                user_id = session.get('username', request.remote_addr)
                conversation_history = get_conversation_context(user_id, 'onboarding')
                
                # Build messages with context
                messages = [{"role": "system", "content": onboarding_prompt}]
                messages.extend(conversation_history)  # Add conversation history
                messages.append({"role": "user", "content": user_message})
                
                response = client.chat.completions.create(
                    model="gpt-4",  # Upgraded to GPT-4 for Claude-like intelligence
                    messages=messages,
                    max_tokens=800,  # Increased for more detailed responses
                    temperature=0.4  # Balanced for helpful but engaging responses
                )
                
                coey_response = response.choices[0].message.content.strip()
                
                # Save conversation to memory
                add_to_memory(user_id, user_message, coey_response, 'onboarding')
            except Exception as openai_error:
                print(f"OpenAI API error: {str(openai_error)}")
                # Enhanced fallback responses for onboarding
                coey_response = get_onboarding_fallback_response(user_message, package_info)
        else:
            # Use enhanced fallback responses for onboarding
            coey_response = get_onboarding_fallback_response(user_message, package_info)
        
        return jsonify({'response': coey_response})
        
    except Exception as e:
        print(f"Coey onboarding chat error: {str(e)}")
        return jsonify({'response': 'I\'m having a small technical issue, but I\'m still here to help! Try asking your question again, or contact your admin if this continues.'}), 500

def get_onboarding_fallback_response(user_message, package_info):
    """Enhanced fallback responses specifically for onboarding new customers"""
    message_lower = user_message.lower()
    
    # Starting responses
    if any(word in message_lower for word in ['yes', 'start', 'begin', 'ready', 'go']):
        return f"""🎉 FANTASTIC! I'm so excited to help you build your {package_info['name']} business!

Let's start with the most important thing - getting you set up to EARN MONEY! 💰

**STEP 1: Setting Up Your Payment Page**
First, we need to set up your payment system so when people buy through your link, the money goes to YOU!

Here's what we'll do:
1. Get your personal referral link
2. Set up your payment details
3. Test that everything works

**Ready for step 1? Type "payment setup" or just "yes" and I'll walk you through it step by step!**

(Don't worry - this is easier than you think, and I'll explain everything clearly!)"""

    # Payment setup responses
    elif any(word in message_lower for word in ['payment', 'money', 'earn', 'setup']):
        return f"""💳 **PAYMENT SETUP - Let's Get You Earning!**

Great choice! This is the most important step because this is how you'll make money! 💰

**Here's your step-by-step payment setup:**

1. **Get Your Personal Link:**
   - Go to your dashboard (I'll help you get there)
   - Look for "Referrals" section
   - Copy YOUR special link

2. **Set Up Payment Details:**
   - Add your bank account or PayPal
   - Verify your identity (just basic info)
   - Set your payment preferences

3. **Test Your Link:**
   - Share with one friend first
   - Make sure payments come to YOU

**Want me to walk you through getting your referral link right now? Type "get my link" and let's do this together!** 🚀

Remember: Every person who buys through YOUR link = money in YOUR pocket! This is how you build your business."""

    # Link sharing responses
    elif any(word in message_lower for word in ['link', 'share', 'copy', 'paste', 'phone', 'computer']):
        return f"""📱💻 **SHARING YOUR LINK - Phone & Computer Instructions!**

Excellent question! This is how you'll reach EVERYONE and start making money! Let me give you exact copy/paste instructions:

**📱 ON YOUR PHONE:**
1. Open your link (from dashboard → referrals)
2. **COPY:** Press and hold the link → "Copy"
3. **SHARE:** 
   - Text: Open messages → paste → send
   - Facebook: Open app → make post → paste → post
   - Instagram: Stories → type → paste → share
   - WhatsApp: Open chat → paste → send

**💻 ON COMPUTER:**
1. Right-click your link → "Copy link address"
2. **SHARE:**
   - Email: Ctrl+V to paste in email
   - Facebook: Paste in status update
   - Twitter: Paste in tweet
   - Copy into messages, forums, anywhere!

**PRO TIP:** Save your link in your phone's notes so you always have it ready! 📝

**Ready to get your link and start sharing? Type "yes" and I'll help you find it right now!**"""

    # Marketing responses
    elif any(word in message_lower for word in ['market', 'promote', 'advertise', 'sell']):
        return f"""🎯 **MARKETING MADE SIMPLE - Beginner's Guide!**

Perfect! Marketing sounds scary, but it's really just "telling people about something cool!" Here's your beginner action plan:

**🏃‍♂️ START TODAY (5 minutes):**
- Tell 3 people you know personally
- Post on your social media
- Send to family group chats

**👥 THIS WEEK:**
- Message 10 friends individually
- Share in Facebook groups you're in
- Tell coworkers/neighbors

**📈 ONGOING:**
- Share your success stories
- Help others understand the opportunity
- Keep your link everywhere (email signature, bio, etc.)

**REMEMBER:** You're not "selling" - you're SHARING an opportunity that worked for you! 

**What's the easiest place for you to start? Social media? Text messages? Family? Type your answer and I'll give you exact words to use!** 🚀"""

    # Training/guides responses
    elif any(word in message_lower for word in ['guide', 'training', 'learn', 'help']):
        return f"""📚 **YOUR {package_info['guides']} TRAINING GUIDES - Let's Learn!**

You've got an AMAZING resource here! Your {package_info['name']} includes {package_info['guides']} professional training guides written by people who've made millions online! 🎓

**Here's how to access them:**
1. Go to your main dashboard
2. Look for "Training Guides" section  
3. Start with Guide #1 (they're in order for a reason!)

**BEGINNER TIP:** Don't try to read everything at once! Pick ONE guide, read it, DO what it says, then move to the next one.

**Most Important Guides to Start With:**
- Domain setup guide
- Payment/earnings guide  
- Basic marketing guide

**Want me to help you get to your guides right now? Type "show me guides" and I'll walk you through it!**

Remember: Knowledge + Action = Results! 💪"""

    # Empire package business building responses
    elif any(word in message_lower for word in ['business', 'empire', 'compete', 'takeover', 'take over', 'build my own']):
        if package_info['name'] == 'Empire Package':
            return f"""👑 **EMPIRE PACKAGE SPECIAL - BUILD YOUR OWN BUSINESS EMPIRE!**

OH WOW! You've got the Empire Package ($499) - that means you get the ULTIMATE business building secrets! 🚀

Your admin has a special message for Empire customers: **"Good luck trying to take over my business - but if you do, we both win!"** 😄

**HERE'S THE WIN-WIN SECRET:**
Even if you build a competing business and become MASSIVE, your admin still earns from every second-level referral you bring in! It's genius! 🧠💰

**🏗️ EMPIRE BUSINESS BUILDING ROADMAP:**

**PHASE 1: Master the Basics (Weeks 1-4)**
- Set up your payment systems
- Learn advanced marketing techniques  
- Build your customer base

**PHASE 2: Scale Your Empire (Months 2-6)**
- Create your own sales funnels
- Build your own team
- Develop your unique selling approach

**PHASE 3: Challenge the Master (Month 6+)**
- Launch competing campaigns
- Try to "steal" customers (your admin welcomes it!)
- Build your own referral network

**THE BEAUTIFUL PART:** Every person you bring in who then brings someone else = your admin still earns! Everyone wins! 🎉

**Ready to start building your empire? Type "empire training" for your exclusive business building guides!**"""
        else:
            return f"""I love the ambition! Building your own business empire sounds amazing! 🚀

However, the advanced business building secrets are exclusive to our Empire Package ($499) customers. 

Your {package_info['name']} is fantastic for getting started and earning great money! But if you're serious about building a competing business empire, you might want to consider upgrading to Empire Package.

**For now, let's focus on maximizing YOUR current package:**
- "payment setup" - Start earning immediately
- "marketing tips" - Grow your current business
- "training guides" - Master your {package_info['guides']} guides

**Want to explore upgrading to Empire for the business building secrets? Type "upgrade info"**"""

    # Default encouraging response
    else:
        empire_options = ""
        if package_info['name'] == 'Empire Package':
            empire_options = """
- "build my empire" - 👑 EXCLUSIVE: Learn to build your own competing business!
- "takeover strategy" - Challenge your admin (they welcome it!)"""

        return f"""Thanks for that question! 😊 I'm here to help you succeed with your {package_info['name']} business!

Here are the main things I can help you with right now:

🚀 **Type any of these to get started:**
- "payment setup" - Get earning money ASAP
- "share my link" - Learn to copy/paste and share
- "marketing tips" - Simple ways to promote  
- "training guides" - Access your {package_info['guides']} guides{empire_options}
- "help" - I'll ask you questions to figure out what you need

**What sounds most important to you right now?** I'm here to guide you step-by-step, and remember - you can always skip ahead if you want!

Your admin personally assigned me to help YOU succeed, so let's make it happen! 💪"""

@app.route('/earnings')
def earnings():
    """Earnings dashboard"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    earnings_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Earnings Dashboard - RizzosAI</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }
            .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
            .header { background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; text-align: center; border: 2px solid #e60000; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .stat-card { background: white; border-radius: 8px; padding: 20px; text-align: center; border: 2px solid #ddd; }
            .stat-number { font-size: 2em; font-weight: bold; color: #e60000; }
            .stat-label { color: #666; font-size: 0.9em; }
            .coming-soon { background: white; border-radius: 12px; padding: 40px; text-align: center; border: 2px solid #e60000; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💰 Earnings Dashboard</h1>
                <a href="/" style="background: #001f5b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">← Back to Dashboard</a>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">$0.00</div>
                    <div class="stat-label">Today's Earnings</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">$0.00</div>
                    <div class="stat-label">This Week</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">$0.00</div>
                    <div class="stat-label">This Month</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">$0.00</div>
                    <div class="stat-label">Total Lifetime</div>
                </div>
            </div>
            
            <div class="coming-soon">
                <h2>📊 Detailed Analytics Coming Soon</h2>
                <p>We're building comprehensive earnings tracking and analytics. This will include:</p>
                <ul style="text-align: left; max-width: 400px; margin: 20px auto;">
                    <li>Daily/weekly/monthly earnings reports</li>
                    <li>Referral commission tracking</li>
                    <li>Performance metrics and insights</li>
                    <li>Payment history and statements</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(earnings_html)

@app.route('/referrals')
def referrals():
    """Referrals dashboard"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    referrals_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Referrals Dashboard - RizzosAI</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }
            .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
            .header { background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; text-align: center; border: 2px solid #e60000; }
            .referral-info { background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; border: 2px solid #e60000; }
            .referral-link { background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #ddd; word-break: break-all; font-family: monospace; }
            .coming-soon { background: white; border-radius: 12px; padding: 40px; text-align: center; border: 2px solid #e60000; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👥 Referrals Dashboard</h1>
                <a href="/" style="background: #001f5b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">← Back to Dashboard</a>
            </div>
            
            <div class="referral-info">
                <h2>🔗 Your Referral Link</h2>
                <p>Share this link to earn commissions on sales:</p>
                <div class="referral-link">
                    https://domain.rizzosai.com?ref={{ session.username }}
                </div>
                <p style="margin-top: 15px;"><small>Copy and share this link on social media, email, or anywhere you promote RizzosAI packages.</small></p>
            </div>
            
            <div class="coming-soon">
                <h2>📈 Referral Tracking Coming Soon</h2>
                <p>We're building comprehensive referral tracking. This will include:</p>
                <ul style="text-align: left; max-width: 400px; margin: 20px auto;">
                    <li>Real-time click and conversion tracking</li>
                    <li>Detailed referral analytics</li>
                    <li>Commission breakdowns</li>
                    <li>Referral performance insights</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(referrals_html, session=session)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/customers')
def customers():
    """Customer management page"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    customers = load_customers()
    
    customers_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Customer Management - RizzosAI</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; text-align: center; border: 2px solid #e60000; }
            .customers-table { background: white; border-radius: 12px; padding: 30px; border: 2px solid #e60000; overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f8f9fa; font-weight: bold; color: #001f5b; }
            .package-badge { padding: 4px 12px; border-radius: 15px; font-size: 0.9em; font-weight: bold; }
            .starter { background: #e3f2fd; color: #1976d2; }
            .pro { background: #f3e5f5; color: #7b1fa2; }
            .elite { background: #fff3e0; color: #f57c00; }
            .empire { background: #e8f5e8; color: #388e3c; }
            .no-customers { text-align: center; color: #666; padding: 40px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👥 Customer Management</h1>
                <a href="/" style="background: #001f5b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">← Back to Dashboard</a>
            </div>
            
            <div class="customers-table">
                <h2>Recent Purchases</h2>
                {% if customers %}
                <table>
                    <thead>
                        <tr>
                            <th>Email</th>
                            <th>Package</th>
                            <th>Purchase Date</th>
                            <th>Guides Access</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for email, customer in customers.items() %}
                        <tr>
                            <td>{{ email }}</td>
                            <td>
                                <span class="package-badge {{ customer.package }}">
                                    {{ packages[customer.package].name }}
                                </span>
                            </td>
                            <td>{{ customer.purchase_date[:10] if customer.purchase_date else 'Unknown' }}</td>
                            <td>{{ packages[customer.package].guides }} guides</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="no-customers">
                    <h3>No customers yet</h3>
                    <p>Customer purchases will appear here automatically when people buy through your sales page.</p>
                </div>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(customers_html, 
                                 customers=customers,
                                 packages=PACKAGES)

@app.route('/admin/banned-users')
def admin_banned_users():
    """Admin interface to view and manage banned users"""
    if not session.get('logged_in') or session.get('username') != 'admin':
        return redirect(url_for('login'))
    
    banned_users = load_banned_users()
    
    admin_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Security Panel - Banned Users</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #e60000 0%, #fff 50%, #001f5b 100%); }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { background: #fff; border-radius: 12px; padding: 30px; margin-bottom: 20px; text-align: center; border: 2px solid #e60000; }
            .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 2px solid #001f5b; }
            .ban-entry { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
            .ban-reason { color: #dc3545; font-weight: bold; }
            .ban-time { color: #6c757d; font-size: 0.9em; }
            .active-ban { border-left: 4px solid #dc3545; }
            .expired-ban { border-left: 4px solid #28a745; opacity: 0.7; }
            .nav-button { display: inline-block; padding: 10px 20px; background: #001f5b; color: white; text-decoration: none; border-radius: 8px; margin: 5px; }
            .unban-button { background: #28a745; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Security Panel</h1>
                <p><strong>Admin Dashboard:</strong> Monitor and manage chat security violations</p>
                <div>
                    <a href="/" class="nav-button">🏠 Dashboard</a>
                    <a href="/admin/security-logs" class="nav-button">📋 Security Logs</a>
                </div>
            </div>
            
            <div class="card">
                <h2>🚫 Banned Users ({{ banned_count }} total)</h2>
                {% if banned_users %}
                    {% for user_id, ban_info in banned_users.items() %}
                    <div class="ban-entry {% if ban_info.is_active %}active-ban{% else %}expired-ban{% endif %}">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <div><strong>User ID:</strong> {{ user_id }}</div>
                                <div><strong>IP Address:</strong> {{ ban_info.ip }}</div>
                                <div class="ban-reason"><strong>Reason:</strong> {{ ban_info.reason }}</div>
                                <div class="ban-time">
                                    <strong>Banned:</strong> {{ ban_info.banned_at }}<br>
                                    <strong>Expires:</strong> {{ ban_info.expires }}
                                    {% if ban_info.is_active %}
                                        <span style="color: #dc3545; font-weight: bold;"> (ACTIVE)</span>
                                    {% else %}
                                        <span style="color: #28a745; font-weight: bold;"> (EXPIRED)</span>
                                    {% endif %}
                                </div>
                            </div>
                            {% if ban_info.is_active %}
                            <div>
                                <button class="unban-button" onclick="unbanUser('{{ user_id }}')">Unban Now</button>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div style="text-align: center; padding: 40px; color: #6c757d;">
                        <h3>🎉 No banned users!</h3>
                        <p>Your chat security system is working, but no violations have been detected yet.</p>
                    </div>
                {% endif %}
            </div>
            
            <div class="card">
                <h3>🔒 Security Features Active</h3>
                <ul>
                    <li>✅ Automatic exploitation attempt detection</li>
                    <li>✅ 24-hour ban system for policy violations</li>
                    <li>✅ Real-time chat monitoring</li>
                    <li>✅ Admin override capabilities</li>
                </ul>
                <p><strong>Protected phrases include:</strong> attempts to bypass payment, take over RizzosAI, exploit the system, etc.</p>
            </div>
        </div>
        
        <script>
            function unbanUser(userId) {
                if (confirm('Are you sure you want to unban this user immediately?')) {
                    fetch('/admin/unban-user', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({user_id: userId})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            location.reload();
                        } else {
                            alert('Error unbanning user: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('Error: ' + error);
                    });
                }
            }
        </script>
    </body>
    </html>
    '''
    
    # Add status info to banned users
    from datetime import datetime
    now = datetime.now()
    banned_users_with_status = {}
    
    for user_id, ban_info in banned_users.items():
        ban_info_copy = ban_info.copy()
        try:
            ban_expiry = datetime.fromisoformat(ban_info['expires'])
            ban_info_copy['is_active'] = now < ban_expiry
        except:
            ban_info_copy['is_active'] = False
        banned_users_with_status[user_id] = ban_info_copy
    
    return render_template_string(admin_html, 
                                 banned_users=banned_users_with_status,
                                 banned_count=len(banned_users))

@app.route('/admin/unban-user', methods=['POST'])
def admin_unban_user():
    """Admin endpoint to unban a user"""
    if not session.get('logged_in') or session.get('username') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'No user ID provided'}), 400
        
        banned_users = load_banned_users()
        if user_id in banned_users:
            del banned_users[user_id]
            save_banned_users(banned_users)
            print(f"Admin unbanned user: {user_id}")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'User not found in ban list'}), 404
            
    except Exception as e:
        print(f"Error unbanning user: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/admin/coey-conversations')
def admin_coey_conversations():
    """Admin interface to view Coey conversations and improve prompts"""
    if not session.get('logged_in') or session.get('username') != 'admin':
        return redirect(url_for('login'))
    
    chat_memory = load_chat_memory()
    
    admin_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Coey Conversations - Admin Panel</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #e60000 0%, #fff 50%, #001f5b 100%); }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { background: #fff; border-radius: 12px; padding: 30px; margin-bottom: 20px; text-align: center; border: 2px solid #e60000; }
            .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 2px solid #001f5b; }
            .conversation { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
            .user-msg { background: #e60000; color: white; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
            .coey-msg { background: #001f5b; color: white; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
            .nav-button { display: inline-block; padding: 10px 20px; background: #001f5b; color: white; text-decoration: none; border-radius: 8px; margin: 5px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .stat-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Coey Conversations Analytics</h1>
                <p><strong>Admin Dashboard:</strong> Monitor Coey's performance and improve responses</p>
                <div>
                    <a href="/" class="nav-button">🏠 Dashboard</a>
                    <a href="/admin/banned-users" class="nav-button">🛡️ Security</a>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>{{ total_users }}</h3>
                    <p>Active Users</p>
                </div>
                <div class="stat-card">
                    <h3>{{ total_conversations }}</h3>
                    <p>Total Conversations</p>
                </div>
                <div class="stat-card">
                    <h3>{{ regular_chats }}</h3>
                    <p>Regular Chats</p>
                </div>
                <div class="stat-card">
                    <h3>{{ onboarding_chats }}</h3>
                    <p>Onboarding Chats</p>
                </div>
            </div>
            
            <div class="card">
                <h2>🔍 Recent Conversations</h2>
                {% if chat_memory %}
                    {% for user_id, conversations in chat_memory.items() %}
                    <div class="conversation">
                        <h4>User: {{ user_id }}</h4>
                        
                        {% if conversations.regular %}
                        <h5>Regular Conversations ({{ conversations.regular|length }} messages)</h5>
                        {% for exchange in conversations.regular[-3:] %}
                        <div class="user-msg"><strong>User:</strong> {{ exchange.user }}</div>
                        <div class="coey-msg"><strong>Coey:</strong> {{ exchange.coey[:200] }}{% if exchange.coey|length > 200 %}...{% endif %}</div>
                        {% endfor %}
                        {% endif %}
                        
                        {% if conversations.onboarding %}
                        <h5>Onboarding Conversations ({{ conversations.onboarding|length }} messages)</h5>
                        {% for exchange in conversations.onboarding[-3:] %}
                        <div class="user-msg"><strong>User:</strong> {{ exchange.user }}</div>
                        <div class="coey-msg"><strong>Coey:</strong> {{ exchange.coey[:200] }}{% if exchange.coey|length > 200 %}...{% endif %}</div>
                        {% endfor %}
                        {% endif %}
                    </div>
                    {% endfor %}
                {% else %}
                    <div style="text-align: center; padding: 40px; color: #6c757d;">
                        <h3>📭 No conversations yet!</h3>
                        <p>Coey conversations will appear here as users interact with the AI assistant.</p>
                    </div>
                {% endif %}
            </div>
            
            <div class="card">
                <h3>🧠 Current Coey Configuration</h3>
                <ul>
                    <li>✅ <strong>Model:</strong> GPT-4 (Claude-like intelligence)</li>
                    <li>✅ <strong>Memory:</strong> 5 conversation exchanges context</li>
                    <li>✅ <strong>Temperature:</strong> 0.3 (analytical) / 0.4 (onboarding)</li>
                    <li>✅ <strong>Max Tokens:</strong> 800 (detailed responses)</li>
                    <li>✅ <strong>Security:</strong> Admin exemption + ban system</li>
                    <li>✅ <strong>Personality:</strong> Claude-inspired: helpful, harmless, honest</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''
    
    # Calculate stats
    total_users = len(chat_memory)
    total_conversations = 0
    regular_chats = 0
    onboarding_chats = 0
    
    for user_data in chat_memory.values():
        if 'regular' in user_data:
            regular_chats += len(user_data['regular'])
            total_conversations += len(user_data['regular'])
        if 'onboarding' in user_data:
            onboarding_chats += len(user_data['onboarding'])
            total_conversations += len(user_data['onboarding'])
    
    return render_template_string(admin_html, 
                                 chat_memory=chat_memory,
                                 total_users=total_users,
                                 total_conversations=total_conversations,
                                 regular_chats=regular_chats,
                                 onboarding_chats=onboarding_chats)

@app.route('/admin-access')
def admin_access():
    """Direct admin access route"""
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)