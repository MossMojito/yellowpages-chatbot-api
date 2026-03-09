#!/usr/bin/env bash
# =============================================================================
# deploy-gcp.sh — End-to-end GCP deployment for Yellow Pages Chatbot
#
# Prerequisites:
#   - gcloud CLI installed and authenticated (`gcloud auth login`)
#   - Docker Desktop running
#   - kubectl installed
#   - OPENAI_API_KEY exported in your shell (or passed as $1)
#
# Usage:
#   export OPENAI_API_KEY="sk-..."
#   bash scripts/deploy-gcp.sh
#
# Or pass the key directly:
#   bash scripts/deploy-gcp.sh "sk-..."
# =============================================================================

set -euo pipefail   # Exit on error, unset variable, or pipe failure

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID="earnest-cooler-377009"
REGION="asia-southeast1"
CLUSTER_NAME="yellowpages-cluster"
REPO_NAME="yellowpages-chatbot"       # Artifact Registry repository name
BACKEND_IMAGE="backend"
FRONTEND_IMAGE="frontend"
K8S_SECRET_NAME="app-secrets"

# Image URIs (Artifact Registry format)
AR_HOST="${REGION}-docker.pkg.dev"
BACKEND_URI="${AR_HOST}/${PROJECT_ID}/${REPO_NAME}/${BACKEND_IMAGE}:latest"
FRONTEND_URI="${AR_HOST}/${PROJECT_ID}/${REPO_NAME}/${FRONTEND_IMAGE}:latest"

# Resolve OPENAI_API_KEY from arg or environment
OPENAI_API_KEY="${1:-${OPENAI_API_KEY:-}}"
if [[ -z "$OPENAI_API_KEY" ]]; then
  echo "❌ OPENAI_API_KEY is not set. Export it or pass it as the first argument."
  exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Yellow Pages Chatbot — GCP Deployment                 ║"
echo "║   Project : ${PROJECT_ID}                    ║"
echo "║   Region  : ${REGION}                            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Set active GCP project
# ─────────────────────────────────────────────────────────────────────────────
echo "▶ STEP 1 — Setting GCP project to ${PROJECT_ID}..."
gcloud config set project "${PROJECT_ID}"
echo "✅ Project set."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Enable required APIs
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ STEP 2 — Enabling required GCP APIs..."
gcloud services enable \
  container.googleapis.com \
  artifactregistry.googleapis.com \
  --project="${PROJECT_ID}"
echo "✅ APIs enabled: container, artifactregistry."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Create Artifact Registry repository (idempotent)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ STEP 3 — Creating Artifact Registry repository '${REPO_NAME}'..."
if gcloud artifacts repositories describe "${REPO_NAME}" \
     --location="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "   Repository already exists — skipping creation."
else
  gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Docker images for Yellow Pages Chatbot" \
    --project="${PROJECT_ID}"
  echo "✅ Repository created."
fi

# Configure Docker to authenticate against Artifact Registry
gcloud auth configure-docker "${AR_HOST}" --quiet
echo "✅ Docker authenticated with Artifact Registry."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Build and push Docker images
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ STEP 4 — Building and pushing Docker images..."

# Backend image
echo "   🔨 Building backend image..."
docker build -t "${BACKEND_URI}" ./backend
echo "   📤 Pushing backend image..."
docker push "${BACKEND_URI}"
echo "   ✅ Backend image pushed: ${BACKEND_URI}"

# Frontend image (requires frontend/Dockerfile — Task 2)
echo "   🔨 Building frontend image..."
docker build -t "${FRONTEND_URI}" ./frontend
echo "   📤 Pushing frontend image..."
docker push "${FRONTEND_URI}"
echo "   ✅ Frontend image pushed: ${FRONTEND_URI}"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Create GKE Autopilot cluster (idempotent)
# Using Autopilot: no node pool management needed, scales automatically
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ STEP 5 — Creating GKE cluster '${CLUSTER_NAME}' (Autopilot)..."
if gcloud container clusters describe "${CLUSTER_NAME}" \
     --region="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "   Cluster already exists — skipping creation."
else
  gcloud container clusters create-auto "${CLUSTER_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}"
  echo "✅ GKE Autopilot cluster created."
fi

# Fetch cluster credentials so kubectl can connect
gcloud container clusters get-credentials "${CLUSTER_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}"
echo "✅ kubectl configured for cluster '${CLUSTER_NAME}'."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Create Kubernetes secret for OPENAI_API_KEY (idempotent)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ STEP 6 — Creating Kubernetes secret '${K8S_SECRET_NAME}'..."
if kubectl get secret "${K8S_SECRET_NAME}" &>/dev/null; then
  echo "   Secret already exists — updating..."
  kubectl delete secret "${K8S_SECRET_NAME}"
fi
kubectl create secret generic "${K8S_SECRET_NAME}" \
  --from-literal=openai-api-key="${OPENAI_API_KEY}"
echo "✅ Kubernetes secret created."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Apply Kubernetes deployment manifests
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ STEP 7 — Applying Kubernetes manifests..."
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
echo "✅ Manifests applied."

# ─────────────────────────────────────────────────────────────────────────────
# Wait for deployments to roll out
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "⏳ Waiting for backend rollout..."
kubectl rollout status deployment/backend --timeout=180s

echo "⏳ Waiting for frontend rollout..."
kubectl rollout status deployment/frontend --timeout=180s

# ─────────────────────────────────────────────────────────────────────────────
# Print external IPs
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "🌐 Fetching external IPs (may take 1-2 minutes for LoadBalancer provisioning)..."
echo ""
kubectl get services backend-service frontend-service

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   ✅  Deployment complete!                               ║"
echo "║   Use the EXTERNAL-IP above to access your services.    ║"
echo "╚══════════════════════════════════════════════════════════╝"
