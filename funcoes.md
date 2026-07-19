# Funcionalidades do WellSaaS

> Relato resumido de cada funcionalidade da plataforma. WellSaaS é um SaaS multi-tenant voltado para empreendedores da área de saúde/nutrição (coaches, nutricionistas, clínicas), com três perfis de usuário: **superadmin**, **empreendedor (tenant)** e **cliente final**.

> **AssApp (2026-07-15):** multi-tenant, JWT, UI WellSaaS, signup simulado, Finance/Documents, MandatoDetail+H2, ponte User↔Membro e portal do associado. Stripe adiado. Ver [`CHANGELOG_2026_07_15.md`](docs/changelog/CHANGELOG_2026_07_15.md).

---

## Autenticação e Acesso

### Login
Sistema de autenticação JWT com suporte a múltiplos perfis (superadmin, empreendedor e cliente). O login busca o usuário primeiro no schema `sistema` (superadmin) e depois nos schemas dos tenants, permitindo acesso unificado a partir de uma única tela.

### Cadastro de Empreendedor
Fluxo de registro que cria automaticamente um tenant isolado (schema PostgreSQL próprio) e redireciona para o checkout do Stripe para seleção do plano de assinatura. Ao concluir o pagamento, o tenant é ativado e o empreendedor já pode acessar o painel.

### Recuperação de Senha
Mecanismo de redefinição de senha por e-mail, disponível para empreendedores e clientes. O backend processa a solicitação e envia um link temporário seguro para o endereço cadastrado.

---

## Área do Empreendedor

### Dashboard
Painel inicial do empreendedor com KPIs resumidos: número de clientes, agendamentos do dia, receita do mês e tarefas pendentes. Serve como ponto de entrada para todas as funcionalidades do sistema.

### Gestão de Clientes
CRUD completo de clientes do empreendedor, com dados pessoais, histórico de atendimentos, status ativo/inativo e visualização por abas (perfil, planos, documentos etc.). Cada cliente está isolado dentro do schema do tenant.

### Agendamentos (Bookings)
Calendário de agendamentos com criação, edição, confirmação e cancelamento de consultas. Integra-se automaticamente ao Google Calendar do empreendedor (sincronização unidirecional) e respeita a agenda de disponibilidade configurada por dia da semana e horário.

### Planos de Refeição (Meal Plans)
Criação e gerenciamento de planos alimentares personalizados, que podem ser atribuídos a clientes específicos. O cliente pode visualizar o plano atribuído no seu portal de acesso.

### Planos de Vitaminas (Vitamin Plans)
Módulo similar ao de refeições, voltado à prescrição de suplementos e vitaminas. Permite criar planos com detalhes dos suplementos e atribuí-los a clientes.

### Receitas (Recipes)
Biblioteca de receitas que o empreendedor pode criar, categorizar e compartilhar. As receitas também podem ser exibidas no website público do tenant.

### Anamneses
Formulários de anamnese clínica para coleta estruturada de informações dos clientes antes ou durante o atendimento. O empreendedor cria e gerencia os registros; o histórico fica vinculado ao perfil de cada cliente.

### Prescrições
Módulo especializado para emissão de prescrições nutricionais/clínicas, com seleção de paciente, itens da prescrição a partir de uma biblioteca de ativos (endpoint `/api/prescricao/ativos/`) e registro completo para consulta futura.

### Mensagens
Sistema de mensagens internas entre empreendedor e clientes, com histórico de conversa, contador de não lidas e marcação automática de leitura. Disponível tanto no painel do empreendedor quanto no portal do cliente.

### Documentos
Permite ao empreendedor fazer upload de documentos (PDF, DOC, imagens etc.) e compartilhá-los com clientes específicos. O cliente pode visualizar e baixar os documentos recebidos pelo seu portal.

### Financeiro
Módulo de controle financeiro com lançamento de receitas e despesas, categorização (consultas, e-commerce, assinatura, impostos etc.), dashboard com KPIs do mês (entradas, saídas e saldo líquido) e envio de relatório mensal por e-mail.

### Relatórios
Painéis com relatórios gerenciais do negócio, incluindo métricas de atendimentos, financeiras e de clientes. Organizado em painéis estilo dashboard com widgets de KPIs e tabelas de detalhamento.

### E-commerce (Produtos e Pedidos)
Gerenciamento de catálogo de produtos e pedidos dos clientes. O empreendedor cadastra produtos com preço e descrição; os clientes acessam o catálogo e realizam compras diretamente pelo website público do tenant.

### Carrinho de Compras
Carrinho persistente no website público com adição/remoção de itens, atualização de quantidades e fluxo de checkout. Inclui contador de itens no header e integração com o módulo de pedidos.

### Planos de Assinatura Internos (Subscriptions)
O empreendedor pode criar e gerenciar planos de assinatura para seus próprios clientes (ex.: plano básico, premium), distintos dos planos de assinatura do SaaS. Os clientes podem visualizar e contratar esses planos pelo website público.

### Contatos (CRM)
Módulo leve de CRM para gerenciar contatos de potenciais clientes ou parceiros, independente da carteira de clientes ativos. Suporta listagem com filtros, detalhamento e notas.

### Mensagens de Suporte (Support)
Lista de tickets de suporte abertos pelos clientes ou pelo próprio empreendedor. Permite acompanhar e responder solicitações de atendimento dentro da plataforma.

### Website Builder (CMS)
Construtor de website público do tenant, com configuração de seções (hero, sobre, features, planos, depoimentos) via interface visual. O site gerado é acessível publicamente e pode exibir receitas, blog, planos e formulário de contato.

### Blog
Módulo de publicação de artigos para o website público do tenant. O empreendedor cria, edita e publica posts com upload de imagens, que ficam disponíveis na área pública do site.

### Documentos Públicos / Landing Pages internas
Além do website, o empreendedor pode criar páginas de destino (landing pages) individuais para produtos ou campanhas específicas, gerenciadas pelo painel administrativo.

### Configurações (Settings)
Painel de configurações do tenant com abas para dados do negócio, logo, tema de cores do website, integração com WhatsApp, configuração de pagamentos e informações de conta. Contempla também a configuração do logo exibido na navbar pública da plataforma.

---

## Integrações

### Pagamentos / Stripe
Integração completa com Stripe para processamento de assinaturas dos empreendedores: criação de checkout session no cadastro, webhooks para atualizar status (ativa, trial, cancelada) e Customer Portal para o empreendedor gerenciar plano e forma de pagamento.

### Google Calendar
Sincronização unidirecional dos agendamentos criados no sistema para o Google Calendar do empreendedor, com atualização automática ao editar ou cancelar. A autenticação é feita via OAuth 2.0 com tokens criptografados.

### WhatsApp Business
Módulo de integração com a API do WhatsApp (modo BYO — Bring Your Own credentials). O empreendedor configura suas credenciais nas configurações do tenant; a disponibilidade depende do plano de assinatura contratado.

---

## Área do Cliente Final

### Portal do Cliente
Interface dedicada ao cliente do empreendedor, com acesso a perfil próprio, planos de refeição e vitaminas atribuídos, histórico de agendamentos, mensagens, documentos recebidos, pedidos realizados e assinatura vigente. Acessível após login com as credenciais criadas pelo empreendedor.

---

## Superadmin (Painel da Plataforma)

### Planos de Assinatura SaaS (Plans)
Gerenciamento dos planos oferecidos pela plataforma WellSaaS para os empreendedores, com configuração de módulos habilitados por plano (booking, website, blog, e-commerce, financeiro, etc.), preço, período de trial e integração com produtos do Stripe.

### Assinantes (Subscribers / Tenants)
Visão geral de todos os tenants cadastrados, com possibilidade de visualizar dados, alterar o plano vinculado, suspender ou reativar o acesso. Inclui formulário inline para edição rápida de cada tenant.

### Landing Page da Plataforma
Gerenciamento do conteúdo da landing page principal do WellSaaS (`/`), incluindo textos do hero, SEO, CTA e seções de apresentação. Segue o padrão singleton — existe apenas uma instância editável pelo superadmin.

### Logs de Webhooks Stripe
Visualização dos eventos recebidos do Stripe (checkout concluído, assinatura criada/atualizada/cancelada etc.) com status de processamento. Auxilia no diagnóstico de falhas no fluxo de cobrança.

---

## Infraestrutura e Plataforma

### Multi-tenancy
Cada empreendedor possui um schema PostgreSQL isolado, garantindo segregação total dos dados. O roteamento de tenant é feito por path/domínio via middleware Django, sem interferência entre clientes.

### Detecção de País e Idioma
O sistema detecta automaticamente o país do usuário para exibir planos, preços e conteúdo no idioma e moeda adequados. Suporte a quatro idiomas: Português, Inglês, Espanhol e Italiano (i18n via i18next).

### Controle de Módulos por Plano
Cada plano de assinatura define quais módulos ficam disponíveis para o tenant (booking, website/CMS, blog, e-commerce, financeiro, suporte, planos internos, WhatsApp). O frontend oculta automaticamente as rotas e menus dos módulos não incluídos no plano vigente.
