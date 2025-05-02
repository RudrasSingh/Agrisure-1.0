import io
import base64
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

def compute_time_series(fetch_func, bbox, geometry, end_date: datetime, days: int, size):
    """
    Calls fetch_func for each day in [end_date-days, end_date], returns DataFrame of mean values.
    """
    dates = [end_date - timedelta(days=i) for i in range(days, -1, -1)]
    records = []
    for d in dates:
        start = (d - timedelta(days=1)).isoformat() + "T00:00:00Z"
        end   = (d + timedelta(days=1)).isoformat() + "T23:59:59Z"
        arr = fetch_func(bbox, geometry, (start, end), size)
        val = float(np.nanmean(arr))
        records.append({"date": d.date(), "value": val})
    return pd.DataFrame(records)

def plot_trend(df, title: str, ylabel: str):
    """
    Returns a base64-encoded PNG of df['value'] vs df['date'].
    """
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(df["date"], df["value"], marker="o")
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    fig.autofmt_xdate()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
    
def analyze_indices(bbox, geometry, end_date, size):
    """
    Compute 20-day and quarter time series for NDVI, NDMI, GNDVI, and return plots + data.
    """
    # 20 days
    df20 = {
        "ndvi" : compute_time_series(fetch_func=__import__("utils.sentinel_utils", fromlist=["fetch_ndvi"]).fetch_ndvi, bbox=bbox, geometry=geometry, end_date=end_date, days=20, size=size),
        "ndmi" : compute_time_series(fetch_func=__import__("utils.sentinel_utils", fromlist=["fetch_ndmi"]).fetch_ndmi, bbox=bbox, geometry=geometry, end_date=end_date, days=20, size=size),
        "gndvi": compute_time_series(fetch_func=__import__("utils.sentinel_utils", fromlist=["fetch_gndvi"]).fetch_gndvi, bbox=bbox, geometry=geometry, end_date=end_date, days=20, size=size),
    }
    # quarter (~90 days)
    df90 = {
        "ndvi" : compute_time_series(fetch_func=__import__("utils.sentinel_utils", fromlist=["fetch_ndvi"]).fetch_ndvi, bbox=bbox, geometry=geometry, end_date=end_date, days=90, size=size),
        "ndmi" : compute_time_series(fetch_func=__import__("utils.sentinel_utils", fromlist=["fetch_ndmi"]).fetch_ndmi, bbox=bbox, geometry=geometry, end_date=end_date, days=90, size=size),
        "gndvi": compute_time_series(fetch_func=__import__("utils.sentinel_utils", fromlist=["fetch_gndvi"]).fetch_gndvi, bbox=bbox, geometry=geometry, end_date=end_date, days=90, size=size),
    }
    # True color just a single image for each period
    tc20 = __import__("utils.sentinel_utils", fromlist=["fetch_true_color"]).fetch_true_color(bbox, geometry, ((end_date-timedelta(days=20)).isoformat()+"T00:00:00Z", end_date.isoformat()+"T23:59:59Z"), size)
    tc90 = __import__("utils.sentinel_utils", fromlist=["fetch_true_color"]).fetch_true_color(bbox, geometry, ((end_date-timedelta(days=90)).isoformat()+"T00:00:00Z", end_date.isoformat()+"T23:59:59Z"), size)

    # Plot and encode
    plots = {}
    for key, df in df20.items():
        plots[f"{key}_20d"] = plot_trend(df, f"{key.upper()} Trend (20 days)", key.upper())
    for key, df in df90.items():
        plots[f"{key}_90d"] = plot_trend(df, f"{key.upper()} Trend (90 days)", key.upper())

    # Compute simple confidence: average drop % between 20d and 90d mean
    mean20 = np.mean([df20[k]["value"].mean() for k in df20])
    mean90 = np.mean([df90[k]["value"].mean() for k in df90])
    confidence = max(0.0, min(1.0, (mean90 - mean20) / (mean90 + 1e-6)))

    return {
        "series_20d": {k: df20[k].to_dict(orient="records") for k in df20},
        "series_90d": {k: df90[k].to_dict(orient="records") for k in df90},
        "plots": plots,
        "true_color_20d": tc20,  # raw array or encode as needed
        "true_color_90d": tc90,
        "confidence": confidence
    }
