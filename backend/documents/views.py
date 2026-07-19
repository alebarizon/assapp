from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from accounts.models import User
from mandatos.permissions import IsBoardOrAdmin
from membros.services import resolver_membro_do_user

from .models import Document, DocumentAudience
from .serializers import DocumentSerializer


def _membro_do_user(user):
    return resolver_membro_do_user(user, auto_link=True)


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Document.objects.select_related("membro", "uploaded_by").all()
        audience = self.request.query_params.get("audience")
        membro_id = self.request.query_params.get("membro")
        if audience:
            qs = qs.filter(audience=audience)
        if membro_id:
            qs = qs.filter(membro_id=membro_id)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        doc = self.get_object()
        return FileResponse(doc.file.open("rb"), as_attachment=True, filename=doc.file.name.split("/")[-1])


class MeusDocumentosView(APIView):
    """
    Documentos visíveis ao usuário autenticado:
    - gerais
    - diretoria (se board/admin)
    - docs do próprio Membro (match por e-mail)
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request):
        user = request.user
        membro = _membro_do_user(user)
        qs = Document.objects.select_related("membro", "uploaded_by").filter(
            audience=DocumentAudience.GERAL
        )
        if user.role in (User.ASSOCIATION_ADMIN, User.BOARD_MEMBER, User.SUPERADMIN):
            qs = Document.objects.select_related("membro", "uploaded_by").filter(
                audience__in=[DocumentAudience.GERAL, DocumentAudience.DIRETORIA]
            )
            if membro:
                qs = qs | Document.objects.filter(
                    audience=DocumentAudience.MEMBRO, membro=membro
                )
        elif membro:
            qs = qs | Document.objects.filter(
                audience=DocumentAudience.MEMBRO, membro=membro
            )

        qs = qs.distinct().order_by("-created_at")
        serializer = DocumentSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def get_download(self, request, pk):
        # unused — download via nested route below
        pass


class MeuDocumentoDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        membro = _membro_do_user(user)
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response({"detail": "Não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        allowed = False
        if doc.audience == DocumentAudience.GERAL:
            allowed = True
        elif doc.audience == DocumentAudience.DIRETORIA and user.role in (
            User.ASSOCIATION_ADMIN,
            User.BOARD_MEMBER,
            User.SUPERADMIN,
        ):
            allowed = True
        elif (
            doc.audience == DocumentAudience.MEMBRO
            and membro
            and doc.membro_id == membro.id
        ):
            allowed = True

        if not allowed:
            return Response({"detail": "Sem permissão."}, status=status.HTTP_403_FORBIDDEN)

        return FileResponse(
            doc.file.open("rb"),
            as_attachment=True,
            filename=doc.file.name.split("/")[-1],
        )
