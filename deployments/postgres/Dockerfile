FROM postgres:16

COPY /deployments/postgres/conf/pg_hba.conf /etc/postgresql/pg_hba.conf
COPY /deployments/postgres/conf/postgresql.conf /etc/postgresql/postgresql.conf

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]