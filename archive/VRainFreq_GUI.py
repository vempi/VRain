import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import scipy.stats as stats
import matplotlib.ticker as ticker
import os
import sys
import glob
import webbrowser

def _base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────── Shared utilities ────────────────────────────

LICENSE_TEXT = (
    "VRain | Frequency Analysis Tool (VRainFreq) v.1\n\n"
    "Software License Agreement / Perjanjian Lisensi Perangkat Lunak\n\n"
    "Copyright (c) 2025 Vempi Satriya Adi Hendrawan\n\n"
    "Permission is granted to use this software for education or commercial purposes.\n"
    "Izin diberikan untuk menggunakan perangkat lunak ini untuk keperluan edukasi atau komersial.\n\n"
    "Restrictions:\n"
    "- You may not distribute, modify, or sell this software without permission.\n\n"
    "Disclaimer:\n"
    "This software is provided \"as is\" without warranties.\n\n"
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

class FrequencyAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VRain | Frequency Analysis Tool (VRainFreq v.1)")
        self.root.geometry("800x500")
        
        self.file_paths = []
        self.data = None
        self.dfs = None
        
        # Menu Bar
        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open File...", command=self.load_files)
        file_menu.add_command(label="Load Demo", command=self.load_demo)
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        about_menu = tk.Menu(menu_bar, tearoff=0)
        about_menu.add_command(label="License", command=self.show_license)
        about_menu.add_command(label="Help", command=lambda: webbrowser.open("https://github.com/vempi/VRain.exe/blob/main/help/vrainfreq_v1.md"))
        about_menu.add_separator()
        about_menu.add_command(label="Website", command=lambda: webbrowser.open("https://vempi.staff.ugm.ac.id"))
        menu_bar.add_cascade(label="About", menu=about_menu)

        # Header
        hdr = tk.Frame(root, bg="#4682B4", pady=6)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="VRain  |  Frequency Analysis Tool  (VRainFreq)",
                 font=("Arial", 12, "bold"), bg="#4682B4", fg="white").pack()
        tk.Label(hdr, text="Fit distributions and compute rainfall return levels",
                 font=("Arial", 9), bg="#4682B4", fg="#d0e8f8").pack()

        # Status bar (packed last via side=BOTTOM)
        self.status_var = tk.StringVar(value="Ready  —  Load a file or click Demo to get started.")
        tk.Label(root, textvariable=self.status_var, anchor="w",
                 relief=tk.SUNKEN, fg="gray", font=("Arial", 8),
                 bd=1).pack(fill=tk.X, side=tk.BOTTOM)

        # Main Frames
        frame_left = tk.Frame(root, padx=6, pady=6)
        frame_left.grid(row=0, column=0, sticky="ns")

        frame_right = tk.Frame(root)
        frame_right.grid(row=0, column=1, sticky="nsew")
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        # ── Input group ──────────────────────────────────────────────────────
        inp_frame = tk.LabelFrame(frame_left, text="Input", padx=5, pady=5)
        inp_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        self.check_multiple = tk.BooleanVar()
        self.chk_multiple = tk.Checkbutton(inp_frame, text="Batch (folder)",
                                            variable=self.check_multiple,
                                            command=self.toggle_batch_mode)
        self.chk_multiple.grid(row=0, column=0, columnspan=2, sticky="w")

        tk.Label(inp_frame, text="File (CSV / XLSX):").grid(row=1, column=0, sticky="w")
        btn_row = tk.Frame(inp_frame)
        btn_row.grid(row=1, column=1, sticky="w")
        self.btn_browse = tk.Button(btn_row, text="Browse", command=self.load_files)
        self.btn_browse.pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row, text="Demo", command=self.load_demo,
                  bg="#e8f4f8").pack(side=tk.LEFT, padx=2)
        
        # ── Analysis settings ────────────────────────────────────────────────
        set_frame = tk.LabelFrame(frame_left, text="Analysis Settings", padx=5, pady=5)
        set_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        tk.Label(set_frame, text="Data column:").grid(row=0, column=0, sticky="w")
        self.combo_column = ttk.Combobox(set_frame, width=14)
        self.combo_column.grid(row=0, column=1, sticky="w", padx=4)

        tk.Label(set_frame, text="Plot method:").grid(row=1, column=0, sticky="w")
        self.combo_method = ttk.Combobox(set_frame, values=["Weibull", "Cunnane", "Hazen"], width=14)
        self.combo_method.grid(row=1, column=1, sticky="w", padx=4)

        tk.Label(set_frame, text="Significance (α):").grid(row=2, column=0, sticky="w")
        self.alpha = tk.StringVar(value="0.05")
        self.alpha_combobox = ttk.Combobox(set_frame, textvariable=self.alpha, state="readonly",
                                            values=("0.01", "0.05", "0.10"), width=14)
        self.alpha_combobox.grid(row=2, column=1, sticky="w", padx=4)
        self.alpha_combobox.current(1)

        tk.Button(set_frame, text="Analyze (plot position)",
                  command=self.perform_analysis).grid(row=3, column=0, columnspan=2, pady=4)

        # ── Statistics table ─────────────────────────────────────────────────
        tk.Label(frame_left, text="Statistics:").grid(row=2, column=0, sticky="w")
        self.tree_stats = ttk.Treeview(frame_left, columns=("Metric", "Value"),
                                        show="headings", height=6)
        self.tree_stats.heading("Metric", text="Metric")
        self.tree_stats.heading("Value", text="Value")
        self.tree_stats.column("Metric", width=140)
        self.tree_stats.column("Value", width=90)
        self.tree_stats.grid(row=3, column=0, columnspan=2, pady=4, sticky="ew")

        # ── Return period settings ────────────────────────────────────────────
        rp_frame = tk.LabelFrame(frame_left, text="Return Periods", padx=5, pady=5)
        rp_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        tk.Label(rp_frame, text="Periods (comma-sep):").grid(row=0, column=0, sticky="w")
        self.entry_prob = tk.Entry(rp_frame, width=22)
        self.entry_prob.grid(row=0, column=1, sticky="w", padx=4)
        self.entry_prob.insert(0, "1.1,5,10,20,50,100,1000")
        tk.Button(rp_frame, text="Convert", command=self.convert_values).grid(row=1, column=0,
                                                                                columnspan=2, pady=3)
        self.tree_prob = ttk.Treeview(rp_frame, columns=("Return Period", "Probability"),
                                       show="headings", height=5)
        self.tree_prob.heading("Return Period", text="Return Period (yr)")
        self.tree_prob.heading("Probability", text="Probability")
        self.tree_prob.column("Return Period", width=120)
        self.tree_prob.column("Probability", width=100)
        self.tree_prob.grid(row=2, column=0, columnspan=2, pady=3, sticky="ew")

        # ── Run & Export ──────────────────────────────────────────────────────
        run_frame = tk.Frame(frame_left)
        run_frame.grid(row=5, column=0, columnspan=2, pady=6)
        tk.Button(run_frame, text="Run Analysis", command=self.perform_anfreq,
                  bg="#4682B4", fg='white', font=("Arial", 10, "bold"),
                  width=14).pack(side=tk.LEFT, padx=4)
        tk.Button(run_frame, text="Export Results",
                  command=self.export_results, width=14).pack(side=tk.LEFT, padx=4)
        
        # Matplotlib Frame
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.fig1, self.ax1 = plt.subplots()
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=frame_right)
        self.canvas1.get_tk_widget().pack(fill="both", expand=True)

        
    def optimal_bins(self):
        """Calculate the optimal number of bins for the Chi-Square test."""
        sturges = int(1 + 3.322 * np.log10(len(self.data)))  # Sturges' Rule
        sqrt_rule = int(np.sqrt(len(self.data)))  # Square Root Rule
        return max(sturges, sqrt_rule)  # Use the larger value
    
    def fit_distributions(self):
        self.gev_params = stats.genextreme.fit(self.data)
        self.norm_params = stats.norm.fit(self.data)
        self.lognorm_params = stats.lognorm.fit(self.data, floc=0)
        self.gumbel_params = stats.gumbel_r.fit(self.data)
        self.logpearson_params = stats.pearson3.fit(np.log(self.data))
    
    def compute_return_levels(self):
        self.gev_levels = stats.genextreme.ppf(1 - self.prob_return, *self.gev_params)
        self.norm_levels = stats.norm.ppf(1 - self.prob_return, *self.norm_params)
        self.lognorm_levels = stats.lognorm.ppf(1 - self.prob_return, *self.lognorm_params)
        self.gumbel_levels = stats.gumbel_r.ppf(1 - self.prob_return, *self.gumbel_params)
        self.logpearson_levels = np.exp(stats.pearson3.ppf(1 - self.prob_return, *self.logpearson_params))
        
        shape, loc, scale = self.gev_params
        self.gev_conf_5 = stats.genextreme.ppf(1 - self.prob_return, shape, loc, scale * 0.95)
        self.gev_conf_95 = stats.genextreme.ppf(1 - self.prob_return, shape, loc, scale * 1.05)
    
    def perform_stat_tests(self):
        self.ks_results = {
            "GEV": stats.kstest(self.data, 'genextreme', args=self.gev_params),
            "Normal": stats.kstest(self.data, 'norm', args=self.norm_params),
            "Log-Normal": stats.kstest(self.data, 'lognorm', args=self.lognorm_params),
            "Gumbel": stats.kstest(self.data, 'gumbel_r', args=self.gumbel_params),
            "Log-Pearson III": stats.kstest(np.log(self.data), 'pearson3', args=self.logpearson_params)
        }
        
        hist_obs, bin_edges = np.histogram(self.data, bins=self.num_bins)
        self.chi_square = {}
        for name, params, dist_func in zip(
            ["GEV", "Normal", "Log-Normal", "Gumbel", "Log-Pearson III"],
            [self.gev_params, self.norm_params, self.lognorm_params, self.gumbel_params, self.logpearson_params],
            [stats.genextreme, stats.norm, stats.lognorm, stats.gumbel_r, stats.pearson3]
        ):
            cdf_vals = dist_func.cdf(bin_edges, *params)
            freqs = len(self.data) * np.diff(cdf_vals)
            freqs *= hist_obs.sum() / freqs.sum()
            freqs[freqs == 0] = 1e-6
            self.chi_square[name] = stats.chisquare(hist_obs, freqs)
    
    def compute_critical_values(self):
        self.ks_critical = 1.36 / np.sqrt(len(self.data))
        self.df_chi = self.num_bins - 1 - len(self.norm_params)
        self.chi_critical = stats.chi2.ppf(1 - float(self.alpha.get()), self.df_chi)
    
    def create_result_dfs(self):
        self.results_pval = pd.DataFrame({
            "Distribution": list(self.ks_results.keys()),
            "KS Statistic": [res.statistic for res in self.ks_results.values()],
            "KS p-value": [res.pvalue for res in self.ks_results.values()],
            "Chi-Square Statistic": [res.statistic for res in self.chi_square.values()],
            "Chi-Square p-value": [res.pvalue for res in self.chi_square.values()]
        })
    
        self.results_cr = pd.DataFrame({
            "Distribution": list(self.ks_results.keys()),
            "Χ²": [self.chi_square[name].statistic for name in self.ks_results.keys()],
            "Χ²_crit": [self.chi_critical] * len(self.ks_results),
            "Chi Result": ["Accepted" if self.chi_square[name].statistic < self.chi_critical else "Rejected" for name in self.ks_results.keys()],
            "Δ_max": [self.ks_results[name].statistic for name in self.ks_results.keys()],
            "Δ_crit": [self.ks_critical] * len(self.ks_results),
            "KS Result": ["Accepted" if self.ks_results[name].statistic < self.ks_critical else "Rejected" for name in self.ks_results.keys()]
        })
        
        self.results_df = pd.DataFrame({
            "Return period": self.return_periods,
            "Probability": self.prob_return,
            "Normal (Median)": self.norm_levels,
            "Log-Normal (Median)": self.lognorm_levels,
            "Gumbel (Median)": self.gumbel_levels,
            "Log-Pearson III (Median)": self.logpearson_levels,
            "GEV (Median)": self.gev_levels
        })
    
    def get_results(self):
        return {
            "KS Test Results": self.results_pval,
            "Chi-Square Test Results": self.results_cr,
            "Return Levels": self.results_df
        }
    
    
    def compute_reduced_variate(self):
        self.z_obs = -np.log(-np.log(self.prob_return_obs))
        self.z_gev = -np.log(-np.log(1 - self.prob_return))
        self.sel_idx = np.linspace(0, len(self.z_gev) - 1, len(self.return_periods), dtype=int)
        self.sel_z = self.z_gev[self.sel_idx]
        
        self.sel_ret = self.return_periods[self.sel_idx]
    
    def plot_frequency_analysis(self):
        
        self.compute_reduced_variate()
        
        prob_labels = 1/(self.return_periods)
        P_exceedance = np.arange(np.ceil(prob_labels[-1]), np.floor(prob_labels[0]) + 1, 1, dtype=int)/100
        prob_scale = -np.log(-np.log(1 - P_exceedance))
        xscale = prob_scale
        
        self.ax.clear()
        self.ax.plot(self.z_obs, np.array(self.data), 'o', mfc='w', mec='k', mew=1.5, label='Observed Events')
        self.ax.plot(self.z_gev, self.gev_levels, 'r-', label='GEV')
        self.ax.plot(self.z_gev, self.norm_levels, 'b-', label='Normal')
        self.ax.plot(self.z_gev, self.lognorm_levels, 'g-', label='Log-Normal')
        self.ax.plot(self.z_gev, self.gumbel_levels, 'm-', label='Gumbel')
        self.ax.plot(self.z_gev, self.logpearson_levels, 'c-', label='Log-Pearson III')
        self.ax.fill_between(self.z_gev, self.gev_conf_5, self.gev_conf_95, color='gray', alpha=0.3, label='GEV 90% CI')
    
        self.ax.set_xlabel("Return Period (years)")
        self.ax.set_xticks(self.sel_z)
        ret_str = [str(x) if x % 1 != 0 else str(int(x)) for x in self.sel_ret]
        self.ax.set_xticklabels(ret_str)
        self.ax.set_ylabel("Precipitation (mm)")
        self.ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
        self.ax.set_title("Frequency Analysis of Rainfall Data (Gumbel Reduced Variate)")
        self.ax.legend()
        self.ax.grid(True, which="both", linestyle="-", linewidth=1, alpha=0.5)
    
        for xv in xscale:
            self.ax.axvline(xv, color='gray', linestyle="-", alpha=0.3, linewidth=0.5, zorder=0)
    
        self.ax0 = self.ax.twiny()
        self.ax0.set_xlim(self.ax.get_xlim())
        self.ax0.set_xlabel("Probability of Exceedance (%)")
        self.ax0.set_xticks(self.z_gev)
        self.ax0.set_xticklabels([f"{p:.1f}%" for p in prob_labels])
    
        self.canvas.draw()

    def plot_histogram_pdf(self):
        # Plot setup
        self.ax1.clear()
        step = 5
        # Histogram        
        bin_edges = np.arange(self.data.min(), self.data.max() + step, step)
        hist_data, bins, _ = self.ax1.hist(self.data, bins=bin_edges, density=True, 
                                     alpha=0.6, color='b', label='Data Frequency')
        
        # X-axis range
        xmin, xmax = self.ax1.get_xlim()
        x = np.linspace(xmin, xmax, 100)
        
        # Define distributions
        distributions = {"Normal": stats.norm,"Log-Normal": stats.lognorm,"Gumbel": stats.gumbel_r,
                         "GEV": stats.genextreme,"Log-Pearson III": stats.pearson3}
        
        # Fit distributions and plot their PDFs
        for name, dist in distributions.items():
            params = dist.fit(self.data)
            pdf_fitted = dist.pdf(x, *params)
            self.ax1.plot(x, pdf_fitted, label=f'{name} Fitted Curve')
        
        # Formatting the plot
        self.ax1.set_title("PDF with Histogram for Multiple Distributions")
        self.ax1.set_xlabel("Rainfall (mm)")
        self.ax1.set_ylabel("Density")
        self.ax1.legend()
        self.ax1.grid(True, linestyle='--', alpha=0.6)
        
        self.canvas1.draw()

    def convert_values(self):
        """Convert user input to numeric values and display them in the Treeview table."""
        str_val = self.entry_prob.get()

        try:
            # Convert input string to a list of numeric values
            self.return_periods = np.array([float(x) if "." in x else int(x) for x in str_val.split(",")])
            self.prob_return = np.array([1/i for i in self.return_periods])

            # Clear previous entries in Treeview
            for item in self.tree_prob.get_children():
                self.tree_prob.delete(item)

            # Insert converted values into Treeview
            for returnperiod in self.return_periods :
                probs = 1/(returnperiod)
                self.tree_prob.insert("", "end", values=(returnperiod, probs))

        except ValueError:
            # Handle invalid input
            self.entry_prob.delete(0, tk.END)
            self.entry_prob.insert(0, "Invalid input! Enter numbers separated by commas.")
    
    def load_demo(self):
        demo_path = os.path.join(_base_path(), "demo", "VRainFreq_demo.csv")
        if os.path.exists(demo_path):
            self.file_paths = [demo_path]
            self._load_file_list()
            self.status_var.set("Demo file loaded — click Run Analysis to see results.")
        else:
            messagebox.showwarning("Demo Not Found",
                f"Demo file not found at:\n{demo_path}")

    def show_license(self):
        win = tk.Toplevel(self.root)
        win.title("Software License Agreement")
        win.geometry("600x380")
        text = tk.Text(win, wrap="word", width=70, height=20)
        text.insert("1.0", LICENSE_TEXT)
        text.insert("end", "vempi.staff.ugm.ac.id", "link")
        text.insert("end", "  |  vempi@ugm.ac.id\n")
        text.tag_configure("link", foreground="blue", underline=True)
        text.tag_bind("link", "<Button-1>",
                      lambda e: webbrowser.open("https://vempi.staff.ugm.ac.id"))
        text.config(state="disabled")
        text.pack(padx=10, pady=10, fill="both", expand=True)
        tk.Button(win, text="OK", command=win.destroy).pack(pady=8)

    def load_files(self):
        if self.check_multiple.get():
            folder_path = filedialog.askdirectory()
            if folder_path:
                self.file_paths = (
                    glob.glob(os.path.join(folder_path, "*.csv")) +
                    glob.glob(os.path.join(folder_path, "*.xlsx")) +
                    glob.glob(os.path.join(folder_path, "*.xls"))
                )
        else:
            file_path = filedialog.askopenfilename(
                filetypes=[("Data files", "*.csv *.xlsx *.xls"),
                            ("CSV files", "*.csv"),
                            ("Excel files", "*.xlsx *.xls"),
                            ("All files", "*.*")])
            self.file_paths = [file_path] if file_path else []

        if self.file_paths:
            self._load_file_list()

    def _load_file_list(self):
        data_list = []
        for i, fp in enumerate(self.file_paths):
            try:
                df = smart_read(fp)
                # Auto-detect time column and use rest as data
                tcol = detect_col(df, ['time', 'date', 'datetime', 'year', 'tahun',
                                       'tanggal', 'waktu'], fallback_idx=0)
                # Rename time column to "date", keep rest
                df = df.rename(columns={tcol: 'date'})
                # Try parsing date column, fall through if it's just a year integer
                try:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                except Exception:
                    pass
                data_list.append(df)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read {fp}: {e}")
                return

        self.dfs = data_list[0]
        for df in data_list[1:]:
            self.dfs = pd.merge(self.dfs, df, on="date", how="outer")

        # Auto-populate column selector: only numeric columns (excluding date)
        num_cols = [c for c in self.dfs.columns
                    if c != 'date' and pd.api.types.is_numeric_dtype(self.dfs[c])]
        self.combo_column["values"] = num_cols
        if num_cols:
            # Pre-select the most likely rain column
            best = detect_col(self.dfs[num_cols], ['rain', 'rainfall', 'hujan', 'precip'])
            self.combo_column.set(best)

        n = len(self.file_paths)
        self.status_var.set(
            f"{n} file(s) loaded — {len(num_cols)} data column(s) detected. "
            f"Selected: {self.combo_column.get()}")
    
    def toggle_batch_mode(self):
        if self.check_multiple.get():
            self.btn_browse.config(text="Browse (Folder)")
        else:
            self.btn_browse.config(text="Browse")
    
    def perform_analysis(self):
        
        if self.dfs is None:
            messagebox.showerror("Error", "No file loaded")
            return
        
        column = self.combo_column.get()
        method = self.combo_method.get()
        
        if not column or column not in self.dfs.columns:
            messagebox.showerror("Error", "Please select a valid column")
            return
        
        if not method:
            messagebox.showerror("Error", "Please select a method")
            return
        
        self.data = np.sort(self.dfs[column].dropna())
        n = len(self.data)
        
        if method == "Weibull":
            self.prob_return_obs = np.array([(i + 1) / (n + 1) for i in range(n)])
        elif method == "Gringorten":
            self.prob_return_obs = np.array([(i - 0.44) / (n + 0.12) for i in range(n)])
        elif method == "Cunnane":
            self.prob_return_obs = np.array([(i + 0.4) / (n + 0.2) for i in range(n)])
        elif method == "Hazen":
            self.prob_return_obs = np.array([(i + 0.5) / n for i in range(n)])
        elif method == "Blom":
            self.prob_return_obs = np.array([(i - 0.375) / (n + 0.25) for i in range(n)])
        else:
            raise ValueError("Invalid method. Choose from: Weibull, Cunnane, Hazen, Gringorten, Blom")
        
        self.calculate_statistics()
        self.show_plot()
    
    def batch_run(self):
        if self.dfs is None:
            messagebox.showerror("Error", "No file loaded")
            return
        
        method = self.combo_method.get()
        if not method:
            messagebox.showerror("Error", "Please select a method")
            return
        
        # Iterate over each column and perform analysis
        for column in self.dfs.columns:

            if self.dfs is None:
                messagebox.showerror("Error", "No file loaded")
                return

            self.data = np.sort(self.dfs[column].dropna())
            n = len(self.data)
            
            self.num_bins = self.optimal_bins()
            self.fit_distributions()
            self.compute_return_levels()
            self.perform_stat_tests()
            self.compute_critical_values()
            self.create_result_dfs()
            
            self.plot_histogram_pdf()
            self.plot_frequency_analysis()
            messagebox.showinfo("Batch Run", f"Analysis completed for column: {column}")

    
    def perform_anfreq(self):
        
        self.num_bins = self.optimal_bins()
        self.fit_distributions()
        self.compute_return_levels()
        self.perform_stat_tests()
        self.compute_critical_values()
        self.create_result_dfs()
        
        self.plot_histogram_pdf()
        self.plot_frequency_analysis()

    def calculate_statistics(self):
        # Compute statistics
        min_val = np.min(self.data)
        max_val = np.max(self.data)
        median_val = np.median(self.data)
        
        # Compute mode (handle multi-mode cases)
        mode_result = stats.mode(self.data, keepdims=True)  # keepdims ensures output is always an array
        mode_val = mode_result.mode[0] if mode_result.count[0] > 0 else "No Mode"
    
        sample_size = len(self.data)
        mean_val = np.mean(self.data)
        std_dev = np.std(self.data, ddof=1)  # Sample standard deviation (ddof=1)
        skew_val = stats.skew(self.data)
        kurtosis_val = stats.kurtosis(self.data, fisher=False)  # Pearson’s kurtosis
    
        # Clear previous entries in tree_stats
        self.tree_stats.delete(*self.tree_stats.get_children())
    
        # Insert new statistics into tree_stats
        self.tree_stats.insert("", "end", values=("Mean", round(mean_val, 4)))
        self.tree_stats.insert("", "end", values=("Median", round(median_val, 4)))
        self.tree_stats.insert("", "end", values=("Mode", mode_val))
        self.tree_stats.insert("", "end", values=("Min", round(min_val, 4)))
        self.tree_stats.insert("", "end", values=("Max", round(max_val, 4)))
        self.tree_stats.insert("", "end", values=("Standard Deviation", round(std_dev, 4)))
        self.tree_stats.insert("", "end", values=("Sample Size", sample_size))
        self.tree_stats.insert("", "end", values=("Skewness", round(skew_val, 4)))
        self.tree_stats.insert("", "end", values=("Kurtosis", round(kurtosis_val, 4)))

    def show_plot(self):
        self.ax.clear()
        self.ax.plot(self.prob_return_obs, self.data, marker="o", linestyle="-")
        self.ax.set_xlabel("Plot Position")
        self.ax.set_ylabel("Value")
        self.ax.set_title("Frequency Analysis Plot")
        self.ax.grid(True)
        for i, txt in enumerate(self.prob_return_obs):
            self.ax.annotate(round(txt, 2), (self.prob_return_obs[i], self.data[i]))
        self.canvas.draw()

    def export_results(self):
        if self.dfs is None:
            messagebox.showerror("Error", "No analysis performed")
            return
        
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", 
                                                 filetypes=[("CSV Files", "*.csv")])
        
        if save_path:
            with open(save_path, "w") as file:
                file.write("Value,Rank,Plot Position\n")
                for row in self.tree_freq.get_children():
                    file.write(",".join(str(x) for x in self.tree_freq.item(row, "values")) + "\n")
            messagebox.showinfo("Success", "Results exported successfully")
        
if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.iconbitmap("3.ico")
    except Exception:
        pass
    app = FrequencyAnalysisApp(root)
    root.mainloop()
