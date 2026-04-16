import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import os
import sys
from admin_utils import verify_login, get_security_question, reset_password_if_correct

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_GUI_PATH = os.path.join(BASE_DIR, "main_gui.py")
TAKE_ATTENDANCE_PATH = os.path.join(BASE_DIR, "take_attendance.py")


def _run_script(script_path, error_context):
    try:
        subprocess.run([sys.executable, script_path], check=True, cwd=BASE_DIR)
    except Exception as e:
        messagebox.showerror("Error", f"Could not open {error_context}:\n{e}")


# ---------------------- Helper ----------------------
def open_main_dashboard():
    """Open main admin dashboard."""
    root.destroy()
    _run_script(MAIN_GUI_PATH, "admin dashboard")


def open_take_attendance():
    """Run attendance without logging in."""
    _run_script(TAKE_ATTENDANCE_PATH, "attendance module")


# ---------------------- Forgot Password ----------------------
def forgot_password():
    username = simpledialog.askstring("Forgot Password", "Enter your username:")
    if not username:
        return

    question = get_security_question(username)
    if not question:
        messagebox.showerror("Error", "Username not found.")
        return

    answer = simpledialog.askstring("Security Question", f"{question}")
    if not answer:
        return

    new_password = simpledialog.askstring("Reset Password", "Enter new password:", show="*")
    if not new_password:
        return

    confirm_password = simpledialog.askstring("Reset Password", "Confirm new password:", show="*")
    if new_password != confirm_password:
        messagebox.showerror("Error", "Passwords do not match.")
        return

    result = reset_password_if_correct(username, answer, new_password)
    if result:
        messagebox.showinfo("Success", "Password reset successful! Try logging in again.")
    else:
        messagebox.showerror("Error", "Incorrect security answer.")


# ---------------------- Login ----------------------
def login():
    username = username_entry.get()
    password = password_entry.get()

    if verify_login(username, password):
        messagebox.showinfo("Success", f"Welcome, {username}!")
        open_main_dashboard()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")


# ---------------------- UI ----------------------
root = tk.Tk()
root.title("Face Recognition Attendance System - Login")
root.geometry("420x400")
root.config(bg="#ecf0f1")

tk.Label(root, text="Admin Login", font=("Arial", 20, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(pady=20)

tk.Label(root, text="Username:", bg="#ecf0f1", font=("Arial", 12)).pack()
username_entry = tk.Entry(root, width=30)
username_entry.pack(pady=5)

tk.Label(root, text="Password:", bg="#ecf0f1", font=("Arial", 12)).pack()
password_entry = tk.Entry(root, show="*", width=30)
password_entry.pack(pady=5)

tk.Button(
    root,
    text="Login",
    width=20,
    height=2,
    bg="#27ae60",
    fg="white",
    font=("Arial", 11, "bold"),
    command=login,
).pack(pady=15)

tk.Button(
    root,
    text="Forgot Password?",
    bg="#ecf0f1",
    fg="#2980b9",
    bd=0,
    font=("Arial", 10, "underline"),
    command=forgot_password,
).pack(pady=5)

# ---------------------- Take Attendance Button ----------------------
tk.Label(root, text="OR", bg="#ecf0f1", font=("Arial", 11, "bold")).pack(pady=8)
tk.Button(
    root,
    text="Take Attendance",
    width=20,
    height=2,
    bg="#8e44ad",
    fg="white",
    font=("Arial", 11, "bold"),
    command=open_take_attendance,
).pack(pady=8)

root.mainloop()
