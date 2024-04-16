FROM registry:2

RUN mkdir "/certs"

COPY /etc/letsencrypt/live/rchat-company.ru/fullchain.pem /certs/fullchain.pem
COPY /etc/letsencrypt/live/rchat-company.ru/privkey.pem /certs/privkey.pem