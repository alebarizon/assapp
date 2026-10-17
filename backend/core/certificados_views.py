"""
Verificação pública de certificados (cursos e eventos) pelo código impresso no PDF.

GET /api/certificados/<code>/?schema=       dados do certificado
GET /api/certificados/<code>/pdf/?schema=   download do PDF
"""
from django.http import HttpResponse
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from tenants.resolvers import resolve_tenant_from_request


def _localizar(code: str):
    from courses.models import CourseEnrollment
    from eventos.models import InscricaoEvento

    code = code.strip().upper()
    enrollment = (
        CourseEnrollment.objects.filter(certificate_code=code, status=CourseEnrollment.COMPLETED)
        .select_related("course", "membro")
        .first()
    )
    if enrollment and enrollment.course.certificate_enabled:
        return "curso", enrollment
    inscricao = InscricaoEvento.objects.filter(certificado_codigo=code).select_related("evento").first()
    if inscricao:
        return "evento", inscricao
    raise NotFound("Certificado não encontrado.")


class CertificadoPublicBase(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "certificados_public"

    def _tenant(self, request):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            raise NotFound("Associação não encontrada. Informe ?schema=.")
        return tenant


class CertificadoVerificacaoView(CertificadoPublicBase):
    def get(self, request, code):
        tenant = self._tenant(request)
        with schema_context(tenant.schema_name):
            tipo, obj = _localizar(code)
            if tipo == "curso":
                data = obj.completed_at
                payload = {
                    "participant_name": obj.membro.nome_completo,
                    "title": obj.course.title,
                    "action": "concluiu o curso",
                    "workload_hours": obj.course.workload_hours,
                    "code": obj.certificate_code,
                }
            else:
                data = obj.certificado_emitido_em
                payload = {
                    "participant_name": obj.nome,
                    "title": obj.evento.titulo,
                    "action": "participou do evento",
                    "workload_hours": obj.evento.carga_horaria,
                    "code": obj.certificado_codigo,
                }
            payload.update(
                {
                    "valid": True,
                    "kind": tipo,
                    "issued_at": timezone.localtime(data).date().isoformat() if data else None,
                    "issuer": tenant.name,
                }
            )
            return Response(payload)


class CertificadoPdfView(CertificadoPublicBase):
    def get(self, request, code):
        tenant = self._tenant(request)
        with schema_context(tenant.schema_name):
            tipo, obj = _localizar(code)
            if tipo == "curso":
                from courses.services import build_enrollment_certificate

                pdf = build_enrollment_certificate(obj, tenant.name)
                slug = obj.course.slug
            else:
                from eventos.services import build_inscricao_certificate

                pdf = build_inscricao_certificate(obj, tenant.schema_name, tenant.name)
                slug = obj.evento.slug
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="certificado-{slug}.pdf"'
        return response
