from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
import os
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    """Main sales page for RizzosAI domain packages"""
    return render_template('index.html')

@app.route('/packages')
def packages():
    """Detailed packages page"""
    return render_template('packages.html')

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Webhook endpoint for Stripe payments - integrates with Zapier"""
    try:
        data = request.get_json()
        
        # Log the webhook for debugging
        app.logger.info(f"Received Stripe webhook: {data}")
        
        # Extract customer and package information
        if data and 'customer_email' in data:
            customer_email = data.get('customer_email')
            package_type = data.get('package_type', 'starter')
            customer_name = data.get('customer_name', '')
            
            # This data can be used by Zapier to:
            # 1. Create customer account in backoffice
            # 2. Send welcome email with guides
            # 3. Set up customer access
            
            app.logger.info(f"Processing purchase: {customer_email}, Package: {package_type}")
            
            return jsonify({
                'status': 'success',
                'customer_email': customer_email,
                'package_type': package_type,
                'redirect_url': f'https://backoffice.rizzosai.com/login?welcome=true&package={package_type}'
            }), 200
        
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
        
    except Exception as e:
        app.logger.error(f"Webhook error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/success')
def success():
    """Success page after purchase - redirect to backoffice"""
    package_type = request.args.get('package', 'starter')
    customer_email = request.args.get('email', '')
    
    # You can add tracking or analytics here
    app.logger.info(f"Customer {customer_email} completed {package_type} purchase")
    
    return render_template('success.html', 
                         package_type=package_type, 
                         customer_email=customer_email)

@app.route('/redirect-to-backoffice')
def redirect_to_backoffice():
    """Redirect customers to backoffice after purchase"""
    package_type = request.args.get('package', 'starter')
    email = request.args.get('email', '')
    
    # Build redirect URL with parameters
    redirect_url = f'https://backoffice.rizzosai.com/login'
    if package_type or email:
        params = []
        if package_type:
            params.append(f'package={package_type}')
        if email:
            params.append(f'email={email}')
        if params:
            redirect_url += '?' + '&'.join(params)
    
    return redirect(redirect_url)

@app.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    """Terms and conditions page"""
    return render_template('terms.html')

@app.errorhandler(404)
def not_found(error):
    """Custom 404 page"""
    return render_template('404.html'), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)