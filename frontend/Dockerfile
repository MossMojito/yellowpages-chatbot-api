# =============================================================================
# Multi-stage Dockerfile for the React (Vite) frontend
#
# Stage 1 — builder : installs dependencies and runs `vite build`
# Stage 2 — runtime : copies the dist/ output into a tiny nginx image
#
# Result: a lean production image (~25 MB) with no Node.js or dev deps
# =============================================================================

# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:18-alpine AS builder

# Set working directory inside the build container
WORKDIR /app

# Copy dependency manifests first for layer caching.
# npm install only reruns when package*.json changes, not on every code change.
COPY package.json package-lock.json ./

# Install all dependencies (including devDependencies needed for the build)
RUN npm ci --silent

# Copy the rest of the source code
COPY . .

# Build the production bundle — Vite outputs to ./dist by default
RUN npm run build

# ── Stage 2: Runtime (nginx) ──────────────────────────────────────────────────
FROM nginx:stable-alpine

# Remove the default nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy the Vite production build from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom nginx config (handles SPA routing + /api proxy)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 (nginx default)
EXPOSE 80

# Start nginx in the foreground so Docker can manage the process
CMD ["nginx", "-g", "daemon off;"]
