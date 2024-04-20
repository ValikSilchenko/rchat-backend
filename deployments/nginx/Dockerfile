FROM nginx

COPY nginx.conf /etc/nginx/nginx.conf
COPY sites /etc/nginx/sites
RUN mkdir -p /var/www/rchat-test/photo-cache
RUN chown -hR www-data:www-data /var/www
