"""
Configuração do Gunicorn para Wellnz SaaS

Este arquivo contém as configurações do servidor WSGI Gunicorn para o Django.
Use este arquivo com o comando:
    gunicorn core.wsgi:application -c gunicorn_config.py

Ou adicione ao seu systemd service file.
"""

import multiprocessing
import os

# Caminho base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# Configurações do Servidor
# =============================================================================

# Endereço e porta onde o Gunicorn irá escutar
bind = os.environ.get('GUNICORN_BIND', '127.0.0.1:8000')

# Número de workers (processos)
# Recomendado: (2 * num_cores) + 1
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# Tipo de worker
# Para Django, use 'sync' ou 'gevent' (requer gevent instalado)
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'sync')

# Número de threads por worker (apenas para worker_class='gthread')
threads = int(os.environ.get('GUNICORN_THREADS', 1))

# Timeout para workers (segundos)
# Aumente se tiver operações longas no Django
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))

# Keep-alive timeout (segundos)
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 5))

# =============================================================================
# Configurações de Performance
# =============================================================================

# Número máximo de requisições por worker antes de reiniciar
# Isso ajuda a prevenir memory leaks
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', 1000))

# Jitter para max_requests (previne que todos os workers reiniciem ao mesmo tempo)
max_requests_jitter = int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', 100))

# Worker timeout (mata workers que não respondem)
# Usa diretório temporário com permissão de escrita (/dev/shm é um tmpfs no Linux)
worker_tmp_dir = os.environ.get('GUNICORN_WORKER_TMP_DIR', '/dev/shm')

# =============================================================================
# Configurações de Logging
# =============================================================================

# Acesso (requests HTTP)
# Usa stdout em Docker (logs via docker logs) ou arquivo se especificado
default_access_log = os.environ.get('GUNICORN_ACCESS_LOG', '-')  # '-' = stdout
accesslog = default_access_log
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" '
    '%(D)s %(p)s %({Host}i)s %({X-Tenant-Subdomain}i)s'
)

# Erro (erros do servidor)
# Usa stderr em Docker (logs via docker logs) ou arquivo se especificado
default_error_log = os.environ.get('GUNICORN_ERROR_LOG', '-')  # '-' = stderr
errorlog = default_error_log

# Nível de log
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Captura output do stdout/stderr
capture_output = True

# =============================================================================
# Configurações de Processo
# =============================================================================

# Usuário e grupo para executar o Gunicorn (se executando como root)
# IMPORTANTE: Não execute como root em produção sem configurar isso
user = os.environ.get('GUNICORN_USER', None)
group = os.environ.get('GUNICORN_GROUP', None)

# Diretório de trabalho
chdir = BASE_DIR

# Python path
pythonpath = BASE_DIR

# =============================================================================
# Configurações de Segurança
# =============================================================================

# Limita o número de conexões pendentes
backlog = int(os.environ.get('GUNICORN_BACKLOG', 2048))

# Permite conexões somente de localhost (use com Nginx como proxy)
forwarded_allow_ips = os.environ.get('GUNICORN_FORWARDED_ALLOW_IPS', '127.0.0.1,::1')

# =============================================================================
# Configurações Específicas do Django
# =============================================================================

# Variáveis de ambiente
raw_env = [
    'DJANGO_SETTINGS_MODULE=core.settings',
]

# Pré-carregar a aplicação (melhora performance)
preload_app = os.environ.get('GUNICORN_PRELOAD', 'True') == 'True'

# =============================================================================
# Configurações Avançadas
# =============================================================================

# Graceful timeout (tempo para workers terminarem graciosamente)
graceful_timeout = int(os.environ.get('GUNICORN_GRACEFUL_TIMEOUT', 30))

# Spew (debug - imprime cada requisição)
spew = os.environ.get('GUNICORN_SPEW', 'False') == 'True'

# Daemon mode (executa em background - use com systemd em vez disso)
daemon = False

# PID file (útil para scripts de gerenciamento)
# Em Docker, não é necessário (ou pode usar /tmp)
# Se o diretório não existir, não cria pidfile (None = não cria)
import os
_logs_dir = os.path.join(BASE_DIR, 'logs')
if os.path.exists(_logs_dir) and os.access(_logs_dir, os.W_OK):
    pidfile = os.environ.get('GUNICORN_PIDFILE', os.path.join(_logs_dir, 'gunicorn.pid'))
else:
    pidfile = os.environ.get('GUNICORN_PIDFILE', None)  # Não cria pidfile se diretório não existir

# =============================================================================
# Hooks (Callbacks)
# =============================================================================

def on_starting(server):
    """Chamado quando o Gunicorn está iniciando."""
    server.log.info("Iniciando Gunicorn para Wellnz SaaS...")

def on_reload(server):
    """Chamado quando o Gunicorn está recarregando."""
    server.log.info("Recarregando Gunicorn...")

def when_ready(server):
    """Chamado quando o Gunicorn está pronto para aceitar conexões."""
    server.log.info(f"Gunicorn pronto. Escutando em {server.address}")

def worker_int(worker):
    """Chamado quando um worker recebe SIGINT ou SIGQUIT."""
    worker.log.info("Worker recebeu sinal de interrupção")

def pre_fork(server, worker):
    """Chamado antes de fazer fork de um worker."""
    pass

def post_fork(server, worker):
    """Chamado depois de fazer fork de um worker."""
    server.log.info(f"Worker {worker.pid} criado")

def pre_exec(server):
    """Chamado antes de fazer exec do novo processo."""
    server.log.info("Executando novo processo...")

def on_exit(server):
    """Chamado quando o Gunicorn está encerrando."""
    server.log.info("Gunicorn está encerrando...")

