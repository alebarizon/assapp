"""Testes do CFP completo: submissão pelo autor, parecer duplo-cego por critérios, decisão e certificados."""
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from core.certificados_views import CertificadoPdfView, CertificadoVerificacaoView
from eventos.models import CallForPapers, CertificadoPapel, EventoAcademico, Parecer, SubmissaoTrabalho
from eventos.views import (
    EventoAcademicoViewSet,
    MeuParecerViewSet,
    MinhasChamadasView,
    MinhaSubmissaoViewSet,
    SubmissaoTrabalhoViewSet,
)

factory = APIRequestFactory()

CRITERIOS = [{"nome": "Relevância", "peso": 3}, {"nome": "Clareza", "peso": 1}]


def _req(method, user, data=None, fmt="json"):
    request = getattr(factory, method)("/", data or {}, format=fmt)
    force_authenticate(request, user=user)
    return request


def _cfp(anonimo=True, **kwargs):
    agora = timezone.now()
    evento = EventoAcademico.objects.create(
        titulo="Congresso",
        slug=f"congresso-{CallForPapers.objects.count()}",
        data_inicio=agora + timedelta(days=60),
        data_fim=agora + timedelta(days=62),
        status="cfp_aberto",
    )
    dados = dict(
        evento=evento,
        titulo="Chamada",
        instrucoes="Resumo",
        data_abertura=agora - timedelta(days=1),
        data_fechamento=agora + timedelta(days=10),
        areas_tematicas=["Ensino", "Pesquisa"],
        max_submissoes_por_autor=1,
        anonimo=anonimo,
        criterios=CRITERIOS,
    )
    dados.update(kwargs)
    return CallForPapers.objects.create(**dados)


def _parecerista(username="rev", email="rev@teste.org", tenant=None):
    return User.objects.create_user(
        username=username, email=email, password="x", role=User.REVIEWER, first_name="Rita", tenant=tenant
    )


def _submetida(user, cfp, **kwargs):
    dados = dict(
        cfp=cfp, autor=user, titulo="Trabalho", resumo="Resumo", area_tematica="Ensino", status="submetido",
        submetido_em=timezone.now(), coautores=[{"nome": "Carlos Coautor", "email": "carlos@x.org", "instituicao": ""}],
    )
    dados.update(kwargs)
    return SubmissaoTrabalho.objects.create(**dados)


@pytest.mark.django_db
class TestAutor:
    def test_rascunho_editar_e_submeter(self, test_tenant, member):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            cfp = _cfp()
            chamadas = MinhasChamadasView.as_view()(_req("get", user))
            assert [c["id"] for c in chamadas.data] == [str(cfp.id)]

            criar = MinhaSubmissaoViewSet.as_view({"post": "create"})(
                _req(
                    "post",
                    user,
                    {
                        "cfp": str(cfp.id),
                        "titulo": "Ensino híbrido",
                        "resumo": "Estudo de caso",
                        "area_tematica": "Ensino",
                        "palavras_chave": ["ensino", " híbrido "],
                        "coautores": [{"nome": " Bia  Lima ", "email": "BIA@X.ORG"}, {"nome": ""}],
                    },
                ),
            )
            assert criar.status_code == 201, criar.data
            assert criar.data["coautores"] == [{"nome": "Bia Lima", "email": "bia@x.org", "instituicao": ""}]
            sub_id = criar.data["id"]

            enviar = MinhaSubmissaoViewSet.as_view({"post": "submeter"})(_req("post", user), pk=sub_id)
            assert enviar.status_code == 200, enviar.data
            assert enviar.data["status"] == "submetido"
            assert SubmissaoTrabalho.objects.get(pk=sub_id).membro_id == membro.id

            editar = MinhaSubmissaoViewSet.as_view({"patch": "partial_update"})(
                _req("patch", user, {"titulo": "Outro"}), pk=sub_id
            )
            assert editar.status_code == 400

    def test_limite_por_autor_e_area(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            cfp = _cfp()
            _submetida(user, cfp)
            rascunho = SubmissaoTrabalho.objects.create(
                cfp=cfp, autor=user, titulo="Segundo", resumo="R", area_tematica="Ensino"
            )
            resp = MinhaSubmissaoViewSet.as_view({"post": "submeter"})(_req("post", user), pk=rascunho.pk)
            assert resp.status_code == 400
            assert "Limite" in resp.data["detail"]

            cfp.max_submissoes_por_autor = 5
            cfp.save()
            rascunho.area_tematica = "Outra"
            rascunho.save()
            resp = MinhaSubmissaoViewSet.as_view({"post": "submeter"})(_req("post", user), pk=rascunho.pk)
            assert "área" in resp.data["detail"]

    def test_multipart_com_arquivo_obrigatorio(self, test_tenant, member):
        from django.core.files.uploadedfile import SimpleUploadedFile

        user, _ = member
        with schema_context(test_tenant.schema_name):
            cfp = _cfp(exige_arquivo=True)
            sem_arquivo = MinhaSubmissaoViewSet.as_view({"post": "create"})(
                _req("post", user, {"cfp": str(cfp.id), "titulo": "T", "resumo": "R", "area_tematica": "Ensino"})
            )
            resp = MinhaSubmissaoViewSet.as_view({"post": "submeter"})(_req("post", user), pk=sem_arquivo.data["id"])
            assert resp.status_code == 400
            assert "arquivo" in resp.data["detail"].lower()

            resp = MinhaSubmissaoViewSet.as_view({"patch": "partial_update"})(
                _req(
                    "patch",
                    user,
                    {
                        "coautores": '[{"nome": "Bia", "email": "bia@x.org"}]',
                        "palavras_chave": '["ensino"]',
                        "arquivo": SimpleUploadedFile("trabalho.pdf", b"%PDF-1.4 teste", "application/pdf"),
                    },
                    fmt="multipart",
                ),
                pk=sem_arquivo.data["id"],
            )
            assert resp.status_code == 200, resp.data
            assert resp.data["tem_arquivo"] is True
            assert resp.data["coautores"][0]["nome"] == "Bia"
            ruim = MinhaSubmissaoViewSet.as_view({"patch": "partial_update"})(
                _req("patch", user, {"arquivo": SimpleUploadedFile("x.exe", b"MZ")}, fmt="multipart"),
                pk=sem_arquivo.data["id"],
            )
            assert "arquivo" in ruim.data
            resp = MinhaSubmissaoViewSet.as_view({"post": "submeter"})(_req("post", user), pk=sem_arquivo.data["id"])
            assert resp.status_code == 200, resp.data

    def test_chamada_fechada(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            cfp = _cfp(data_fechamento=timezone.now() - timedelta(hours=1))
            resp = MinhaSubmissaoViewSet.as_view({"post": "create"})(
                _req("post", user, {"cfp": str(cfp.id), "titulo": "T", "resumo": "R"})
            )
            assert resp.status_code == 400

    def test_nao_ve_trabalho_de_outro(self, test_tenant, member, board_user):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            sub = _submetida(board_user, _cfp())
            resp = MinhaSubmissaoViewSet.as_view({"get": "retrieve"})(_req("get", user), pk=sub.pk)
            assert resp.status_code == 404


@pytest.mark.django_db
class TestParecer:
    def _atribuir(self, board_user, sub, parecerista):
        return SubmissaoTrabalhoViewSet.as_view({"post": "atribuir_parecerista"})(
            _req("post", board_user, {"parecerista_id": str(parecerista.id), "prazo": "2026-12-01"}), pk=sub.pk
        )

    def test_conflito_de_interesse(self, test_tenant, member, board_user):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            sub = _submetida(user, _cfp())
            assert self._atribuir(board_user, sub, user).status_code == 400
            coautor = _parecerista("carlos", "carlos@x.org", test_tenant)
            resp = self._atribuir(board_user, sub, coautor)
            assert resp.status_code == 400
            assert "coautor" in resp.data["detail"]

    def test_duplo_cego_e_nota_ponderada(self, test_tenant, member, board_user):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            sub = _submetida(user, _cfp(anonimo=True))
            rev = _parecerista(tenant=test_tenant)
            assert self._atribuir(board_user, sub, rev).status_code == 201
            assert len(mail.outbox) == 1

            lista = MeuParecerViewSet.as_view({"get": "list"})(_req("get", rev))
            item = lista.data[0]
            assert item["submissao"]["autoria"] is None
            assert "autor" not in item["submissao"]
            assert item["criterios"] == CRITERIOS

            concluir = MeuParecerViewSet.as_view({"post": "concluir"})(
                _req("post", rev, {"recomendacao": "aceitar", "notas": {"Relevância": 5, "Clareza": 1}}),
                pk=item["id"],
            )
            assert concluir.status_code == 200, concluir.data
            # (5*3 + 1*1) / 4 = 4.00
            assert concluir.data["nota_ponderada"] == "4.00"
            sub.refresh_from_db()
            assert sub.status == "em_parecer"  # decisão é da comissão

    def test_identificado_quando_nao_anonimo(self, test_tenant, member, board_user):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            sub = _submetida(user, _cfp(anonimo=False))
            rev = _parecerista(tenant=test_tenant)
            self._atribuir(board_user, sub, rev)
            item = MeuParecerViewSet.as_view({"get": "list"})(_req("get", rev)).data[0]
            assert "Ana" in item["submissao"]["autoria"]

    def test_nota_faltando_rejeitada(self, test_tenant, member, board_user):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            sub = _submetida(user, _cfp())
            rev = _parecerista(tenant=test_tenant)
            self._atribuir(board_user, sub, rev)
            parecer = Parecer.objects.get()
            resp = MeuParecerViewSet.as_view({"post": "concluir"})(
                _req("post", rev, {"recomendacao": "aceitar", "notas": {"Relevância": 5}}), pk=parecer.pk
            )
            assert resp.status_code == 400

    def test_outro_usuario_nao_acessa_parecer(self, test_tenant, member, board_user):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            sub = _submetida(board_user, _cfp())
            rev = _parecerista(tenant=test_tenant)
            self._atribuir(board_user, sub, rev)
            resp = MeuParecerViewSet.as_view({"get": "retrieve"})(_req("get", user), pk=Parecer.objects.get().pk)
            assert resp.status_code == 404


@pytest.mark.django_db
class TestDecisaoECertificados:
    def test_fluxo_completo(self, test_tenant, member, board_user):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            cfp = _cfp()
            sub = _submetida(user, cfp)
            rev = _parecerista(tenant=test_tenant)
            parecer = Parecer.objects.create(submissao=sub, parecerista=rev)
            MeuParecerViewSet.as_view({"post": "concluir"})(
                _req(
                    "post",
                    rev,
                    {
                        "recomendacao": "aceitar",
                        "notas": {"Relevância": 4, "Clareza": 4},
                        "comentarios_autor": "Ótima discussão.",
                        "comentarios_internos": "Sigiloso",
                    },
                ),
                pk=parecer.pk,
            )
            mail.outbox.clear()

            decidir = SubmissaoTrabalhoViewSet.as_view({"post": "decidir"})(
                _req("post", board_user, {"decisao": "aceitar", "comentario": "Parabéns"}), pk=sub.pk
            )
            assert decidir.status_code == 200, decidir.data
            assert decidir.data["status"] == "aceito"
            assert decidir.data["nota_media"] == "4.00"

            carta = mail.outbox[0]
            assert set(carta.to) == {"ana@teste.org", "carlos@x.org"}
            assert "Ótima discussão." in carta.body
            assert "Sigiloso" not in carta.body
            assert "Rita" not in carta.body

            minha = MinhaSubmissaoViewSet.as_view({"get": "retrieve"})(_req("get", user), pk=sub.pk)
            assert minha.data["comentarios_pareceres"] == ["Ótima discussão."]

            # Parecer não muda depois da decisão
            tarde = MeuParecerViewSet.as_view({"post": "concluir"})(
                _req("post", rev, {"recomendacao": "rejeitar", "notas": {"Relevância": 1, "Clareza": 1}}),
                pk=parecer.pk,
            )
            assert tarde.status_code == 400

            emitir = EventoAcademicoViewSet.as_view({"post": "emitir_certificados_cientificos"})(
                _req("post", board_user, {"notificar": False}), pk=cfp.evento.pk
            )
            assert emitir.status_code == 200, emitir.data
            assert emitir.data == {"autores": 1, "pareceristas": 1, "emails_enviados": 0}
            again = EventoAcademicoViewSet.as_view({"post": "emitir_certificados_cientificos"})(
                _req("post", board_user, {"notificar": False}), pk=cfp.evento.pk
            )
            assert again.data["autores"] == 0 and again.data["pareceristas"] == 0

            cert = CertificadoPapel.objects.get(papel="autor")
            assert "Carlos Coautor" in cert.detalhe
            codigo = cert.codigo

        verif = CertificadoVerificacaoView.as_view()(factory.get("/?schema=teste"), code=codigo)
        assert verif.status_code == 200
        assert verif.data["action"] == "apresentou trabalho no evento"
        pdf = CertificadoPdfView.as_view()(factory.get("/?schema=teste"), code=codigo)
        assert pdf.status_code == 200
        assert pdf["Content-Type"] == "application/pdf"

    def test_lista_de_pareceristas(self, test_tenant, member, board_user):
        with schema_context(test_tenant.schema_name):
            _parecerista(tenant=test_tenant)
            resp = EventoAcademicoViewSet.as_view({"get": "pareceristas"})(_req("get", board_user))
            emails = {c["email"] for c in resp.data}
            assert {"rev@teste.org", "ana@teste.org", "diretoria@teste.org"} <= emails
