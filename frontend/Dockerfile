FROM node:18-slim as builder

WORKDIR /app
COPY . .
# Frontend is static, no build needed - just copy

FROM nginx:alpine

# Copy static files
COPY --from=builder /app /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
