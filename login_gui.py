import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog

from admin_utils import (
    get_security_question,
    reset_password_if_correct,
    validate_password_strength,
    verify_login,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_GUI_PATH = os.path.join(BASE_DIR, "main_gui.py")
TAKE_ATTENDANCE_PATH = os.path.join(BASE_DIR, "take_attendance.py")

BG_APP = "#EFF3F8"
BG_BRAND = "#0F172A"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#D7DFEA"
PRIMARY = "#0F766E"
PRIMARY_HOVER = "#0D665F"
SECONDARY = "#1E293B"
SECONDARY_HOVER = "#111827"
ACCENT = "#EA580C"
TEXT_MAIN = "#0F172A"
TEXT_MUTED = "#475569"
TEXT_LIGHT = "#E2E8F0"
ERROR = "#B91C1C"
SUCCESS = "#0F766E"

username_entry = None
password_entry = None
show_password_var = None
status_var = None
root = None


def _center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = max((screen_width - width) // 2, 0)
    y = max((screen_height - height) // 2, 0)
    window.geometry(f"{width}x{height}+{x}+{y}")


def _set_status(message):
    if status_var is not None:
        status_var.set(message)


def _on_enter(button, hover_color):
    button.configure(bg=hover_color)


def _on_leave(button, normal_color):
    button.configure(bg=normal_color)


def _styled_button(parent, text, command, bg, hover, fg="white", width=24, pady=10):
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        activebackground=hover,
        activeforeground=fg,
        relief="flat",
        bd=0,
        cursor="hand2",
        width=width,
        pady=pady,
        font=("Segoe UI", 10, "bold"),
    )
    button.bind("<Enter>", lambda _: _on_enter(button, hover))
    button.bind("<Leave>", lambda _: _on_leave(button, bg))
    return button


def _launch_script(script_path, error_context):
    try:
        subprocess.Popen([sys.executable, script_path], cwd=BASE_DIR)
        return True
    except Exception as exc:
        messagebox.showerror("Error", f"Could not open {error_context}:\n{exc}")
        _set_status(f"Could not open {error_context}.")
        return False


def _toggle_password_visibility():
    if password_entry is None or show_password_var is None:
        return

    password_entry.configure(show="" if show_password_var.get() else "*")


def open_main_dashboard():
    root.withdraw()
    ok = _launch_script(MAIN_GUI_PATH, "admin dashboard")
    if ok:
        root.destroy()
    else:
        root.deiconify()


def open_take_attendance():
    _set_status("Opening attendance camera module...")
    _launch_script(TAKE_ATTENDANCE_PATH, "attendance module")


def forgot_password():
    username = simpledialog.askstring("Forgot Password", "Enter your username:")
    if not username:
        return

    question = get_security_question(username)
    if not question:
        messagebox.showerror("Error", "Username not found.")
        _set_status("Password reset failed. Username not found.")
        return

    answer = simpledialog.askstring("Security Question", question)
    if not answer:
        return

    new_password = simpledialog.askstring("Reset Password", "Enter new password:", show="*")
    if not new_password:
        return

    valid, reason = validate_password_strength(new_password)
    if not valid:
        messagebox.showwarning("Weak Password", reason)
        _set_status("Password reset failed due to weak password.")
        return

    confirm_password = simpledialog.askstring(
        "Reset Password",
        "Confirm new password:",
        show="*",
    )
    if new_password != confirm_password:
        messagebox.showerror("Error", "Passwords do not match.")
        _set_status("Password reset failed. Passwords did not match.")
        return

    result = reset_password_if_correct(username, answer, new_password)
    if result:
        messagebox.showinfo("Success", "Password reset successful. Try logging in again.")
        _set_status("Password reset completed.")
    else:
        messagebox.showerror("Error", "Incorrect security answer or invalid password.")
        _set_status("Password reset failed. Try again.")


def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if not username or not password:
        _set_status("Enter both username and password.")
        return

    if verify_login(username, password):
        _set_status("Login successful. Opening dashboard...")
        open_main_dashboard()
    else:
        _set_status("Invalid username or password.")
        messagebox.showerror("Login Failed", "Invalid username or password.")


def _labeled_entry(parent, label_text, show=None):
    tk.Label(
        parent,
        text=label_text,
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10, "bold"),
        anchor="w",
    ).pack(fill="x", pady=(0, 6))

    frame = tk.Frame(parent, bg=CARD_BORDER, bd=0, highlightthickness=1, highlightbackground=CARD_BORDER)
    frame.pack(fill="x", pady=(0, 14))

    entry = tk.Entry(
        frame,
        show=show,
        relief="flat",
        bd=0,
        bg="#FFFFFF",
        fg=TEXT_MAIN,
        font=("Segoe UI", 11),
        insertbackground=TEXT_MAIN,
    )
    entry.pack(fill="x", padx=10, pady=9)
    return entry


def build_ui():
    global root, username_entry, password_entry, show_password_var, status_var

    root = tk.Tk()
    root.title("Face Recognition Attendance System - Login")
    root.configure(bg=BG_APP)
    root.resizable(False, False)
    _center_window(root, 940, 560)

    shell = tk.Frame(root, bg=BG_APP)
    shell.pack(fill="both", expand=True, padx=18, pady=18)

    brand_panel = tk.Frame(shell, bg=BG_BRAND, width=340)
    brand_panel.pack(side="left", fill="y")
    brand_panel.pack_propagate(False)

    tk.Label(
        brand_panel,
        text="Face Attendance",
        bg=BG_BRAND,
        fg="white",
        font=("Segoe UI Semibold", 24),
    ).pack(anchor="w", padx=28, pady=(36, 8))

    tk.Label(
        brand_panel,
        text="Secure and simple attendance management",
        bg=BG_BRAND,
        fg=TEXT_LIGHT,
        font=("Segoe UI", 11),
        wraplength=280,
        justify="left",
    ).pack(anchor="w", padx=28, pady=(0, 22))

    for item in [
        "Register and train faces quickly",
        "Take live attendance with camera",
        "View and export attendance records",
    ]:
        tk.Label(
            brand_panel,
            text=f"- {item}",
            bg=BG_BRAND,
            fg="#CBD5E1",
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=30, pady=3)

    tk.Frame(brand_panel, bg="#1E293B", height=1).pack(fill="x", padx=28, pady=(28, 18))

    tk.Label(
        brand_panel,
        text="Tip: Use admin123 for first login and update it immediately.",
        bg=BG_BRAND,
        fg="#94A3B8",
        font=("Segoe UI", 9),
        wraplength=280,
        justify="left",
    ).pack(anchor="w", padx=28)

    content_area = tk.Frame(shell, bg=BG_APP)
    content_area.pack(side="left", fill="both", expand=True, padx=(18, 0))

    card = tk.Frame(
        content_area,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=CARD_BORDER,
        bd=0,
    )
    card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.82, relheight=0.84)

    inner = tk.Frame(card, bg=CARD_BG)
    inner.pack(fill="both", expand=True, padx=34, pady=28)

    tk.Label(
        inner,
        text="Admin Sign In",
        bg=CARD_BG,
        fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 20),
    ).pack(anchor="w")

    tk.Label(
        inner,
        text="Access dashboard controls and attendance reports",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
    ).pack(anchor="w", pady=(4, 24))

    username_entry = _labeled_entry(inner, "Username")
    password_entry = _labeled_entry(inner, "Password", show="*")

    show_password_var = tk.BooleanVar(value=False)
    tk.Checkbutton(
        inner,
        text="Show password",
        variable=show_password_var,
        command=_toggle_password_visibility,
        bg=CARD_BG,
        fg=TEXT_MUTED,
        activebackground=CARD_BG,
        activeforeground=TEXT_MAIN,
        selectcolor=CARD_BG,
        font=("Segoe UI", 9),
        cursor="hand2",
    ).pack(anchor="w", pady=(0, 16))

    _styled_button(inner, "Login", login, PRIMARY, PRIMARY_HOVER).pack(fill="x", pady=(2, 10))

    _styled_button(
        inner,
        "Forgot Password",
        forgot_password,
        SECONDARY,
        SECONDARY_HOVER,
        width=24,
        pady=8,
    ).pack(fill="x", pady=(0, 10))

    _styled_button(
        inner,
        "Take Attendance Without Login",
        open_take_attendance,
        ACCENT,
        "#C2410C",
        width=24,
        pady=8,
    ).pack(fill="x")

    status_var = tk.StringVar(value="Ready")
    tk.Label(
        inner,
        textvariable=status_var,
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 9),
        anchor="w",
    ).pack(fill="x", pady=(18, 0))

    root.bind("<Return>", lambda _: login())
    username_entry.focus_set()


if __name__ == "__main__":
    build_ui()
    root.mainloop()
