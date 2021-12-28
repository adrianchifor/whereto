import os
import sys
import logging
import utils
import aiohttp
import asyncio
from typing import Tuple
from fastapi import HTTPException
from asyncio.exceptions import TimeoutError
from aiohttp.client_exceptions import ClientConnectorError

log = logging.getLogger("whereto")

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", None)
if not OPENWEATHERMAP_API_KEY:
    sys.exit("OPENWEATHERMAP_API_KEY is not defined, exiting")

API = "https://api.openweathermap.org/data/2.5/onecall"
EXCLUDE = "current,minutely,hourly,alerts"


async def get_weather(
    session, key: str, lat: float, lon: float, retries: int = 3
) -> Tuple[str, dict]:
    url = f"{API}?lat={lat}&lon={lon}&exclude={EXCLUDE}&units=metric&appid={OPENWEATHERMAP_API_KEY}"
    try:
        async with session.get(url) as r:
            response = await r.json()
            if r.status == 200:
                daily = {"lat": lat, "lon": lon}
                for day in response["daily"]:
                    day_month = utils.timestamp_to_day(day["dt"])
                    daily[day_month] = {
                        "temp": {"min": day["temp"]["min"], "max": day["temp"]["max"]},
                        "weather": {
                            "description": day["weather"][0]["description"],
                            "icon": day["weather"][0]["icon"],
                        },
                        "pop": day["pop"],
                    }
                return key, daily
            else:
                if "message" in response:
                    log.error(
                        f"Got non-200 response from openweathermap: {r.status} - {response['message']}"
                    )
                raise HTTPException(
                    500, detail=f"Failed to query weather API ({r.status})"
                )
    except (ClientConnectorError, TimeoutError) as e:
        log.error(f"Failed to query openweathermap: {e}")
        if retries > 0:
            log.info(f"{retries} retries left..")
            await asyncio.sleep(2)
            return await get_weather(session, key, lat, lon, retries - 1)
        raise HTTPException(500, detail="Failed to query weather API")
