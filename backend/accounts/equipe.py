"""Gestão da equipe da associação: convites, perfis e links de senha."""
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError

from core.emails import enviar_email, frontend_url

from .access import GESTOR, PERFIS_VALIDOS, is_equipe, perfis_do_user, sugerir_perfis
from .models import User


def normalizar_perfis(perfis):
    perfis = [p for p in dict.fromkeys(perfis or []) if p]
    invalidos = [p for p in perfis if p not in PERFIS_VALIDOS]
    if invalidos:
        raise ValidationError({"perfis": f"Perfil inválido: {', '.join(invalidos)}."})
    if not perfis:
        raise ValidationError({"perfis": "Selecione ao menos um perfil."})
    return perfis


def gestores_ativos(excluir=None):
    qs = User.objects.filter(is_active=True, role__in=(User.ASSOCIATION_ADMIN, User.BOARD_MEMBER))
    if excluir is not None:
        qs = qs.exclude(pk=excluir.pk)
    return [u for u in qs if GESTOR in perfis_do_user(u)]


def garantir_gestor_restante(user, novos_perfis=None, desativar=False):
    """Impede que a associação fique sem nenhum gestor ativo."""
    perde_gestao = desativar or (novos_perfis is not None and GESTOR not in novos_perfis)
    if perde_gestao and GESTOR in perfis_do_user(user) and not gestores_ativos(excluir=user):
        raise ValidationError(
            {"detail": "A associação precisa de ao menos um gestor ativo. Defina outro gestor antes."}
        )


def cargos_ativos(user):
    from mandatos.models import CargoMandato, MandatoStatus

    return list(
        CargoMandato.objects.filter(
            usuario=user, ativo=True, mandato__status=MandatoStatus.ATIVO
        ).values_list("cargo", flat=True)
    )


def perfis_sugeridos(user):
    return sugerir_perfis(cargos_ativos(user))


def link_definir_senha(user, schema):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return frontend_url(f"/definir-senha?schema={schema}&uid={uid}&token={token}")


def usuario_do_link(uid, token):
    try:
        pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=pk)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    if not default_token_generator.check_token(user, token):
        return None
    return user


def convite_pendente(user):
    return not user.has_usable_password() and user.last_login is None


def enviar_convite(user, schema, associacao, convidado_por=None):
    quem = (convidado_por.get_full_name() or convidado_por.email) if convidado_por else associacao
    texto = (
        f"Olá, {user.first_name or user.email}!\n\n"
        f"{quem} convidou você para acessar o painel de {associacao} no Gesttora.\n"
        "Clique no botão abaixo para definir sua senha. O link vale por alguns dias."
    )
    return enviar_email(
        user.email,
        f"Convite para o painel de {associacao}",
        texto,
        link=link_definir_senha(user, schema),
        link_label="Definir senha",
    )


def enviar_redefinicao(user, schema, associacao):
    texto = (
        f"Olá, {user.first_name or user.email}!\n\n"
        f"Recebemos um pedido para redefinir sua senha em {associacao}.\n"
        "Se não foi você, ignore este e-mail."
    )
    return enviar_email(
        user.email,
        "Redefinição de senha",
        texto,
        link=link_definir_senha(user, schema),
        link_label="Definir nova senha",
    )


@transaction.atomic
def convidar(*, email, first_name, last_name, perfis, tenant_id, schema, associacao, convidado_por):
    email = (email or "").strip().lower()
    if not email:
        raise ValidationError({"email": "Informe o e-mail."})
    perfis = normalizar_perfis(perfis)
    user = User.objects.filter(email=email).first()
    if user and is_equipe(user):
        raise ValidationError({"email": "Este e-mail já faz parte da equipe."})
    if user and user.role not in (User.MEMBER, User.REVIEWER):
        raise ValidationError({"email": "Este e-mail não pode ser adicionado à equipe."})
    if user:
        # Associado ou parecerista ganha acesso ao painel e mantém a própria senha.
        user.role = User.BOARD_MEMBER
        user.perfis = perfis
        user.is_active = True
        user.save(update_fields=["role", "perfis", "is_active"])
    else:
        user = User(
            email=email,
            first_name=(first_name or "").strip() or email.split("@")[0],
            last_name=(last_name or "").strip(),
            role=User.BOARD_MEMBER,
            perfis=perfis,
            tenant_id=tenant_id,
            is_active=True,
        )
        user.set_unusable_password()
        user.save()
    enviado = enviar_convite(user, schema, associacao, convidado_por)
    return user, enviado
