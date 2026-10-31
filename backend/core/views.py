"""Views auxiliares do core AssApp."""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django_tenants.utils import schema_context


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    try:
        with schema_context("public"):
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return JsonResponse({"status": "healthy", "message": "AssApp API is running"}, status=200)
    except Exception as e:
        return JsonResponse(
            {"status": "starting", "message": f"API starting (error: {str(e)})"},
            status=200,
        )


@csrf_exempt
@require_http_methods(["GET"])
def health_email(request):
    """Para monitor externo (UptimeRobot etc.): 503 se o SMTP caiu ou há e-mail parado na fila."""
    from datetime import timedelta

    from django.utils import timezone

    from core.emails import smtp_disponivel
    from core.models import EmailPendente

    with schema_context("public"):
        smtp = smtp_disponivel()
        pendentes = EmailPendente.objects.filter(status=EmailPendente.PENDENTE)
        atrasados = pendentes.filter(criado_em__lt=timezone.now() - timedelta(minutes=30)).count()
        desistencias = EmailPendente.objects.filter(
            status=EmailPendente.DESISTIU, criado_em__gte=timezone.now() - timedelta(days=1)
        ).count()
        total_pendentes = pendentes.count()
    ok = smtp is not False and atrasados == 0 and desistencias == 0
    return JsonResponse(
        {
            "status": "ok" if ok else "falha",
            "smtp": {True: "ok", False: "indisponivel", None: "desligado"}[smtp],
            "pendentes": total_pendentes,
            "pendentes_ha_mais_de_30min": atrasados,
            "desistencias_24h": desistencias,
        },
        status=200 if ok else 503,
    )


@csrf_exempt
@require_http_methods(["GET"])
def api_root(request):
    return JsonResponse(
        {
            "name": "AssApp API",
            "version": "0.1.0-mvp",
            "project": "PIPE FAPESP Jornada Tecnológica — Fase 1",
            "endpoints": {
                "health": "/health/",
                "auth": "/api/auth/",
                "mandatos": "/api/mandatos/",
                "memoria": "/api/memoria/",
                "eventos": "/api/eventos/",
                "membros": "/api/membros/",
                "finance": "/api/finance/",
                "documents": "/api/documents/",
                "ecommerce": "/api/ecommerce/",
                "website": "/api/website/",
            },
        },
        status=200,
    )
