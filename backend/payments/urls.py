from django.urls import path

from .views import (
    CobrarAnuidadeView,
    CobrarPedidoView,
    ConfiguracaoPagamentoView,
    DisponibilidadeView,
    MinhaCobrancaView,
    SimularPagamentoView,
    TestarConfiguracaoView,
    WebhookAsaasView,
)

app_name = "payments"

urlpatterns = [
    path("configuracao/", ConfiguracaoPagamentoView.as_view(), name="configuracao"),
    path("configuracao/testar/", TestarConfiguracaoView.as_view(), name="configuracao-testar"),
    path("disponibilidade/", DisponibilidadeView.as_view(), name="disponibilidade"),
    path("anuidades/<uuid:anuidade_id>/cobrar/", CobrarAnuidadeView.as_view(), name="cobrar-anuidade"),
    path("pedidos/<uuid:pedido_id>/cobrar/", CobrarPedidoView.as_view(), name="cobrar-pedido"),
    path("cobrancas/<uuid:cobranca_id>/", MinhaCobrancaView.as_view(), name="cobranca"),
    path(
        "cobrancas/<uuid:cobranca_id>/simular-pagamento/",
        SimularPagamentoView.as_view(),
        name="simular-pagamento",
    ),
    path("webhook/asaas/", WebhookAsaasView.as_view(), name="webhook-asaas"),
]
