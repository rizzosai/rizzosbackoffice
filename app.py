from flask import Flask, request, redirect, url_for, session, flash, render_template_string, jsonify
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rizzos-secret-key-2024-secure')

# Configure OpenAI for Coey - FRESH CLEAN IMPLEMENTATION
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

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
    """Get conversation history for context"""
    memory = load_chat_memory()
    if user_id not in memory or conversation_type not in memory[user_id]:
        return []
    
    # Convert to OpenAI message format
    messages = []
    for exchange in memory[user_id][conversation_type]:
        messages.append({"role": "user", "content": exchange['user']})
        messages.append({"role": "assistant", "content": exchange['coey']})
    
    return messages

def load_customers():
    """Load customer data from JSON file"""
    try:
        with open(CUSTOMERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_customers(customers):
    """Save customer data to JSON file"""
    with open(CUSTOMERS_FILE, 'w') as f:
        json.dump(customers, f, indent=2)

def add_customer(email, package):
    """Add a new customer with their package"""
    customers = load_customers()
    customers[email] = {
        'package': package,
        'signup_date': datetime.now().isoformat(),
        'last_login': None
    }
    save_customers(customers)

def get_customer_package(email):
    """Get customer's package type"""
    customers = load_customers()
    return customers.get(email, {}).get('package', None)

def update_customer_login(email):
    """Update customer's last login time"""
    customers = load_customers()
    if email in customers:
        customers[email]['last_login'] = datetime.now().isoformat()
        save_customers(customers)

def load_banned_users():
    """Load banned users from JSON file"""
    try:
        with open(BANNED_USERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_banned_users(banned_users):
    """Save banned users to JSON file"""
    with open(BANNED_USERS_FILE, 'w') as f:
        json.dump(banned_users, f, indent=2)

def ban_user(user_id, reason="Policy violation"):
    """Ban a user for 24 hours"""
    banned_users = load_banned_users()
    ban_until = datetime.now() + timedelta(hours=24)
    banned_users[user_id] = {
        'banned_until': ban_until.isoformat(),
        'reason': reason,
        'banned_at': datetime.now().isoformat()
    }
    save_banned_users(banned_users)

def is_user_banned(user_id):
    """Check if user is currently banned"""
    # Admin is never banned
    if user_id == ADMIN_USERNAME:
        return False
        
    banned_users = load_banned_users()
    if user_id not in banned_users:
        return False
    
    ban_until = datetime.fromisoformat(banned_users[user_id]['banned_until'])
    if datetime.now() > ban_until:
        # Ban expired, remove from list
        del banned_users[user_id]
        save_banned_users(banned_users)
        return False
    
    return True

def unban_user(user_id):
    """Manually unban a user (admin function)"""
    banned_users = load_banned_users()
    if user_id in banned_users:
        del banned_users[user_id]
        save_banned_users(banned_users)
        return True
    return False

def detect_exploitation_attempt(message):
    """Detect potential exploitation attempts in user messages"""
    exploitation_patterns = [
        "take over rizzosai without paying",
        "hack rizzosai",
        "bypass payment",
        "free access to everything",
        "steal the business model",
        "copy your system for free",
        "get empire package without paying",
        "exploit the system",
        "backdoor access",
        "admin privileges",
        "override security",
        "crack the system"
    ]
    
    message_lower = message.lower()
    for pattern in exploitation_patterns:
        if pattern in message_lower:
            return True
    return False

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
    },
    'empire-trial': {
        'name': 'Empire Free Trial',
        'price': 'FREE',
        'guides': 3,   # Very limited - just enough to hook them
        'level': 1,    # Starter level only 
        'features': [
            '🎯 FREE 3-day Empire preview (normally $499)',
            'Access to 3 starter guides only',
            'See what you\'re missing with locked premium content',
            'Limited dashboard - upgrade prompts everywhere',
            '⏰ Trial expires in 72 hours - upgrade to keep access',
            '🔒 25+ advanced Empire guides locked',
            '📧 Email capture for upgrade sequence automation'
        ]
    }
}

# FRESH CLEAN OpenAI CHAT FUNCTION
def get_coey_response(user_message, package_info, username, conversation_type='regular'):
    """Get response from Coey AI - COMPLETELY FRESH IMPLEMENTATION"""
    
    system_prompt = f"""You are Coey, the intelligent AI business assistant for RizzosAI. You help customers maximize their domain business success.

CUSTOMER CONTEXT:
- Username: {username}
- Package: {package_info['name']} ({package_info['price']})
- Access Level: {package_info['guides']} training guides
- Your role: Strategic business advisor and implementation guide

CORE PERSONALITY:
- Professional yet approachable business mentor
- Strategic thinker focused on actionable solutions
- Claude-like intelligence with deep analytical thinking
- Results-oriented with emphasis on implementation

Remember: You're helping them build a successful domain business empire. Think deeply, provide value, and help them succeed."""

    # Try OpenAI API with completely fresh, clean implementation
    if OPENAI_API_KEY and OPENAI_API_KEY != 'your-openai-key-here':
        try:
            # COMPLETELY FRESH OpenAI import and initialization
            import openai
            openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            # Get conversation history for context
            user_id = username if username else 'anonymous'
            conversation_history = get_conversation_context(user_id, conversation_type)
            
            # Build messages with context
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": user_message})
            
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=800,
                temperature=0.3
            )
            
            coey_response = response.choices[0].message.content.strip()
            
            # Save conversation to memory
            add_to_memory(user_id, user_message, coey_response, conversation_type)
            return coey_response
            
        except Exception as openai_error:
            print(f"OpenAI API error: {str(openai_error)}")
            # Return helpful fallback message
            return f"🤖 Hi {username}! I'm temporarily running in offline mode while our systems update. I can still help you with your {package_info['name']} business! You have access to {package_info['guides']} expert training guides. What would you like to know about your business setup?"
    
    # Enhanced fallback responses
    fallback_responses = {
        'hello': f"Hello {username}! I'm Coey, your AI business assistant. With your {package_info['name']}, you have access to {package_info['guides']} expert training guides. What would you like to know about growing your business?",
        'help': f"I can help you with: 📊 Business analytics, 🎓 Guide implementation, 💡 Strategy advice, 🔧 Technical support, and 📈 Scaling strategies for your {package_info['name']}. What interests you?",
        'guides': f"Your {package_info['name']} includes {package_info['guides']} comprehensive guides. Start with the foundation guides, then progress to advanced strategies. Which specific guide would you like help with?",
        'default': f"Thanks for your question, {username}! With your {package_info['name']}, you have access to proven strategies. Check your training guides for detailed implementation steps, or ask me something more specific about your business goals."
    }
    
    # Enhanced keyword matching
    message_lower = user_message.lower()
    if any(word in message_lower for word in ['hello', 'hi', 'hey']):
        return fallback_responses['hello']
    elif any(word in message_lower for word in ['help', 'what can you do']):
        return fallback_responses['help']
    elif any(word in message_lower for word in ['guides', 'training']):
        return fallback_responses['guides']
    else:
        return fallback_responses['default']

if __name__ == '__main__':
    app.run(debug=True)