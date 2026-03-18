import tkinter as tk
from pymongo import MongoClient


#client = MongoClient("mongodb+srv://samuelstevenbrown_db_user:AP4ZAtZa2IudGZeA@clipboardhistory.k5hds3x.mongodb.net/?appName=ClipBoardHistory")
#db = client.Clipboard_history
#collection = db.history

# Colors for theme
BG = "#1e1e2e"
FG = "#ffffff"
ACCENT = "#6c5ce7"
BOX = "#2c2c3a"

clipboard_history = {}

# --- Clipboard functions ---
def save_clipboard():
    try:
        text = root.clipboard_get()
        if text and text not in clipboard_history:
            clipboard_history[text] = True
            update_listbox(text)
        elif text in clipboard_history:
            highlight_selected(text)
    except:
        pass
    root.after(1000, save_clipboard)

def update_listbox(text):
    listbox.insert(0, text)
    show_selected(text)

def copy_selected():
    try:
        selected = listbox.get(listbox.curselection())
        root.clipboard_clear()
        root.clipboard_append(selected)
    except:
        pass

def clear_history():
    clipboard_history.clear()
    update_listbox()

def show_selected(key):
    all_items = listbox.get(0, tk.END)
    if key in all_items:
        index = all_items.index(key)
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(index)
        listbox.activate(index)

# --- UI Setup ---
root = tk.Tk()
root.title("Clipboard Manager")
root.geometry("450x400")
root.configure(bg=BG)
root.resizable(False, False)

# Top frame (title/header)
top_frame = tk.Frame(root, bg=BG)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

title = tk.Label(
    top_frame,
    text="📋 Clipboard Manager",
    bg=BG,
    fg=FG,
    font=("Segoe UI", 16, "bold")
)
title.pack()

# Center frame (listbox)
center_frame = tk.Frame(root, bg=BG)
center_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

listbox = tk.Listbox(
    center_frame,
    width=50,
    height=15,
    bg=BOX,
    fg=FG,
    selectbackground=ACCENT,
    selectforeground="white",
    bd=0,
    highlightthickness=0,
    font=("Consolas", 11),
    activestyle="none"
)
listbox.pack(fill=tk.BOTH, expand=True)

# Bottom frame (buttons side by side)
bottom_frame = tk.Frame(root, bg=BG)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

copy_button = tk.Button(
    bottom_frame,
    text="Copy Selected",
    command=copy_selected,
    bg=ACCENT,
    fg="white",
    activebackground="#5a4fcf",
    activeforeground="white",
    bd=0,
    padx=15,
    pady=8,
    font=("Segoe UI", 10, "bold"),
    cursor="hand2"
)
copy_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(
    bottom_frame,
    text="Clear History",
    command=clear_history,
    bg=ACCENT,
    fg="white",
    activebackground="#5a4fcf",
    activeforeground="white",
    bd=0,
    padx=15,
    pady=8,
    font=("Segoe UI", 10, "bold"),
    cursor="hand2"
)
clear_button.pack(side=tk.RIGHT, padx=5)

# Start clipboard tracking
save_clipboard()

root.mainloop()