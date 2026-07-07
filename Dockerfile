FROM nginx:alpine

# Copy static files
COPY . /usr/share/nginx/html/

# Remove files not needed for serving
RUN rm -f /usr/share/nginx/html/Dockerfile \
    /usr/share/nginx/html/docker-compose.yml \
    /usr/share/nginx/html/.env.example \
    /usr/share/nginx/html/README.md

# Custom nginx config
RUN { \
    echo 'server {'; \
    echo '    listen 80;'; \
    echo '    root /usr/share/nginx/html;'; \
    echo '    index index.html;'; \
    echo '    location / {'; \
    echo '        try_files $uri $uri/ /index.html;'; \
    echo '    }'; \
    echo '    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|webp)$ {'; \
    echo '        expires 1y;'; \
    echo '        add_header Cache-Control "public, immutable";'; \
    echo '    }'; \
    echo '}'; \
} > /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --spider -q http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
