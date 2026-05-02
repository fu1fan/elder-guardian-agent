FROM python:3.11-slim

ARG APP_DIR
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG http_proxy
ARG https_proxy
ARG no_proxy

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY packages/guardian-shared /app/packages/guardian-shared
COPY ${APP_DIR} /app/${APP_DIR}
COPY configs /app/configs

WORKDIR /app/${APP_DIR}
RUN pip install --no-cache-dir -e /app/packages/guardian-shared -e .

EXPOSE 8000

