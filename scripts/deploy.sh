#!/usr/bin/env bash
# =============================================================================
# Deploy AssApp (DigitalOcean) — padrão WellSaaS (pull-only)
#
# Uso:
#   ./scripts/deploy.sh staging
#   ./scripts/deploy.sh production
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
warning() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
error() { echo -e "${RED}[ERRO]${NC} $1" >&2; exit 1; }

ENVIRONMENT=${1:-staging}
if [[ ! "$ENVIRONMENT" =~ ^(production|staging)$ ]]; then
  error "Ambiente inválido: $ENVIRONMENT (use staging ou production)"
fi

if [ ! -f docker-compose.yml ]; then
  error "Execute a partir da raiz do projeto (/opt/assapp)"
fi

ENV_FILE=".env.$ENVIRONMENT"
if [ ! -f "$ENV_FILE" ]; then
  error "Arquivo $ENV_FILE não encontrado. Crie a partir de env.${ENVIRONMENT}.example"
fi

if [ "$ENVIRONMENT" = "production" ]; then
  COMPOSE_FILE="docker-compose.prod.yml"
  IMAGE_TAG_DEFAULT="latest"
  HOST_PORT=80
  CONTAINER_NAMES="assapp_db_prod assapp_backend_prod assapp_frontend_prod assapp_nginx_prod"
else
  COMPOSE_FILE="docker-compose.staging.yml"
  IMAGE_TAG_DEFAULT="develop"
  HOST_PORT=8080
  CONTAINER_NAMES="assapp_db_staging assapp_backend_staging assapp_frontend_staging assapp_nginx_staging"
fi

log "Deploy AssApp → $ENVIRONMENT ($COMPOSE_FILE)"

# Carrega env (ignora comentários e linhas vazias)
set -a
# shellcheck disable=SC1090
source <(grep -v '^#' "$ENV_FILE" | grep -v '^$' | sed 's/\r$//')
set +a

DOCKER_USERNAME_VALUE=${DOCKER_USERNAME:-alebarizon}
IMAGE_TAG_VALUE=${IMAGE_TAG:-$IMAGE_TAG_DEFAULT}
BACKEND_IMAGE="${DOCKER_USERNAME_VALUE}/assapp-backend:${IMAGE_TAG_VALUE}"
FRONTEND_IMAGE="${DOCKER_USERNAME_VALUE}/assapp-frontend:${IMAGE_TAG_VALUE}"

if grep -qE '^[[:space:]]*build:' "$COMPOSE_FILE"; then
  error "build: encontrado em $COMPOSE_FILE — proibido em staging/prod (somente pull)"
fi

export COMPOSE_DOCKER_CLI_BUILD=0
export DOCKER_BUILDKIT=0

# Desabilita Dockerfiles locais (evita build acidental)
for df in frontend/Dockerfile backend/Dockerfile; do
  if [ -f "$df" ]; then
    mv "$df" "${df}.disabled" 2>/dev/null || true
  fi
done

log "Parando stack anterior..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans --timeout 30 2>/dev/null || true
for c in $CONTAINER_NAMES; do
  docker stop "$c" 2>/dev/null || true
  docker rm -f "$c" 2>/dev/null || true
done

if command -v lsof &>/dev/null; then
  if lsof -i ":$HOST_PORT" 2>/dev/null | grep -q LISTEN; then
    warning "Porta $HOST_PORT em uso — tentando liberar containers que a usam"
    docker ps --format '{{.ID}} {{.Ports}}' | grep -E ":${HOST_PORT}->" | awk '{print $1}' | xargs -r docker stop 2>/dev/null || true
    docker ps -a --format '{{.ID}} {{.Ports}}' | grep -E ":${HOST_PORT}->|: ${HOST_PORT}/" | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true
  fi
fi

if [ -n "${DOCKER_PASSWORD:-}" ]; then
  log "Login Docker Hub..."
  echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME_VALUE" --password-stdin
fi

log "Pull $BACKEND_IMAGE"
docker pull "$BACKEND_IMAGE"
log "Pull $FRONTEND_IMAGE"
docker pull "$FRONTEND_IMAGE"

log "Subindo stack..."
IMAGE_TAG="$IMAGE_TAG_VALUE" DOCKER_USERNAME="$DOCKER_USERNAME_VALUE" \
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

log "Aguardando health (:$HOST_PORT/health/)..."
HEALTH_OK=false
for i in $(seq 1 24); do
  if curl -fsS "http://127.0.0.1:${HOST_PORT}/health/" >/dev/null 2>&1; then
    HEALTH_OK=true
    break
  fi
  sleep 5
done

if [ "$HEALTH_OK" = true ]; then
  log "✅ Health OK — AssApp $ENVIRONMENT no ar (porta $HOST_PORT)"
else
  warning "Health ainda falhou — logs recentes do backend:"
  docker logs "assapp_backend_${ENVIRONMENT}" --tail 80 2>&1 || true
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps || true
  exit 1
fi

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
log "Deploy $ENVIRONMENT concluído."
