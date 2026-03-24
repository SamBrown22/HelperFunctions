from flask import Flask, request, jsonify
import bcrypt
import os
import base64
import uuid
import sqlite3

app = Flask(__name__)

DB_FILE = 'password_manager.db'
   
# region DB Management
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

def create_user_record(username, password_hash, salt):
    user_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO users (id, username, password_hash, salt) VALUES (?, ?, ?, ?)',
              (user_id, username, password_hash, salt))
    conn.commit()
    conn.close()
    return user_id

def get_user_by_username(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, password_hash, salt FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

def create_session(user_id):
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO sessions (session_id, user_id) VALUES (?, ?)', (session_id, user_id))
    conn.commit()
    conn.close()
    return session_id

def get_session_user_id(session_id):
    if not session_id:
        return None
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT user_id FROM sessions WHERE session_id = ?', (session_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def delete_session(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

def add_entry_for_user(user_id, name, username_enc, password_enc, url):
    entry_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO entries (id, user_id, name, username_enc, password_enc, url) VALUES (?, ?, ?, ?, ?, ?)',
              (entry_id, user_id, name, username_enc, password_enc, url))
    conn.commit()
    conn.close()
    return entry_id

def get_entries_for_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT name, username_enc, password_enc, url FROM entries WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_entry_for_user(user_id, name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM entries WHERE user_id = ? AND name = ?', (user_id, name))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted > 0
# endregion

# region Authentication and User Management
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json
    username = data['username']
    password = data['password']

    get_user_by_username(username)
    if get_user_by_username(username):
        return jsonify({'error': 'Username already exists'}), 400

    # Generate a random encryption salt for this user
    encryption_salt = os.urandom(16)
    password_hash = hash_password(password)

    create_user_record(username, password_hash, base64.b64encode(encryption_salt).decode())
    return jsonify({
        'message': 'User created',
        'salt': base64.b64encode(encryption_salt).decode()
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    user = get_user_by_username(username)
    if user:
        user_id, password_hash, salt = user

    if not user or not verify_password(password, password_hash):
        return jsonify({'error': 'Invalid credentials'}), 401

    session_id = create_session(user_id)

    return jsonify({
        'message': 'Login successful',
        'session_id': session_id,
        'salt': salt
    })

@app.route('/logout', methods=['POST'])
def logout():
    session_id = request.headers.get('Session-ID')
    if not session_id:
        return jsonify({'error': 'Invalid session'}), 401
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    deleted = c.rowcount
    conn.commit()
    conn.close()

    if deleted:
        return jsonify({'message': 'Logged out'})
    return jsonify({'error': 'Invalid session'}), 401
# endregion

# region PasswordManager API
@app.route('/add_entry', methods=['POST'])
def add_entry():
    session_id = request.headers.get('Session-ID')
    user_id = get_session_user_id(session_id)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    name = data['name']
    username_enc = data['username']
    password_enc = data['password']
    url = data.get('url', '')

    add_entry_for_user(user_id, name, username_enc, password_enc, url)

    return jsonify({'message': 'Saved'})

@app.route('/get_entries', methods=['GET'])
def get_entries():
    session_id = request.headers.get('Session-ID')
    user_id = get_session_user_id(session_id)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    rows = get_entries_for_user(user_id)

    entries = {row[0]: {'username': row[1], 'password': row[2], 'url': row[3]} for row in rows}
    return jsonify({'entries': entries})

@app.route('/delete_entry', methods=['DELETE'])
def delete_entry():
    session_id = request.headers.get('Session-ID')
    user_id = get_session_user_id(session_id)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    name = request.args.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400

    delete_entry_for_user(user_id, name)

    return jsonify({'message': 'Deleted'})
# endregion

# MAIN
if __name__ == '__main__':
    print("Initializing database...")
    init_db()

    print("Starting secure password manager server...")
    app.run(debug=True)