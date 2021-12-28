import csv
from math import cos, asin, sqrt
from functools import lru_cache
from datetime import datetime
from fastapi import Request


def valid_lat_lon(lat: float, lon: float) -> bool:
    try:
        assert -90 <= lat <= 90
        assert -180 <= lon <= 180
        return True
    except AssertionError:
        return False


def closest_by_pop(
    cities: dict, lat: float, lon: float, radius_km: int = 200, limit: int = 10
) -> list:
    closest_cities = []
    for city in cities.values():
        distance = _distance(lat, lon, city["lat"], city["lon"])
        if distance <= radius_km:
            closest_cities.append(city)

    if len(closest_cities) < limit:
        limit = len(closest_cities)

    return sorted(closest_cities, key=lambda city: city["pop"], reverse=True)[:limit]


# https://en.wikipedia.org/wiki/Haversine_formula
@lru_cache(maxsize=300000)  # ~120MB
def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    p = 0.017453292519943295  # pi/180
    a = (
        0.5
        - cos((lat2 - lat1) * p) / 2
        + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    )
    return int(12742 * asin(sqrt(a)))  # 2 * earth_radius * asin...


def populate_cities() -> dict:
    cities = {}
    index = 0
    with open("worldcities.csv", "r") as f:
        for row in csv.reader(f):
            # Skip first (column titles)
            if index == 0:
                index += 1
                continue
            # Skip low or no population
            if row[4] == "" or float(row[4]) < 50000:
                continue

            cities[f"{row[0]}/{row[3]}"] = {
                "city": str(row[0]),
                "lat": float(row[1]),
                "lon": float(row[2]),
                "country": str(row[3]),
                "pop": int(float(row[4])),
            }

    return cities


def timestamp_to_day(ts: int) -> str:
    return datetime.utcfromtimestamp(ts).strftime("%d/%m")


def get_visitor_ipaddr(request: Request) -> str:
    if "CF-Connecting-IP" in request.headers:
        # Will only return if using Cloudflare
        return request.headers.get("CF-Connecting-IP")
    elif "X-Original-Forwarded-For" in request.headers:
        # Get first IP from X-Original-Forwarded-For
        return request.headers.get("X-Original-Forwarded-For").split(",")[0].strip()
    elif "X-Forwarded-For" in request.headers:
        # Get first IP from X-Forwarded-For
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    else:
        return request.client.host or "127.0.0.1"
