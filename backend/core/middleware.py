"""
Middleware customizado para path-based routing com django-tenants.

Este middleware identifica o tenant baseado no primeiro segmento do path da URL.
Usa o URL resolver do Django para distinguir entre rotas públicas e tenant slugs.

Documentação completa: docs/MIDDLEWARE_TENANT_ROUTING.md
Changelog: docs/CHANGELOG_MIDDLEWARE.md
"""
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve, Resolver404
from django_tenants.utils import get_tenant_model, get_public_schema_name, schema_context
from django_tenants.utils import remove_www
from django.db import connection


class TenantPathMiddleware(MiddlewareMixin):
    """
    Middleware para identificar tenant baseado no path da URL.
    
    Extrai o tenant do primeiro segmento do path:
    - wellflows.online/minhaempresa/... -> tenant: 'minhaempresa'
    - wellflows.online/... -> schema público
    
    Usa o URL resolver do Django para verificar se o path corresponde a uma rota
    registrada antes de tratar como tenant. Isso evita conflitos quando rotas
    públicas (como /health/, /admin/, /api/) são interpretadas como tenant slugs.
    
    IMPORTANTE: Este middleware deve estar ANTES de qualquer middleware que acesse o banco.
    O django-tenants configura automaticamente o schema quando request.tenant é definido.
    """
    
    TENANT_MODEL = None
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.TENANT_MODEL = get_tenant_model()
    
    def process_request(self, request):
        """
        Processa a requisição e identifica o tenant pelo path.
        Configura o schema do banco de dados através de request.tenant.
        """
        # Remove www do hostname se existir
        hostname = remove_www(request.get_host().split(':')[0])
        
        # Extrai o primeiro segmento do path
        path_parts = request.path.strip('/').split('/')
        tenant_slug = path_parts[0] if path_parts and path_parts[0] else None
        
        # Se não há primeiro segmento, é rota raiz - usa schema público
        if not tenant_slug:
            request.tenant = None
            return None
        
        # Tenta resolver a URL usando o URL resolver do Django
        # Se a rota existe no Django, é uma rota pública (health, admin, api, etc)
        # Isso é mais robusto que manter uma lista manual de rotas públicas
        try:
            # Tenta resolver sem acessar o banco primeiro
            # O resolve() do Django apenas verifica URLs, não precisa do banco
            resolve(request.path)
            
            # Rota existe no Django - é rota pública, usa schema público
            request.tenant = None
            return None
            
        except Resolver404:
            # Rota não existe no Django - pode ser um tenant slug
            # Continua o processamento abaixo para buscar o tenant
            pass
        except Exception:
            # Outro erro ao resolver (pode ser problema de configuração ou banco)
            # Por segurança, trata como rota pública
            request.tenant = None
            return None
        
        # Se chegou aqui, a rota não existe no Django - trata como tenant slug
        # Busca o tenant pelo slug no schema público
        try:
            # IMPORTANTE: Busca no schema público usando schema_context
            # Isso garante que a busca acontece no schema correto
            with schema_context(get_public_schema_name()):
                tenant = self.TENANT_MODEL.objects.get(slug=tenant_slug, is_active=True)
            
            # Define o tenant no request
            # O django-tenants detecta automaticamente e configura o schema através do backend
            # O backend django_tenants.postgresql_backend intercepta queries e usa o schema correto
            request.tenant = tenant
            
            # Ajusta o path removendo o slug do tenant
            # wellflows.online/minhaempresa/api/auth -> /api/auth
            new_path = '/' + '/'.join(path_parts[1:]) if len(path_parts) > 1 else '/'
            request.path = new_path
            request.path_info = new_path
            
        except self.TENANT_MODEL.DoesNotExist:
            # Tenant não encontrado, usa schema público
            request.tenant = None
        
        return None
    
    def process_response(self, request, response):
        """
        Processa a resposta (necessário para MiddlewareMixin).
        """
        return response


class TenantUserMiddleware(MiddlewareMixin):
    """
    Middleware para identificar o tenant do usuário autenticado.
    
    Quando não há tenant identificado pelo path (ex: /app/subscriptions),
    este middleware identifica o tenant do usuário logado e configura o schema.
    
    IMPORTANTE: Este middleware processa o token JWT diretamente porque o DRF
    processa a autenticação depois dos middlewares do Django.
    """
    
    TENANT_MODEL = None
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.TENANT_MODEL = get_tenant_model()
    
    def _get_user_from_jwt(self, request):
        """
        Extrai o usuário do token JWT se presente.
        Isso permite identificar o tenant antes do DRF processar a autenticação.
        """
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework_simplejwt.exceptions import InvalidToken
        
        auth = JWTAuthentication()
        try:
            header = auth.get_header(request)
            if header is None:
                return None
            
            raw_token = auth.get_raw_token(header)
            if raw_token is None:
                return None
            
            validated_token = auth.get_validated_token(raw_token)
            user_id = validated_token.get('user_id')
            
            if not user_id:
                return None
            
            # Usa a autenticação customizada para buscar o usuário
            from accounts.authentication import TenantAwareJWTAuthentication
            tenant_auth = TenantAwareJWTAuthentication()
            user = tenant_auth.get_user(validated_token)
            return user
        except (InvalidToken, Exception):
            return None
    
    def process_request(self, request):
        """
        Identifica o tenant do usuário autenticado se não há tenant no path.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Se já há tenant identificado pelo path, não faz nada
        if hasattr(request, 'tenant') and request.tenant:
            logger.debug(f"TenantUserMiddleware: Tenant já identificado pelo path: {request.tenant.schema_name}")
            return None
        
        # Tenta obter o usuário do JWT diretamente (antes do DRF processar)
        user = self._get_user_from_jwt(request)
        
        # Se não encontrou pelo JWT, tenta pelo request.user (pode estar autenticado por sessão)
        if not user and hasattr(request, 'user') and request.user and request.user.is_authenticated:
            user = request.user
        
        # Se não há usuário autenticado, não faz nada
        if not user:
            logger.debug("TenantUserMiddleware: Usuário não autenticado")
            return None
        
        logger.debug(f"TenantUserMiddleware: Processando usuário {user.id} (role: {getattr(user, 'role', 'N/A')})")
        
        # Se for superadmin, não tem tenant
        if hasattr(user, 'role') and user.role == 'superadmin':
            logger.debug("TenantUserMiddleware: Usuário é superadmin, não tem tenant")
            return None
        
        # Tenta obter o tenant do usuário de várias formas
        tenant = None
        
        # 1. PRIORIDADE MÁXIMA: Tenta usar o atributo _tenant definido diretamente pela autenticação
        # Este é o método mais rápido e confiável
        if hasattr(user, '_tenant') and user._tenant:
            tenant = user._tenant
            logger.debug(f"TenantUserMiddleware: Usando tenant do atributo _tenant: {tenant.schema_name}")
        
        # 2. PRIORIDADE: Tenta usar o atributo _tenant_schema definido pela autenticação
        # Este é o método mais confiável porque a autenticação já identificou o schema
        if not tenant and hasattr(user, '_tenant_schema') and user._tenant_schema:
            schema_name = user._tenant_schema
            try:
                with schema_context('public'):
                    tenant = self.TENANT_MODEL.objects.get(schema_name=schema_name, is_active=True)
                    logger.debug(f"TenantUserMiddleware: Buscou tenant pelo schema_name: {schema_name}")
            except self.TENANT_MODEL.DoesNotExist:
                pass
        
        # 2. Se não encontrou pelo _tenant_schema, tenta buscar pelo tenant_id do usuário
        # Mas precisa estar no schema correto para acessar o ForeignKey
        if not tenant and hasattr(user, 'tenant_id') and user.tenant_id:
            try:
                with schema_context('public'):
                    tenant = self.TENANT_MODEL.objects.get(id=user.tenant_id, is_active=True)
            except (self.TENANT_MODEL.DoesNotExist, AttributeError):
                pass
        
        # 3. Fallback: Busca o tenant pelo user_id em todos os schemas
        # Isso é mais lento, mas funciona como último recurso
        if not tenant:
            try:
                with schema_context('public'):
                    tenants = list(self.TENANT_MODEL.objects.filter(is_active=True))
                
                # Busca o usuário em cada schema para encontrar qual tenant ele pertence
                for t in tenants:
                    try:
                        with schema_context(t.schema_name):
                            from accounts.models import User
                            found_user = User.objects.filter(id=user.id).first()
                            if found_user:
                                tenant = t
                                # Armazena o schema para uso futuro
                                user._tenant_schema = t.schema_name
                                break
                    except Exception:
                        continue
            except Exception:
                pass
        
        # Se encontrou tenant, define no request E configura o schema
        # IMPORTANTE: O django-tenants precisa que connection.set_tenant seja chamado
        if tenant:
            request.tenant = tenant
            # Configura o schema explicitamente usando connection.set_tenant
            connection.set_tenant(tenant)
            logger.info(f"TenantUserMiddleware: ✅ Identificado e configurado tenant '{tenant.schema_name}' para usuário {user.id}")
        else:
            logger.warning(f"TenantUserMiddleware: ⚠️ Não foi possível identificar tenant para usuário {user.id}")
        
        return None

