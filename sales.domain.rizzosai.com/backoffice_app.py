from flask import Flask, request, redirect, url_for, session, flash, render_template_string, jsonify
import os
import openai
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rizzos-secret-key-2024-secure')

# Configure OpenAI for Coey
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'rizzos2024')

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
                <a href="/earnings" class="nav-button">💰 Earnings</a>
                <a href="/referrals" class="nav-button">👥 Referrals</a>
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
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            
            # Check for package parameter from redirect
            package_type = request.args.get('package', 'starter')
            if package_type in PACKAGES:
                session['package'] = package_type
            else:
                session['package'] = 'starter'
            
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
                    chatMessages.innerHTML += `<div class="message coey-message"><strong>Coey:</strong> ${data.response}</div>`;
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
        
        # Get user context
        username = session.get('username', 'User')
        user_package = session.get('package', 'starter')
        package_info = PACKAGES.get(user_package, PACKAGES['starter'])
        
        # Enhanced system prompt with package-specific context
        system_prompt = f"""You are Coey, an AI business assistant for RizzosAI domain business owners. 
        You help users with their {package_info['name']} ({package_info['price']}) package.
        
        The user {username} has access to {package_info['guides']} training guides and these features:
        {chr(10).join('- ' + feature for feature in package_info['features'])}
        
        You help users with:
        - Understanding their training guides and how to implement them
        - Business strategy advice for domain and referral marketing  
        - Technical help with their backoffice and domain setup
        - Analytics and performance insights
        - Scaling their online business based on their package level
        - Package upgrade recommendations when appropriate
        
        Be helpful, encouraging, and provide actionable advice. Keep responses concise but informative.
        Reference their specific package level and available guides when relevant."""
        
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

@app.route('/admin-access')
def admin_access():
    """Direct admin access route"""
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)