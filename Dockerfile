FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs backups

CMD ["python", "main.py", "--web"]

RUN echo "Build $(date)" > /tmp/build_time

CMD ["python", "main.py", "--web"]