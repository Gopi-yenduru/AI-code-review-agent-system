# =============================================================================
# Frontend Dockerfile — AI Code Review Agent (React + Vite + Nginx)
# =============================================================================

# --- Build Stage ---
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- Production Stage ---
FROM nginx:alpine AS production

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx config for SPA routing with environment variable substitution
COPY nginx.conf /etc/nginx/templates/default.conf.template
ENV BACKEND_URL=http://localhost:8000

EXPOSE 80

CMD ["/bin/sh", "-c", "envsubst '$BACKEND_URL' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
