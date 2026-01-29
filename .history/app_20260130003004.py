from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
import sqlite3
import os
from dotenv import load_dotenv 
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread  # ← ADD THIS LINE



# Load environment variables
load_dotenv()



app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-default-secret-key')



# Create database
def init_db():
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            subject TEXT,
            message TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT (datetime('now', '+5 hours', '+30 minutes'))
        )
    ''')
    conn.commit()
    conn.close()



init_db()



# Admin login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function



# Admin login page
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD'):
            session['logged_in'] = True
            return redirect(url_for('admin_messages'))
        
        return 'Invalid credentials'
    
    return '''
        <form method="post" style="max-width:300px;margin:100px auto;padding:20px;border:1px solid #ccc;border-radius:10px;font-family:Arial;">
            <h2 style="text-align:center;color:#4F46E5;">Admin Login</h2>
            <input type="text" name="username" placeholder="Username" required style="width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px;box-sizing:border-box;"><br>
            <input type="password" name="password" placeholder="Password" required style="width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px;box-sizing:border-box;"><br>
            <button type="submit" style="width:100%;padding:10px;background:#4F46E5;color:white;border:none;border-radius:5px;cursor:pointer;font-size:16px;">Login</button>
        </form>
    '''



# Email notification function
def send_email_notification(name, email, phone, subject, message):
    try:
        sender_email = os.getenv('MAIL_USERNAME')
        sender_password = os.getenv('MAIL_PASSWORD')
        recipient_email = os.getenv('MAIL_RECIPIENT')
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = '🔔 New Contact Form Submission - Landing Page'
        
        body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📬 NEW CONTACT FORM SUBMISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━



👤 Name: {name}
📧 Email: {email}
📱 Phone: {phone if phone else 'Not provided'}
📋 Subject: {subject if subject else 'Not provided'}
💬 Message: 
{message}



━━━━━━━━━━━━━━━━━━━━━━━━━━━━
View all messages in admin panel
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False



# Home route
@app.route('/')
def index():
    return render_template('index.html')



# Form submission - UPDATED WITH BACKGROUND EMAIL
@app.route('/api/contact', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        
        # Debug: Print what we received
        print(f"📥 Received data: {data}")
        
        name = data.get('name', '')
        email = data.get('email', '')
        phone = data.get('phone', '')
        subject = data.get('subject', '')
        message = data.get('message', '')
        
        # Debug: Print extracted values
        print(f"📝 Name: '{name}', Email: '{email}', Phone: '{phone}', Subject: '{subject}', Message: '{message}'")
        
        # Validate required fields
        if not name or not email or not message:
            error_msg = f'Missing fields - Name: {bool(name)}, Email: {bool(email)}, Message: {bool(message)}'
            print(f"❌ Validation failed: {error_msg}")
            return jsonify({'success': False, 'message': error_msg}), 400
        
        # Save to database FIRST (fast operation)
        conn = sqlite3.connect('contacts.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO contacts (name, email, phone, subject, message) VALUES (?, ?, ?, ?, ?)',
                       (name, email, phone, subject, message))
        conn.commit()
        conn.close()
        
        print("✅ Saved to database successfully!")
        
        # Send email in BACKGROUND THREAD (won't block response)
        def send_email_async():
            send_email_notification(name, email, phone, subject, message)
        
        Thread(target=send_email_async, daemon=True).start()
        
        # Return immediately without waiting for email
        return jsonify({'success': True, 'message': 'Message sent successfully!'})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to send message: {str(e)}'}), 500



# Protected admin route
@app.route('/admin/messages')
@login_required
def admin_messages():
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts ORDER BY id DESC')
    messages = cursor.fetchall()
    conn.close()
    return render_template('admin.html', messages=messages)



# Admin logout route
@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))



if __name__ == '__main__':
    app.run(debug=True)
