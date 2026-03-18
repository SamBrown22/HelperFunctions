import itertools
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
        text_single_line = " ".join(text.splitlines())
        current_clipboard.set(
            f"{text_single_line[:50]}{'...' if len(text_single_line) > 50 else ''}"
        )
        if text_single_line:
            if text_single_line in clipboard_history:
                del clipboard_history[text_single_line]
            clipboard_history[text_single_line] = True
            update_listbox()
    except:
        pass
    root.after(1000, save_clipboard)

def update_listbox():
    try:
        selected_index = listbox.curselection()[0]
        selected_value = listbox.get(selected_index)
    except IndexError:
        selected_value = None 

    listbox.delete(0, tk.END)

    for key in itertools.islice(reversed(clipboard_history), 1, None):
        listbox.insert(tk.END, key)

    if selected_value in listbox.get(0, tk.END):
        index = listbox.get(0, tk.END).index(selected_value)
        listbox.selection_set(index)
        listbox.activate(index)

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

# --- UI Setup ---
root = tk.Tk()
root.title("Clipboard Manager")
root.geometry("500x500")
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

current_clipboard = tk.StringVar()

current_frame = tk.LabelFrame(
    center_frame,
    text="Current Clipboard",
    bg=BG,
    fg=FG,
    font=("Segoe UI", 9, "bold"),
    labelanchor="nw",
    bd=0,
    relief="solid",
)
current_frame.pack(fill=tk.X, pady=10, anchor="w")

current_clipboard_entry = tk.Label(
    current_frame,
    textvariable=current_clipboard,
    bg=BOX,
    fg=FG,
    font=("Consolas", 10),
    anchor="w",
    justify="left",
    bd=0,
    padx=8,
    pady=6,
    wraplength=400,
)
current_clipboard_entry.pack(fill=tk.BOTH, expand=True)

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