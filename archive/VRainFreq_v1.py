import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Secondary x-axis: Probability of Exceedance
def to_prob(x):
    """Convert return period (years) to probability of exceedance (%)"""
    return (1 / x) * 100

# Load data
method = "hazen"  # Pilih metode
num_bins = 10

df = pd.read_csv("D:/OneDrive/Downloads/GSMAP_2001-2048_merged.csv")
data = df['Rain']

# Sort data for plotting positions
data_sorted = np.sort(data)
n = len(data)
rank = np.arange(1, n + 1)

# Pilih metode plotting position
if method == 'weibull':
    prob_exceedance = rank / (n + 1)
elif method == 'gumbel':
    prob_exceedance = (rank - 0.44) / (n + 0.12)
elif method == 'hazen':
    prob_exceedance = (rank - 0.5) / n
elif method == 'blom':
    prob_exceedance = (rank - 0.375) / (n + 0.25)
else:
    raise ValueError("Metode tidak dikenali. Pilih: weibull, gumbel, gringorten, cunnane, hazen, atau blom.")

# Compute statistics
min_val = np.min(data)
max_val = np.max(data)
median_val = np.median(data)
mode_result = stats.mode(data, keepdims=True)  # keepdims ensures it's always an array
mode_val = mode_result.mode[0]  # Extract the first mode value
sample_size = len(data)
mean_val = np.mean(data)
std_dev = np.std(data, ddof=1)
skew_val = stats.skew(data)
kurtosis_val = stats.kurtosis(data, fisher=False)

# Create DataFrame for formatted output
stats_df = pd.DataFrame({
    "Metric": ["Min", "Max", "Median", "Mode", "Sample Size", "Mean", "St Dev", "Skew", "Kurtosis"],
    "Value": [min_val, max_val, median_val, mode_val, sample_size, mean_val, std_dev, skew_val, kurtosis_val]
})


# Fit Distributions
gev_params = stats.genextreme.fit(data)
norm_params = stats.norm.fit(data)
lognorm_params = stats.lognorm.fit(data, floc=0)
gumbel_params = stats.gumbel_r.fit(data)
logpearson_params = stats.pearson3.fit(np.log(data))

# Define return periods with better spacing
returnperiods = np.array([1.1,2, 5, 10, 20, 50, 100, 200])
prob_return = 1 / returnperiods

# Compute return levels
gev_levels = stats.genextreme.ppf(1 - prob_return, *gev_params)
norm_levels = stats.norm.ppf(1 - prob_return, *norm_params)
lognorm_levels = stats.lognorm.ppf(1 - prob_return, *lognorm_params)
gumbel_levels = stats.gumbel_r.ppf(1 - prob_return, *gumbel_params)
logpearson_levels = np.exp(stats.pearson3.ppf(1 - prob_return, *logpearson_params))

shape, loc, scale = gev_params
gev_conf_5 = stats.genextreme.ppf(1 - prob_return, shape, loc, scale * 0.9)
gev_conf_95 = stats.genextreme.ppf(1 - prob_return, shape, loc, scale * 1.1)

# Perform statistical tests
ks_results = {
    "GEV": stats.kstest(data, 'genextreme', args=gev_params),
    "Normal": stats.kstest(data, 'norm', args=norm_params),
    "Log-Normal": stats.kstest(data, 'lognorm', args=lognorm_params),
    "Gumbel": stats.kstest(data, 'gumbel_r', args=gumbel_params),
    "Log-Pearson III": stats.kstest(np.log(data), 'pearson3', args=logpearson_params)
}

# Define bins for chi-square test
hist_obs, bin_edges = np.histogram(data, bins=num_bins)

chi_square = {}
for dist_name, params, dist_func in zip(
    ["GEV", "Normal", "Log-Normal", "Gumbel", "Log-Pearson III"],
    [gev_params, norm_params, lognorm_params, gumbel_params, logpearson_params],
    [stats.genextreme, stats.norm, stats.lognorm, stats.gumbel_r, stats.pearson3]
):
    cdf_vals = dist_func.cdf(bin_edges, *params)
    freqs = n * np.diff(cdf_vals)
    freqs *= hist_obs.sum() / freqs.sum()  # Normalize expected frequencies
    freqs[freqs == 0] = 1e-6  # Avoid zero expected frequencies
    chi_square[dist_name] = stats.chisquare(hist_obs, freqs)

distributions = {"GEV": stats.genextreme,"Normal": stats.norm,"Log-Normal": stats.lognorm,
                 "Gumbel": stats.gumbel_r,"Log-Pearson III": stats.pearson3}

lst_params = {"GEV": gev_params,"Normal": norm_params,"Log-Normal": lognorm_params,
              "Gumbel": gumbel_params,"Log-Pearson III": logpearson_params}

param_str = {
    "Normal": f"Mean={lst_params['Normal'][0]:.3f}, StDv={lst_params['Normal'][1]:.3f}",
    "Log-Normal": f"MeanLog={np.log(lst_params['Log-Normal'][2]):.3f}, StDvLog={lst_params['Log-Normal'][0]:.3f}",
    "Gumbel": f"Loctn={lst_params['Gumbel'][0]:.3f}, Scale={lst_params['Gumbel'][1]:.3f}",
    "Log-Pearson III": f"MeanLog={np.log(lst_params['Log-Pearson III'][1]):.3f}, StDvLog={lst_params['Log-Pearson III'][2]:.3f}",
    "GEV": f"Loctn={lst_params['GEV'][1]:.3f}, Scale={lst_params['GEV'][2]:.3f}, Shape={lst_params['GEV'][0]:.3f}"
}

# Create DataFrame for results
results_pval = pd.DataFrame({
    "Distribution": list(ks_results.keys()),
    "KS Statistic": [res.statistic for res in ks_results.values()],
    "KS p-value": [res.pvalue for res in ks_results.values()],
    "Chi-Square Statistic": [res.statistic for res in chi_square.values()],
    "Chi-Square p-value": [res.pvalue for res in chi_square.values()]
})

# Compute critical KS value (D_crit)
alpha = 0.05  # Significance level

ks_critical = 1.36 / np.sqrt(n)  # KS critical value for alpha=0.05

# Compute critical Chi-Square value
df_chi = num_bins - 1 - len(lst_params["Normal"])  # Degrees of freedom correction
chi_critical = stats.chi2.ppf(1 - alpha, df_chi)

# Create DataFrame for results
results_cr = pd.DataFrame({
    "Distribution": list(distributions.keys()),
    "Χ²": [chi_square[name].statistic for name in distributions.keys()],
    "Χ²_crit": [chi_critical] * len(distributions),
    "Chi Result": ["Accepted" if chi_square[name].statistic < chi_critical else "Rejected" for name in distributions.keys()],
    "Δ_max": [ks_results[name].statistic for name in distributions.keys()],
    "Δ_crit": [ks_critical] * len(distributions),
    "KS Result": ["Accepted" if ks_results[name].statistic < ks_critical else "Rejected" for name in distributions.keys()]
})

return_df = pd.DataFrame({"Return period": returnperiods, "Probability":prob_return,
                          "Normal (Median)": norm_levels,
                          "Log-Normal (Median)": lognorm_levels,
                          "Gumbel (Median)": gumbel_levels,
                          "Log-Pearson III (Median)": logpearson_levels,
                          "GEV (Median)": gev_levels})


# Compute reduced variate for observed events (Gumbel EV1)
z_obs = -np.log(-np.log(prob_exceedance))  # Corrected formula
z_gev = -np.log(-np.log(1 - prob_return))

# Ensure lengths match by interpolating or selecting fewer ticks
sel_idx = np.linspace(0, len(z_gev) - 1, len(returnperiods), dtype=int)
sel_z = z_gev[sel_idx]

sel_ret = returnperiods[sel_idx]

#z_min, z_max = z_gev[0], z_gev[-1]
#log_range = np.logspace(np.log10(z_min + offset), np.log10(z_max + offset), base=10) - offset

prob_labels = to_prob(returnperiods)

P_exceedance = np.arange(np.ceil(prob_labels[-1]), np.floor(prob_labels[0]) + 1, 1, dtype=int)/100
prob_scale = -np.log(-np.log(1 - P_exceedance))

#xscale = z_obs
#xscale = log_range
xscale = prob_scale

# Plot setup
fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.plot(z_obs, data_sorted, 'o', mfc='w', mec='k', mew=1.5, label='Observed Events')
ax1.plot(z_gev, gev_levels, 'r-', label='GEV')
ax1.plot(z_gev, norm_levels, 'b-', label='Normal')
ax1.plot(z_gev, lognorm_levels, 'g-', label='Log-Normal')
ax1.plot(z_gev, gumbel_levels, 'm-', label='Gumbel')
ax1.plot(z_gev, logpearson_levels, 'c-', label='Log-Pearson III')
#ax1.plot(z_gev, gev_conf_5, 'k--', label='GEV 5% CI')
#ax1.plot(z_gev, gev_conf_95, 'k--', label='GEV 95% CI')

ax1.fill_between(z_gev, gev_conf_5, gev_conf_95, color='gray', alpha=0.3, label='GEV 90% CI')

# Primary x-axis: Return Period
ax1.set_xlabel("Return Period (years)")
ax1.set_xticks(sel_z)
ret_str = [str(x) if x % 1 != 0 else str(int(x)) for x in sel_ret]
ax1.set_xticklabels(ret_str )  # Ensure they are strings
ax1.set_ylabel("Precipitation (mm)")
ax1.yaxis.set_major_locator(ticker.MultipleLocator(10))
ax1.set_title("Frequency Analysis of Rainfall Data (Gumbel Reduced Variate)")
ax1.legend()
ax1.grid(True, which="both", linestyle="-", linewidth=1, alpha=0.5)

for xv in xscale:
    ax1.axvline(xv, color='gray', linestyle="-", alpha=0.3, linewidth=0.5, zorder=0)

ax2 = ax1.twiny()
ax2.set_xlim(ax1.get_xlim())  # Ensure both x-axes have the same range
ax2.set_xlabel("Probability of Exceedance (%)")
ax2.set_xticks(z_gev)
ax2.set_xticklabels([f"{p:.1f}%" for p in prob_labels])

plt.show()

# ============================ QQ Plot

# Plot setup
fig, ax = plt.subplots(1, 1, figsize=(8, 6))

# Histogram and PDF Plot
#num_bins = 10
#hist_data, bins, _ = ax.hist(data, bins=num_bins, density=True, alpha=0.6, color='b', label='Data Frequency')

step = 2.5
bin_edges = np.arange(data.min(), data.max() + step, step)

hist_data, bins, _ = ax.hist(data, bins=bin_edges, density=True, alpha=0.6, color='b', label='Data Frequency')

xmin, xmax = ax.get_xlim()
x = np.linspace(xmin, xmax, 100)

for name, dist in {
    "Normal": stats.norm,
    "Log-Normal": stats.lognorm,
    "Gumbel": stats.gumbel_r,
    "GEV": stats.genextreme,
    "Log-Pearson III": stats.pearson3
}.items():
    params = dist.fit(data)
    pdf_fitted = dist.pdf(x, *params)
    ax.plot(x, pdf_fitted, label=f'{name} Fitted Curve')

ax.set_title("PDF with Histogram for Multiple Distributions")
ax.set_xlabel("Rainfall (mm)")
ax.set_ylabel("Density")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.show()

# QQ-Plot
for name, dist in {
    "Normal": stats.norm,
    "Log-Normal": stats.lognorm,
    "Gumbel": stats.gumbel_r,
    "GEV": stats.genextreme,
    "Log-Pearson III": stats.pearson3
}.items():
    params = dist.fit(data)
    if name == "Log-Normal":
        shape, loc, scale = params
        stats.probplot(data, dist=dist, sparams=(shape, loc, scale), plot=ax)
    elif name in ["GEV", "Log-Pearson III"]:
        shape, loc, scale = params
        stats.probplot(data, dist=dist, sparams=(shape, loc, scale), plot=ax)
    else:
        stats.probplot(data, dist=dist, sparams=params, plot=ax)
ax.set_title("QQ-Plot for Multiple Distributions")
ax.grid(True, linestyle='--', alpha=0.6)

