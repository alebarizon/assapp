# AssApp — Hipóteses de Pesquisa PIPE FAPESP

> **Projeto:** Arquitetura de software para gestão contínua de conhecimento institucional em associações científicas  
> **Fase:** PIPE Jornada Tecnológica — Fase 1  
> **Associação piloto:** ABCiber (www.abciber.org.br)

---

## Questão Central de Pesquisa

> É possível projetar uma arquitetura de software que preserve e transfira **ativamente** conhecimento institucional entre ciclos de gestão em associações científicas, e quais são os requisitos funcionais, de modelagem de dados e de interface necessários para que essa arquitetura seja adotada e mantida por diretorias sucessivas com diferentes perfis técnicos?

---

## H1 — Modelagem de Conhecimento Institucional

### Hipótese

A representação de processos recorrentes de associações científicas (ciclos de filiação, eventos, publicações) como **modelos de dados com histórico auditável e anotações contextuais** é suficiente para reduzir o tempo de onboarding de novas diretorias em **pelo menos 50%** em relação ao processo atual baseado em planilhas.

### Implementação no AssApp

| Entidade | Módulo | Função |
|----------|--------|--------|
| `Mandato` | `mandatos` | Ciclo de gestão com início/fim e status |
| `MandatoSnapshot` | `mandatos` | Estado consolidado auditável (hash SHA-256) |
| `ContextoHistorico` | `memoria` | Quem decidiu o quê, por quê, em qual mandato |
| `TimelineInstitucional` | `memoria` | Visão cronológica por mandato |
| `TransicaoMandato` | `mandatos` | Handoff estruturado entre gestões |

### Métricas de Validação

- **Tempo de onboarding** (horas até diretoria operacional): baseline ABCiber vs. AssApp
- **Completude do snapshot**: % de dados críticos capturados automaticamente
- **Consultas ao histórico**: frequência de acesso a `ContextoHistorico` nos primeiros 90 dias

### Decisões de Design (rastreabilidade científica)

1. **Snapshot com hash** — garante integridade auditável para publicação científica
2. **Campos `decisao` + `moto`** em `ContextoHistorico` — forçam registro do "por quê", não apenas do "o quê"
3. **Vínculo obrigatório a `mandato_id`** — contextualiza cada registro no ciclo de gestão

---

## H2 — Arquitetura Adaptativa a Perfis de Gestão

### Hipótese

Uma **interface adaptativa** que se reconfigura conforme o perfil técnico da diretoria ativa (gestores experientes vs. iniciantes em sistemas) resulta em taxas de **adoção sustentada superiores** a interfaces padronizadas.

> Conexão com expertise do PR: dissertação de mestrado (ECA/USP, 2000) sobre sistemas personalizados e adaptativos para Web.

### Implementação no AssApp

| Componente | Função |
|------------|--------|
| `PerfilTecnico` (enum) | `iniciante`, `intermediario`, `avancado` no modelo User |
| `OnboardingEtapa.perfil_minimo` | Filtra etapas visíveis por perfil |
| `OnboardingWizard.tsx` | UI com wizards expandidos para iniciantes |
| Modo "Nova Diretoria" | Dashboard adaptado durante `TransicaoMandato` |

### Comportamentos Adaptativos

| Perfil | Comportamento |
|--------|---------------|
| `iniciante` | Wizards passo-a-passo, tooltips expandidos, etapas simplificadas |
| `intermediario` | Checklist com links diretos, menos hand-holding |
| `avancado` | Dashboard compacto, atalhos, etapas opcionais ocultas |

### Métricas de Validação

- **Taxa de conclusão do onboarding** (% etapas obrigatórias concluídas)
- **DAU/MAU** nos primeiros 90 dias por mandato
- **Tempo médio por etapa** comparado entre perfis
- **Taxa de abandono** (diretorias que param de usar após 30/60/90 dias)

---

## H3 — Integração de Fluxos Acadêmicos

### Hipótese

A integração nativa entre gestão de membros, gestão de eventos e fluxo de submissão/publicação de trabalhos científicos em uma **única plataforma** elimina redundâncias operacionais que, na configuração atual de ferramentas desconectadas, consomem em média **X horas/mês** de trabalho voluntário de gestores.

> *X será mensurado na Fase 1 com diário de bordo dos gestores da ABCiber.*

### Implementação no AssApp

| Entidade | Integração |
|----------|------------|
| `EventoAcademico` | Vinculado a `Mandato` |
| `SubmissaoTrabalho.membro` | FK para `Membro` — autor já é associado |
| `CallForPapers` | Substitui Google Forms |
| `Parecer` | Substitui e-mail/planilha de pareceristas |
| `AnaisPublicacao` | Geração automática a partir de submissões aceitas |
| `InscricaoEvento` | Integrada com `Anuidade` e financeiro |

### Fluxo Integrado (H3)

```
Membro filiado
    → Inscrição no EventoAcademico
    → Submissão via CallForPapers
    → Atribuição de Parecerista (role: reviewer)
    → Avaliação (Parecer)
    → Aceite → AnaisPublicacao
    → Certificado (InscricaoEvento)
    → Lançamento financeiro (se pago)
```

### Métricas de Validação

- **Horas/mês em tarefas redundantes** (diário de bordo pré e pós AssApp)
- **Tempo médio submissão → publicação em anais**
- **Taxa de erro** (submissões duplicadas, pareceres perdidos)
- **Número de ferramentas externas** necessárias (meta: 0 para fluxo completo)

---

## Protocolo de Pesquisa — Fase 1

### Revisão Sistemática da Literatura
- Gestão do conhecimento em OSCs
- Sistemas adaptativos para Web
- Plataformas de gestão associativa

### Entrevistas Estruturadas
- **Amostra:** 5–8 associações científicas paulistas
- **Roteiro:** [`research/roteiro_entrevista_gestores.md`](../research/roteiro_entrevista_gestores.md)
- **Dados:** armazenados anonimizados em `research/dados/`

### Prototipagem Iterativa
- Sprint 2: Mandatos + Onboarding (ABCiber)
- Sprint 3: Memória Institucional
- Sprint 5: Eventos + CFP

Status detalhado (Sprints 1–5, pendências, Sprint 6): [`docs/referencia/STATUS_SPRINTS_FASE1.md`](../referencia/STATUS_SPRINTS_FASE1.md)

### Testes de Usabilidade
- Com diretoria entrante da ABCiber
- Métricas: SUS (System Usability Scale), tempo de tarefa, taxa de erro

---

## Rastreabilidade Código ↔ Hipóteses

Ao implementar funcionalidades, documentar no código:

```python
# H1: Snapshot automático preserva memória institucional entre mandatos
def criar_snapshot(self, tipo="encerramento"):
    ...

# H2: Etapas filtradas por perfil técnico do usuário
def visivel_para_perfil(self, perfil: str) -> bool:
    ...
```

Commits e changelogs devem referenciar H1, H2 ou H3 quando aplicável.

---

**Última atualização:** 2026-07-13
