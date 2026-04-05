


# GUI Setup
root = tk.Tk()
root.title("Preprocess Hourly Rainfall Data (VRainSat) v.1")

# Menu
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open", command=load_csv)
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