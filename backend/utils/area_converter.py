def convert_to_sq_meters(value: float, unit: str) -> float:
    """
    Convert area from various units to square meters.
    Supported units:
      - hectare
      - acre
      - bigha
      - kattha
      - gaj
      - decimil
      - sq_meter / sqm
      - sq_km
    """
    unit = unit.strip().lower()
    factors = {
        "hectare": 10000,
        "acre": 4046.8564224,
        "bigha": 2508.0,        # typical North India bigha
        "kattha": 136.0,        # 1 bigha = 18 kattha => 2508/18 ≈ 139; adjust per region
        "gaj": 0.83612736,      # 1 gaj = 0.83612736 m²
        "decimil": 4.0468564224,# 1 decimil = 0.1 acre
        "sq_meter": 1,
        "sqm": 1,
        "sq_km": 1_000_000,
    }

    if unit not in factors:
        raise ValueError(f"Unsupported area unit: {unit}")

    return value * factors[unit]


def convert_from_sq_meters(area_sqm: float) -> dict:
    """
    Given an area in square meters, return conversions into all supported units.
    """
    inv_factors = {
        "hectare": 1/10000,
        "acre": 1/4046.8564224,
        "bigha": 1/2508.0,
        "kattha": 1/136.0,
        "gaj": 1/0.83612736,
        "decimil": 1/4.0468564224,
        "sq_meter": 1,
        "sqm": 1,
        "sq_km": 1/1_000_000,
    }

    return {unit: area_sqm * factor for unit, factor in inv_factors.items()}
