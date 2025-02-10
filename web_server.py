import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
import time
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
GPIO.setmode(GPIO.BOARD)
reader = SimpleMFRC522()

# LED Pins
GREEN_LED = 18
RED_LED = 12
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)

# Database Setup
DATABASE = 'rfid_users.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  rfid_uid TEXT UNIQUE,
                  username TEXT UNIQUE)''')
    conn.commit()
    conn.close()

init_db()

def blink_led(led_pin, duration=3):
    GPIO.output(led_pin, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(led_pin, GPIO.LOW)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    try:
        print("Place new RFID tag to register...")
        rfid_uid, _ = reader.write(username)
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO users (rfid_uid, username) VALUES (?, ?)",
                  (str(rfid_uid), username))
        conn.commit()
        conn.close()
        
        blink_led(GREEN_LED)
        return redirect(url_for('index'))
    except Exception as e:
        print("Error:", str(e))
        blink_led(RED_LED)
        return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    try:
        print("Scan your RFID tag to login...")
        rfid_uid, username = reader.read()
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE rfid_uid=?", (str(rfid_uid),))
        user = c.fetchone()
        conn.close()
        
        if user:
            blink_led(GREEN_LED)
            return f"Welcome {user[2]}! Authentication successful."
        else:
            blink_led(RED_LED)
            return "Access denied! Unknown RFID tag."
    except Exception as e:
        print("Error:", str(e))
        blink_led(RED_LED)
        return "Authentication failed. Please try again."

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        GPIO.cleanup()

@app.route('/clone', methods=['POST'])
def clone_card():
    """Demonstration of RFID cloning vulnerability"""
    try:
        # Read original card
        print("Place original card to clone...")
        src_id, src_data = reader.read()
        
        # Write to blank card
        print("Place blank card...")
        reader.write(src_data)
        
        # Mark as cloned in database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("UPDATE users SET cloned=1 WHERE rfid_uid=?", (str(src_id),))
        conn.commit()
        conn.close()
        
        led_feedback(True)
        return "Cloning successful! Test cloned card in login."
    except Exception as e:
        print("Cloning failed:", str(e))
        led_feedback(False)
        return "Cloning failed"

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        GPIO.cleanup()