FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN mkdir -p instance

EXPOSE 5000

ENV FLASK_APP=app.py
ENV GUNICORN_WORKERS=4
ENV GUNICORN_BIND=0.0.0.0:5000

CMD ["sh", "-c", "python init_db.py && gunicorn --workers $GUNICORN_WORKERS --bind $GUNICORN_BIND app:app"]
