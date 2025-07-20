FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY ui/ ui/
COPY tests/ tests/

CMD ["pytest", "--maxfail=1", "--disable-warnings", "-q"]
