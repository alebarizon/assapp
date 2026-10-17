"""Certificados de evento, verificação pública unificada, e-mails transacionais e idioma da API."""
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from core.certificados_views import CertificadoPdfView, CertificadoVerificacaoView
from courses.models import Course, CourseEnrollment
from courses.services import enroll_membro
from eventos.models import EventoAcademico, InscricaoEvento
from eventos.views import EventoAcademicoViewSet, InscricaoEventoViewSet
from formularios.models import Formulario, Pergunta, Resposta, Secao
from formularios.views import FormularioViewSet

factory = APIRequestFactory()


def _call(viewset_cls, actions, user, method, data=None, **kwargs):
    if method == "get":
        request = factory.get("/", data or {})
    else:
        request = getattr(factory, method)("/", data or {}, format="json")
    force_authenticate(request, user=user)
    return viewset_cls.as_view(actions)(request, **kwargs)


def _public(view_cls, code):
    return view_cls.as_view()(factory.get("/?schema=teste"), code=code)


@pytest.fixture
def evento(test_tenant):
    with schema_context(test_tenant.schema_name):
        inicio = timezone.now() - timedelta(days=2)
        ev = EventoAcademico.objects.create(
            titulo="Congresso Teste",
            data_inicio=inicio,
            data_fim=inicio + timedelta(days=1),
            carga_horaria=16,
        )
        presente = InscricaoEvento.objects.create(evento=ev, nome="Rita Lima", email="rita@x.org")
        ausente = InscricaoEvento.objects.create(evento=ev, nome="Caio", email="caio@x.org")
    return {"evento": ev, "presente": presente, "ausente": ausente}


@pytest.mark.django_db
class TestCertificadosEvento:
    def test_presenca_emissao_email_e_pdf(self, test_tenant, board_user, evento):
        ev, presente = evento["evento"], evento["presente"]
        with schema_context(test_tenant.schema_name):
            resp = _call(
                EventoAcademicoViewSet,
                {"post": "presencas"},
                board_user,
                "post",
                {"inscricoes": [str(presente.id)], "presente": True},
                pk=str(ev.id),
            )
            assert resp.data["alteradas"] == 1

            resp = _call(EventoAcademicoViewSet, {"post": "emitir_certificados"}, board_user, "post", {}, pk=str(ev.id))
            assert resp.status_code == 200, resp.data
            assert resp.data == {"emitidos": 1, "emails_enviados": 1, "inscritos_sem_presenca": 1}
            presente.refresh_from_db()
            assert presente.certificado_codigo and presente.certificado_emitido_em
            assert len(mail.outbox) == 1 and mail.outbox[0].to == ["rita@x.org"]
            assert presente.certificado_codigo in mail.outbox[0].body
            assert "schema=teste" in mail.outbox[0].body

            # Reemitir não duplica
            resp = _call(EventoAcademicoViewSet, {"post": "emitir_certificados"}, board_user, "post", {}, pk=str(ev.id))
            assert resp.data["emitidos"] == 0

            resp = _call(InscricaoEventoViewSet, {"get": "certificado"}, board_user, "get", pk=str(presente.id))
            assert resp.status_code == 200
            assert resp["Content-Type"] == "application/pdf"
            assert resp.content.startswith(b"%PDF")

    def test_inscrever_associado_preenche_dados_e_bloqueia_duplicado(self, test_tenant, board_user, member, evento):
        _, membro = member
        ev = evento["evento"]
        with schema_context(test_tenant.schema_name):
            payload = {"evento": str(ev.id), "membro": str(membro.id)}
            resp = _call(InscricaoEventoViewSet, {"post": "create"}, board_user, "post", payload)
            assert resp.status_code == 201, resp.data
            assert resp.data["nome"] == "Ana Maria Silva" and resp.data["email"] == "ana@teste.org"
            resp = _call(InscricaoEventoViewSet, {"post": "create"}, board_user, "post", payload)
            assert resp.status_code == 400
            resp = _call(InscricaoEventoViewSet, {"post": "create"}, board_user, "post", {"evento": str(ev.id)})
            assert resp.status_code == 400

    def test_certificado_desativado(self, test_tenant, board_user, evento):
        ev = evento["evento"]
        with schema_context(test_tenant.schema_name):
            EventoAcademico.objects.filter(pk=ev.pk).update(certificado_habilitado=False)
            resp = _call(EventoAcademicoViewSet, {"post": "emitir_certificados"}, board_user, "post", {}, pk=str(ev.id))
            assert resp.status_code == 400


@pytest.mark.django_db
class TestVerificacaoPublica:
    def test_evento(self, test_tenant, evento):
        with schema_context(test_tenant.schema_name):
            InscricaoEvento.objects.filter(pk=evento["presente"].pk).update(
                presente=True, certificado_codigo="ABC123DEF0", certificado_emitido_em=timezone.now()
            )
        resp = _public(CertificadoVerificacaoView, "abc123def0")
        assert resp.status_code == 200
        assert resp.data["kind"] == "evento"
        assert resp.data["participant_name"] == "Rita Lima"
        assert resp.data["workload_hours"] == 16
        resp = _public(CertificadoPdfView, "ABC123DEF0")
        assert resp.status_code == 200 and resp.content.startswith(b"%PDF")

    def test_curso(self, test_tenant, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            course = Course.objects.create(title="Ética", status=Course.PUBLISHED, certificate_enabled=True)
            CourseEnrollment.objects.create(
                course=course,
                membro=membro,
                status=CourseEnrollment.COMPLETED,
                completed_at=timezone.now(),
                certificate_code="FFEE001122",
            )
        resp = _public(CertificadoVerificacaoView, "FFEE001122")
        assert resp.data["kind"] == "curso" and resp.data["title"] == "Ética"
        assert _public(CertificadoPdfView, "FFEE001122").status_code == 200

    def test_codigo_inexistente(self, test_tenant):
        assert _public(CertificadoVerificacaoView, "NAOEXISTE").status_code == 404


@pytest.mark.django_db
class TestEmails:
    def test_convite_de_formulario_envia_email(self, test_tenant, board_user, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            f = Formulario.objects.create(titulo="Consulta", status=Formulario.PUBLICADO, created_by=board_user)
            s = Secao.objects.create(formulario=f, titulo="G")
            Pergunta.objects.create(secao=s, texto="Q", tipo=Pergunta.TEXTO_CURTO)
            resp = _call(FormularioViewSet, {"post": "convites"}, board_user, "post", {"membros": [str(membro.id)]}, pk=str(f.id))
            assert resp.status_code == 201
            assert resp.data["emails_enviados"] == 1
            token = Resposta.objects.get(formulario=f, membro=membro).token
            assert mail.outbox[0].to == ["ana@teste.org"]
            assert f"/site/formularios/convite/{token}?schema=teste" in mail.outbox[0].body

            resp = _call(FormularioViewSet, {"post": "convites"}, board_user, "post", {"reenviar_pendentes": True}, pk=str(f.id))
            assert resp.data["emails_enviados"] == 1
            assert len(mail.outbox) == 2

    def test_convite_em_rascunho_nao_envia(self, test_tenant, board_user, member):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            f = Formulario.objects.create(titulo="Rascunho", created_by=board_user)
            resp = _call(FormularioViewSet, {"post": "convites"}, board_user, "post", {"membros": [str(membro.id)]}, pk=str(f.id))
            assert resp.data["criados"] == 1 and resp.data["emails_enviados"] == 0
            assert not mail.outbox

    def test_matricula_envia_email_apos_commit(self, test_tenant, member, django_capture_on_commit_callbacks):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            course = Course.objects.create(title="Bioestatística", status=Course.PUBLISHED)
            with django_capture_on_commit_callbacks(execute=True):
                _, reason = enroll_membro(course, membro)
            assert reason == "created"
            assert len(mail.outbox) == 1
            assert "Bioestatística" in mail.outbox[0].subject
            with django_capture_on_commit_callbacks(execute=True):
                _, reason = enroll_membro(course, membro)
            assert reason == "already_enrolled" and len(mail.outbox) == 1


def test_erros_em_portugues_mesmo_com_navegador_em_ingles():
    from django.test import RequestFactory
    from django.utils import translation

    request = RequestFactory().get("/", HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9")
    idioma = translation.get_language_from_request(request)
    assert idioma == "pt-br"
    with translation.override(idioma):
        from rest_framework import serializers

        class S(serializers.Serializer):
            nome = serializers.CharField()

        s = S(data={})
        s.is_valid()
        assert "obrigatório" in str(s.errors["nome"][0])
