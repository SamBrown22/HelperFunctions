import tkinter as tk
from tkinter import ttk, messagebox
import requests
import os
import base64
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# region Colors and Globals
BG = "#1e1e2e"
FG = "#ffffff"
BOX = "#2c2c3a"
ACCENT = "#6c5ce7"
TABLE_FG = "#000000"

user_key = None
session_id = None
entries = {}
# endregion

# region Encryption functions
def derive_key(password, salt):
    if isinstance(password, str):
        password = password.encode()
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1
    )
    return kdf.derive(password)

def encrypt(data: str, key):
    salt = os.urandom(16)
    key_for_aes = derive_key(key, salt)
    aesgcm = AESGCM(key_for_aes)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data.encode(), None)
    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode()

def decrypt(token: str, key):
    raw = base64.b64decode(token)
    salt = raw[:16]
    nonce = raw[16:28]
    ciphertext = raw[28:]
    key_for_aes = derive_key(key, salt)
    aesgcm = AESGCM(key_for_aes)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
# endregion

# region Server Functions
def create_user(username, password):
    try:
        res = requests.post(
            "http://localhost:5000/create_user",
            json={
                'username': username, 
                'password': password
            }
        )

        if res.status_code == 200:
            return base64.b64decode(res.json()['salt'])
        else:
            messagebox.showerror("Error", res.json()['error'])
            return None
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None

def login_user(username, password):
    try:
        r = requests.post("http://localhost:5000/login",
                          json={'username': username, 'password': password})
        if r.status_code == 200:
            data = r.json()

            # Assuming server returns salt and session_id
            salt = base64.b64decode(data['salt'])
            key = derive_key(password, salt)
            return key, data['session_id']
        else:
            messagebox.showerror("Login Failed", r.json()['error'])
            return None, None
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None, None

def add_entry_to_server(name, username, password, url):
    enc_user = encrypt(username, user_key)
    enc_pass = encrypt(password, user_key)
    try:
        headers = {'Session-ID': session_id}
        requests.post("http://localhost:5000/add_entry", json={
            'name': name,
            'username': enc_user,
            'password': enc_pass,
            'url': url
        }, headers=headers)
    except Exception as e:
        print("Error saving entry:", e)

def get_entries_from_server():
    global entries
    try:
        headers = {'Session-ID': session_id}
        res = requests.get("http://localhost:5000/get_entries", headers=headers)
        data = res.json()['entries']
        decrypted_entries = {}
        for name, entry in data.items():
            decrypted_entries[name] = {
                'username': decrypt(entry['username'], user_key),
                'password': decrypt(entry['password'], user_key),
                'url': entry.get('url', '')
            }
        entries = decrypted_entries
    except Exception as e:
        print("Error fetching entries:", e)
# endregion

# region GUI Functions

def refresh_list():
    for row in table.get_children():
        table.delete(row)
    for i, (name, data) in enumerate(entries.items()):
        tag = "evenrow" if i % 2 == 0 else "oddrow"
        table.insert("", "end", iid=name, values=(name, data['username'], data['password'], data['url']), tags=(tag,))

def on_table_click(event):
    row_id = table.identify_row(event.y)
    col_id = table.identify_column(event.x)

    if not row_id:
        return

    name, username, password, url = table.item(row_id, "values")

    if col_id == "#2":
        root.clipboard_clear()
        root.clipboard_append(username)
        print("Copied username:", username)

    elif col_id == "#3":
        root.clipboard_clear()
        root.clipboard_append(password)
        print("Copied password:", password)

def login_prompt():
    global user_key, userId
    prompt_win = tk.Tk()
    prompt_win.title("Login")
    prompt_win.geometry("400x250")
    prompt_win.configure(bg=BG)

    tk.Label(prompt_win, text="Username:", bg=BG, fg=FG).pack(pady=10)
    user_e = tk.Entry(prompt_win, bg=BOX, fg=FG, insertbackground=FG)
    user_e.pack()

    tk.Label(prompt_win, text="Password:", bg=BG, fg=FG).pack(pady=10)
    pass_e = tk.Entry(prompt_win, bg=BOX, fg=FG, insertbackground=FG, show="*")
    pass_e.pack()

    def try_login():
        username = user_e.get().strip()
        password = pass_e.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please fill all fields")
            return
        key, sid = login_user(username, password)
        if key and sid:
            global user_key, session_id
            user_key = key
            session_id = sid
            prompt_win.destroy()
    
    def try_create():
        username = user_e.get().strip()
        password = pass_e.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please fill all fields")
            return
        salt = create_user(username, password)
        if salt:
            messagebox.showinfo("Success", "User created! Please login now.")
        else:
            messagebox.showerror("Error", "Failed to create user")

    tk.Button(prompt_win, text="Login", bg=ACCENT, fg=FG, command=try_login).pack(pady=20)
    tk.Button(prompt_win, text="Create Account", bg=ACCENT, fg=FG, command=try_create).pack()
    prompt_win.mainloop()

def create_password_manager():
    global root, table
    root = tk.Tk()
    root.title("🔒Password Manager")
    root.geometry("900x600")
    root.configure(bg=BG)

    title_label = tk.Label(root, text="🔒 Password Manager", font=("Segoe UI", 16), bg=BG, fg=FG)
    title_label.pack(pady=(10, 2))

    # Frame Layout
    main_frame = tk.Frame(root, bg=BG)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    left_frame = tk.Frame(main_frame, bg=BG, width=350)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,15))

    separator = tk.Frame(main_frame, bg="#444444", width=2)
    separator.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=10)

    right_frame = tk.Frame(main_frame, bg=BG)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # Add Entry Form (Left Frame)
    form_title = tk.Label(left_frame, text="Add New Entry", font=("Segoe UI", 14), bg=BG, fg=FG)
    form_title.pack(pady=(0,10))

    tk.Label(left_frame, text="Name:", bg=BG, fg=FG, anchor="w").pack(fill=tk.X)
    name_e = tk.Entry(left_frame, bg=BOX, fg=FG, insertbackground=FG)
    name_e.pack(fill=tk.X, pady=(0,5))

    tk.Label(left_frame, text="Username:", bg=BG, fg=FG, anchor="w").pack(fill=tk.X)
    user_e = tk.Entry(left_frame, bg=BOX, fg=FG, insertbackground=FG)
    user_e.pack(fill=tk.X, pady=(0,5))

    tk.Label(left_frame, text="Password:", bg=BG, fg=FG, anchor="w").pack(fill=tk.X)
    pass_e = tk.Entry(left_frame, bg=BOX, fg=FG, insertbackground=FG, show="*")
    pass_e.pack(fill=tk.X, pady=(0,5))

    tk.Label(left_frame, text="URL:", bg=BG, fg=FG, anchor="w").pack(fill=tk.X)
    url_e = tk.Entry(left_frame, bg=BOX, fg=FG, insertbackground=FG)
    url_e.pack(fill=tk.X, pady=(0,10))

    def save_entry():
        name = name_e.get().strip()
        username = user_e.get().strip()
        password = pass_e.get().strip()
        url = url_e.get().strip()
        if not name or not username or not password:
            messagebox.showerror("Error", "Name, Username, and Password are required")
            return
        add_entry_to_server(name, username, password, url)
        entries[name] = {'username': username, 'password': password, 'url': url}
        refresh_list()
        # Clear form
        name_e.delete(0, tk.END)
        user_e.delete(0, tk.END)
        pass_e.delete(0, tk.END)
        url_e.delete(0, tk.END)

    save_btn = tk.Button(left_frame, text="Save Entry", bg=ACCENT, fg=FG, command=save_entry)
    save_btn.pack(fill=tk.X)

    # Entries List (Right Frame)
    list_title = tk.Label(right_frame, text="Saved Entries", font=("Segoe UI", 14), bg=BG, fg=FG)
    list_title.pack(pady=(0,10))

    table = ttk.Treeview(right_frame, columns=("Name","Username","Password","URL"), show="headings", height=15)
    table.pack(fill=tk.BOTH, expand=True)

    style = ttk.Style()
    style.configure("Treeview", background=BOX, foreground=TABLE_FG, fieldbackground=BOX, rowheight=25)
    style.configure("Treeview.Heading", background=BOX, foreground=TABLE_FG)
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", FG)])

    table.column("Name", width=150, stretch=tk.NO)
    table.column("Username", width=150, anchor=tk.W)    
    table.column("Password", width=150, anchor=tk.W)
    table.column("URL", width=200, anchor=tk.W)

    table.heading("Name", text="Name", anchor=tk.W)
    table.heading("Username", text="Username", anchor=tk.W)
    table.heading("Password", text="Password", anchor=tk.W)
    table.heading("URL", text="URL", anchor=tk.W)

    table.tag_configure("oddrow", background="#DDDCDC")
    table.tag_configure("evenrow", background="#CDCDCD")

    table.bind("<Button-3>", on_table_click)

# endregion

# ---------------- Main ----------------

login_prompt()
get_entries_from_server()
create_password_manager()
refresh_list()
root.mainloop()