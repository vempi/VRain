import pandas as pd
import re
import numpy as np
import glob,os
import seaborn as sns
import matplotlib.pyplot as plt
#from __future__ import division, print_function


# ============================ Basic ================================ # 

def gather_PERSIANN(pattern='*.csv',loc='',dirout=''):
    lst = glob.glob(pattern)

    dfs = pd.DataFrame()
    for i in lst:
        print(i)
        df = pd.read_csv(i).iloc[:,0:2]
        # Regular expression to capture year, month, and day
        pat = r'PERSIANN_1h(/d{4})(/d{2})(/d{2})(/d{2})'
        extracted = df['Time'].str.extract(pat)
        datetime_str = extracted.apply(lambda x: f"{x[0]}-{x[1]}-{x[2]} {x[3]}:00:00", axis=1)
        df['Time'] = pd.to_datetime(datetime_str, format='%Y-%m-%d %H')
        print(i)
        # Append to the master dataframe
        dfs = dfs.append(df, ignore_index=True)

    # Sort the master dataframe by the date column
    dfs = dfs.sort_values(by='Time').reset_index(drop=True)
    dfs.to_csv(dirout+'PERSIANN_2001-2023_'+loc+'_merge.csv')
    return dfs

def prePERSIANN(dfin):
    df = dfin.copy()
    df['Time'] = pd.to_datetime(df['Time'])
    df.set_index('Time', inplace=True)
    df = df.iloc[:,:1]; df.columns = ['Rain']

    df['Rain'] = df['Rain'].apply(lambda x: 0 if x < 0 else x)
    df['Rain'] = df['Rain'].apply(lambda x: 0 if x < 1 else x)
    
    return df
    
def interpol(inp,new_len):
    def print_list(values):
        print('[' + ', '.join(format(value, '.3f') for value in values) + ']')
    def interpolate(inp, fi):
        i, f = int(fi // 1), fi % 1  # Split floating-point index into whole & fractional parts.
        j = i+1 if f > 0 else i  # Avoid index error.
        return (1-f) * inp[i] + f * inp[j]
        
    delta = (len(inp)-1) / (new_len-1)
    outp = [interpolate(inp, i*delta) for i in range(new_len)]
    return outp

def calcum(dur,n):
    cumulative_df = pd.DataFrame()
    for column in dur.columns:
        cumulative_sum = dur[column].cumsum()
        min_value = min(cumulative_sum)
        max_value = max(cumulative_sum)
        try: 
            ndata = pd.Series([(x - min_value) / (max_value - min_value) for x in cumulative_sum])
            data =  ndata.dropna()
            inter = interpol(list(data), n)
            cumulative_df[column] = inter
        except: 
            cumulative_df[column] = np.nan
    return cumulative_df

def get_rain_series(df, threshold = 50, dat='',sta='', dirout='',
                    norain = 1, saveas=True):
    df['Rain'] = df['Rain'].apply(lambda x: 0 if x < norain else x)
    
    sel = df[df['Rain'] != 0]
    sel['Time'] = sel.index
    # Sort the DataFrame by time
    
    sel['time_diff'] = sel.Time.diff()
    thre= pd.Timedelta(hours=1)
    sel['Group'] = (sel['time_diff'] > thre).cumsum()
    sel['time_diff'] = sel['time_diff'].fillna(pd.Timedelta(0))
    
    sel = sel.drop(columns=['time_diff'])
    
    sel = sel.set_index('Group',drop=True)
    
    ex = sel.groupby(sel.index)['Rain'].sum()
    label = sel.groupby(sel.index)['Time'].min().reset_index()
    
    if type(threshold)==int:
        prcntl = threshold
        idxs = ex[(ex > threshold) & (ex < 500)].index
    elif type(threshold)==float:
        prcntl = np.percentile(ex.values,(threshold*100))
        idxs = ex[(ex > prcntl) & (ex < 500)].index
    
    out = sel.loc[idxs]
    labelsel = label.loc[idxs]['Time']
    
    out = out.reset_index()
    
    out['Group'] = pd.factorize(out['Group'])[0] + 1

    if saveas==True:out.to_csv(dirout+'olah_'+dat+'-'+sta+'_selected.csv')

    # Create a new column to enumerate each date within groups
    out['Jam'] = out.groupby('Group').cumcount()
    
    # Use pivot to reshape the DataFrame
    pivoted = out.pivot(index='Jam', columns='Group', values='Rain')
    pivoted.columns = labelsel
    
    if saveas==True:pivoted.to_csv(dirout+'pakai_'+dat+'-'+sta+'_pivot.csv')
    
    return pivoted, prcntl



def getpivot(pivoted, dat='',sta='', dirout='', saveas=True):
    
    #pivoted.apply(lambda x: (x != 0).sum()).to_csv('olah_'+dat+'-'+sta+'-durasi.csv')
    dur = pivoted.count()
    if saveas==True:
        dur.to_csv(dirout+'olah_'+dat+'-'+sta+'-durasi.csv')

        # ===== Plot
        fig, ax = plt.subplots(figsize=(15,5),dpi=300)
        sns.heatmap(pivoted, cmap='Blues', annot=False, vmax=10,vmin=0,
                    cbar_kws={'label':'[mm/jam]'},ax=ax)  
        ax.set_ylabel('Durasi')
        plt.tight_layout()
        plt.savefig(dirout+'olah_'+dat+'-'+sta+'-durasi.png',dpi=300)
        plt.show()
    return dur

def plot_getpivot(f, threshold, norain,dat='',sta='', dirout=''):
    dfin = pd.read_csv(f,index_col=0)
    df = prePERSIANN(dfin)
    
    try:
        if '.' in threshold: par = float(threshold)
        else: par = int(threshold)          
    except ValueError as e:
        messagebox.showerror("Error", "Please select the option of threshold type!")
        return
    
    pivoted, prcntl = get_rain_series(df, par, dat,sta, dirout,
                                      norain, saveas=False)
    dur = pivoted.count()

    fig, ax = plt.subplots(figsize=(15,5),dpi=120)
    sns.heatmap(pivoted, cmap='Blues', annot=False, vmax=10,vmin=0,
                cbar_kws={'label':'[mm/jam]'},ax=ax)  
    ax.set_ylabel('Durasi')
    plt.tight_layout()

    popup1 = tk.Toplevel(root)  # Create a new top-level window
    popup1.title("Rainfall Events")
            
    canvas1 = FigureCanvasTkAgg(fig, master=popup1)
    canvas1.draw()
    canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def getperiod(dur, dat='',sta='', dirout='', saveas=True):
    nper = dur.mode()[0]
    bins = dur.max()-dur.min()
    if saveas==True:
        fig = plt.hist(dur, bins=bins, edgecolor='black')  # Adjust the number of bins as needed
        plt.xlabel('Periode hujan (jam)')
        plt.ylabel('Jumlah kejadian')
        plt.title(sta)
        plt.savefig(dirout+'pakai_'+dat+'-'+sta+'_histogram-durasi.png',dpi=300)
        plt.show()

    return nper

def plot_getperiod(f, threshold, norain, dat='',sta='', dirout=''):
    dfin = pd.read_csv(f,index_col=0)
    df = prePERSIANN(dfin)
    pivoted, prcntl = get_rain_series(df, threshold, dat,sta, dirout,
                                      norain, saveas=False)
    dur = getpivot(pivoted, dat,sta, dirout, False)
    nper = dur.mode()[0]
    bins = dur.max()-dur.min()
    fig = plt.hist(dur, bins=bins, edgecolor='black')  # Adjust the number of bins as needed
    plt.xlabel('Periode hujan (jam)')
    plt.ylabel('Jumlah kejadian')
    plt.title(sta)
    popup2 = Toplevel(root)  # Create a new top-level window
    popup2.title("Rainfall Events")
    canvas2 = FigureCanvasTkAgg(fig, master=popup2)
    canvas2.draw()
    canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def getcum(pivoted,nper, dat='',sta='', dirout='', saveas=True):
    cums = calcum(pivoted, nper+1)
    tmp = cums.copy()
    cums['Average'] = tmp.mean(axis=1)
    cums['Percentile10'] = tmp.quantile(0.1,axis=1)
    cums['Percentile90'] = tmp.quantile(0.9,axis=1)
    if saveas==True:
        cums.to_csv(dirout+'pakai_'+dat+'-'+sta+'-cumulated-'+str(nper)+'jam.csv')
        
        # plot!
        perc = cums*100
    
        # Calculate the steepest curve based on maximum change
        idmax = perc.iloc[2].idxmax()
        #diffs = df.diff().abs().sum(axis=1)
        #idx = diffs.idxmax()
        #idxmax = df.iloc[:,[idx]].columns[0]
    
        for col in perc.columns:
            if col == 'Average':
                fig = plt.plot(perc.index, perc[col], linewidth=3, label='Average')
            elif col == idmax:
                print(col)
                fig = plt.plot(perc.index, perc[col], linewidth=3, label=str(col))
            else:
                fig = plt.plot(perc.index, perc[col], color='gray', alpha=0.7,label='_hidden')
        plt.xlabel('Jam ke-')
        plt.ylabel('Hujan kumulatif (%)')
        plt.title(sta)
        plt.legend()
        plt.savefig(dirout+'pakai_'+dat+'-'+sta+'-cumulated-'+str(nper)+'jam.png',dpi=300)
        plt.show()
                
    return cums

def plot_getcum(pivoted,nper, dat='',sta='', dirout='', saveas=True):
    cums = calcum(pivoted, nper+1)
    tmp = cums.copy()
    cums['Average'] = tmp.mean(axis=1)
    cums['Percentile10'] = tmp.quantile(0.1,axis=1)
    cums['Percentile90'] = tmp.quantile(0.9,axis=1)

    cums.to_csv(dirout+'pakai_'+dat+'-'+sta+'-cumulated-'+str(nper)+'jam.csv')
    perc = cums*100
    idmax = perc.iloc[2].idxmax()
    for col in perc.columns:
        if col == 'Average':
            fig = plt.plot(perc.index, perc[col], linewidth=3, label='Average')
        elif col == idmax:
            print(col)
            fig = plt.plot(perc.index, perc[col], linewidth=3, label=str(col))
        else:
            fig = plt.plot(perc.index, perc[col], color='gray', alpha=0.7,label='_hidden')
    plt.xlabel('Jam ke-')
    plt.ylabel('Hujan kumulatif (%)')
    plt.title(sta)
    plt.legend()

    popup3 = Toplevel(root)  # Create a new top-level window
    popup3.title("Rainfall Events")
    canvas3 = FigureCanvasTkAgg(fig, master=popup3)
    canvas3.draw()
    canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def getdistribusi(cums, nper, dat='',sta='', dirout='', saveas=True):
    
    # For TKINTER
    for widget in dashboard_frame.winfo_children():
        widget.destroy()
    
    dfsel = cums.drop('Average',axis=1)

    dfdist = dfsel.diff().fillna(dfsel)*100

    dfdist['Jam'] = dfdist.index
    
    df_melted = dfdist.melt(id_vars='Jam', var_name='Date', value_name='Rain')
    df_melted = df_melted[df_melted['Jam']!=0]
    if saveas==True:
        # Plot using Seaborn
        fig, ax = plt.subplots(figsize=(12,8),dpi=100)
        sns.barplot(x='Jam', y='Rain', data=df_melted, color='C0',
                    capsize=.1,errwidth=1,ax=ax)
    
        # Annotate the 'Average' value on top of the bar
        average_value = cums['Average'].diff()[1:]
        for i, value in enumerate(average_value):
            value=value*100
            plt.text(i, 0.1, f'{value:.1f}', ha='center', va='bottom', fontsize=11, 
                     color='white')
    
        plt.title(sta)
        plt.xlabel('Jam'); plt.ylabel('Prosentase hujan (%)')
        #plt.tight_layout()
        plt.savefig(dirout+'pakai_'+dat+'-'+sta+'-Durasi-rerata-'+str(nper)+'jam.png')
        plt.show()
        
        canvas_figure = FigureCanvasTkAgg(fig, master=dashboard_frame)
        canvas_figure.draw()
        canvas_figure.get_tk_widget().pack(fill="x", expand=False)

        
    return df_melted


def open_directory():
    folder_selected = filedialog.askdirectory()  # Open folder selection dialog
    if folder_selected:  # If a folder is selected
        label.config(text=f"Selected Folder:\n{folder_selected}")


def open_directory(path):
    if not os.path.isdir(path):
        messagebox.showerror("Error", "Invalid directory path!")
        return

    # Open the directory (Windows, Mac, Linux)
    try:
        if os.name == "nt":  # Windows
            os.startfile(path)
        elif os.name == "posix":  # macOS & Linux
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open directory:\n{e}")


# ============================== 1. Olah table ============================== #

#os.chdir('C:/Users/lenovo/OneDrive - UGM 365/Projects-konsultansi/10.PHR-Batch-4/1.Data-internal/Hujan/2.Tabuler-jam-jam-an')
os.chdir('D:/OneDrive - UGM 365/Projects-konsultansi/10.PHR-Batch-4/1.Data-internal/Hujan/2.Tabuler-jam-jam-an/')
f = 'PERSIANN_2001-2023_Rantau-bais_merge.csv'; selected_type='PERSIANN'; file_id = 'Rantau Bais'
input_type = 'PERSIANN'
thresh_type = "1. Absolute value (in mm)"
par_thresh = '50' ; par_rainmin= '2'
output_dir = 'D:/OneDrive - UGM 365/Projects-konsultansi/10.PHR-Batch-4/1.Data-internal/Hujan/2.Tabuler-jam-jam-an/'

try:
    if '.' in par_thresh: par = float(par_thresh)
    else: par = int(par_thresh)          
except ValueError as e:
    messagebox.showerror("Error", "Please select the option of threshold type!")


dfin = pd.read_csv(f,index_col=0)
df = prePERSIANN(dfin)        

pivoted, prcntl = get_rain_series(df, par, input_type,file_id,output_dir,float(par_rainmin),True)



dur = getpivot(pivoted,input_type,file_id,output_dir)
nper = getperiod(dur,input_type,file_id,output_dir)

cums = getcum(pivoted,nper,input_type,file_id,output_dir)
melt = getdistribusi(cums,nper,input_type,file_id,output_dir)        

# ============================ From Chat GPT ================================ # 

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def show_example():
    selected_type = input_type.get()
    if selected_type == "PERSIANN":
        example = "time,rainfall\n00:00,0.5\n01:00,1.2\n02:00,0.8"
    elif selected_type == "GSMAP":
        example = "time,rainfall\n2024-01-01 00:00,0.3\n2024-01-01 01:00,1.5\n2024-01-01 02:00,0.7"
    elif selected_type == "GPM":
        example = "time,rainfall\n01-01-2024 00:00,0.4\n01-01-2024 01:00,1.1\n01-01-2024 02:00,0.9"
    else:
        example = "Please select a data type."
    
    messagebox.showinfo("Example Format", example)

def load_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    input_dir.set(file_path)
    
    if not file_path:
        return
    try:
        dfin = pd.read_csv(file_path,index_col=0)
        df = prePERSIANN(dfin)
        status_label1.config(text="Step 1. Reading file: DONE", fg="blue")
        
        #process_data(df)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file: {e}")

def process_data(f,par_thresh, input_type, thresh_type, file_id, output_dir, par_rainmin):      
    output_dir = output_dir+'/'

    try:
        if '.' in par_thresh: par = float(par_thresh)
        else: par = int(par_thresh)          
    except ValueError as e:
        messagebox.showerror("Error", "Please select the option of threshold type!")
        return
    
    if thresh_type == "1. Absolute value (in mm)" and type(par)==float:
        messagebox.showerror("Error", "Threshold should be in Integer if you select Option 1")
        return
    elif thresh_type == "2. Percentile (in fraction)" and type(par)==int:
        messagebox.showerror("Error", "Threshold should be between 0-1 if you select Option 2")
        return
    elif thresh_type == 'Select Threshold Type':  # If no selection is made
        messagebox.showerror("Error", "Please select the option of Threshold type!")
        return
    #except:
        #messagebox.showerror("Warning", "Please select the option of threshold type or define it correctly! \n The program defines threshold type automatically")
    
    try:
        dfin = pd.read_csv(f,index_col=0)
        df = prePERSIANN(dfin)        
        
        tmp = df.reset_index(inplace=False)
        if "Time" not in tmp.columns or "Rain" not in tmp.columns:
            raise ValueError("CSV must contain at least'Time' and 'Rain' columns.")
        #status_label1.config(text="Step 1. Reading file: DONE", fg="blue")
        status_label1.destroy()
        
        try:
            pivoted, prcntl = get_rain_series(df, par, input_type,file_id,output_dir,par_rainmin,True)
            #status_label2.config(text="Step 2. Preprocess data: DONE", fg="blue")
            status_label2.destroy()
        except Exception as e:
            messagebox.showerror("Processing Error", f"Error processing data: {e}")

        dur = getpivot(pivoted,input_type,file_id,output_dir)

        #status_label3.config(text="Step 3. Group Rainfall Event: DONE", fg="blue")
        status_label3.destroy()

        nper = getperiod(dur,input_type,file_id,output_dir)
        #status_label4.config(text="Step 4. Get Mean Duration: DONE", fg="blue")
        status_label4.destroy()
        
        cums = getcum(pivoted,nper,input_type,file_id,output_dir)
        melt = getdistribusi(cums,nper,input_type,file_id,output_dir)
        
        status_label5.config(text="Step 1. Reading file: DONE -> Step 2. Preprocess data: DONE -> Step 3. Group Rainfall Event: DONE \n-> Step 4. Get Mean Duration: DONE -> Step 5. Write Outputs: DONE", fg="blue")
        duration_label.config(text=f"Storm Duration: {nper:.0f} hours, from total rainfall event greater than: {prcntl:.1f} mm (as threshold)")
        
    except Exception as e:
        messagebox.showerror("Processing Error", f"Error processing data: {e}")

def reset():
    for widget in dashboard_frame.winfo_children():
        widget.destroy()

    duration_label.config(text="Storm Duration (hours): N/A")
    status_label1.config(text="Step 1. Reading file: N/A", fg='red')
    status_label2.config(text="Step 2. Preprocess data: N/A", fg='red')
    status_label3.config(text="Step 3. Group Rainfall Event: N/A", fg='red')
    status_label4.config(text="Step 4. Get Mean Duration: N/A", fg='red')
    status_label5.config(text="Step 5. Write Outputs: N/A", fg='red')


def select_output_directory():
    directory = filedialog.askdirectory()
    if directory:
        output_dir.set(directory)

def save_results():
    if not output_dir.get():
        messagebox.showwarning("Warning", "Please select an output directory first!")
    else:
        messagebox.showinfo("Save", f"Results saved to {output_dir.get()} successfully!")

license_text = """Rainfall Duration Analysis (VRainHour) v.1 \n\nSoftware License Agreement \nPerjanjian Lisensi Perangkat Lunak\n
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
For enquiries, contact: <a href=\"vempi.staff.ugm.ac.id\">vempi.staff.ugm.ac.id</a> | vempi@ugm.ac.id \nUntuk info lebih lanjut, hubungi: <a href=\"vempi.staff.ugm.ac.id\">vempi.staff.ugm.ac.id</a> | vempi@ugm.ac.id"""
        
# GUI Setup
root = tk.Tk()
root.title("Rainfall Duration Analysis (VRainHour) v.1")

# Menu
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open", command=load_csv)
#file_menu.add_command(label="Save", command=save_results)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)


help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", license_text))
menu_bar.add_cascade(label="Help", menu=help_menu)

frame = tk.Frame(root, padx=10, pady=10, width=900, height=1200)
frame.pack_propagate(False)  # Prevent resizing to fit children

frame.pack(padx=10, pady=10)

# Dropdown Menu for Input Type
input_type_frame = tk.LabelFrame(frame, text="Select Data Type")
input_type_frame.pack(pady=5, fill="both")
input_type = ttk.Combobox(input_type_frame, values=["PERSIANN"], state="readonly")
input_type.pack(side="left",pady=5, padx=5)
input_type.set('PERSIANN')

# example 
example_button = tk.Button(input_type_frame, text="Show Example CSV or TXT Format", command=show_example)
example_button.pack(side="left",pady=5)

# Section: File Operations
file_frame = tk.LabelFrame(frame, text="File Input")
file_frame.pack(pady=5, fill="both")

input_dir = tk.StringVar(value='D:/OneDrive - UGM 365/Projects-konsultansi/10.PHR-Batch-4/1.Data-internal/Hujan/2.Tabuler-jam-jam-an/PERSIANN_2001-2023_Rantau-bais_merge.csv')
input_dir_entry = tk.Entry(file_frame, textvariable=input_dir, state='readonly', width=75)
input_dir_entry.pack(side="left", padx=5, pady=5)
load_button = tk.Button(file_frame, text="Load CSV File", command=load_csv)
load_button.pack(side="left", padx=5, pady=5)

file_id_label = tk.Label(file_frame, text="File ID:")
file_id_label.pack(side="left", padx=0)

file_id = tk.StringVar(value='Station Name')
file_id_entry = tk.Entry(file_frame, textvariable=file_id, width=20)
file_id_entry.pack(side='left',padx=5, pady=0)

# Section: Rainfall Threshold Parameters
par_frame = tk.LabelFrame(frame, text="Rainfall Threshold Parameters")
par_frame.pack(pady=5, fill="both")

# Par 1
thresh_label2 = tk.Label(par_frame, text="If Option 1 chosen, please put integer value in mm (e.g.,50), \nbut if Option 2, put percentile fraction 0-1 (e.g., 0.75)",
                         justify="left")
thresh_label2.pack(side="left",padx=5, pady=5)

thresh_type = ttk.Combobox(par_frame, values=["1. Absolute value (in mm)",'2. Percentile (in fraction)'], state="readonly")
thresh_type.set("Select Threshold Type")
thresh_type.pack(side='left',padx=5)

thresh_label = tk.Label(par_frame, text="Accumulated Rainfall (mm) \nor Percentile Threshold:",
                        justify="left")
thresh_label.pack(side="left",padx=5)


par_thresh = tk.StringVar()
thresh_entry = tk.Entry(par_frame, textvariable=par_thresh, width=10)
thresh_entry.pack(side="left",padx=5, pady=10)

# Par 1
par_frame2 = tk.LabelFrame(frame)
par_frame2.pack(pady=5, fill="both")
rainmin_label = tk.Label(par_frame2, text="Minimum Hourly Rainfall Included (mm):")
rainmin_label.pack(side="left", padx=5)
par_rainmin = tk.StringVar(value=1.5)
rainmin_entry = tk.Entry(par_frame2, textvariable=par_rainmin, width=10)
rainmin_entry.pack(side="left", padx=5, pady=5)

# Section: Output dir
output_dir = tk.StringVar(value='D:/OneDrive - UGM 365/Projects-konsultansi/10.PHR-Batch-4/1.Data-internal/Hujan')
output_dir_frame = tk.LabelFrame(frame, text="Output Directory")
output_dir_frame.pack(pady=5, fill="both")
output_dir_entry = tk.Entry(output_dir_frame, textvariable=output_dir, state='readonly', width=75)
output_dir_entry.pack(side="left", padx=5, pady=5)
select_output_button = tk.Button(output_dir_frame, text="Browse", command=select_output_directory)
select_output_button.pack(side="left", padx=5, pady=5)

# Section: Processing
process_frame = tk.LabelFrame(frame, text="Processing")
process_frame.pack(pady=5, fill="both")

#Menu View (selipan)
view_menu = tk.Menu(menu_bar, tearoff=0)
view_menu.add_command(label="Rainfall events", command=lambda:plot_getpivot(input_dir_entry.get(), 
                                                                            par_thresh.get(), float(par_rainmin.get()),
                                                                            input_type.get(),file_id.get(), 
                                                                            output_dir.get()))  # Menu option to pop up figure
# #view_menu.add_separator()

# #getcum(pivoted,nper, dat='',sta='', dirout='', saveas=True)
# #view_menu.add_command(label="Duration Distribution", command=show_figure)  # Menu option to pop up figure
# #view_menu.add_separator()

# #view_menu.add_command(label="Rainfall events", command=lambda:getcum(pivoted,nper, dat='',sta='', dirout='', saveas=True))
menu_bar.add_cascade(label="View", menu=view_menu)

process_button = tk.Button(process_frame, text="Process Data", command=lambda: process_data(input_dir_entry.get(),
                                                                                            par_thresh.get(),
                                                                                            input_type.get(),
                                                                                            thresh_type.get(),
                                                                                            file_id.get(),
                                                                                            output_dir.get(),
                                                                                            float(par_rainmin.get())))

process_button.pack(side="left", padx=5, pady=5)
reset_button = tk.Button(process_frame, text="Reset", command=reset)
reset_button.pack(side="left", padx=5, pady=5)
save_button = tk.Button(process_frame, text="Save", command=save_results)
save_button.pack(side="left", padx=5, pady=5)

exit_button = tk.Button(process_frame, text="Check Saved Files", command=lambda:open_directory(output_dir.get()))
exit_button.pack(side="left", padx=5, pady=5)

# Section: Results
status_label1 = tk.Label(frame, text="Step 1. Reading file: N/A", font=("Arial", 9), fg="red");status_label1.pack(pady=5)
status_label2 = tk.Label(frame, text="Step 2. Preprocess data: N/A", font=("Arial", 9), fg="red");status_label2.pack(pady=5)
status_label3 = tk.Label(frame, text="Step 3. Group Rainfall Event: N/A", font=("Arial", 9), fg="red");status_label3.pack(pady=5)
status_label4 = tk.Label(frame, text="Step 4. Get Mean Duration: N/A", font=("Arial", 9), fg="red");status_label4.pack(pady=5)
status_label5 = tk.Label(frame, text="Step 5. Write Outputs: N/A", font=("Arial", 9), fg="red");status_label5.pack(pady=5)

duration_label = tk.Label(frame, text="Storm Duration (hours): N/A", font=("Arial", 12))
duration_label.pack(pady=5)

# Section: Dashboard
dashboard_frame = tk.LabelFrame(frame, text="Dashboard")
dashboard_frame.pack(pady=5, fill="y", expand=False)


root.mainloop()
