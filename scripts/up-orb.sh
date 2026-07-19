#!/usr/bin/env bash
# up-orb.sh — Sobe o ambiente de desenvolvimento no Mac (OrbStack / ARM64)
#
# Uso:
#   ./scripts/up-orb.sh           — sobe em foreground (logs no terminal)
#   ./scripts/up-orb.sh -d        — sobe em background (detached)
#   ./scripts/up-orb.sh --build   — força rebuild da imagem frontend antes de subir
#   ./scripts/up-orb.sh --help    — exibe esta ajuda
#
# Equivalente manual:
#   docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.orb.yml up

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

COMPOSE_CMD="docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  -f docker-compose.orb.yml"

FRONTEND_IMAGE="assapp-frontend-dev:local"
DETACHED=false
BUILD_FRONTEND=false

# ─── Parseia argumentos ───────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    -d|--detach)   DETACHED=true ;;
    --build)       BUILD_FRONTEND=true ;;
    --help|-h)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *)
      echo "Argumento desconhecido: $arg. Use --help para instruções."
      exit 1
      ;;
  esac
done

cd "$PROJECT_ROOT"

# ─── Verificações iniciais ────────────────────────────────────────────────────
echo ">>> Verificando ambiente..."

if ! command -v docker &>/dev/null; then
  echo "ERRO: Docker não encontrado. Instale o OrbStack: https://orbstack.dev"
  exit 1
fi

if ! docker info &>/dev/null 2>&1; then
  echo "ERRO: Docker daemon não está acessível. Abra o OrbStack e tente novamente."
  exit 1
fi

for f in docker-compose.yml docker-compose.dev.yml docker-compose.orb.yml; do
  if [ ! -f "$f" ]; then
    echo "ERRO: Arquivo $f não encontrado em $PROJECT_ROOT"
    exit 1
  fi
done

if [ ! -f ".env" ]; then
  echo ">>> .env não encontrado — copiando de .env.example"
  cp .env.example .env
  echo "    Edite .env se precisar ajustar portas/credenciais."
fi

# ─── Build da imagem frontend (se solicitado ou se não existe) ─────────────────
if $BUILD_FRONTEND || ! docker image inspect "$FRONTEND_IMAGE" &>/dev/null 2>&1; then
  echo ">>> Buildando imagem frontend para ARM64: $FRONTEND_IMAGE"
  docker build \
    --platform linux/arm64 \
    -f frontend/Dockerfile.dev \
    -t "$FRONTEND_IMAGE" \
    ./frontend
  echo ">>> Imagem frontend buildada com sucesso."
else
  echo ">>> Imagem frontend já existe: $FRONTEND_IMAGE (use --build para forçar rebuild)"
fi

# ─── Sobe os containers ───────────────────────────────────────────────────────
echo ""
echo ">>> Subindo ambiente AssApp (OrbStack / ARM64)..."
echo "    Compose files: docker-compose.yml + docker-compose.dev.yml + docker-compose.orb.yml"
echo "    Frontend: http://localhost:${FRONTEND_PORT:-5174}"
echo "    Backend:  http://localhost:${BACKEND_PORT:-8001}"
echo ""

if $DETACHED; then
  $COMPOSE_CMD up -d
  echo ""
  echo ">>> Ambiente subido em background. Comandos úteis:"
  echo "    docker compose logs -f backend"
  echo "    docker compose logs -f frontend"
  echo "    docker compose ps"
  echo "    docker compose down"
else
  $COMPOSE_CMD up
fi
