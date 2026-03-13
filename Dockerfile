# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────────────────────────
# ffmpeg  — audio extraction
# git     — needed by whisper to fetch model
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# ── App setup ─────────────────────────────────────────────────────────────────
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Whisper model at build time so it's baked into the image.
# This avoids a cold-start delay on first message.
# Change 'base' below if you set WHISPER_MODEL to something else.
ARG WHISPER_MODEL_PREBAKE=base
RUN python -c "import whisper; whisper.load_model('${WHISPER_MODEL_PREBAKE}')"

COPY bot.py .

# ── Runtime ────────────────────────────────────────────────────────────────────
# TELEGRAM_TOKEN must be injected as an environment variable via Choreo secrets.
ENV WHISPER_MODEL=base

CMD ["python", "bot.py"]
