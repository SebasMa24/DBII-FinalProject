FROM postgres:17

COPY config/pg_hba.conf /etc/postgresql/pg_hba.conf

# Configura para que postgres use tu pg_hba.conf personalizado
CMD ["postgres", "-c", "hba_file=/etc/postgresql/pg_hba.conf"]