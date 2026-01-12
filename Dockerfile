# Multi-stage Dockerfile for SIMCO AI Edge Agent
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

# Environment Defaults
ENV SIMCO_DEBUG=False
ENV SIMCO_BUFFER_DB=/data/buffer.db
ENV SIMCO_MACHINE_REGISTRY_FILE=/data/machine_registry.json
ENV SIMCO_DEVICE_STATE_FILE=/data/device_state.json

VOLUME /data
RUN mkdir -p /data

CMD ["python", "-m", "simco_agent"]
