FROM rasa/rasa-sdk:3.6.2

USER root
RUN pip install --no-cache-dir psycopg2-binary==2.9.9

WORKDIR /app
COPY . /app/actions
ENV PYTHONPATH=/app

USER 1001
