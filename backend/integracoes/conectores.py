"""
Catálogo de integrações exibido na página Integrações.

Cada conector é declarado aqui (sem tabela). `situacao` é calculada por associação:
"ativo", "configurado" (credencial salva, desligado), "disponivel" ou "em_breve".
`acao` diz ao painel onde configurar: "pagamento" (modal de pagamento online),
"webhooks" (seção de webhooks de saída) ou None.
"""
from dataclasses import dataclass
from typing import Callable

CATEGORIAS = [
    ("pagamentos", "Pagamentos"),
    ("plataforma", "Automação e plataforma aberta"),
    ("comunicacao", "Comunicação"),
    ("cientifico", "Científico"),
    ("fiscal", "Fiscal e contábil"),
    ("eventos", "Eventos e agenda"),
    ("documentos", "Assinatura de documentos"),
]
_CATEGORIA_LABEL = dict(CATEGORIAS)


@dataclass(frozen=True)
class Conector:
    slug: str
    nome: str
    categoria: str
    descricao: str
    acao: str | None = None
    situacao: Callable[[], str] | None = None


def _gateway(provedor: str) -> Callable[[], str]:
    def situacao():
        from payments.models import ConfiguracaoPagamento

        config = ConfiguracaoPagamento.atual()
        if config.provedor != provedor:
            return "disponivel"
        if config.ativo:
            return "ativo"
        return "configurado" if config.api_key_cifrada else "disponivel"

    return situacao


def _webhooks() -> str:
    from .models import WebhookSaida

    return "ativo" if WebhookSaida.objects.filter(ativo=True).exists() else "disponivel"


CONECTORES = [
    Conector(
        "asaas", "Asaas", "pagamentos",
        "Pix, boleto e cartão nas anuidades e na loja, com baixa automática.",
        acao="pagamento", situacao=_gateway("asaas"),
    ),
    Conector(
        "pagbank", "PagBank", "pagamentos",
        "Pix e checkout do PagBank (PagSeguro) para quem já tem conta.",
        acao="pagamento", situacao=_gateway("pagbank"),
    ),
    Conector(
        "mercadopago", "Mercado Pago", "pagamentos",
        "Pix, cartão parcelado e boleto pelo Mercado Pago.",
        acao="pagamento", situacao=_gateway("mercadopago"),
    ),
    Conector("efi", "Efí (Pix Automático)", "pagamentos", "Anuidade recorrente por Pix Automático."),
    Conector(
        "webhooks", "Webhooks de saída", "plataforma",
        "Avise outros sistemas quando um associado se cadastra, paga a anuidade ou se inscreve em evento.",
        acao="webhooks", situacao=_webhooks,
    ),
    Conector(
        "automacao", "Make, Zapier, n8n e Pluga", "plataforma",
        "Conecte planilhas, CRMs e centenas de apps usando um webhook de saída como gatilho.",
        acao="webhooks", situacao=lambda: "disponivel",
    ),
    Conector("whatsapp", "WhatsApp", "comunicacao", "Lembretes de anuidade e avisos pela API oficial do WhatsApp."),
    Conector("rdstation", "RD Station e Mailchimp", "comunicacao", "Sincronizar associados e inscritos com listas de marketing."),
    Conector("orcid", "ORCID", "cientifico", "Login com ORCID e dados do perfil do pesquisador no cadastro."),
    Conector("ojs", "OJS (revista)", "cientifico", "Acesso de associado em dia à revista da associação."),
    Conector("crossref", "Crossref (DOI)", "cientifico", "DOI para os trabalhos dos anais."),
    Conector("nfse", "Nota fiscal de serviço", "fiscal", "Emissão de NFS-e para inscrições e cursos."),
    Conector("contabil", "Omie e Conta Azul", "fiscal", "Contas a receber sincronizadas com o sistema contábil."),
    Conector("agenda", "Google Agenda", "eventos", "Eventos e assembleias na agenda do associado."),
    Conector("videoconferencia", "Zoom e Google Meet", "eventos", "Sala criada automaticamente para eventos e assembleias online."),
    Conector("assinatura", "ZapSign e Clicksign", "documentos", "Assinatura eletrônica de atas e termos de posse."),
]


def catalogo() -> list[dict]:
    itens = []
    for c in CONECTORES:
        try:
            situacao = c.situacao() if c.situacao else "em_breve"
        except Exception:
            situacao = "disponivel"
        itens.append(
            {
                "slug": c.slug,
                "nome": c.nome,
                "categoria": c.categoria,
                "categoria_label": _CATEGORIA_LABEL[c.categoria],
                "descricao": c.descricao,
                "situacao": situacao,
                "acao": c.acao,
            }
        )
    return itens
