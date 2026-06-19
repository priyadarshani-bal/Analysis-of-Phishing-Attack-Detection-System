from flask import Flask, render_template, request, jsonify
import sqlite3
import pickle
import numpy as np
from utils import extract_features, extract_email_features
import re

app = Flask(__name__)
model = pickle.load(open('model.pkl', 'rb'))

# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        result TEXT,
        confidence REAL,
        type TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

def save_log(data, result, confidence, dtype):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("INSERT INTO logs (data, result, confidence, type) VALUES (?, ?, ?, ?)",
                   (data, result, confidence, dtype))

    conn.commit()
    conn.close()

# -------- ACTION SYSTEM --------
def take_action(result):
    if "Phishing" in result:
        return "⚠️ Block this! Do not proceed."
    return "✅ Safe to proceed."

# -------- URL DETECTION --------
def detect_url(url):
    features = np.array([extract_features(url)])
    pred = model.predict(features)[0]
    prob = model.predict_proba(features)[0][pred]

    score = 0

    # 🚨 Rule 1: IP address in URL
    if re.search(r'\d+\.\d+\.\d+\.\d+', url):
        score += 2

    # 🚨 Rule 2: HTTP (not HTTPS)
    if not url.startswith("https"):
        score += 1

    # 🚨 Rule 3: Suspicious keywords
    if re.search(r'login|verify|secure|bank|update', url, re.I):
        score += 1

    # 🚨 Rule 4: Too many dots
    if url.count('.') > 3:
        score += 1

    # 🎯 FINAL DECISION (Hybrid)
    if pred == 1 or score >= 2:
        result = "Phishing Website"
    else:
        result = "Legitimate Website"

    confidence = round(prob * 100, 2)

    return result, confidence

# -------- EMAIL DETECTION --------
def detect_email(text):
    score = 0

    # Convert to lowercase
    text = text.lower()

    # 🚨 Strong phishing indicators
    if re.search(r'urgent|immediately|action required|verify now|click here', text):
        score += 2

    # 🔐 Sensitive info request
    if re.search(r'password|bank|account|login|otp', text):
        score += 2

    # 🔗 Links in email
    if re.search(r'http[s]?://', text):
        score += 1

    # 📧 Suspicious sender-like pattern
    if re.search(r'@\w+\.(com|net|org)', text):
        score += 1

    # 🎯 FINAL DECISION
    if score >= 3:
        return "Phishing Email", 90.0
    else:
        return "Safe Email", 95.0

# -------- ROUTES --------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/url', methods=['POST'])
def url_check():
    url = request.form['url']
    result, confidence = detect_url(url)
    action = take_action(result)

    save_log(url, result, confidence, "url")

    return render_template('result.html',
                           data=url,
                           result=result,
                           confidence=confidence,
                           action=action)
                           
@app.route('/email', methods=['POST'])
def email_check():
    email = request.form['email'].strip()
    result, confidence = detect_email(email)
    action = take_action(result)

    save_log(email, result, confidence, "email")

    return render_template('result.html',
                           data=email,
                           result=result,
                           confidence=confidence,
                           action=action)

@app.route('/history')
def history():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM logs ORDER BY id DESC")
    data = cursor.fetchall()

    conn.close()

    return render_template('history.html', data=data)

@app.route('/dashboard')
def dashboard():
    import sqlite3

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logs WHERE data = '' OR data IS NULL")
   
    # Count results
    cursor.execute("SELECT result, COUNT(*) FROM logs GROUP BY result")
    data = cursor.fetchall()

    # Convert to dict
    result_dict = {row[0]: row[1] for row in data}

    phishing = result_dict.get("Phishing Website", 0) + result_dict.get("Phishing Email", 0)
    safe = result_dict.get("Legitimate Website", 0) + result_dict.get("Safe Email", 0)
    email = result_dict.get("Phishing Email", 0) + result_dict.get("Safe Email", 0)
    total = sum(result_dict.values())

    labels = list(result_dict.keys())
    values = list(result_dict.values())

    conn.close()

    return render_template('dashboard.html',
                           labels=labels,
                           values=values,
                           phishing=phishing,
                           safe=safe,
                           email=email,
                          total=total)

# -------- API --------
@app.route('/api/check_url', methods=['POST'])
def api_check():
    data = request.json
    url = data.get("url")

    result, confidence = detect_url(url)

    return jsonify({
        "url": url,
        "result": result,
        "confidence": confidence
    })

if __name__ == '__main__':
    app.run(debug=True)