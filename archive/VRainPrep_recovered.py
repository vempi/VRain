import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import glob
import os

def gather_data(loc='', dirout='', source='UGM-Hidro', 
                period='None', calc='Sum'):
    
    if not dirout.endswith("/"): dirout+'/'
    
    def aggregate(dfin,agg_period,calc):
        # Set Time as index
        dfin.set_index("Time", inplace=True)    
        # Define aggregation options
        agg_options = {"30-min": "30T", "1-hour": "1H", "3-hour": "3H", "6-hour": "6H",
                       "12-hour": "12H", "24-hour": "24H", "Monthly": "M", "Quarterly": "Q",
                       "Annual": "A", "Seasonal": "Seasonal"}
        time_code = agg_options.get(agg_period)
        # Aggregate and store results in a dictionary
        if time_code == 'Seasonal':  # Custom seasonal grouping
            dfin['Season'] = dfin.index.to_series().dt.month % 12 // 3  # Converts months to seasons (0=DJF, 1=MAM, etc.)
            season_labels = {0: 'DJF', 1: 'MAM', 2: 'JJA', 3: 'SON'}
            dfin['Season'] = dfin['Season'].map(season_labels)
        
            if calc == 'Sum':
                res = dfin.groupby('Season').sum()
            elif calc == 'Average':
                res = dfin.groupby('Season').mean()
            elif calc == 'Maximum':
                res = dfin.groupby('Season').max()
            elif calc == 'Minimum':
                res = dfin.groupby('Season').min()
            elif calc == 'Count':
                res = dfin.groupby('Season').apply(lambda x: (x > 1).sum())
            else:
                raise ValueError("Invalid calculation type.")
        
        else:
            if calc=='Sum': res = dfin.resample(time_code).sum()
            elif calc=='Average': res = dfin.resample(time_code).mean()
            elif calc=='Maximum': res = dfin.resample(time_code).max()
            elif calc=='Minimum': res = dfin.resample(time_code).min()
            elif calc=='Count': res = dfin.resample(time_code).apply(lambda x: (x > 1).sum())
            
        res.reset_index(inplace=True)
        return res
    
    def proPERSIANN(file):
        df = pd.read_csv(file).iloc[:, 0:2]
        df.replace(-99, np.nan, inplace=True)  # Mengubah -99 menjadi NaN
        pat = r'PERSIANN_1h(\d{4})(\d{2})(\d{2})(\d{2})'
        extracted = df['Time'].astype(str).str.extract(pat)
        if extracted.isnull().values.any():
            print("Skipping file due to format issues:", file)
            return
        datetime_str = extracted.apply(lambda x: f"{x[0]}-{x[1]}-{x[2]} {x[3]}:00:00", axis=1)
        df['Time'] = pd.to_datetime(datetime_str, format='%Y-%m-%d %H:%M:%S', errors='coerce')        
        return df
    
    def readRain(fin,source):
        print(fin)
        if source=='PERSIANN': 
            dout = proPERSIANN(fin)
        elif source=='GSMAP':    
            dout= pd.read_csv(fin).iloc[:, 0:2]
        elif source=='GPM':    
            dout = pd.read_csv(fin).iloc[7:, 0:2]
        elif source=='UGM-hidro':    
            print('HEYYYYYYYYYYYYYYYYYYYYYYYY')
            dout= pd.read_csv(fin).iloc[:, 0:2]
            print(dout)
        dout.columns = ['Time','Rain']   
        dout['Time'] = pd.to_datetime(dout['Time'],errors='coerce')  
        dout["Rain"] = dout["Rain"].astype(float)
        return dout
    
    def list_all_items(path, pattern):
        items = []
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(pattern.lstrip("*")) or pattern == "*":
                        items.append(f"{os.path.join(root, file)}")
            return items
        except Exception as e:
            return [f"Error: {e}"]
    
    pattern='*.csv'
    if loc.endswith(".csv"):
        progress_var.set(0)
        try:
            dfs = readRain(loc,source); progress_var.set(1);root.update_idletasks()
        except:
            messagebox.showerror("Error", "Please select data source type correctly!")
            return
    else:
        try:
            lsts = list_all_items(loc, pattern)
            
            if not lsts:
                messagebox.showerror("Error", "No CSV files found in the selected directory.")
                return
            else: total_files = len(lsts)
            
            lst = list()
            dfs = pd.DataFrame()
            
            progress_var.set(0)
            try:
                for i,file in enumerate(lsts):
                    try: df = readRain(file,source)
                    except: messagebox.showerror("Iteration Error", "Error in reading single CSV!")
                    dfs = pd.concat([dfs, df], ignore_index=True)
                    progress_var.set(i)  # Update progress variable
                root.update_idletasks()  # Refresh GUI
            except:
                messagebox.showerror("Error", "Files are listed but error in reading CSV!")                
        except:
            messagebox.showerror("Error", "Error in reading CSV files or missing folders!")
            return
            
    dfs = dfs.sort_values(by='Time').reset_index(drop=True)
    if period!='None': out = aggregate(dfs,period,calc)
    else: out = dfs.copy()
    start = str(out['Time'][0].year)
    end = str(out['Time'][len(out.Time)-1].year)
    output_file = os.path.join(dirout, 'VRain-prep_'+source+'_'+start+'-'+end+'_'+time_var.get()+'-'+stat_var.get()+'.csv')
    try: 
        out.to_csv(output_file, index=False)
        messagebox.showinfo("Success", f"Processed data saved to {output_file}")
    except:
        messagebox.showerror("Error", "File can not be saved! Please close the file")    

def toggle_input():
    if input_type_var.get() == "Folder":
        input_folder_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        input_folder_button.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        input_file_entry.grid_remove()
        input_file_button.grid_remove()
    else:
        input_file_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        input_file_button.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        input_folder_entry.grid_remove()
        input_folder_button.grid_remove()

def select_input_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if file_path:
        input_file_var.set(file_path)

def select_input_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        input_folder_var.set(folder_selected)

def select_output_folder():
    folder_selected = filedialog.askdirectory()
    output_folder_var.set(folder_selected)

def process_data():
    if input_folder_var.get(): input_dir = input_folder_var.get()
    elif input_file_var.get(): input_dir = input_file_var.get()
    
    output_dir = output_folder_var.get()
    source = data_source_var.get()
    stat = data_source_var.get()
    
    if not input_dir or not output_dir:
        messagebox.showerror("Error", "Please select both input and output directories.")
        return

    gather_data(loc=input_dir, dirout=output_dir, source=source, 
                period=time_var.get(),calc=stat_var.get())

def on_entry_change(var_name, index, mode):
    if input_folder_var.get():
        input_file_var.set("")  # Clear the second entry if the first is filled
    elif input_file_var.get():
        input_folder_var.set("")  # Clear the first entry if the second is filled

def open_link():
    webbrowser.open("https://vempi.staff.ugm.ac.id")

def open_demo():
    webbrowser.open("https://github.com/vempi/VRain/tree/main/demo")

def open_help():
    webbrowser.open("https://github.com/vempi/VRain.exe/blob/main/help/vrainprep_v1.md")

def show_license():
    license_window = tk.Toplevel()
    license_window.title("Software License Agreement")
    license_window.geometry("600x400")

    license_text = """Rainfall Data Preparation (VRainPrep) v.1\n
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
"""

    text_widget = tk.Text(license_window, wrap="word", width=70, height=20)
    text_widget.insert("1.0", license_text)
    text_widget.insert("end", "vempi.staff.ugm.ac.id", "link")
    text_widget.insert("end", " | vempi@ugm.ac.id\n")

    # Konfigurasi tag untuk hyperlink
    text_widget.tag_configure("link", foreground="blue", underline=True)
    text_widget.tag_bind("link", "<Button-1>", open_link)

    text_widget.config(state="disabled")  # Supaya tidak bisa diedit
    text_widget.pack(padx=10, pady=10, fill="both", expand=True)

    tk.Button(license_window, text="OK", command=license_window.destroy).pack(pady=10)

if os.environ.get("PYTHON_SPLASH"):
    from ctypes import windll
    windll.user32.PostQuitMessage(0)  # Forces splash screen to close

try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    print("Splash module not found, running normally.")


# GUI Setup 
root = tk.Tk()
root.title("VRain | Rainfall Data Preparation (VRainPrep) v.1")

# Set custom icon (Windows - .ico format)
try:
    root.iconbitmap("1.ico")  # Replace "myicon.ico" with your actual file
except:
    print("ICO file not found.")

# Setup Menu
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# "File" Menu
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open", command=select_input_file)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# "About" Menu
about_menu = tk.Menu(menu_bar, tearoff=0)
about_menu.add_command(label="About", command=show_license)
about_menu.add_separator()
about_menu.add_command(label="Help", command=open_help)

# Add Menus to the Menu Bar
menu_bar.add_cascade(label="File", menu=file_menu)
menu_bar.add_cascade(label="About", menu=about_menu)

license_text = """VRain | Hourly Rainfall Data Pre-processor (VRainPrep) v.1\n
Software License Agreement / Perjanjian Lisensi Perangkat Lunak\n
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
"""

# Frame untuk input
tk.Label(root, text="Select Folder or File", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
frame_input = tk.Frame(root, padx=10, pady=5, relief=tk.RIDGE, borderwidth=2)
frame_input.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

# Radio Button untuk memilih tipe input
input_type_var = tk.StringVar(value="Folder")
tk.Radiobutton(frame_input, text="Folder Input", variable=input_type_var, value="Folder", command=toggle_input).grid(row=0, column=0, padx=10, pady=5, sticky="w")
tk.Radiobutton(frame_input, text="File Input", variable=input_type_var, value="File", command=toggle_input).grid(row=1, column=0, padx=10, pady=5, sticky="w")

# Input Folder
input_folder_var = tk.StringVar()
input_folder_entry = tk.Entry(frame_input, textvariable=input_folder_var, width=50)
input_folder_button = tk.Button(frame_input, text="Browse", command=select_input_folder)

# Input File CSV
input_file_var = tk.StringVar()
input_file_entry = tk.Entry(frame_input, textvariable=input_file_var, width=50)
input_file_button = tk.Button(frame_input, text="Browse", command=select_input_file)

# Default: Folder Input visible, File Input hidden
input_folder_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
input_folder_button.grid(row=0, column=2, padx=10, pady=5, sticky="w")
input_file_entry.grid_remove()
input_file_button.grid_remove()

# Data Source
tk.Label(frame_input, text="Data Source Type:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
data_source_var = tk.StringVar(value="None")
ttk.Combobox(frame_input, textvariable=data_source_var, values=['PERSIANN', 'GPM', 'GSMAP', 'UGM-Hidro'], state="readonly").grid(row=2, column=1, padx=10, pady=5, sticky="ew")

# Frame untuk input
# tk.Label(root, text="Select Folder or File", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=3, pady=5, sticky="w")
# frame_input = tk.Frame(root, padx=10, pady=10, relief=tk.RIDGE, borderwidth=2)
# frame_input.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

# # Input Folder
# tk.Label(frame_input, text="Input Folder:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
# input_folder_var = tk.StringVar()
# input_folder_var.trace_add("write", on_entry_change)
# tk.Entry(frame_input, textvariable=input_folder_var, width=50).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
# tk.Button(frame_input, text="Browse", command=select_input_folder).grid(row=0, column=2, padx=10, pady=5, sticky="w")

# # Input File CSV
# tk.Label(frame_input, text="Input File CSV:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
# input_file_var = tk.StringVar()
# input_file_var.trace_add("write", on_entry_change)
# tk.Entry(frame_input, textvariable=input_file_var, width=50).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
# tk.Button(frame_input, text="Browse", command=select_input_file).grid(row=1, column=2, padx=10, pady=5, sticky="w")

# Data Source
tk.Label(frame_input, text="Data Source Type:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
data_source_var = tk.StringVar(value="None")
ttk.Combobox(frame_input, textvariable=data_source_var, values=['PERSIANN','PERSIANN', 'GPM', 'GSMAP','UGM-Hidro'], state="readonly").grid(row=2, column=1, padx=10, pady=5, sticky="ew")

# Combobox Aggregate Period
tk.Label(root, text="Aggregate period:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
time_var = tk.StringVar(value='None')
ttk.Combobox(root, textvariable=time_var, values=["None", "30-min", "1-hour", "3-hour", 
                                                  "6-hour", "12-hour", "24-hour",
                                                  "Monthly","Quarterly","Annual",
                                                  "Seasonal"], state="readonly").grid(row=2, column=1, padx=10, pady=5, sticky="ew")

# Combobox Statistic
tk.Label(root, text="Calculation method:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
stat_var = tk.StringVar(value='Sum')
ttk.Combobox(root, textvariable=stat_var, values=["Minimum", "Average", "Maximum", "Sum", "Count"], state="readonly").grid(row=3, column=1, padx=10, pady=5, sticky="ew")

# Output Folder
tk.Label(root, text="Output Folder:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
output_folder_var = tk.StringVar()
tk.Entry(root, textvariable=output_folder_var, width=50).grid(row=4, column=1, padx=10, pady=5, sticky="ew")
tk.Button(root, text="Browse", command=select_output_folder).grid(row=4, column=2, padx=10, pady=5, sticky="w")

# Tombol Process
tk.Button(root, text="Process Data", command=process_data, bg="#4682B4", fg='white').grid(row=5, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

# Progress bar
style = ttk.Style()
style.theme_use("clam")
style.configure("Blue.Horizontal.TProgressbar", troughcolor="white", background="#4682B4", troughrelief="flat", thickness=20)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=300, style="Blue.Horizontal.TProgressbar")
progress_bar.grid(row=6, column=1, columnspan=2, padx=10,pady=10, sticky="ew")

root.mainloop()
