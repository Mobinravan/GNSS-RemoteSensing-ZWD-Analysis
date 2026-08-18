# Phobos
# Code: Phobos - Mobin Ravan

import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta

# =================
# 1. Load VMF3 data
# ==================
vmf3_file = r'C:\Users\PARSIAN-IT\Desktop\GNSSRS_Proj\ALBH_VMF3_2025_DOY244_334.csv'
vmf3_data = pd.read_csv(vmf3_file)

# Extract ZWD for DOY 244
doy_target = 244
vmf3_row = vmf3_data[vmf3_data['DOY'] == doy_target]

if len(vmf3_row) == 0:
    print(f"ERROR: No data found for DOY {doy_target} in VMF3 file!")
    exit()

zwd_vmf3_m = vmf3_row['ZWD'].values[0]
zwd_vmf3_mm = zwd_vmf3_m * 1000

pressure_vmf3 = vmf3_row['Pressure'].values[0]
temp_vmf3 = vmf3_row['Temp'].values[0]

print("="*80)
print("VMF3 Data for DOY 244:")
print("="*80)
print(f"  ZWD = {zwd_vmf3_mm:.2f} mm")
print(f"  Surface Pressure = {pressure_vmf3:.2f} hPa")
print(f"  Surface Temperature = {temp_vmf3:.2f} deg C")

# ============================================
# 2. Load closest COSMIC-2 file for DOY 244
# ============================================
cosmic_folder = r'C:\Users\PARSIAN-IT\Desktop\wetPf2_nrt_2025_244'
files = [f for f in os.listdir(cosmic_folder) if f.endswith('_nc')]

print(f"\nTotal COSMIC-2 files for DOY 244: {len(files)}")

LAT_ALBH = 48.39
LON_ALBH = -123.68

closest_file = None
min_distance = float('inf')
closest_lat = None
closest_lon = None
ds_best = None

for file in files:
    file_path = os.path.join(cosmic_folder, file)
    try:
        ds = xr.open_dataset(file_path)
        
        if 'lat' in ds.attrs and 'lon' in ds.attrs:
            lat_str = ds.attrs['lat'].split(',')[0].strip()
            lon_str = ds.attrs['lon'].split(',')[0].strip()
            lat = float(lat_str)
            lon = float(lon_str)
            
            distance = np.sqrt((lat - LAT_ALBH)**2 + (lon - LON_ALBH)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_file = file_path
                closest_lat = lat
                closest_lon = lon
                ds_best = ds
        
        ds.close()
    except Exception as e:
        continue

if closest_file is None:
    print("ERROR: No valid COSMIC-2 file found for DOY 244!")
    exit()

print(f"\nClosest COSMIC-2 file:")
print(f"  File: {os.path.basename(closest_file)}")
print(f"  Latitude: {closest_lat:.4f} deg")
print(f"  Longitude: {closest_lon:.4f} deg")
print(f"  Distance from ALBH: {min_distance:.4f} degrees")

# ============================================
# 3. Extract COSMIC-2 profile and compute ZWD
# ============================================
height = ds_best.MSL_alt.values
temp = ds_best.Temp.values
pressure = ds_best.Pres.values
vapor = ds_best.Vp.values
rel_humidity = ds_best.rh.values
refractivity = ds_best.ref.values

height_m = height * 1000
C2 = 71.6
C3 = 3.73e5

Nw = np.zeros_like(height_m)
for i in range(len(height_m)):
    T_k = temp[i] + 273.15
    if T_k > 0 and vapor[i] > 0:
        Nw[i] = C2 * vapor[i] / T_k + C3 * vapor[i] / (T_k**2)

integral_nw = np.trapz(Nw, height_m)
zwd_cosmic = 1e-6 * integral_nw
zwd_cosmic_mm = zwd_cosmic * 1000

surface_height = height[0]
surface_temp = temp[0]
surface_pressure = pressure[0]
surface_vapor = vapor[0]

print("\nCOSMIC-2 Results for DOY 244:")
print("="*80)
print(f"  ZWD = {zwd_cosmic_mm:.2f} mm")
print(f"  Integral Nw dh = {integral_nw:.2f}")
print(f"  Number of profile levels: {len(height)}")
print(f"  Surface Height: {surface_height:.2f} km")
print(f"  Surface Temperature: {surface_temp:.2f} deg C")
print(f"  Surface Pressure: {surface_pressure:.2f} hPa")
print(f"  Surface Vapor Pressure: {surface_vapor:.2f} hPa")

# ============================================
# 4. ZWD Comparison
# ============================================
print("\n" + "="*80)
print("ZWD Comparison for DOY 244:")
print("="*80)
print(f"  VMF3:     {zwd_vmf3_mm:.2f} mm")
print(f"  COSMIC-2: {zwd_cosmic_mm:.2f} mm")
diff_zwd = zwd_cosmic_mm - zwd_vmf3_mm
print(f"  Difference: {diff_zwd:.2f} mm")
if zwd_vmf3_mm != 0:
    print(f"  Relative Difference: {diff_zwd / zwd_vmf3_mm * 100:.2f} %")

# ============================================
# 5. Save COSMIC-2 profile to CSV
# ============================================
profile_df = pd.DataFrame({
    'height_km': height,
    'temp_C': temp,
    'pressure_hPa': pressure,
    'vapor_pressure_hPa': vapor,
    'rel_humidity_percent': rel_humidity,
    'refractivity_N': refractivity,
    'Nw': Nw
})

profile_df.to_csv('COSMIC2_profile_DOY244.csv', index=False)
print(f"\nCOSMIC-2 profile saved to 'COSMIC2_profile_DOY244.csv'.")

# ============================================
# 6. Plot comparison figures with smaller text
# ============================================
fig, axes = plt.subplots(2, 2, figsize=(12, 9))

# 6.1 Temperature Profile
ax1 = axes[0, 0]
ax1.plot(temp, height, 'b-', linewidth=2, label='COSMIC-2')
ax1.set_xlabel('Temperature (C)', fontsize=9)
ax1.set_ylabel('Height (km)', fontsize=9)
ax1.set_title('Temperature Profile - COSMIC-2 (DOY 244)', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=8)
ax1.tick_params(labelsize=8)

# 6.2 Water Vapor Pressure Profile
ax2 = axes[0, 1]
ax2.plot(vapor, height, 'r-', linewidth=2, label='COSMIC-2')
ax2.set_xlabel('Vapor Pressure (hPa)', fontsize=9)
ax2.set_ylabel('Height (km)', fontsize=9)
ax2.set_title('Water Vapor Pressure Profile - COSMIC-2', fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=8)
ax2.tick_params(labelsize=8)

# 6.3 ZWD Comparison Bar Chart
ax3 = axes[1, 0]
methods = ['VMF3', 'COSMIC-2']
zwd_values = [zwd_vmf3_mm, zwd_cosmic_mm]
colors = ['blue', 'red']
bars = ax3.bar(methods, zwd_values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
ax3.set_ylabel('ZWD (mm)', fontsize=9)
ax3.set_title('ZWD Comparison for DOY 244', fontsize=10)
ax3.grid(True, alpha=0.3, axis='y')
ax3.tick_params(labelsize=8)

for bar, val in zip(bars, zwd_values):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
             f'{val:.2f} mm', ha='center', va='bottom', fontsize=8)

ax3.text(0.5, max(zwd_values) + 10, f'Diff: {diff_zwd:.2f} mm', 
         ha='center', va='bottom', fontsize=9, color='red')

# 6.4 Nw Profile
ax4 = axes[1, 1]
ax4.plot(Nw, height, 'purple', linewidth=2, label='Nw')
ax4.set_xlabel('Nw', fontsize=9)
ax4.set_ylabel('Height (km)', fontsize=9)
ax4.set_title('Wet Refractivity (Nw) Profile', fontsize=10)
ax4.grid(True, alpha=0.3)
ax4.legend(fontsize=8)
ax4.tick_params(labelsize=8)

ax4.text(0.02, 0.98, f'Integral Nw = {integral_nw:.2f}', 
         transform=ax4.transAxes, fontsize=8, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.suptitle('COSMIC-2 vs VMF3 ZWD Analysis - DOY 244 (Sep 1, 2025)', fontsize=12)
plt.tight_layout()
plt.savefig('COSMIC2_VMF3_comparison_DOY244.png', dpi=300, bbox_inches='tight')
plt.show()

# ============================================
# 7. Summary Table
# ============================================
print("\n" + "="*80)
print("Comparison Summary Table:")
print("="*80)

summary_df = pd.DataFrame({
    'Parameter': ['ZWD (mm)', 'Surface Pressure (hPa)', 'Surface Temperature (C)', 'Distance from ALBH (deg)', 'Number of Levels'],
    'VMF3': [f'{zwd_vmf3_mm:.2f}', f'{pressure_vmf3:.2f}', f'{temp_vmf3:.2f}', '-', '-'],
    'COSMIC-2': [f'{zwd_cosmic_mm:.2f}', f'{surface_pressure:.2f}', f'{surface_temp:.2f}', f'{min_distance:.4f}', f'{len(height)}']
})

print(summary_df.to_string(index=False))

print("\n" + "="*80)
print("Analysis Complete!")
print("Output files:")
print("  - COSMIC2_profile_DOY244.csv")
print("  - COSMIC2_VMF3_comparison_DOY244.png")
print("="*80)