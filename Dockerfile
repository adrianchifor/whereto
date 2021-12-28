FROM python:3.8-slim

RUN pip install --no-cache-dir 'fastapi' 'uvicorn[standard]' \
  'slowapi' 'aiohttp' 'expiring-dict' 'jinja2' 'aiofiles'

WORKDIR /app
COPY *.py /app/
COPY worldcities.csv /app
COPY static /app/static
COPY templates /app/templates

USER 1001

CMD uvicorn main:app --host 0.0.0.0 --port 8080