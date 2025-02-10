import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
GPIO.setmode(GPIO.BOARD)
reader = SimpleMFRC522()

# LED Configuration
GREEN_LED = 18
RED_LED = 12
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)

# In-memory user storage
registered_users = []

def blink_led(led_pin, duration=3):
    GPIO.output(led_pin, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(led_pin, GPIO.LOW)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username'].strip()
    if not username:
        return redirect(url_for('index'))
    
    try:
        if any(user['username'] == username for user in registered_users):
            blink_led(RED_LED)
            return "Username already exists!"
        
        print("Place new RFID tag to register...")
        reader.write(username)
        time.sleep(1)
        rfid_uid, _ = reader.read()  # Read back the UID
        
        if any(str(rfid_uid) == user['rfid_uid'] for user in registered_users):
            blink_led(RED_LED)
            return "RFID tag already registered!"
        
        registered_users.append({
            'rfid_uid': str(rfid_uid),
            'username': username,
            'is_cloned': False
        })
        
        blink_led(GREEN_LED)
        return redirect(url_for('index'))
    
    except Exception as e:
        print("Error:", str(e))
        blink_led(RED_LED)
        return "Registration failed!"

@app.route('/login', methods=['POST'])
def login():
    try:
        print("Scan your RFID tag to login...")
        rfid_uid, _ = reader.read()
        
        for user in registered_users:
            if user['rfid_uid'] == str(rfid_uid):
                status = f"Welcome {user['username']}!"
                if user['is_cloned']:
                    status += " (Cloned Card Detected!)"
                blink_led(GREEN_LED)
                return status
        
        blink_led(RED_LED)
        return "Access denied! Unknown RFID tag."
    
    except Exception as e:
        print("Error:", str(e))
        blink_led(RED_LED)
        return "Authentication failed!"

@app.route('/clone', methods=['POST'])
def clone_card():
    try:
        print("Place original card to clone...")
        src_uid, src_data = reader.read()
        src_username = src_data.strip()
        
        original_user = next((u for u in registered_users if u['rfid_uid'] == str(src_uid)), None)
        
        if not original_user:
            blink_led(RED_LED)
            return "Original card not registered!"
        
        print("Place blank card...")
        time.sleep(2)  # Allow time for the user to swap cards
        
        reader.write(src_username)
        time.sleep(1)  # Delay before reading back
        cloned_uid, _ = reader.read()  # Read back the cloned card UID
        
        registered_users.append({
            'rfid_uid': str(cloned_uid),
            'username': src_username,
            'is_cloned': True
        })
        
        blink_led(GREEN_LED)
        return "Cloning successful! Try cloned card in login."
    
    except Exception as e:
        print("Cloning failed:", str(e))
        blink_led(RED_LED)
        return "Cloning failed!"

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        GPIO.cleanup()
