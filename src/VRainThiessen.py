import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, MultiPolygon, shape
from shapely.ops import unary_union
from scipy.spatial import Voronoi
import os
import sys
import subprocess
import webbrowser

def _base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))
import shapefile
from pyproj import Transformer
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ─────────────────────────────── Shared utilities ────────────────────────────

LICENSE_TEXT = (
    "VRain | Thiessen Polygon Generator (VRainThiessen) v.1\n\n"
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

# ===================== Shapefile helper functions ===================== #

def _read_shp(path):
    sf = shapefile.Reader(path)
    fields = [f[0] for f in sf.fields[1:]]
    records = []
    for sr in sf.shapeRecords():
        rec = dict(zip(fields, sr.record))
        rec['geometry'] = shape(sr.shape.__geo_interface__)
        records.append(rec)
    return records

def _epsg_int(crs_str):
    return int(crs_str.split(':')[1])

def _transform_geom(geom, t):
    if geom.geom_type == 'Point':
        x, y = t.transform(geom.x, geom.y)
        return Point(x, y)
    elif geom.geom_type == 'Polygon':
        ext = [t.transform(x, y) for x, y in geom.exterior.coords]
        ints = [[t.transform(x, y) for x, y in ring.coords] for ring in geom.interiors]
        return Polygon(ext, ints)
    elif geom.geom_type == 'MultiPolygon':
        return MultiPolygon([_transform_geom(p, t) for p in geom.geoms])
    return geom

def _to_crs(records, from_crs, to_crs):
    if from_crs == to_crs:
        return [r.copy() for r in records]
    t = Transformer.from_crs(_epsg_int(from_crs), _epsg_int(to_crs), always_xy=True)
    return [{**r, 'geometry': _transform_geom(r['geometry'], t)} for r in records]

def _total_bounds(records):
    xs, ys = [], []
    for r in records:
        b = r['geometry'].bounds
        xs += [b[0], b[2]]; ys += [b[1], b[3]]
    return min(xs), min(ys), max(xs), max(ys)

def _clip(records, boundary_records):
    boundary_union = unary_union([r['geometry'] for r in boundary_records])
    out = []
    for r in records:
        clipped = r['geometry'].intersection(boundary_union)
        if not clipped.is_empty:
            out.append({**r, 'geometry': clipped})
    return out

def _sjoin_within(points, polygons):
    result = []
    for pt in points:
        nr = pt.copy()
        for pg in polygons:
            if pg['geometry'].contains(pt['geometry']):
                nr.update({k: v for k, v in pg.items() if k != 'geometry'})
                break
        result.append(nr)
    return result

def _plot_records(ax, records, point=False, color='none', edgecolor='black',
                  markersize=8, linewidth=0.8, label=''):
    if point:
        xs = [r['geometry'].x for r in records]
        ys = [r['geometry'].y for r in records]
        ax.plot(xs, ys, 'o', color='red' if color == 'none' else color,
                markersize=markersize, linestyle='', label=label)
    else:
        patches = []
        for r in records:
            g = r['geometry']
            polys = list(g.geoms) if g.geom_type == 'MultiPolygon' else [g]
            for poly in polys:
                coords = np.array(poly.exterior.coords)
                patches.append(mpatches.Polygon(coords, closed=True))
        pc = PatchCollection(patches, facecolor=color, edgecolor=edgecolor,
                             linewidth=linewidth, label=label)
        ax.add_collection(pc)
        ax.autoscale()

def _save_shp(records, path):
    if not records:
        return
    g0 = records[0]['geometry']
    shp_type = shapefile.POINT if 'Point' in g0.geom_type else shapefile.POLYGON
    w = shapefile.Writer(path, shp_type)
    cols = [k for k in records[0] if k != 'geometry']
    for col in cols:
        w.field(str(col)[:10], 'C', 100)
    for r in records:
        g = r['geometry']
        if 'Point' in g.geom_type:
            w.point(g.x, g.y)
        else:
            polys = list(g.geoms) if g.geom_type == 'MultiPolygon' else [g]
            w.poly([list(p.exterior.coords) for p in polys])
        w.record(*[str(r.get(c, '')) for c in cols])
    w.close()


# ===================== Main Application Class ===================== #

class ThiessenApp:
    def __init__(self, root):

        self.root = root
        self.root.title("VRain | Thiessen Polygon Generator (VRainThiessen) v.1")
        self.root.geometry("800x600")

        # Create Menu Bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Load Demo", command=self.load_demo)
        self.file_menu.add_command(label="Open Output", command=lambda: self.open_directory(self.save_dir), state='disabled')
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Plot Style Menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Default", command=lambda: self.set_plot_style('classic'))
        self.edit_menu.add_command(label="Seaborn", command=lambda: self.set_plot_style('seaborn'))
        self.edit_menu.add_command(label="Grayscale", command=lambda: self.set_plot_style('grayscale'))
        self.edit_menu.add_command(label="Solarize", command=lambda: self.set_plot_style('Solarize_Light2'))
        self.edit_menu.add_command(label="ggplot", command=lambda: self.set_plot_style('ggplot'))
        self.edit_menu.add_command(label="BMH", command=lambda: self.set_plot_style('bmh'))
        self.edit_menu.add_command(label="Fivethirtyeight", command=lambda: self.set_plot_style('fivethirtyeight'))
        self.edit_menu.add_command(label="Color blind", command=lambda: self.set_plot_style('tableau-colorblind10'))
        self.menu_bar.add_cascade(label="Plot Style", menu=self.edit_menu)

        # About Menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="License", command=self.show_license)
        self.help_menu.add_command(label="Help", command=lambda: webbrowser.open("https://github.com/vempi/VRain.exe/blob/main/help/vrainthiessen_v1.md"))
        self.help_menu.add_separator()
        self.help_menu.add_command(label="Website", command=lambda: webbrowser.open("https://vempi.staff.ugm.ac.id"))
        self.menu_bar.add_cascade(label="About", menu=self.help_menu)

        # Header
        hdr = tk.Frame(root, bg="#4682B4", pady=6)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="VRain  |  Thiessen Polygon Generator  (VRainThiessen)",
                 font=("Arial", 12, "bold"), bg="#4682B4", fg="white").pack()
        tk.Label(hdr, text="Compute Thiessen/Voronoi weights for areal rainfall",
                 font=("Arial", 9), bg="#4682B4", fg="#d0e8f8").pack()

        # Status bar (created early, packed last via side=BOTTOM)
        self.status_var = tk.StringVar(value="Ready  —  Load a shapefile and station CSV/XLSX, or click Demo.")
        self._statusbar = tk.Label(root, textvariable=self.status_var, anchor="w",
                                   relief=tk.SUNKEN, fg="gray", font=("Arial", 8), bd=1)
        self._statusbar.pack(fill=tk.X, side=tk.BOTTOM)

        # Main Container Frame
        self.main_frame = tk.Frame(root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Input Frame
        self.input_frame = tk.LabelFrame(self.main_frame, text="Input Files", padx=10, pady=10)
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)

        # Shapefile Input
        self.label_shapefile = tk.Label(self.input_frame, text="Shapefile Area:")
        self.label_shapefile.grid(row=0, column=0, sticky="w")

        self.shapefile_path = tk.StringVar()
        self.entry_shapefile = tk.Entry(self.input_frame, textvariable=self.shapefile_path, width=50, state="normal")
        self.entry_shapefile.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        self.btn_shapefile = tk.Button(self.input_frame, text="Browse", command=self.load_shapefile)
        self.btn_shapefile.grid(row=0, column=2, sticky="w")

        # CSV / XLSX Input
        self.label_csv = tk.Label(self.input_frame, text="Station file (CSV/XLSX/SHP):")
        self.label_csv.grid(row=2, column=0, sticky="w")

        self.points_path = tk.StringVar()
        self.entry_points = tk.Entry(self.input_frame, textvariable=self.points_path, width=50, state="normal")
        self.entry_points.grid(row=2, column=1, padx=5, pady=5, sticky="e")

        btn_row2 = tk.Frame(self.input_frame)
        btn_row2.grid(row=2, column=2, sticky="w", padx=2)
        tk.Button(btn_row2, text="Browse", command=self.load_csv).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row2, text="Demo", command=self.load_demo, bg="#e8f4f8").pack(side=tk.LEFT, padx=2)

        self.btn_example = tk.Button(self.input_frame, text="See format", command=self.show_example)
        self.btn_example.grid(row=1, column=2, sticky="e")

        # CRS Selection
        self.crs_options = {"LatLon (EPSG:4326)": "EPSG:4326", "Web Mercator (EPSG:3857)": "EPSG:3857",
                            "UTM Zone 49S (EPSG:32749)": "EPSG:32749"}

        self.label_crs = tk.Label(self.input_frame, text="Select CRS (CSV coordinate):")
        self.label_crs.grid(row=1, column=0, sticky="w")
        self.crs_var = tk.StringVar()
        self.crs_dropdown = ttk.Combobox(self.input_frame, textvariable=self.crs_var, values=list(self.crs_options.keys()))
        self.crs_dropdown.set("LatLon (EPSG:4326)")
        self.crs_dropdown.grid(row=1, column=1, pady=5, sticky="e")

        # Action Buttons
        self.output_frame = tk.LabelFrame(self.main_frame, text="Output Files", padx=10, pady=10)
        self.output_frame.pack(fill=tk.X, padx=5, pady=5)

        self.label_out_crs = tk.Label(self.output_frame, text="Select CRS output:")
        self.label_out_crs.grid(row=0, column=0, sticky="w")
        self.out_crs_var = tk.StringVar()
        self.out_crs_dropdown = ttk.Combobox(self.output_frame, textvariable=self.out_crs_var, values=list(self.crs_options.keys()))
        self.out_crs_dropdown.set("LatLon (EPSG:4326)")
        self.out_crs_dropdown.grid(row=0, column=1, pady=5, sticky="e")

        self.button_frame = tk.Frame(self.main_frame, pady=10)
        self.button_frame.pack(fill=tk.X)

        self.btn_generate = tk.Button(self.button_frame, text="Generate Thiessen Polygons",
                                      command=self.generate_polygons, bg="#4682B4", fg='white')
        self.btn_generate.pack(side=tk.LEFT, padx=5)

        self.btn_save = tk.Button(self.button_frame, text="Save Outputs", command=self.save_outputs)
        self.btn_save.pack(side=tk.LEFT, padx=5)

        self.btn_reset = tk.Button(self.button_frame, text="Reset", command=self.reset_data)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        # Plot Frame
        self.plot_frame = tk.LabelFrame(self.main_frame, text="Visualization", padx=10, pady=10)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.counties = None
        self.counties_crs = "EPSG:4326"
        self.rainfall = None
        self.rainfall_crs = "EPSG:4326"
        self.tp_polys_clipped = None
        self.plot_style = 'default'
        self.out_dir_var = ''

    def load_shapefile(self):
        file_path = filedialog.askopenfilename(filetypes=[("Shapefiles", "*.shp")])
        if file_path:
            self.shapefile_path.set(file_path)
            self.counties = _read_shp(file_path)
            self.counties_crs = "EPSG:4326"  # default; ideally read from .prj
            messagebox.showinfo("Sukses", f"Shapefile berhasil dimuat dengan CRS: {self.counties_crs}")

            plt.style.use(self.plot_style)
            fig, ax = plt.subplots(figsize=(10, 10))
            _plot_records(ax, self.counties, color='none', edgecolor='black', label='Catchment area')
            ax.set_title("Area Boundary")
            ax.set_xlabel("X"); ax.set_ylabel('Y')
            for widget in self.plot_frame.winfo_children(): widget.destroy()
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def load_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Data files", "*.csv *.xlsx *.xls *.shp"),
                       ("CSV files", "*.csv"),
                       ("Excel files", "*.xlsx *.xls"),
                       ("Shapefiles", "*.shp"),
                       ("All files", "*.*")])
        if file_path:
            self.points_path.set(file_path)
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ('.csv', '.xlsx', '.xls'):
                df = smart_read(file_path)
                xcol = detect_col(df, ['x', 'lon', 'longitude', 'bujur', 'east'], fallback_idx=1)
                ycol = detect_col(df, ['y', 'lat', 'latitude', 'lintang', 'north'], fallback_idx=2)
                ncol = detect_col(df, ['name', 'nama', 'station', 'stasiun', 'id'], fallback_idx=0)
                selected_crs = self.crs_options.get(self.crs_var.get(), "EPSG:4326")
                self.rainfall = [{'name': str(row[ncol]),
                                  'geometry': Point(float(row[xcol]), float(row[ycol])),
                                  **{k: row[k] for k in df.columns if k not in [xcol, ycol]}}
                                 for i, row in df.iterrows()]
                self.rainfall_crs = selected_crs
                self.status_var.set(
                    f"Station file loaded: {os.path.basename(file_path)}  "
                    f"(name={ncol}, x={xcol}, y={ycol})")
            else:
                self.rainfall = _read_shp(file_path)
                self.rainfall_crs = "EPSG:4326"

            if self.counties is not None:
                self.rainfall = _to_crs(self.rainfall, self.rainfall_crs, self.counties_crs)
                messagebox.showinfo("Sukses", f"Data berhasil dimuat dan dikonversi ke CRS: {self.counties_crs}")

                plt.style.use(self.plot_style)
                fig, ax = plt.subplots(figsize=(10, 10))
                _plot_records(ax, self.counties, color='none', edgecolor='black', label='Catchment area')
                _plot_records(ax, self.rainfall, point=True, color='red', markersize=8, label="Rainfall stations")
                ax.set_title("Station Locations")
                ax.set_xlabel("X"); ax.set_ylabel('Y')
                for widget in self.plot_frame.winfo_children(): widget.destroy()
                canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def set_plot_style(self, style):
        self.plot_style = style

    def generate_polygons(self):
        if self.counties is None or self.rainfall is None:
            messagebox.showerror("Error", "Harap muat file shapefile dan CSV terlebih dahulu!")
            return

        x = [r['geometry'].x for r in self.rainfall]
        y = [r['geometry'].y for r in self.rainfall]
        coords = list(zip(x, y))
        min_x, min_y, max_x, max_y = _total_bounds(self.counties)
        buffer = max(max_x - min_x, max_y - min_y)
        coords_tp = coords + [[min_x - buffer, min_y - buffer], [max_x + buffer, min_y - buffer],
                              [max_x + buffer, max_y + buffer], [min_x - buffer, max_y + buffer]]

        tp = Voronoi(coords_tp)
        tp_poly_list = []

        for region in tp.regions:
            if -1 in region or len(region) == 0:
                continue
            poly = Polygon([tp.vertices[i] for i in region])
            tp_poly_list.append({'geometry': poly})

        self.tp_polys_clipped = _clip(tp_poly_list, self.counties)
        total_county_area = sum(r['geometry'].area for r in self.counties)
        for r in self.tp_polys_clipped:
            r['Area'] = r['geometry'].area
            r['Weight'] = r['geometry'].area / total_county_area

        self.rainfall = _sjoin_within(self.rainfall, self.tp_polys_clipped)

        # Reproject to output CRS
        selected_out_crs = self.crs_options.get(self.out_crs_var.get(), "EPSG:4326")
        self.tp_polys_clipped = _to_crs(self.tp_polys_clipped, self.counties_crs, selected_out_crs)
        self.rainfall = _to_crs(self.rainfall, self.counties_crs, selected_out_crs)
        self.counties = _to_crs(self.counties, self.counties_crs, selected_out_crs)
        self.counties_crs = selected_out_crs

        plt.style.use(self.plot_style)
        fig, ax = plt.subplots(figsize=(10, 10))
        _plot_records(ax, self.counties, color='none', edgecolor='black', label='Catchment area')
        _plot_records(ax, self.tp_polys_clipped, color='white', edgecolor='black', linewidth=0.5, label='Thiessen Polygon')
        _plot_records(ax, self.rainfall, point=True, color='red', markersize=8, label="Rainfall stations")
        ax.set_title(f"Station Locations & Thiessen Polygons ({selected_out_crs})")
        ax.set_xlabel("X")
        ax.set_ylabel('Y')
        ax.legend()

        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        messagebox.showinfo("Sukses", f"Thiessen polygons generated in CRS: {selected_out_crs}!")

    def save_outputs(self):
        if self.tp_polys_clipped is None or self.rainfall is None:
            messagebox.showerror("Error", "Tidak ada data untuk disimpan!")
            return

        self.save_dir = filedialog.askdirectory()

        if self.save_dir:
            _save_shp(self.tp_polys_clipped, os.path.join(self.save_dir, "Thiessen_Polygons.shp"))
            df_out = pd.DataFrame([{k: v for k, v in r.items() if k != 'geometry'} for r in self.rainfall])
            df_out.to_csv(os.path.join(self.save_dir, "Rainfall_Stations_With_Weights.csv"), index=False)
            self.file_menu.entryconfig("Open Output", state="normal")
            messagebox.showinfo("Sukses", f"Data berhasil disimpan pada folder: {self.save_dir}!")

    def show_example(self):
        popup = tk.Toplevel(self.root)
        popup.title("Example Data")
        popup.geometry("300x200")

        tree = ttk.Treeview(popup, columns=("Name", "X", "Y"), show="headings")
        tree.heading("Name", text="Name")
        tree.heading("X", text="X")
        tree.heading("Y", text="Y")

        example_data = pd.DataFrame({
            "name": ["Station1", "Station2", "Station3"],
            "x": [110.0, 110.5, 111.0],
            "y": [-7.5, -7.6, -7.4]
        })

        for index, row in example_data.iterrows():
            tree.insert("", "end", values=(row["name"], row["x"], row["y"]))

        tree.pack(expand=True, fill="both", padx=10, pady=10)

        close_button = tk.Button(popup, text="Close", command=popup.destroy)
        close_button.pack(pady=5)

    def reset_data(self):
        """Reset all loaded data and clear the GUI."""
        self.counties = None
        self.rainfall = None
        self.tp_polys_clipped = None

        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        self.crs_var.set("LatLon (EPSG:4326)")
        self.out_crs_var.set("LatLon (EPSG:4326)")
        self.shapefile_path.set("")
        self.points_path.set("")

        messagebox.showinfo("Reset", "All data has been cleared!")

    def select_output_directory(self):
        """Open a directory selection dialog and store the selected path"""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.out_dir_var.set(folder_selected)

    def load_demo(self):
        demo_path = os.path.join(_base_path(), "demo", "VRainThiessen_demo.csv")
        if os.path.exists(demo_path):
            self.points_path.set(demo_path)
            df = smart_read(demo_path)
            xcol = detect_col(df, ['x', 'lon', 'longitude', 'bujur', 'east'], fallback_idx=1)
            ycol = detect_col(df, ['y', 'lat', 'latitude', 'lintang', 'north'], fallback_idx=2)
            ncol = detect_col(df, ['name', 'nama', 'station', 'stasiun', 'id'], fallback_idx=0)
            selected_crs = self.crs_options.get(self.crs_var.get(), "EPSG:4326")
            self.rainfall = [{'name': str(row[ncol]),
                              'geometry': Point(float(row[xcol]), float(row[ycol])),
                              **{k: row[k] for k in df.columns if k not in [xcol, ycol]}}
                             for i, row in df.iterrows()]
            self.rainfall_crs = selected_crs
            self.status_var.set(
                "Demo station file loaded  —  Provide a boundary shapefile, then click Generate.")
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

    def open_directory(self, path):
        if not os.path.isdir(path):
            messagebox.showerror("Error", "Invalid directory path!")
            return

        try:
            if os.name == "nt":  # Windows
                os.startfile(path)
            elif os.name == "posix":  # macOS & Linux
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open directory:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ThiessenApp(root)
    root.mainloop()
