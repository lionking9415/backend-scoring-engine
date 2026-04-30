# Frontend Dockerfile for Google Cloud Run
# Two-stage build: Node for React, nginx:alpine to serve it.

# ── Stage 1: build the React app ─────────────────────────────────────
FROM node:18-alpine AS builder

WORKDIR /app

# Install deps first (layer-cached unless package.json changes)
COPY package*.json ./
RUN npm ci --prefer-offline

# Copy source and build
COPY public/ ./public/
COPY src/ ./src/
RUN npm run build

# ── Stage 2: serve with nginx ────────────────────────────────────────
FROM nginx:alpine

# gettext provides `envsubst`, used by the entrypoint to substitute
# ${BACKEND_URL} inside nginx.conf at container start-up.
RUN apk add --no-cache gettext

# nginx config template — BACKEND_URL substituted at runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Custom entrypoint that runs envsubst then starts nginx
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# React build artifacts
COPY --from=builder /app/build /usr/share/nginx/html

# Cloud Run forwards traffic to $PORT (default 8080); nginx listens on 8080.
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:8080/health || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
