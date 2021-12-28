import logging

from fastapi.params import File
import utils
import aiohttp
import json
from expiring_dict import ExpiringDict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from asyncio import gather
from weather import get_weather

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s"
)
log = logging.getLogger("whereto")

cities = utils.populate_cities()
weather_cache = ExpiringDict(ttl=86400, interval=1800)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

limiter = Limiter(key_func=utils.get_visitor_ipaddr)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/favicon.ico")
async def favicon(request: Request, response_class=FileResponse):
    return FileResponse("static/images/favicon.ico")


@app.get("/api/weather")
@limiter.limit("20/minute")
async def api_weather(request: Request, lat: float, lon: float, radius: int):
    if not utils.valid_lat_lon(lat, lon):
        raise HTTPException(400, detail="latitude or longitude incorrect")

    # For local testing
    # with open("test_resp.json", "r") as f:
    #     return json.loads(f.readline())

    closest_cities = utils.closest_by_pop(cities, lat, lon, radius)
    if len(closest_cities) == 0:
        raise HTTPException(404, detail="No cities found within radius")

    cities_weather = {}
    fetch_cities = []
    for city in closest_cities:
        key = f"{city['city']}/{city['country']}"
        if key in weather_cache:
            log.info(f"{key} found in cache")
            cities_weather[key] = weather_cache[key]
        else:
            log.info(f"{key} NOT in cache, querying openweathermap")
            fetch_cities.append(city)

    if len(fetch_cities) > 0:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            results = await gather(
                *[
                    get_weather(
                        session, f"{c['city']}/{c['country']}", c["lat"], c["lon"]
                    )
                    for c in fetch_cities
                ]
            )
            for key, result in results:
                weather_cache[key] = result
                cities_weather[key] = result

    return cities_weather
