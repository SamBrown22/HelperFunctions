from flask import Flask, request, jsonify
import bcrypt
import os
import base64
import uuid
import sqlite3

app = Flask(__name__)

# SQLite DB setup
DB_FILE = 'password_manager.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        salt TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS entries (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        name TEXT,
        username_enc TEXT,
        password_enc TEXT,
        url TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    conn.commit()
    conn.close()

init_db()

# In-memory sessions for simplicity (could be DB too)
sessions = {}

# ---------------- USERS ----------------

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json
    username = data['username']
    password = data['password']

    connection = sqlite3.connect(DB_FILE)
    c = connection.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    if c.fetchone():
        connection.close()
        return jsonify({'error': 'User exists'}), 400

    # Generate a random encryption salt for this user
    encryption_salt = os.urandom(16)
    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)

    c.execute('INSERT INTO users (id, username, password_hash, salt) VALUES (?, ?, ?, ?)',
              (user_id, username, password_hash, base64.b64encode(encryption_salt).decode()))
    connection.commit()
    connection.close()

    return jsonify({
        'message': 'User created',
        'salt': base64.b64encode(encryption_salt).decode()
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, password_hash, salt FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()

    if not user or not verify_password(password, user[1]):
        return jsonify({'error': 'Invalid credentials'}), 401

    user_id, _, salt = user

    # Create session
    session_id = str(uuid.uuid4())
    sessions[session_id] = user_id

    return jsonify({
        'message': 'Login successful',
        'session_id': session_id,
        'salt': salt
    })

@app.route('/logout', methods=['POST'])
def logout():
    session_id = request.headers.get('Session-ID')
    if session_id in sessions:
        del sessions[session_id]
        return jsonify({'message': 'Logged out'})
    return jsonify({'error': 'Invalid session'}), 401

# ---------------- ENTRIES ----------------

@app.route('/add_entry', methods=['POST'])
def add_entry():
    session_id = request.headers.get('Session-ID')
    user_id = sessions.get(session_id)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    name = data['name']
    username_enc = data['username']
    password_enc = data['password']
    url = data.get('url', '')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO entries (id, user_id, name, username_enc, password_enc, url) VALUES (?, ?, ?, ?, ?, ?)',
              (str(uuid.uuid4()), user_id, name, username_enc, password_enc, url))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Saved'})

@app.route('/get_entries', methods=['GET'])
def get_entries():
    session_id = request.headers.get('Session-ID')
    user_id = sessions.get(session_id)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT name, username_enc, password_enc, url FROM entries WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()

    entries = {row[0]: {'username': row[1], 'password': row[2], 'url': row[3]} for row in rows}
    return jsonify({'entries': entries})

@app.route('/delete_entry', methods=['DELETE'])
def delete_entry():
    session_id = request.headers.get('Session-ID')
    user_id = sessions.get(session_id)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    name = request.args.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM entries WHERE user_id = ? AND name = ?', (user_id, name))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Deleted'})

# ---------------- RUN ----------------

if __name__ == '__main__':
    print("Starting secure password manager server...")
    app.run(debug=True)