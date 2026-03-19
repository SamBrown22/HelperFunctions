import json
import os
import tkinter as tk
import bcrypt
from tkinter import ttk\

# Colors for theme
BG = "#1e1e2e"
FG = "#ffffff"
ACCENT = "#6c5ce7"
BOX = "#2c2c3a"

entries = {}
verified = False

# Security Functions
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_config(hashed_password):
    os.makedirs("./data", exist_ok=True)
    if not os.path.exists("./data/config.json"):
        with open("./data/config.json", "w") as f:
            json.dump({"hash-password": hashed_password}, f)

# Data Management Functions

def write_entries():
    os.makedirs("./data", exist_ok=True)
    with open("./data/passwords.json", "w") as f:
        json.dump(entries, f)

def read_entries():
    global entries
    try:
        with open("./data/passwords.json", "r") as f:
            entries = json.load(f)
    except FileNotFoundError:
        entries = {}

def add_entry(name, username, password, url):
    entries[name] = {'username': username, 'password': password, 'url': url}

def get_entry(name):
    return entries.get(name, None)

def delete_entry():
    selected = table.focus()
    if selected:
        del entries[selected]
        table.delete(selected)
        write_entries()

def refresh_list():
   for i in range (len(entries)):
        entry = list(entries.keys())[i]
        if not table.exists(entry):
            data = entries[entry]

            if i % 2 == 0:
                table.insert("", "end", iid=entry, values=(entry, data['username'], data['password'], data['url']), tags=("evenrow",))
            else:
                table.insert("", "end", iid=entry, values=(entry, data['username'], data['password'], data['url']), tags=("oddrow",))

# GUI Functions
def open_add_window():
    add_win = tk.Toplevel(root)
    add_win.title("Add Entry")
    add_win.geometry("300x260")
    add_win.configure(bg=BG)

    tk.Label(add_win, text="Name:", bg=BG, fg=FG).pack(pady=3)
    name_e = tk.Entry(add_win, bg=BOX, fg=FG, insertbackground=FG)
    name_e.pack()

    tk.Label(add_win, text="Username:", bg=BG, fg=FG).pack(pady=3)
    user_e = tk.Entry(add_win, bg=BOX, fg=FG, insertbackground=FG)
    user_e.pack()

    tk.Label(add_win, text="Password:", bg=BG, fg=FG).pack(pady=3)
    pass_e = tk.Entry(add_win, bg=BOX, fg=FG, insertbackground=FG, show="*")
    pass_e.pack()

    tk.Label(add_win, text="URL:", bg=BG, fg=FG).pack(pady=3)
    url_e = tk.Entry(add_win, bg=BOX, fg=FG, insertbackground=FG)
    url_e.pack()

    def save_entry():
        name = name_e.get().strip()
        username = user_e.get().strip()
        password = pass_e.get().strip()
        url = url_e.get().strip()

        if not name or not username or not password:
            return 

        add_entry(name, username, password, url)
        refresh_list()
        add_win.destroy()

    tk.Button(add_win, text="Save Entry", bg=ACCENT, fg=FG, command=save_entry).pack(pady=10)

def password_prompt():
    prompt_win = tk.Toplevel(root)
    prompt_win.title("Enter Master Password")
    prompt_win.geometry("300x150")
    prompt_win.configure(bg=BG)

    tk.Label(prompt_win, text="Master Password:", bg=BG, fg=FG).pack(pady=10)
    pass_e = tk.Entry(prompt_win, bg=BOX, fg=FG, insertbackground=FG, show="*")
    pass_e.pack()

    def check_password():
        entered = pass_e.get().strip()
        if verify_password(entered, hashed_password):
            global verified
            verified = True
            prompt_win.destroy()
        else:
            print("Incorrect password")

    tk.Button(prompt_win, text="Submit", bg=ACCENT, fg=FG, command=check_password).pack(pady=10)

    root.wait_window(prompt_win)

def create_master_password():
    create_win = tk.Toplevel(root)
    create_win.title("Create Master Password")
    create_win.geometry("300x150")
    create_win.configure(bg=BG)

    tk.Label(create_win, text="Create Master Password:", bg=BG, fg=FG).pack(pady=10)
    pass_e = tk.Entry(create_win, bg=BOX, fg=FG, insertbackground=FG, show="*")
    pass_e.pack()

    def save_master():
        global hashed_password
        entered = pass_e.get().strip()
        if entered:
            hashed_password = hash_password(entered)
            create_config(hashed_password)
            create_win.destroy()

    tk.Button(create_win, text="Create", bg=ACCENT, fg=FG, command=save_master).pack(pady=10)

# Event Handlers
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

# -----------------------------
# Main Window
# -----------------------------
root = tk.Tk()
root.title("Password Manager")
root.geometry("500x400")
root.configure(bg=BG)

top_frame = tk.Frame(root, bg=BG)
center_frame = tk.Frame(root, bg=BG)
bottom_frame = tk.Frame(root, bg=BG)

top_frame.pack(pady=10)
center_frame.pack(pady=10)
bottom_frame.pack(pady=10)

# Label Configurations
title_label = tk.Label(top_frame, text="🔒 Password Manager", font=("Segoe UI", 16), bg=BG, fg=FG)
title_label.pack()

list_label = tk.Label(center_frame, text="Saved Entries", bg=BG, fg=FG)
list_label.pack()

# Main Listing Configurations

table = ttk.Treeview(center_frame, columns=("Name", "Username", "Password", "URL"), show="headings", height=10)

style = ttk.Style()
style.configure("Treeview", background=BOX, foreground=FG, fieldbackground=BOX, rowheight=25)
style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", FG)])

table.column("Name", width=150, stretch=tk.NO)
table.column("Username", width=150, anchor=tk.W)    
table.column("Password", width=150, anchor=tk.W)
table.column("URL", width=200, anchor=tk.W)

table.heading("Name", text="Name", anchor=tk.W)
table.heading("Username", text="Username", anchor=tk.W)
table.heading("Password", text="Password", anchor=tk.W)
table.heading("URL", text="URL", anchor=tk.W)

table.tag_configure("oddrow", background="#E8E8E8")
table.tag_configure("evenrow", background='#FFFFFF')

table.bind("<Button-3>", on_table_click)

table.pack()

# Button Configurations

add_btn = tk.Button(root, text="Add Entry", bg=ACCENT, fg=FG, command=open_add_window)
add_btn.pack(pady=10, side=tk.LEFT, padx=20)

delete_btn = tk.Button(root, text="Delete Selected", bg=ACCENT, fg=FG, command=delete_entry)
delete_btn.pack(pady=5, side=tk.RIGHT, padx=20)

# MAIN LOGIC
if not os.path.exists("./data/config.json"):
    create_master_password()
else:
    with open("./data/config.json", "r") as f:
        config = json.load(f)
        hashed_password = config.get("hash-password", "")
    password_prompt()

if verified:
    try:
        read_entries()
        refresh_list()
    except Exception as e:
        print("Error loading entries:", e)

    root.mainloop()

    if root.protocol("WM_DELETE_WINDOW", lambda: (write_entries(), root.destroy())):
        pass
else:
    root.destroy()
