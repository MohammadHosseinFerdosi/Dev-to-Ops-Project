FROM example.com/python:3.12-slim

WORKDIR /app

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -i https://example.com/simple -r requirements.txt

COPY app/ ./app/

USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "app"]
