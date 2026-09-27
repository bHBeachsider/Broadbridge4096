FROM python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 espeak-ng \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 1000 --create-home bbvoice \
    && mkdir /models /work && chown bbvoice:bbvoice /models /work
WORKDIR /app
COPY requirements.txt requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c requirements.lock.txt && pip freeze > /app/installed-packages.txt
COPY local_voice.py models.json ./
USER bbvoice
ENTRYPOINT ["python", "/app/local_voice.py"]
