import pandas as pd
import numpy as np
import os
import sys
import subprocess
import webbrowser

def _base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ─────────────────────────────── Shared utilities ────────────────────────────

LICENSE_TEXT = (
    "VRain | Rainfall Duration Analysis (VRainStorm) v.1\n\n"
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

# ============================ First order functions ================================ #

def preOlah(dfin):
    df = dfin.copy()
    # Clean junk rows
    df = df[df['Time'].astype(str).str.strip().str.len() > 0]
    df = df[~df['Time'].astype(str).str.contains("User", case=False, na=False)]
    
    # Try flexible datetime parsing
    try:
        # allow mixed formats and dayfirst
        df['Time'] = pd.to_datetime(df['Time'], errors='raise', format="mixed", dayfirst=True)
    except Exception as e:
        print(f"⚠️ Could not parse datetime directly: {e}")
        n = len(df)
        try:
            # If column looks numeric, infer step
            numeric_time = pd.to_numeric(df['Time'], errors='coerce')
            diffs = numeric_time.diff().dropna()
            step = diffs.mode()[0] if not diffs.empty else 1
            start = pd.to_datetime("2000-01-01")
            df['Time'] = pd.date_range(start=start, periods=n, freq=pd.to_timedelta(step, unit="D"))
        except Exception:
            # fallback → daily step
            start = pd.to_datetime("2000-01-01")
            df['Time'] = pd.date_range(start=start, periods=n, freq="D")
    
    # Use datetime as index
    df.set_index('Time', inplace=True)

    # Keep only first data column
    df = df.iloc[:, :1]
    df.columns = ['Rain']

    # Clean Rain values
    df['Rain'] = pd.to_numeric(df['Rain'], errors="coerce").fillna(0)
    df['Rain'] = df['Rain'].apply(lambda x: max(x, 0))

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


def categorize_peak(dfcat, cumulative=True):
    categories = {"First Quarter": [],"Second Quarter": [],"Third Quarter": [],"Fourth Quarter": []}
    if cumulative==True: dfhour = dfcat.diff().fillna(dfcat.iloc[0])
    for col in dfhour.columns:
        peak_idx = dfhour[col].idxmax()  # Find the peak index
        #duration = len(dfhour[col])  # Total duration (number of hours)
        duration = dfhour.index[-1]
        # Define quarter thresholds
        q1 = duration / 4
        q2 = duration / 2
        q3 = 3 * duration / 4
        # Categorize based on peak position
        if peak_idx <= q1: categories["First Quarter"].append(col)
        elif peak_idx <= q2: categories["Second Quarter"].append(col)
        elif peak_idx <= q3: categories["Third Quarter"].append(col)
        else: categories["Fourth Quarter"].append(col)
    category_dfs = [(cat, dfhour[cols]) for cat, cols in categories.items()]
    return category_dfs


def calcum(piv,n):
    cumulative_df = pd.DataFrame()
    for column in piv.columns:
        cumulative_sum = piv[column].cumsum()
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
    if saveas==True:out.to_csv(dirout+'VRain_'+dat+'-'+sta+'_selected.csv')
    # Create a new column to enumerate each date within groups
    out['Jam'] = out.groupby('Group').cumcount()
    # Use pivot to reshape the DataFrame
    pivoted = out.pivot(index='Jam', columns='Group', values='Rain')
    pivoted.columns = labelsel
    if saveas==True:pivoted.to_csv(dirout+'VRain_'+dat+'-'+sta+'_pivot.csv')
    return pivoted, prcntl

def getpivot(pivoted, dat='',sta='', dirout='', saveas=True):
    dur = pivoted.count()
    if saveas==True:
        dur.to_csv(dirout+'VRain_'+dat+'-'+sta+'-duration.csv')

        # ===== Plot
        fig, ax = plt.subplots(figsize=(15,5), dpi=300)
        data = pivoted.fillna(0).values.astype(float)
        im = ax.imshow(data, cmap='Blues', aspect='auto', vmax=10, vmin=0)
        ax.figure.colorbar(im, ax=ax, label='[mm/hour]')
        col_labels = [str(c.date()) if hasattr(c, 'date') else str(c) for c in pivoted.columns]
        ax.set_xticks(range(len(col_labels)))
        ax.set_xticklabels(col_labels, rotation=45, ha='right', fontsize=8)
        ax.set_yticks(range(len(pivoted.index)))
        ax.set_yticklabels(pivoted.index)
        ax.set_ylabel('Duration')

        plt.tight_layout()
        plt.savefig(dirout + 'VRain_' + dat + '-' + sta + '-duration.png', dpi=300)
        plt.show()
    return dur


def getperiod(dur, dat='',sta='', dirout='', saveas=True):
    nper = dur.mode()[0]
    bins = dur.max()-dur.min()
    if saveas==True:
        fig = plt.hist(dur, bins=bins, edgecolor='black')  # Adjust the number of bins as needed
        plt.xlabel('Rainfall Period (Hours)')
        plt.ylabel('Number of events')
        plt.title(sta)
        plt.savefig(dirout+'VRain_'+dat+'-'+sta+'_histogram-duration_'+str(nper)+'-hour.png',dpi=300)
        plt.show()

    return nper

def plot_getperiod(f, threshold, norain, dat='',sta='', dirout=''):
    dfin = pd.read_csv(f,index_col=0)
    dfin = pd.read_csv(f)
    dfin = dfin.iloc[:, -2:]; dfin.columns = ['Time','Rain']
    
    df = preOlah(dfin)
    pivoted, prcntl = get_rain_series(df, threshold, dat,sta, dirout,
                                      norain, saveas=False)
    dur = getpivot(pivoted, dat,sta, dirout, False)
    nper = dur.mode()[0]
    bins = dur.max()-dur.min()
    fig = plt.hist(dur, bins=bins, edgecolor='black')  # Adjust the number of bins as needed
    plt.xlabel('Rainfall Period (Hour)')
    plt.ylabel('Number of events')
    plt.title(sta)
    popup2 = Toplevel(root)  # Create a new top-level window
    popup2.title("Rainfall Events")
    canvas2 = FigureCanvasTkAgg(fig, master=popup2)
    canvas2.draw()
    canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def plot_gethuff(f, threshold, norain,dat='',sta='', dirout='', dur_mode=''):

    try:
        if '.' in threshold: par = float(threshold)
        else: par = int(threshold)          
    except ValueError as e:
        messagebox.showerror("Error", "Please select the option of threshold type!")
        return    

    raw = smart_read(f)
    tcol = detect_col(raw, ['time', 'date', 'datetime', 'tanggal', 'waktu'])
    rcol = detect_col(raw, ['rain', 'rainfall', 'hujan', 'precip'], fallback_idx=1)
    dfin = raw[[tcol, rcol]].copy(); dfin.columns = ['Time','Rain']
    df = preOlah(dfin)
    pivoted, prcntl = get_rain_series(df, par, dat,sta, dirout,
                                      norain, saveas=False)
    
    if dur_mode=="Fixed duration (Hour)": dur_typing = int(dur_num.get())
    elif dur_mode=="Dominant duration (Hour)":
        dur_typing = int(pivoted.count().mode()[0])
    else: dur_typing = dur_type.get() 

    if type(dur_typing)==str:
        cum = calcum(pivoted, 11)
        cum.index=(cum.index / (len(cum) - 1)) * 1  # Convert to 0-100%
        xlabel='Duration fraction (0-1)'
    else:
        cum = calcum(pivoted, dur_typing+1)
        xlabel = 'Hour'

    df_huff = categorize_peak(cum, cumulative=True)
    
    for i, tmp in enumerate(df_huff):
        df_huff[i][1]['Average'] = tmp[1].mean(axis=1)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))  # 2x2 grid
    fig.suptitle(sta+"\nHuff method (all samples)", fontsize=14)
    for (category, df_group), ax in zip(df_huff, axes.flatten()):
        if len(df_group.columns)==1:
            ax.text(0.5, 0.5, "No data", ha='center', va='center', fontsize=14, 
                    color='k', transform=ax.transAxes)  # Use relative positioning
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_frame_on(False)
        else:   
            num_event = len(df_group.columns)
            for col in df_group.columns:
                if col == 'Average':
                    ax.plot(df_group.index, df_group[col], linewidth=3, label='Average')
                    for x, y in zip(df_group.index, df_group[col]):
                        ax.text(x, y+0.02, f'{y:.2f}',ha='center', va='bottom',fontsize=12, color='k')
                else:
                    ax.plot(df_group.index, df_group[col], color='gray', alpha=0.7,label='_hidden')
                ax.set_title(category+": "+str(num_event)+" events")
                ax.set_xlabel(xlabel)
                ax.set_ylabel('Rainfall fraction (0-1)')
                ax.grid(True)
    plt.tight_layout(rect=[0, 0, 1, 0.96])        
    plt.show()

    popup1 = tk.Toplevel(root)  # Create a new top-level window
    popup1.title("Plot Huff Rainfall Distribution")
            
    canvas1 = FigureCanvasTkAgg(fig, master=popup1)
    canvas1.draw()
    canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def getcum_huff(pivoted, nper,dat='',sta='', dirout=''):
    
    if nper==100:    
        cums = calcum(pivoted, 11)
        cums.index=(cums.index / (len(cums) - 1)) * 1  # Convert to 0-100%
        namae = 'VRain_'+dat+'-'+sta+'-cumulated-'+'100-percent.csv'
        xlabel='Duration fraction (0-1)'
        xlabelcum='Duration fraction (%)'
    else:
        cums = calcum(pivoted, nper+1)
        namae = 'VRain_'+dat+'-'+sta+'-cumulated-'+str(nper)+'-hour.csv'
        xlabel = 'Hour'; xlabelcum = 'Hour'
    
    df_huff = categorize_peak(cums, cumulative=True)

    tmp = cums.copy()
    cums['Average'] = tmp.mean(axis=1)
    cums['Percentile10'] = tmp.quantile(0.1,axis=1)
    cums['Percentile90'] = tmp.quantile(0.9,axis=1)
    cums.to_csv(dirout+namae) 
    
    for i, tmp in enumerate(df_huff):
        df_huff[i][1]['Average'] = tmp[1].mean(axis=1)
    
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))  # 2x2 grid
    fig.suptitle(sta+"\nHuff method (all samples)", fontsize=14)
    for (category, df_group), ax in zip(df_huff, axes.flatten()):
        if len(df_group.columns)==1:
            ax.text(0.5, 0.5, "No data", ha='center', va='center', fontsize=14, 
                    color='k', transform=ax.transAxes)  # Use relative positioning
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_frame_on(False)
        else:   
            num_event = len(df_group.columns)
            for col in df_group.columns:
                if col == 'Average':
                    ax.plot(df_group.index, df_group[col], linewidth=3, label='Average')
                    for x, y in zip(df_group.index, df_group[col]):
                        ax.text(x, y+0.02, f'{y:.2f}',ha='center', va='bottom',fontsize=12, color='k')
                else:
                    ax.plot(df_group.index, df_group[col], color='gray', alpha=0.7,label='_hidden')
                ax.set_title(category+": "+str(num_event)+" events")
                ax.set_xlabel(xlabel)
                ax.set_ylabel('Rainfall fraction (0-1)')
                ax.grid(True)
    plt.tight_layout(rect=[0, 0, 1, 0.96])        
    plt.show()
        
    # Create Cumulative plot
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))  # 2x2 grid
    fig.suptitle(sta+"\nHuff method (all durations)", fontsize=14)
    # Plot each category
    for (category, df_group), ax in zip(df_huff, axes.flatten()):
        if len(df_group.columns)==1:
            ax.text(0.5, 0.5, "No data", ha='center', va='center', fontsize=14, 
                    color='k', transform=ax.transAxes)  # Use relative positioning
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_frame_on(False)
        else:  
            num_event = len(df_group.columns)
            df_cumsum = df_group.cumsum()
            for col in df_group.columns:
                if col == 'Average':
                    ax.plot(df_cumsum.index, df_cumsum[col], linewidth=3, label='Average')
                else:
                    ax.plot(df_cumsum.index, df_cumsum[col], color='gray', alpha=0.7,label='_hidden')
            ax.set_title(category+": "+str(num_event)+" events")
            ax.set_xlabel("'Duration fraction (0-1)'")
            ax.set_ylabel("Cumulative rainfall (0-1)")
            ax.grid(True)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Prevent title overlap
    plt.show()
    
    # plot whole
    perc = cums*100
    if nper==100: perc.index = (df_cumsum.index)*100
    # Calculate the steepest curve based on maximum change
    idmax = perc.iloc[2].idxmax()
    for col in perc.columns:
        if col == 'Average':
            fig = plt.plot(perc.index, perc[col], linewidth=3, label='Average')
        elif col == idmax:
            print(col)
            fig = plt.plot(perc.index, perc[col], linewidth=3, label=str(col))
        else:
            fig = plt.plot(perc.index, perc[col], color='gray', alpha=0.7,label='_hidden')
            
    plt.xlabel(xlabelcum)
    plt.ylabel('Cumulative rainfall (%)')
    plt.title(sta)
    plt.legend()
    plt.savefig(dirout+namae.replace('.csv','.png'),dpi=300)
    plt.show()
    return cums

def getdistribusi(cums, nper, dat='',sta='', dirout='', saveas=True):
    
    # For TKINTER
    for widget in dashboard_frame.winfo_children():
        widget.destroy()
    
    try: dfsel = cums.drop('Average',axis=1)
    except: dfsel = cums
    average_value = dfsel.mean(axis=1).diff().iloc[1:]
    average_value.iat[0] = dfsel.mean(axis=1).iloc[1]
    
    dfdist = dfsel.diff().fillna(dfsel)*100
    if nper==100: dfdist.index=(dfdist.index*100).astype(int)
    dfdist['Jam'] = dfdist.index

    df_melted = dfdist.melt(id_vars='Jam', var_name='Date', value_name='Rain')
    df_melted = df_melted[df_melted['Jam']!=0]
    if saveas==True:
        fig, ax = plt.subplots(figsize=(10, 5.5), dpi=100)
        means = df_melted.groupby('Jam')['Rain'].mean()
        errs  = df_melted.groupby('Jam')['Rain'].sem().fillna(0)
        ax.bar(range(len(means)), means.values, yerr=errs.values, color='C0', capsize=3)
        ax.set_xticks(range(len(means)))
        ax.set_xticklabels(means.index.astype(str))

        # Annotate the 'Average' value on top of the bar
        for p, value in zip(ax.patches, average_value):
            value=value*100
            ax.text(p.get_x() + p.get_width() / 2, 0.1, f'{value:.1f}', ha='center', va='bottom', fontsize=11, 
                     color='white')
    
        plt.title(sta)
        plt.ylabel('Rainfall intensity (%)')
        if nper==100: plt.xlabel('Duration fraction (%)')
        else: plt.xlabel('Hour')
        
        plt.tight_layout()
        plt.savefig(dirout+'VRain_'+dat+'-'+sta+'-mean-duration-'+str(nper)+'-hour.png')
        plt.show()
        
        canvas_figure = FigureCanvasTkAgg(fig, master=dashboard_frame)
        canvas_figure.draw()
        canvas_figure.get_tk_widget().pack(fill="x", expand=False)
    return df_melted


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


# ============================ Second order function ================================ #

def show_example():
    selected_type = input_type.get()
    if selected_type == "Default":
        example = "Time;Rain(mm)\n1/1/2001 0:00;0.5\n1/1/2001 1:00;1.2\n1/1/2001 2:00;0.8\n..."
    elif selected_type == "GSMAP":
        example = "time,rainfall\n2024-01-01 00:00,0.3\n2024-01-01 01:00,1.5\n2024-01-01 02:00,0.7"
    elif selected_type == "GPM":
        example = "time,rainfall\n01-01-2024 00:00,0.4\n01-01-2024 01:00,1.1\n01-01-2024 02:00,0.9"
    else:
        example = "Please select a data type."
    
    messagebox.showinfo("Example Format", example)

def load_csv():
    file_path = filedialog.askopenfilename(
        filetypes=[("Data files", "*.csv *.xlsx *.xls"),
                   ("CSV files", "*.csv"),
                   ("Excel files", "*.xlsx *.xls"),
                   ("All files", "*.*")])
    if not file_path:
        return
    input_dir.set(file_path)
    try:
        raw = smart_read(file_path)
        tcol = detect_col(raw, ['time', 'date', 'datetime', 'tanggal', 'waktu'])
        rcol = detect_col(raw, ['rain', 'rainfall', 'hujan', 'precip'], fallback_idx=1)
        dfin = raw[[tcol, rcol]].copy()
        dfin.columns = ['Time', 'Rain']
        preOlah(dfin)
        status_var.set(f"File loaded: {os.path.basename(file_path)}  "
                       f"(time={tcol}, rain={rcol})")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file: {e}")

def load_demo():
    demo_path = os.path.join(_base_path(), "demo", "VRainStorm_demo.csv")
    if os.path.exists(demo_path):
        input_dir.set(demo_path)
        file_id.set("Demo Station")
        status_var.set("Demo file loaded — set Output folder, then click Process Data.")
        load_csv.__wrapped__ = True
        try:
            raw = smart_read(demo_path)
            tcol = detect_col(raw, ['time', 'date', 'datetime', 'tanggal', 'waktu'])
            rcol = detect_col(raw, ['rain', 'rainfall', 'hujan', 'precip'], fallback_idx=1)
            dfin = raw[[tcol, rcol]].copy()
            dfin.columns = ['Time', 'Rain']
            preOlah(dfin)
        except Exception:
            pass
    else:
        messagebox.showwarning("Demo Not Found",
            f"Demo file not found at:\n{demo_path}")

def process_data(f,par_thresh, input_type, thresh_type, file_id, output_dir, 
                 par_rainmin,durtype): 
    
    status_label=[i for i in log_frame.winfo_children()]
    
    status_label[0].config(text="Step 1. Reading file: N/A", font=("Arial", 9), fg="red")
    status_label[1].config(text="Step 2. Preprocess data: N/A", font=("Arial", 9), fg="red")
    try: status_label[2].config(text="Step 3. Group rainfall event: N/A", font=("Arial", 9), fg="red")
    except: messagebox.showerror("Error", "Please reset first!")
    status_label[3].config(text="Step 4. Get duration pattern: N/A", font=("Arial", 9), fg="red")
    status_label[4].config(text="Step 5. Write outputs: N/A", font=("Arial", 9), fg="red")
    status_label[5].config(text="Dominant storm duration: (hours): N/A", font=("Arial", 12))
    
    view_menu.entryconfig("Huff quarter", state="normal")
    output_dir = output_dir+'/'

    if durtype=="Fixed duration (Hour)": dur_typing = int(dur_num.get())
    else: dur_typing = durtype

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
        raw = smart_read(f)
        tcol = detect_col(raw, ['time', 'date', 'datetime', 'tanggal', 'waktu'])
        rcol = detect_col(raw, ['rain', 'rainfall', 'hujan', 'precip'], fallback_idx=1)
        dfin = raw[[tcol, rcol]].copy()
        dfin.columns = ['Time', 'Rain']
        df = preOlah(dfin)

        tmp = df.reset_index(inplace=False)
        if "Time" not in tmp.columns or "Rain" not in tmp.columns:
            raise ValueError("File must contain Time and Rain columns.")
        #status_label1.config(text="Step 1. Reading file: DONE", fg="blue")
        status_label[0].destroy()
        
        try:
            pivoted, prcntl = get_rain_series(df, par, input_type,file_id,output_dir,float(par_rainmin),True)
            #status_label2.config(text="Step 2. Preprocess data: DONE", fg="blue")
            status_label[1].destroy()
        except Exception as e:
            messagebox.showerror("Processing Error", f"Error processing data: {e}")

        dur = getpivot(pivoted,input_type,file_id,output_dir)

        #status_label3.config(text="Step 3. Group Rainfall Event: DONE", fg="blue")
        status_label[2].destroy()

        nper = getperiod(dur,input_type,file_id,output_dir)
        #status_label4.config(text="Step 4. Get Mean Duration: DONE", fg="blue")
        status_label[3].destroy()
        
        if dur_typing=="Dominant duration (Hour)":
            cums = getcum_huff(pivoted,nper,input_type,file_id,output_dir)
            melt = getdistribusi(cums,nper,input_type,file_id,output_dir)
        elif dur_typing=="Percentage (%)":
            cums = getcum_huff(pivoted,100,input_type,file_id,output_dir)
            melt = getdistribusi(cums,100,input_type,file_id,output_dir)
        elif type(dur_typing)==int:
            cums = getcum_huff(pivoted,dur_typing,input_type,file_id,output_dir)
            melt = getdistribusi(cums,dur_typing,input_type,file_id,output_dir)
        else:
            messagebox.showerror("Processing Error", f"Error duration type input")
            
        num = len(pivoted.columns)
        status_label[4].config(text="Step 1. Reading file: DONE -> Step 2. Preprocess data: DONE -> Step 3. Group Rainfall Event: DONE \n-> Step 4. Get Mean Duration: DONE -> Step 5. Write Outputs: DONE", fg="blue")
        status_label[5].config(text=f"Dominant storm duration: {nper:.0f} hours, from total rainfall event greater than: {prcntl:.1f} mm (as threshold) \nNumber of samples: {num}")        
        
    except Exception as e:
        messagebox.showerror("Processing Error", f"Error processing data: {e}")

def init():
    status_label1 = tk.Label(log_frame, text="Step 1. Reading file: N/A", font=("Arial", 9), fg="red");status_label1.pack(pady=1)
    status_label2 = tk.Label(log_frame, text="Step 2. Preprocess data: N/A", font=("Arial", 9), fg="red");status_label2.pack(pady=1)
    status_label3 = tk.Label(log_frame, text="Step 3. Group rainfall event: N/A", font=("Arial", 9), fg="red");status_label3.pack(pady=1)
    status_label4 = tk.Label(log_frame, text="Step 4. Get duration pattern: N/A", font=("Arial", 9), fg="red");status_label4.pack(pady=1)
    status_label5 = tk.Label(log_frame, text="Step 5. Write outputs: N/A", font=("Arial", 9), fg="red");status_label5.pack(pady=1)
    duration_label = tk.Label(log_frame, text="Dominant storm duration: (hours): N/A", font=("Arial", 10)); duration_label.pack(pady=1)

def reset():
    for widget in dashboard_frame.winfo_children(): widget.destroy()
    for w in log_frame.winfo_children(): w.destroy()
    init()
    #status_label5.destroy()

def select_output_directory():
    directory = filedialog.askdirectory()
    if directory:
        output_dir.set(directory)

def save_results():
    if not output_dir.get():
        messagebox.showwarning("Warning", "Please select an output directory first!")
    else:
        messagebox.showinfo("Save", f"Results saved to {output_dir.get()} successfully!")

def on_combobox_select(event):
    selected_value = dur_type.get()
    if selected_value == "Fixed duration (Hour)":
        dur_num.config(state="normal")  # Aktifkan Entry
    else:
        dur_num.config(state="disabled")  # Nonaktifkan Entry

# ============================== Dummy input ============================== #

#os.chdir('C:/Users/lenovo/OneDrive - UGM 365/Projects-konsultansi/10.PHR-Batch-4/1.Data-internal/Hujan/2.Tabuler-jam-jam-an')
# os.chdir('E:/OneDrive - UGM 365/Projects-konsultansi/10.PHR-Batch-4/1.Data-internal/Hujan/2.Tabuler-jam-jam-an/')
# file_path = 'PERSIANN_2001-2023_Rantau-bais_merge.csv'; input_type='PERSIANN'; file_id = 'Rantau Bais'
# f = file_path
# par_thresh = '50' ; par_rainmin= "2"; thresh_type = "1. Absolute value (in mm)"
# output_dir = 'E:/OneDrive - UGM 365/Projects-konsultansi/10.PHR-Batch-4/1.Data-internal/Hujan/2.Tabuler-jam-jam-an/'
# process_data(file_path,par_thresh, input_type, thresh_type, file_id, output_dir, par_rainmin)

# ============================== GUI Main program ============================== #


license_text = """VRain | Rainfall Duration Analysis (VRainStorm) v.1 \n\nSoftware License Agreement \nPerjanjian Lisensi Perangkat Lunak\n
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
root.title("VRain | Rainfall Duration Analysis (VRainStorm) v.1")

try:root.iconbitmap("2.ico")
except: pass

# Menu
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open File...", command=load_csv)
file_menu.add_command(label="Load Demo", command=load_demo)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)


# Header
hdr = tk.Frame(root, bg="#4682B4", pady=6)
hdr.pack(fill=tk.X)
tk.Label(hdr, text="VRain  |  Rainfall Duration Analysis  (VRainStorm)",
         font=("Arial", 12, "bold"), bg="#4682B4", fg="white").pack()
tk.Label(hdr, text="Extract storm events and Huff rainfall distribution patterns",
         font=("Arial", 9), bg="#4682B4", fg="#d0e8f8").pack()

frame = tk.Frame(root, padx=10, pady=10, width=900, height=1200)
frame.pack_propagate(False)  # Prevent resizing to fit children

frame.pack(padx=10, pady=10)

# Dropdown Menu for Input Type
input_type_frame = tk.LabelFrame(frame, text="Data Type (Hourly rainfall)")
input_type_frame.pack(pady=5, fill="both")
input_type = ttk.Combobox(input_type_frame, values=["Default"], state="readonly")
input_type.pack(side="left",pady=5, padx=5)
input_type.set("Default")

# example 
example_button = tk.Button(input_type_frame, text="Show Example CSV Format", command=show_example)
example_button.pack(side="left",pady=5)

# Section: File Operations
file_frame = tk.LabelFrame(frame, text="File Input")
file_frame.pack(pady=5, fill="both")

input_dir = tk.StringVar(value='')
input_dir_entry = tk.Entry(file_frame, textvariable=input_dir, width=75)
input_dir_entry.pack(side="left", padx=5, pady=5)
load_button = tk.Button(file_frame, text="Load File", command=load_csv)
load_button.pack(side="left", padx=5, pady=5)
demo_button = tk.Button(file_frame, text="Demo", command=load_demo, bg="#e8f4f8")
demo_button.pack(side="left", padx=2, pady=5)

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
thresh_type.set("1. Absolute value (in mm)")
thresh_type.pack(side='left',padx=5)

thresh_label = tk.Label(par_frame, text="Accumulated Rainfall (mm) \nor Percentile Threshold:",
                        justify="left")
thresh_label.pack(side="left",padx=5)



par_thresh = tk.StringVar(value=50)
thresh_entry = tk.Entry(par_frame, textvariable=par_thresh, width=10)
thresh_entry.pack(side="left",padx=5, pady=10)

# Par 1
par_frame2 = tk.LabelFrame(frame)
par_frame2.pack(pady=5, fill="both")
rainmin_label = tk.Label(par_frame2, text="Minimum Hourly Rainfall Included (mm):")
rainmin_label.pack(side="left", padx=5)
par_rainmin = tk.StringVar(value=1)
rainmin_entry = tk.Entry(par_frame2, textvariable=par_rainmin, width=10)
rainmin_entry.pack(side="left", padx=5, pady=5)

# Section: Output dir
output_dir = tk.StringVar(value='')
output_dir_frame = tk.LabelFrame(frame, text="Output Directory")
output_dir_frame.pack(pady=5, fill="both")
output_dir_entry = tk.Entry(output_dir_frame, textvariable=output_dir, width=75)
output_dir_entry.pack(side="left", padx=5, pady=5)
select_output_button = tk.Button(output_dir_frame, text="Browse", command=select_output_directory)
select_output_button.pack(side="left", padx=5, pady=5)

# Section: Processing
process_frame = tk.LabelFrame(frame, text="Processing")
process_frame.pack(pady=5, fill="both")


thresh_label3 = tk.Label(process_frame, text="Duration Type (for plot)",justify="left")
thresh_label3.pack(side="left",padx=5, pady=5)

dur_type = ttk.Combobox(process_frame, values=["Percentage (%)",
                                               "Dominant duration (Hour)",
                                               "Fixed duration (Hour)"], state="readonly")
dur_type.pack(side="left",pady=5, padx=5)
dur_type.set("Percentage (%)")

thresh_label4 = tk.Label(process_frame, text="Fixed duration",justify="left")
thresh_label4.pack(side="left",padx=5, pady=5)
dur_num = ttk.Combobox(process_frame, values=[1,2,3,4,5,6,7,8,9,10,11,12,24], state="disabled")
dur_num.pack(side="left",pady=5, padx=5)

dur_type.bind("<<ComboboxSelected>>", on_combobox_select)  # Bind event

#Menu View (selipan)
view_menu = tk.Menu(menu_bar, tearoff=0)

if dur_type.get()=="Fixed duration (Hour)": 
    dur_typing = int(dur_num.get())
else: dur_typing = dur_type.get()

view_menu.add_command(label="Huff quarter", 
                      command=lambda:plot_gethuff(input_dir_entry.get(),
                                                  par_thresh.get(), float(par_rainmin.get()),
                                                  input_type.get(),file_id.get(),
                                                  output_dir.get(),
                                                  dur_type.get()),
                      state="disabled")  # Menu option to pop up figure

# #view_menu.add_separator()
# #getcum(pivoted,nper, dat='',sta='', dirout='', saveas=True)
# #view_menu.add_command(label="Duration Distribution", command=show_figure)  # Menu option to pop up figure
# #view_menu.add_separator()

# #view_menu.add_command(label="Rainfall events", command=lambda:getcum(pivoted,nper, dat='',sta='', dirout='', saveas=True))
menu_bar.add_cascade(label="Plot", menu=view_menu)

about_menu = tk.Menu(menu_bar, tearoff=0)
about_menu.add_command(label="License", command=lambda: _show_license(root))
about_menu.add_command(label="Help", command=lambda: webbrowser.open("https://github.com/vempi/VRain.exe/blob/main/help/vrainstorm_v1.md"))
about_menu.add_separator()
about_menu.add_command(label="Website", command=lambda: webbrowser.open("https://vempi.staff.ugm.ac.id"))
menu_bar.add_cascade(label="About", menu=about_menu)

def _show_license(parent):
    win = tk.Toplevel(parent)
    win.title("Software License Agreement")
    win.geometry("600x380")
    text = tk.Text(win, wrap="word", width=70, height=20)
    text.insert("1.0", LICENSE_TEXT)
    text.insert("end", "vempi.staff.ugm.ac.id", "link")
    text.insert("end", "  |  vempi@ugm.ac.id\n")
    text.tag_configure("link", foreground="blue", underline=True)
    text.tag_bind("link", "<Button-1>", lambda e: webbrowser.open("https://vempi.staff.ugm.ac.id"))
    text.config(state="disabled")
    text.pack(padx=10, pady=10, fill="both", expand=True)
    tk.Button(win, text="OK", command=win.destroy).pack(pady=8)

process_button = tk.Button(process_frame, text="Process Data", 
                           command=lambda: process_data(input_dir_entry.get(),
                                                        par_thresh.get(), input_type.get(),
                                                        thresh_type.get(),
                                                        file_id.get(), output_dir.get(),
                                                        float(par_rainmin.get()),
                                                        dur_type.get()),
                           bg="#4682B4", fg='white')

process_button.pack(side="left", padx=5, pady=5)
reset_button = tk.Button(process_frame, text="Reset Plot", command=reset)
reset_button.pack(side="left", padx=5, pady=5)

exit_button = tk.Button(process_frame, text="Check Saved Files", command=lambda:open_directory(output_dir.get()))
exit_button.pack(side="left", padx=5, pady=5)

# Section: Dashboard
log_frame = tk.LabelFrame(frame, text="Progress Log")
log_frame.pack(pady=5, fill="x", expand=False)

# Section: Results
status_label1 = tk.Label(log_frame, text="Step 1. Reading file: N/A", font=("Arial", 9), fg="red");status_label1.pack(pady=1)
status_label2 = tk.Label(log_frame, text="Step 2. Preprocess data: N/A", font=("Arial", 9), fg="red");status_label2.pack(pady=1)
status_label3 = tk.Label(log_frame, text="Step 3. Group rainfall event: N/A", font=("Arial", 9), fg="red");status_label3.pack(pady=1)
status_label4 = tk.Label(log_frame, text="Step 4. Get duration pattern: N/A", font=("Arial", 9), fg="red");status_label4.pack(pady=1)
status_label5 = tk.Label(log_frame, text="Step 5. Write outputs: N/A", font=("Arial", 9), fg="red");status_label5.pack(pady=1)

duration_label = tk.Label(log_frame, text="Dominant storm duration: (hours): N/A", font=("Arial", 10))
duration_label.pack(pady=5)


dashboard_frame = tk.LabelFrame(frame, text="Plot Dashboard")
dashboard_frame.pack(pady=5, fill="y", expand=False)

# Status bar
status_var = tk.StringVar(value="Ready  —  Load a file or click Demo to get started.")
tk.Label(root, textvariable=status_var, anchor="w",
         relief=tk.SUNKEN, fg="gray", font=("Arial", 8),
         bd=1).pack(fill=tk.X, side=tk.BOTTOM)

root.mainloop()