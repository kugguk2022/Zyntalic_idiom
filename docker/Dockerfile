FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -e ".[web,pdf]"

EXPOSE 8000
CMD ["uvicorn", "apps.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
