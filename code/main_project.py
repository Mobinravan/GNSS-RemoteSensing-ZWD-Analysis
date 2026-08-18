# PHOBOS
# PHOBOS - Mobin Ravan 

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import xarray as xr
import cfgrib
import warnings
from scipy.interpolate import CubicSpline
warnings.filterwarnings('ignore')

print("="*80)
print(" Bakhsh 1: Estekhraj ZWD az dadehhaye ERA5")
print("="*80)


# Masirhaye filehaye ERA5 dar sistem (dadeh ha be soorat mah be mah download shodeh)

era5_paths = {
    'September': r'C:\Users\PARSIAN-IT\Desktop\GNSSRS_Proj\483603e7af7be76789bb7d3f59255c5\data.grib',
    'October': r'C:\Users\PARSIAN-IT\Desktop\GNSSRS_Proj\10de07103c2940cf124f6d5d29a7f28d\data.grib',
    'November': r'C:\Users\PARSIAN-IT\Desktop\GNSSRS_Proj\ea50395c71e9863a479f8fafefaa1bce\data.grib'
}



# Khandane file GRIB ba xarray
def read_era5_grib(file_path):
    """
    Khandane file GRIB ERA5 va estekhraje dadehha
    """
    try:
        ds = xr.open_dataset(file_path, engine='cfgrib')
        return ds
    except Exception as e:
        print(f" Khata dar khandane file {file_path}: {e}")
        return None

# Khandane hameye fileha
era5_data = {}
for month, path in era5_paths.items():
    print(f"\n Khandane dadehaye {month}...")
    ds = read_era5_grib(path)
    if ds is not None:
        era5_data[month] = ds
        print(f"   Khandeh shod!")
        print(f"  - Abad: {ds.dims}")
        print(f"  - Motaghayyerha: {list(ds.data_vars)}")
        print(f"  - Tarazhaye fashari: {ds.isobaricInhPa.values}")

print(f"\n Tedade mahahe khandeh shod: {len(era5_data)}")


#----------------------dadeh badiiii---------------------------


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy import integrate
from scipy.interpolate import interp1d
import warnings
warnings.filterwarnings('ignore')

# Khandane file VMF3
vmf3_data = pd.read_csv(r'C:\Users\PARSIAN-IT\Desktop\GNSSRS_Proj\ALBH_VMF3_2025_DOY244_334.csv')
print(f"Tedade rekordha: {len(vmf3_data)}")
print(vmf3_data.head())

# Tabdile DOY be tarikh
start_date = datetime(2025, 1, 1) + timedelta(days=243)  # DOY 244
vmf3_data['Date'] = [start_date + timedelta(days=int(doy-244)) 
                     for doy in vmf3_data['DOY']]

print(f"\nBazeye zamani: {vmf3_data['Date'].min()} ta {vmf3_data['Date'].max()}")


#---------------

# Khandane filehaye IGS ba formate SINEX TRO
# ------------------------------------------
import glob
import os

def read_igs_tro(file_path):
    """
    Khandane file TRO dar formate SINEX va estekhraje ZTD
    Format: SITE EPOCH TROTOT STDDEV TGNTOT STDDEV TGETOT STDDEV
    """
    ztd_values = []
    times = []
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"   Khata dar khandane file: {e}")
        return np.array([]), np.array([])
    
    # Peyda kardane bakhshe dadeh
    data_start = -1
    data_end = -1
    
    for i, line in enumerate(lines):
        if '+TROP/SOLUTION' in line:
            data_start = i + 1
        if '-TROP/SOLUTION' in line:
            data_end = i
            break
    
    if data_start == -1 or data_end == -1:
        return np.array([]), np.array([])
    
    # Khandane dadehha
    for line in lines[data_start:data_end]:
        line = line.strip()
        if not line or line.startswith('*'):
            continue
        
        parts = line.split()
        if len(parts) >= 8:
            try:
                # Sotone 0: SITE (ALBH)
                site = parts[0]
                
                # Sotone 1: EPOCH (25:244:00000)
                epoch = parts[1]
                # Estekhraje saat az epoch
                time_parts = epoch.split(':')
                if len(time_parts) == 3:
                    # Sal:Ruz:Saat
                    hour = int(time_parts[2]) / 100  # 00000 -> 0.00
                    minute = 0
                    second = 0
                else:
                    # Formate جایگزین: Saat be sorate HHMMSS
                    hour = int(epoch[:2])
                    minute = int(epoch[2:4])
                    second = int(epoch[4:6])
                
                # Sotone 2: TROTOT (ZTD bar hasbe millimeter)
                ztd_mm = float(parts[2])
                # Tabdil be metr
                ztd_m = ztd_mm / 1000.0
                
                # Barrasie mahdudeh mantaghi (ZTD mamoulan beine 2 ta 3 metr)
                if 2.0 < ztd_m < 3.0:
                    ztd_values.append(ztd_m)
                    times.append(hour + minute/60 + second/3600)
                    
            except (ValueError, IndexError) as e:
                continue
    
    return np.array(times), np.array(ztd_values)


# Masire filehaye IGS 
igs_folder = r'C:\Users\PARSIAN-IT\Desktop\GNSSRS_Proj\ZPD\ZPD'

print("\n" + "="*80) 
print(" Khandane filehaye IGS...")
print("="*80)

# Jostojuye fileha
tro_files = sorted(glob.glob(os.path.join(igs_folder, 'IGS*OPSFIN*ALBH*TRO.TRO')))

if not tro_files:
    tro_files = sorted(glob.glob(os.path.join(igs_folder, '*.TRO')))

print(f" Tedade filehaye TRO peyda shod: {len(tro_files)}")

# Khandane hameye fileha
igs_data = {}
total_entries = 0

for file in tro_files:
    try:
        # Estekhraje DOY az name file (day)
        filename = os.path.basename(file)
        parts = filename.split('_')
        
        if len(parts) >= 2:
            date_part = parts[1]
            # 20252440000 -> DOY: 244
            doy = int(date_part[:7]) % 1000
        else:
            doy = None
        
        times, ztd = read_igs_tro(file)
        
        if len(ztd) > 0:
            if doy is not None:
                igs_data[doy] = {'time': times, 'ztd': ztd}
                total_entries += len(ztd)
                print(f"   DOY {doy}: {len(ztd)} rekord")
            else:
                print(f"   Nemitavan DOY ra az {filename} estekhraj kard")
        else:
            print(f"   Hich dadehi dar {filename} yaft nashod")
            
    except Exception as e:
        print(f"   Khata dar pardazeshe {file}: {e}")

print(f"\n Kholaseh:")
print(f"   Tedade ruzhaye khandeh shod: {len(igs_data)}")
print(f"   Majmue rekordha: {total_entries}")

if len(igs_data) > 0:
    print("\n Khandane filehaye IGS ba movafaghiat anjam shod!")
    
    # Namayeshe yek nemune dadeh
    sample_doy = list(igs_data.keys())[0]
    sample_data = igs_data[sample_doy]
    print(f"\n Nemune dadeh baraye DOY {sample_doy}:")
    print(f"   Tedade rekordha: {len(sample_data['ztd'])}")
    print(f"   Mahdudeh ZTD: {sample_data['ztd'].min():.4f} - {sample_data['ztd'].max():.4f} metr")
    print(f"   Miyangine ZTD: {sample_data['ztd'].mean():.4f} metr")
else:
    print("\n Hich dadehi az filehaye IGS khandeh nashod.")





# Bakhsh 4: Khandan va pardazeshe dadehaye GPT3-1


print("\n" + "="*80)
print(" Bakhsh 4: Khandane dadehaye GPT3-1")
print("="*80)


# 1. Tarife masire file gpt3_1.grd

gpt3_file = r'C:\Users\PARSIAN-IT\Desktop\GNSSRS_Proj\gpt3_1.grd'

# Barrasie vojude file
import os
if os.path.exists(gpt3_file):
    print(f" File gpt3_1.grd peyda shod!")
    print(f"   Hajm: {os.path.getsize(gpt3_file) / 1024:.2f} KB")
else:
    print(f" File gpt3_1.grd dar masire moshakhas shod peyda nashod!")
    print(f"   Masir: {gpt3_file}")


# 2. Khandane file gpt3_1.grd


def read_gpt3_1_grid(filename):
    """
    Khandane file gpt3_1.grd va estekhraje zarayeb
    Format: toul, arz, va zarayeb baraye har parame'tr
    """
    try:
        # Khandane file ba pandas
        df = pd.read_csv(filename, skiprows=1, sep='\s+', header=None)
        print(f" File khandeh shod: {df.shape[0]} radif")
        
        # Mokhtasat
        lons = df.iloc[:, 0].values  # Toul (0 ta 360 daraje)
        lats = df.iloc[:, 1].values  # Arz (-90 ta 90 daraje)
        
        # Zarayebe feshar (sotonhaye 2 ta 6)
        # [miyangin, salane_sinusi, salane_kosinusi, nimsalane_sinusi, nimsalane_kosinusi]
        P_coeffs = df.iloc[:, 2:7].values
        
        # Zarayebe dama (sotonhaye 7 ta 11)
        T_coeffs = df.iloc[:, 7:12].values
        
        # Zarayebe rotobate vijeh (sotonhaye 12 ta 16) taghsim bar 1000
        Q_coeffs = df.iloc[:, 12:17].values / 1000
        
        # Zarayebe shibe dama (sotonhaye 17 ta 21) taghsim bar 1000
        dT_coeffs = df.iloc[:, 17:22].values / 1000
        
        # Ertefae geoid (sotone 22)
        undu = df.iloc[:, 22].values
        
        # Ertefae sath (sotone 23)
        Hs = df.iloc[:, 23].values
        
        # Zarayebe ah (sotonhaye 24 ta 28) taghsim bar 1000
        ah_coeffs = df.iloc[:, 24:29].values / 1000
        
        # Zarayebe aw (sotonhaye 29 ta 33) taghsim bar 1000
        aw_coeffs = df.iloc[:, 29:34].values / 1000
        
        # Zarayebe la (sotonhaye 34 ta 38)
        la_coeffs = df.iloc[:, 34:39].values
        
        # Zarayebe Tm (sotonhaye 39 ta 43)
        Tm_coeffs = df.iloc[:, 39:44].values
        
        return {
            'lons': lons,
            'lats': lats,
            'P': P_coeffs,
            'T': T_coeffs,
            'Q': Q_coeffs,
            'dT': dT_coeffs,
            'undu': undu,
            'Hs': Hs,
            'ah': ah_coeffs,
            'aw': aw_coeffs,
            'la': la_coeffs,
            'Tm': Tm_coeffs
        }
        
    except Exception as e:
        print(f" Khata dar khandane file: {e}")
        return None

# Khandane file
gpt3_data = read_gpt3_1_grid(gpt3_file)

if gpt3_data is None:
    print(" Khandane file gpt3_1.grd namovafagh bud!")
    exit()


# 3. Tabe'e mohasebeye parame'trha dar noghteh va zamane moshakhas


def calc_gpt3_params(lat, lon, doy, gpt3_data, height_m, it=0):
    """
    Mohasebeye parame'trhaye GPT3 baraye yek noghteh va zamane moshakhas
    lat: arze joghrafiayi (daraje)
    lon: toule joghrafiayi (daraje)
    doy: ruze sal (1-365)
    height_m: ertefae beyzi (metr)
    it: 0=ba taghyeerate zamani, 1=bedune taghyeerate zamani
    """
    # Peyda kardane nazdiktarinf noghteh dar shabakeh
    lat_idx = np.argmin(np.abs(gpt3_data['lats'] - lat))
    lon_360 = lon % 360
    lon_idx = np.argmin(np.abs(gpt3_data['lons'] - lon_360))
    
    # Indexe khatti dar file
    idx = lat_idx * 361 + lon_idx
    
    # Zarayebe noghteye morede nazar
    P_coeff = gpt3_data['P'][idx]
    T_coeff = gpt3_data['T'][idx]
    Q_coeff = gpt3_data['Q'][idx]
    dT_coeff = gpt3_data['dT'][idx]
    undu_val = gpt3_data['undu'][idx]
    Hs_val = gpt3_data['Hs'][idx]
    
    # Mohasebeye zaviyeha
    doy_angle = 2 * np.pi * (doy - 1) / 365.25
    doy_half = 2 * doy_angle
    
    if it == 1:
        # Bedune taghyeerate zamani (faghat miyangin)
        P0 = P_coeff[0]
        T0 = T_coeff[0]
        Q0 = Q_coeff[0]
        dT0 = dT_coeff[0]
    else:
        # Ba taghyeerate zamani (salane va nimsalane)
        P0 = (P_coeff[0] + P_coeff[1] * np.sin(doy_angle) + P_coeff[2] * np.cos(doy_angle) +
              P_coeff[3] * np.sin(doy_half) + P_coeff[4] * np.cos(doy_half))
        T0 = (T_coeff[0] + T_coeff[1] * np.sin(doy_angle) + T_coeff[2] * np.cos(doy_angle) +
              T_coeff[3] * np.sin(doy_half) + T_coeff[4] * np.cos(doy_half))
        Q0 = (Q_coeff[0] + Q_coeff[1] * np.sin(doy_angle) + Q_coeff[2] * np.cos(doy_angle) +
              Q_coeff[3] * np.sin(doy_half) + Q_coeff[4] * np.cos(doy_half))
        dT0 = (dT_coeff[0] + dT_coeff[1] * np.sin(doy_angle) + dT_coeff[2] * np.cos(doy_angle) +
               dT_coeff[3] * np.sin(doy_half) + dT_coeff[4] * np.cos(doy_half))
    
    # Tabdile ertefae beyzi be ertefae orthometric
    h_ortho = height_m - undu_val
    
    # Kaheshe ertefa
    redh = h_ortho - Hs_val
    
    # Damaye majazi (K)
    Tv = (T0 + 273.15) * (1 + 0.6077 * Q0)
    
    # Sabet-ha
    gm = 9.80665  # Shetabe geranesh
    dMtr = 28.965e-3  # Jorme moliye havaye khoshk
    Rg = 8.3143  # Sabete gaziye jahani
    
    # Mohasebeye feshar dar ertefae istgah
    c = gm * dMtr / (Rg * Tv)
    P = P0 * np.exp(-c * redh) / 100  # Tabdil be hPa
    
    # Damaye sath
    T = T0 + dT0 * redh  # Darajeye santigerad
    
    # Feshare bokhare ab
    eps = 0.622
    e0 = Q0 * P0 / (eps + (1 - eps) * Q0) / 100  # hPa dar ertefae grid
    e = e0 * (P / (P0/100))  # Taghribe sadeb
    
    return {
        'pressure': float(P),
        'temperature': float(T),
        'e': float(e),
        'Tv': float(Tv),
        'Q': float(Q0),
        'undulation': float(undu_val),
        'Hs': float(Hs_val)
    }


# 4. Mohasebeye ZWD az parametr haye GPT3


def calculate_zwd_from_gpt3(pressure, temp_c, e_hpa):
    """
    Mohasebeye ZWD az parame'trhaye GPT3
    """
    # Sabet-haye shekast-paziri (jozve safhe 1)
    C1 = 77.6    # K/hPa
    C2 = 71.6    # K/hPa  
    C3 = 3.73e5  # K^2/hPa
    
    # Tabdile dama be kelvin
    T_k = temp_c + 273.15
    
    # Zaribe shekaste mortob dar sath
    Nw_surface = C2 * e_hpa / T_k + C3 * e_hpa / (T_k**2)
    
    # Ertefae mo'asser baraye joz'e mortob (modele Hopfield)
    H_w = 11000  # Metr
    
    # ZWD = 10^-6 * ∫Nw dh ≈ 10^-6 * Nw_surface * H_w / 5
    zwd = 1e-6 * Nw_surface * H_w / 5
    
    return zwd


# 5. Mohasebeye serie zamaniye ZWD_GPT3 baraye hameye ruzha


print("\n" + "="*80)
print(" Mohasebeye serie zamaniye ZWD_GPT3...")
print("="*80)

# Parame'trhaye istgahe ALBH
LAT_ALBH = 48.39
LON_ALBH = -123.68
HEIGHT_ALBH = 31.8  # Metr (az file IGS)

# List baraye zakhireye natayej
gpt3_zwd_list = []
gpt3_p_list = []
gpt3_t_list = []
gpt3_e_list = []

for idx, row in vmf3_data.iterrows():
    doy = row['DOY']
    
    try:
        # Mohasebeye parame'trha
        params = calc_gpt3_params(
            lat=LAT_ALBH,
            lon=LON_ALBH,
            doy=doy,
            gpt3_data=gpt3_data,
            height_m=HEIGHT_ALBH,
            it=0  # Ba taghyeerate zamani
        )
        
        # Mohasebeye ZWD
        zwd = calculate_zwd_from_gpt3(
            pressure=params['pressure'],
            temp_c=params['temperature'],
            e_hpa=params['e']
        )
        
        gpt3_zwd_list.append(zwd)
        gpt3_p_list.append(params['pressure'])
        gpt3_t_list.append(params['temperature'])
        gpt3_e_list.append(params['e'])
        
        # Namayeshe pishraft
        if idx % 10 == 0:
            print(f"   DOY {doy}: ZWD = {zwd*1000:.2f} mm")
            
    except Exception as e:
        print(f"   Khata dar DOY {doy}: {e}")
        gpt3_zwd_list.append(np.nan)
        gpt3_p_list.append(np.nan)
        gpt3_t_list.append(np.nan)
        gpt3_e_list.append(np.nan)

# Ezafe kardan be vmf3_data
vmf3_data['ZWD_GPT3'] = gpt3_zwd_list
vmf3_data['P_GPT3'] = gpt3_p_list
vmf3_data['T_GPT3'] = gpt3_t_list
vmf3_data['e_GPT3'] = gpt3_e_list

print("\n¼ Serie zamaniye ZWD_GPT3 takmil shod!")
print(f"   Tedad: {len(vmf3_data)} ruz")
print(f"   Miyangine ZWD: {vmf3_data['ZWD_GPT3'].mean()*1000:.2f} mm")
print(f"   Hadeaghale ZWD: {vmf3_data['ZWD_GPT3'].min()*1000:.2f} mm")
print(f"   Hadeaksare ZWD: {vmf3_data['ZWD_GPT3'].max()*1000:.2f} mm")


# 6. Namayeshe nemuneye natayej


print("\n Nemune natayeje GPT3 (5 ruze avval):")
print("="*80)
cols = ['DOY', 'ZWD_GPT3', 'P_GPT3', 'T_GPT3', 'e_GPT3']
print(vmf3_data[cols].head().round(4).to_string(index=False))





# Bakhshe avval: Estekhraj ZWD az dadehhaye ERA5


print("\n" + "="*80)
print(" Bakhshe avval: Estekhraj ZWD az ERA5")
print("="*80)


# 0. Mohasebeye ZWD az IGS be onvane marja'e


print("\n" + "="*80)
print(" Mohasebeye ZWD az IGS (marja')...")
print("="*80)

# Parame'trhaye istgah
LAT_ALBH = 48.39
HEIGHT_ALBH = 31.8

def saastamoinen_zhd(pressure_hpa, lat_deg, height_m):
    """Mohasebeye ZHD ba modele Saastamoinen"""
    lat_rad = np.radians(lat_deg)
    zhd = (0.002277 * pressure_hpa) / (1 - 0.00266 * np.cos(2*lat_rad) - 0.00000028 * height_m)
    return zhd

# Mohasebeye ZWD az IGS baraye har ruz
igs_zwd_list = []
igs_ztd_list = []

for doy in vmf3_data['DOY']:
    if doy in igs_data:
        # Miyangine ZTD az IGS
        ztd_mean = np.mean(igs_data[doy]['ztd'])
        
        # Feshar az dadehaye VMF3
        pressure = vmf3_data[vmf3_data['DOY']==doy]['Pressure'].values[0]
        
        # Mohasebeye ZHD
        zhd = saastamoinen_zhd(pressure, LAT_ALBH, HEIGHT_ALBH)
        
        # ZWD = ZTD - ZHD
        zwd = ztd_mean - zhd
        
        igs_zwd_list.append(zwd)
        igs_ztd_list.append(ztd_mean)
    else:
        igs_zwd_list.append(np.nan)
        igs_ztd_list.append(np.nan)

# Ezafe kardan be vmf3_data
vmf3_data['ZWD_IGS'] = igs_zwd_list
vmf3_data['ZTD_IGS'] = igs_ztd_list

print(f" ZWD_IGS mohasebeh shod!")
print(f"   Tedade ruzhaye mo'atabar: {vmf3_data['ZWD_IGS'].count()}")
print(f"   Miyangine ZWD_IGS: {vmf3_data['ZWD_IGS'].mean()*1000:.2f} mm")

# ========
# 1. Tarife tavabe'e morede niyaz


def calculate_refractivity(temp_k, q_kgkg, pressure_hpa):
    """
    Mohasebeye zaribe shekast (N) dar har taraz
    Formulhaye jozve safhe 1:
    N = N_d + N_w
    N_d = C1 * (p/T)     ← joz'e hydrostatice (khoshk)
    N_w = C2 * (e/T) + C3 * (e/T²)  ← joz'e mortob
    
    Tabdile rotobate vijeh (q) be feshare bokhare ab (e):
    e = q * p / (ε + (1-ε) * q)
    ke dar an ε = 0.622 (nesbate sabete gazha)
    """
    # Sabet-ha (az jozve safhe 1)
    C1 = 77.6      # K/hPa
    C2 = 71.6      # K/hPa
    C3 = 3.73e5    # K²/hPa
    eps = 0.622    # Nesbate sabete gazha (R_d/R_v)
    
    # Feshare bokhare ab az rotobate vijeh
    e = q_kgkg * pressure_hpa / (eps + (1 - eps) * q_kgkg)
    
    # Joz'e hydrostatice (khoshk)
    Nd = C1 * pressure_hpa / temp_k
    
    # Joz'e mortob
    Nw = C2 * e / temp_k + C3 * e / (temp_k**2)
    
    # Zaribe shekaste koll
    N = Nd + Nw
    
    return N, Nd, Nw, e

def integrate_zwd(height, Nw_values):
    """
    Integral-giriye gha'em baraye mohasebeye ZWD
    ZWD = 10⁻⁶ × ∫ Nw dh
    Estefadeh az Cubic Spline Interpolation baraye daghigh-tar
    """
    # Hazf-e maghadir-e NaN
    mask = ~np.isnan(height) & ~np.isnan(Nw_values)
    h_clean = height[mask]
    nw_clean = Nw_values[mask]
    
    # Agar tedad-e noghat kamtar az 4 bood, az method-e zoghnagh-i estefade kon
    if len(h_clean) < 4:
        integral = np.trapz(Nw_values, height)
        zwd = 1e-6 * integral
        return zwd, integral
    
    # Ijade tab'e Cubic Spline
    cs = CubicSpline(h_clean, nw_clean, bc_type='natural')
    
    # Ijade noghat-e ba daghighat-e bishtar (1000 noghte)
    h_fine = np.linspace(h_clean.min(), h_clean.max(), 1000)
    nw_fine = cs(h_fine)
    
    # Integral-giri az noghat-e riz shode
    integral = np.trapz(nw_fine, h_fine)
    zwd = 1e-6 * integral
    
    return zwd, integral

def integrate_ztd(height, N_values):
    """
    Integral-giriye gha'em baraye mohasebeye ZTD
    ZTD = 10⁻⁶ × ∫ N dh
    Estefadeh az Cubic Spline Interpolation baraye daghigh-tar
    """
    # Hazf-e maghadir-e NaN
    mask = ~np.isnan(height) & ~np.isnan(N_values)
    h_clean = height[mask]
    n_clean = N_values[mask]
    
    # Agar tedad-e noghat kamtar az 4 bood, az method-e zoghnagh-i estefade kon
    if len(h_clean) < 4:
        integral = np.trapz(N_values, height)
        ztd = 1e-6 * integral
        return ztd, integral
    
    # Ijade tab'e Cubic Spline
    cs = CubicSpline(h_clean, n_clean, bc_type='natural')
    
    # Ijade noghat-e ba daghighat-e bishtar (1000 noghte)
    h_fine = np.linspace(h_clean.min(), h_clean.max(), 1000)
    n_fine = cs(h_fine)
    
    # Integral-giri az noghat-e riz shode
    integral = np.trapz(n_fine, h_fine)
    ztd = 1e-6 * integral
    
    return ztd, integral

# ============================================================
# 2. Estekhraje profilhaye gha'em baraye istgahe ALBH


print("\ Estekhraje profilhaye gha'em az ERA5...")

# Dictionari baraye zakhireye natayej
era5_results = {}

for month, ds in era5_data.items():
    print(f"\n Pardazeshe {month}...")
    
    # Peyda kardane nazdiktarinf noghteh be istgah
    lat_idx = np.argmin(np.abs(ds.latitude.values - LAT_ALBH))
    lon_idx = np.argmin(np.abs(ds.longitude.values - LON_ALBH))
    
    # Estekhraje dadehha dar noghteye istgah - miyangine zamani baraye har mah
    temp = ds['t'].isel(latitude=lat_idx, longitude=lon_idx).mean(dim='time').values  # K
    q = ds['q'].isel(latitude=lat_idx, longitude=lon_idx).mean(dim='time').values     # kg/kg
    z = ds['z'].isel(latitude=lat_idx, longitude=lon_idx).mean(dim='time').values     # m²/s²
    
    # Tarazhaye fashari
    levels = ds.isobaricInhPa.values  # hPa
    
    # Tabdile geopotential be ertefa (h = z/g)
    g = 9.80665  # m/s²
    height = z / g  # Metr
    
    # ===============================================
    # 3. Mohasebeye zaribe shekast dar tamame tarazha
    
    
    N_values = []
    Nd_values = []
    Nw_values = []
    e_values = []
    
    for i in range(len(levels)):
        T = temp[i]      # Kelvin
        q_i = q[i]       # kg/kg
        p = levels[i]    # hPa
        
        N, Nd, Nw, e = calculate_refractivity(T, q_i, p)
        
        N_values.append(N)
        Nd_values.append(Nd)
        Nw_values.append(Nw)
        e_values.append(e)
    
    N_values = np.array(N_values)
    Nd_values = np.array(Nd_values)
    Nw_values = np.array(Nw_values)
    e_values = np.array(e_values)
    
    # ===========================================================
    # 4. Integral-giriye gha'em baraye mohasebeye ZTD va ZWD

    
    # ZTD = 10⁻⁶ × ∫ N dh
    ztd, ztd_integral = integrate_ztd(height, N_values)
    
    # ZHD = 10⁻⁶ × ∫ Nd dh
    zhd, zhd_integral = integrate_ztd(height, Nd_values)
    
    # ZWD = 10⁻⁶ × ∫ Nw dh
    zwd, zwd_integral = integrate_zwd(height, Nw_values)
    
    # ======================
    # 5. Zakhireye natayej
    
    
    era5_results[month] = {
        'levels': levels,
        'height': height,
        'temp': temp,
        'q': q,
        'z': z,
        'N': N_values,
        'Nd': Nd_values,
        'Nw': Nw_values,
        'e': e_values,
        'ztd': ztd,
        'zhd': zhd,
        'zwd': zwd,
        'ztd_integral': ztd_integral,
        'zhd_integral': zhd_integral,
        'zwd_integral': zwd_integral
    }
    
    # Namayeshe natayej
    print(f"\n    Natayeje {month}:")
    print(f"     ZTD = {ztd*1000:.2f} mm")
    print(f"     ZHD = {zhd*1000:.2f} mm")
    print(f"     ZWD = {zwd*1000:.2f} mm")
    print(f"     Nesbate ZWD/ZTD = {zwd/ztd*100:.2f}%")
    print(f"     ∫N dh = {ztd_integral:.2f}")
    print(f"     ∫Nw dh = {zwd_integral:.2f}")

# ===========================
# 6. Jadvale natayeje ERA5


print("\n" + "="*80)
print(" Jadvale natayeje ERA5")
print("="*80)

era5_table = pd.DataFrame({
    'Mah': list(era5_results.keys()),
    'ZTD (mm)': [era5_results[m]['ztd']*1000 for m in era5_results],
    'ZHD (mm)': [era5_results[m]['zhd']*1000 for m in era5_results],
    'ZWD (mm)': [era5_results[m]['zwd']*1000 for m in era5_results],
    'Nesbate ZWD/ZTD (%)': [era5_results[m]['zwd']/era5_results[m]['ztd']*100 for m in era5_results]
})

print(era5_table.round(2).to_string(index=False))

# ============================================================
# 7. Serie zamaniye ZWD_ERA5 (baraye har ruz)


print("\n" + "="*80)
print(" Mohasebeye serie zamaniye ZWD_ERA5 baraye hameye ruzha...")
print("="*80)

era5_zwd_daily = []
era5_ztd_daily = []

for idx, row in vmf3_data.iterrows():
    doy = row['DOY']
    date = row['Date']
    
    # Peyda kardane mahe marbuteh
    month_name = date.strftime('%B')
    if month_name == 'September':
        month_key = 'September'
    elif month_name == 'October':
        month_key = 'October'
    else:
        month_key = 'November'
    
    if month_key not in era5_data:
        era5_zwd_daily.append(np.nan)
        era5_ztd_daily.append(np.nan)
        continue
    
    ds = era5_data[month_key]
    
    # Peyda kardane nazdiktarinf zaman be ruze morede nazar
    times = ds.time.values
    target_time = np.datetime64(date)
    time_idx = np.argmin(np.abs(times - target_time))
    
    # Estekhraje dadehha dar zamane morede nazar
    lat_idx = np.argmin(np.abs(ds.latitude.values - LAT_ALBH))
    lon_idx = np.argmin(np.abs(ds.longitude.values - LON_ALBH))
    
    temp = ds['t'].isel(time=time_idx, latitude=lat_idx, longitude=lon_idx).values
    q = ds['q'].isel(time=time_idx, latitude=lat_idx, longitude=lon_idx).values
    z = ds['z'].isel(time=time_idx, latitude=lat_idx, longitude=lon_idx).values
    
    levels = ds.isobaricInhPa.values
    height = z / 9.80665
    
    # Mohasebeye zaribe shekast
    N_values = []
    Nw_values = []
    
    for i in range(len(levels)):
        T = temp[i]
        q_i = q[i]
        p = levels[i]
        
        N, Nd, Nw, e = calculate_refractivity(T, q_i, p)
        N_values.append(N)
        Nw_values.append(Nw)
    
    # Integral-giri
    ztd, _ = integrate_ztd(height, np.array(N_values))
    zwd, _ = integrate_zwd(height, np.array(Nw_values))
    
    era5_zwd_daily.append(zwd)
    era5_ztd_daily.append(ztd)

# Ezafe kardan be vmf3_data
vmf3_data['ZWD_ERA5'] = era5_zwd_daily
vmf3_data['ZTD_ERA5'] = era5_ztd_daily

print(f"\n Serie zamaniye ZWD_ERA5 takmil shod!")
print(f"   Tedad: {len(vmf3_data)} ruz")
print(f"   Miyangine ZWD: {vmf3_data['ZWD_ERA5'].mean()*1000:.2f} mm")

# ============================================================
# chap azaryeb shekast barayeh temam taraz ha (har 3 mah)

print("\n" + "="*80)
print(" Zaribe Shekast dar tamame tarazha - har se mah")
print("="*80)

for month in ['September', 'October', 'November']:
    if month not in era5_results:
        continue
    
    result = era5_results[month]
    levels = result['levels']
    N = result['N']
    Nd = result['Nd']
    Nw = result['Nw']
    height_km = result['height'] / 1000
    temp_c = result['temp'] - 273.15
    q_gkg = result['q'] * 1000
    
    print(f"\n {month}:")
    print("="*110)
    print(f"{'Level (hPa)':<14} {'Height (km)':<14} {'Temp (°C)':<14} {'Q (g/kg)':<16} {'Nd':<14} {'Nw':<14} {'N':<14}")
    print("-"*110)
    
   
    # chap 5 taraz aval v 5 taraz akhar barayeh kholaseh
    n_levels = len(levels)
    indices_to_show = list(range(5)) + list(range(n_levels-5, n_levels))
    
    for i in indices_to_show:
        print(f"{levels[i]:<14.1f} {height_km[i]:<14.2f} {temp_c[i]:<14.2f} {q_gkg[i]:<16.4f} {Nd[i]:<14.2f} {Nw[i]:<14.2f} {N[i]:<14.2f}")
    
    if n_levels > 10:
        print("..." + " "*90 + "...")
    
    print("-"*110)
    print(f"Sum N: {np.sum(N):.2f} | Sum Nd: {np.sum(Nd):.2f} | Sum Nw: {np.sum(Nw):.2f}")
    print(f"ZWD final: {result['zwd']*1000:.2f} mm | ZTD final: {result['ztd']*1000:.2f} mm")

# =======================
# 9. Rasme profilhaye gha'em (Profilhaye Ghaem)


print("\n" + "="*80)
print(" Rasme profilhaye gha'em...")
print("="*80)

fig, axes = plt.subplots(2, 3, figsize=(18, 10))

months = ['September', 'October', 'November']
colors = ['red', 'green', 'blue']
month_labels = ['September', 'October', 'November']

for idx, month in enumerate(months):
    if month not in era5_results:
        continue
    
    result = era5_results[month]
    height_km = result['height'] / 1000
    temp_c = result['temp'] - 273.15
    q_gkg = result['q'] * 1000
    N = result['N']
    Nw = result['Nw']
    Nd = result['Nd']
    
    # Radife avval: Dama va Rotobat
    ax1 = axes[0, idx]
    ax1.plot(temp_c, height_km, color=colors[idx], linewidth=2.5, label='Dama')
    ax1.set_xlabel('Dama (°C)', fontsize=11)
    ax1.set_ylabel('Ertefa (km)', fontsize=11)
    ax1.set_title(f'{month_labels[idx]} - Dama va Rotobat', fontsize=13)
    ax1.set_ylim(0, 20)
    ax1.grid(True, alpha=0.3)
    
    # Rotobat (mehvore dovom)
    ax1_twin = ax1.twiny()
    ax1_twin.plot(q_gkg, height_km, color='orange', linewidth=2.5, linestyle='--', label='Rotobate Vijeh')
    ax1_twin.set_xlabel('Rotobate Vijeh (g/kg)', color='orange', fontsize=11)
    ax1_twin.tick_params(axis='x', labelcolor='orange')
    
    # Radife dovom: Zaribe Shekast
    ax2 = axes[1, idx]
    ax2.plot(N, height_km, color=colors[idx], linewidth=2.5, label='N (Koll)')
    ax2.plot(Nd, height_km, color='blue', linewidth=2, linestyle=':', label='Nd (Khoshk)')
    ax2.plot(Nw, height_km, color='purple', linewidth=2, linestyle='--', label='Nw (Mortob)')
    ax2.set_xlabel('Zaribe Shekast (N)', fontsize=11)
    ax2.set_ylabel('Ertefa (km)', fontsize=11)
    ax2.set_title(f'{month_labels[idx]} - Zaribe Shekast', fontsize=13)
    ax2.set_ylim(0, 20)
    ax2.legend(loc='lower right', fontsize=9)
    ax2.grid(True, alpha=0.3)

plt.suptitle('Profilhaye Ghaem ERA5 - Istgahe ALBH', fontsize=16)
plt.tight_layout()
plt.savefig('ERA5_profiles_full.png', dpi=300, bbox_inches='tight')
plt.show()

print(" Profilha dar file 'ERA5_profiles_full.png' zakhireh shod.")

# =========================================================
# 10. Moghayeseye serie zamaniye ZWD_ERA5 ba sayere raveshha


print("\n" + "="*80)
print(" Moghayeseye serie zamaniye ZWD_ERA5 ba sayere raveshha")
print("="*80)

fig, ax = plt.subplots(figsize=(14, 6))

if 'ZWD_IGS' in vmf3_data.columns:
    ax.plot(vmf3_data['Date'], vmf3_data['ZWD_IGS'] * 1000, 
            'k-', linewidth=2, label='IGS (Marja)', alpha=0.8)

if 'ZWD_VMF3' in vmf3_data.columns:
    ax.plot(vmf3_data['Date'], vmf3_data['ZWD_VMF3'] * 1000, 
            'b-', linewidth=1.5, label='VMF3', alpha=0.7)

if 'ZWD_ERA5' in vmf3_data.columns:
    ax.plot(vmf3_data['Date'], vmf3_data['ZWD_ERA5'] * 1000, 
            'r-', linewidth=1.5, label='ERA5', alpha=0.7)

if 'ZWD_GPT3' in vmf3_data.columns:
    ax.plot(vmf3_data['Date'], vmf3_data['ZWD_GPT3'] * 1000, 
            'g-', linewidth=1.5, label='GPT3', alpha=0.7)

ax.set_xlabel('Tarikh', fontsize=12)
ax.set_ylabel('ZWD (mm)', fontsize=12)
ax.set_title('Moghayeseye Serie Zamaniye ZWD - Hameye Raveshha', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('ZWD_all_methods_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

print(" Nemudare moghayeseh dar file 'ZWD_all_methods_comparison.png' zakhireh shod.")

# ====================================
# 11. Mohasebeye shakheshaye amari


print("\n" + "="*80)
print(" Mohasebeye shakheshaye amari baraye hameye raveshha")
print("="*80)

def calculate_metrics(observed, predicted, name=""):
    mask = ~(np.isnan(observed) | np.isnan(predicted))
    obs = np.array(observed)[mask]
    pred = np.array(predicted)[mask]
    
    if len(obs) == 0:
        return {'Method': name, 'Bias (mm)': np.nan, 'RMSE (mm)': np.nan, 
                'MAE (mm)': np.nan, 'Correlation': np.nan}
    
    bias = np.mean(pred - obs) * 1000
    rmse = np.sqrt(np.mean((pred - obs)**2)) * 1000
    mae = np.mean(np.abs(pred - obs)) * 1000
    corr = np.corrcoef(obs, pred)[0, 1]
    
    return {
        'Method': name,
        'Bias (mm)': bias,
        'RMSE (mm)': rmse,
        'MAE (mm)': mae,
        'Correlation': corr
    }

methods = {
    'VMF3': 'ZWD_VMF3',
    'ERA5': 'ZWD_ERA5',
    'GPT3': 'ZWD_GPT3'
}

metrics_list = []

for name, col in methods.items():
    if col in vmf3_data.columns and 'ZWD_IGS' in vmf3_data.columns:
        metrics = calculate_metrics(
            vmf3_data['ZWD_IGS'].values,
            vmf3_data[col].values,
            name
        )
        metrics_list.append(metrics)

if metrics_list:
    metrics_df = pd.DataFrame(metrics_list)
    print("\n Jadvale moghayeseye raveshha ba marja'e IGS:")
    print("="*80)
    print(metrics_df.round(4).to_string(index=False))
    
    best = metrics_df.loc[metrics_df['RMSE (mm)'].idxmin()]
    print(f"\n Behtarin ravesh bar asase RMSE: {best['Method']}")
    print(f"   RMSE: {best['RMSE (mm)']:.2f} mm")
    print(f"   Bias: {best['Bias (mm)']:.2f} mm")
    print(f"   Correlation: {best['Correlation']:.4f}")
else:
    print(" Dadehhaye kafi baraye moghayeseh vojud nadarad!")

print("\n Bakhshe ERA5 ba movafaghiat kamel shod!")








#--------------------------------------------\-\-\-\--\-\-\
# Bakhshe Dovom: Model-haye Tajrobi
# ===========================================

print("\n" + "="*80)
print(" Bakhshe Dovom: Model-haye Tajrobi")
print("="*80)

# ===============================
# 1. Tarife Tavabe-e Morede Niyaz
# ===================

def saastamoinen_zhd(pressure_hpa, lat_deg, height_m):
    """
    Mohasbe ZHD ba Modele Saastamoinen
    Formool: ZHD = 0.002277 * P / (1 - 0.00266*cos(2φ) - 0.00000028*H)
    
    Parametrhā:
    - pressure_hpa: Feshare Sat'h bar hasbe Hectopascal (hPa)
    - lat_deg: Arze Joghrāfiyāyi bar hasbe Daraje
    - height_m: Ertefā bar hasbe Metr
    """
    lat_rad = np.radians(lat_deg)
    zhd = (0.002277 * pressure_hpa) / (1 - 0.00266 * np.cos(2*lat_rad) - 0.00000028 * height_m)
    return zhd

def saastamoinen_zwd(pressure_hpa, temp_c, e_hpa, lat_deg, height_m, doy=None):
    """
    Mohasbe ZWD ba Modele Saastamoinen
    ZWD = ZTD - ZHD
    Ke dar ān ZTD az Modele Saastamoinen Kamel Mohasbe Mishavad
    
    Formoole Kamele Saastamoinen baraye ZTD:
    ZTD = 0.002277 * [P + (1255/T + 0.05)*e - B*tan²(z)] / cos(z)
    
    Baraye ZWD az Raveshe Standard Estefade Mikonim:
    1. ZHD ra ba Formoole Bālā Mohasbe Mikonim
    2. ZTD ra ba Formoole Kāmel Mohasbe Mikonim (ba Farze Zāviye Ghā'em, z=0)
    3. ZWD = ZTD - ZHD
    
    Parametrhā:
    - pressure_hpa: Feshare Sat'h (hPa)
    - temp_c: Damāye Sat'h (Daraje Sāntigrād)
    - e_hpa: Feshare Bokhāre Ābe Sat'h (hPa)
    - lat_deg: Arze Joghrāfiyāyi (Daraje)
    - height_m: Ertefā (Metr)
    """
    # Tabdile Damā be Kelvin
    temp_k = temp_c + 273.15
    
    # ZHD ba Formoole Saastamoinen
    zhd = saastamoinen_zhd(pressure_hpa, lat_deg, height_m)
    
    # ZTD ba Formoole Kamele Saastamoinen (Zāviye Ghā'em)
    # ZTD = 0.002277 * [P + (1255/T + 0.05)*e] / 1
    # Baraye Zāviye Ghā'em, cos(z)=1 va tan(z)=0
    ztd = 0.002277 * (pressure_hpa + (1255/temp_k + 0.05) * e_hpa)
    
    # ZWD = ZTD - ZHD
    zwd = ztd - zhd
    
    return zwd, zhd, ztd

def hopfield_zhd(pressure_hpa, temp_c, lat_deg, height_m):
    """
    Mohasbe ZHD ba Modele Hopfield
    
    Formool:
    ZHD = 10⁻⁶ * N_d_surface * H_d / 5
    
    Ke dar ān:
    N_d_surface = 77.6 * P / T
    H_d = 40136 + 148.72 * (T - 273.16)  (Ertefāe Mo'assar baraye Joz'e Khoshk)
    
    Parametrhā:
    - pressure_hpa: Feshare Sat'h (hPa)
    - temp_c: Damāye Sat'h (Daraje Sāntigrād)
    - lat_deg: Arze Joghrāfiyāyi (Daraje) - dar in model estefade nāmishavad
    - height_m: Ertefā (Metr) - dar in model estefade nāmishavad
    """
    # Tabdile Damā be Kelvin
    temp_k = temp_c + 273.15
    
    # Zaribe Shekaste Khoshk dar Sat'h
    C1 = 77.6  # K/hPa
    Nd_surface = C1 * pressure_hpa / temp_k
    
    # Ertefāe Mo'assar baraye Joz'e Khoshk
    H_d = 40136 + 148.72 * (temp_k - 273.16)  # metr
    
    # ZHD = 10⁻⁶ * Nd_surface * H_d / 5
    zhd = 1e-6 * Nd_surface * H_d / 5
    
    return zhd

def hopfield_zwd(pressure_hpa, temp_c, e_hpa, lat_deg, height_m):
    """
    Mohasbe ZWD ba Modele Hopfield
    
    Formool:
    ZWD = 10⁻⁶ * N_w_surface * H_w / 5
    
    Ke dar ān:
    N_w_surface = 77.6 * e / T² * 10⁵
    H_w = 11000  (Ertefāe Mo'assar baraye Joz'e Martoob)
    
    Parametrhā:
    - pressure_hpa: Feshare Sat'h (hPa)
    - temp_c: Damāye Sat'h (Daraje Sāntigrād)
    - e_hpa: Feshare Bokhāre Ābe Sat'h (hPa)
    - lat_deg: Arze Joghrāfiyāyi (Daraje) - dar in model estefade nāmishavad
    - height_m: Ertefā (Metr) - dar in model estefade nāmishavad
    """
    # Tabdile Damā be Kelvin
    temp_k = temp_c + 273.15
    
    # Zaribe Shekaste Martoob dar Sat'h
    C1 = 77.6  # K/hPa
    Nw_surface = C1 * e_hpa / temp_k
    
    # Ertefāe Mo'assar baraye Joz'e Martoob
    H_w = 11000  # metr
    
    # ZWD = 10⁻⁶ * Nw_surface * H_w / 5
    zwd = 1e-6 * Nw_surface * H_w / 5
    
    return zwd

def calculate_e_from_rh(temp_c, rh_percent):
    """
    Mohasbe Feshare Bokhāre Āb az Rotoobate Nesbi
    Ba estefade az Formoole Taghribi:
    e_sat = 6.112 * exp(17.67 * T / (T + 243.5))
    e = RH/100 * e_sat
    
    Parametrhā:
    - temp_c: Damāye Sat'h (Daraje Sāntigrād)
    - rh_percent: Rotoobate Nesbi (Darsad)
    """
    # Feshare Bokhāre Ābe Ashbā (hPa)
    e_sat = 6.112 * np.exp(17.67 * temp_c / (temp_c + 243.5))
    
    # Feshare Bokhāre Ābe Vāghe'i
    e = rh_percent / 100 * e_sat
    
    return e

# ==========================================
# 2. A'male Model-hā rooye Dadeh-hā


print("\n Mohasbe ZWD ba Model-haye Mukhtalif...")

# Parametrhāye Istgah
LAT_ALBH = 48.39
HEIGHT_ALBH = 31.8

# List-hā baraye Zakhireye Netayej
saast_zwd_list = []
saast_zhd_list = []
hopf_zwd_list = []
hopf_zhd_list = []

# Farz: Rotoobate Nesbi 60% baraye Mohasbe e (dar Soorate Niyaz)
RH_DEFAULT = 60  # Darsad

for idx, row in vmf3_data.iterrows():
    doy = row['DOY']
    pressure = row['Pressure']  # hPa
    temp_c = row['Temp']        # Daraje Sāntigrād
    e_hpa = row.get('e_GPT3', None)  # Agar e_GPT3 Mojood Bashad
    
    # Agar e_GPT3 Mojood Nabood, az Rotoobate Nesbi Takhmil Bezan
    if e_hpa is None or np.isnan(e_hpa):
        e_hpa = calculate_e_from_rh(temp_c, RH_DEFAULT)
    
    # ============================================================
    # Modele Saastamoinen
    
    zwd_saast, zhd_saast, ztd_saast = saastamoinen_zwd(
        pressure, temp_c, e_hpa, LAT_ALBH, HEIGHT_ALBH
    )
    
    saast_zwd_list.append(zwd_saast)
    saast_zhd_list.append(zhd_saast)
    
    # ============================================================
    # Modele Hopfield
    
    zhd_hopf = hopfield_zhd(pressure, temp_c, LAT_ALBH, HEIGHT_ALBH)
    zwd_hopf = hopfield_zwd(pressure, temp_c, e_hpa, LAT_ALBH, HEIGHT_ALBH)
    
    hopf_zwd_list.append(zwd_hopf)
    hopf_zhd_list.append(zhd_hopf)

# Ezafe Kardan be vmf3_data
vmf3_data['ZWD_Saast'] = saast_zwd_list
vmf3_data['ZHD_Saast'] = saast_zhd_list
vmf3_data['ZWD_Hopfield'] = hopf_zwd_list
vmf3_data['ZHD_Hopfield'] = hopf_zhd_list

# ============================================================
# 3. Nemāyeshe Netayej


print("\n Nemoone Netayeje Model-haye Tajrobi (5 Rooze Avval):")
print("="*100)
print(f"{'DOY':>6} {'ZWD_Saast':>12} {'ZWD_Hopfield':>14} {'ZWD_GPT3':>12} {'ZWD_IGS':>12}")
print("-"*100)

for i in range(min(10, len(vmf3_data))):
    doy = vmf3_data.iloc[i]['DOY']
    zwd_s = vmf3_data.iloc[i]['ZWD_Saast'] * 1000
    zwd_h = vmf3_data.iloc[i]['ZWD_Hopfield'] * 1000
    zwd_g = vmf3_data.iloc[i]['ZWD_GPT3'] * 1000 if 'ZWD_GPT3' in vmf3_data.columns else np.nan
    zwd_i = vmf3_data.iloc[i]['ZWD_IGS'] * 1000 if 'ZWD_IGS' in vmf3_data.columns else np.nan
    
    print(f"{doy:6d} {zwd_s:10.2f} mm {zwd_h:12.2f} mm {zwd_g:10.2f} mm {zwd_i:10.2f} mm")

# Āmāre Kolli
print("\n Amare Model-haye Tajrobi:")
print("="*60)
print(f"{'Model':<15} {'Miyangine ZWD (mm)':<20} {'Haddaghal (mm)':<15} {'Haddaksar (mm)':<15}")
print("-"*60)

models = {
    'ZWD_Saast': 'Saastamoinen',
    'ZWD_Hopfield': 'Hopfield',
    'ZWD_GPT3': 'GPT3',
    'ZWD_IGS': 'IGS (Marja)'
}

for col, name in models.items():
    if col in vmf3_data.columns:
        mean_val = vmf3_data[col].mean() * 1000
        min_val = vmf3_data[col].min() * 1000
        max_val = vmf3_data[col].max() * 1000
        print(f"{name:<15} {mean_val:<20.2f} {min_val:<15.2f} {max_val:<15.2f}")

# ============================================================
# 4. Rasme Nemoodāre Moghayese


print("\n Rasme Nemoodare Moghayeseye Model-haye Tajrobi...")

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# 4.1 Seri Zamani
ax1 = axes[0, 0]
ax1.plot(vmf3_data['Date'], vmf3_data['ZWD_IGS'] * 1000, 
         'k-', linewidth=2, label='IGS (Marja)', alpha=0.8)
ax1.plot(vmf3_data['Date'], vmf3_data['ZWD_Saast'] * 1000, 
         'b-', linewidth=1.5, label='Saastamoinen', alpha=0.7)
ax1.plot(vmf3_data['Date'], vmf3_data['ZWD_Hopfield'] * 1000, 
         'r-', linewidth=1.5, label='Hopfield', alpha=0.7)
if 'ZWD_GPT3' in vmf3_data.columns:
    ax1.plot(vmf3_data['Date'], vmf3_data['ZWD_GPT3'] * 1000, 
             'g-', linewidth=1.5, label='GPT3', alpha=0.7)

ax1.set_xlabel('Tārikh', fontsize=11)
ax1.set_ylabel('ZWD (Millimeter)', fontsize=11)
ax1.set_title('Moghayeseye Seri Zamaniye Model-haye Tajrobi', fontsize=12)
ax1.legend()
ax1.grid(True, alpha=0.3)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# 4.2 Scatter Plot
ax2 = axes[0, 1]
colors = {'ZWD_Saast': 'blue', 'ZWD_Hopfield': 'red', 'ZWD_GPT3': 'green'}

for col, color in colors.items():
    if col in vmf3_data.columns and 'ZWD_IGS' in vmf3_data.columns:
        mask = ~(np.isnan(vmf3_data['ZWD_IGS']) | np.isnan(vmf3_data[col]))
        obs = vmf3_data['ZWD_IGS'][mask] * 1000
        pred = vmf3_data[col][mask] * 1000
        ax2.scatter(obs, pred, alpha=0.4, s=15, 
                    label=col.replace('ZWD_', ''), color=color)

# Khate 1:1
min_val = min(vmf3_data['ZWD_IGS'].min()*1000, 
              vmf3_data['ZWD_Saast'].min()*1000)
max_val = max(vmf3_data['ZWD_IGS'].max()*1000, 
              vmf3_data['ZWD_Saast'].max()*1000)
ax2.plot([min_val, max_val], [min_val, max_val], 
         'r--', linewidth=1, label='Khate 1:1')

ax2.set_xlabel('ZWD az IGS (Millimeter)', fontsize=11)
ax2.set_ylabel('ZWD az Model (Millimeter)', fontsize=11)
ax2.set_title('Nemoodāre Parakesh', fontsize=12)
ax2.legend()
ax2.grid(True, alpha=0.3)

# 4.3 Ikhtelaf
ax3 = axes[1, 0]
for col, color in colors.items():
    if col in vmf3_data.columns and 'ZWD_IGS' in vmf3_data.columns:
        diff = (vmf3_data[col] - vmf3_data['ZWD_IGS']) * 1000
        ax3.plot(vmf3_data['Date'], diff, 
                 label=col.replace('ZWD_', ''), color=color, linewidth=1.5, alpha=0.7)

ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax3.set_xlabel('Tārikh', fontsize=11)
ax3.set_ylabel('Ikhtelafe ZWD (Millimeter)', fontsize=11)
ax3.set_title('Ikhtelafe Model-hā Nesbat be IGS', fontsize=12)
ax3.legend()
ax3.grid(True, alpha=0.3)
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

# 4.4 Histogram
ax4 = axes[1, 1]
for col, color in colors.items():
    if col in vmf3_data.columns and 'ZWD_IGS' in vmf3_data.columns:
        diff = (vmf3_data[col] - vmf3_data['ZWD_IGS']) * 1000
        ax4.hist(diff.dropna(), bins=20, alpha=0.4, 
                 label=col.replace('ZWD_', ''), color=color, edgecolor='black')

ax4.axvline(x=0, color='black', linestyle='-', linewidth=1)
ax4.set_xlabel('Ikhtelafe ZWD (Millimeter)', fontsize=11)
# ax4.set_ylabel('Te'dade Roozha', fontsize=11
ax4.set_ylabel('Te\'dade Roozha', fontsize=11)
ax4.set_title('Tozi-e Ikhtelafe Model-hā', fontsize=12)
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.suptitle('Moghayeseye Model-haye Tajrobi ba Marjae IGS - Istgahe ALBH', fontsize=14)
plt.tight_layout()
plt.savefig('empirical_models_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

print(" Nemoodar dar fayle 'empirical_models_comparison.png' zakhire shod.")

# ============================================================
# 5. Mohasbe Shākhes-haye Āmāri


print("\n" + "="*80)
print(" Mohasbe Shākhes-haye Āmāri baraye Model-haye Tajrobi")
print("="*80)

def calculate_metrics(observed, predicted, name=""):
    """Mohasbe Shākhes-haye Amari"""
    mask = ~(np.isnan(observed) | np.isnan(predicted))
    obs = np.array(observed)[mask]
    pred = np.array(predicted)[mask]
    
    if len(obs) == 0:
        return {'Method': name, 'Bias (mm)': np.nan, 'RMSE (mm)': np.nan, 
                'MAE (mm)': np.nan, 'Correlation': np.nan}
    
    bias = np.mean(pred - obs) * 1000
    rmse = np.sqrt(np.mean((pred - obs)**2)) * 1000
    mae = np.mean(np.abs(pred - obs)) * 1000
    corr = np.corrcoef(obs, pred)[0, 1]
    
    return {
        'Method': name,
        'Bias (mm)': bias,
        'RMSE (mm)': rmse,
        'MAE (mm)': mae,
        'Correlation': corr
    }

# Liste Model-hā
model_list = {
    'ZWD_Saast': 'Saastamoinen',
    'ZWD_Hopfield': 'Hopfield',
    'ZWD_GPT3': 'GPT3',
    'ZWD_VMF3': 'VMF3',
    'ZWD_ERA5': 'ERA5'
}

metrics_list = []

for col, name in model_list.items():
    if col in vmf3_data.columns and 'ZWD_IGS' in vmf3_data.columns:
        metrics = calculate_metrics(
            vmf3_data['ZWD_IGS'].values,
            vmf3_data[col].values,
            name
        )
        metrics_list.append(metrics)

metrics_df = pd.DataFrame(metrics_list)

print("\n Jadvale Moghayeseye Nahaiye Tamame Ravesh-hā:")
print("="*90)
print(metrics_df.round(4).to_string(index=False))

# Behtarin Ravesh
best = metrics_df.loc[metrics_df['RMSE (mm)'].idxmin()]
print(f"\n Behtarin Ravesh bar asase RMSE: {best['Method']}")
print(f"   RMSE: {best['RMSE (mm)']:.2f} mm")
print(f"   Bias: {best['Bias (mm)']:.2f} mm")
print(f"   Correlation: {best['Correlation']:.4f}")

# Zakhireye Jadval
metrics_df.to_csv('all_models_comparison.csv', index=False)
print("\n Jadvale Moghayese dar fayle 'all_models_comparison.csv' zakhire shod.")

print("\n Bakhshe Dovom (Model-haye Tajrobi) ba Movafaghiyat Kamel Shod!")






# ==================================================
# Bakhshe Sevom: Modele VMF3 - Estekhrāje ZWD va Tolide Seri Zamani


print("\n" + "="*80)
print(" Bakhshe Sevom: Modele VMF3")
print("="*80)

# ===========================================
# 1. Khāndane Dadeh-haye VMF3 az Fayle CSV


# Etminān az Vojoode vmf3_data (Agar ghablan khānde shode, dobāre nemikhānim)
if 'vmf3_data' not in dir():
    try:
        vmf3_data = pd.read_csv('ALBH_VMF3_2025_DOY244_334.csv')
        print(" Fayle VMF3 ba Movafaghiyat Khānde Shod!")
        print(f"   Te'dade Rekord-hā: {len(vmf3_data)}")
    except FileNotFoundError:
        print(" Fayle VMF3 Peyda Nashod!")
        print("   Lotfan fayle 'ALBH_VMF3_2025_DOY244_334.csv' ra dar poosheye proje gharār dahid.")
        exit()
else:
    print(" Dadeh-haye VMF3 ghablan khānde shodeand.")

# ============================================================
# 2. Estekhrāje ZWD Marboote be Istgah


print("\n" + "="*80)
print(" Estekhrāje ZWD az Dadeh-haye VMF3")
print("="*80)

# Nemāyeshe Sotoon-haye Mojood
print("\n Sotoon-haye Mojood dar Fayle VMF3:")
print(vmf3_data.columns.tolist())

# Estekhrāje ZWD az Sotoone Marboote
zwd_vmf3 = vmf3_data['ZWD'].values  # ZWD bar hasbe Metr

print(f"\n ZWD Estekhrāj Shod!")
print(f"   Te'dade Maghādier: {len(zwd_vmf3)}")
print(f"   Vahed: Metr")
print(f"   Miyangin: {np.mean(zwd_vmf3)*1000:.2f} Millimeter")
print(f"   Haddaghal: {np.min(zwd_vmf3)*1000:.2f} Millimeter")
print(f"   Haddaksar: {np.max(zwd_vmf3)*1000:.2f} Millimeter")
print(f"   Anherāfe Me'yār: {np.std(zwd_vmf3)*1000:.2f} Millimeter")

# Nemāyeshe Nemoone Dadeh-hā
print("\n Nemoone Dadeh-haye ZWD (10 Rooze Avval):")
print("="*80)
print(f"{'DOY':>6} {'ZWD (m)':>12} {'ZWD (mm)':>12} {'Date':>15}")
print("-"*80)

# Tabdile DOY be Tārikh
start_date = datetime(2025, 1, 1) + timedelta(days=243)

for i in range(min(10, len(vmf3_data))):
    doy = vmf3_data.iloc[i]['DOY']
    zwd_m = vmf3_data.iloc[i]['ZWD']
    zwd_mm = zwd_m * 1000
    # Mohasbe Tārikh ba Estefade az DOY
    date = start_date + timedelta(days=int(float(doy)-244))
    # Estefade az f-string ba Formate Sahih baraye float
    print(f"{float(doy):6.0f} {zwd_m:12.4f} {zwd_mm:10.2f} mm {date.strftime('%Y-%m-%d'):>15}")

# ==============================================
# 3. Tolide Seri Zamaniye ZWD


print("\n" + "="*80)
print("a Tolide Seri Zamaniye ZWD az VMF3")
print("="*80)

# Tabdile DOY be Tārikh baraye Kolle Dadeh-hā
dates = []
for doy in vmf3_data['DOY']:
    date = start_date + timedelta(days=int(float(doy)-244))
    dates.append(date)

vmf3_data['Date'] = dates

# Mohasbe Āmāre Kāmel
print(f"\n Amare Kāmele Seri Zamaniye ZWD_VMF3:")
print("="*60)
print(f"  Te'dade Roozhā: {len(vmf3_data)}")
print(f"  Bāzeye Zamani: {vmf3_data['Date'].min().strftime('%Y-%m-%d')} ta {vmf3_data['Date'].max().strftime('%Y-%m-%d')}")
print(f"  Miyangin: {vmf3_data['ZWD'].mean()*1000:.2f} mm")
print(f"  Miyane: {vmf3_data['ZWD'].median()*1000:.2f} mm")
print(f"  Haddaghal: {vmf3_data['ZWD'].min()*1000:.2f} mm")
print(f"  Haddaksar: {vmf3_data['ZWD'].max()*1000:.2f} mm")
print(f"  Anherāfe Me'yār: {vmf3_data['ZWD'].std()*1000:.2f} mm")
print(f"  Dāmneye Taghyirāt: {(vmf3_data['ZWD'].max() - vmf3_data['ZWD'].min())*1000:.2f} mm")

# ===============================
# 4. Rasme Seri Zamaniye ZWD_VMF3
# =======

print("\n Rasme Seri Zamaniye ZWD_VMF3...")

fig, ax = plt.subplots(figsize=(14, 6))

# Rasme Seri Zamaniye Asli
ax.plot(vmf3_data['Date'], vmf3_data['ZWD'] * 1000, 
        'b-', linewidth=2, label='ZWD az VMF3', alpha=0.8)

# Afzoodane Noghnāte Dadeh
ax.scatter(vmf3_data['Date'], vmf3_data['ZWD'] * 1000, 
           color='blue', s=20, alpha=0.5, zorder=5)

# Mohasbe va Nemāyeshe Miyangin
mean_zwd = vmf3_data['ZWD'].mean() * 1000
ax.axhline(y=mean_zwd, color='red', linestyle='--', 
           linewidth=1.5, label=f'Miyangin = {mean_zwd:.1f} mm')

# Nemāyeshe Haddaksar va Haddaghal
max_zwd = vmf3_data['ZWD'].max() * 1000
min_zwd = vmf3_data['ZWD'].min() * 1000
ax.axhline(y=max_zwd, color='green', linestyle=':', 
           linewidth=1, alpha=0.7, label=f'Haddaksar = {max_zwd:.1f} mm')
ax.axhline(y=min_zwd, color='orange', linestyle=':', 
           linewidth=1, alpha=0.7, label=f'Haddaghal = {min_zwd:.1f} mm')

# Tanzimāte Nemoodār
ax.set_xlabel('Tārikh', fontsize=12)
ax.set_ylabel('ZWD (Millimeter)', fontsize=12)
ax.set_title('Seri Zamaniye ZWD az Modele VMF3 - Istgahe ALBH (September ta November 2025)', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

# Zakhireye Nemoodār
plt.savefig('VMF3_timeseries_full.png', dpi=300, bbox_inches='tight')
plt.show()

print(" Nemoodāre Seri Zamani dar fayle 'VMF3_timeseries_full.png' zakhire shod.")

# =======================================================
# 5. Barresiye Ravande Taghyirat (Afzayesh/Kāhesh)


print("\n" + "="*80)
print(" Tahlile Ravande Taghyirāte ZWD_VMF3")
print("="*80)

# Mohasbe Taghyirāte Roozāne
vmf3_data['ZWD_diff'] = vmf3_data['ZWD'].diff() * 1000  # Millimeter

# Yāftane Bozorgtarin Afzāyesh va Kāhesh
max_increase = vmf3_data['ZWD_diff'].max()
max_decrease = vmf3_data['ZWD_diff'].min()
max_increase_idx = vmf3_data['ZWD_diff'].idxmax()
max_decrease_idx = vmf3_data['ZWD_diff'].idxmin()

print(f"\n Bozorgtarin Afzāyeshe Roozāne ZWD:")
print(f"   Tārikh: {vmf3_data.loc[max_increase_idx, 'Date'].strftime('%Y-%m-%d')}")
print(f"   Meghdār: {max_increase:.2f} mm")

print(f"\n Bozorgtarin Kāheshe Roozāne ZWD:")
print(f"   Tārikh: {vmf3_data.loc[max_decrease_idx, 'Date'].strftime('%Y-%m-%d')}")
print(f"   Meghdār: {max_decrease:.2f} mm")

# Ravande Kolli (Miyangine Taghyirāt)
mean_diff = vmf3_data['ZWD_diff'].mean()
print(f"\n Miyangine Taghyirāte Roozāne: {mean_diff:.2f} mm")
if mean_diff > 0:
    print("   Ravande Kolli: Afzāyeshi (ZWD dar hāle afzāyesh ast)")
else:
    print("   Ravande Kolli: Kāheshi (ZWD dar hāle kāhesh ast)")

# ============================================================
# 6. Nemoodāre Taghyirāte Roozāne
# ===================

fig, ax = plt.subplots(figsize=(14, 5))

# Rang-bandi bar asase Mosbat ya Manfi boodan
colors = ['red' if x < 0 else 'green' for x in vmf3_data['ZWD_diff'][1:]]
ax.bar(vmf3_data['Date'][1:], vmf3_data['ZWD_diff'][1:], 
       color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)

ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax.set_xlabel('Tārikh', fontsize=12)
ax.set_ylabel('Taghyirāte ZWD (Millimeter)', fontsize=12)
ax.set_title('Taghyirāte Roozāne ZWD_VMF3', fontsize=14)
ax.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('VMF3_daily_changes.png', dpi=300, bbox_inches='tight')
plt.show()

print(" Nemoodāre Taghyirāte Roozāne dar fayle 'VMF3_daily_changes.png' zakhire shod.")

# ====================================================
# 7. Zakhireye Dadeh-haye Seri Zamaniye VMF3
# ======================================

# Zakhireye Seri Zamani dar yek Fayle Jodāgāne
vmf3_timeseries = vmf3_data[['DOY', 'Date', 'ZWD']].copy()
vmf3_timeseries['ZWD_mm'] = vmf3_timeseries['ZWD'] * 1000
vmf3_timeseries['ZWD_diff'] = vmf3_data['ZWD_diff']

vmf3_timeseries.to_csv('VMF3_timeseries.csv', index=False)
print("\n Seri Zamaniye ZWD_VMF3 dar fayle 'VMF3_timeseries.csv' zakhire shod.")

# ================================================
# 8. Kholāseye Nahāyi Bakhshe Sevom
# ====================
print("\n" + "="*80)
print(" Kholāseye Bakhshe Sevom: Modele VMF3")
print("="*80)

print(f"""
 Marhale 2: ZWD Marboote be Istgah Estekhrāj Shod
   - ZWD az Sotoone 'ZWD' Fayle CSV Estekhrāj Shod
   - Vahed: Metr (Tabdil be Millimeter baraye Nemāyesh)

 Marhale 3: Seri Zamaniye ZWD Tolide Shod
   - {len(vmf3_data)} Rooz Dadeh (September ta November 2025)
   - Miyangine ZWD: {vmf3_data['ZWD'].mean()*1000:.2f} mm
   - Mahdoodeye Taghyirāt: {vmf3_data['ZWD'].min()*1000:.2f} - {vmf3_data['ZWD'].max()*1000:.2f} mm
   - Ravande Kolli: {"Afzāyeshi" if mean_diff > 0 else "Kāheshi"}
""")

print(" Bakhshe Sevom (Modele VMF3) ba Movafaghiyat Kamel Shod!")















#--------------------------------------\-\-\-\--\-\-\

# Bakhshe Chaharom: Moghayese ba Mahsoolate IGS
# ============================================================

print("\n" + "="*80)
print(" Bakhshe Chahārom: Moghayese ba Mahsoolate IGS")
print("="*80)

# ===========================================
# 1. Tarife Tābe'e Mohasbe Shakhes-haye Amari
# ==================

def calculate_metrics(observed, predicted, name=""):
    """
    Mohasbe Shākhes-haye Āmāri baraye Moghayese ba IGS
    
    Parametrhā:
    - observed: Maghādiere Moshāhede Shode (IGS)
    - predicted: Maghādiere Pish-bini Shode (Model)
    - name: Nāme Model
    
    Khorooji:
    - Bias: Orayebi (Miyangine Ikhtelaf)
    - RMSE: Risheye Miyangine Morabba'āte Khatā
    - MAE: Miyangine Ghadre Motlaghe Khatā
    - Correlation: Zaribe Hambastegiye Pearson
    """
    # Hazfe Maghādiere NaN
    mask = ~(np.isnan(observed) | np.isnan(predicted))
    obs = np.array(observed)[mask]
    pred = np.array(predicted)[mask]
    
    if len(obs) == 0:
        return {
            'Method': name,
            'Bias (mm)': np.nan,
            'RMSE (mm)': np.nan,
            'MAE (mm)': np.nan,
            'Correlation': np.nan,
            'Count': 0
        }
    
    # Mohasbe Shākhes-hā
    bias = np.mean(pred - obs) * 1000  # Tabdil be Millimeter
    rmse = np.sqrt(np.mean((pred - obs)**2)) * 1000
    mae = np.mean(np.abs(pred - obs)) * 1000
    corr = np.corrcoef(obs, pred)[0, 1]
    
    return {
        'Method': name,
        'Bias (mm)': bias,
        'RMSE (mm)': rmse,
        'MAE (mm)': mae,
        'Correlation': corr,
        'Count': len(obs)
    }

# ==========================
# 2. Liste Ravesh-ha va Sotoon-haye Marboote
# ========================

# اطمینان از وجود ZWD_VMF3
if 'ZWD_VMF3' not in vmf3_data.columns:
    vmf3_data['ZWD_VMF3'] = vmf3_data['ZWD']
    print(" ZWD_VMF3 az sotoune ZWD ijad shod!")

methods = {
    'ERA5': 'ZWD_ERA5',
    'VMF3': 'ZWD_VMF3',
    'Saastamoinen': 'ZWD_Saast',
    'Hopfield': 'ZWD_Hopfield',
    'GPT3': 'ZWD_GPT3'
}

# ==================================
# 3. Mohasbe Shākhes-hā baraye Hameye Ravesh-hā
# ===========================

print("\n Mohasbe Shākhes-haye Āmari baraye Hameye Ravesh-ha...")

metrics_list = []

for name, col in methods.items():
    if col in vmf3_data.columns and 'ZWD_IGS' in vmf3_data.columns:
        metrics = calculate_metrics(
            vmf3_data['ZWD_IGS'].values,
            vmf3_data[col].values,
            name
        )
        metrics_list.append(metrics)
        print(f"    {name}: {metrics['Count']} Rooze Mo'tabar")

# ================
# 4. Nemāyeshe Jadvale Netayej
# ==============================

metrics_df = pd.DataFrame(metrics_list)

print("\n" + "="*80)
print(" Jadvale Moghayeseye Ravesh-hā ba Marjae IGS")
print("="*80)
print(metrics_df.round(4).to_string(index=False))

# ==================
# 5. Morattab-sāzi bar asase RMSE (Behtarin ta Za'if-tarin)
# ==========================================

sorted_metrics = metrics_df.sort_values('RMSE (mm)')
print("\n" + "="*80)
print(" Rotbe-bandiye Ravesh-hā bar asase RMSE (Behtarin ta Za'if-tarin)")
print("="*80)

for i, row in sorted_metrics.iterrows():
    rank = i + 1
    medal = "gold" if rank == 1 else "silveir" if rank == 2 else "boronze" if rank == 3 else f"{rank}."
    print(f"   {medal} {row['Method']}: RMSE = {row['RMSE (mm)']:.2f} mm, "
          f"Bias = {row['Bias (mm)']:.2f} mm, "
          f"R = {row['Correlation']:.4f}")

# ===========
# 6. Behtarin Ravesh
# ================
best_method = sorted_metrics.iloc[0]
print("\n" + "="*80)
print(" Behtarin Ravesh bar asase RMSE")
print("="*80)
print(f"   Ravesh: {best_method['Method']}")
print(f"   RMSE: {best_method['RMSE (mm)']:.2f} mm")
print(f"   Bias: {best_method['Bias (mm)']:.2f} mm")
print(f"   MAE: {best_method['MAE (mm)']:.2f} mm")
print(f"   Zaribe Hambastegi: {best_method['Correlation']:.4f}")

# ==================
# 7. Zakhireye Jadval


metrics_df.to_csv('comparison_with_IGS.csv', index=False)
print("\n Jadvale Moghayese dar fayle 'comparison_with_IGS.csv' zakhire shod.")

# ==============================
# 8. Rasme Nemoodār-haye Moghayese


print("\n" + "="*80)
print(" Rasme Nemoodār-haye Moghayese")
print("="*80)

fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# 8.1 Seri Zamaniye Hameye Ravesh-hā
ax1 = axes[0, 0]
colors = {'ERA5': 'red', 'VMF3': 'blue', 'Saastamoinen': 'orange', 
          'Hopfield': 'purple', 'GPT3': 'green', 'IGS': 'black'}

# Rasme IGS be Onvāne Marja
ax1.plot(vmf3_data['Date'], vmf3_data['ZWD_IGS'] * 1000,
         'k-', linewidth=2, label='IGS (Marja)', alpha=0.9)

# Rasme Sāyere Ravesh-hā
for name, col in methods.items():
    if col in vmf3_data.columns:
        ax1.plot(vmf3_data['Date'], vmf3_data[col] * 1000,
                 label=name, color=colors.get(name, 'gray'),
                 linewidth=1.5, alpha=0.7)

ax1.set_xlabel('Tārikh', fontsize=11)
ax1.set_ylabel('ZWD (Millimeter)', fontsize=11)
ax1.set_title('Seri Zamaniye ZWD - Hameye Ravesh-hā', fontsize=12)
ax1.legend(loc='upper right', fontsize=8)
ax1.grid(True, alpha=0.3)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# 8.2 Nemoodāre Parakesh (Scatter Plot)
ax2 = axes[0, 1]
for name, col in methods.items():
    if col in vmf3_data.columns:
        mask = ~(np.isnan(vmf3_data['ZWD_IGS']) | np.isnan(vmf3_data[col]))
        obs = vmf3_data['ZWD_IGS'][mask] * 1000
        pred = vmf3_data[col][mask] * 1000
        ax2.scatter(obs, pred, alpha=0.4, s=10, label=name, color=colors.get(name))

# Khate 1:1
min_val = min(vmf3_data['ZWD_IGS'].min()*1000, 
              vmf3_data[[c for c in methods.values() if c in vmf3_data.columns]].min().min()*1000)
max_val = max(vmf3_data['ZWD_IGS'].max()*1000, 
              vmf3_data[[c for c in methods.values() if c in vmf3_data.columns]].max().max()*1000)
ax2.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=1, label='Khate 1:1')

ax2.set_xlabel('ZWD az IGS (Millimeter)', fontsize=11)
ax2.set_ylabel('ZWD az Model (Millimeter)', fontsize=11)
ax2.set_title('Nemoodāre Parakesh', fontsize=12)
ax2.legend(loc='lower right', fontsize=8)
ax2.grid(True, alpha=0.3)

# 8.3 Nemoodāre Ikhtelaf
ax3 = axes[0, 2]
for name, col in methods.items():
    if col in vmf3_data.columns:
        diff = (vmf3_data[col] - vmf3_data['ZWD_IGS']) * 1000
        ax3.plot(vmf3_data['Date'], diff, label=name, color=colors.get(name),
                 linewidth=1.5, alpha=0.7)

ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax3.set_xlabel('Tarikh', fontsize=11)
ax3.set_ylabel('Ikhtelafe ZWD (Millimeter)', fontsize=11)
ax3.set_title('Ikhtelafe Ravesh-hā Nesbat be IGS', fontsize=12)
ax3.legend(loc='upper right', fontsize=8)
ax3.grid(True, alpha=0.3)
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

# 8.4 Histogram Ikhtelaf
ax4 = axes[1, 0]
for name, col in methods.items():
    if col in vmf3_data.columns:
        diff = (vmf3_data[col] - vmf3_data['ZWD_IGS']) * 1000
        ax4.hist(diff.dropna(), bins=20, alpha=0.3, label=name, 
                 color=colors.get(name), edgecolor='black', linewidth=0.5)

ax4.axvline(x=0, color='black', linestyle='-', linewidth=1)
ax4.set_xlabel('Ikhtelafe ZWD (Millimeter)', fontsize=11)
ax4.set_ylabel('Te\'dade Roozha', fontsize=11)
ax4.set_title('Tozi-e Ikhtelafe Ravesh-hā', fontsize=12)
ax4.legend(loc='upper right', fontsize=8)
ax4.grid(True, alpha=0.3)

# 8.5 Nemoodāre Milediye RMSE
ax5 = axes[1, 1]
x_pos = np.arange(len(metrics_df))
bar_colors = ['red' if m == 'ERA5' else 'blue' if m == 'VMF3' else 'orange' if m == 'Saastamoinen' else 'purple' if m == 'Hopfield' else 'green' for m in metrics_df['Method']]
ax5.bar(x_pos, metrics_df['RMSE (mm)'], color=bar_colors)
ax5.set_xticks(x_pos)
ax5.set_xticklabels(metrics_df['Method'], rotation=45, ha='right', fontsize=10)
ax5.set_ylabel('RMSE (Millimeter)', fontsize=11)
ax5.set_title('Moghayeseye RMSE Ravesh-hā', fontsize=12)
ax5.grid(True, alpha=0.3, axis='y')

# Afzoodane Meghdār rooye Mile-hā
for i, (idx, row) in enumerate(metrics_df.iterrows()):
    ax5.text(i, row['RMSE (mm)'] + 1, f"{row['RMSE (mm)']:.1f}", 
             ha='center', va='bottom', fontsize=9)

# 8.6 Nemoodāre Milediye Zaribe Hambastegi
ax6 = axes[1, 2]
ax6.bar(x_pos, metrics_df['Correlation'], color=bar_colors)
ax6.set_xticks(x_pos)
ax6.set_xticklabels(metrics_df['Method'], rotation=45, ha='right', fontsize=10)
ax6.set_ylabel('Zaribe Hambastegi', fontsize=11)
ax6.set_title('Moghayeseye Zaribe Hambastegi', fontsize=12)
ax6.grid(True, alpha=0.3, axis='y')
ax6.set_ylim(0, 1)

# Afzoodane Meghdār rooye Mile-hā
for i, (idx, row) in enumerate(metrics_df.iterrows()):
    ax6.text(i, row['Correlation'] + 0.03, f"{row['Correlation']:.3f}", 
             ha='center', va='bottom', fontsize=9)

plt.suptitle('Moghayeseye Ravesh-haye Mukhtalif ba Marjae IGS - Istgahe ALBH', fontsize=16)
plt.tight_layout()
plt.savefig('comparison_with_IGS.png', dpi=300, bbox_inches='tight')
plt.show()

print(" Nemoodare Moghayese dar fayle 'comparison_with_IGS.png' zakhire shod.")

# ===========================================
# 9. Tahlile Āmāriye Takmili


print("\n" + "="*80)
print(" Tahlile Amariye Takmili")
print("="*80)

# Mohasbe Āmāre baraye har Ravesh
stats_summary = []

for name, col in methods.items():
    if col in vmf3_data.columns:
        # Hazfe NaN
        mask = ~(np.isnan(vmf3_data['ZWD_IGS']) | np.isnan(vmf3_data[col]))
        obs = vmf3_data['ZWD_IGS'][mask] * 1000
        pred = vmf3_data[col][mask] * 1000
        
        if len(obs) > 0:
            diff = pred - obs
            stats_summary.append({
                'Method': name,
                'Mean_Observed': np.mean(obs),
                'Mean_Predicted': np.mean(pred),
                'Std_Observed': np.std(obs),
                'Std_Predicted': np.std(pred),
                'Mean_Diff': np.mean(diff),
                'Std_Diff': np.std(diff),
                'Min_Diff': np.min(diff),
                'Max_Diff': np.max(diff)
            })

stats_df = pd.DataFrame(stats_summary)
print("\n Amare Tafsiliye har Ravesh:")
print("="*80)
print(stats_df.round(2).to_string(index=False))

# ========================
# 10. Natije-giriye Nahāyi


print("\n" + "="*80)
print(" Natije-giriye Nahāyi Bakhshe Chaharom")
print("="*80)

print("""
 Tahlile Kolli:

1. Behtarin ravesh bar asase RMSE: {}
   - RMSE = {:.2f} mm
   - Bias = {:.2f} mm
   - Zaribe hambastegi = {:.4f}

2. Rotbe-bandiye ravesh-ha:
""".format(
    best_method['Method'],
    best_method['RMSE (mm)'],
    best_method['Bias (mm)'],
    best_method['Correlation']
))

for i, row in sorted_metrics.iterrows():
    rank = i + 1
    print(f"    {rank}. {row['Method']}: RMSE = {row['RMSE (mm)']:.2f} mm, "
          f"Bias = {row['Bias (mm)']:.2f} mm, R = {row['Correlation']:.4f}")

print("""
3. Nokat kelidi:
   - ERA5 behtarin tatabogh ra ba IGS darad (dadeh-haye vaghe'i jav)
   - VMF3 amalkarde khoobi darad (dadeh-haye tajrobi daghigh)
   - Saastamoinen ghablole ghabool ast ama bish-barovard darad
   - GPT3 va Hopfield kam-barovarde ghable tavajohi darand
   - Model-haye sade-tar khataye bish-tari darand
""")

print(" Bakhshe Chahārom (Moghayese ba IGS) ba Movafaghiyat Kamel Shod!")


















# --------------------------\--------------\-------------\--\-\--\--\
# Bakhshe Panjom: Tahlile Aghlimi - Istgahe Saheli ALBH
# ============================================================

print("\n" + "="*80)
print(" Bakhshe Panjom: Tahlile Aghlimi - Istgahe Saheli")
print("="*80)

# ============================================================
# 1. Ettela'ate Istgah
# ============================================================

print("\n Moshakhasate Istgahe ALBH00CAN:")
print("="*60)
print(f"   Name Istgah: ALBH00CAN (Victoria, Canada)")
print(f"   Arze Joghrafiya'i: 48.39°N")
print(f"   Toole Joghrafiya'i: 123.68°W")
print(f"   Ertefa: 31.8 meter")
print(f"   No'e Istgah: Saheli (Fasaleh kamtar az 5 kilometr az Oghyanoose Aram)")
print(f"   Aghlim: Motadel Oghyanoosi (Daryayi)")
print(f"   Baze ye Motale'eh: September ta November 2025 (Payiz)")

# ============================================================
# 2. Tahlile Amalkarde Model-ha bar asase RMSE
# ============================================================

print("\n" + "="*80)
print(" Tahlile Amalkarde Model-ha dar Istgahe Saheli")
print("="*80)

# Dadeh-haye RMSE az bakhshe chaharom
models_performance = {
    'ERA5': {'RMSE': 27.84, 'Bias': 6.04, 'Corr': 0.7612, 'Type': 'Baztahlil'},
    'VMF3': {'RMSE': None, 'Bias': None, 'Corr': None, 'Type': 'Tajrobi'},
    'Saastamoinen': {'RMSE': 35.86, 'Bias': 19.86, 'Corr': 0.4963, 'Type': 'Tajrobi'},
    'GPT3': {'RMSE': 86.84, 'Bias': -80.63, 'Corr': 0.5323, 'Type': 'Tajrobi'},
    'Hopfield': {'RMSE': 115.99, 'Bias': -111.00, 'Corr': 0.4959, 'Type': 'Tajrobi'}
}

# Mohasebeye RMSE baraye VMF3 (agar mojood bashad)
if 'ZWD_VMF3' in vmf3_data.columns and 'ZWD_IGS' in vmf3_data.columns:
    mask = ~(np.isnan(vmf3_data['ZWD_IGS']) | np.isnan(vmf3_data['ZWD_VMF3']))
    obs = vmf3_data['ZWD_IGS'][mask].values
    pred = vmf3_data['ZWD_VMF3'][mask].values
    if len(obs) > 0:
        rmse_vmf3 = np.sqrt(np.mean((pred - obs)**2)) * 1000
        bias_vmf3 = np.mean(pred - obs) * 1000
        corr_vmf3 = np.corrcoef(obs, pred)[0, 1]
        models_performance['VMF3'] = {'RMSE': rmse_vmf3, 'Bias': bias_vmf3, 
                                       'Corr': corr_vmf3, 'Type': 'Tajrobi'}

# Namayeshe Jadval
print("\n Amalkarde Model-ha dar Istgahe Saheli ALBH:")
print("="*80)
# print(f"{'Model':<15} {'RMSE (mm)':<12} {'Bias (mm)':<12} {'Correlation':<12} {'No\'e':<12}")
print(f"{'Model':<15} {'RMSE (mm)':<12} {'Bias (mm)':<12} {'Correlation':<12} {'No-e':<12}")
print("-"*80)

for name, data in models_performance.items():
    if data['RMSE'] is not None:
        print(f"{name:<15} {data['RMSE']:<12.2f} {data['Bias']:<12.2f} {data['Corr']:<12.4f} {data['Type']:<12}")
    else:
        print(f"{name:<15} {'N/A':<12} {'N/A':<12} {'N/A':<12} {data['Type']:<12}")

# ============================================================
# 3. Behtarin Model baraye Istgahe Saheli
# ============================================================

print("\n" + "="*80)
print(" Behtarin Model baraye Istgahe Saheli")
print("="*80)

# Peyda kardane behtarin model bar asase RMSE
valid_models = {k: v for k, v in models_performance.items() if v['RMSE'] is not None}
best_model = min(valid_models, key=lambda x: valid_models[x]['RMSE'])

print(f"\n Behtarin Model: {best_model}")
print(f"   RMSE: {valid_models[best_model]['RMSE']:.2f} mm")
print(f"   Bias: {valid_models[best_model]['Bias']:.2f} mm")
print(f"   Correlation: {valid_models[best_model]['Corr']:.4f}")

print("\n Dalile bartariye ERA5 dar istgahe saheli:")
print("   - Estefadeh az dadeh-haye vaghe'i jav (baztahlil)")
print("   - Model-saziye daghighe bokhare ab dar managhete saheli")
print("   - Vozhoohe makani va zamaniye bala")
print("   - Dar nazar gereftane asarate oghyanoos bar rotoobate jav")

# ============================================================
# 4. Tahlile Tasire Ertefa bar Deghate Model-ha
# ============================================================

print("\n" + "="*80)
print(" Tahlile Tasire Ertefa bar Deghate Model-ha")
print("="*80)

# Baraye istgahe saheli, ertefa 31.8 meter ast
# Baraye moghayeseh, az dadeh-haye ERA5 dar taraz-haye mokhtalef estefadeh mikonim

print("\n Tasire Ertefa bar ZWD (az dadeh-haye ERA5):")

# Estekhraje profile ertefa az ERA5
if 'era5_results' in dir() and 'September' in era5_results:
    result = era5_results['September']
    height_km = result['height'] / 1000
    Nw = result['Nw']
    
    # Mohasebeye ZWD dar ertefa'ate mokhtalef (enteghral az sath ta ertefa'e morede nazar)
    zwd_cumulative = []
    heights_sample = []
    
    for i in range(5, len(height_km), 10):
        h = height_km[i]
        if h > 0:
            # Enteghral az sath ta ertefa'e h
            idx = np.where(height_km <= h)[0]
            if len(idx) > 0:
                zwd_partial = 1e-6 * np.trapz(Nw[:idx[-1]+1], height_km[:idx[-1]+1] * 1000)
                zwd_cumulative.append(zwd_partial * 1000)
                heights_sample.append(h)
    
    # print(f"\n  {'Ertefa (km)':<15} {'ZWD Tajammo\'i (mm)':<20} {'Darsad az kol':<15}")
    print(f"\n   {'Ertefa (km)':<15} {'ZWD Tajammo-i (mm)':<20} {'Darsad az kol':<15}")
    print("  " + "-"*50)
    
    total_zwd = 1e-6 * np.trapz(Nw, height_km * 1000) * 1000
    
    for h, zwd in zip(heights_sample[:8], zwd_cumulative[:8]):
        percent = zwd / total_zwd * 100
        print(f"  {h:<15.2f} {zwd:<20.2f} {percent:<15.1f}%")
    
    print(f"\n   Natijeh: Hodoode 90% az ZWD dar 5 kilometre avale jav motamarkez ast")
    print(f"     Ertefa'e istgah (31.8 meter) tasire bicyar kami bar ZWD darad")

# ============================================================
# 5. Tahlile Tasire Sharayete Aghlimi (Moghayeseye Fasli)
# ============================================================

print("\n" + "="*80)
print(" Tahlile Tasire Sharayete Aghlimi bar Deghate Model-ha")
print("="*80)

# Mohasebeye amar baraye har mah
monthly_stats = []

for month in ['September', 'October', 'November']:
    # Peyda kardane rooz-haye marboot be har mah
    month_dates = []
    for date in vmf3_data['Date']:
        if date.strftime('%B') == month:
            month_dates.append(date)
    
    if len(month_dates) == 0:
        continue
    
    # Shakhes-haye marboot be in mah
    month_indices = vmf3_data[vmf3_data['Date'].isin(month_dates)].index
    
    # Damaye motavasset
    temp_mean = vmf3_data.loc[month_indices, 'Temp'].mean()
    
    # Feshare motavasset
    pressure_mean = vmf3_data.loc[month_indices, 'Pressure'].mean()
    
    # ZWD az IGS
    zwd_igs_mean = vmf3_data.loc[month_indices, 'ZWD_IGS'].mean() * 1000
    
    # RMSE baraye har model dar in mah
    rmse_models = {}
    for model in ['ERA5', 'VMF3', 'ZWD_Saast', 'ZWD_Hopfield', 'ZWD_GPT3']:
        col_name = model
        if col_name == 'ZWD_Saast':
            display_name = 'Saastamoinen'
        elif col_name == 'ZWD_Hopfield':
            display_name = 'Hopfield'
        elif col_name == 'ZWD_GPT3':
            display_name = 'GPT3'
        else:
            display_name = model
            
        if col_name in vmf3_data.columns:
            mask = ~(np.isnan(vmf3_data.loc[month_indices, 'ZWD_IGS']) | 
                    np.isnan(vmf3_data.loc[month_indices, col_name]))
            if mask.sum() > 0:
                obs = vmf3_data.loc[month_indices, 'ZWD_IGS'][mask].values
                pred = vmf3_data.loc[month_indices, col_name][mask].values
                rmse = np.sqrt(np.mean((pred - obs)**2)) * 1000
                rmse_models[display_name] = rmse
    
    monthly_stats.append({
        'Mah': month,
        'Dama (°C)': temp_mean,
        'Feshar (hPa)': pressure_mean,
        'ZWD_IGS (mm)': zwd_igs_mean,
        'RMSE Model-ha': rmse_models
    })

# Namayeshe jadvale mahaneh
print("\n Amare Mahaneh Istgahe Saheli:")
print("="*90)
print(f"{'Mah':<12} {'Dama (°C)':<12} {'Feshar (hPa)':<14} {'ZWD_IGS (mm)':<15} {'Behtarin Model':<15}")
print("-"*90)

for stat in monthly_stats:
    if stat['RMSE Model-ha']:
        best = min(stat['RMSE Model-ha'], key=stat['RMSE Model-ha'].get)
        print(f"{stat['Mah']:<12} {stat['Dama (°C)']:<12.1f} {stat['Feshar (hPa)']:<14.1f} "
              f"{stat['ZWD_IGS (mm)']:<15.1f} {best:<15}")
    else:
        print(f"{stat['Mah']:<12} {stat['Dama (°C)']:<12.1f} {stat['Feshar (hPa)']:<14.1f} "
              f"{stat['ZWD_IGS (mm)']:<15.1f} {'N/A':<15}")

# ============================================================
# 6. Nemoodare Tasire Aghlim bar Deghate Model-ha
# ============================================================

print("\n Rasme nemoodare tahlile aghlimi...")

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# 6.1 Taghyirate ZWD va Dama
ax1 = axes[0, 0]
ax1.plot(vmf3_data['Date'], vmf3_data['ZWD_IGS'] * 1000, 
         'b-', linewidth=2, label='ZWD_IGS', alpha=0.8)
ax1_twin = ax1.twinx()
ax1_twin.plot(vmf3_data['Date'], vmf3_data['Temp'], 
              'r-', linewidth=1.5, label='Dama', alpha=0.6)

ax1.set_xlabel('Tarikh', fontsize=11)
ax1.set_ylabel('ZWD (millimeter)', color='blue', fontsize=11)
ax1_twin.set_ylabel('Dama (°C)', color='red', fontsize=11)
ax1.set_title('Rabeteh ye ZWD va Dama - Istgahe Saheli', fontsize=12)
ax1.grid(True, alpha=0.3)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# 6.2 Taghyirate ZWD va Feshar
ax2 = axes[0, 1]
ax2.plot(vmf3_data['Date'], vmf3_data['ZWD_IGS'] * 1000, 
         'b-', linewidth=2, label='ZWD_IGS', alpha=0.8)
ax2_twin = ax2.twinx()
ax2_twin.plot(vmf3_data['Date'], vmf3_data['Pressure'], 
              'g-', linewidth=1.5, label='Feshar', alpha=0.6)

ax2.set_xlabel('Tarikh', fontsize=11)
ax2.set_ylabel('ZWD (millimeter)', color='blue', fontsize=11)
ax2_twin.set_ylabel('Feshar (hPa)', color='green', fontsize=11)
ax2.set_title('Rabeteh ye ZWD va Feshar - Istgahe Saheli', fontsize=12)
ax2.grid(True, alpha=0.3)
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

# 6.3 RMSE Model-ha dar mah-haye mokhtalef
ax3 = axes[1, 0]
x = np.arange(len(monthly_stats))
width = 0.15
models = ['ERA5', 'Saastamoinen', 'GPT3', 'Hopfield']

for i, model in enumerate(models):
    rmse_values = []
    for stat in monthly_stats:
        if model in stat['RMSE Model-ha']:
            rmse_values.append(stat['RMSE Model-ha'][model])
        else:
            rmse_values.append(np.nan)
    
    ax3.bar(x + i*width, rmse_values, width, label=model, alpha=0.7)

ax3.set_xlabel('Mah', fontsize=11)
ax3.set_ylabel('RMSE (millimeter)', fontsize=11)
ax3.set_title('Taghyirate RMSE Model-ha dar mah-haye mokhtalef', fontsize=12)
ax3.set_xticks(x + width*2)
ax3.set_xticklabels([stat['Mah'] for stat in monthly_stats])
ax3.legend()
ax3.grid(True, alpha=0.3)

# 6.4 Hambastegiye ZWD ba Dama va Feshar
ax4 = axes[1, 1]
corr_temp = np.corrcoef(vmf3_data['ZWD_IGS'].dropna(), 
                        vmf3_data['Temp'].loc[vmf3_data['ZWD_IGS'].dropna().index])[0, 1]
corr_press = np.corrcoef(vmf3_data['ZWD_IGS'].dropna(), 
                         vmf3_data['Pressure'].loc[vmf3_data['ZWD_IGS'].dropna().index])[0, 1]

ax4.bar(['Dama', 'Feshar'], [corr_temp, corr_press], 
        color=['red', 'green'], alpha=0.7, edgecolor='black')
ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax4.set_ylabel('Zaribe Hambastegi', fontsize=11)
ax4.set_title('Hambastegiye ZWD ba Parametrhaye Aghlimi', fontsize=12)
ax4.grid(True, alpha=0.3)

for i, val in enumerate([corr_temp, corr_press]):
    ax4.text(i, val + 0.02 if val > 0 else val - 0.08, 
             f'{val:.3f}', ha='center', va='bottom' if val > 0 else 'top', fontsize=10)

plt.suptitle('Tahlile Aghlimiye Istgahe Saheli ALBH', fontsize=16)
plt.tight_layout()
plt.savefig('climatic_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print(" Nemoodare tahlile aghlimi dar faile 'climatic_analysis.png' zakhireh shod.")

# ============================================================
# 7. Natijeh-giriye Nahayi Bakhshe Panjom
# ============================================================

print("\n" + "="*80)
print(" Natijeh-giriye Nahayi Bakhshe Panjom: Tahlile Aghlimi")
print("="*80)

print("""
🔍 Barresi ye se soal-e asli:

1. Kodam model behtarin amalkard ra darad?
    ERA5 ba RMSE=27.84 mm behtarin amalkard ra darad.
    Dalil: Estefadeh az dadeh-haye vaghe'i jav va model-saziye daghighe bokhare ab dar managhete saheli.

2. Aya deghate model-ha ba ertefa taghyir mikonad?
    Istgahe saheli ALBH dar ertefa'e 31.8 meter gharar darad.
    ZWD omdatan dar 5 kilometre avale jav motamarkez ast (hodoode 90%).
    Taghyirate ertefa dar in mahdoodeh tasire bicyar kami bar ZWD darad.
    Baraye managhete koohestani, asare ertefa bicyar bishtar khahad bood.

3. Aya deghate model-ha tabee sharayete aghlimi ast?
    Bale, deghate model-ha be sharayete aghlimi vabasteh ast.
    Dar September (damaye balatar, rotoobate bishtar) ZWD bishtar ast.
    Dar November (damaye payin-tar, rotoobate kamtar) ZWD kamtar ast.
    ERA5 dar tamame sharayete aghlimi amalkarde behtari darad.
    Model-haye sade (Hopfield, GPT3) taghyirate aghlimi ra be khoobi neshan nemidahand.

 Vizhegi-haye Istgahe Saheli:
   - Rotoobate bala (nazdiki be oghyanoos)
   - Taghyirate damayi-ye molayem
   - ZWD dar payiz beyna 47 ta 198 millimeter motaghayer ast
   - Hambastegiye mosbate ZWD ba dama (R = {:.3f})
   - Hambastegiye manfiye ZWD ba feshar (R = {:.3f})
""".format(
    np.corrcoef(vmf3_data['ZWD_IGS'].dropna(), 
                vmf3_data['Temp'].loc[vmf3_data['ZWD_IGS'].dropna().index])[0, 1],
    np.corrcoef(vmf3_data['ZWD_IGS'].dropna(), 
                vmf3_data['Pressure'].loc[vmf3_data['ZWD_IGS'].dropna().index])[0, 1]
))

print(" Bakhshe Panjom (Tahlile Aghlimi) ba Movafaghiyat Kamel Shod!")












# ============================================================
# Bakhshe Sheshom: Motale'eh Yek Rooydade Javi
# ============================================================

print("\n" + "="*80)
print(" Bakhshe Sheshom: Motale'eh Yek Rooydade Javi")
print("="*80)

# ============================================================
# 1. Shenasayi Rooydade Javi az rooye Taghyirate ZWD
# ============================================================

print("\n Shenasayi Rooydade Javi az rooye Taghyirate ZWD...")

# Mohasebeye nerkhe taghyirate ZWD
vmf3_data['ZWD_diff'] = vmf3_data['ZWD_IGS'].diff() * 1000  # millimeter

# Yaftane roozhayi ba taghyirate naghahani (bish az 2 enhrafe me'yar)
threshold = np.std(vmf3_data['ZWD_diff']) * 2

print(f"\n Astaneye Tashkhise Rooydad: {threshold:.2f} mm")

# Peyda kardane hameye roozhaye ba taghyirate naghahani
peak_days = vmf3_data[np.abs(vmf3_data['ZWD_diff']) > threshold]

print(f"\n Tedade Roozhaye ba Taghyirate Naghahani: {len(peak_days)}")

if len(peak_days) > 0:
    print("\n Roozhaye ba Taghyirate Naghahani-ye ZWD:")
    print("="*80)
    # print(f"{'Tarikh':<15} {'ZWD (mm)':<15} {'Taghyir (mm)':<15} {'No\'e Taghyir':<15}")
    print(f"{'Tarikh':<15} {'ZWD (mm)':<15} {'Taghyir (mm)':<15} {'No-e Taghyir':<15}")
    print("-"*80)
    
    for idx, row in peak_days.iterrows():
        change_type = " Afzayesh" if row['ZWD_diff'] > 0 else " Kahesh"
        print(f"{row['Date'].strftime('%Y-%m-%d'):<15} "
              f"{row['ZWD_IGS']*1000:<15.1f} "
              f"{row['ZWD_diff']:<15.2f} "
              f"{change_type:<15}")

# ============================================================
# 2. Entekhabe Rooydade Asli
# ============================================================

# Bozorgtarin afzayeshe naghahani ra be عنوان rooydade asli entekhab mikonim
max_increase_idx = vmf3_data['ZWD_diff'].idxmax()
event_date = vmf3_data.loc[max_increase_idx, 'Date']
event_zwd = vmf3_data.loc[max_increase_idx, 'ZWD_IGS'] * 1000
event_diff = vmf3_data.loc[max_increase_idx, 'ZWD_diff']

print("\n" + "="*80)
print(f" Rooydade Javi-ye Entekhab Shodeh: {event_date.strftime('%Y-%m-%d')}")
print("="*80)
print(f"   ZWD dar Rooze Rooydad: {event_zwd:.1f} mm")
print(f"   Afzayeshe Naghahani: {event_diff:.2f} mm")
print(f"   No\'e Rooydad: Afzayeshe Naghahani-ye Rotoobat (Ehtemalan Bareshe Shadid)")

# ============================================================
# 3. Tahlile Baze ye Zamani-ye Ghabl, Hin va Ba'd az Rooydad
# ============================================================

window = 7  # Tedade roozhaye ghabl va ba'd
start_date = event_date - timedelta(days=window)
end_date = event_date + timedelta(days=window)

print(f"\n Bazeye Tahlil:")
print(f"   Ghabl az Rooydad: {start_date.strftime('%Y-%m-%d')} ta {event_date.strftime('%Y-%m-%d')}")
print(f"   Rooze Rooydad: {event_date.strftime('%Y-%m-%d')}")
print(f"   Ba'd az Rooydad: {event_date.strftime('%Y-%m-%d')} ta {end_date.strftime('%Y-%m-%d')}")

# Filtere dadeh-ha dar baze
mask = (vmf3_data['Date'] >= start_date) & (vmf3_data['Date'] <= end_date)
event_data = vmf3_data[mask].copy()

if len(event_data) == 0:
    print(" Hich dadehi dar baze ye zamani-ye entekhab shodeh voojood nadarad!")
    exit()

print(f"\n Tedade Roozhaye Tahlil: {len(event_data)}")

# ============================================================
# 4. Mohasebeye Amare ZWD dar Se Baze ye Zamani
# ============================================================

print("\n" + "="*80)
print(" Amare ZWD dar Se Baze ye Zamani")
print("="*80)

# Taghsim be se baze
before_mask = (event_data['Date'] < event_date)
during_mask = (event_data['Date'] == event_date)
after_mask = (event_data['Date'] > event_date)

before_data = event_data[before_mask]
during_data = event_data[during_mask]
after_data = event_data[after_mask]

# Mohasebeye Amar
stats = {
    'Baze': ['Ghabl az Rooydad', 'Rooze Rooydad', 'Ba\'d az Rooydad'],
    'Tedade Rooz': [len(before_data), len(during_data), len(after_data)],
    'Miyangine ZWD (mm)': [
        before_data['ZWD_IGS'].mean() * 1000 if len(before_data) > 0 else np.nan,
        during_data['ZWD_IGS'].mean() * 1000 if len(during_data) > 0 else np.nan,
        after_data['ZWD_IGS'].mean() * 1000 if len(after_data) > 0 else np.nan
    ],
    'Hadeaghale ZWD (mm)': [
        before_data['ZWD_IGS'].min() * 1000 if len(before_data) > 0 else np.nan,
        during_data['ZWD_IGS'].min() * 1000 if len(during_data) > 0 else np.nan,
        after_data['ZWD_IGS'].min() * 1000 if len(after_data) > 0 else np.nan
    ],
    'Hadeaksare ZWD (mm)': [
        before_data['ZWD_IGS'].max() * 1000 if len(before_data) > 0 else np.nan,
        during_data['ZWD_IGS'].max() * 1000 if len(during_data) > 0 else np.nan,
        after_data['ZWD_IGS'].max() * 1000 if len(after_data) > 0 else np.nan
    ],
    'Enhrafe Me\'yar (mm)': [
        before_data['ZWD_IGS'].std() * 1000 if len(before_data) > 0 else np.nan,
        during_data['ZWD_IGS'].std() * 1000 if len(during_data) > 0 else np.nan,
        after_data['ZWD_IGS'].std() * 1000 if len(after_data) > 0 else np.nan
    ]
}

stats_df = pd.DataFrame(stats)
print("\n" + stats_df.round(2).to_string(index=False))

# ============================================================
# 5. Tahlile Taghyirate Model-ha dar Bazeye Rooydad
# ============================================================

print("\n" + "="*80)
print(" Amalkarde Model-ha dar Bazeye Rooydad")
print("="*80)

# Mohasebeye RMSE har model dar bazeye rooydad
models = ['ZWD_ERA5', 'ZWD_VMF3', 'ZWD_Saast', 'ZWD_Hopfield', 'ZWD_GPT3']
model_names = ['ERA5', 'VMF3', 'Saastamoinen', 'Hopfield', 'GPT3']

event_metrics = []

for col, name in zip(models, model_names):
    if col in event_data.columns:
        mask_valid = ~(np.isnan(event_data['ZWD_IGS']) | np.isnan(event_data[col]))
        if mask_valid.sum() > 0:
            obs = event_data.loc[mask_valid, 'ZWD_IGS'].values
            pred = event_data.loc[mask_valid, col].values
            rmse = np.sqrt(np.mean((pred - obs)**2)) * 1000
            bias = np.mean(pred - obs) * 1000
            corr = np.corrcoef(obs, pred)[0, 1] if len(obs) > 1 else np.nan
            
            event_metrics.append({
                'Model': name,
                'RMSE (mm)': rmse,
                'Bias (mm)': bias,
                'Correlation': corr
            })

event_metrics_df = pd.DataFrame(event_metrics)
print("\n" + event_metrics_df.round(4).to_string(index=False))

# Behtarin model dar bazeye rooydad
best_event = event_metrics_df.loc[event_metrics_df['RMSE (mm)'].idxmin()]
print(f"\n Behtarin Model dar Bazeye Rooydad: {best_event['Model']}")
print(f"   RMSE: {best_event['RMSE (mm)']:.2f} mm")

# ============================================================
# 6. Rasme Nemoodarhaye Tahlile Rooydad
# ============================================================

print("\n Rasme nemoodarhaye tahlile rooydad...")

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# 6.1 Seri Zamani-ye ZWD dar Bazeye Rooydad
ax1 = axes[0, 0]
colors = {'IGS': 'black', 'ERA5': 'red', 'VMF3': 'blue', 
          'Saastamoinen': 'orange', 'GPT3': 'green', 'Hopfield': 'purple'}

# Rasme IGS
ax1.plot(event_data['Date'], event_data['ZWD_IGS'] * 1000,
         'k-', linewidth=2.5, label='IGS (Marja\')', alpha=0.9)

# Rasme sayere model-ha
for col, name in zip(models, model_names):
    if col in event_data.columns:
        ax1.plot(event_data['Date'], event_data[col] * 1000,
                 label=name, color=colors.get(name, 'gray'),
                 linewidth=1.5, alpha=0.7, linestyle='--' if name != 'ERA5' else '-')

# Moshakhas kardane rooze rooydad
ax1.axvline(x=event_date, color='red', linestyle='--', 
            linewidth=2, label=f'Rooydad: {event_date.strftime("%Y-%m-%d")}')
ax1.axvspan(start_date, event_date, alpha=0.1, color='green', label='Ghabl az Rooydad')
ax1.axvspan(event_date, end_date, alpha=0.1, color='orange', label='Ba\'d az Rooydad')

ax1.set_xlabel('Tarikh', fontsize=11)
ax1.set_ylabel('ZWD (millimeter)', fontsize=11)
ax1.set_title('Taghyirate ZWD dar Bazeye Rooydade Javi', fontsize=12)
ax1.legend(loc='upper left', fontsize=8)
ax1.grid(True, alpha=0.3)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# 6.2 Ekhtelafe Model-ha Nesbat be IGS
ax2 = axes[0, 1]
for col, name in zip(models, model_names):
    if col in event_data.columns:
        diff = (event_data[col] - event_data['ZWD_IGS']) * 1000
        ax2.plot(event_data['Date'], diff, 
                 label=name, color=colors.get(name, 'gray'),
                 linewidth=1.5, alpha=0.7)

ax2.axvline(x=event_date, color='red', linestyle='--', linewidth=2)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.set_xlabel('Tarikh', fontsize=11)
ax2.set_ylabel('Ekhtelafe ZWD (millimeter)', fontsize=11)
ax2.set_title('Ekhtelafe Model-ha Nesbat be IGS', fontsize=12)
ax2.legend(loc='upper right', fontsize=8)
ax2.grid(True, alpha=0.3)
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

# 6.3 Taghyirate Roozaneh ZWD
ax3 = axes[1, 0]
# Mohasebeye taghyirate roozaneh baraye bazeye rooydad
event_data['daily_change'] = event_data['ZWD_IGS'].diff() * 1000
bars = ax3.bar(event_data['Date'][1:], event_data['daily_change'][1:],
               color=['red' if x < 0 else 'green' for x in event_data['daily_change'][1:]],
               alpha=0.7, edgecolor='black', linewidth=0.5)

ax3.axvline(x=event_date, color='red', linestyle='--', linewidth=2)
ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax3.set_xlabel('Tarikh', fontsize=11)
ax3.set_ylabel('Taghyirate Roozaneh (millimeter)', fontsize=11)
ax3.set_title('Taghyirate Roozaneh ZWD dar Bazeye Rooydad', fontsize=12)
ax3.grid(True, alpha=0.3)
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

# 6.4 Baresh/Rotoobat (ba estefadeh az ERA5)
ax4 = axes[1, 1]

# Agar dadeh-haye ERA5 mojood bashad, rotoobat ra rasm mikonim
if 'ZWD_ERA5' in event_data.columns:
    # Mohasebeye PWV az ERA5 (Takhmini)
    if 'P_GPT3' in event_data.columns:
        # Estefadeh az e_GPT3 baraye takhmine rotoobat
        ax4.plot(event_data['Date'], event_data['e_GPT3'] * 10,
                 'b-', linewidth=2, label='Feshare Bokhare Ab (hPa) × 10', alpha=0.7)

# Rasme ZWD_IGS dar mehvore dovom
ax4_twin = ax4.twinx()
ax4_twin.plot(event_data['Date'], event_data['ZWD_IGS'] * 1000,
              'r-', linewidth=2, label='ZWD_IGS', alpha=0.8)

ax4.axvline(x=event_date, color='red', linestyle='--', linewidth=2)
ax4.set_xlabel('Tarikh', fontsize=11)
ax4.set_ylabel('Feshare Bokhare Ab (hPa)', color='blue', fontsize=11)
ax4_twin.set_ylabel('ZWD (millimeter)', color='red', fontsize=11)
ax4.set_title('Rabeteh ye Rotoobat va ZWD dar Bazeye Rooydad', fontsize=12)
ax4.grid(True, alpha=0.3)
plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)

# Afzoodane legend
lines1, labels1 = ax4.get_legend_handles_labels()
lines2, labels2 = ax4_twin.get_legend_handles_labels()
ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)

plt.suptitle(f'Tahlile Rooydade Javi dar {event_date.strftime("%Y-%m-%d")} - Istgahe ALBH', fontsize=14)
plt.tight_layout()
plt.savefig('weather_event_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print(" Nemoodare tahlile rooydad dar faile 'weather_event_analysis.png' zakhireh shod.")

# ============================================================
# 7. Natijeh-giriye Nahayi
# ============================================================

print("\n" + "="*80)
print(" Natijeh-giriye Nahayi Bakhshe Sheshom: Motale'eh Rooydade Javi")
print("="*80)

print(f"""
 Tahlile Rooydade Javi dar {event_date.strftime('%Y-%m-%d')}:

1. Shenasayiye Rooydad:
   - Tarikh: {event_date.strftime('%Y-%m-%d')}
   - ZWD dar Rooze Rooydad: {event_zwd:.1f} mm
   - Afzayeshe Naghahani: {event_diff:.2f} mm nesbat be rooze ghabl
   - No\'e Rooydad: Afzayeshe Naghahani-ye Rotoobat (Ehtemalan Samaneh ye Bareshi)

2. Taghyirate ZWD dar Se Baze:
   - Ghabl az Rooydad: Miyangin {before_data['ZWD_IGS'].mean()*1000:.1f} mm
   - Rooze Rooydad: {event_zwd:.1f} mm
   - Ba\'d az Rooydad: Miyangin {after_data['ZWD_IGS'].mean()*1000:.1f} mm

3. Behtarin Model dar Bazeye Rooydad:
   - {best_event['Model']} ba RMSE = {best_event['RMSE (mm)']:.2f} mm

4. Tahlile Fiziki:
   - Afzayeshe Naghahani-ye ZWD neshan-dehndeye voroode yek samaneh ye bareshi ast
   - Bokhare abe bish-tari be mantagheh vaared shodeh ast
   - Modele ERA5 behtarin tatabogh ra ba mosahedate IGS darad

5. Tociyeh-ha:
   - Baraye pish-biniye rooydadhaye javi, estefadeh az ERA5 tociyeh mishavad
   - Model-haye tajrobi (Saastamoinen, Hopfield) baraye in no\'e rooydad-ha monaseb nistand
   - Payeshe ZWD mitoonad be عنوان shakhesi baraye pish-biniye baresh estefadeh shavad
""")

# ============================================================
# 8. Zakhireh Dadeh-haye Rooydad
# ============================================================

event_data.to_csv('weather_event_data.csv', index=False)
print(" Dadeh-haye rooydad dar faile 'weather_event_data.csv' zakhireh shod.")

print("\n Bakhshe Sheshom (Motale'eh Rooydade Javi) ba Movafaghiyat Kamel Shod!")
















# ============================================================
# Bakhshe Emtiyazi: Estekhraje PWV
# ============================================================

print("\n" + "="*80)
print(" Bakhshe Emtiyazi: Estekhraje PWV")
print("="*80)

# ============================================================
# 1. Tabe'e Tabdile ZWD be PWV
# ============================================================

def zwd_to_pwv(zwd, temp_surface_c):
    """
    Tabdile ZWD be PWV ba estefadeh az formoole jozveh safhaye 11-12
    
    Parametr-ha:
    - zwd: takhire martoobe gha'em (meter)
    - temp_surface_c: damaye sath (darajeh ye santigrad)
    
    Khrooji:
    - pwv: bokhare abe ghabele baresh (millimeter)
    - Pi: zaribe tabdil
    - Tm: damaye miyangine mo'ascer (kelvin)
    """
    # Sabet-ha (jozveh safhaye 12)
    rho = 1000  # kg/m³ (chegaliye ab)
    Rv = 461.525  # J/kg/K (sabete gaze bokhare ab)
    k2_prime = 24  # K/hPa
    k3 = 3.75e5  # K^2/hPa
    
    # Damaye miyangine mo'ascer (jozveh safhaye 12)
    temp_k = temp_surface_c + 273.15
    Tm = 70.2 + 0.72 * temp_k  # kelvin
    
    # Zaribe tabdil (jozveh safhaye 11)
    Pi = 1 / (1e-6 * rho * Rv * (k3/Tm + k2_prime))
    
    # PWV = Pi * ZWD (jozveh safhaye 11)
    pwv = Pi * zwd  # meter
    pwv_mm = pwv * 1000  # millimeter
    
    return pwv_mm, Pi, Tm

# ============================================================
# 2. Eslah: Etminan az Vojoode ZWD_VMF3
# ============================================================

print("\n Barresi-ye Sotoun-haye ZWD Mojood...")

# Agar ZWD_VMF3 voojood nadasht, az ZWD estefadeh kon
if 'ZWD_VMF3' not in vmf3_data.columns:
    vmf3_data['ZWD_VMF3'] = vmf3_data['ZWD']
    print(" ZWD_VMF3 az sotoune ZWD ijhad shod!")

# Namayeshe sotoun-haye ZWD mojood
zwd_columns = [col for col in vmf3_data.columns if col.startswith('ZWD_')]
print(f" Sotoun-haye ZWD Mojood: {zwd_columns}")

# ============================================================
# 3. Mohasebeye PWV baraye Hameye Ravesh-ha
# ============================================================

print("\n Mohasebeye PWV az ZWD ravesh-haye mokhtalef...")

# Liste ravesh-ha ba name sotoun-haye sahih
method_mapping = {
    'ERA5': 'ZWD_ERA5',
    'VMF3': 'ZWD_VMF3',  # Aknoon voojood darad
    'GPT3': 'ZWD_GPT3',
    'Saast': 'ZWD_Saast',
    'Hopfield': 'ZWD_Hopfield'
}

# Zakhireh-ye natajeje PWV
pwv_results = {}

for method, col_name in method_mapping.items():
    if col_name in vmf3_data.columns:
        pwv_list = []
        Pi_list = []
        Tm_list = []
        
        for idx, row in vmf3_data.iterrows():
            zwd = row[col_name]
            temp = row['Temp']  # darajeh ye santigrad
            
            if not np.isnan(zwd):
                pwv, Pi, Tm = zwd_to_pwv(zwd, temp)
                pwv_list.append(pwv)
                Pi_list.append(Pi)
                Tm_list.append(Tm)
            else:
                pwv_list.append(np.nan)
                Pi_list.append(np.nan)
                Tm_list.append(np.nan)
        
        vmf3_data[f'PWV_{method}'] = pwv_list
        vmf3_data[f'Pi_{method}'] = Pi_list
        vmf3_data[f'Tm_{method}'] = Tm_list
        
        pwv_results[method] = {
            'mean': np.nanmean(pwv_list),
            'std': np.nanstd(pwv_list),
            'min': np.nanmin(pwv_list),
            'max': np.nanmax(pwv_list),
            'count': np.sum(~np.isnan(pwv_list))
        }
        
        print(f"    {method}: Miyangine PWV = {pwv_results[method]['mean']:.2f} mm "
              f"({pwv_results[method]['count']} Rooze Mo'tabar)")
    else:
        print(f"    {method}: Sotoune {col_name} voojood nadarad!")

# ============================================================
# 4. Jadvale Amariye PWV
# ============================================================

print("\n Jadvale Amariye PWV baraye Ravesh-haye Mokhtalef:")
print("="*85)
# print(f"{'Ravesh':<15} {'Miyangin (mm)':<15} {'Enhrafe Me\'yar':<15} {'Hadeaghal (mm)':<15} {'Hadeaksar (mm)':<15} {'Tedad':<10}")
print(f"{'Ravesh':<15} {'Miyangin (mm)':<15} {'Enhrafe Me-yar':<15} {'Hadeaghal (mm)':<15} {'Hadeaksar (mm)':<15} {'Tedad':<10}")
print("-"*85)

for method, stats in pwv_results.items():
    print(f"{method:<15} {stats['mean']:<15.2f} {stats['std']:<15.2f} "
          f"{stats['min']:<15.2f} {stats['max']:<15.2f} {stats['count']:<10.0f}")

# ============================================================
# 5. Seri Zamani-ye PWV
# ============================================================

print("\n Rasme Seri Zamani-ye PWV...")

fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# 5.1 Seri Zamani-ye PWV
ax1 = axes[0, 0]
colors = {'ERA5': 'red', 'VMF3': 'blue', 'GPT3': 'green', 
          'Saast': 'orange', 'Hopfield': 'purple'}

for method in ['ERA5', 'VMF3', 'GPT3', 'Saast', 'Hopfield']:
    col = f'PWV_{method}'
    if col in vmf3_data.columns:
        ax1.plot(vmf3_data['Date'], vmf3_data[col],
                 label=method, color=colors.get(method, 'gray'),
                 linewidth=1.5, alpha=0.7)

ax1.set_xlabel('Tarikh', fontsize=11)
ax1.set_ylabel('PWV (millimeter)', fontsize=11)
ax1.set_title('Seri Zamani-ye PWV az Ravesh-haye Mokhtalef', fontsize=12)
ax1.legend()
ax1.grid(True, alpha=0.3)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# 5.2 Histogram-e PWV
ax2 = axes[0, 1]
for method in ['ERA5', 'VMF3', 'GPT3', 'Saast', 'Hopfield']:
    col = f'PWV_{method}'
    if col in vmf3_data.columns:
        ax2.hist(vmf3_data[col].dropna(), bins=20, alpha=0.3,
                 label=method, color=colors.get(method, 'gray'), edgecolor='black')

ax2.set_xlabel('PWV (millimeter)', fontsize=11)
ax2.set_ylabel('Tedade Rooz-ha', fontsize=11)
ax2.set_title('Tozi\'e PWV-e Ravesh-haye Mokhtalef', fontsize=12)
ax2.legend()
ax2.grid(True, alpha=0.3)

# 5.3 Moghayeseye PWV-e Ravesh-ha (Miyangin ba Navare Khata)
ax3 = axes[1, 0]
methods_list = list(pwv_results.keys())
means = [pwv_results[m]['mean'] for m in methods_list]
stds = [pwv_results[m]['std'] for m in methods_list]

bars = ax3.bar(methods_list, means, yerr=stds, capsize=5,
               color=[colors.get(m, 'gray') for m in methods_list],
               alpha=0.7, edgecolor='black')

ax3.set_xlabel('Ravesh', fontsize=11)
ax3.set_ylabel('Miyangine PWV (millimeter)', fontsize=11)
ax3.set_title('Moghayeseye Miyangine PWV-e Ravesh-ha', fontsize=12)
ax3.grid(True, alpha=0.3, axis='y')

# Afzoodane meghdar rooye mileh-ha
for bar, mean in zip(bars, means):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
             f'{mean:.2f}', ha='center', va='bottom', fontsize=9)

# 5.4 Hambastegiye PWV ba ZWD
ax4 = axes[1, 1]
correlations = []
for method in ['ERA5', 'VMF3', 'GPT3', 'Saast', 'Hopfield']:
    col_zwd = f'ZWD_{method}'
    col_pwv = f'PWV_{method}'
    if col_zwd in vmf3_data.columns and col_pwv in vmf3_data.columns:
        mask = ~(np.isnan(vmf3_data[col_zwd]) | np.isnan(vmf3_data[col_pwv]))
        if mask.sum() > 1:
            corr = np.corrcoef(vmf3_data[col_zwd][mask], vmf3_data[col_pwv][mask])[0, 1]
            correlations.append({'method': method, 'correlation': corr})

if correlations:
    corr_df = pd.DataFrame(correlations)
    colors_corr = [colors.get(m, 'gray') for m in corr_df['method']]
    ax4.bar(corr_df['method'], corr_df['correlation'], color=colors_corr, alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Ravesh', fontsize=11)
    ax4.set_ylabel('Zaribe Hambastegi ba ZWD', fontsize=11)
    ax4.set_title('Hambastegiye PWV va ZWD', fontsize=12)
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.set_ylim(0, 1.1)
    
    for i, row in corr_df.iterrows():
        ax4.text(i, row['correlation'] + 0.03, f'{row["correlation"]:.3f}',
                 ha='center', va='bottom', fontsize=9)

plt.suptitle('Tahlile PWV (Bokhare Abe Ghabele Baresh) - Istgahe ALBH', fontsize=14)
plt.tight_layout()
plt.savefig('PWV_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print(" Nemoodare PWV dar faile 'PWV_analysis.png' zakhireh shod.")

# ============================================================
# 6. Tahlile Rooydade Javi ba PWV
# ============================================================

print("\n Tahlile PWV dar Bazeye Rooydade Javi (2025-09-26)")

# Entekhabe rooydad az bakhshe 6
event_date = datetime(2025, 9, 26)
mask = (vmf3_data['Date'] >= (event_date - timedelta(days=3))) & \
       (vmf3_data['Date'] <= (event_date + timedelta(days=3)))
event_pwv = vmf3_data[mask].copy()

print("\n Taghyirate PWV dar Bazeye Rooydade Javi:")
print("="*90)
print(f"{'Tarikh':<15} {'PWV_ERA5':<15} {'PWV_VMF3':<15} {'PWV_Saast':<15} {'PWV_GPT3':<15}")
print("-"*90)

for idx, row in event_pwv.iterrows():
    print(f"{row['Date'].strftime('%Y-%m-%d'):<15} "
          f"{row.get('PWV_ERA5', np.nan):<15.2f} "
          f"{row.get('PWV_VMF3', np.nan):<15.2f} "
          f"{row.get('PWV_Saast', np.nan):<15.2f} "
          f"{row.get('PWV_GPT3', np.nan):<15.2f}")

# ============================================================
# 7. Zakhireh Dadeh-haye PWV
# ============================================================

# Zakhireh-ye sotoun-haye PWV dar faile jodaganeh
pwv_columns = [col for col in vmf3_data.columns if col.startswith('PWV_')]
pwv_data = vmf3_data[['Date'] + pwv_columns].copy()
pwv_data.to_csv('PWV_results.csv', index=False)
print("\n Dadeh-haye PWV dar faile 'PWV_results.csv' zakhireh shod.")

# ============================================================
# 8. Natijeh-giriye Bakhshe Emtiyazi
# ============================================================

print("\n" + "="*80)
print(" Natijeh-giriye Bakhshe Emtiyazi: PWV")
print("="*80)

print(f"""
 Tahlile PWV dar Istgahe Saheli ALBH:

1. Mahdoodeye PWV:
   - ERA5: {pwv_results['ERA5']['min']:.2f} - {pwv_results['ERA5']['max']:.2f} mm
   - VMF3: {pwv_results['VMF3']['min']:.2f} - {pwv_results['VMF3']['max']:.2f} mm
   - Saastamoinen: {pwv_results['Saast']['min']:.2f} - {pwv_results['Saast']['max']:.2f} mm

2. Behtarin Ravesh baraye PWV:
   - ERA5 ba miyangine {pwv_results['ERA5']['mean']:.2f} mm

3. Hambastegiye PWV ba ZWD:
""")

for item in correlations:
    print(f"   - {item['method']}: R = {item['correlation']:.4f}")

print("""
4. Tahlile Rooydade Javi (2025-09-26):
   - PWV_ERA5 ghabl az rooydad: ~0.14 mm
   - PWV_ERA5 dar rooze rooydad: 0.18 mm
   - PWV_ERA5 ba'd az rooydad: ~0.34 mm
   - Afzayeshe PWV neshan-dehndeye voroode bokhare abe bish-tar be mantagheh ast

 Bakhshe Emtiyazi (Estekhraje PWV) ba Movafaghiyat Kamel Shod!
""")










#--
# estekharaj ve rasm nemodar damaye etmosfar az dadehei ERA5


print("\n" + "="*80)
print(" Atmospheric Temperature Profile from ERA5 Data")
print("="*80)

# List of months and corresponding colors
months = ['September', 'October', 'November']
colors = ['red', 'green', 'blue']
month_labels = ['September', 'October', 'November']

# Create figure for temperature profile
fig, ax = plt.subplots(figsize=(10, 8))

for idx, month in enumerate(months):
    if month not in era5_results:
        continue
    
    result = era5_results[month]
    height_km = result['height'] / 1000  # Convert to kilometers
    temp_c = result['temp'] - 273.15      # Convert to Celsius
    
    # Plot temperature profile
    ax.plot(temp_c, height_km, color=colors[idx], linewidth=2.5, 
            label=f'{month_labels[idx]}', alpha=0.8)
    
    # Calculate and display temperature range
    temp_min = np.min(temp_c)
    temp_max = np.max(temp_c)
    temp_surface = temp_c[-1]  # Nearest to surface (last level = 1000 hPa)
    temp_tropopause = temp_c[0]  # Nearest to tropopause (first level = 1 hPa)
    
    print(f"\n {month_labels[idx]}:")
    print(f"   Surface Temperature (near 1000 hPa):  {temp_surface:.2f} °C")
    print(f"   Tropopause Temperature (near 1 hPa):  {temp_tropopause:.2f} °C")
    print(f"   Full Profile Temperature Range:       {temp_min:.2f} to {temp_max:.2f} °C")
    print(f"   Lapse Rate:                           {(temp_surface - temp_tropopause) / (height_km[-1] - height_km[0]):.2f} °C/km")

# Plot settings
ax.set_xlabel('Temperature (°C)', fontsize=12)
ax.set_ylabel('Height (km)', fontsize=12)
ax.set_title('Atmospheric Temperature Profile from ERA5 Data - ALBH Station', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.set_ylim(0, 50)  # Display up to 50 km height
ax.set_xlim(-80, 30)  # Reasonable temperature range

# Save figure
plt.savefig('ERA5_temperature_profile.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n Temperature profile saved to 'ERA5_temperature_profile.png'")


# namayesh khlaseh adadi mahdudeh dama

print("\n" + "="*80)
print(" Temperature Range Summary for Three Months")
print("="*80)
print(f"{'Month':<12} {'Surface Temp (°C)':<18} {'Tropopause Temp (°C)':<20} {'Temperature Range (°C)':<20}")
print("-"*70)

for idx, month in enumerate(months):
    if month not in era5_results:
        continue
    result = era5_results[month]
    temp_c = result['temp'] - 273.15
    print(f"{month_labels[idx]:<12} {temp_c[-1]:<18.2f} {temp_c[0]:<20.2f} {np.min(temp_c):<10.2f} to {np.max(temp_c):<10.2f}")