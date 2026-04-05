![image](https://github.com/user-attachments/assets/8d94b93a-a78b-4e19-9e43-fb07bd440a7a)

# VRain — Rainfall Analysis Suite

(c) Developed by [vempi](https://github.com/vempi). Publicly available for use without restrictions or charges.  
By downloading the software, the user accepts full responsibility for its use.

Intended for hydrology and water resources practitioners:
students, teachers, researchers, hydrologists, water resources engineers, and policy makers.

---

## Programs

| Program | Description |
|---|---|
| **VRainPrep** | Rainfall data pre-processing (quality check, gap-filling, format conversion) |
| **VRainStorm** | Storm event analysis and design storm derivation |
| **VRainThiessen** | Thiessen polygon weighted-average areal rainfall |
| **VRainFreq** | Rainfall frequency analysis (IDF curves, return periods, distribution fitting) |

---

## Download (Windows EXE)

> **Go to [Releases](https://github.com/vempi/VRain/releases) to download the latest compiled executables.**  
> No Python installation required.

---

## Run from Source

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
```

```bash
python src/VRainPrep.py
python src/VRainStorm.py
python src/VRainThiessen.py
python src/VRainFreq.py
```

---

## Build EXE

```bash
python -m venv venv_build
venv_build\Scripts\pip install -r requirements.txt pyinstaller
cd build
build_exe.bat
```

Output EXEs will be in `dist/`.

---

## Repository Structure

```
VRain/
├── src/          # Main source files
├── assets/       # Application icons
├── build/        # PyInstaller spec files & build script
├── demo/         # Sample input data
├── help/         # User manuals
└── archive/      # Legacy / old versions
```

---

## User Manuals

See the [help/](help/) folder for user manuals (EN & ID).  
Demo data available in [demo/](demo/).
