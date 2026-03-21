FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY mcp_video/ mcp_video/

RUN pip install --no-cache-dir .

ENTRYPOINT ["mcp-video"]
