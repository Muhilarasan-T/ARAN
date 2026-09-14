# ---- Build Stage ----
FROM node:18-alpine AS build

WORKDIR /app

# Copy package.json and install dependencies
COPY frontend/package.json ./
RUN npm install

# Copy frontend source code and build
COPY frontend/ ./
RUN npm run build

# ---- Production Stage ----
FROM nginx:alpine

# Copy the build artifacts from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Replace default nginx config with our reverse-proxy config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Default nginx config will serve index.html
CMD ["nginx", "-g", "daemon off;"]
