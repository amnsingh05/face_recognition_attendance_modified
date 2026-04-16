import os
import re
import subprocess
import sys
import threading
import traceback
import tkinter as tk
from tkinter import messagebox

from admin_utils import add_user, change_password, validate_password_strength
from train_model import train_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")

BG_APP = "#F4F7FB"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#D8E0EA"
TEXT_MAIN = "#0F172A"
TEXT_MUTED = "#475569"
PRIMARY = "#0F766E"
PRIMARY_HOVER = "#0D665F"

root = None
status_var = None


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


def _styled_button(parent, text, command, bg, hover, fg="white", pady=9):
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
        font=("Segoe UI", 10, "bold"),
        pady=pady,
    )
    button.bind("<Enter>", lambda _: _on_enter(button, hover))
    button.bind("<Leave>", lambda _: _on_leave(button, bg))
    return button


def _report_callback_exception(exc, val, tb):
    error_text = "".join(traceback.format_exception(exc, val, tb))
    messagebox.showerror("Unexpected Error", error_text)
    _set_status("Unexpected error occurred.")


def _run_script_worker(script_name, script_path):
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        root.after(
            0,
            lambda: (
                messagebox.showerror("Error", f"Failed to open {script_name}:\n{exc}"),
                _set_status(f"Failed to open {script_name}."),
            ),
        )
        return

    if result.returncode != 0:
        details = (result.stderr or result.stdout or "Unknown error.").strip()
        root.after(
            0,
            lambda: (
                messagebox.showerror("Error", f"{script_name} failed:\n{details}"),
                _set_status(f"{script_name} failed."),
            ),
        )
    else:
        root.after(0, lambda: _set_status(f"{script_name} closed."))


def run_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    if not os.path.exists(script_path):
        messagebox.showerror("Error", f"{script_name} not found.")
        _set_status(f"{script_name} not found.")
        return

    _set_status(f"Opening {script_name}...")
    worker = threading.Thread(
        target=_run_script_worker,
        args=(script_name, script_path),
        daemon=True,
    )
    worker.start()


def _validate_username(username):
    username = str(username).strip()
    if not USERNAME_PATTERN.fullmatch(username):
        messagebox.showwarning(
            "Input Error",
            "Username must be 3-30 characters and contain only letters, numbers, or underscore.",
        )
        return False
    return True


def _validate_password(password):
    valid, reason = validate_password_strength(password)
    if not valid:
        messagebox.showwarning("Weak Password", reason)
        return False
    return True


def register_face():
    run_script("register_face.py")


def take_attendance():
    run_script("take_attendance.py")


def view_attendance():
    run_script("view_attendance.py")


def train_model_action():
    _set_status("Training model...")
    messagebox.showinfo("Info", "Training started. Please wait.")
    train_model()
    _set_status("Model training completed.")


def _form_entry(parent, label_text, show=None):
    tk.Label(
        parent,
        text=label_text,
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10, "bold"),
        anchor="w",
    ).pack(fill="x", pady=(0, 5))

    frame = tk.Frame(parent, bg=CARD_BORDER, highlightthickness=1, highlightbackground=CARD_BORDER)
    frame.pack(fill="x", pady=(0, 12))

    entry = tk.Entry(
        frame,
        show=show,
        relief="flat",
        bd=0,
        font=("Segoe UI", 11),
        bg="#FFFFFF",
        fg=TEXT_MAIN,
        insertbackground=TEXT_MAIN,
    )
    entry.pack(fill="x", padx=10, pady=8)
    return entry


def _build_modal(title, width, height):
    modal = tk.Toplevel(root)
    modal.title(title)
    modal.configure(bg=BG_APP)
    modal.resizable(False, False)

    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_w = root.winfo_width()
    root_h = root.winfo_height()

    x = root_x + max((root_w - width) // 2, 0)
    y = root_y + max((root_h - height) // 2, 0)
    modal.geometry(f"{width}x{height}+{x}+{y}")

    card = tk.Frame(
        modal,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=CARD_BORDER,
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    return modal, card


def open_change_password_window():
    modal, card = _build_modal("Change Password", 460, 400)

    inner = tk.Frame(card, bg=CARD_BG)
    inner.pack(fill="both", expand=True, padx=22, pady=20)

    tk.Label(
        inner,
        text="Change Password",
        bg=CARD_BG,
        fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 17),
    ).pack(anchor="w", pady=(0, 14))

    username_entry = _form_entry(inner, "Username")
    old_entry = _form_entry(inner, "Current Password", show="*")
    new_entry = _form_entry(inner, "New Password", show="*")

    def save_new_pass():
        user = username_entry.get().strip()
        old = old_entry.get().strip()
        new = new_entry.get().strip()

        if not user or not old or not new:
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        if not _validate_username(user) or not _validate_password(new):
            return

        if change_password(user, old, new):
            messagebox.showinfo("Success", "Password updated successfully.")
            _set_status(f"Password updated for {user}.")
            modal.destroy()
        else:
            messagebox.showerror("Error", "Incorrect credentials or invalid new password.")

    _styled_button(inner, "Save Password", save_new_pass, PRIMARY, PRIMARY_HOVER).pack(fill="x", pady=(8, 0))


def open_add_admin_window():
    modal, card = _build_modal("Add New Admin", 500, 500)

    inner = tk.Frame(card, bg=CARD_BG)
    inner.pack(fill="both", expand=True, padx=22, pady=20)

    tk.Label(
        inner,
        text="Create New Admin",
        bg=CARD_BG,
        fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 17),
    ).pack(anchor="w", pady=(0, 14))

    username_entry = _form_entry(inner, "New Username")
    password_entry = _form_entry(inner, "New Password", show="*")
    question_entry = _form_entry(inner, "Security Question")
    answer_entry = _form_entry(inner, "Security Answer")

    def save_new_admin():
        user = username_entry.get().strip()
        pwd = password_entry.get().strip()
        question = question_entry.get().strip()
        answer = answer_entry.get().strip()

        if not user or not pwd or not question or not answer:
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        if not _validate_username(user) or not _validate_password(pwd):
            return

        if add_user(user, pwd, question, answer):
            messagebox.showinfo("Success", "New admin added successfully.")
            _set_status(f"New admin created: {user}")
            modal.destroy()
        else:
            messagebox.showerror("Error", "Username already exists or data is invalid.")

    _styled_button(inner, "Save Admin", save_new_admin, PRIMARY, PRIMARY_HOVER).pack(fill="x", pady=(8, 0))


def open_attendance_folder():
    attendance_dir = os.path.join(BASE_DIR, "attendance")
    os.makedirs(attendance_dir, exist_ok=True)

    try:
        os.startfile(attendance_dir)  # type: ignore[attr-defined]
        _set_status("Attendance folder opened.")
    except Exception as exc:
        messagebox.showerror("Error", f"Could not open attendance folder:\n{exc}")
        _set_status("Failed to open attendance folder.")


def _action_card(parent, row, col, title, command, color, hover):
    card = tk.Frame(
        parent,
        bg=CARD_BG,
        highlightthickness=1,
        highlightbackground=CARD_BORDER,
    )
    card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    inner = tk.Frame(card, bg=CARD_BG)
    inner.pack(fill="both", expand=True, padx=14, pady=14)

    tk.Label(
        inner,
        text=title,
        bg=CARD_BG,
        fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 13),
        anchor="w",
    ).pack(fill="x", pady=(0, 12))

    _styled_button(inner, "Open", command, color, hover).pack(fill="x")


def build_ui():
    global root, status_var

    root = tk.Tk()
    root.title("Admin Dashboard")
    root.configure(bg=BG_APP)
    root.resizable(False, False)
    root.report_callback_exception = _report_callback_exception
    _center_window(root, 980, 660)

    shell = tk.Frame(root, bg=BG_APP)
    shell.pack(fill="both", expand=True, padx=16, pady=16)

    header = tk.Frame(shell, bg=BG_APP)
    header.pack(fill="x", pady=(4, 10))

    tk.Label(
        header,
        text="Dashboard",
        bg=BG_APP,
        fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 24),
    ).pack(anchor="w")

    cards = tk.Frame(shell, bg=BG_APP)
    cards.pack(fill="both", expand=True)

    for i in range(2):
        cards.columnconfigure(i, weight=1)
    for i in range(4):
        cards.rowconfigure(i, weight=1)

    actions = [
        ("Register New Face", register_face, "#2563EB", "#1D4ED8"),
        ("Train Model", train_model_action, "#0F766E", "#0D665F"),
        ("Take Attendance", take_attendance, "#7C3AED", "#6D28D9"),
        ("View Attendance", view_attendance, "#EA580C", "#C2410C"),
        ("Open Attendance Folder", open_attendance_folder, "#334155", "#1E293B"),
        ("Change Password", open_change_password_window, "#BE185D", "#9D174D"),
        ("Add New Admin", open_add_admin_window, "#0EA5E9", "#0284C7"),
        ("Logout", root.destroy, "#DC2626", "#B91C1C"),
    ]

    for idx, (title, command, color, hover) in enumerate(actions):
        row = idx // 2
        col = idx % 2
        _action_card(cards, row, col, title, command, color, hover)

    status_var = tk.StringVar(value="Ready")
    status_bar = tk.Label(
        root,
        textvariable=status_var,
        bg="#E2E8F0",
        fg="#334155",
        anchor="w",
        padx=12,
        pady=6,
        font=("Segoe UI", 9),
    )
    status_bar.pack(fill="x", side="bottom")


if __name__ == "__main__":
    build_ui()
    root.mainloop()
