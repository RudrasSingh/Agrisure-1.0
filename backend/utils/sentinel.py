import os
import requests
from datetime import datetime, timedelta
from .evalScripts import truecolor_eval, ndvi_eval, ndmi_eval, gndvi_eval
from sentinelhub import (
    SHConfig,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    CRS,
    BBox,
    Geometry,
    bbox_to_dimensions,
    MosaickingOrder
)
from config import settings

# ─── Sentinel Config ─────────────────────────────────────────────────────────────
def get_sh_config():
    cfg = SHConfig()
    cfg.sh_client_id = settings.SH_CLIENT_ID
    cfg.sh_client_secret = settings.SH_CLIENT_SECRET
    cfg.sh_base_url = settings.SH_BASE_URL
    if not cfg.sh_client_id or not cfg.sh_client_secret:
        raise RuntimeError("Missing Sentinel Hub credentials")
    # Pre-flight token check
    token_url = f"{cfg.sh_base_url}/oauth/token"
    r = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": cfg.sh_client_id,
        "client_secret": cfg.sh_client_secret
    })
    r.raise_for_status()
    return cfg

# ─── BBOX GEN ───────────────────────────────────────────────────────────────────
def generate_bbox(lat, lon, area_sqm):
    """
    Create a square BBox around (lat,lon) covering ~area_sqm.
    """
    import math
    side_m = math.sqrt(area_sqm)
    half_deg = (side_m/1000)/111  # approx conversion
    return BBox([lon-half_deg/2, lat-half_deg/2, lon+half_deg/2, lat+half_deg/2], crs=CRS.WGS84)

# ─── FETCH FUNCTIONS ─────────────────────────────────────────────────────────────
def _make_request(evalscript: str, bbox: BBox, geometry: Geometry, cfg: SHConfig, 
                  time_interval: tuple, size: tuple):
    return SentinelHubRequest(
        evalscript=evalscript,
        input_data=[SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L2A,
            time_interval=time_interval,
            mosaicking_order=MosaickingOrder.MOST_RECENT
        )],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bbox,
        geometry=geometry,
        size=size,
        config=cfg
    ).get_data()[0]

def fetch_true_color(bbox, geometry, time_interval, size):
    cfg = get_sh_config()
    return _make_request(truecolor_eval, bbox, geometry, cfg, time_interval, size)

def fetch_ndvi(bbox, geometry, time_interval, size):
    cfg = get_sh_config()
    return _make_request(ndvi_eval, bbox, geometry, cfg, time_interval, size)

def fetch_ndmi(bbox, geometry, time_interval, size):
    cfg = get_sh_config()
    return _make_request(ndmi_eval, bbox, geometry, cfg, time_interval, size)

def fetch_gndvi(bbox, geometry, time_interval, size):
    cfg = get_sh_config()
    return _make_request(gndvi_eval, bbox, geometry, cfg, time_interval, size)
