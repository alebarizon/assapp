"""Testes do módulo Formulários."""
from datetime import timedelta

import pytest
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory, force_authenticate

from formularios.models import Formulario, ItemResposta, Pergunta, Resposta, Secao
from formularios.services import resumo
from formularios.views import (
    FormularioViewSet,
    MeusFormulariosViewSet,
    PublicConviteView,
    PublicFormularioView,
)

factory = APIRequestFactory()


def _call(viewset_cls, actions, user, method, data=None, **kwargs):
    if method == "get":
        request = factory.get("/", data or {})
    else:
        request = getattr(factory, method)("/", data or {}, format="json")
    if user is not None:
        force_authenticate(request, user=user)
    return viewset_cls.as_view(actions)(request, **kwargs)


def _public(view_cls, method, token, data=None):
    url = "/?schema=teste"
    request = factory.get(url) if method == "get" else factory.post(url, data or {}, format="json")
    return view_cls.as_view()(request, token=token)


@pytest.fixture
def formulario(test_tenant, board_user):
    with schema_context(test_tenant.schema_name):
        f = Formulario.objects.create(
            titulo="Avaliação do Congresso",
            status=Formulario.PUBLICADO,
            link_publico_ativo=True,
            created_by=board_user,
        )
        s = Secao.objects.create(formulario=f, titulo="Geral", ordem=0)
        nota = Pergunta.objects.create(secao=s, texto="Nota geral", tipo=Pergunta.ESCALA, obrigatoria=True, ordem=0)
        temas = Pergunta.objects.create(
            secao=s, texto="Temas", tipo=Pergunta.MULTIPLA_ESCOLHA, opcoes=["IA", "Ética", "Ensino"], ordem=1
        )
        comentario = Pergunta.objects.create(secao=s, texto="Comentários", tipo=Pergunta.TEXTO_LONGO, ordem=2)
    return {"form": f, "nota": nota, "temas": temas, "comentario": comentario}


@pytest.mark.django_db
class TestDiretoria:
    def test_member_cannot_manage(self, test_tenant, member):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            resp = _call(FormularioViewSet, {"post": "create"}, user, "post", {"titulo": "X"})
            assert resp.status_code == 403

    def test_create_with_nested_structure(self, test_tenant, board_user):
        payload = {
            "titulo": "Pesquisa",
            "secoes": [
                {
                    "titulo": "Perfil",
                    "perguntas": [
                        {"texto": "Área", "tipo": "escolha_unica", "opcoes": ["Exatas", "Humanas", " "]},
                        {"texto": "Idade", "tipo": "numero", "opcoes": ["ignorada"]},
                    ],
                }
            ],
        }
        with schema_context(test_tenant.schema_name):
            resp = _call(FormularioViewSet, {"post": "create"}, board_user, "post", payload)
            assert resp.status_code == 201, resp.data
            f = Formulario.objects.get(pk=resp.data["id"])
            perguntas = list(Pergunta.objects.filter(secao__formulario=f).order_by("ordem"))
            assert [p.texto for p in perguntas] == ["Área", "Idade"]
            assert perguntas[0].opcoes == ["Exatas", "Humanas"]
            assert perguntas[1].opcoes == []
            assert f.created_by == board_user

    def test_choice_requires_two_options(self, test_tenant, board_user):
        payload = {"titulo": "P", "secoes": [{"perguntas": [{"texto": "Q", "tipo": "escolha_unica", "opcoes": ["Só"]}]}]}
        with schema_context(test_tenant.schema_name):
            resp = _call(FormularioViewSet, {"post": "create"}, board_user, "post", payload)
            assert resp.status_code == 400

    def test_cannot_publish_without_questions(self, test_tenant, board_user):
        with schema_context(test_tenant.schema_name):
            f = Formulario.objects.create(titulo="Vazio")
            resp = _call(FormularioViewSet, {"patch": "partial_update"}, board_user, "patch", {"status": "publicado"}, pk=str(f.id))
            assert resp.status_code == 400
            assert "status" in resp.data

    def test_update_preserves_question_ids_and_removes_missing(self, test_tenant, board_user, formulario):
        f, nota = formulario["form"], formulario["nota"]
        with schema_context(test_tenant.schema_name):
            secao = f.secoes.first()
            payload = {
                "secoes": [
                    {
                        "id": str(secao.id),
                        "titulo": "Geral",
                        "perguntas": [
                            {"id": str(nota.id), "texto": "Nota do evento", "tipo": "escala", "escala_min": 0, "escala_max": 10},
                            {"texto": "Nova", "tipo": "texto_curto"},
                        ],
                    }
                ]
            }
            resp = _call(FormularioViewSet, {"patch": "partial_update"}, board_user, "patch", payload, pk=str(f.id))
            assert resp.status_code == 200, resp.data
            nota.refresh_from_db()
            assert nota.texto == "Nota do evento" and nota.escala_max == 10
            assert Pergunta.objects.filter(secao__formulario=f).count() == 2
            assert not Pergunta.objects.filter(pk=formulario["temas"].id).exists()

    def test_duplicate(self, test_tenant, board_user, formulario):
        with schema_context(test_tenant.schema_name):
            resp = _call(FormularioViewSet, {"post": "duplicar"}, board_user, "post", pk=str(formulario["form"].id))
            assert resp.status_code == 201
            copia = Formulario.objects.get(pk=resp.data["id"])
            assert copia.status == Formulario.RASCUNHO
            assert Pergunta.objects.filter(secao__formulario=copia).count() == 3

    def test_invites_are_idempotent(self, test_tenant, board_user, member, formulario):
        _, membro = member
        with schema_context(test_tenant.schema_name):
            url_kwargs = {"pk": str(formulario["form"].id)}
            resp = _call(FormularioViewSet, {"post": "convites"}, board_user, "post", {"membros": [str(membro.id)]}, **url_kwargs)
            assert resp.data == {"criados": 1, "existentes": 0, "emails_enviados": 1}
            resp = _call(FormularioViewSet, {"post": "convites"}, board_user, "post", {"todos_ativos": True}, **url_kwargs)
            assert resp.data == {"criados": 0, "existentes": 1, "emails_enviados": 0}
            resp = _call(FormularioViewSet, {"get": "convites"}, board_user, "get", **url_kwargs)
            assert resp.data[0]["status"] == "pendente"


@pytest.mark.django_db
class TestLinkPublico:
    def test_get_and_submit(self, test_tenant, formulario):
        f = formulario["form"]
        with schema_context("public"):
            resp = _public(PublicFormularioView, "get", f.public_token)
        assert resp.status_code == 200
        assert resp.data["associacao"] == "Associação Teste"
        assert len(resp.data["secoes"][0]["perguntas"]) == 3

        answers = {
            str(formulario["nota"].id): 5,
            str(formulario["temas"].id): ["IA", "Ensino"],
            str(formulario["comentario"].id): "Excelente evento,\nmuito bem organizado!",
        }
        resp = _public(PublicFormularioView, "post", f.public_token, {"nome": "João", "email": "joao@x.org", "answers": answers})
        assert resp.status_code == 201, resp.data
        with schema_context(test_tenant.schema_name):
            resposta = Resposta.objects.get(formulario=f)
            assert resposta.status == Resposta.ENVIADA and resposta.nome == "João"
            assert ItemResposta.objects.filter(resposta=resposta).count() == 3
            comentario = ItemResposta.objects.get(resposta=resposta, pergunta=formulario["comentario"])
            assert comentario.valor_texto == "Excelente evento,\nmuito bem organizado!"
            assert resumo(f)["perguntas"][2]["textos"] == ["Excelente evento,\nmuito bem organizado!"]

    def test_requires_identification_and_required_answers(self, test_tenant, formulario):
        f = formulario["form"]
        resp = _public(PublicFormularioView, "post", f.public_token, {"answers": {}})
        assert resp.status_code == 400 and "nome" in resp.data
        resp = _public(PublicFormularioView, "post", f.public_token, {"nome": "J", "email": "j@x.org", "answers": {}})
        assert resp.status_code == 400
        assert str(formulario["nota"].id) in resp.data["erros"]

    def test_rejects_invalid_values(self, test_tenant, formulario):
        f = formulario["form"]
        answers = {str(formulario["nota"].id): 9, str(formulario["temas"].id): ["Outro"]}
        resp = _public(PublicFormularioView, "post", f.public_token, {"nome": "J", "email": "j@x.org", "answers": answers})
        assert resp.status_code == 400
        assert set(resp.data["erros"]) == {str(formulario["nota"].id), str(formulario["temas"].id)}

    def test_closed_or_disabled_link(self, test_tenant, formulario):
        f = formulario["form"]
        with schema_context(test_tenant.schema_name):
            f.encerra_em = timezone.now() - timedelta(hours=1)
            f.save()
        resp = _public(PublicFormularioView, "post", f.public_token, {"nome": "J", "email": "j@x.org", "answers": {str(formulario["nota"].id): 3}})
        assert resp.status_code == 400
        with schema_context(test_tenant.schema_name):
            f.link_publico_ativo = False
            f.save()
        assert _public(PublicFormularioView, "get", f.public_token).status_code == 404


@pytest.mark.django_db
class TestPortalEConvite:
    def test_portal_draft_then_submit_once(self, test_tenant, member, formulario):
        user, membro = member
        f, nota = formulario["form"], formulario["nota"]
        with schema_context(test_tenant.schema_name):
            f.disponivel_no_portal = True
            f.save()
            resp = _call(MeusFormulariosViewSet, {"get": "list"}, user, "get")
            assert [i["id"] for i in resp.data] == [str(f.id)]

            resp = _call(MeusFormulariosViewSet, {"post": "salvar"}, user, "post", {"answers": {str(formulario["comentario"].id): "Ótimo"}}, pk=str(f.id))
            assert resp.data["situacao"] == "em_andamento"
            resp = _call(MeusFormulariosViewSet, {"get": "retrieve"}, user, "get", pk=str(f.id))
            assert resp.data["valores"] == {str(formulario["comentario"].id): "Ótimo"}

            resp = _call(MeusFormulariosViewSet, {"post": "enviar"}, user, "post", {"answers": {str(nota.id): "4"}}, pk=str(f.id))
            assert resp.status_code == 200, resp.data
            resposta = Resposta.objects.get(formulario=f, membro=membro)
            assert resposta.origem == Resposta.PORTAL and resposta.status == Resposta.ENVIADA

            resp = _call(MeusFormulariosViewSet, {"post": "enviar"}, user, "post", {"answers": {str(nota.id): "4"}}, pk=str(f.id))
            assert resp.status_code == 400

    def test_hidden_form_not_visible_without_invite(self, test_tenant, member, formulario):
        user, _ = member
        with schema_context(test_tenant.schema_name):
            resp = _call(MeusFormulariosViewSet, {"get": "retrieve"}, user, "get", pk=str(formulario["form"].id))
            assert resp.status_code == 404

    def test_invite_link_and_portal_share_the_same_response(self, test_tenant, member, formulario):
        user, membro = member
        f = formulario["form"]
        with schema_context(test_tenant.schema_name):
            convite = Resposta.objects.create(formulario=f, membro=membro, origem=Resposta.CONVITE, nome=membro.nome_completo)
            resp = _call(MeusFormulariosViewSet, {"get": "list"}, user, "get")
            assert resp.data[0]["minha_situacao"] == "pendente"

        resp = _public(PublicConviteView, "get", convite.token)
        assert resp.status_code == 200 and resp.data["nome"] == "Ana Maria Silva"
        resp = _public(PublicConviteView, "post", convite.token, {"answers": {str(formulario["nota"].id): 2}, "enviar": True})
        assert resp.status_code == 200, resp.data
        with schema_context(test_tenant.schema_name):
            convite.refresh_from_db()
            assert convite.status == Resposta.ENVIADA
            assert Resposta.objects.filter(formulario=f).count() == 1


@pytest.mark.django_db
class TestResultados:
    def test_summary_and_csv(self, test_tenant, board_user, formulario):
        f, nota, temas = formulario["form"], formulario["nota"], formulario["temas"]
        with schema_context(test_tenant.schema_name):
            for valor, escolhas in ((5, ["IA"]), (3, ["IA", "Ética"])):
                r = Resposta.objects.create(formulario=f, status=Resposta.ENVIADA, enviada_em=timezone.now(), nome="X")
                ItemResposta.objects.create(resposta=r, pergunta=nota, valor_texto=str(valor))
                ItemResposta.objects.create(resposta=r, pergunta=temas, valor_lista=escolhas)
            Resposta.objects.create(formulario=f, status=Resposta.EM_ANDAMENTO)

            dados = resumo(f)
            assert dados["total_respostas"] == 2
            por_texto = {p["texto"]: p for p in dados["perguntas"]}
            assert por_texto["Nota geral"]["media"] == 4.0
            assert {o["opcao"]: o["total"] for o in por_texto["Temas"]["opcoes"]} == {"IA": 2, "Ética": 1, "Ensino": 0}

            resp = _call(FormularioViewSet, {"get": "exportar"}, board_user, "get", pk=str(f.id))
            assert resp.status_code == 200
            linhas = resp.content.decode("utf-8-sig").strip().splitlines()
            assert len(linhas) == 3
            assert "IA, Ética" in linhas[2]
