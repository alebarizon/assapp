"""
API de governança.

Painel:  /api/governanca/assembleias/   CRUD + convocar, iniciar, encerrar, cancelar, presencas, quorum,
                                        gerar-ata, publicar-ata, ata-pdf
         /api/governanca/votacoes/      CRUD + abrir, encerrar, cancelar, participacao
Portal:  /api/governanca/minhas/        assembleias e votações do associado
         /api/governanca/minhas/votacoes/<id>/votar/
         /api/governanca/minhas/assembleias/<id>/presenca/
         /api/governanca/minhas/assembleias/<id>/ata-pdf/
"""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.emails import nome_associacao
from mandatos.permissions import IsBoardOrAdmin
from membros.models import Membro
from membros.services import resolver_membro_do_user

from .models import (
    Assembleia,
    AssembleiaStatus,
    Eleitor,
    FormaPresenca,
    Modalidade,
    PresencaAssembleia,
    Votacao,
    VotacaoStatus,
)
from .serializers import AssembleiaSerializer, OpcaoVotacaoSerializer, PresencaSerializer, VotacaoSerializer
from .services import (
    GovernancaError,
    abrir_votacao,
    build_ata_pdf,
    convocar,
    encerrar_votacao,
    gerar_ata,
    mudar_status,
    participacao,
    publicar_ata,
    quorum,
    recebendo_votos,
    registrar_presenca,
    votar,
)

UUID_LOOKUP = r"[0-9a-fA-F-]{36}"


def _executar(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except GovernancaError as exc:
        raise ValidationError({"detail": str(exc)})


def _pdf_ata(request, assembleia):
    pdf = build_ata_pdf(assembleia, nome_associacao(request))
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="ata-{assembleia.data_hora:%Y-%m-%d}.pdf"'
    return response


class AssembleiaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "governanca"
    serializer_class = AssembleiaSerializer
    pagination_class = None
    lookup_value_regex = UUID_LOOKUP

    def get_queryset(self):
        return Assembleia.objects.prefetch_related("votacoes").order_by("-data_hora")

    def perform_destroy(self, instance):
        if instance.status != AssembleiaStatus.RASCUNHO:
            raise ValidationError({"detail": "Só rascunhos podem ser excluídos; cancele a assembleia."})
        instance.delete()

    def _status(self, novo):
        assembleia = self.get_object()
        _executar(mudar_status, assembleia, novo)
        return Response(self.get_serializer(assembleia).data)

    @action(detail=True, methods=["post"])
    def convocar(self, request, pk=None):
        assembleia = self.get_object()
        enviados = _executar(convocar, assembleia, bool(request.data.get("notificar", True)))
        return Response({**self.get_serializer(assembleia).data, "emails_enviados": enviados})

    @action(detail=True, methods=["post"])
    def iniciar(self, request, pk=None):
        return self._status(AssembleiaStatus.EM_ANDAMENTO)

    @action(detail=True, methods=["post"])
    def encerrar(self, request, pk=None):
        return self._status(AssembleiaStatus.ENCERRADA)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        return self._status(AssembleiaStatus.CANCELADA)

    @action(detail=True, methods=["get", "post", "delete"])
    def presencas(self, request, pk=None):
        assembleia = self.get_object()
        if request.method == "POST":
            membro = get_object_or_404(Membro, pk=request.data.get("membro"))
            forma = request.data.get("forma") or FormaPresenca.PRESENCIAL
            _executar(registrar_presenca, assembleia, membro, forma, request.user)
        elif request.method == "DELETE":
            if assembleia.status not in (AssembleiaStatus.CONVOCADA, AssembleiaStatus.EM_ANDAMENTO):
                raise ValidationError({"detail": "A lista de presença está fechada."})
            assembleia.presencas.filter(membro_id=request.query_params.get("membro")).delete()
        qs = assembleia.presencas.select_related("membro")
        return Response({"presencas": PresencaSerializer(qs, many=True).data, "quorum": quorum(assembleia)})

    @action(detail=True, methods=["post"], url_path="gerar-ata")
    def gerar_ata(self, request, pk=None):
        assembleia = self.get_object()
        if assembleia.ata_publicada_em:
            raise ValidationError({"detail": "A ata já foi publicada."})
        assembleia.ata = gerar_ata(assembleia)
        assembleia.save(update_fields=["ata", "updated_at"])
        return Response(self.get_serializer(assembleia).data)

    @action(detail=True, methods=["post"], url_path="publicar-ata")
    def publicar_ata(self, request, pk=None):
        assembleia = _executar(publicar_ata, self.get_object(), request.user)
        return Response(self.get_serializer(assembleia).data)

    @action(detail=True, methods=["get"], url_path="ata-pdf")
    def ata_pdf(self, request, pk=None):
        return _pdf_ata(request, self.get_object())


class VotacaoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    modulo = "governanca"
    serializer_class = VotacaoSerializer
    pagination_class = None
    lookup_value_regex = UUID_LOOKUP

    def get_queryset(self):
        qs = Votacao.objects.select_related("assembleia").prefetch_related("opcoes")
        assembleia = self.request.query_params.get("assembleia")
        if assembleia:
            qs = qs.filter(assembleia_id=assembleia)
        return qs

    def perform_destroy(self, instance):
        if instance.status != VotacaoStatus.RASCUNHO:
            raise ValidationError({"detail": "Só rascunhos podem ser excluídos; cancele a votação."})
        instance.delete()

    @action(detail=True, methods=["post"])
    def abrir(self, request, pk=None):
        votacao = self.get_object()
        eleitores = _executar(abrir_votacao, votacao)
        return Response({**self.get_serializer(self.get_object()).data, "eleitores": eleitores})

    @action(detail=True, methods=["post"])
    def encerrar(self, request, pk=None):
        votacao = self.get_object()
        _executar(encerrar_votacao, votacao, request.user)
        return Response(self.get_serializer(votacao).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        votacao = self.get_object()
        if votacao.status not in (VotacaoStatus.RASCUNHO, VotacaoStatus.ABERTA):
            raise ValidationError({"detail": "Esta votação não pode ser cancelada."})
        votacao.status = VotacaoStatus.CANCELADA
        votacao.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(votacao).data)

    @action(detail=True, methods=["get"])
    def participacao(self, request, pk=None):
        votacao = self.get_object()
        eleitores = votacao.eleitores.select_related("membro").order_by("membro__nome_completo")
        return Response(
            {
                **participacao(votacao),
                "eleitores_lista": [
                    {"membro": str(e.membro_id), "nome": e.membro.nome_completo, "votou": bool(e.votou_em)}
                    for e in eleitores
                ],
            }
        )


def _membro(request) -> Membro:
    membro = resolver_membro_do_user(request.user, auto_link=True)
    if not membro:
        raise PermissionDenied("Disponível apenas para associados.")
    return membro


class MinhaGovernancaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membro = _membro(request)
        presentes = set(
            PresencaAssembleia.objects.filter(membro=membro).values_list("assembleia_id", flat=True)
        )
        assembleias = Assembleia.objects.exclude(status=AssembleiaStatus.RASCUNHO).order_by("-data_hora")[:20]
        eleitores = {
            e.votacao_id: e
            for e in Eleitor.objects.filter(membro=membro).select_related("votacao__assembleia")
        }
        votacoes = []
        for votacao_id, eleitor in eleitores.items():
            v = eleitor.votacao
            if v.status in (VotacaoStatus.RASCUNHO, VotacaoStatus.CANCELADA):
                continue
            dados = VotacaoSerializer(v, context={"request": request}).data
            dados["opcoes"] = OpcaoVotacaoSerializer(v.opcoes.all(), many=True).data
            dados.update({"ja_votou": bool(eleitor.votou_em), "pode_votar": recebendo_votos(v) and not eleitor.votou_em})
            votacoes.append(dados)
        votacoes.sort(key=lambda d: (not d["pode_votar"], d["created_at"]), reverse=False)
        return Response(
            {
                "assembleias": [
                    {
                        **AssembleiaSerializer(a, context={"request": request}).data,
                        "presente": a.id in presentes,
                        "pode_marcar_presenca": a.status == AssembleiaStatus.EM_ANDAMENTO
                        and a.modalidade != Modalidade.PRESENCIAL
                        and a.id not in presentes,
                        "ata": a.ata if a.ata_publicada_em else "",
                    }
                    for a in assembleias
                ],
                "votacoes": votacoes,
            }
        )


class VotarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        votacao = get_object_or_404(Votacao, pk=pk)
        opcoes = request.data.get("opcoes") or []
        if not isinstance(opcoes, list):
            raise ValidationError({"opcoes": "Informe uma lista."})
        comprovante = _executar(votar, votacao, _membro(request), opcoes)
        return Response({"comprovante": comprovante}, status=status.HTTP_201_CREATED)


class MinhaPresencaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        assembleia = get_object_or_404(Assembleia, pk=pk)
        if assembleia.status != AssembleiaStatus.EM_ANDAMENTO or assembleia.modalidade == Modalidade.PRESENCIAL:
            raise ValidationError({"detail": "A presença online não está aberta para esta assembleia."})
        _executar(registrar_presenca, assembleia, _membro(request), FormaPresenca.ONLINE, request.user)
        return Response({"presente": True})


class MinhaAtaPdfView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _membro(request)
        assembleia = get_object_or_404(Assembleia, pk=pk, ata_publicada_em__isnull=False)
        return _pdf_ata(request, assembleia)
