from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os
import random
import string
import base64
import qrcode
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'Swetha'
DATABASE_URL = "postgresql://abu:1212@localhost/Eauth"
conn = psycopg2.connect(DATABASE_URL)


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phone_number = request.form['phone_number']
        email = request.form['email']
        date_of_birth = request.form['date_of_birth']
        roll_no = request.form['roll_no']
        department = request.form['department']
        college = request.form['college']
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (username, password, phone_number, email, date_of_birth, roll_no, department, college) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                       (username, password, phone_number, email, date_of_birth, roll_no, department, college))
        conn.commit()
        cursor.close()

        return "Registered successfully. Go and login."

    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login_user():
    username = request.form['username']
    password = request.form['password']

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    cursor.close()

    if user:
        session['user_id'] = user[0]
        return redirect(url_for('verification'))
    else:
        return "Invalid credentials. Please try again."

@app.route('/verification', methods=['GET', 'POST'])
def verification():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = conn.cursor()
    cursor.execute("SELECT otp FROM students WHERE id = %s", (user_id,))
    stored_otp = cursor.fetchone()[0]
    
    if stored_otp:
        otp = stored_otp
    else:
        otp = generate_otp()
        cursor.execute("UPDATE students SET otp = %s WHERE id = %s", (otp, user_id))
        conn.commit()

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(otp)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == str(otp):
            return redirect(url_for('success'))
        else:
            return "Incorrect OTP. Please try again."

    return render_template('verification.html', qr_code=img_base64)

@app.route('/success')
def success():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = get_user(session['user_id'])

    print(f"User in success route: {user}")

    if user:
        return render_template('success.html', user=user)
    else:
        return "Unable to retrieve user information. Please try logging in again."

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = get_user(session['user_id'])

    print(f"User in profile route: {user}")

    if user:
        return render_template('profile.html', user=user)
    else:
        return "Unable to retrieve user information. Please try logging in again."

def get_user(user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    print(f"User ID: {user_id}")
    print(f"User from Database: {user}")

    return user

if __name__ == '__main__':
    app.run(debug=True)
