import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import glob
import os


# Ganti dengan path ke folder utama yang berisi subfolder dengan CSV
loc = 'E:/UGM 365/VSA Research Team - Documents/2024/02 Bengawan Solo (Vega)/Data Hujan/LAB HIDRO UGM/BOCO (UGM-Sipil) [DONE]'
#loc = 'C:/Users/LENOVO/Downloads/vempisatriyaGaG9rH'
dirout = 'E:/UGM 365/VSA Research Team - Documents/2024/02 Bengawan Solo (Vega)/Data Hujan/'

def gather_data(loc='', dirout='', source='UGM-Hidro', 
                period='None'):
    
    def proPERSIANN(file):
        df = pd.read_csv(file).iloc[:, 0:2]
        pat = r'PERSIANN_1h(\d{4})(\d{2})(\d{2})(\d{2})'
        extracted = df['Time'].astype(str).str.extract(pat)
        if extracted.isnull().values.any():
            print("Skipping file due to format issues:", i)
            return
        datetime_str = extracted.apply(lambda x: f"{x[0]}-{x[1]}-{x[2]} {x[3]}:00:00", axis=1)
        df['Time'] = pd.to_datetime(datetime_str, format='%Y-%m-%d %H:%M:%S', errors='coerce')        
        return df
    
    def list_all_items(path, pattern="*"):
        items = []
        try:
            for root, dirs, files in os.walk(path):
                items.append(f"[Folder] {root}")
                for file in files:
                    if file.endswith(pattern.lstrip("*")) or pattern == "*":
                        items.append(f"  [File] {os.path.join(root, file)}")
            return items
        except Exception as e:
            return [f"Error: {e}"]
    
    pattern='*.csv'
    if loc.endswith(".csv"):
        try:dfs = proPERSIANN(loc)
        except:
            messagebox.showerror("Error", "Please select data source type correctly!")
            return
    else:
        try:
            lsts = list_all_items(loc, pattern)
            #folder_path = loc  # Gunakan string langsung
            #lsts = glob.glob(os.path.join(folder_path, '**', pattern), recursive=True)
            #folder_path = Path(loc)  # Ganti dengan path folder Anda
            #lsts = [item for item in folder_path.rglob(pattern)]
            total_files = len(lsts)
            
            if not lsts:
                messagebox.showerror("Error", "No CSV files found in the selected directory.")
                return
            
            lst = list()
            dfs = pd.DataFrame()
            
            progress_var.set(0)
            for i,file in enumerate(lsts):
                if source=='PERSIANN': 
                    #lst = glob.glob(os.path.join(loc, pattern))
                    df = proPERSIANN(file)
                    
                elif source=='UGM-Hidro':    
                    df= pd.read_csv(file).iloc[:, 0:2]
                    df['Date Time'] = pd.to_datetime(df['Date Time'],errors='coerce')        
                    
                dfs = pd.concat([dfs, df], ignore_index=True)
                progress_var.set(i)  # Update progress variable
                root.update_idletasks()  # Refresh GUI
        except:
            messagebox.showerror("Error", "Please select data source type correctly!")
            return
        
    dfs.columns = ['Time','Rain']     
    dfs = dfs.sort_values(by='Time').reset_index(drop=True)
    if period!='None': dfs = aggregate(dfs,period)
    start = str(dfs.Time[0].year)
    end = str(dfs.Time[len(dfs.Time)-1].year)
    output_file = os.path.join(dirout, source+'_'+start+'-'+end+'_merged.csv')
    dfs.to_csv(output_file, index=False)
    messagebox.showinfo("Success", f"Processed data saved to {output_file}")

def aggregate(dfin,period):
    # Set Time as index
    dfin.set_index("Time", inplace=True)    
    # Define aggregation options
    agg_options = {"30-min": "30T","1-hour": "1H","3-hour": "3H","6-hour": "6H",
                   "12-hour": "12H","24-hour": "24H"}
    time_code = agg_options.get(period)
    # Aggregate and store results in a dictionary
    aggregated_results = dfin.resample(time_code).sum() 
    return aggregated_results
    

def select_input_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if file_path:
        input_file_var.set(file_path)

def select_input_folder():
    folder_selected = filedialog.askdirectory()
    input_folder_var.set(folder_selected)

def select_output_folder():
    folder_selected = filedialog.askdirectory()
    output_folder_var.set(folder_selected)

def process_data():
    if input_folder_var.get(): input_dir = input_folder_var.get()
    elif input_file_var.get(): input_dir = input_file_var.get()
    
    output_dir = output_folder_var.get()
    source = data_source_var.get()
    
    if not input_dir or not output_dir:
        messagebox.showerror("Error", "Please select both input and output directories.")
        return

    gather_data(loc=input_dir, dirout=output_dir, source=source, 
                period=time_var)

def open_help():
    webbrowser.open("https://vempi.staff.ugm.ac.id")

def on_entry_change(var_name, index, mode):
    if input_folder_var.get():
        input_file_var.set("")  # Clear the second entry if the first is filled
    elif input_file_var.get():
        input_folder_var.set("")  # Clear the first entry if the second is filled

def open_link(event):
    webbrowser.open("https://vempi.staff.ugm.ac.id")

def show_license():
    license_window = tk.Toplevel()
    license_window.title("Software License Agreement")
    license_window.geometry("600x400")

    license_text = """Rainfall Data Processor (VRainPrep) v.1\n
Software License Agreement / Perjanjian Lisensi Perangkat Lunak\\
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


# GUI Setup
root = tk.Tk()
root.title("VRain | Hourly Rainfall Data Pre-processor (VRainPrep) v.1")
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="About", command=show_license)

#file_menu.add_command(label="Save", command=save_results)
file_menu.add_separator()
file_menu.add_command(label="Help", command=open_help)
menu_bar.add_cascade(label="About", menu=file_menu)


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
frame_input = tk.Frame(root, padx=10, pady=10, relief=tk.RIDGE, borderwidth=2)
frame_input.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w")

# Label Header
tk.Label(frame_input, text="Select Folder or File (entry one of below)", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=3, pady=5, sticky="w")

# Input Folder
tk.Label(frame_input, text="Input Folder:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
input_folder_var = tk.StringVar()
input_folder_var.trace_add("write", on_entry_change)
tk.Entry(frame_input, textvariable=input_folder_var, width=50).grid(row=1, column=1, padx=10, pady=5, sticky="w")
tk.Button(frame_input, text="Browse", command=select_input_folder).grid(row=1, column=2, padx=10, pady=5, sticky="w")

# Input File CSV
tk.Label(frame_input, text="Input File CSV:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
input_file_var = tk.StringVar()
input_file_var.trace_add("write", on_entry_change)
tk.Entry(frame_input, textvariable=input_file_var, width=50).grid(row=2, column=1, padx=10, pady=5, sticky="w")
tk.Button(frame_input, text="Browse", command=select_input_file).grid(row=2, column=2, padx=10, pady=5, sticky="w")

# Data Source (Dipindahkan setelah Input File)
tk.Label(frame_input, text="Data Source Type:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
data_source_var = tk.StringVar(value='PERSIANN')
tk.OptionMenu(frame_input, data_source_var, 'PERSIANN', 'GSMAP', 'UGM-Hidro').grid(row=3, column=1, padx=10, pady=5, sticky="w")

# Combobox (Dropdown with Entry)
options = ["None","30-min", "1-hour", "3-hour", "6-hour", "12-hour", "24-hour"]
tk.Label(root, text="Aggregate period:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
time_var = tk.StringVar(value='None')
combobox = ttk.Combobox(root, textvariable=time_var, values=options, state="readonly")
#combobox.current(0)
combobox.grid(row=1, column=1, padx=10, pady=5, sticky="w")


# Output Folder (Tetap di root)
tk.Label(root, text="Output Folder:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
output_folder_var = tk.StringVar()
tk.Entry(root, textvariable=output_folder_var, width=50).grid(row=2, column=1, padx=10, pady=5, sticky="w")
tk.Button(root, text="Browse", command=select_output_folder).grid(row=2, column=2, padx=10, pady=5, sticky="w")

# Tombol Process
tk.Button(root, text="Process Data", command=process_data, bg="#4682B4", fg='white').grid(row=3, column=1, columnspan=1, pady=10, sticky="s")

# Progress bar
style = ttk.Style()
style.theme_use("clam")  # 'clam' allows custom colors

# Define a custom style with a blue progress bar
style.configure("Blue.Horizontal.TProgressbar",
                troughcolor="white", 
                background="#4682B4",  # Steel Blue
                troughrelief="flat",
                thickness=20)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=300,
                               style="Blue.Horizontal.TProgressbar")
progress_bar.grid(row=4, column=1, columnspan=1, pady=10, sticky="n")

root.mainloop()