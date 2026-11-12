FROM python:3.12-slim
RUN useradd -m -u 1000 app
WORKDIR /app
COPY --chown=app:app app.py engine.py manifest.example.json ./
COPY --chown=app:app static ./static
USER app
ENV PORT=7860 INQUIRY_DATA=/home/app/inquiry-data
EXPOSE 7860
CMD ["python", "app.py"]
