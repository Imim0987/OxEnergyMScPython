# A19141S1_Assignment_Notebook_Template.py
# Jupyter-ready Python notebook script for MSc Energy Infrastructure assignment
# Purpose: template to implement Parts A-D of the assignment:
# - Build simplified EHV network (regional buses)
# - Run power flow for 2025 baseline and 2030 high-renewables
# - Identify stressed lines and voltages
# - Test mitigation scenarios
#
# INSTRUCTIONS:
# 1) Open this file as a notebook cell-by-cell (or paste into a new .ipynb).
# 2) Replace placeholder file paths and fill the small DATA sections with your downloaded datasets
#    (FES regional workbook, GSP shapefiles, PyPSA generation CSV, renewables.ninja outputs).
# 3) Run cells top-to-bottom. Use the 'Synthetic test' switch to test without external data.

# =========================
# 0. Environment and imports
# =========================
import os
import math
import json
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Power system libraries
try:
    import pandapower as pp
    import pandapower.networks as pn
except Exception as e:
    pp = None
    print('pandapower not available. Install with `pip install pandapower` to run real PFs')

# -------------------------
# Quick config - edit here
# -------------------------
CONFIG = {
    'data_dir': './data',             # place to store inputs downloaded from hints
    'fes_workbook': './data/FES_Regional.xlsx',
    'gsp_shapefile': './data/GSP_boundaries.shp',
    'pypsa_generation_csv': './data/UK_2025_gen_above100MW.csv',
    'renewables_ninja_dir': './data/renewables_ninja',
    'use_synthetic_test': True,       # set False once you add real data
    'base_power_mw': 100.0,           # Pbase for per-unit (MW)
    'verbose': True
}

# =========================
# 1. Helper functions
# =========================

def log(*args, **kwargs):
    if CONFIG.get('verbose', True):
        print(*args, **kwargs)


def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)


# =========================
# 2. Synthetic test dataset
# =========================
# This small test network helps verify the workflow without external files.

def build_synthetic_region_network():
    """Return bus_df, line_df describing a small toy GB-like network for testing."""
    # Five-region toy example
    bus_df = pd.DataFrame([
        {'bus': 0, 'name': 'Scotland', 'lon': -3.8, 'lat': 56.5, 'v_kv': 400.0},
        {'bus': 1, 'name': 'North',    'lon': -2.5, 'lat': 54.5, 'v_kv': 400.0},
        {'bus': 2, 'name': 'Midlands', 'lon': -1.2, 'lat': 52.5, 'v_kv': 400.0},
        {'bus': 3, 'name': 'South',    'lon': -0.4, 'lat': 51.2, 'v_kv': 400.0},
        {'bus': 4, 'name': 'London',   'lon': -0.1, 'lat': 51.5, 'v_kv': 400.0}
    ])

    # Example demands and generation (MW) - baseline 2025
    bus_df['P_demand_MW'] = [2000, 1500, 3000, 2500, 4000]
    bus_df['P_gen_MW'] = [4000, 500, 600, 800, 200]

    # Lines connecting them (approx distances) - simple chain with diagonals
    line_df = pd.DataFrame([
        {'from_bus':0, 'to_bus':1, 'length_km':200},
        {'from_bus':1, 'to_bus':2, 'length_km':200},
        {'from_bus':2, 'to_bus':3, 'length_km':200},
        {'from_bus':3, 'to_bus':4, 'length_km':60},
        {'from_bus':0, 'to_bus':2, 'length_km':330},
        {'from_bus':1, 'to_bus':3, 'length_km':300}
    ])

    # Assume base r and x per 100 km (per-phase) crude values for 400kV
    line_df['R_ohm'] = 0.03 * line_df['length_km'] / 100.0  # 0.03 ohm/100km example
    line_df['X_ohm'] = 0.15 * line_df['length_km'] / 100.0  # 0.15 ohm/100km

    return bus_df, line_df


# =========================
# 3. Data loader functions
# =========================

def load_gsp_buses(shapefile_path):
    """Load GSP boundaries and return centroid-located GeoDataFrame of buses.
    Expects a polygon shapefile with a name/region column. Replace 'NAME' key if needed."""
    gdf = gpd.read_file(shapefile_path)
    gdf = gdf.to_crs(epsg=4326)
    gdf['centroid'] = gdf.geometry.centroid
    gdf['lon'] = gdf.centroid.x
    gdf['lat'] = gdf.centroid.y
    # Example: keep only relevant columns
    gdf = gdf.rename(columns={'NAME':'region_name'}) if 'NAME' in gdf.columns else gdf
    return gdf


def load_fes_regional(fes_path):
    """Load FES workbook and return simplified DataFrame per region with demand and embedded gen.
    This loader is a placeholder. Update to match workbook sheet names and layout."""
    # Placeholder - user to implement based on actual FES workbook layout
    raise NotImplementedError('Load FES regional workbook according to its structure')


# =========================
# 4. Per-unit conversions
# =========================

def compute_zbase(v_base_kv, p_base_mw):
    # Convert to consistent units (ohm)
    v_base = v_base_kv * 1e3
    p_base = p_base_mw * 1e6
    z_base = v_base**2 / p_base
    return z_base


# =========================
# 5. Build pandapower network
# =========================

def build_pandapower_network(bus_df, line_df, pbase_mw=CONFIG['base_power_mw']):
    """Create a pandapower network from bus and line tables. Returns pandapower net and mapping dicts."""
    if pp is None:
        raise RuntimeError('pandapower not installed')

    net = pp.create_empty_network()
    bus_index_map = {}

    # Create buses
    for _, r in bus_df.iterrows():
        vn_kv = r['v_kv'] / 1.0
        b = pp.create_bus(net, vn_kv=vn_kv, name=r['name'])
        bus_index_map[int(r['bus'])] = b

    # Create external grid (slack) - choose the highest generation bus as slack (simple heuristic)
    slack_bus_id = int(bus_df['P_gen_MW'].idxmax())
    slack_pp_bus = bus_index_map[int(bus_df.loc[slack_bus_id, 'bus'])]
    pp.create_ext_grid(net, bus=slack_pp_bus, vm_pu=1.02)

    # Create simple lines using create_line_from_parameters
    for _, row in line_df.iterrows():
        from_bus = bus_index_map[int(row['from_bus'])]
        to_bus = bus_index_map[int(row['to_bus'])]
        length_km = float(row['length_km'])
        # Line parameters: r_ohm_per_km, x_ohm_per_km, c_nf_per_km, max_i_ka
        r_ohm_per_km = row['R_ohm'] / max(0.001, row['length_km'])
        x_ohm_per_km = row['X_ohm'] / max(0.001, row['length_km'])
        # Use default values for c and max_i
        pp.create_line_from_parameters(net, from_bus, to_bus, length_km,
                                       r_ohm_per_km, x_ohm_per_km,
                                       c_nf_per_km=0.0, max_i_ka=1.0, name=f"L_{from_bus}_{to_bus}")

    # Add loads and generators
    for _, r in bus_df.iterrows():
        b = bus_index_map[int(r['bus'])]
        p_mw = float(r.get('P_demand_MW', 0.0))
        q_mvar = 0.0
        if p_mw > 0:
            pp.create_load(net, bus=b, p_mw=p_mw/1e3, q_mvar=q_mvar/1e3, name=f"Load_{r['name']}")
        gen_mw = float(r.get('P_gen_MW', 0.0))
        if gen_mw > 0:
            pp.create_sgen(net, bus=b, p_mw=gen_mw/1e3, name=f"Gen_{r['name']}")

    return net


# =========================
# 6. Run power flow and collect metrics
# =========================

def run_powerflow_and_metrics(net):
    pp.runpp(net)
    # Bus voltages
    vm_pu = net.res_bus.vm_pu.values
    va_degree = net.res_bus.va_degree.values
    # Line loading
    lines = net.res_line
    line_loading = lines.loading_percent.values
    line_p_mw = lines.pl_mw.values
    line_q_mvar = lines.ql_mvar.values
    losses_mw = net.res_line.pl_mw.sum()
    metrics = {
        'vm_pu': vm_pu,
        'va_degree': va_degree,
        'line_loading_percent': line_loading,
        'line_p_mw': line_p_mw,
        'line_q_mvar': line_q_mvar,
        'line_losses_mw': losses_mw
    }
    return metrics


# =========================
# 7. Scenario: scale renewables to meet annual demand
# =========================

def compute_required_renewable_capacity(total_annual_demand_mwh, annual_cf):
    """Given annual energy demand (MWh) and capacity factor (0-1), return capacity in MW required."""
    # Annual energy per MW = 8760 * CF MWh per installed MW
    if annual_cf <= 0:
        return np.nan
    cap_mw = total_annual_demand_mwh / (8760.0 * annual_cf)
    return cap_mw


# =========================
# 8. Plotting helpers
# =========================

def plot_bus_map(bus_df, metrics=None, title='Bus voltages'):
    """Simple scatter map of buses colored by voltage magnitude (if provided)."""
    fig, ax = plt.subplots(figsize=(8,6))
    gdf = gpd.GeoDataFrame(bus_df.copy(), geometry=gpd.points_from_xy(bus_df.lon, bus_df.lat))
    gdf.plot(ax=ax, color='lightgrey')
    if metrics is not None and 'vm_pu' in metrics:
        vals = metrics['vm_pu']
        sc = ax.scatter(bus_df.lon, bus_df.lat, c=vals, cmap='coolwarm', s=120, edgecolor='k')
        plt.colorbar(sc, label='Vm(pu)')
    else:
        ax.scatter(bus_df.lon, bus_df.lat, color='k', s=60)
    for _, r in bus_df.iterrows():
        ax.text(r['lon']+0.05, r['lat']+0.02, r['name'], fontsize=8)
    ax.set_title(title)
    plt.show()


# =========================
# 9. Main execution flow - synthetic test
# =========================
if __name__ == '__main__':
    ensure_dir(CONFIG['data_dir'])

    if CONFIG['use_synthetic_test']:
        log('Building synthetic dataset for testing...')
        bus_df, line_df = build_synthetic_region_network()
        log('Bus table:')
        display(bus_df)
        log('Line table:')
        display(line_df)

        if pp is None:
            log('pandapower not installed; skipping PF. Set use_synthetic_test=False to load real data when pandapower is available.')
        else:
            net = build_pandapower_network(bus_df, line_df)
            log('Running power flow...')
            metrics = run_powerflow_and_metrics(net)
            log('Line losses (MW):', metrics['line_losses_mw'])
            plot_bus_map(bus_df, metrics=metrics, title='Synthetic test - bus voltages (pu)')

    else:
        log('Non-synthetic data path selected - implement loaders and turn off synthetic_test once data is in place.')

# End of notebook template
# ------------------------
# Next steps (suggested):
# 1) Replace synthetic data by loading GSP and FES regional data
# 2) Create function to place PV/Wind by scaling region capacities using renewables.ninja CFs
# 3) Implement Part C scaling to meet Clean Power 2030 (annual energy balance)
# 4) Add mitigation scenario functions (add_line_capacity, add_storage, add_shunt_compensator)
# 5) Export figures and tables for your report
