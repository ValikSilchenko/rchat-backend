FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && rm requirements.txt

COPY /rchat /app/rchat

CMD ["python", "-m", "rchat.app"]