import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from flask import Flask, render_template, request, jsonify
import requests
import random
import datetime

# Supabase Configuration
SUPABASE_URL = "https://fatwlmmxmgaprrdecsec.supabase.co"
SUPABASE_KEY = "sb_publishable_87ysThu2h81upqDbgKNLJQ_1bf8DQ_5"

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=representation" 
}

app = Flask(__name__, template_folder='template')

# Email OTP Function
def send_otp_email(to_email, otp):
    sender_email = os.getenv("abhiramkrv@gmail.com")
    sender_pass = os.getenv("jazq egep eelz nccs")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "Notebook App – OTP Verification"

    body = f"""
Dear User,

Your One Time Password (OTP) is:

{otp}

This OTP is valid for 10 minutes.
Please do not share it with anyone.

Regards,
Notebook App Team
"""
    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_pass)
    server.send_message(msg)
    server.quit()

# Home Route - Shows Login/Register Page
@app.route("/")
def index():
    return render_template("auth.html")

# Dashboard Route - Shows Main Dashboard
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# Login API
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password required"
        }), 400

    try:
        # Fetch user by username
        url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=id,username,password,email"
        res = requests.get(url, headers=SUPABASE_HEADERS)
        users = res.json()

        # User not found
        if not users:
            return jsonify({
                "success": False,
                "message": "User not registered"
            }), 404

        user = users[0]

        # Password mismatch
        if user["password"] != password:
            return jsonify({
                "success": False,
                "message": "Invalid password"
            }), 401

        # Login success
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# Register API
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return jsonify({
            "success": False,
            "message": "Username, password, and email are required"
        }), 400

    try:
        # Check if username OR email already exists
        check_url = (
            f"{SUPABASE_URL}/rest/v1/users"
            f"?or=(username.eq.{username},email.eq.{email})"
            f"&select=id"
        )
        check_res = requests.get(check_url, headers=SUPABASE_HEADERS)
        existing = check_res.json()

        if existing:
            return jsonify({
                "success": False,
                "message": "User already exists"
            }), 409

        # Insert new user
        payload = {
            "username": username,
            "password": password,
            "email": email,
            "otp": None,
            "otpexp": None,
            "isotpused": False
        }

        insert_url = f"{SUPABASE_URL}/rest/v1/users"
        res = requests.post(insert_url, headers=SUPABASE_HEADERS, json=payload)

        if res.status_code == 201:
            return jsonify({
                "success": True,
                "message": "Registration successful"
            })

        return jsonify({
            "success": False,
            "message": res.text
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# Forgot Password / Send OTP API
@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400

    try:
        # Generate 6 digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Find user by Email
        # Note: We need the user's ID to update the row
        search_url = f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}&select=id"
        search_res = requests.get(search_url, headers=SUPABASE_HEADERS)
        users = search_res.json()

        if not users or len(users) == 0:
            return jsonify({"success": False, "message": "Email not found"}), 404

        user_id = users[0]['id']

        # Update User with OTP in Supabase
        update_url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
        update_payload = {
            "otp": otp_code,
            "otpexp": (datetime.datetime.now() + datetime.timedelta(minutes=10)).isoformat()
        }
        requests.patch(update_url, headers=SUPABASE_HEADERS, json=update_payload)

        # Send OTP via Email
        send_otp_email(email, otp_code)

        return jsonify({"success": True, "message": f"OTP sent to {email}"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Run Server
if __name__ == "__main__":
    app.run(debug=True, port=5000)
