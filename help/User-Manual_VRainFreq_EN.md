# VRainFreq User Manual

Welcome to the **VRainFreq** (Frequency Analysis Tool) user manual. This document provides a comprehensive guide on how to use the VRainFreq software for frequency analysis of hydrological or meteorological data. The tool is designed to help users analyze and visualize data using various statistical methods and distributions.

---

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [User Interface Overview](#user-interface-overview)
5. [Loading Data](#loading-data)
6. [Performing Frequency Analysis](#performing-frequency-analysis)
7. [Batch Analysis](#batch-analysis)
8. [Visualizing Results](#visualizing-results)
9. [Exporting Results](#exporting-results)
10. [License](#license)
11. [Troubleshooting](#troubleshooting)

---

## Introduction

VRainFreq is a Python-based application designed for frequency analysis of hydrological or meteorological data. It supports various statistical methods (e.g., Weibull, Cunnane, Hazen, Gringorten, Blom, Tukey) and probability distributions (e.g., GEV, Normal, Log-Normal, Gumbel, Log-Pearson III). The tool provides both graphical and tabular outputs for easy interpretation of results.

---

## Installation

### Prerequisites
- Python 3.7 or higher
- Required Python libraries: `pandas`, `numpy`, `matplotlib`, `scipy`, `tkinter`

### Installation Steps
1. **Install Python**: Download and install Python from [python.org](https://www.python.org/).
2. **Install Required Libraries**:
   Open a terminal or command prompt and run the following commands:
   ```bash
   pip install pandas numpy matplotlib scipy
   ```
3. **Download VRainFreq**:
   - Clone the repository or download the script file.
   - Ensure the script is saved as `VRainFreq.py`.

4. **Run the Application**:
   - Navigate to the directory containing `VRainFreq.py`.
   - Run the script using Python:
     ```bash
     python VRainFreq.py
     ```

---

## Getting Started

Once the application is running, you will see the main window with the title **"VRain | Frequency Analysis Tool (VRainFreq v.1)"**. The interface is divided into two main sections:
- **Left Panel**: Input controls and statistics table.
- **Right Panel**: Graphical outputs (plots).

---

## User Interface Overview

### Menu Bar
- **File**:
  - **Open**: Load a single file or multiple files for batch analysis.
  - **Exit**: Close the application.
- **Help**:
  - **License**: View the software license agreement.

### Left Panel
- **Enable Batch Analysis**: Check this option to analyze multiple files in a folder.
- **Browse**: Select a file or folder containing data.
- **Column Selection**: Choose the column to analyze (for single file mode).
- **Method Selection**: Choose the statistical method for frequency analysis.
- **Significance Level (α)**: Set the significance level for statistical tests.
- **Return Periods**: Enter return periods for analysis (comma-separated values).
- **Output Directory**: Set the directory to save results (optional).
- **Run Frequency Analysis**: Perform analysis on the selected data.
- **Batch Run**: Perform analysis on all columns in the loaded dataset.

### Right Panel
- **Frequency Plot**: Displays the frequency analysis plot.
- **Histogram with PDF**: Displays the histogram with fitted probability density functions.

---

## Loading Data

### Single File Mode
1. Uncheck **Enable Batch Analysis**.
2. Click **Browse** and select a CSV or Excel file.
3. Select the column to analyze from the dropdown menu.

### Batch Mode
1. Check **Enable Batch Analysis**.
2. Click **Browse** and select a folder containing CSV or Excel files.
3. The tool will merge all files into a single dataset for analysis.

---

## Performing Frequency Analysis

1. **Select Method**: Choose a statistical method from the dropdown (e.g., Gringorten).
2. **Set Return Periods**: Enter return periods (e.g., `1.1,5,10,20,50,100,200`).
3. **Set Significance Level**: Choose a significance level (e.g., 0.05).
4. **Run Analysis**:
   - For single column analysis, click **Run Frequency Analysis**.
   - For batch analysis, click **Batch Run**.

---

## Batch Analysis

In batch mode, the tool will:
1. Merge all files in the selected folder.
2. Perform frequency analysis on each column.
3. Save results for each column in the output directory.

---

## Visualizing Results

### Frequency Plot
- Displays observed data and fitted distributions.
- Includes confidence intervals for the GEV distribution.
- Annotations provide GEV parameters and scaling information.

### Histogram with PDF
- Displays the histogram of the data.
- Overlays fitted probability density functions for comparison.

---

## Exporting Results

The tool automatically saves the following files in the output directory:
1. **VRain_ks_{station_name}.csv**: Kolmogorov-Smirnov test results.
2. **VRain_chi-square_{station_name}.csv**: Chi-square test results.
3. **VRain_return-levels_{station_name}.csv**: Return levels for selected return periods.
4. **VRain_stat_{station_name}.csv**: Summary statistics.
5. **VRain_Distribution-plot_{station_name}.png**: Frequency plot.
6. **VRain_Histogram-plot_{station_name}.png**: Histogram with PDF.

---

## License

The software is provided under the following license agreement:
- **Copyright**: © 2025 Vempi Satriya Adi Hendrawan.
- **Permissions**: Free for educational and commercial use.
- **Restrictions**: Redistribution, modification, or sale of the software is prohibited without permission.
- **Disclaimer**: The software is provided "as is" without warranties. The developer is not responsible for any damages.

For inquiries, contact:  
**vempi@ugm.ac.id** | **vempi.staff.ugm.ac.id**

---

## Troubleshooting

### Common Issues
1. **File Not Loaded**:
   - Ensure the file path is correct.
   - Check if the file format is supported (CSV or Excel).

2. **Memory Error**:
   - Reduce the dataset size or split the data into smaller files.

3. **Invalid Input**:
   - Ensure return periods are entered as comma-separated values (e.g., `1,5,10`).

4. **Plotting Errors**:
   - Check if the data contains missing or invalid values.

### Contact Support
For additional support, contact the developer at **vempi@ugm.ac.id**.

---

Thank you for using VRainFreq! We hope this tool helps you in your frequency analysis tasks.
