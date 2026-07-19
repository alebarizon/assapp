#!/bin/bash
# =============================================================================
# Setup inicial — DigitalOcean Droplet (AssApp)
# Adaptado de WellSaaS scripts/setup_digitalocean.sh
#
# Uso (do Mac):
#   scp scripts/setup_digitalocean.sh root@159.203.183.184:/tmp/
#   ssh root@159.203.183.184 'bash /tmp/setup_digitalocean.sh'
#
# Ou no servidor:
#   curl -fsSL https://raw.githubusercontent.com/alebarizon/assapp/main/scripts/setup_digitalocean.sh | bash
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_DIR="/opt/assapp"

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
warning() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
error() { echo -e "${RED}[ERRO]${NC} $1" >&2; exit 1; }

if [ "$(id -u)" -ne 0 ]; then
  error "Execute como root (ssh root@...)"
fi

log "Iniciando setup do servidor DigitalOcean (AssApp)..."

export DEBIAN_FRONTEND=noninteractive

log "Atualizando sistema..."
apt-get update
apt-get upgrade -y

log "Instalando dependências básicas..."
apt-get install -y \
  curl \
  wget \
  git \
  vim \
  ufw \
  fail2ban \
  unattended-upgrades \
  apt-transport-https \
  ca-certificates \
  gnupg \
  lsb-release \
  lsof

log "Instalando Docker..."
if ! command -v docker &>/dev/null; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable docker
  systemctl start docker
  log "Docker instalado"
else
  log "Docker já está instalado"
fi

# Plugin compose (docker compose) já vem com docker-compose-plugin
if docker compose version &>/dev/null; then
  log "Docker Compose plugin OK: $(docker compose version)"
else
  warning "docker compose plugin não encontrado — verifique a instalação"
fi

log "Configurando usuário deploy..."
if ! id -u deploy &>/dev/null; then
  useradd -m -s /bin/bash deploy
  usermod -aG docker deploy
  usermod -aG sudo deploy
  # Mesma chave SSH do root, se existir
  if [ -f /root/.ssh/authorized_keys ]; then
    mkdir -p /home/deploy/.ssh
    cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
    chown -R deploy:deploy /home/deploy/.ssh
    chmod 700 /home/deploy/.ssh
    chmod 600 /home/deploy/.ssh/authorized_keys
  fi
  log "Usuário 'deploy' criado"
else
  usermod -aG docker deploy || true
  log "Usuário 'deploy' já existe"
fi

log "Configurando firewall (UFW)..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # Produção HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8080/tcp  # Staging (mesmo droplet)
log "Firewall: 22, 80, 443, 8080"

log "Configurando fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

log "Configurando atualizações automáticas..."
grep -q 'Automatic-Reboot "false"' /etc/apt/apt.conf.d/50unattended-upgrades 2>/dev/null \
  || echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades
systemctl enable unattended-upgrades

log "Criando diretório da aplicação ${APP_DIR}..."
mkdir -p "$APP_DIR"
chown deploy:deploy "$APP_DIR"

log "Configurando swap..."
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  log "Swap 2GB configurado"
else
  log "Swap já existe"
fi

log "Instalando Certbot (SSL futuro)..."
apt-get install -y certbot

log "Ajustando limites do sistema..."
if ! grep -q 'soft nofile 65536' /etc/security/limits.conf 2>/dev/null; then
  cat >> /etc/security/limits.conf << 'EOF'
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
EOF
fi

log "Setup concluído!"
echo ""
log "Verificações rápidas:"
docker --version
docker compose version
ufw status numbered | head -20
ls -ld "$APP_DIR"
echo ""
log "Próximos passos:"
log "1. Secrets no GitHub: DO_HOST=IP, DO_USER=root|deploy, DO_SSH_KEY, DOCKER_*"
log "2. No Mac: completar docker-compose.prod.yml / staging + scripts/deploy.sh"
log "3. Clone (quando for deploy): git clone https://github.com/alebarizon/assapp.git ${APP_DIR}"
log "4. SSL (quando tiver domínio): certbot certonly --standalone -d seu-dominio.com"
