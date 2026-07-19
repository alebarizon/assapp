# Dockerfile para Backend Django - Wellnz SaaS
# 
# Este Dockerfile constrói a imagem do backend Django com Gunicorn
# para produção com suporte ao django-tenants

FROM python:3.11-slim as base

# Define variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Stage: Dependencies
# =============================================================================

FROM base as dependencies

# Copia arquivos de requisitos
COPY requirements.txt /app/

# Instala dependências Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage: Test (inclui dependências de teste)
# =============================================================================

FROM dependencies as test

# As dependências de teste já estão no requirements.txt
# Este stage pode ser usado para executar testes
# Exemplo: docker build --target test -t wellsaas-backend:test .

# =============================================================================
# Stage: Production
# =============================================================================

FROM base as production

# Copia dependências instaladas
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Cria usuário não-root para executar o aplicativo
RUN groupadd -r django && useradd -r -g django django && \
    mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R django:django /app && \
    chmod -R 755 /app/logs

# Copia código do projeto
COPY --chown=django:django . /app/

# Define usuário
USER django

# Expõe porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Comando padrão
CMD ["gunicorn", "--config", "gunicorn_config.py", "core.wsgi:application"]

