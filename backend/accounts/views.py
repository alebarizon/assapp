"""Views de autenticação — login, register (signup simulado) e setup pós-compra."""
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from django_tenants.utils import get_tenant_model, schema_context
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .plans import PLAN_SLUGS, SAAS_PLANS, get_plan
from .serializers import UserSerializer
from .validators import validate_tenant_slug


def _tenant_status_payload(schema_name: str) -> dict:
    """Lê flags do Tenant em public para o schema informado."""
    Tenant = get_tenant_model()
    if schema_name == "sistema":
        return {
            "schema_name": "sistema",
            "setup_completed": True,
            "plan_slug": None,
            "name": "Sistema AssApp",
            "is_sistema": True,
        }
    with schema_context("public"):
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return {
                "schema_name": schema_name,
                "setup_completed": False,
                "plan_slug": None,
                "name": None,
                "is_sistema": False,
            }
        return {
            "schema_name": tenant.schema_name,
            "setup_completed": tenant.setup_completed,
            "plan_slug": tenant.plan_slug,
            "name": tenant.name,
            "cnpj": tenant.cnpj,
            "city": tenant.city,
            "state": tenant.state,
            "description": tenant.description,
            "is_sistema": False,
        }


def _issue_auth_response(user: User, user_schema: str) -> dict:
    refresh = RefreshToken.for_user(user)
    tenant_status = _tenant_status_payload(user_schema)
    return {
        "user": UserSerializer(user).data,
        "tenant_schema": user_schema,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "setup_completed": tenant_status["setup_completed"],
        "tenant": tenant_status,
    }


def _resolve_request_schema(request) -> str | None:
    if hasattr(request, "tenant") and request.tenant:
        return request.tenant.schema_name
    user = request.user
    if getattr(user, "_tenant_schema", None):
        return user._tenant_schema
    if getattr(user, "role", None) == User.SUPERADMIN:
        return "sistema"
    return None


class SimpleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response(
                {"error": "Email e senha são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = None
        user_schema = None
        Tenant = get_tenant_model()

        with schema_context("public"):
            try:
                Tenant.objects.get(schema_name="sistema", is_active=True)
                with schema_context("sistema"):
                    candidate = User.objects.filter(email=email).first()
                    if candidate and candidate.check_password(password):
                        user = candidate
                        user_schema = "sistema"
            except Tenant.DoesNotExist:
                pass

            if not user:
                for tenant in Tenant.objects.filter(is_active=True).exclude(
                    schema_name="sistema"
                ):
                    with schema_context(tenant.schema_name):
                        candidate = User.objects.filter(email=email).first()
                        if candidate and candidate.check_password(password):
                            user = candidate
                            user_schema = tenant.schema_name
                            break

        if not user or not user.check_password(password):
            return Response(
                {"error": "Credenciais inválidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {"error": "Usuário inativo."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        with schema_context(user_schema):
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])
            payload = _issue_auth_response(user, user_schema)

        return Response(payload, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        """H2 — permite atualizar perfil_tecnico."""
        allowed = {"perfil_tecnico", "first_name", "last_name", "phone_number", "locale"}
        for field in allowed:
            if field in request.data:
                setattr(request.user, field, request.data[field])
        request.user.save()
        return Response(UserSerializer(request.user).data)


class PublicPlansView(APIView):
    """GET /api/auth/plans/ — planos SaaS estáticos (sem Stripe neste ciclo)."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(SAAS_PLANS)


class RegisterAssociationView(APIView):
    """
    Signup público com pagamento simulado.
    Cria Tenant + Domain + schema + User(association_admin) e devolve JWT.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data or {}
        first_name = (payload.get("first_name") or "").strip()
        last_name = (payload.get("last_name") or "").strip()
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password") or ""
        association_name = (payload.get("association_name") or "").strip()
        tenant_slug_raw = (payload.get("tenant_slug") or "").strip().lower()
        plan_slug = (payload.get("plan_slug") or payload.get("plan") or "").strip().lower()
        cnpj = (payload.get("cnpj") or "").strip() or None
        phone = (payload.get("phone") or payload.get("phone_number") or "").strip() or None
        city = (payload.get("city") or "").strip() or None
        state = (payload.get("state") or "").strip().upper() or None
        if state and len(state) > 2:
            state = state[:2]

        if not all([email, password, first_name, association_name, tenant_slug_raw, plan_slug]):
            return Response(
                {
                    "detail": (
                        "Campos obrigatórios: first_name, email, password, "
                        "association_name, tenant_slug, plan_slug."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(password) < 8:
            return Response(
                {"detail": "A senha deve ter pelo menos 8 caracteres."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if plan_slug not in PLAN_SLUGS or not get_plan(plan_slug):
            return Response(
                {"detail": f"Plano inválido. Opções: {', '.join(sorted(PLAN_SLUGS))}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant_slug = validate_tenant_slug(tenant_slug_raw)
        except DjangoValidationError as exc:
            msg = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        Tenant = get_tenant_model()
        from tenants.models import Domain

        with schema_context("public"):
            if Tenant.objects.filter(slug=tenant_slug).exists() or Tenant.objects.filter(
                schema_name=tenant_slug
            ).exists():
                return Response(
                    {"detail": f"O slug '{tenant_slug}' já está em uso. Escolha outro."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Tenant.objects.filter(name__iexact=association_name).exists():
                return Response(
                    {"detail": "Já existe uma associação com este nome."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Schema + migrate via auto_create_schema
            tenant = Tenant.objects.create(
                name=association_name,
                slug=tenant_slug,
                schema_name=tenant_slug,
                cnpj=cnpj,
                city=city,
                state=state,
                is_active=True,
                on_trial=True,
                setup_completed=False,
                plan_slug=plan_slug,
                payment_simulated=True,
            )

            base_domain = getattr(settings, "BASE_DOMAIN", "localhost")
            # Dev local: slug.localhost (mesmo padrão do init); senão slug.BASE_DOMAIN
            if "localhost" in base_domain or base_domain in ("assapp.local", "localhost"):
                domain_name = f"{tenant_slug}.localhost"
            else:
                domain_name = f"{tenant_slug}.{base_domain}"

            Domain.objects.create(
                domain=domain_name,
                tenant=tenant,
                is_primary=True,
            )
            tenant_id = tenant.id

        with schema_context(tenant_slug):
            if User.objects.filter(email=email).exists():
                # rollback tenant em public
                with schema_context("public"):
                    Tenant.objects.filter(id=tenant_id).delete()
                return Response(
                    {"detail": "Este e-mail já está em uso."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User(
                email=email,
                username=email.split("@")[0],
                first_name=first_name,
                last_name=last_name,
                role=User.ASSOCIATION_ADMIN,
                phone_number=phone,
                is_staff=True,
                is_active=True,
                perfil_tecnico=User.PERFIL_INICIANTE,
                terms_accepted=True,
            )
            user.set_password(password)
            user.tenant_id = tenant_id
            user.save()

            with schema_context("public"):
                Tenant.objects.filter(id=tenant_id).update(owner_id=user.id)

            payload = _issue_auth_response(user, tenant_slug)

        return Response(payload, status=status.HTTP_201_CREATED)


class TenantStatusView(APIView):
    """GET /api/auth/tenant-status/ — setup_completed e dados cadastrais leves."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        schema = _resolve_request_schema(request)
        if not schema:
            return Response(
                {"detail": "Não foi possível identificar o tenant da sessão."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(_tenant_status_payload(schema))


class AssociationSetupView(APIView):
    """
    POST /api/auth/setup/ — wizard pós-compra: dados + 1º mandato + diretoria.
    Não reutiliza TransicaoMandato / OnboardingEtapa (H2).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role == User.SUPERADMIN:
            return Response(
                {"detail": "Superadmin não realiza setup de associação."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schema = _resolve_request_schema(request)
        if not schema or schema == "sistema":
            return Response(
                {"detail": "Tenant da sessão não identificado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Tenant = get_tenant_model()
        with schema_context("public"):
            try:
                tenant = Tenant.objects.get(schema_name=schema)
            except Tenant.DoesNotExist:
                return Response(
                    {"detail": "Associação não encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if tenant.setup_completed:
                return Response(
                    {"detail": "Setup já concluído para esta associação."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            tenant_id = tenant.id

        payload = request.data or {}
        mandato_data = payload.get("mandato") or {}
        cargos_data = payload.get("cargos") or []

        titulo = (mandato_data.get("titulo") or "").strip()
        data_inicio_raw = mandato_data.get("data_inicio")
        data_fim_raw = mandato_data.get("data_fim")

        if not titulo or not data_inicio_raw:
            return Response(
                {"detail": "mandato.titulo e mandato.data_inicio são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data_inicio = date.fromisoformat(str(data_inicio_raw)[:10])
            data_fim = (
                date.fromisoformat(str(data_fim_raw)[:10]) if data_fim_raw else None
            )
        except ValueError:
            return Response(
                {"detail": "Datas do mandato inválidas (use YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Atualiza dados cadastrais do Tenant
        with schema_context("public"):
            tenant = Tenant.objects.get(id=tenant_id)
            for field in ("description", "city", "cnpj"):
                if field in payload and payload[field] is not None:
                    setattr(tenant, field, (payload[field] or "").strip() or None)
            if "state" in payload and payload["state"] is not None:
                st = (payload["state"] or "").strip().upper()
                tenant.state = st[:2] if st else None
            if "association_name" in payload and payload["association_name"]:
                tenant.name = payload["association_name"].strip()
            tenant.save()

        from mandatos.models import CargoMandato, Mandato, MandatoStatus, TipoCargo

        valid_cargos = {c.value for c in TipoCargo}

        if not cargos_data:
            cargos_data = [{"cargo": TipoCargo.PRESIDENTE}]

        cargos_normalizados = []
        for item in cargos_data:
            cargo = (item.get("cargo") or "").strip().lower()
            if cargo not in valid_cargos:
                return Response(
                    {"detail": f"Cargo inválido: {cargo}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cargos_normalizados.append(
                {
                    "cargo": cargo,
                    "email": (item.get("email") or "").strip().lower() or None,
                    "first_name": (item.get("first_name") or "").strip(),
                    "last_name": (item.get("last_name") or "").strip(),
                    "cargo_custom": (item.get("cargo_custom") or "").strip() or None,
                }
            )

        if not any(c["cargo"] == TipoCargo.PRESIDENTE for c in cargos_normalizados):
            return Response(
                {"detail": "É obrigatório informar ao menos um cargo presidente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for item in cargos_normalizados:
            if item["cargo"] != TipoCargo.PRESIDENTE and not item["email"]:
                return Response(
                    {
                        "detail": (
                            f"Informe e-mail para o cargo {item['cargo']} "
                            "(exceto presidente, que pode usar o admin)."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with schema_context(schema):
            if Mandato.objects.filter(status=MandatoStatus.ATIVO).exists():
                return Response(
                    {"detail": "Já existe um mandato ativo neste tenant."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Mandato.objects.filter(numero_sequencial=1).exists():
                return Response(
                    {"detail": "O 1º mandato já foi criado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            admin_user = User.objects.get(pk=request.user.pk)

            with transaction.atomic():
                mandato = Mandato.objects.create(
                    titulo=titulo,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    status=MandatoStatus.ATIVO,
                    numero_sequencial=1,
                    descricao=mandato_data.get("descricao") or None,
                )
                mandato_id = mandato.id

                for item in cargos_normalizados:
                    email = item["email"]
                    if item["cargo"] == TipoCargo.PRESIDENTE and not email:
                        board_user = admin_user
                    else:
                        board_user = User.objects.filter(email=email).first()
                        if not board_user:
                            board_user = User(
                                email=email,
                                username=email.split("@")[0],
                                first_name=item["first_name"] or email.split("@")[0],
                                last_name=item["last_name"],
                                role=User.BOARD_MEMBER,
                                is_active=True,
                                perfil_tecnico=User.PERFIL_INICIANTE,
                                tenant_id=tenant_id,
                            )
                            board_user.set_password(get_random_string(12))
                            board_user.save()
                        elif board_user.role == User.MEMBER:
                            board_user.role = User.BOARD_MEMBER
                            board_user.save(update_fields=["role"])

                    CargoMandato.objects.create(
                        mandato=mandato,
                        usuario=board_user,
                        cargo=item["cargo"],
                        cargo_custom=item["cargo_custom"],
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        ativo=True,
                    )

        with schema_context("public"):
            Tenant.objects.filter(id=tenant_id).update(setup_completed=True)

        return Response(
            {
                "detail": "Setup concluído.",
                "setup_completed": True,
                "mandato_id": str(mandato_id),
                "tenant": _tenant_status_payload(schema),
            },
            status=status.HTTP_201_CREATED,
        )
