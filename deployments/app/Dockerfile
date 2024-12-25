FROM python:3.11-slim

WORKDIR /app

RUN apt update && apt install libpq-dev gcc -y
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt && rm requirements.txt

COPY /rchat /app/rchat

CMD ["python", "-m", "rchat.app"]