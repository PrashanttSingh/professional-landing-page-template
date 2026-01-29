from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Database setup
def init_db():
    conn = sqlite3.connect('contacts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contacts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT NOT NULL,
                  phone TEXT,
                  subject TEXT NOT NULL,
                  message TEXT NOT NULL,
                  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Home route - serve the landing page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to handle contact form submission
@app.route('/api/contact', methods=['POST'])
def contact():
    try:
        # Get form data
        data = request.get_json()

        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone', '')
        subject = data.get('subject')
        message = data.get('message')

        # Validate required fields
        if not all([name, email, subject, message]):
            return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400

        # Save to database
        conn = sqlite3.connect('contacts.db')
        c = conn.cursor()
        c.execute('''INSERT INTO contacts (name, email, phone, subject, message)
                     VALUES (?, ?, ?, ?, ?)''', (name, email, phone, subject, message))
        conn.commit()
        conn.close()

        # Send email notification (optional - configure SMTP settings)
        # send_email_notification(name, email, subject, message)

        return jsonify({
            'success': True, 
            'message': 'Thank you! Your message has been received.'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Admin route to view all submissions
@app.route('/admin/messages')
def admin_messages():
    conn = sqlite3.connect('contacts.db')
    c = conn.cursor()
    c.execute('SELECT * FROM contacts ORDER BY submitted_at DESC')
    messages = c.fetchall()
    conn.close()

    return render_template('admin.html', messages=messages)

# Optional: Email notification function
def send_email_notification(name, email, subject, message):
    """
    Configure your email settings here
    """
    try:
        # Email configuration (update with your details)
        sender_email = "your-email@gmail.com"  # Your email
        sender_password = "your-app-password"   # App password (not regular password)
        receiver_email = "your-email@gmail.com" # Where to receive notifications

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"New Contact Form Submission: {subject}"

        body = f"""
        New contact form submission:

        Name: {name}
        Email: {email}
        Subject: {subject}
        Message: {message}
        """

        msg.attach(MIMEText(body, 'plain'))

        # Send email via Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print(f"Email error: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
