#!/bin/sh
set -e

echo "Starting frontend with BACKEND_URL: ${BACKEND_URL}"

# Substitute environment variables in nginx config
envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

echo "Generated nginx config:"
cat /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'
