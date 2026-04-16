import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import sys

# Internal imports (direct calls)
from train_model import train_model
from admin_utils import change_password, add_user

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# External script runner (for camera-based scripts)
def run_script(script_name):
    try:
        script_path = os.path.join(BASE_DIR, script_name)
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"{script_name} not found!")
            return
        subprocess.run([sys.executable, script_path], check=True, cwd=BASE_DIR)
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ------------------- Button Actions -------------------

def register_face():
    run_script("register_face.py")

def take_attendance():
    run_script("take_attendance.py")

def view_attendance():
    run_script("view_attendance.py")

def train_model_action():
    messagebox.showinfo("Info", "Training started...\nPlease wait.")
    train_model()   # ✅ direct call → popup works correctly

# ------------------- Change Password Window -------------------

def open_change_password_window():
    win = tk.Toplevel(root)
    win.title("Change Password")
    win.geometry("400x300")
    win.config(bg="#f0f4f7")

    tk.Label(win, text="Change Admin Password", font=("Arial", 16, "bold"),
             bg="#f0f4f7").pack(pady=15)

    tk.Label(win, text="Username:", bg="#f0f4f7").pack()
    username_entry = tk.Entry(win, width=30)
    username_entry.pack(pady=3)

    tk.Label(win, text="Old Password:", bg="#f0f4f7").pack()
    old_entry = tk.Entry(win, show="*", width=30)
    old_entry.pack(pady=3)

    tk.Label(win, text="New Password:", bg="#f0f4f7").pack()
    new_entry = tk.Entry(win, show="*", width=30)
    new_entry.pack(pady=3)

    def save_new_pass():
        user = username_entry.get().strip()
        old = old_entry.get().strip()
        new = new_entry.get().strip()

        if not user or not old or not new:
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        if change_password(user, old, new):
            messagebox.showinfo("Success", "Password updated successfully!")
            win.destroy()
        else:
            messagebox.showerror("Error", "Incorrect credentials.")

    tk.Button(win, text="Save Password", width=15, bg="#2ecc71", fg="white",
              font=("Arial", 11, "bold"), command=save_new_pass).pack(pady=15)

# ------------------- Add New Admin Window -------------------

def open_add_admin_window():
    win = tk.Toplevel(root)
    win.title("Add New Admin")
    win.geometry("400x380")
    win.config(bg="#f0f4f7")

    tk.Label(win, text="Create New Admin", font=("Arial", 16, "bold"),
             bg="#f0f4f7").pack(pady=15)

    fields = ["New Username", "New Password", "Security Question", "Security Answer"]
    entries = []

    for field in fields:
        tk.Label(win, text=field + ":", bg="#f0f4f7").pack()
        ent = tk.Entry(win, width=30, show="*" if "Password" in field else None)
        ent.pack(pady=3)
        entries.append(ent)

    def save_new_admin():
        user, pwd, ques, ans = [e.get().strip() for e in entries]

        if not user or not pwd or not ques or not ans:
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        if add_user(user, pwd, ques, ans):
            messagebox.showinfo("Success", "New admin added successfully!")
            win.destroy()
        else:
            messagebox.showerror("Error", "Username already exists.")

    tk.Button(win, text="Save Admin", width=15, bg="#3498db", fg="white",
              font=("Arial", 11, "bold"), command=save_new_admin).pack(pady=15)

# ------------------- Admin Dashboard -------------------

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Admin Dashboard - Face Recognition Attendance System")
    root.geometry("520x550")
    root.config(bg="#f8f9fa")

    tk.Label(root, text="Admin Dashboard",
             font=("Arial", 22, "bold"),
             bg="#f8f9fa",
             fg="#2c3e50").pack(pady=25)

    buttons = [
        ("Register New Face", register_face, "#3498db"),
        ("Train Model", train_model_action, "#2ecc71"),
        ("Take Attendance", take_attendance, "#9b59b6"),
        ("View Attendance", view_attendance, "#f39c12"),
        ("Change Password", open_change_password_window, "#e67e22"),
        ("Add New Admin", open_add_admin_window, "#16a085"),
        ("Logout", root.destroy, "#e74c3c")
    ]

    for text, cmd, color in buttons:
        tk.Button(root, text=text, width=25, height=2,
                  bg=color, fg="white",
                  font=("Arial", 12, "bold"),
                  command=cmd).pack(pady=8)

    root.mainloop()
