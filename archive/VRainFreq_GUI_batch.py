import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import scipy.stats as stats
import matplotlib.ticker as ticker
import glob, os

class FrequencyAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VRain | Frequency Analysis Tool (VRainFreq) v.1")
        #self.root.attributes('-fullscreen', True)  # Set full screen
        self.root.state('zoomed')  # Maximized window (Windows)

        self.file_paths = []
        self.data = None
        self.dfs = None
        self.output_dir = os.getcwd()  # Default: current directory

        # Menu Bar
        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)
        
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.load_files)
        #file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="License", command=self.show_license)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        # Main Frames
        frame_left = tk.Frame(root)
        frame_left.grid(row=0, column=0, sticky="ns")
        
        frame_right = tk.Frame(root)
        frame_right.grid(row=0, column=1, sticky="nsew")
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)
        
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
        
        tk.Button(frame_left, text="Set Column & Calculate Statistics", command=self.perform_stats).grid(row=4, column=0, columnspan=2, pady=5)
        
        # Table for statistics
        self.tree_stats = ttk.Treeview(frame_left, columns=("Metric", "Value"), 
                                       show="headings", height=8)
        self.tree_stats.heading("Metric", text="Metric")
        self.tree_stats.heading("Value", text="Value")
        self.tree_stats.grid(row=5, column=0, columnspan=2, pady=5, sticky="ew")
        
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
        
        # Matplotlib Frame
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=frame_right)
        self.canvas2_widget = self.canvas2.get_tk_widget()
        self.canvas2_widget.pack(fill="both", expand=True)
        self.canvas2_widget.pack_forget()  # Sembunyikan canvas
        
        self.fig1, self.ax1 = plt.subplots()
        #self.ax11 = self.ax1.twiny()
        #self.ax11.set_xticks([]); self.ax11.set_xticklabels([])
        #self.ax11.set_visible(False)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=frame_right)
        self.canvas1_widget = self.canvas1.get_tk_widget()
        self.canvas1_widget.pack(fill="both", expand=True)
        self.canvas1_widget.pack_forget()  # Sembunyikan canvas
        
    def optimal_bins(self):
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
        alpha = float(self.alpha.get())
        self.gev_levels = stats.genextreme.ppf(1 - self.prob_return, *self.gev_params)
        self.norm_levels = stats.norm.ppf(1 - self.prob_return, *self.norm_params)
        self.lognorm_levels = stats.lognorm.ppf(1 - self.prob_return, *self.lognorm_params)
        self.gumbel_levels = stats.gumbel_r.ppf(1 - self.prob_return, *self.gumbel_params)
        self.logpearson_levels = np.exp(stats.pearson3.ppf(1 - self.prob_return, *self.logpearson_params))
        
        shape, loc, scale = self.gev_params
        
        self.gev_conf_low = stats.genextreme.ppf((1 - self.prob_return)-alpha/2, shape, loc, scale)
        self.gev_conf_high = stats.genextreme.ppf((1 - self.prob_return)+alpha/2, shape, loc, scale)

        
    def perform_stat_tests(self):
        self.ks_results = {
            "GEV": stats.kstest(self.data, 'genextreme', args=self.gev_params),
            "Normal": stats.kstest(self.data, 'norm', args=self.norm_params),
            "Log-Normal": stats.kstest(self.data, 'lognorm', args=self.lognorm_params),
            "Gumbel": stats.kstest(self.data, 'gumbel_r', args=self.gumbel_params),
            "Log-Pearson III": stats.kstest(np.log(self.data), 'pearson3', args=self.logpearson_params)
        }
        
        self.lst_params = {"GEV": self.gev_params,"Normal": self.norm_params,"Log-Normal": self.lognorm_params,
                           "Gumbel": self.gumbel_params,"Log-Pearson III": self.logpearson_params}

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
        # self.param_str = pd.DataFrame({"Normal": f"Mean={self.lst_params['Normal'][0]:.3f}, StDv={self.lst_params['Normal'][1]:.3f}",
        #                                 "Log-Normal": f"MeanLog={np.log(self.lst_params['Log-Normal'][2]):.3f}, StDvLog={self.lst_params['Log-Normal'][0]:.3f}",
        #                                 "Gumbel": f"Loctn={self.lst_params['Gumbel'][0]:.3f}, Scale={self.lst_params['Gumbel'][1]:.3f}",
        #                                 "Log-Pearson III": f"MeanLog={np.log(self.lst_params['Log-Pearson III'][1]):.3f}, StDvLog={self.lst_params['Log-Pearson III'][2]:.3f}",
        #                                 "GEV": f"Loctn={self.lst_params['GEV'][1]:.3f}, Scale={self.lst_params['GEV'][2]:.3f}, Shape={self.lst_params['GEV'][0]:.3f}"},index=0)
    
        self.results_stat = pd.DataFrame({
            "Distribution": list(self.ks_results.keys()),
            "Chi-square": [self.chi_square[name].statistic for name in self.ks_results.keys()],
            "Chi crit": [self.chi_critical] * len(self.ks_results),
            "Chi Result": ["Accepted" if self.chi_square[name].statistic < self.chi_critical else "Rejected" for name in self.ks_results.keys()],
            "Chi-Square p-value": [res.pvalue for res in self.chi_square.values()],
            "Delta KS max": [self.ks_results[name].statistic for name in self.ks_results.keys()],
            "Delta KS crit": [self.ks_critical] * len(self.ks_results),
            "KS Result": ["Accepted" if self.ks_results[name].statistic < self.ks_critical else "Rejected" for name in self.ks_results.keys()],
            "Parameters": [
                f"Mean={self.lst_params['Normal'][0]:.3f}, StDv={self.e['Normal'][1]:.3f}" if name == "Normal" else
                f"MeanLog={np.log(self.lst_params['Log-Normal'][2]):.3f}, StDvLog={self.lst_params['Log-Normal'][0]:.3f}" if name == "Log-Normal" else
                f"Loctn={self.lst_params['Gumbel'][0]:.3f}, Scale={self.lst_params['Gumbel'][1]:.3f}" if name == "Gumbel" else
                f"MeanLog={np.log(self.lst_params['Log-Pearson III'][1]):.3f}, StDvLog={self.lst_params['Log-Pearson III'][2]:.3f}" if name == "Log-Pearson III" else
                f"Loctn={self.lst_params['GEV'][1]:.3f}, Scale={self.lst_params['GEV'][2]:.3f}, Shape={self.lst_params['GEV'][0]:.3f}" if name == "GEV" else
                "N/A"
                for name in self.ks_results.keys()],
            "ID": self.station_name
            })

        
        self.results_df = pd.DataFrame({
            "Return period": self.return_periods,
            "Probability": self.prob_return,
            "Normal": self.norm_levels,
            "Log-Normal": self.lognorm_levels,
            "Gumbel": self.gumbel_levels,
            "Log-Pearson III": self.logpearson_levels,
            "GEV": self.gev_levels
        })
        
        # Save each DataFrame as a CSV file
        #self.param_str.to_csv(os.path.join(self.output_dir, "VRain_params_"+self.station_name+".csv"), index=False)
        self.results_stat.to_csv(os.path.join(self.output_dir, "VRain_stat-test_"+self.station_name+".csv"), index=False)
        self.results_df.to_csv(os.path.join(self.output_dir, "VRain_return-level_"+self.station_name+".csv"), index=False)
    
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
        mu, epsilon, R = self.gev_params  # Unpack parameters
        param_text = "GEV parameters\n"  # Title
        param_text += f"μ = {mu:.3f}  ∈ = {epsilon:.3f}  R = {R:.3f}\n\n"
        param_text += f"Note: Horizontal axis is scaled\nusing Gumbel (EV I) reduced variate"        
        
        ax.text(0.65, 0.05, param_text, transform=ax.transAxes, fontsize=10, 
                ha='left', va='bottom', bbox=dict(facecolor='white', alpha=0.5))
    
    def plot_frequency_analysis(self): 
        self.compute_reduced_variate()
        prob_labels = np.array(1/(self.return_periods)*100)
        P_exceedance = np.arange(np.ceil(prob_labels[-1]), np.floor(prob_labels[0]) + 1, 1, dtype=int)/100
        prob_scale = -np.log(-np.log(1 - P_exceedance))
        xscale = prob_scale
        
        self.canvas1_widget.pack(fill="both", expand=True)
        self.ax1.clear()
        self.ax1.plot(self.z_obs, np.array(self.data), 'o', mfc='w', mec='k', mew=1.5, label='Observed Events')
        self.ax1.plot(self.z_gev, self.gev_levels, 'r-', label='GEV')
        self.ax1.plot(self.z_gev, self.norm_levels, 'b-', label='Normal')
        self.ax1.plot(self.z_gev, self.lognorm_levels, 'g-', label='Log-Normal')
        self.ax1.plot(self.z_gev, self.gumbel_levels, 'm-', label='Gumbel')
        self.ax1.plot(self.z_gev, self.logpearson_levels, 'c-', label='Log-Pearson III')
        alpha = f"{1-float(self.alpha.get()):.0%}"
        self.ax1.fill_between(self.z_gev, self.gev_conf_low, self.gev_conf_high, color='gray', alpha=0.3, label='GEV '+alpha+' CI')
    
        self.ax1.set_xlabel("Return Period (years)")
        self.add_annotation(self.ax1)

        self.ax1.set_xticks(self.sel_z)
        ret_str = [str(x) if x % 1 != 0 else str(int(x)) for x in self.sel_ret]
        self.ax1.set_xticklabels(ret_str)
        self.ax1.set_ylabel("Precipitation (mm)")
        self.ax1.yaxis.set_major_locator(ticker.MultipleLocator(10))
        self.ax1.set_title(f"Frequency Plot ({self.station_name})")
        self.ax1.legend(loc='upper left')
        self.ax1.grid(True, which="both", linestyle="-", linewidth=1, alpha=0.5)
    
        for xv in xscale:
            self.ax1.axvline(xv, color='gray', linestyle="-", alpha=0.3, linewidth=0.5, zorder=0)
        
        output_path = self.output_dir,"VRain_Distribution-plot_"+self.station_name+".png"
        self.canvas1.draw()

        #self.fig1.savefig(output_path, dpi=300, bbox_inches="tight")

        # Only create ax11 once, and do not clear it later
        #if not hasattr(self, "ax11"):  # Create only if it doesn't exist
            #self.ax11 = self.ax1.twiny()
    
        # self.ax11.set_xlim(self.ax1.get_xlim())  # Ensure the same limits
        # self.ax11.set_xlabel("Probability of Exceedance (%)")
        # self.ax11.set_xticks(self.z_gev)
        # self.ax11.set_xticklabels([f"{p:.1f}%" for p in prob_labels])\
    
    def plot_histogram_pdf(self): 
        # Clear previous figure
        self.canvas2_widget.pack(fill="both", expand=True)
        self.ax2.clear()
    
        step = 5  # Bin width for histogram
        # Histogram (Compute actual frequency counts)
        bin_edges = np.arange(self.data.min(), self.data.max() + step, step)
        hist_counts, bins, _ = self.ax2.hist(self.data, bins=bin_edges, density=False, 
                                             alpha=0.6, color='b', label='Data Frequency')
        # X-axis range
        xmin, xmax = self.ax2.get_xlim()
        x = np.linspace(xmin, xmax, 100)
    
        # Define distributions and their corresponding colors
        distributions = {
            "Normal": (stats.norm, 'b'),
            "Log-Normal": (stats.lognorm, 'g'),
            "Gumbel": (stats.gumbel_r, 'm'),
            "GEV": (stats.genextreme, 'r'),
            "Log-Pearson III": (stats.pearson3, 'c')
        }
    
        # Scale PDF curves to match histogram frequencies
        total_count = sum(hist_counts)
        bin_width = bins[1] - bins[0]
    
        # Fit distributions and plot their PDFs (scaled to frequency)
        for name, (dist, color) in distributions.items():
            params = dist.fit(self.data)
            pdf_fitted = dist.pdf(x, *params) * total_count * bin_width  # Scale density to match frequency
            self.ax2.plot(x, pdf_fitted, color=color, label=f'{name}')
    
        # Formatting the plot
        self.ax2.set_title("Histogram with PDF")
        self.ax2.set_xlabel("Rainfall (mm)")
        self.ax2.set_ylabel("Frequency")  
        self.ax2.legend()
        self.ax2.grid(True, linestyle='--', alpha=0.6)
        
        output_path = self.output_dir, "VRain_Histogram-plot_" + self.station_name + ".png"
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
    
    
    def browse_output_dir(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_dir = folder_selected

    def load_files(self):
        if self.check_multiple.get():
            # Select folder containing files
            folder_path = filedialog.askdirectory()
            if folder_path:
                # Get both CSV and XLSX files
                csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
                xlsx_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
                self.file_paths = csv_files + xlsx_files  # Combine both file lists
                self.output_dir = folder_path
                self.merge_files()  # Updated method to merge both types
        else:
            file_path = filedialog.askopenfilename(filetypes=[("CSV & Excel Files", "*.csv;*.xlsx"), ("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")])
            self.file_paths = [file_path] if file_path else []
            folder_path = os.path.dirname(file_path) if file_path else ""
            self.output_dir = folder_path
            self.load_single_file()  # Updated method to handle both file types
    
    def merge_files(self):
        """
        Merge all columns from multiple CSV/XLSX files by stacking them horizontally (column by column),
        ignoring the index. Column names follow the pattern: 'filename-column_name'.
        """
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
            messagebox.showinfo("Batch Run", f"Merged file saved to: \n\n{output_file}\n\nIt is recommended to check and validate first the output file before use it as input of this program (as a single CSV)")
        
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
        else:
            self.btn_browse.config(text="Browse (File CSV or XLSX)")

    def perform_stats(self):
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
        self.station_name = column
        
        n = len(self.data)
        
        if method == "Weibull":
            self.prob_return_obs = np.array([(i + 1) / (n + 1) for i in range(n)])
        elif method == "Cunnane":
            self.prob_return_obs = np.array([(i + 0.4) / (n + 0.2) for i in range(n)])
        elif method == "Hazen":
            self.prob_return_obs = np.array([(i + 0.5) / n for i in range(n)])
        elif method == "Gringorten":
            self.prob_return_obs = np.array([(i + 0.44) / (n + 0.12) for i in range(n)])
        elif method == "Blom":
            self.prob_return_obs = np.array([(i + 0.375) / (n + 0.25) for i in range(n)])
        elif method == "Tukey":
            self.prob_return_obs = np.array([(i + 1/3) / (n + 1/3) for i in range(n)])
        else:
            raise ValueError("Invalid method. Choose from: Weibull, Cunnane, Hazen, Gringorten, Blom, Tukey")
    
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
            self.station_name = column

            self.num_bins = self.optimal_bins()
            self.fit_distributions()
            self.compute_return_levels()
            self.perform_stat_tests()
            self.compute_critical_values()
            self.create_result_dfs()
            
            self.plot_histogram_pdf()
            try:
                self.plot_frequency_analysis()
                messagebox.showinfo("Batch Run", f"Analysis completed and file saved for \n**{column}**\nContinue to the next data? ")
            except MemoryError:
                messagebox.showerror("Warning", f"There is a problem in fitting a Distribution for:\n\n**{column}**")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")


    def perform_anfreq(self):
        self.num_bins = self.optimal_bins()
        self.fit_distributions()
        self.compute_return_levels()
        self.perform_stat_tests()
        self.compute_critical_values()
        self.create_result_dfs()
        
        if self.dfs is None:
            messagebox.showerror("Error", "No file loaded")
            return
        
        column = self.combo_column.get()
        method = self.combo_method.get()
        
        self.station_name = column
        
        if not column or column not in self.dfs.columns:
            messagebox.showerror("Error", "Please select a valid column")
            return
        
        if not method:
            messagebox.showerror("Error", "Please select a method")
            return
    
        self.plot_histogram_pdf()
        try:
            self.plot_frequency_analysis()
        except MemoryError:
            messagebox.showerror("Warning", "There is a problem in fitting a Distribution")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")

    def calculate_statistics(self):
        min_val = np.min(self.data)
        max_val = np.max(self.data)
        median_val = np.median(self.data)
        
        #mode_result = stats.mode(self.data, keepdims=True)
        #mode_val = mode_result.mode[0] if mode_result.count[0] > 0 else "No Mode"
    
        sample_size = len(self.data)
        mean_val = np.mean(self.data)
        std_dev = np.std(self.data, ddof=1)
        skew_val = stats.skew(self.data)
        kurtosis_val = stats.kurtosis(self.data, fisher=False)
    
        self.tree_stats.delete(*self.tree_stats.get_children())
    
        self.tree_stats.insert("", "end", values=("Mean", round(mean_val, 4)))
        self.tree_stats.insert("", "end", values=("Median", round(median_val, 4)))
        self.tree_stats.insert("", "end", values=("Min", round(min_val, 4)))
        self.tree_stats.insert("", "end", values=("Max", round(max_val, 4)))
        self.tree_stats.insert("", "end", values=("Standard Deviation", round(std_dev, 4)))
        self.tree_stats.insert("", "end", values=("Sample Size", sample_size))
        self.tree_stats.insert("", "end", values=("Skewness", round(skew_val, 4)))
        self.tree_stats.insert("", "end", values=("Kurtosis", round(kurtosis_val, 4)))
        
        self.stats_df = pd.DataFrame({"Metric": ["Min", "Max", "Median", "Sample Size", "Mean", "St Dev", "Skew", "Kurtosis"],
                                      "Value": [min_val, max_val, median_val, sample_size, mean_val, std_dev, skew_val, kurtosis_val]})
        
        self.stats_df.to_csv(os.path.join(self.output_dir,"VRain_stat_"+self.station_name+".csv"), index=False)

    def show_plot(self):
        self.canvas1_widget.pack(fill="both", expand=True)
        self.ax1.clear()
        self.ax1.plot(self.prob_return_obs, self.data, marker="o", linestyle="-")
        self.ax1.set_xlabel("Plotting Position")
        self.ax1.set_ylabel("Value")
        self.ax1.set_title("Empirical Probability Plot")
        self.ax1.grid(True)
        for i, txt in enumerate(self.prob_return_obs):
            self.ax1.annotate(round(txt, 2), (self.prob_return_obs[i], self.data[i]))
        self.canvas1.draw()

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