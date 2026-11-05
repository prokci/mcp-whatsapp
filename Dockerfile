FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYDOLL_HEADLESS=true
ENV PYDOLL_LOG_LEVEL=INFO
ENV PYDOLL_BROWSER_TYPE=chrome
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y\
    curl \
    wget \
    gnupg \
    unzip \
    xvfb \
    fonts-liberation \
    ca-certificates \
    procps \
    libmagic1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN groupadd -r pydoll && useradd -r -g pydoll -s /bin/bash pydoll \
    && mkdir -p /home/pydoll \
    && chown -R pydoll:pydoll /home/pydoll \
    && chown -R pydoll:pydoll /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN google-chrome --version

RUN chmod +x /app/entrypoint.sh

EXPOSE ${MCP_PORT}

ENTRYPOINT ["/app/entrypoint.sh"]