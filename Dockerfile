FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# системні залежності (важливо для postgres drivers)
RUN apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  dos2unix \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

# Копіюємо start.sh і приводимо у Unix формат + даємо права
COPY start.sh .
RUN dos2unix start.sh && chmod +x start.sh

COPY . .

RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]