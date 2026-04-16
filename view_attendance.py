import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ATTENDANCE_DIR = os.path.join(BASE_DIR, "attendance")
os.makedirs(ATTENDANCE_DIR, exist_ok=True)

BG_APP = "#EEF3F8"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#D7DFEA"
TEXT_MAIN = "#0F172A"
TEXT_MUTED = "#475569"
PRIMARY = "#0F766E"
PRIMARY_HOVER = "#0D665F"
SECONDARY = "#1E293B"
SECONDARY_HOVER = "#111827"
ACCENT = "#EA580C"
ACCENT_HOVER = "#C2410C"

root = None
tree = None
search_entry = None
date_combobox = None

current_df = pd.DataFrame(columns=["Name", "Date", "Time"])
visible_df = pd.DataFrame(columns=["Name", "Date", "Time"])

search_var = None
date_filter_var = None
stats_var = None
file_var = None


def _center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = max((screen_width - width) // 2, 0)
    y = max((screen_height - height) // 2, 0)
    window.geometry(f"{width}x{height}+{x}+{y}")


def _configure_ttk_styles(window):
    style = ttk.Style(window)
    style.theme_use("clam")

    style.configure(
        "Modern.Treeview",
        background="#FFFFFF",
        foreground=TEXT_MAIN,
        rowheight=34,
        fieldbackground="#FFFFFF",
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Modern.Treeview.Heading",
        background="#DCE7F5",
        foreground="#1E293B",
        relief="flat",
        font=("Segoe UI", 10, "bold"),
        padding=(6, 8),
    )
    style.map(
        "Modern.Treeview",
        background=[("selected", "#CFE8E5")],
        foreground=[("selected", TEXT_MAIN)],
    )

    style.configure(
        "Modern.Vertical.TScrollbar",
        troughcolor="#E7EDF5",
        background="#94A3B8",
        arrowcolor="#334155",
        bordercolor="#E7EDF5",
        darkcolor="#E7EDF5",
        lightcolor="#E7EDF5",
    )


def _on_enter(button, hover_color):
    button.configure(bg=hover_color)


def _on_leave(button, normal_color):
    button.configure(bg=normal_color)


def _styled_button(parent, text, command, bg, hover, fg="white", width=14):
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
        width=width,
        pady=7,
    )
    button.bind("<Enter>", lambda _: _on_enter(button, hover))
    button.bind("<Leave>", lambda _: _on_leave(button, bg))
    return button


def clear_table():
    if tree is None:
        return

    for item in tree.get_children():
        tree.delete(item)


def _display_value(value):
    if pd.isna(value):
        return "-"

    value = str(value).strip()
    return value if value else "-"


def _set_file_label(file_path):
    if file_var is None:
        return

    if file_path:
        file_var.set(f"Loaded File: {os.path.basename(file_path)}")
    else:
        file_var.set("Loaded File: None")


def _update_stats(df):
    if stats_var is None:
        return

    total_records = len(df)
    unique_people = 0 if df.empty else df["Name"].nunique()
    stats_var.set(f"Visible Records: {total_records}    Unique People: {unique_people}")


def _render_dataframe(df):
    global visible_df

    clear_table()

    if df is None or df.empty:
        visible_df = pd.DataFrame(columns=["Name", "Date", "Time"])
        _update_stats(visible_df)
        return

    for idx, (_, row) in enumerate(df.iterrows()):
        tag = "even" if idx % 2 == 0 else "odd"
        tree.insert(
            "",
            "end",
            values=(
                _display_value(row["Name"]),
                _display_value(row["Date"]),
                _display_value(row["Time"]),
            ),
            tags=(tag,),
        )

    tree.tag_configure("even", background="#FFFFFF")
    tree.tag_configure("odd", background="#F8FAFC")

    visible_df = df.copy()
    _update_stats(visible_df)


def _normalize_attendance_dataframe(df):
    if df.empty:
        return pd.DataFrame(columns=["Name", "Date", "Time"])

    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    name_col = next((c for c in df.columns if c in ["name", "username"]), None)
    date_col = next((c for c in df.columns if c == "date" or "date" in c), None)
    time_col = next((c for c in df.columns if c == "time" or "time" in c), None)

    if not name_col or not time_col:
        raise ValueError("Invalid attendance format. Required columns: Name and Time.")

    normalized = pd.DataFrame(
        {
            "Name": df[name_col].apply(_display_value),
            "Date": df[date_col].apply(_display_value) if date_col else "-",
            "Time": df[time_col].apply(_display_value),
        }
    )

    return normalized.reset_index(drop=True)


def _refresh_date_filter_options():
    if date_filter_var is None or date_combobox is None:
        return

    if current_df.empty:
        values = ["All Dates"]
    else:
        unique_dates = sorted(
            {
                date
                for date in current_df["Date"].astype(str).tolist()
                if date and date != "-"
            }
        )
        values = ["All Dates"] + unique_dates

    date_combobox.configure(values=values)

    if date_filter_var.get() not in values:
        date_filter_var.set("All Dates")


def load_dataframe(file_path):
    global current_df

    try:
        df = pd.read_csv(file_path)
        current_df = _normalize_attendance_dataframe(df)
        _set_file_label(file_path)
        _refresh_date_filter_options()
        apply_filter()

        if current_df.empty:
            messagebox.showinfo("No Records", "This attendance file has no rows yet.")

    except Exception as exc:
        messagebox.showerror("Error", f"Failed to load attendance:\n{exc}")


def apply_filter(*_):
    filtered = current_df.copy()

    selected_date = date_filter_var.get().strip() if date_filter_var is not None else "All Dates"
    if selected_date and selected_date != "All Dates":
        filtered = filtered[filtered["Date"].astype(str) == selected_date]

    query = search_var.get().strip().lower() if search_var is not None else ""
    if query:
        mask = (
            filtered["Name"].astype(str).str.lower().str.contains(query, na=False)
            | filtered["Date"].astype(str).str.lower().str.contains(query, na=False)
            | filtered["Time"].astype(str).str.lower().str.contains(query, na=False)
        )
        filtered = filtered[mask]

    _render_dataframe(filtered.reset_index(drop=True))


def clear_filter():
    if search_var is not None:
        search_var.set("")
    if date_filter_var is not None:
        date_filter_var.set("All Dates")
    apply_filter()


def open_attendance_file():
    file_path = filedialog.askopenfilename(
        initialdir=ATTENDANCE_DIR,
        title="Select Attendance File",
        filetypes=[("CSV Files", "*.csv")],
    )
    if file_path:
        load_dataframe(file_path)


def load_latest_file():
    try:
        files = [
            os.path.join(ATTENDANCE_DIR, filename)
            for filename in os.listdir(ATTENDANCE_DIR)
            if filename.lower().endswith(".csv")
        ]

        if not files:
            messagebox.showwarning("No Data", "No attendance files found.")
            _set_file_label(None)
            _render_dataframe(pd.DataFrame(columns=["Name", "Date", "Time"]))
            _refresh_date_filter_options()
            return

        latest_file = max(files, key=os.path.getmtime)
        load_dataframe(latest_file)

    except Exception as exc:
        messagebox.showerror("Error", str(exc))


def export_current_csv():
    if visible_df.empty:
        messagebox.showwarning("No Data", "There is no attendance data to export.")
        return

    save_path = filedialog.asksaveasfilename(
        initialdir=ATTENDANCE_DIR,
        title="Export as CSV",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
    )
    if not save_path:
        return

    try:
        visible_df.to_csv(save_path, index=False)
        messagebox.showinfo("Success", f"Exported CSV:\n{save_path}")
    except Exception as exc:
        messagebox.showerror("Error", f"Failed to export CSV:\n{exc}")


def export_current_excel():
    if visible_df.empty:
        messagebox.showwarning("No Data", "There is no attendance data to export.")
        return

    save_path = filedialog.asksaveasfilename(
        initialdir=ATTENDANCE_DIR,
        title="Export as Excel",
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx")],
    )
    if not save_path:
        return

    try:
        visible_df.to_excel(save_path, index=False)
        messagebox.showinfo("Success", f"Exported Excel:\n{save_path}")
    except Exception as exc:
        messagebox.showerror(
            "Error",
            f"Failed to export Excel:\n{exc}\n\nTip: install dependency using `pip install openpyxl`.",
        )


def _focus_search(_event=None):
    if search_entry is not None:
        search_entry.focus_set()
        search_entry.select_range(0, "end")


def build_ui():
    global root, tree, search_entry, date_combobox
    global search_var, date_filter_var, stats_var, file_var

    root = tk.Tk()
    root.title("View Attendance Records")
    root.configure(bg=BG_APP)
    root.resizable(False, False)
    _center_window(root, 1120, 700)

    _configure_ttk_styles(root)

    shell = tk.Frame(root, bg=BG_APP)
    shell.pack(fill="both", expand=True, padx=16, pady=16)

    header_card = tk.Frame(shell, bg=CARD_BG, highlightthickness=1, highlightbackground=CARD_BORDER)
    header_card.pack(fill="x")

    header_inner = tk.Frame(header_card, bg=CARD_BG)
    header_inner.pack(fill="x", padx=18, pady=16)

    tk.Label(
        header_inner,
        text="Attendance Records",
        bg=CARD_BG,
        fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 22),
    ).pack(anchor="w")

    tk.Label(
        header_inner,
        text="Search by name/date/time, filter by date, and export clean reports.",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
    ).pack(anchor="w", pady=(4, 0))

    info_row = tk.Frame(shell, bg=BG_APP)
    info_row.pack(fill="x", pady=(10, 8))

    file_var = tk.StringVar(value="Loaded File: None")
    stats_var = tk.StringVar(value="Visible Records: 0    Unique People: 0")

    file_chip = tk.Label(
        info_row,
        textvariable=file_var,
        bg="#DCE7F5",
        fg="#1E293B",
        font=("Segoe UI", 9, "bold"),
        padx=10,
        pady=6,
    )
    file_chip.pack(side="left")

    stats_chip = tk.Label(
        info_row,
        textvariable=stats_var,
        bg="#DCFCE7",
        fg="#166534",
        font=("Segoe UI", 9, "bold"),
        padx=10,
        pady=6,
    )
    stats_chip.pack(side="left", padx=(8, 0))

    filter_card = tk.Frame(shell, bg=CARD_BG, highlightthickness=1, highlightbackground=CARD_BORDER)
    filter_card.pack(fill="x")

    filter_inner = tk.Frame(filter_card, bg=CARD_BG)
    filter_inner.pack(fill="x", padx=14, pady=12)

    tk.Label(
        filter_inner,
        text="Search",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10, "bold"),
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        filter_inner,
        textvariable=search_var,
        width=32,
        font=("Segoe UI", 10),
        relief="flat",
        bd=0,
        bg="#F8FAFC",
        fg=TEXT_MAIN,
        insertbackground=TEXT_MAIN,
    )
    search_entry.pack(side="left", padx=(8, 14), ipady=7)
    search_var.trace_add("write", apply_filter)

    tk.Label(
        filter_inner,
        text="Date",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10, "bold"),
    ).pack(side="left")

    date_filter_var = tk.StringVar(value="All Dates")
    date_combobox = ttk.Combobox(
        filter_inner,
        textvariable=date_filter_var,
        state="readonly",
        width=16,
        font=("Segoe UI", 10),
    )
    date_combobox.pack(side="left", padx=(8, 10))
    date_combobox.bind("<<ComboboxSelected>>", apply_filter)

    _styled_button(filter_inner, "Clear", clear_filter, SECONDARY, SECONDARY_HOVER, width=10).pack(
        side="left"
    )

    table_card = tk.Frame(shell, bg=CARD_BG, highlightthickness=1, highlightbackground=CARD_BORDER)
    table_card.pack(fill="both", expand=True, pady=(10, 0))

    table_frame = tk.Frame(table_card, bg=CARD_BG)
    table_frame.pack(fill="both", expand=True, padx=12, pady=12)

    columns = ("Name", "Date", "Time")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Modern.Treeview")

    column_widths = {"Name": 380, "Date": 220, "Time": 220}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=column_widths[col])

    yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview, style="Modern.Vertical.TScrollbar")
    tree.configure(yscrollcommand=yscroll.set)

    tree.pack(side="left", fill="both", expand=True)
    yscroll.pack(side="right", fill="y")

    actions = tk.Frame(shell, bg=BG_APP)
    actions.pack(fill="x", pady=(12, 0))

    _styled_button(actions, "Open File", open_attendance_file, PRIMARY, PRIMARY_HOVER).pack(
        side="left",
        padx=(0, 8),
    )
    _styled_button(actions, "Load Latest", load_latest_file, SECONDARY, SECONDARY_HOVER).pack(
        side="left",
        padx=(0, 8),
    )
    _styled_button(actions, "Export CSV", export_current_csv, "#2563EB", "#1D4ED8").pack(
        side="left",
        padx=(0, 8),
    )
    _styled_button(actions, "Export Excel", export_current_excel, ACCENT, ACCENT_HOVER).pack(
        side="left",
        padx=(0, 8),
    )
    _styled_button(actions, "Close", root.destroy, "#DC2626", "#B91C1C", width=10).pack(side="right")

    root.bind("<Control-f>", _focus_search)


if __name__ == "__main__":
    build_ui()
    _refresh_date_filter_options()
    load_latest_file()
    root.mainloop()
