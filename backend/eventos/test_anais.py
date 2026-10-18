"""Testes dos anais por trabalho: publicação, página pública, citação e PDF."""
from datetime import date, timedelta

import pytest
from django.core.files.base import ContentFile
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from eventos.anais import citacoes, nome_abnt, nome_apa
from eventos.models import CallForPapers, EventoAcademico, SubmissaoTrabalho, TrabalhoPublicado
from eventos.views import (
    EventoAcademicoViewSet,
    PublicAnaisView,
    PublicTrabalhoPdfView,
    PublicTrabalhoView,
    TrabalhoPublicadoViewSet,
)

factory = APIRequestFactory()


def _req(method, user, data=None, fmt="json"):
    request = getattr(factory, method)("/", data or {}, format=fmt)
    force_authenticate(request, user=user)
    return request


def _evento_com_aceitos(user, publicado_site=True):
    user.first_name, user.last_name = "Ana", "Silva"
    user.save()
    agora = timezone.now()
    evento = EventoAcademico.objects.create(
        titulo="Congresso de Ensino",
        slug="congresso-ensino",
        data_inicio=agora - timedelta(days=5),
        data_fim=agora - timedelta(days=3),
        local="Recife",
        status="em_avaliacao",
        publicado_site=publicado_site,
    )
    cfp = CallForPapers.objects.create(
        evento=evento, titulo="Chamada", instrucoes="", data_abertura=agora - timedelta(days=60),
        data_fechamento=agora - timedelta(days=30), areas_tematicas=["Ensino"],
    )
    comum = dict(cfp=cfp, autor=user, resumo="Resumo do estudo.", area_tematica="Ensino")
    a = SubmissaoTrabalho.objects.create(
        titulo="Ensino híbrido na pós", status="aceito", palavras_chave=["ensino"],
        coautores=[{"nome": "Carlos Souza Filho", "email": "c@x.org", "instituicao": "UFPE"}], **comum
    )
    b = SubmissaoTrabalho.objects.create(titulo="Ensino híbrido na pós", status="aceito_com_revisoes", **comum)
    SubmissaoTrabalho.objects.create(titulo="Rejeitado", status="rejeitado", **comum)
    return evento, a, b


def _gerar(board_user, evento):
    return EventoAcademicoViewSet.as_view({"post": "gerar_anais"})(_req("post", board_user, {}), pk=evento.pk)


@pytest.mark.django_db
class TestPublicacao:
    def test_um_registro_por_aceito_com_slug_estavel(self, test_tenant, member, board_user):
        user, membro = member
        with schema_context(test_tenant.schema_name):
            membro.instituicao = "UFRJ"
            membro.orcid = "0000-0002-1825-0097"
            membro.save()
            evento, a, b = _evento_com_aceitos(user)
            a.membro = membro
            a.save()
            a.arquivo.save("final.pdf", ContentFile(b"%PDF-1.4 final"), save=True)

            resp = _gerar(board_user, evento)
            assert resp.status_code == 200, resp.data
            slugs = sorted(t["slug"] for t in resp.data["trabalhos"])
            assert slugs == ["ensino-hibrido-na-pos", "ensino-hibrido-na-pos-2"]
            assert resp.data["cidade"] == "Recife"

            pub_a = TrabalhoPublicado.objects.get(submissao=a)
            assert pub_a.autores[0] == {"nome": membro.nome_completo, "instituicao": "UFRJ", "orcid": "0000-0002-1825-0097"}
            assert pub_a.autores[1]["nome"] == "Carlos Souza Filho"
            assert pub_a.arquivo.name.endswith(".pdf")

            pub_a.doi = "10.1234/x.1"
            pub_a.save()
            slug_a = pub_a.slug
            a.titulo = "Título revisado"
            a.save()
            b.status = "rejeitado"
            b.save()
            _gerar(board_user, evento)

            pub_a.refresh_from_db()
            assert pub_a.titulo == "Título revisado"
            assert pub_a.slug == slug_a and pub_a.doi == "10.1234/x.1"
            assert TrabalhoPublicado.objects.count() == 1

    def test_editar_anais_e_trabalho(self, test_tenant, member, board_user):
        from django.core.files.uploadedfile import SimpleUploadedFile

        user, _ = member
        with schema_context(test_tenant.schema_name):
            evento, _, _ = _evento_com_aceitos(user)
            _gerar(board_user, evento)
            resp = EventoAcademicoViewSet.as_view({"patch": "editar_anais"})(
                _req("patch", board_user, {"isbn": "978-65-00-00000-0", "licenca": "cc-by-nc"}), pk=evento.pk
            )
            assert resp.status_code == 200, resp.data
            assert resp.data["licenca_display"] == "CC BY-NC 4.0"

            trabalho = TrabalhoPublicado.objects.first()
            view = TrabalhoPublicadoViewSet.as_view({"patch": "partial_update"})
            ruim = view(_req("patch", board_user, {"doi": "abc"}), pk=trabalho.pk)
            assert ruim.status_code == 400
            ok = view(
                _req(
                    "patch",
                    board_user,
                    {"doi": "https://doi.org/10.5555/anais.1", "arquivo": SimpleUploadedFile("v2.pdf", b"%PDF")},
                    fmt="multipart",
                ),
                pk=trabalho.pk,
            )
            assert ok.status_code == 200, ok.data
            assert ok.data["doi"] == "10.5555/anais.1"
            assert ok.data["tem_arquivo"] is True
            assert "/site/eventos/congresso-ensino/anais/" in ok.data["url_publica"]


@pytest.mark.django_db
class TestPaginaPublica:
    def test_sumario_detalhe_e_pdf(self, test_tenant, member, board_user):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            evento, _, _ = _evento_com_aceitos(user)
            _gerar(board_user, evento)
            slug = TrabalhoPublicado.objects.order_by("ordem").first().slug

        sumario = PublicAnaisView.as_view()(factory.get("/?schema=teste"), slug="congresso-ensino")
        assert sumario.status_code == 200
        assert len(sumario.data["trabalhos"]) == 2
        assert sumario.data["licenca_url"].startswith("https://creativecommons.org/")

        detalhe = PublicTrabalhoView.as_view()(factory.get("/?schema=teste"), slug="congresso-ensino", trabalho_slug=slug)
        assert detalhe.status_code == 200
        assert detalhe.data["citacoes"]["abnt"].startswith("SILVA, Ana")
        assert "@inproceedings{" in detalhe.data["citacoes"]["bibtex"]
        assert "schema=teste" in detalhe.data["url"]

        pdf = PublicTrabalhoPdfView.as_view()(factory.get("/?schema=teste"), slug="congresso-ensino", trabalho_slug=slug)
        assert pdf.status_code == 200
        assert pdf.content.startswith(b"%PDF")

        nada = PublicTrabalhoView.as_view()(factory.get("/?schema=teste"), slug="congresso-ensino", trabalho_slug="x")
        assert nada.status_code == 404

    def test_evento_nao_publicado_no_site(self, test_tenant, member, board_user):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            evento, _, _ = _evento_com_aceitos(user, publicado_site=False)
            _gerar(board_user, evento)
        resp = PublicAnaisView.as_view()(factory.get("/?schema=teste"), slug="congresso-ensino")
        assert resp.status_code == 404


class TestCitacao:
    def test_nomes(self):
        assert nome_abnt("Ana Maria Silva") == "SILVA, Ana Maria"
        assert nome_abnt("Carlos Souza Filho") == "SOUZA FILHO, Carlos"
        assert nome_apa("Ana Maria da Silva") == "Silva, A. M."
        assert nome_abnt("Platão") == "PLATÃO"

    @pytest.mark.django_db
    def test_formatos(self, test_tenant, member, board_user):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            evento, a, _ = _evento_com_aceitos(user)
            _gerar(board_user, evento)
            t = TrabalhoPublicado.objects.get(submissao=a)
            t.doi = "10.1234/abc"
            t.anais.issn = "1234-5678"
            c = citacoes(t, "Sociedade X", "https://site/x", hoje=date(2026, 10, 18))
        assert "SILVA, Ana; SOUZA FILHO, Carlos. Ensino híbrido na pós." in c["abnt"]
        assert "In: CONGRESSO DE ENSINO" in c["abnt"]
        assert "Recife: Sociedade X" in c["abnt"]
        assert "ISSN 1234-5678. DOI: 10.1234/abc." in c["abnt"]
        assert c["abnt"].endswith("Acesso em: 18 out. 2026.")
        assert c["apa"].startswith("Silva, A., & Souza Filho, C. (")
        assert c["apa"].endswith("https://doi.org/10.1234/abc")
        assert "author = {Silva, Ana and Souza Filho, Carlos}" in c["bibtex"]
