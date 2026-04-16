import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ATTENDANCE_DIR = os.path.join(BASE_DIR, "attendance")
os.makedirs(ATTENDANCE_DIR, exist_ok=True)

# ---------------- Functions ----------------

def clear_table():
    for item in tree.get_children():
        tree.delete(item)

def load_dataframe(file_path):
    """Safely load CSV and normalize columns."""
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            raise ValueError("Attendance file is empty")

        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]

        # Map possible column names
        name_col = next((c for c in df.columns if c in ["name", "username"]), None)
        time_col = next((c for c in df.columns if "time" in c), None)
        date_col = next((c for c in df.columns if "date" in c), None)

        if not name_col or not time_col:
            raise ValueError("Invalid attendance file format")

        clear_table()

        for _, row in df.iterrows():
            tree.insert(
                "",
                "end",
                values=(
                    row.get(name_col, "-"),
                    row.get(date_col, "-") if date_col else "-",
                    row.get(time_col, "-")
                )
            )

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load attendance:\n{e}")

def open_attendance_file():
    file_path = filedialog.askopenfilename(
        initialdir=ATTENDANCE_DIR,
        title="Select Attendance File",
        filetypes=[("CSV Files", "*.csv")]
    )
    if file_path:
        load_dataframe(file_path)
        messagebox.showinfo("Loaded", os.path.basename(file_path))

def load_latest_file():
    try:
        files = [
            os.path.join(ATTENDANCE_DIR, f)
            for f in os.listdir(ATTENDANCE_DIR)
            if f.endswith(".csv")
        ]

        if not files:
            messagebox.showwarning("No Data", "No attendance files found.")
            return

        latest_file = max(files, key=os.path.getctime)
        load_dataframe(latest_file)
        messagebox.showinfo("Loaded", f"Latest file: {os.path.basename(latest_file)}")

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ---------------- GUI ----------------

root = tk.Tk()
root.title("View Attendance Records")
root.geometry("600x420")

tk.Label(
    root,
    text="Attendance Records",
    font=("Helvetica", 16, "bold")
).pack(pady=10)

# Table
frame = tk.Frame(root)
frame.pack(fill="both", expand=True, padx=10)

columns = ("Name", "Date", "Time")
tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.pack(fill="both", expand=True)

# Buttons
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Open File", width=18, command=open_attendance_file).grid(row=0, column=0, padx=8)
tk.Button(btn_frame, text="Load Latest", width=15, command=load_latest_file).grid(row=0, column=1, padx=8)
tk.Button(btn_frame, text="Close", width=10, command=root.destroy).grid(row=0, column=2, padx=8)

root.mainloop()
