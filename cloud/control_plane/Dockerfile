FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cloud/control_plane /app/cloud/control_plane

# Ensure simco_common is available if needed (likely needed later for shared schemas)
# COPY simco_common /app/simco_common 

ENV PYTHONPATH=/app

CMD ["uvicorn", "cloud.control_plane.app:app", "--host", "0.0.0.0", "--port", "8080"]
