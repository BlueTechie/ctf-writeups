FROM python:3.15-rc-slim-trixie@sha256:14684656c0069b49e897c63d52bbbe7df8a4bf189911a597403fd3b4ffeaae06 AS base
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until
ARG SNAPSHOT_DATE=20260927T000000Z
ARG FLAG="flagbot{fake_flag}"
ENV FLAG=$FLAG

WORKDIR /app

COPY requirements.txt /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt
RUN mkdir /tmp/db

COPY . /app

ENTRYPOINT ["python3"]
CMD ["app.py"]

