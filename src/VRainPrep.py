import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os
import sys
import numpy as np
import webbrowser
import threading
import queue

def _base_path():
    """Return base directory — handles both normal run and PyInstaller frozen exe."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────── Shared utilities ────────────────────────────

LICENSE_TEXT = (
    "VRain | Hourly Rainfall Data Pre-processor (VRainPrep) v.1\n\n"
    "Software License Agreement / Perjanjian Lisensi Perangkat Lunak\n\n"
    "Copyright (c) 2025 Vempi Satriya Adi Hendrawan\n\n"
    "Permission is granted to use this software for education or commercial purposes.\n"
    "Izin diberikan untuk menggunakan perangkat lunak ini untuk keperluan edukasi atau komersial.\n\n"
    "Restrictions:\n"
    "- You may not distribute, modify, or sell this software without permission.\n"
    "- Anda tidak boleh mendistribusikan, memodifikasi, atau menjual perangkat lunak ini tanpa izin.\n\n"
    "Disclaimer:\n"
    "This software is provided \"as is\" without warranties.\n"
    "Perangkat lunak ini disediakan \"sebagaimana adanya\" tanpa jaminan.\n\n"
    "For enquiries, contact:\n"
)

def smart_read(file_path):
    """Read CSV (comma or semicolon) or Excel file into a DataFrame."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ('.xlsx', '.xls'):
        return pd.read_excel(file_path)
    try:
        df = pd.read_csv(file_path)
        if df.shape[1] == 1:
            df = pd.read_csv(file_path, sep=';')
    except Exception:
        df = pd.read_csv(file_path, sep=';')
    return df

def detect_col(df, keywords, fallback_idx=0):
    """Return first column whose name contains any keyword (case-insensitive)."""
    for col in df.columns:
        if any(kw in col.lower() for kw in keywords):
            return col
    return df.columns[fallback_idx] if len(df.columns) > fallback_idx else df.columns[0]

# ─────────────────────────────── Core logic ──────────────────────────────────

def gather_data(loc='', dirout='', source='UGM-Hidro',
                period='None', calc='Sum',
                progress_callback=None, root_update=None,
                on_error=None, on_success=None):

    def _err(title, msg):
        if on_error:
            on_error(title, msg)
        else:
            messagebox.showerror(title, msg)

    def _info(title, msg):
        if on_success:
            on_success(title, msg)
        else:
            messagebox.showinfo(title, msg)

    if not dirout.endswith("/"):
        dirout += '/'

    def aggregate(dfin, agg_period, calc):
        try:
            dfin.set_index("Time", inplace=True)
        except Exception:
            pass
        agg_options = {
            "30-min": "30T", "1-hour": "1H", "3-hour": "3H", "6-hour": "6H",
            "12-hour": "12H", "24-hour": "24H", "Monthly": "ME", "Quarterly": "QE",
            "Annual": "YE", "Seasonal": "Seasonal"
        }
        time_code = agg_options.get(agg_period)
        if time_code == 'Seasonal':
            dfin['Season'] = dfin.index.to_series().dt.month % 12 // 3
            season_labels = {0: 'DJF', 1: 'MAM', 2: 'JJA', 3: 'SON'}
            dfin['Season'] = dfin['Season'].map(season_labels)
            ops = {'Sum': 'sum', 'Average': 'mean', 'Maximum': 'max',
                   'Minimum': 'min', 'Count': lambda x: (x > 1).sum()}
            if calc in ops:
                res = dfin.groupby('Season').agg(ops[calc])
            else:
                raise ValueError("Invalid calculation type.")
        else:
            ops = {'Sum': 'sum', 'Average': 'mean', 'Maximum': 'max',
                   'Minimum': 'min', 'Count': lambda x: (x > 1).sum()}
            res = dfin.resample(time_code).agg(ops.get(calc, 'sum'))
        res.reset_index(inplace=True)
        return res

    def proPERSIANN(file):
        # PERSIANN raw CSV has a metadata header row then 2-column data rows.
        # e.g.: "Time, Rain(mm), Latitude, -7.792, ..."  (7 cols)
        #        "PERSIANN_1h2010010100, 0.000"           (2 cols)
        # Read with header=None + skiprows=1 + usecols=[0,1] to avoid mismatch.
        try:
            df = pd.read_csv(file, header=None, skiprows=1, usecols=[0, 1],
                             names=['Time', 'Rain'], skipinitialspace=True)
        except Exception:
            df = pd.read_csv(file, sep=';', header=None, skiprows=1, usecols=[0, 1],
                             names=['Time', 'Rain'], skipinitialspace=True)
        df['Rain'] = pd.to_numeric(df['Rain'], errors='coerce')
        df.replace(-99, np.nan, inplace=True)
        pat = r'PERSIANN_1h(\d{4})(\d{2})(\d{2})(\d{2})'
        extracted = df['Time'].astype(str).str.strip().str.extract(pat)
        if extracted.isnull().values.any():
            print("Skipping file due to format issues:", file)
            return None
        datetime_str = extracted.apply(
            lambda x: f"{x[0]}-{x[1]}-{x[2]} {x[3]}:00:00", axis=1)
        df['Time'] = pd.to_datetime(datetime_str, format='%Y-%m-%d %H:%M:%S', errors='coerce')
        return df

    def readRain(fin, source):
        if source == 'PERSIANN':
            dout = proPERSIANN(fin)
        elif source == 'GSMAP':
            raw = smart_read(fin)
            tcol = detect_col(raw, ['time', 'date', 'datetime', 'tanggal', 'waktu'])
            rcol = detect_col(raw, ['rain', 'rainfall', 'hujan', 'precip'], fallback_idx=1)
            dout = raw[[tcol, rcol]]
        elif source == 'GPM':
            tmp = smart_read(fin)
            result = (tmp == "time").to_numpy().nonzero()
            time_row = result[0][0]
            dout = tmp.iloc[time_row + 1:, 0:2]
        elif source == 'UGM-Hidro':
            raw = smart_read(fin)
            tcol = detect_col(raw, ['time', 'date', 'datetime', 'tanggal', 'waktu'])
            rcol = detect_col(raw, ['rain', 'rainfall', 'hujan', 'precip'], fallback_idx=1)
            dout = raw[[tcol, rcol]]
        else:
            raw = smart_read(fin)
            dout = raw.iloc[:, 0:2]

        dout = dout.copy()
        dout.columns = ['Time', 'Rain']
        dout['Time'] = pd.to_datetime(dout['Time'], errors='coerce')
        dout["Rain"] = pd.to_numeric(dout["Rain"], errors='coerce').astype(float)
        return dout

    def list_all_items(path, patterns):
        items = []
        for root_dir, dirs, files in os.walk(path):
            for file in files:
                if any(file.lower().endswith(p) for p in patterns):
                    items.append(os.path.join(root_dir, file))
        return items

    patterns = ['.csv', '.xlsx', '.xls']
    ext = os.path.splitext(loc)[1].lower()
    if ext in ('.csv', '.xlsx', '.xls'):
        if progress_callback:
            progress_callback(0)
        try:
            dfs = readRain(loc, source)
            if progress_callback:
                progress_callback(100)
        except Exception:
            _err("Error", "Please select data source type correctly!")
            return
    else:
        try:
            lsts = list_all_items(loc, patterns)
            if not lsts:
                _err("Error", "No CSV/XLSX files found in the selected directory.")
                return
            total_files = len(lsts)
            dfs = pd.DataFrame()
            if progress_callback:
                progress_callback(0)
            for i, file in enumerate(lsts):
                try:
                    df = readRain(file, source)
                    dfs = pd.concat([dfs, df], ignore_index=True)
                    if progress_callback:
                        progress_callback(int((i + 1) / total_files * 100))
                except Exception:
                    _err("Iteration Error", f"Error reading: {file}")
        except Exception:
            _err("Error", "Error reading files or missing folders!")
            return

    dfs = dfs.sort_values(by='Time').reset_index(drop=True)
    if period != 'None':
        out = aggregate(dfs, period, calc)
    else:
        out = dfs.copy()

    start = str(out['Time'].iloc[0].year)
    end = str(out['Time'].iloc[-1].year)
    output_file = os.path.join(
        dirout, f'VRain-prep_{source}_{start}-{end}_{period}-{calc}.csv')
    try:
        out.to_csv(output_file, index=False)
        _info("Success", f"Processed data saved to:\n{output_file}")
    except Exception:
        _err("Error",
             "File cannot be saved! Make sure the output file is not open in another program.")


# ─────────────────────────────── GUI Application ─────────────────────────────

class VRainPrepApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VRain | Rainfall Data Preparation (VRainPrep) v.1")
        self.root.resizable(True, True)

        try:
            self.root.iconbitmap("1.ico")
        except Exception:
            pass

        self._build_menu()
        self._build_header()
        self._build_input_frame()
        self._build_settings_frame()
        self._build_output_frame()
        self._build_process_section()
        self._build_statusbar()

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _build_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open File...", command=self.select_input_file)
        file_menu.add_command(label="Load Demo", command=self.load_demo)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        about_menu = tk.Menu(menu_bar, tearoff=0)
        about_menu.add_command(label="License", command=self.show_license)
        about_menu.add_command(label="Help", command=self.open_help)
        about_menu.add_separator()
        about_menu.add_command(label="Website", command=self.open_website)
        menu_bar.add_cascade(label="About", menu=about_menu)

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self.root, bg="#4682B4", pady=6)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="VRain  |  Rainfall Data Preparation  (VRainPrep)",
                 font=("Arial", 12, "bold"), bg="#4682B4", fg="white").pack()
        tk.Label(hdr, text="Prepare and aggregate time-series rainfall data",
                 font=("Arial", 9), bg="#4682B4", fg="#d0e8f8").pack()

    # ── Input Frame ───────────────────────────────────────────────────────────

    def _build_input_frame(self):
        frame = tk.LabelFrame(self.root, text="Input", padx=8, pady=6)
        frame.pack(fill=tk.X, padx=10, pady=4)
        frame.columnconfigure(1, weight=1)

        self.input_type_var = tk.StringVar(value="File")
        tk.Radiobutton(frame, text="Single file (CSV / XLSX)",
                       variable=self.input_type_var, value="File",
                       command=self._toggle_input).grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Radiobutton(frame, text="Folder (batch merge)",
                       variable=self.input_type_var, value="Folder",
                       command=self._toggle_input).grid(row=0, column=2, columnspan=2, sticky="w")

        self.input_file_var = tk.StringVar()
        self.input_file_entry = tk.Entry(frame, textvariable=self.input_file_var, width=52)
        self.input_file_entry.grid(row=1, column=0, columnspan=3, padx=4, pady=4, sticky="ew")
        tk.Button(frame, text="Browse", command=self.select_input_file,
                  width=8).grid(row=1, column=3, padx=2)
        tk.Button(frame, text="Demo", command=self.load_demo,
                  bg="#e8f4f8", width=7).grid(row=1, column=4, padx=2)

        self.input_folder_var = tk.StringVar()
        self.input_folder_entry = tk.Entry(frame, textvariable=self.input_folder_var, width=52)
        self.input_folder_btn = tk.Button(frame, text="Browse",
                                          command=self.select_input_folder, width=8)

        tk.Label(frame, text="Data source:").grid(row=3, column=0, sticky="w", pady=4)
        self.data_source_var = tk.StringVar(value="UGM-Hidro")
        ttk.Combobox(frame, textvariable=self.data_source_var,
                     values=['PERSIANN', 'GPM', 'GSMAP', 'UGM-Hidro'],
                     state="readonly", width=18).grid(row=3, column=1, sticky="w", padx=4)

        frame.columnconfigure(1, weight=1)

    # ── Settings Frame ────────────────────────────────────────────────────────

    def _build_settings_frame(self):
        frame = tk.LabelFrame(self.root, text="Settings", padx=8, pady=6)
        frame.pack(fill=tk.X, padx=10, pady=4)

        tk.Label(frame, text="Aggregate period:").grid(row=0, column=0, sticky="w")
        self.time_var = tk.StringVar(value="None")
        ttk.Combobox(frame, textvariable=self.time_var,
                     values=["None", "30-min", "1-hour", "3-hour", "6-hour",
                             "12-hour", "24-hour", "Monthly", "Quarterly",
                             "Annual", "Seasonal"],
                     state="readonly", width=18).grid(row=0, column=1, sticky="w", padx=8, pady=3)

        tk.Label(frame, text="Calculation method:").grid(row=1, column=0, sticky="w")
        self.stat_var = tk.StringVar(value="Sum")
        ttk.Combobox(frame, textvariable=self.stat_var,
                     values=["Minimum", "Average", "Maximum", "Sum", "Count"],
                     state="readonly", width=18).grid(row=1, column=1, sticky="w", padx=8, pady=3)

    # ── Output Frame ──────────────────────────────────────────────────────────

    def _build_output_frame(self):
        frame = tk.LabelFrame(self.root, text="Output", padx=8, pady=6)
        frame.pack(fill=tk.X, padx=10, pady=4)
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Output folder:").grid(row=0, column=0, sticky="w")
        self.output_folder_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.output_folder_var,
                 width=52).grid(row=0, column=1, sticky="ew", padx=4)
        tk.Button(frame, text="Browse", command=self.select_output_folder,
                  width=8).grid(row=0, column=2, padx=2)

    # ── Process Section ───────────────────────────────────────────────────────

    def _build_process_section(self):
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=6)

        self.process_button = tk.Button(
            btn_frame, text="Process Data", command=self.process_data,
            bg="#4682B4", fg="white", font=("Arial", 10, "bold"), width=18)
        self.process_button.pack(side=tk.LEFT, padx=4)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("VRain.Horizontal.TProgressbar",
                        troughcolor="white", background="#4682B4",
                        troughrelief="flat", thickness=18)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            btn_frame, variable=self.progress_var, maximum=100,
            style="VRain.Horizontal.TProgressbar")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

    # ── Status Bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Ready  —  Load a file or click Demo to get started.")
        tk.Label(self.root, textvariable=self.status_var, anchor="w",
                 relief=tk.SUNKEN, fg="gray", font=("Arial", 8),
                 bd=1).pack(fill=tk.X, side=tk.BOTTOM, padx=0, pady=0)

    # ── Toggle File / Folder input ────────────────────────────────────────────

    def _toggle_input(self):
        if self.input_type_var.get() == "File":
            self.input_file_entry.grid(row=1, column=0, columnspan=3,
                                       padx=4, pady=4, sticky="ew")
            self.input_folder_entry.grid_remove()
            self.input_folder_btn.grid_remove()
            self.process_button.config(text="Process Data")
        else:
            self.input_folder_entry.grid(row=1, column=0, columnspan=3,
                                         padx=4, pady=4, sticky="ew")
            self.input_folder_btn.grid(row=1, column=3, padx=2)
            self.input_file_entry.grid_remove()
            self.process_button.config(text="Merge and Process Data")

    # ── File / Folder selection ───────────────────────────────────────────────

    def select_input_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Data files", "*.csv *.xlsx *.xls"),
                       ("CSV files", "*.csv"),
                       ("Excel files", "*.xlsx *.xls"),
                       ("All files", "*.*")])
        if path:
            self.input_file_var.set(path)
            self.input_type_var.set("File")
            self._toggle_input()
            self.status_var.set(f"File loaded: {os.path.basename(path)}")

    def select_input_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.input_folder_var.set(path)
            self.status_var.set(f"Folder selected: {path}")

    def select_output_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.output_folder_var.set(path)

    # ── Demo ──────────────────────────────────────────────────────────────────

    def load_demo(self):
        demo_path = os.path.join(_base_path(), "demo", "VRainPrep_demo.csv")
        if os.path.exists(demo_path):
            self.input_file_var.set(demo_path)
            self.input_type_var.set("File")
            self._toggle_input()
            self.data_source_var.set("UGM-Hidro")
            self.time_var.set("24-hour")
            self.stat_var.set("Sum")
            self.status_var.set("Demo file loaded — set Output folder, then click Process Data.")
        else:
            messagebox.showwarning("Demo Not Found",
                f"Demo file not found at:\n{demo_path}\n\n"
                "Ensure the 'demo' subfolder exists next to VRainPrep.py.")

    # ── Process ───────────────────────────────────────────────────────────────

    def process_data(self):
        if self.input_type_var.get() == "Folder":
            input_dir = self.input_folder_var.get()
        else:
            input_dir = self.input_file_var.get()
        output_dir = self.output_folder_var.get()

        if not input_dir or not output_dir:
            messagebox.showerror("Error", "Please select both input and output.")
            return

        self.status_var.set("Processing…")
        self.progress_var.set(0)
        self.process_button.config(state="disabled")
        self.root.update_idletasks()

        msg_q = queue.Queue()

        def run():
            gather_data(
                loc=input_dir, dirout=output_dir,
                source=self.data_source_var.get(),
                period=self.time_var.get(),
                calc=self.stat_var.get(),
                progress_callback=lambda v: msg_q.put(('progress', v)),
                on_error=lambda t, m: msg_q.put(('error', (t, m))),
                on_success=lambda t, m: msg_q.put(('info', (t, m))),
            )
            msg_q.put(('done', None))

        threading.Thread(target=run, daemon=True).start()
        self._poll_queue(msg_q)

    def _poll_queue(self, msg_q):
        try:
            while True:
                kind, payload = msg_q.get_nowait()
                if kind == 'progress':
                    self.progress_var.set(payload)
                elif kind == 'error':
                    messagebox.showerror(*payload)
                elif kind == 'info':
                    messagebox.showinfo(*payload)
                elif kind == 'done':
                    self.status_var.set("Done.")
                    self.process_button.config(state="normal")
                    return
        except queue.Empty:
            pass
        self.root.after(50, self._poll_queue, msg_q)

    # ── About ─────────────────────────────────────────────────────────────────

    def show_license(self):
        win = tk.Toplevel(self.root)
        win.title("Software License Agreement")
        win.geometry("600x380")
        text = tk.Text(win, wrap="word", width=70, height=20)
        text.insert("1.0", LICENSE_TEXT)
        text.insert("end", "vempi.staff.ugm.ac.id", "link")
        text.insert("end", "  |  vempi@ugm.ac.id\n")
        text.tag_configure("link", foreground="blue", underline=True)
        text.tag_bind("link", "<Button-1>", lambda e: self.open_website())
        text.config(state="disabled")
        text.pack(padx=10, pady=10, fill="both", expand=True)
        tk.Button(win, text="OK", command=win.destroy).pack(pady=8)

    def open_help(self):
        webbrowser.open("https://github.com/vempi/VRain.exe/blob/main/help/vrainprep_v1.md")

    def open_website(self):
        webbrowser.open("https://vempi.staff.ugm.ac.id")


# ─────────────────────────────── Entry point ─────────────────────────────────

if os.environ.get("PYTHON_SPLASH"):
    from ctypes import windll
    windll.user32.PostQuitMessage(0)

try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

root = tk.Tk()
app = VRainPrepApp(root)
root.mainloop()
