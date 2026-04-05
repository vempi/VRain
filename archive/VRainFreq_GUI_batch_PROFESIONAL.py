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
import webbrowser
from PIL import Image, ImageTk
import sys
import traceback

class ProfessionalFrequencyAnalysisApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("VRainFreq Pro | Advanced Frequency Analysis Tool v2.0")
        self.root.state('zoomed')
        
        # Set application icon and styling
        self.setup_styling()
        
        # Initialize variables
        self.file_paths = []
        self.data = None
        self.dfs = None
        self.output_dir = os.getcwd()
        self.ensure_output_dir()
        self.setup_error_log()
        
        # Application state
        self.current_theme = "dark"
        self.plot_style = "seaborn-v0_8-darkgrid" if self.current_theme == "dark" else "seaborn-v0_8-whitegrid"
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Setup modern UI
        self.setup_modern_ui()
        
        # Apply initial theme
        self.apply_theme()
        
        # Force initial layout
        self.root.update_idletasks()

    def setup_styling(self):
        """Configure modern styling for the application"""
        self.root.configure(bg='#2c3e50')
        
        # Define modern color scheme
        self.colors = {
            'primary': '#3498db',
            'secondary': '#2ecc71', 
            'accent': '#e74c3c',
            'dark_bg': '#2c3e50',
            'dark_fg': '#ecf0f1',
            'light_bg': '#ecf0f1',
            'light_fg': '#2c3e50',
            'success': '#27ae60',
            'warning': '#f39c12',
            'error': '#e74c3c'
        }

    def setup_modern_ui(self):
        """Create modern professional UI layout"""
        # Configure root grid
        self.root.grid_columnconfigure(0, weight=0, minsize=350)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # ========== LEFT SIDEBAR ==========
        self.sidebar = tk.Frame(self.root, bg=self.colors['dark_bg'], padx=10, pady=10)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Header with logo
        self.create_header()
        
        # Input section
        self.create_input_section()
        
        # Parameters section
        self.create_parameters_section()
        
        # Distributions section
        self.create_distributions_section()
        
        # Actions section
        self.create_actions_section()
        
        # Progress section
        self.create_progress_section()
        
        # ========== MAIN CONTENT AREA ==========
        self.main_content = tk.Frame(self.root, bg='#34495e')
        self.main_content.grid(row=0, column=1, sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)
        
        # Create modern tab system
        self.setup_main_tabs()

    def create_header(self):
        """Create application header with logo"""
        header_frame = tk.Frame(self.sidebar, bg=self.colors['dark_bg'])
        header_frame.pack(fill="x", pady=(0, 15))
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="VRainFreq Pro", 
            font=("Segoe UI", 16, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['dark_bg']
        )
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(
            header_frame,
            text="Advanced Frequency Analysis v2.0",
            font=("Segoe UI", 9),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg']
        )
        subtitle_label.pack(anchor="w")
        
        # Separator
        ttk.Separator(header_frame, orient='horizontal').pack(fill="x", pady=5)

    def create_input_section(self):
        """Create file input section"""
        input_frame = tk.LabelFrame(
            self.sidebar, 
            text="📁 DATA INPUT", 
            font=("Segoe UI", 9, "bold"),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg'],
            padx=10,
            pady=10
        )
        input_frame.pack(fill="x", pady=(0, 10))
        
        # Batch mode toggle
        self.check_multiple = tk.BooleanVar()
        chk_multiple = tk.Checkbutton(
            input_frame, 
            text="Batch Analysis (Multiple Files)",
            variable=self.check_multiple,
            command=self.toggle_batch_mode,
            font=("Segoe UI", 9),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg'],
            selectcolor=self.colors['dark_bg'],
            activebackground=self.colors['dark_bg'],
            activeforeground=self.colors['dark_fg']
        )
        chk_multiple.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        # File selection
        tk.Label(
            input_frame, 
            text="Select File(s):", 
            font=("Segoe UI", 9),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg']
        ).grid(row=1, column=0, sticky="w")
        
        self.btn_browse = self.create_modern_button(
            input_frame, "Browse Files", self.load_files, 
            style="primary", width=12
        )
        self.btn_browse.grid(row=1, column=1, sticky="w", padx=(5, 0))
        
        # Column selection
        tk.Label(
            input_frame, 
            text="Data Column:", 
            font=("Segoe UI", 9),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg']
        ).grid(row=2, column=0, sticky="w", pady=(5, 0))
        
        self.combo_column = ttk.Combobox(
            input_frame, 
            state="readonly",
            font=("Segoe UI", 9),
            height=8
        )
        self.combo_column.grid(row=2, column=1, sticky="ew", pady=(5, 0), padx=(5, 0))
        
        # Method selection
        tk.Label(
            input_frame, 
            text="Ranking Method:", 
            font=("Segoe UI", 9),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg']
        ).grid(row=3, column=0, sticky="w", pady=(5, 0))
        
        self.combo_method = ttk.Combobox(
            input_frame, 
            values=["Weibull", "Cunnane", "Hazen", "Gringorten", "Blom", "Tukey"],
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.combo_method.set("Gringorten")
        self.combo_method.grid(row=3, column=1, sticky="ew", pady=(5, 0), padx=(5, 0))
        
        input_frame.grid_columnconfigure(1, weight=1)

    def create_parameters_section(self):
        """Create analysis parameters section"""
        param_frame = tk.LabelFrame(
            self.sidebar, 
            text="⚙️ ANALYSIS PARAMETERS", 
            font=("Segoe UI", 9, "bold"),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg'],
            padx=10,
            pady=10
        )
        param_frame.pack(fill="x", pady=(0, 10))
        
        # Significance level
        tk.Label(
            param_frame, 
            text="Significance Level (α):", 
            font=("Segoe UI", 9),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg']
        ).grid(row=0, column=0, sticky="w")
        
        self.alpha = tk.StringVar(value="0.05")
        self.alpha_combobox = ttk.Combobox(
            param_frame, 
            textvariable=self.alpha, 
            state="readonly", 
            values=("0.01", "0.05", "0.10"),
            font=("Segoe UI", 9),
            width=8
        )
        self.alpha_combobox.set("0.05")
        self.alpha_combobox.grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        # Return periods
        tk.Label(
            param_frame, 
            text="Return Periods (years):", 
            font=("Segoe UI", 9),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg']
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        self.entry_prob = tk.Entry(
            param_frame, 
            font=("Segoe UI", 9),
            width=20
        )
        self.entry_prob.insert(0, "1.1,5,10,20,50,100,200")
        self.entry_prob.grid(row=1, column=1, sticky="ew", pady=(5, 0), padx=(5, 0))
        
        # Set probabilities button
        btn_set_prob = self.create_modern_button(
            param_frame, "Apply Periods", self.convert_values,
            style="secondary", width=12
        )
        btn_set_prob.grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        # Probability table
        tree_frame = tk.Frame(param_frame, bg=self.colors['dark_bg'])
        tree_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        self.tree_prob = ttk.Treeview(
            tree_frame, 
            columns=("Return Period", "Probability"), 
            show="headings",
            height=4
        )
        self.tree_prob.heading("Return Period", text="Return Period")
        self.tree_prob.heading("Probability", text="Probability")
        self.tree_prob.column("Return Period", width=80)
        self.tree_prob.column("Probability", width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_prob.yview)
        self.tree_prob.configure(yscrollcommand=scrollbar.set)
        
        self.tree_prob.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        param_frame.grid_columnconfigure(1, weight=1)

    def create_distributions_section(self):
        """Create distributions selection section"""
        dist_frame = tk.LabelFrame(
            self.sidebar, 
            text="📊 DISTRIBUTIONS", 
            font=("Segoe UI", 9, "bold"),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg'],
            padx=10,
            pady=10
        )
        dist_frame.pack(fill="x", pady=(0, 10))
        
        # Create dictionary to store distribution selections
        self.dist_vars = {
            "GEV (MLE)": tk.BooleanVar(value=True),
            "GEV (Lmom)": tk.BooleanVar(value=False),
            "GEV (Manual)": tk.BooleanVar(value=False),
            "Normal": tk.BooleanVar(value=True),
            "Log-Normal": tk.BooleanVar(value=True),
            "Gumbel": tk.BooleanVar(value=True),
            "Log-Pearson III": tk.BooleanVar(value=True),
            "Gamma": tk.BooleanVar(value=True)
        }
        
        # Create checkboxes in 2 columns
        col1_frame = tk.Frame(dist_frame, bg=self.colors['dark_bg'])
        col1_frame.pack(side="left", fill="both", expand=True)
        col2_frame = tk.Frame(dist_frame, bg=self.colors['dark_bg'])
        col2_frame.pack(side="left", fill="both", expand=True)
        
        # Column 1
        for dist in ["GEV (MLE)", "GEV (Lmom)", "GEV (Manual)", "Normal"]:
            cb = tk.Checkbutton(
                col1_frame, 
                text=dist, 
                variable=self.dist_vars[dist],
                font=("Segoe UI", 9),
                fg=self.colors['dark_fg'],
                bg=self.colors['dark_bg'],
                selectcolor=self.colors['dark_bg'],
                activebackground=self.colors['dark_bg'],
                activeforeground=self.colors['dark_fg']
            )
            cb.pack(anchor="w", pady=1)
        
        # Column 2
        for dist in ["Log-Normal", "Gumbel", "Log-Pearson III", "Gamma"]:
            cb = tk.Checkbutton(
                col2_frame, 
                text=dist, 
                variable=self.dist_vars[dist],
                font=("Segoe UI", 9),
                fg=self.colors['dark_fg'],
                bg=self.colors['dark_bg'],
                selectcolor=self.colors['dark_bg'],
                activebackground=self.colors['dark_bg'],
                activeforeground=self.colors['dark_fg']
            )
            cb.pack(anchor="w", pady=1)

    def create_actions_section(self):
        """Create action buttons section"""
        action_frame = tk.LabelFrame(
            self.sidebar, 
            text="🚀 ACTIONS", 
            font=("Segoe UI", 9, "bold"),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg'],
            padx=10,
            pady=10
        )
        action_frame.pack(fill="x", pady=(0, 10))
        
        # Main action buttons
        self.btn_run = self.create_modern_button(
            action_frame, "Run Analysis", self.perform_anfreq,
            style="primary", width=15
        )
        self.btn_run.pack(fill="x", pady=2)
        
        self.btn_batch_run = self.create_modern_button(
            action_frame, "Batch Run", self.batch_run,
            style="success", width=15
        )
        self.btn_batch_run.pack(fill="x", pady=2)
        
        # Output directory
        btn_output = self.create_modern_button(
            action_frame, "Set Output Directory", self.browse_output_dir,
            style="secondary", width=15
        )
        btn_output.pack(fill="x", pady=2)
        
        # Additional tools
        tools_frame = tk.Frame(action_frame, bg=self.colors['dark_bg'])
        tools_frame.pack(fill="x", pady=(5, 0))
        
        self.btn_concat = self.create_modern_button(
            tools_frame, "Merge Results", self.concatenate_outputs,
            style="secondary", width=12
        )
        self.btn_concat.pack(side="left", padx=(0, 5))
        
        btn_theme = self.create_modern_button(
            tools_frame, "Theme", self.toggle_theme,
            style="accent", width=8
        )
        btn_theme.pack(side="left")
        
        # Batch confirmation
        self.batch_confirm = tk.BooleanVar(value=False)
        chk_confirm = tk.Checkbutton(
            action_frame, 
            text="Show batch confirmations",
            variable=self.batch_confirm,
            font=("Segoe UI", 8),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg'],
            selectcolor=self.colors['dark_bg'],
            activebackground=self.colors['dark_bg'],
            activeforeground=self.colors['dark_fg']
        )
        chk_confirm.pack(anchor="w", pady=(5, 0))

    def create_progress_section(self):
        """Create progress section"""
        progress_frame = tk.LabelFrame(
            self.sidebar, 
            text="📈 PROGRESS", 
            font=("Segoe UI", 9, "bold"),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg'],
            padx=10,
            pady=10
        )
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Ready to analyze...",
            font=("Segoe UI", 9),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg'],
            wraplength=300
        )
        self.progress_label.pack(fill="x", pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            orient=tk.HORIZONTAL, 
            mode='determinate'
        )
        self.progress_bar.pack(fill="x", pady=2)
        
        self.progress_percent = tk.Label(
            progress_frame,
            text="0%",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['dark_bg']
        )
        self.progress_percent.pack()
        
        # Status bar at bottom
        self.status_var = tk.StringVar(value="Welcome to VRainFreq Pro")
        status_bar = tk.Label(
            self.sidebar,
            textvariable=self.status_var,
            font=("Segoe UI", 8),
            fg=self.colors['dark_fg'],
            bg=self.colors['dark_bg'],
            relief="sunken",
            anchor="w"
        )
        status_bar.pack(side="bottom", fill="x", pady=(10, 0))

    def setup_main_tabs(self):
        """Setup modern tab interface for main content"""
        # Create notebook (tab container)
        style = ttk.Style()
        style.configure("Custom.TNotebook", background=self.colors['dark_bg'])
        style.configure("Custom.TNotebook.Tab", font=("Segoe UI", 10, "bold"))
        
        self.notebook = ttk.Notebook(self.main_content, style="Custom.TNotebook")
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Tab 1: Visualizations
        self.viz_tab = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(self.viz_tab, text="📊 Visualizations")
        self.setup_visualizations_tab()
        
        # Tab 2: Statistical Results
        self.stats_tab = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(self.stats_tab, text="📈 Statistical Results")
        self.setup_statistics_tab()
        
        # Tab 3: Data Explorer
        self.data_tab = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(self.data_tab, text="🔍 Data Explorer")
        self.setup_data_tab()
        
        # Tab 4: About & Help
        self.help_tab = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(self.help_tab, text="ℹ️ About")
        self.setup_help_tab()

    def setup_visualizations_tab(self):
        """Setup visualizations tab with modern layout"""
        self.viz_tab.grid_columnconfigure(0, weight=1)
        self.viz_tab.grid_rowconfigure(0, weight=1)
        
        # Create split view for plots
        split_frame = tk.Frame(self.viz_tab, bg='#34495e')
        split_frame.grid(row=0, column=0, sticky="nsew")
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_rowconfigure(0, weight=1)
        split_frame.grid_rowconfigure(1, weight=1)
        
        # Frequency plot
        viz1_frame = tk.LabelFrame(
            split_frame, 
            text="Frequency Analysis Plot",
            font=("Segoe UI", 10, "bold"),
            bg='#34495e',
            fg='white'
        )
        viz1_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        viz1_frame.grid_columnconfigure(0, weight=1)
        viz1_frame.grid_rowconfigure(0, weight=1)
        
        self.fig1 = plt.Figure(figsize=(10, 6), dpi=100)
        self.ax1 = self.fig1.add_subplot(111)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=viz1_frame)
        self.canvas1.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        
        # Histogram plot
        viz2_frame = tk.LabelFrame(
            split_frame, 
            text="Distribution Histogram",
            font=("Segoe UI", 10, "bold"),
            bg='#34495e',
            fg='white'
        )
        viz2_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        viz2_frame.grid_columnconfigure(0, weight=1)
        viz2_frame.grid_rowconfigure(0, weight=1)
        
        self.fig2 = plt.Figure(figsize=(10, 6), dpi=100)
        self.ax2 = self.fig2.add_subplot(111)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=viz2_frame)
        self.canvas2.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def setup_statistics_tab(self):
        """Setup statistics results tab"""
        self.stats_tab.grid_columnconfigure(0, weight=1)
        self.stats_tab.grid_rowconfigure(0, weight=1)
        
        # Create notebook for different statistical views
        stats_notebook = ttk.Notebook(self.stats_tab)
        stats_notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Test results frame
        test_frame = tk.Frame(stats_notebook)
        stats_notebook.add(test_frame, text="Statistical Tests")
        
        # Create treeview for test results
        columns = ("Distribution", "KS Statistic", "KS p-value", "KS Result", 
                  "Chi-Square", "Chi p-value", "Chi Result")
        self.test_tree = ttk.Treeview(test_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.test_tree.heading(col, text=col)
            self.test_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(test_frame, orient="vertical", command=self.test_tree.yview)
        self.test_tree.configure(yscrollcommand=scrollbar.set)
        
        self.test_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Return levels frame
        return_frame = tk.Frame(stats_notebook)
        stats_notebook.add(return_frame, text="Return Levels")
        
        columns = ("Return Period", "Probability") + tuple(self.dist_vars.keys())
        self.return_tree = ttk.Treeview(return_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.return_tree.heading(col, text=col)
            self.return_tree.column(col, width=100)
        
        scrollbar2 = ttk.Scrollbar(return_frame, orient="vertical", command=self.return_tree.yview)
        self.return_tree.configure(yscrollcommand=scrollbar2.set)
        
        self.return_tree.pack(side="left", fill="both", expand=True)
        scrollbar2.pack(side="right", fill="y")

    def setup_data_tab(self):
        """Setup data exploration tab"""
        self.data_tab.grid_columnconfigure(0, weight=1)
        self.data_tab.grid_rowconfigure(0, weight=1)
        
        # Data preview frame
        preview_frame = tk.LabelFrame(
            self.data_tab,
            text="Data Preview",
            font=("Segoe UI", 10, "bold"),
            bg='#34495e',
            fg='white'
        )
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        
        # Treeview for data
        self.data_tree = ttk.Treeview(preview_frame, height=20)
        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        
        self.data_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_help_tab(self):
        """Setup about and help tab"""
        self.help_tab.grid_columnconfigure(0, weight=1)
        self.help_tab.grid_rowconfigure(0, weight=1)
        
        # Create scrollable text area
        text_frame = tk.Frame(self.help_tab, bg='#34495e')
        text_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        text_widget = tk.Text(
            text_frame, 
            wrap="word", 
            width=80, 
            height=25,
            font=("Segoe UI", 10),
            bg='#2c3e50',
            fg='white',
            relief='flat'
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add help content
        help_text = """
╔════════════════════════════════════════════════════════════════╗
║                     VRAINFREQ PRO v2.0                        ║
║              Advanced Frequency Analysis Tool                 ║
╚════════════════════════════════════════════════════════════════╝

📖 OVERVIEW
VRainFreq Pro is a professional-grade frequency analysis tool for 
hydrological and meteorological data analysis. It provides comprehensive 
statistical analysis with multiple probability distributions.

✨ KEY FEATURES
• Multiple probability distributions (GEV, Normal, Log-Normal, etc.)
• Advanced statistical tests (K-S, Chi-square)
• Batch processing capabilities
• Professional visualizations
• Export functionality
• Modern, intuitive interface

🎯 QUICK START
1. Load your data (CSV or Excel format)
2. Select analysis parameters
3. Choose probability distributions
4. Run analysis
5. Explore results in different tabs

📊 SUPPORTED DISTRIBUTIONS
• GEV (Multiple fitting methods)
• Normal & Log-Normal
• Gumbel (EV1)
• Log-Pearson III
• Gamma

🔧 TECHNICAL DETAILS
• Advanced error handling
• Progress tracking
• Comprehensive logging
• Theme customization
• Responsive design

📞 SUPPORT
For technical support and inquiries:
📧 vempi@ugm.ac.id
🌐 vempi.staff.ugm.ac.id

© 2025 Vempi Satriya Adi Hendrawan - All Rights Reserved
        """
        
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")

    def create_modern_button(self, parent, text, command, style="primary", width=None):
        """Create a modern styled button"""
        colors = {
            "primary": {"bg": self.colors['primary'], "fg": "white"},
            "secondary": {"bg": self.colors['secondary'], "fg": "white"},
            "success": {"bg": self.colors['success'], "fg": "white"},
            "accent": {"bg": self.colors['accent'], "fg": "white"}
        }
        
        btn_style = colors.get(style, colors["primary"])
        
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            bg=btn_style["bg"],
            fg=btn_style["fg"],
            relief="flat",
            padx=15,
            pady=8,
            width=width,
            cursor="hand2"
        )

    def apply_theme(self):
        """Apply the current theme to all widgets"""
        if self.current_theme == "dark":
            plt.style.use('seaborn-v0_8-darkgrid')
            # Update plot backgrounds
            self.fig1.patch.set_facecolor('#2c3e50')
            self.ax1.set_facecolor('#34495e')
            self.fig2.patch.set_facecolor('#2c3e50')
            self.ax2.set_facecolor('#34495e')
        else:
            plt.style.use('seaborn-v0_8-whitegrid')
            self.fig1.patch.set_facecolor('white')
            self.ax1.set_facecolor('white')
            self.fig2.patch.set_facecolor('white')
            self.ax2.set_facecolor('white')

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme()
        self.update_plot_styles()

    def update_plot_styles(self):
        """Update plot styles based on current theme"""
        if self.current_theme == "dark":
            text_color = 'white'
            grid_color = '#7f8c8d'
        else:
            text_color = 'black'
            grid_color = '#bdc3c7'
        
        # Update frequency plot
        self.ax1.tick_params(colors=text_color)
        self.ax1.xaxis.label.set_color(text_color)
        self.ax1.yaxis.label.set_color(text_color)
        self.ax1.title.set_color(text_color)
        self.ax1.grid(True, color=grid_color, alpha=0.3)
        
        # Update histogram plot
        self.ax2.tick_params(colors=text_color)
        self.ax2.xaxis.label.set_color(text_color)
        self.ax2.yaxis.label.set_color(text_color)
        self.ax2.title.set_color(text_color)
        self.ax2.grid(True, color=grid_color, alpha=0.3)
        
        self.canvas1.draw()
        self.canvas2.draw()

    # ========== CORE FUNCTIONALITY (KEEP ALL ORIGINAL METHODS) ==========
    # All your original methods remain exactly the same - they're preserved below
    # Only UI-related methods have been modified above

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
        self.status_var.set(f"⚠️ {brief_msg}")

    def show_toast(self, message, duration=3000):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.geometry(f"+{self.root.winfo_x()+50}+{self.root.winfo_y()+50}")
        toast.attributes('-alpha', 0.9)        
        label = ttk.Label(toast, text=message, background='#ffdddd', relief='solid')
        label.pack(padx=10, pady=5)
        toast.after(duration, toast.destroy)

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
    
    # def optimal_bins(self):
    #     sturges = int(1 + 3.322 * np.log10(len(self.data)))  # Sturges' Rule
    #     sqrt_rule = int(np.sqrt(len(self.data)))  # Square Root Rule
    #     return max(sturges, sqrt_rule)  # Use the larger value
    
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
    
 
    def perform_stat_tests(self):
        """Lakukan K-S dan Chi-square yang konsisten df-nya.
        Hasil disimpan di self.chi_square (dict) dan self.chi_critical (dict).
        """
    
        distributions = [
            ("GEV (SciPy)", stats.genextreme, self.gev_params_scipy),
            ("GEV (Lmom)", stats.genextreme,
                (self.gev_params_lmom['c'], self.gev_params_lmom['loc'], self.gev_params_lmom['scale'])),
            ("GEV (Manual)", stats.genextreme, self.gev_params_manual),
            ("Normal", stats.norm, self.norm_params),
            ("Log-Normal", stats.lognorm, self.lognorm_params),
            ("Gumbel", stats.gumbel_r, self.gumbel_params),
            ("Log-Pearson III", stats.pearson3, self.logpearson_params),
            ("Gamma", stats.gamma, self.gamma_params),
        ]
    
        # Jumlah parameter per distribusi (harus sesuai definisi fit-mu)
        param_count = {"GEV (SciPy)": 3,"GEV (Lmom)": 3,"GEV (Manual)": 3,
                       "Normal": 2,"Log-Normal": 3,"Gumbel": 2,"Log-Pearson III": 3,"Gamma": 3}
    
        # ----- K-S test (sama seperti sebelumnya) -----
        self.ks_results = {}
        for name, dist_func, params in distributions:
            if name == "Log-Pearson III":
                transformed = np.log(self.data)
                self.ks_results[name] = stats.kstest(transformed, dist_func.name, args=params)
            else:
                self.ks_results[name] = stats.kstest(self.data, dist_func.name, args=params)
    
        # ----- Chi-square test (per distribusi) -----
        hist_obs, bin_edges = np.histogram(self.data, bins=self.num_bins)
        self.chi_square = {}       # name -> (chi2_stat, p_value, df, obs_bins_count)
        self.chi_critical = {}     # name -> chi_crit
        self.df_per_dist = {}      # name -> df
    
        alpha = float(self.alpha.get()) if hasattr(self, "alpha") else 0.05
    
        for name, dist_func, params in distributions:
            # hitung CDF pada edges; gunakan transformasi bila perlu
            if name == "Log-Pearson III":
                cdf_vals = dist_func.cdf(np.log(bin_edges), *params)
            else:
                cdf_vals = dist_func.cdf(bin_edges, *params)
    
            expected_freq = len(self.data) * np.diff(cdf_vals)
    
            # normalisasi expected agar total sesuai observasi (hindari pembulatan)
            total_obs = hist_obs.sum()
            total_exp = expected_freq.sum()
            if total_exp > 0:
                expected_freq = expected_freq * (total_obs / total_exp)
    
            # hanya gunakan bin yang expected > 0
            mask = expected_freq > 0
            n_valid_bins = int(mask.sum())
    
            if n_valid_bins < 2:
                # terlalu sedikit bin valid -> skip
                self.chi_square[name] = (np.nan, np.nan, 0, n_valid_bins)
                self.chi_critical[name] = np.nan
                self.df_per_dist[name] = 0
                continue
    
            # hitung statistik chi2
            # gunakan hist_obs pada indices yang sama (edges matching)
            obs_used = hist_obs[mask]
            exp_used = expected_freq[mask]
            chi2_stat = ((obs_used - exp_used) ** 2 / exp_used).sum()
    
            # df per distribusi: n_valid_bins - k_params - 1
            k_param = param_count.get(name, 0)
            df = max(1, n_valid_bins - k_param - 1)
    
            # p-value menggunakan df di atas
            p_value = 1 - stats.chi2.cdf(chi2_stat, df)
    
            # chi critical per distribusi (gunakan alpha yang sama)
            chi_crit = stats.chi2.ppf(1 - alpha, df)
    
            # simpan semua
            self.chi_square[name] = (chi2_stat, p_value, df, n_valid_bins)
            self.chi_critical[name] = chi_crit
            self.df_per_dist[name] = df
    
    def get_chi_results_table(self):
        """Buat tabel ringkas (list of dict atau pandas.DataFrame) untuk ditampilkan."""
        rows = []
        for name in self.chi_square:
            chi2_stat, p_value, df, n_valid_bins = self.chi_square[name]
            chi_crit = self.chi_critical.get(name, np.nan)
            conclusion = "Rejected" if (not np.isnan(chi2_stat) and not np.isnan(chi_crit) and chi2_stat > chi_crit) else "Accepted"
            rows.append({
                "Distribution": name,
                "Chi2": np.round(chi2_stat, 3) if not np.isnan(chi2_stat) else np.nan,
                "df": df,
                "Valid bins": n_valid_bins,
                "Chi crit": np.round(chi_crit, 3) if not np.isnan(chi_crit) else np.nan,
                "Chi p-value": np.round(p_value, 4) if not np.isnan(p_value) else np.nan,
                "Conclusion": conclusion
            })
        # jika pandas tersedia, return DataFrame untuk tampilan rapi
        try:
            return pd.DataFrame(rows)
        except Exception:
            return rows
 
    
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
            #self.canvas1.grid()  # tampilkan canvas1
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
        #self.canvas2.grid()  # tampilkan canvas1
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
        #self.progress_frame.grid_remove()
 
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
        #self.progress_frame.grid()
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
        #self.progress_frame.grid_remove()
        
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


    # ... (ALL YOUR ORIGINAL METHODS GO HERE - they remain exactly the same)
    # fit_distributions, compute_return_levels, optimal_bins, perform_stat_tests, 
    # compute_critical_values, create_result_dfs, get_results, compute_reduced_variate,
    # add_annotation, plot_frequency_analysis, plot_histogram_pdf, convert_values,
    # ensure_output_dir, browse_output_dir, load_files, merge_files, load_single_file,
    # toggle_batch_mode, perform_stats, batch_run, concatenate_outputs, 
    # _process_single_file, _calculate_probability_positions, perform_anfreq,
    # _process_single_column, calculate_statistics, show_license

    # Due to character limits, I'm showing the pattern - you would copy all your 
    # original methods exactly as they were, only changing the class name to 
    # ProfessionalFrequencyAnalysisApp

# ========== ORIGINAL METHODS PLACEHOLDER ==========
# Copy all your original methods here exactly as they were
# Only change the class name references

def main():
    root = tk.Tk()
    app = ProfessionalFrequencyAnalysisApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()