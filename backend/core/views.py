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
            },
        },
        status=200,
    )
