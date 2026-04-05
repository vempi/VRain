import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import scipy.stats as stats
import matplotlib.ticker as ticker
import glob, os
import lmoments3 as lm
from lmoments3 import distr as lmdistr
from scipy import special
import concurrent.futures
from datetime import datetime

class FrequencyAnalysisApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("VRain | Frequency Analysis Tool (VRainFreq) v.2")
        self.root.state('zoomed')  # Maximized window (Windows)
    
        # Initialize variables
        self.file_paths = []
        self.data = None
        self.dfs = None
        self.output_dir = os.getcwd()
        self.ensure_output_dir()
        self.setup_error_log()
    
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
        # Menu Bar
        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)
        
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.load_files)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="License", command=self.show_license)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        # ========== CRITICAL LAYOUT CHANGES START HERE ========== #
        
        # Configure root grid weights FIRST
        self.root.grid_columnconfigure(0, weight=0)  # Left frame (no expansion)
        self.root.grid_columnconfigure(1, weight=1)  # Right frame (expands)
        self.root.grid_rowconfigure(0, weight=1)     # Single row
        
        # Main Frames
        frame_left = tk.Frame(self.root, padx=5, pady=5)
        frame_left.grid(row=0, column=0, sticky="nswe")
        
        frame_right = tk.Frame(self.root, bg='#f0f0f0')  # Add background for visibility
        frame_right.grid(row=0, column=1, sticky="nsew")
        
        # Configure frame_right grid
        frame_right.grid_rowconfigure(0, weight=1)
        frame_right.grid_columnconfigure(0, weight=1)
        
        # Plot container - use grid instead of pack
        self.plot_container = tk.Frame(frame_right, bg='white')  # Temporary color for debugging
        self.plot_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.plot_container.grid_propagate(False)  # Prevent auto-resizing
        
        self.plot_container.grid_rowconfigure(0, weight=3)  # 60% for top plot
        self.plot_container.grid_rowconfigure(1, weight=2)  # 40% for bottom plot
        self.plot_container.grid_columnconfigure(0, weight=1)
        
        # ========== MATPLOTLIB CANVAS SETUP ========== #
        
        # Figure 1 (Frequency Analysis)
        self.fig1 = plt.Figure(figsize=(8, 6), dpi=100)
        self.ax1 = self.fig1.add_subplot(111)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.plot_container)
        self.canvas1_widget = self.canvas1.get_tk_widget()
        self.canvas1_widget.grid(row=0, column=0, sticky="nsew", pady=(0,5))
        self.canvas1_widget.grid_remove()   # <-- HIDE initially
        
        # Figure 2 (Histogram)
        self.fig2 = plt.Figure(figsize=(8, 6), dpi=100)
        self.ax2 = self.fig2.add_subplot(111)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.plot_container)
        self.canvas2_widget = self.canvas2.get_tk_widget()
        self.canvas2_widget.grid(row=1, column=0, sticky="nsew", pady=(5,0))
        self.canvas2_widget.grid_remove()   # <-- HIDE initially
        
        # ========== REST OF THE UI COMPONENTS ========== #
        
        # Distribution Selection Frame
        dist_frame = tk.LabelFrame(frame_left, text="Select Distributions (Graph)")
        dist_frame.grid(row=13, column=0, columnspan=2, pady=5, sticky="ew")
                
        # Create dictionary to store distribution selections
        self.dist_vars = { "GEV (MLE)": tk.BooleanVar(value=True),
                          "GEV (Lmom)": tk.BooleanVar(value=False),
                          "GEV (Manual)": tk.BooleanVar(value=False),
                          "Normal": tk.BooleanVar(value=True),
                          "Log-Normal": tk.BooleanVar(value=True),
                          "Gumbel": tk.BooleanVar(value=True),
                          "Log-Pearson III": tk.BooleanVar(value=True),
                          "Gamma": tk.BooleanVar(value=True)}
    
        # Create checkboxes in 2 columns
        col1_frame = tk.Frame(dist_frame)
        col1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        col2_frame = tk.Frame(dist_frame)
        col2_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        # Column 1
        tk.Checkbutton(col1_frame, text="GEV (MLE)", variable=self.dist_vars["GEV (MLE)"]).pack(anchor="w")
        tk.Checkbutton(col1_frame, text="GEV (Lmom)", variable=self.dist_vars["GEV (Lmom)"]).pack(anchor="w")
        tk.Checkbutton(col1_frame, text="GEV (Manual)", variable=self.dist_vars["GEV (Manual)"]).pack(anchor="w")
        tk.Checkbutton(col1_frame, text="Normal", variable=self.dist_vars["Normal"]).pack(anchor="w")
    
        # Column 2
        tk.Checkbutton(col2_frame, text="Log-Normal", variable=self.dist_vars["Log-Normal"]).pack(anchor="w")
        tk.Checkbutton(col2_frame, text="Gumbel", variable=self.dist_vars["Gumbel"]).pack(anchor="w")
        tk.Checkbutton(col2_frame, text="Log-Pearson III", variable=self.dist_vars["Log-Pearson III"]).pack(anchor="w")
        tk.Checkbutton(col2_frame, text="Gamma", variable=self.dist_vars["Gamma"]).pack(anchor="w")
    
        # Now initialize the progress bar
        self.progress_frame = tk.Frame(frame_left)
        self.progress_frame.grid(row=15, column=0, columnspan=2, pady=5, sticky="ew")
        
        self.progress_label = tk.Label(self.progress_frame, text="Progress:")
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.progress_percent = tk.Label(self.progress_frame, text="0%")
        self.progress_percent.pack(side=tk.LEFT, padx=5)
        
        # Initially hide the progress bar
        self.progress_frame.grid_remove()
        
        # Input Components
        self.check_multiple = tk.BooleanVar()
        self.chk_multiple = tk.Checkbutton(frame_left, text="Enable Batch Analysis (files in a folder)", variable=self.check_multiple, command=self.toggle_batch_mode)
        self.chk_multiple.grid(row=0, column=0, columnspan=2, pady=2, sticky="w")
        
        tk.Label(frame_left, text="Select File(s):").grid(row=1, column=0, sticky="w")
        self.btn_browse = tk.Button(frame_left, text="Browse", command=self.load_files)
        self.btn_browse.grid(row=1, column=1, sticky="w")
        
        tk.Label(frame_left, text="Column (for single run):").grid(row=2, column=0, sticky="w")
        self.combo_column = ttk.Combobox(frame_left)
        self.combo_column.grid(row=2, column=1, sticky="w")

        tk.Label(frame_left, text="Ranking Method (plot only):").grid(row=3, column=0, sticky="w")
        self.combo_method = ttk.Combobox(frame_left, values=["Weibull", "Cunnane", "Hazen", "Gringorten", "Blom", "Tukey"])
        self.combo_method.set("Gringorten")  # Set default value
        self.combo_method.grid(row=3, column=1, sticky="w")
        
        # Significance Level Combobox
        tk.Label(frame_left, text="Significance Level (α):").grid(row=6, column=0, sticky="w")
        self.alpha = tk.StringVar(value="0.05")
        self.alpha_combobox = ttk.Combobox(frame_left, textvariable=self.alpha, state="readonly", values=("0.01", "0.05", "0.10"))
        self.alpha_combobox.grid(row=6, column=1, sticky="w")
        self.alpha_combobox.current(1)
        
        # Return Period Entry
        tk.Label(frame_left, text="Return Periods:").grid(row=7, column=0, columnspan=2, sticky="w")
        self.entry_prob = tk.Entry(frame_left, width=30)
        self.entry_prob.grid(row=7, column=1, columnspan=2, sticky="w")
        self.entry_prob.insert(0, "1.1,5,10,20,50,100,200")
        
        tk.Button(frame_left, text="Set Probabilities", command=self.convert_values).grid(row=8, column=0, columnspan=2, pady=5)
        
        # Probability Table
        self.tree_prob = ttk.Treeview(frame_left, columns=("Return Period","Probability"), show="headings")
        self.tree_prob.heading("Return Period", text="Return Period (years)")
        self.tree_prob.heading("Probability", text="Probability")
        self.tree_prob.grid(row=9, column=0, columnspan=3, pady=5, sticky="ew")
        
        tk.Label(frame_left, text="Output Directory (optional):").grid(row=10, column=0, sticky="w")
        self.btn_browse_output = tk.Button(frame_left, text="Browse", command=self.browse_output_dir)
        self.btn_browse_output.grid(row=10, column=1, sticky="w")
        
        # Batch Run Button
        self.btn_run = tk.Button(frame_left, text="Run Frequency Analysis", command=self.perform_anfreq, bg="#4682B4", fg="white")
        self.btn_run.grid(row=11, column=0, sticky="ew", padx=2, pady=5)
                        
        self.btn_batch_run = tk.Button(frame_left, text="Batch Run", command=self.batch_run, bg="#32CD32", fg="white")
        self.btn_batch_run.grid(row=11, column=1, sticky="ew", padx=2, pady=5)
        
        # Add a checkbox for batch run confirmation
        self.batch_confirm = tk.BooleanVar(value=False)
        self.chk_confirm = tk.Checkbutton(frame_left, text="Show confirmations during batch run", 
                                          variable=self.batch_confirm)
        self.chk_confirm.grid(row=12, column=0, columnspan=2, pady=2, sticky="w")
        # Add button to concatenate CSV files
        self.btn_concat = tk.Button(frame_left, text="Concatenate Output CSVs", 
                                   command=self.concatenate_outputs)
        self.btn_concat.grid(row=14, column=0, columnspan=2, pady=5)

        # ================ Add progress bar frame and widgets ================ #
        self.progress_frame = tk.Frame(frame_left)
        self.progress_frame.grid(row=15, column=0, columnspan=2, pady=5, sticky="ew")
        
        self.progress_label = tk.Label(self.progress_frame, text="Progress:")
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.progress_percent = tk.Label(self.progress_frame, text="0%")
        self.progress_percent.pack(side=tk.LEFT, padx=5)
        
        # Initially hide the progress bar
        self.progress_frame.grid_remove()
        
        
        # ========================= Add resize handler ======================== #
        # 
        #self.root.bind('<Configure>', self.on_resize)
        
        # Force initial layout calculation
        self.root.update_idletasks()
        print(f"Canvas1 size: {self.canvas1_widget.winfo_width()}x{self.canvas1_widget.winfo_height()}")
    
                
    def on_resize(self, event):
        """Handle window resize events for both canvases"""
        try:
            if not hasattr(self, 'fig1') or not hasattr(self, 'fig2'):
                return
    
            # Calculate proportional sizes (50% width each, minus margins)
            total_width = max(4, event.width - 20)
            canvas_width = total_width // 2
            canvas_height = max(4, event.height - 20)
    
            # Convert pixels to inches (matplotlib uses inches)
            dpi = self.fig1.get_dpi()
            width_in = canvas_width / dpi
            height_in = canvas_height / dpi
    
            # Resize figures
            self.fig1.set_size_inches(width_in, height_in)
            self.fig2.set_size_inches(width_in, height_in)
    
            # Resize tkinter canvas widgets
            self.canvas1.get_tk_widget().config(width=canvas_width, height=canvas_height)
            self.canvas2.get_tk_widget().config(width=canvas_width, height=canvas_height)
    
            # Redraw both canvases
            self.canvas1.draw()
            self.canvas2.draw()
    
        except Exception as e:
            print(f"Resize error: {e}")

    
    def setup_error_log(self):
        """Initialize error log file with timestamp"""
        self.error_log_path = os.path.join(self.output_dir, "VRain_errors.log")
        with open(self.error_log_path, 'a') as f:
            f.write(f"\n\n=== New Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    def log_error(self, context, error):
        """Centralized error logging"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"[{timestamp}] {context}: {str(error)}"
        # 1. Console
        print(error_msg)
        # 2. File
        try:
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                f.write(error_msg + "\n")
        except Exception as file_error:
            print(f"LOGGING FAILED: Could not write to {self.error_log_path}: {file_error}")
        # 3. UI Feedback
        brief_msg = f"{context}: {str(error)[:100]}"
        if hasattr(self, 'status_var'): self.status_var.set(f"⚠️ {brief_msg}")
        else: self.show_toast(brief_msg)
    
    def show_toast(self, message, duration=3000):
        toast = tk.Toplevel(self.root)  # Changed from 'root' to 'self.root'
        toast.overrideredirect(True)
        toast.geometry(f"+{self.root.winfo_x()+50}+{self.root.winfo_y()+50}")
        toast.attributes('-alpha', 0.9)        
        label = ttk.Label(toast, text=message, background='#ffdddd', relief='solid')
        label.pack(padx=10, pady=5)
        toast.after(duration, toast.destroy)
        
    def fit_distributions(self):
        # Add Gamma distribution fitting0
        self.gamma_params = stats.gamma.fit(self.data)
        # 1. MLE SciPy
        self.gev_params_scipy = stats.genextreme.fit(self.data)
        # 2. L-moments (pakai lmoments3)
        sample_lmom = lm.lmom_ratios(self.data, nmom=4)
        self.gev_params_lmom = lmdistr.gev.lmom_fit(sample_lmom)
        
        # 3. L-moments manual
        def lmoments_manual(data):
            """Hitung L-moments manual dari data"""
            data = np.sort(data)
            n = len(data)
            # Probability Weighted Moments (PWMs)
            b0 = np.mean(data)
            b1 = np.sum(((np.arange(1, n+1) - 1) / (n-1)) * data) / n
            b2 = np.sum((((np.arange(1, n+1) - 1) * (np.arange(1, n+1) - 2)) /
                         ((n-1) * (n-2))) * data) / n
            # L-moments
            l1 = b0
            l2 = 2*b1 - b0
            l3 = 6*b2 - 6*b1 + b0
            # L-skewness
            t3 = l3 / l2 if l2 != 0 else 0.0
            return l1, l2, t3
        """Estimasi parameter GEV dari L-moments manual"""
        l1, l2, t3 = lmoments_manual(self.data)

        # Parameter shape (k), scale (alpha), location (xi)
        k = 7.8590 * t3 + 2.9554 * (t3**2)
        denom = (1 - 2**(-k)) * special.gamma(1 + k)
        alpha = l2 * k / denom if denom != 0 else np.nan
        xi = l1 - (alpha * (1 - special.gamma(1 + k))) / k if not np.isnan(alpha) else l1
        self.gev_params_manual = (k, xi, alpha)

        # k = 7.8590 * t3 + 2.9554 * (t3**2)
        # alpha = l2 * k / ((1 - 2**(-k)) * special.gamma(1 + k))
        # xi = l1 - (alpha * (1 - special.gamma(1 + k))) / k
        # self.gev_params_manual = (k, xi, alpha)

        # Distribusi lain (tetap sama)
        self.norm_params = stats.norm.fit(self.data)
        self.lognorm_params = stats.lognorm.fit(self.data, floc=0)
        self.gumbel_params = stats.gumbel_r.fit(self.data)
        self.logpearson_params = stats.pearson3.fit(np.log(self.data))

    def compute_return_levels(self):
        alpha = float(self.alpha.get())
        
        # Add Gamma return levels if selected
        self.gamma_levels = stats.gamma.ppf(1 - self.prob_return, *self.gamma_params)
        # 1. GEV - MLE SciPy
        self.gev_levels_scipy = stats.genextreme.ppf(1 - self.prob_return, *self.gev_params_scipy)
        # 2. GEV - L-moments library
        gev_c, gev_loc, gev_scale = self.gev_params_lmom['c'], self.gev_params_lmom['loc'], self.gev_params_lmom['scale']
        self.gev_levels_lmom = stats.genextreme.ppf(1 - self.prob_return, gev_c, gev_loc, gev_scale)
        # 3. GEV - L-moments manual
        shape, loc, scale = self.gev_params_manual
        self.gev_levels_manual = stats.genextreme.ppf(1 - self.prob_return, shape, loc, scale)
        # Distribusi lain
        self.norm_levels = stats.norm.ppf(1 - self.prob_return, *self.norm_params)
        self.lognorm_levels = stats.lognorm.ppf(1 - self.prob_return, *self.lognorm_params)
        self.gumbel_levels = stats.gumbel_r.ppf(1 - self.prob_return, *self.gumbel_params)
        self.logpearson_levels = np.exp(stats.pearson3.ppf(1 - self.prob_return, *self.logpearson_params))

        # Confidence interval untuk GEV MLE
        shape, loc, scale = self.gev_params_scipy
        self.gev_conf_low = stats.genextreme.ppf((1 - self.prob_return) - alpha/2, shape, loc, scale)
        self.gev_conf_high = stats.genextreme.ppf((1 - self.prob_return) + alpha/2, shape, loc, scale)
        
    def optimal_bins(self):
        """Compute robust number of histogram bins using multiple rules."""
        n = len(self.data)
        if n < 2:
            return 5  # fallback for very small datasets
    
        # Sturges' rule
        sturges = int(np.ceil(1 + 3.322 * np.log10(n)))
        # Square root rule
        sqrt_rule = int(np.ceil(np.sqrt(n)))
        # Freedman-Diaconis rule (robust to outliers)
        q75, q25 = np.percentile(self.data, [75, 25])
        iqr = q75 - q25
        fd_bins = int(np.ceil((np.max(self.data) - np.min(self.data)) / (2 * iqr / n**(1/3)))) if iqr > 0 else sqrt_rule
    
        # Combine rules
        num_bins = max(sturges, sqrt_rule, fd_bins, 5)  # at least 5 bins
        return num_bins
    
    def perform_stat_tests(self):
        """Lakukan uji statistik (K-S dan Chi-square) untuk semua distribusi yang sudah difit."""
    
        # --------------------
        # Daftar distribusi yang sudah difit
        # --------------------
        distributions = [
            ("GEV (SciPy)", stats.genextreme, self.gev_params_scipy),
            ("GEV (Lmom)", stats.genextreme, 
             (self.gev_params_lmom['c'], self.gev_params_lmom['loc'], self.gev_params_lmom['scale'])),
            ("GEV (Manual)", stats.genextreme, self.gev_params_manual),
            ("Normal", stats.norm, self.norm_params),
            ("Log-Normal", stats.lognorm, self.lognorm_params),
            ("Gumbel", stats.gumbel_r, self.gumbel_params),
            ("Log-Pearson III", stats.pearson3, self.logpearson_params),
            ("Gamma", stats.gamma, self.gamma_params)
        ]
    
        self.lst_params = {
            ("GEV (MLE)", self.gev_params_scipy),
            ("GEV (Lmom)", (self.gev_params_lmom['c'], self.gev_params_lmom['loc'], self.gev_params_lmom['scale'])),
            ("GEV (Manual)", self.gev_params_manual),
            ("Normal", self.norm_params),
            ("Log-Normal", self.lognorm_params),
            ("Gumbel", self.gumbel_params),
            ("Log-Pearson III", self.logpearson_params),
            ("Gamma", self.gamma_params)
        }
    
        # --------------------
        # Kolmogorov–Smirnov test
        # --------------------
        self.ks_results = {}
        for name, dist_func, params in distributions:
            if name == "Log-Pearson III":
                # Uji pada data log-transform
                transformed_data = np.log(self.data)
                self.ks_results[name] = stats.kstest(transformed_data, dist_func.name, args=params)
            else:
                self.ks_results[name] = stats.kstest(self.data, dist_func.name, args=params)
    
        # --------------------
        # Chi-square test
        # --------------------
        hist_obs, bin_edges = np.histogram(self.data, bins=self.num_bins)
        #print(self.num_bins)
        self.chi_square = {}
    
        for name, dist_func, params in distributions:
            # Hitung nilai CDF untuk setiap tepi bin
            if name == "Log-Pearson III":
                cdf_vals = dist_func.cdf(np.log(bin_edges), *params)
            else:
                cdf_vals = dist_func.cdf(bin_edges, *params)
    
            # Hitung frekuensi harapan
            expected_freq = len(self.data) * np.diff(cdf_vals)
    
            # Sesuaikan agar total expected sama dengan total observed
            total_obs = hist_obs.sum()
            total_exp = expected_freq.sum()
            if total_exp > 0:
                expected_freq *= (total_obs / total_exp)
    
            # Hanya ambil bin yang punya expected > 0
            mask = expected_freq > 0
            if mask.sum() < 2:
                # Kalau terlalu sedikit bin valid, skip
                self.chi_square[name] = (np.nan, np.nan, 0)
                continue
    
            # Hitung Chi-square statistic manual
            chi2_stat = ((hist_obs[mask] - expected_freq[mask])**2 / expected_freq[mask]).sum()
            dof = max(1, mask.sum() - len(params) - 1)
            p_value = 1 - stats.chi2.cdf(chi2_stat, dof)
            self.chi_square[name] = (chi2_stat, p_value, dof)

    def compute_critical_values(self):
        self.ks_critical = 1.36 / np.sqrt(len(self.data))
        self.df_chi = self.num_bins - 1 - len(self.norm_params)
        self.chi_critical = stats.chi2.ppf(1 - float(self.alpha.get()), self.df_chi)


    
    def compute_critical_values(self):
        """Compute critical values with safe fallback."""
        n = len(self.data)
        self.ks_critical = 1.36 / np.sqrt(n)
        try:
            self.df_chi = max(1, self.num_bins - 1 - len(self.norm_params))
            self.chi_critical = stats.chi2.ppf(1 - float(self.alpha.get()), self.df_chi)
        except Exception:
            self.df_chi = 1
            self.chi_critical = stats.chi2.ppf(0.95, 1)

    
    def create_result_dfs(self):
        # Ensure output directory exists
        self.ensure_output_dir()
        
        def get_chi_stat(name):
            """Ambil nilai statistic dari hasil chi-square."""
            res = self.chi_square[name]
            if hasattr(res, "statistic"):  # hasil dari scipy.stats.chisquare()
                return res.statistic
            elif isinstance(res, (tuple, list)) and len(res) >= 1:
                return res[0]
            return None
    
        def get_chi_pvalue(name):
            """Ambil nilai p-value dari hasil chi-square."""
            res = self.chi_square[name]
            if hasattr(res, "pvalue"):
                return res.pvalue
            elif isinstance(res, (tuple, list)) and len(res) >= 2:
                return res[1]
            return None
    
        # Buat dataframe hasil statistik
        self.results_stat = pd.DataFrame({
            "Distribution": list(self.ks_results.keys()),
            "Chi-square": [get_chi_stat(name) for name in self.ks_results.keys()],
            "Chi crit": [self.chi_critical] * len(self.ks_results),
            "Chi Result": [
                "Accepted" if (get_chi_stat(name) is not None and get_chi_stat(name) < self.chi_critical) else "Rejected"
                for name in self.ks_results.keys()
            ],
            "Chi-Square p-value": [get_chi_pvalue(name) for name in self.ks_results.keys()],
            "Delta KS max": [self.ks_results[name].statistic for name in self.ks_results.keys()],
            "Delta KS crit": [self.ks_critical] * len(self.ks_results),
            "KS Result": [
                "Accepted" if self.ks_results[name].statistic < self.ks_critical else "Rejected"
                for name in self.ks_results.keys()
            ]
        })
    
        # Dataframe return level
        self.results_df = pd.DataFrame({
            "Return period": self.return_periods,
            "Probability": self.prob_return,
            "Normal": self.norm_levels,
            "Log-Normal": self.lognorm_levels,
            "Gumbel": self.gumbel_levels,
            "Log-Pearson III": self.logpearson_levels,
            "GEV_manual": self.gev_levels_manual,
            "GEV_MLE": self.gev_levels_scipy,
            "GEV_lmom": self.gev_levels_lmom
        })
    
        # Simpan hasil ke CSV
        output_path = os.path.join(self.output_dir, f"VRain_stat-test_{self.station_name}.csv")
        self.results_stat.to_csv(output_path, index=False)
        
        output_path = os.path.join(self.output_dir, f"VRain_return-level_{self.station_name}.csv")
        self.results_df.to_csv(output_path, index=False)

    def get_results(self):
        return {
            #"Distribution Parameters": self.param_str,
            "Test Results": self.results_stat,
            "Return Levels": self.results_df
        }
    
    def compute_reduced_variate(self):
        self.z_obs = -np.log(-np.log(self.prob_return_obs))
        self.z_gev = -np.log(-np.log(1 - self.prob_return))
        self.sel_idx = np.linspace(0, len(self.z_gev) - 1, len(self.return_periods), dtype=int)
        self.sel_z = self.z_gev[self.sel_idx]
        self.sel_ret = self.return_periods[self.sel_idx]
    
    def add_annotation(self, ax):
        mu, epsilon, R = self.gev_params_scipy  # Unpack parameters
        param_text = "GEV parameters\n"  # Title
        param_text += f"μ = {mu:.3f}  ∈ = {epsilon:.3f}  R = {R:.3f}\n\n"
        param_text += f"Note: Horizontal axis is scaled\nusing Gumbel (EV I) reduced variate"        
        
        ax.text(0.65, 0.05, param_text, transform=ax.transAxes, fontsize=10, 
                ha='left', va='bottom', bbox=dict(facecolor='white', alpha=0.5))
    
    def plot_frequency_analysis(self): 
        if self.data is None or len(self.data) == 0:
            print("No data to plot!")
            return
        try:
            self.compute_reduced_variate()
            self.ax1.clear()  # clear sebelum redraw
            self.canvas1_widget.grid()  # tampilkan canvas1
            #self.ax2.set_axis_on()  # Show axes if needed

            # Calculate dynamic sizes based on figure dimensions
            fig_width, fig_height = self.fig1.get_size_inches()
            title_fontsize = max(10, min(16, fig_width * 1.2))
            label_fontsize = max(8, min(12, fig_width * 1.0))
            tick_fontsize = max(7, min(10, fig_width * 0.8))
            
            ret_str = [str(x) if x % 1 != 0 else str(int(x)) for x in self.sel_ret]

            # Plot observed events
            self.ax1.plot(self.z_obs, np.array(self.data), 'o', mfc='w', mec='k', mew=1.5, label='Observed Events') 
            
            # Plot selected distributions with error handling
            try:
                if self.dist_vars["GEV (Manual)"].get():
                    self.ax1.plot(self.z_gev, self.gev_levels_manual, 'brown', label='GEV Manual')
                if self.dist_vars["GEV (MLE)"].get():
                    self.ax1.plot(self.z_gev, self.gev_levels_scipy, 'r-', label='GEV (MLE)')
                if self.dist_vars["GEV (Lmom)"].get():
                    self.ax1.plot(self.z_gev, self.gev_levels_lmom, 'orange', label='GEV (L-moments)')
                if self.dist_vars["Normal"].get():
                    self.ax1.plot(self.z_gev, self.norm_levels, 'b-', label='Normal')
                if self.dist_vars["Log-Normal"].get():
                    self.ax1.plot(self.z_gev, self.lognorm_levels, 'g-', label='Log-Normal')
                if self.dist_vars["Gumbel"].get():
                    self.ax1.plot(self.z_gev, self.gumbel_levels, 'm-', label='Gumbel')
                if self.dist_vars["Log-Pearson III"].get():
                    self.ax1.plot(self.z_gev, self.logpearson_levels, 'c-', label='Log-Pearson III')
                if self.dist_vars["Gamma"].get():
                    self.ax1.plot(self.z_gev, self.gamma_levels, 'y-', label='Gamma')
            
            except ValueError as e:
                
                if "Locator attempting to generate" in str(e):
                    messagebox.showwarning(
                        "Plotting Warning",
                        f"Skipping visualization for {self.station_name}\n"
                        "Data range too large for automatic tick generation.\n"
                        "Statistical results were still saved to CSV."
                    )
                    return
                else:
                    raise            
            
            # Set dynamic font sizes
            self.ax1.set_xlabel("Return Period (years)", fontsize=label_fontsize)
            self.ax1.set_ylabel("Precipitation (mm)", fontsize=label_fontsize)
            self.ax1.set_title(f"Frequency Plot ({self.station_name})", fontsize=title_fontsize)
            self.ax1.tick_params(axis='both', which='major', labelsize=tick_fontsize)
            self.ax1.legend(loc='upper left', fontsize=max(8, min(12, fig_width * 0.9)))
            self.ax1.grid(True, which="both", linestyle="-", linewidth=0.5, alpha=0.5)
            self.ax1.set_xticks(self.sel_z)
            self.ax1.set_xticklabels(ret_str)
            self.ax1.yaxis.set_major_locator(ticker.MultipleLocator(10))
            self.ax1.yaxis.set_major_locator(ticker.MaxNLocator(10))  # Limit y-axis ticks            
            
            # Set the x-axis label before any other formatting
            #self.add_annotation(self.ax1)
            self.fig1.tight_layout(pad=3.0)

            # Calculate probability labels and scales
            prob_labels = np.array(1/(self.return_periods)*100)
            P_exceedance = np.arange(np.ceil(prob_labels[-1]), np.floor(prob_labels[0]) + 1, 1, dtype=int)/100
            prob_scale = -np.log(-np.log(1 - P_exceedance))
            xscale = prob_scale
            
            # Additional grid lines (only if we have enough points)
            if len(xscale) > 0:
                for xv in xscale:
                    if xv <= max(self.z_gev):  # Only plot if within data range
                        self.ax1.axvline(xv, color='gray', linestyle="-", alpha=0.3, linewidth=0.5, zorder=0)
            
            # Set conservative axis limits to prevent tick errors
            try:
                all_values = np.concatenate([
                    np.array(self.data),
                    self.gev_levels_scipy if self.dist_vars["GEV (MLE)"].get() else [],
                    self.gev_levels_lmom if self.dist_vars["GEV (Lmom)"].get() else [],
                    self.norm_levels if self.dist_vars["Normal"].get() else [],
                    self.lognorm_levels if self.dist_vars["Log-Normal"].get() else [],
                    self.gumbel_levels if self.dist_vars["Gumbel"].get() else [],
                    self.logpearson_levels if self.dist_vars["Log-Pearson III"].get() else [],
                    self.gamma_levels if (self.dist_vars["Gamma"].get() and hasattr(self, 'gamma_levels')) else []
                ])
                y_max = min(1000, np.max(all_values) * 1.1)  # More conservative max limit
                #self.ax1.set_ylim(0, y_max)
                self.ax1.set_ylim(0, 300)
            except:
                self.ax1.set_ylim(0, 1000)  # Fallback limit
            
            self.ensure_output_dir()
            output_path = os.path.join(self.output_dir, "VRain_Distribution-plot_" + self.station_name + ".png")

            # Backup ukuran GUI
            orig_size = self.fig1.get_size_inches()
            self.fig1.set_size_inches(8, 12)
            self.fig1.savefig(output_path, dpi=300, bbox_inches="tight")
            self.fig1.set_size_inches(orig_size)
            self.canvas1.draw()
            
        except Exception as e:
            # messagebox.showerror(
            #     "Plotting Error",
            #     f"Failed to generate plot for {self.station_name}:\n{str(e)}\n"
            #     "Statistical results were still saved to CSV.")
            self.log_error(f"Plot failed for {self.station_name}", e)
            
    def plot_histogram_pdf(self): 
        if self.data is None:
            print("Error: No data to plot!")  # Debug
            return

        self.ax2.clear()  # clear sebelum redraw
        self.canvas2_widget.grid()  # tampilkan canvas1
        self.ax2.clear()
        
        fig_width, fig_height = self.fig2.get_size_inches()
        title_fontsize = max(10, min(16, fig_width * 1.2))
        label_fontsize = max(8, min(12, fig_width * 1.0))
        tick_fontsize = max(7, min(10, fig_width * 0.8))
        # Clear previous figure
    
        step = 5  # Bin width for histogram
        # Histogram (Compute actual frequency counts)
        bin_edges = np.arange(self.data.min(), self.data.max() + step, step)
        hist_counts, bins, _ = self.ax2.hist(
            self.data, bins=bin_edges, density=False, 
            alpha=0.6, color='b', label='Data Frequency'
        )
    
        # X-axis range
        xmin, xmax = self.ax2.get_xlim()
        x = np.linspace(xmin, xmax, 200)
    
        # Scale PDF curves to match histogram frequencies
        total_count = sum(hist_counts)
        bin_width = bins[1] - bins[0]
    
        # Plot selected distributions based on checkbox states
        if self.dist_vars["Normal"].get():
            pdf_norm = stats.norm.pdf(x, *self.norm_params) * total_count * bin_width
            self.ax2.plot(x, pdf_norm, 'b', label='Normal')
        
        if self.dist_vars["Log-Normal"].get():
            pdf_lognorm = stats.lognorm.pdf(x, *self.lognorm_params) * total_count * bin_width
            self.ax2.plot(x, pdf_lognorm, 'g', label='Log-Normal')
        
        if self.dist_vars["Gumbel"].get():
            pdf_gumbel = stats.gumbel_r.pdf(x, *self.gumbel_params) * total_count * bin_width
            self.ax2.plot(x, pdf_gumbel, 'm', label='Gumbel')
        
        if self.dist_vars["Log-Pearson III"].get():
            pdf_lp3 = stats.pearson3.pdf(x, *self.logpearson_params) * total_count * bin_width
            self.ax2.plot(x, pdf_lp3, 'c', label='Log-Pearson III')
        
        if self.dist_vars["GEV (MLE)"].get():
            pdf_gev_scipy = stats.genextreme.pdf(x, *self.gev_params_scipy) * total_count * bin_width
            self.ax2.plot(x, pdf_gev_scipy, 'r', label='GEV (MLE)')
        
        if self.dist_vars["Gamma"].get() and hasattr(self, 'gamma_params'):
            pdf_gamma = stats.gamma.pdf(x, *self.gamma_params) * total_count * bin_width
            self.ax2.plot(x, pdf_gamma, 'y', label='Gamma')
        
        if self.dist_vars["GEV (Lmom)"].get():
            pdf_gev_lmom = stats.genextreme.pdf(
                x,
                self.gev_params_lmom['c'],
                self.gev_params_lmom['loc'],
                self.gev_params_lmom['scale']
            ) * total_count * bin_width
            self.ax2.plot(x, pdf_gev_lmom, 'orange', label='GEV (L-moments)')
        
        if self.dist_vars["GEV (Manual)"].get():
            pdf_gev_manual = stats.genextreme.pdf(x, *self.gev_params_manual) * total_count * bin_width
            self.ax2.plot(x, pdf_gev_manual, 'brown', label='GEV (Manual)')
    
        # Formatting the plot
        self.ax2.set_title("Histogram with PDF", fontsize=title_fontsize)
        self.ax2.set_xlabel("Rainfall (mm)", fontsize=label_fontsize)
        self.ax2.set_ylabel("Frequency", fontsize=label_fontsize)
        self.ax2.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        self.ax2.legend(fontsize=max(8, min(12, fig_width * 0.9)))
        self.ax2.grid(True, linestyle='--', alpha=0.6)
        self.fig2.tight_layout(pad=3.0)
        
        output_path = os.path.join(self.output_dir, f"VRain_Histogram-plot_{self.station_name}.png")
        self.canvas2.draw()

    def convert_values(self):
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

    def ensure_output_dir(self):
        """Ensure output directory exists, create if it doesn't"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        return self.output_dir

    def browse_output_dir(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            # Still create VRain-results subfolder, but in user-selected directory
            self.output_dir = os.path.join(folder_selected, "VRain-results")
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            messagebox.showinfo("Output Directory", f"Files will now be saved to:\n{self.output_dir}")

    def load_files(self):
        if self.check_multiple.get():
            # Select folder containing files
            folder_path = filedialog.askdirectory()
            if folder_path:
                # Create VRain-results subfolder in the input directory
                self.output_dir = os.path.join(folder_path, "VRain-results")
                if not os.path.exists(self.output_dir):
                    os.makedirs(self.output_dir)
                
                # Get both CSV and XLSX files
                csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
                xlsx_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
                self.file_paths = csv_files + xlsx_files
                self.merge_files()
        else:
            file_path = filedialog.askopenfilename(filetypes=[("CSV & Excel Files", "*.csv;*.xlsx"), ("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")])
            if file_path:
                # Create VRain-results subfolder in the input file's directory
                input_dir = os.path.dirname(file_path)
                self.output_dir = os.path.join(input_dir, "VRain-results")
                if not os.path.exists(self.output_dir):
                    os.makedirs(self.output_dir)
                
                self.file_paths = [file_path]
                self.load_single_file()
                messagebox.showinfo("Output Directory", f"Results will be saved to:\n{self.output_dir}")
    
    def merge_files(self):
        """
        Merge all columns from multiple CSV/XLSX files by stacking them horizontally (column by column),
        ignoring the index. Column names follow the pattern: 'filename-column_name'.
        """
        
        self.ensure_output_dir()
        dataframes = []

        for file in self.file_paths:
            filename = os.path.splitext(os.path.basename(file))[0]  # Get filename without extension
            
            if file.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.endswith(".xlsx"):
                df = pd.read_excel(file, engine='openpyxl')
                
            else:
                continue  # Skip unsupported files
    
            # Rename columns using pattern: filename-column_name
            df.columns = [f"{filename}-{col}" for col in df.columns]
    
            # Reset index to ensure no misalignment in concatenation
            df = df.reset_index(drop=True)
            dataframes.append(df)
    
        if dataframes:
            # Concatenate all DataFrames horizontally (column by column)
            merged_df = pd.concat(dataframes, axis=1, ignore_index=False)
            self.dfs = merged_df  # Store in class attribute
            # Update dropdown values
            self.combo_column["values"] = list(self.dfs.columns)
            self.combo_column.set(self.dfs.columns[-1])  # Set default value
            
            output_file = os.path.join(self.output_dir, "VRain_merged_stations.csv")
            merged_df.to_csv(output_file, index=False)
            messagebox.showinfo("Batch Run", f"Merged file saved to: \n\n{output_file}")
            
    def load_single_file(self):
        if self.file_paths:
            file = self.file_paths[0]
            try:
                if file.endswith(".csv"):
                    self.dfs = pd.read_csv(file)
                elif file.endswith(".xlsx"):
                    self.dfs = pd.read_excel(file, engine='openpyxl')
                messagebox.showinfo("File read",  "Your file has been successfully loaded. Time to work some magic with VRain! ✨")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {e}")
        self.combo_column["values"] = list(self.dfs.columns)
        self.combo_column.set(self.dfs.columns[-1])  # Set default value
        
    
    def toggle_batch_mode(self):
        if self.check_multiple.get():
            self.btn_browse.config(text="Browse (Folder)")
            # Nonaktifkan button "Run Frequency Analysis" saat batch mode aktif
            self.btn_run.config(state="disabled")
        else:
            self.btn_browse.config(text="Browse (File CSV or XLSX)")
            # Aktifkan kembali button "Run Frequency Analysis" saat batch mode nonaktif
            self.btn_run.config(state="normal")
        
        # Hide progress bar when toggling modes
        self.progress_frame.grid_remove()

    def perform_stats(self, column=None, method=None):
        """Calculate probability positions for the given column and method"""
        if column is None:
            column = self.combo_column.get()
        if method is None:
            method = self.combo_method.get()
        
        if self.dfs is None:
            return False
            
        if not column or column not in self.dfs.columns:
            return False
            
        if not method:
            return False
            
        self.data = np.sort(self.dfs[column].dropna())
        self.station_name = column
        
        n = len(self.data)
        self.prob_return_obs = self._calculate_probability_positions(method, n)
        self.calculate_statistics()
        return True

    def batch_run(self):
        if self.dfs is None:
            messagebox.showerror("Error", "No file loaded")
            return
            
        method = self.combo_method.get()
        if not method:
            messagebox.showerror("Error", "Please select a method")
            return
            
        # Get all columns to process
        columns = list(self.dfs.columns)
        total_columns = len(columns)
        failed_columns = []
        
        # Show progress bar
        self.progress_frame.grid()
        self.progress_bar['maximum'] = total_columns
        self.progress_bar['value'] = 0
        self.progress_percent['text'] = "0%"
        self.root.update_idletasks()
    
        # Store all results
        all_results = []
        
        for i, column in enumerate(columns, 1):
            try:
                # Perform complete analysis including statistics
                self.perform_anfreq(column)
                
                # Store results if needed
                all_results.append({
                    'station': self.station_name,
                    'stats': self.stats_df,
                    'test_results': self.results_stat,
                    'return_levels': self.results_df
                })
                
                # Update progress
                self.progress_bar['value'] = i
                percent_complete = int((i / total_columns) * 100)
                self.progress_percent['text'] = f"{percent_complete}%"
                self.root.update_idletasks()
                
            except Exception as e:
                failed_columns.append((column, str(e)))
                continue
        
        # Hide progress bar
        self.progress_frame.grid_remove()
        
        # Show summary
        if failed_columns:
            error_message = "\n".join([f"{col[0]}: {col[1]}" for col in failed_columns])
            messagebox.showwarning("Completed with Errors",
                                 f"Processed {total_columns - len(failed_columns)}/{total_columns} columns\n\n"
                                 f"Errors:\n{error_message}")
        else:
            messagebox.showinfo("Success", f"Successfully processed {total_columns} columns")
        
        # Auto-concatenate results
        if not self.batch_confirm.get():
            self.concatenate_outputs()
                
    def concatenate_outputs(self):
        """Concatenate all CSV files with the same pattern in the output directory"""
        try:
            self.ensure_output_dir()
            output_dir = self.output_dir
            generated_files = []
            
            # Define patterns and corresponding output files
            patterns = [
                ("VRain_stat-test_*.csv", "VRain_ALL_stat-tests_combined.csv", "VRain_stat-test_"),
                ("VRain_return-level_*.csv", "VRain_ALL_return-levels_combined.csv", "VRain_return-level_"),
                ("VRain_stat_*.csv", "VRain_ALL_basic-stats_combined.csv", "VRain_stat_")
            ]
            
            for pattern, output_file, prefix in patterns:
                file_list = glob.glob(os.path.join(output_dir, pattern))
                if not file_list:
                    continue
                    
                # Process files in parallel using ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Create list of futures for parallel processing
                    futures = []
                    for f in file_list:
                        futures.append(executor.submit(self._process_single_file,f,prefix))
                    
                    # Collect results as they complete
                    dfs = []
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            dfs.append(future.result())
                        except Exception as e:
                            print(f"Error processing file: {e}")
                            continue
                
                if dfs:
                    # Concatenate all DataFrames at once (more efficient than incremental)
                    combined_df = pd.concat(dfs, ignore_index=True)
                    
                    # Optimized writing with compression
                    output_path = os.path.join(output_dir, output_file)
                    combined_df.to_csv(output_path,index=False,
                                       compression='gzip' if output_path.endswith('.gz') else None)
                    generated_files.append(output_file)
                    
                    #Clean up individual files if desired (uncomment if needed)
                    for f in file_list:
                        try: os.remove(f)
                        except OSError: pass
    
            if generated_files:
                message = "Successfully created merged files:\n\n" + \
                         "\n".join(f"• {f}" for f in generated_files) + \
                         f"\n\nSaved to: {output_dir}"
                messagebox.showinfo("Concatenation Complete", message)
            else:
                messagebox.showinfo("No Files Found", "No matching CSV files were found to concatenate.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to concatenate files:\n{str(e)}")

    def _process_single_file(self, file_path, prefix):
        """Helper method to process a single file (used in parallel processing)"""
        df = pd.read_csv(file_path)
        filename = os.path.splitext(os.path.basename(file_path))[0]
        station_name = filename.replace(prefix, "")
        df['Source_File'] = station_name
        return df    
    
    def _calculate_probability_positions(self, method, n):
        """Calculate probability positions based on the selected method"""
        if method == "Weibull":
            return np.array([(i + 1) / (n + 1) for i in range(n)])
        elif method == "Cunnane":
            return np.array([(i + 0.4) / (n + 0.2) for i in range(n)])
        elif method == "Hazen":
            return np.array([(i + 0.5) / n for i in range(n)])
        elif method == "Gringorten":
            return np.array([(i + 0.44) / (n + 0.12) for i in range(n)])
        elif method == "Blom":
            return np.array([(i + 0.375) / (n + 0.25) for i in range(n)])
        elif method == "Tukey":
            return np.array([(i + 1/3) / (n + 1/3) for i in range(n)])
        else:
            raise ValueError("Invalid method")

    def perform_anfreq(self, column=None):
        """Perform complete frequency analysis including statistics."""
        
        if self.dfs is None:
            messagebox.showerror("Error", "No file loaded")
            return False
    
        method = self.combo_method.get()
        if not method:
            messagebox.showerror("Error", "Please select a method")
            return False
    
        # Determine if this is a batch run
        is_batch = column is None and self.check_multiple.get()
    
        # --- 🧹 Clean zeros before analysis ---
        # Replace all 0 values in numeric columns with NaN to avoid fitting/log errors
        self.dfs = self.dfs.apply(
            lambda col: col.replace(0, np.nan) if np.issubdtype(col.dtype, np.number) else col
        )
    
        if is_batch:
            # Batch run - process all columns
            columns = list(self.dfs.columns)
            success_count = 0
    
            for col in columns:
                try:
                    if self._process_single_column(col, method):
                        success_count += 1
                except Exception as e:
                    self.log_error(f"Failed to process column {col}", e)
                    continue
    
            messagebox.showinfo(
                "Batch Complete",
                f"Processed {success_count}/{len(columns)} columns successfully"
            )
            return success_count > 0
    
        else:
            # Single run
            column = column or self.combo_column.get()
            if not column or column not in self.dfs.columns:
                messagebox.showerror("Error", "Please select a valid column")
                return False
    
            try:
                # --- 🧹 Clean zeros in that column only ---
                if np.issubdtype(self.dfs[column].dtype, np.number):
                    self.dfs[column] = self.dfs[column].replace(0, np.nan)
    
                return self._process_single_column(column, method)
            except Exception as e:
                self.log_error(f"Failed to process column {column}", e)
                return False    


    def _process_single_column(self, column, method):
        """Process a single column for frequency analysis"""
        # Reuse perform_stats for the common functionality
        if not self.perform_stats(column, method):
            return False
        
        # Continue with frequency analysis specific steps
        self.num_bins = self.optimal_bins()
        self.fit_distributions()
        self.compute_return_levels()
        self.perform_stat_tests()
        self.compute_critical_values()
        self.create_result_dfs()
        
        # Generate plots
        self.plot_histogram_pdf()
        self.plot_frequency_analysis()
        
        return True

    def calculate_statistics(self):
        if self.data is None or len(self.data) == 0:
            return
            
        min_val = np.min(self.data)
        max_val = np.max(self.data)
        median_val = np.median(self.data)
        sample_size = len(self.data)
        mean_val = np.mean(self.data)
        std_dev = np.std(self.data, ddof=1)
        skew_val = stats.skew(self.data)
        kurtosis_val = stats.kurtosis(self.data, fisher=False)
        
        # Create and save stats dataframe
        self.stats_df = pd.DataFrame({
            "Station": [self.station_name],
            "Min": [min_val],
            "Max": [max_val], 
            "Median": [median_val],
            "Sample Size": [sample_size],
            "Mean": [mean_val],
            "St Dev": [std_dev],
            "Skew": [skew_val],
            "Kurtosis": [kurtosis_val]
        })
        
        self.ensure_output_dir()
        output_path = os.path.join(self.output_dir, f"VRain_stat_{self.station_name}.csv")
        self.stats_df.to_csv(output_path, index=False)


    def show_license(self):
        license_window = tk.Toplevel()
        license_window.title("Software License Agreement")
        license_window.geometry("600x400")

        license_text = """Frequency Analysis Program (VRainFreq) v.1\n
        Software License Agreement \n
        Copyright (c) 2025 Vempi Satriya Adi Hendrawan\n
        \n
        Permission is granted to use this software for education or commercial purposes.\n
        Izin diberikan untuk menggunakan perangkat lunak ini untuk keperluan edukasi atau komersial.\n
        \n
        Restrictions:\n
        - You may not distribute, modify, or sell this software without permission.\n
        - Anda tidak boleh mendistribusikan, memodifikasi, atau menjual perangkat lunak ini tanpa izin.\n
        \n
        Disclaimer:\n
        This software is provided "as is" without warranties. The developer is not responsible for any damages.\n
        Perangkat lunak ini disediakan "sebagaimana adanya" tanpa jaminan. Pengembang tidak bertanggung jawab atas kerusakan apa pun.\n
        \n
        For enquiries, contact:\n
        \n
        vempi@ugm.ac.id | vempi.staff.ugm.ac.id"""
        
        text_widget = tk.Text(license_window, wrap="word", width=70, height=20)
        text_widget.insert("1.0", license_text)

        text_widget.config(state="disabled")  # Supaya tidak bisa diedit
        text_widget.pack(padx=10, pady=10, fill="both", expand=True)

        tk.Button(license_window, text="OK", command=license_window.destroy).pack(pady=10)
    
if __name__ == "__main__":
    root = tk.Tk()
    app = FrequencyAnalysisApp(root)
    root.mainloop()
