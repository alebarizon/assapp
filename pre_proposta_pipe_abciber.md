# Pré-Proposta — PIPE Jornada Tecnológica – Fase 1
**Prazo de submissão: 29/07/2026**

---

## Identificação

**Título do projeto:**
Arquitetura de software para gestão contínua de conhecimento institucional em associações científicas: investigação de requisitos e desenvolvimento de plataforma SaaS adaptativa

**Empresa Sede:** Alexandre Barizon ME
**CNPJ:** 05.562.968/0001-25
**Pesquisador Responsável:** Alexandre Barizon
**Formação:** Engenheiro Mecânico (EESC/USP); Mestre em Ciências da Comunicação — Sistemas Adaptativos para Web (ECA/USP, 2000)
**Bolsista FAPESP anterior:** TT5 — Projeto Neumat/NeuroMat (2018)

---

## 1. Problema de Mercado

### 1.1 Contexto e dimensão do problema

O Brasil conta com um dos maiores ecossistemas de organizações sem fins lucrativos do mundo. Segundo o IBGE (FASFIL 2016), havia 237 mil Fundações Privadas e Associações sem Fins Lucrativos ativas no país, representando 4,3% de todas as organizações formais cadastradas no CEMPRE. O Mapa das Organizações da Sociedade Civil do IPEA, utilizando base mais ampla, registra 820 mil organizações em atividade. Desse universo, destacam-se os segmentos diretamente endereçáveis por esta proposta: 29 mil associações patronais e profissionais (12,2% do total), 15,9 mil organizações de educação e pesquisa (6,7%) e 32,3 mil de cultura e recreação (13,6%) — perfazendo mais de 77 mil organizações com estrutura de membros, eventos e gestão financeira recorrente.

Essas organizações compartilham uma característica estrutural crítica sistematicamente ignorada pelas soluções de software comerciais existentes: **diretorias eleitas com mandatos curtos** (tipicamente de 2 anos), renovadas periodicamente por processo democrático. Essa rotatividade, inerente à governança associativa, produz um fenômeno recorrente e de alto custo operacional: a **ruptura cíclica de memória institucional**.

A cada troca de diretoria, informações críticas sobre associados, histórico financeiro, regras de eventos anteriores, contratos com fornecedores e padrões de comunicação com membros se perdem ou ficam inacessíveis — não por negligência, mas porque estão dispersas em planilhas pessoais, e-mails de gestores que saem e sistemas desconectados entre si. A diretoria entrante recomeça do zero, repetindo erros já cometidos e reinventando processos que funcionaram no passado.

A pesquisa proposta será conduzida no nicho de **associações científicas**, onde o PR dispõe de acesso privilegiado a dados e usuários reais acumulado ao longo de 10 anos. Os requisitos investigados na Fase 1, contudo, são estruturalmente generalizáveis para o mercado endereçável total de mais de 237 mil organizações no Brasil que enfrentam a mesma falha de gestão — posicionando a plataforma resultante como solução vertical para o terceiro setor organizado, e não apenas para o segmento científico-acadêmico.

### 1.2 Evidência empírica do problema

Esta proposta parte de observação longitudinal direta: o Pesquisador Responsável presta suporte técnico contínuo à ABCiber — Associação Brasileira de Pesquisadores em Cibercultura (www.abciber.org.br), sediada em São Paulo, há aproximadamente 10 anos, acompanhando cinco ciclos completos de troca de diretoria. Nesse período, as seguintes disfunções se repetiram sistematicamente em cada ciclo:

- **Gestão caótica de filiações e anuidades:** cadastros desatualizados, inadimplência não monitorada, dificuldade de distinção entre membros ativos e inativos, ausência de automação de cobranças e renovações.
- **Fragmentação da comunicação com membros:** listas de e-mail desatualizadas, comunicações enviadas por ferramentas pessoais de gestores, perda de histórico de interações com filiados entre mandatos.
- **Gestão de eventos com ferramentas improvisadas:** submissão de trabalhos por formulários Google, inscrições por planilhas, emissão manual de certificados, ausência de integração entre submissão, avaliação e publicação de anais.
- **Falta de visão financeira integrada:** receitas de filiações, inscrições em eventos e patrocínios gerenciadas em sistemas separados, sem consolidação que permita à diretoria tomar decisões baseadas em dados.

Esses problemas não são específicos da ABCiber. O PR identificou padrões idênticos em outras unidades com as quais trabalhou (ECA/USP, FAU/USP, IP/USP, FEA/USP, SIBI/USP), sugerindo que se trata de uma falha sistêmica do segmento, não de uma particularidade organizacional.

### 1.3 Por que soluções existentes não resolvem

CRMs comerciais genéricos (Salesforce, HubSpot, Zoho) foram concebidos para empresas com equipes estáveis, hierarquias definidas e relacionamentos comerciais contínuos. Plataformas de gestão de associações internacionais (Wild Apricot, MemberPress, Raklet) não contemplam: (a) o modelo de governança científica brasileiro com eleições periódicas e mandatos curtos; (b) a integração com fluxos de publicação acadêmica (submissão de trabalhos, pareceristas, anais); (c) a necessidade de preservação ativa de memória institucional entre gestões; (d) as especificidades regulatórias e fiscais de associações sem fins lucrativos no Brasil.

---

## 2. Incerteza Técnica e Hipótese de Pesquisa

### 2.1 A questão central

A questão de pesquisa que esta proposta se propõe a investigar na Fase 1 é:

> **É possível projetar uma arquitetura de software que preserve e transfira ativamente conhecimento institucional entre ciclos de gestão em associações científicas, e quais são os requisitos funcionais, de modelagem de dados e de interface necessários para que essa arquitetura seja adotada e mantida por diretorias sucessivas com diferentes perfis técnicos?**

Essa questão não tem resposta trivial. O desafio técnico não é construir um CRM — é investigar como modelar entidades, fluxos e transições de estado de forma que o conhecimento gerado por uma gestão seja **estruturalmente acessível e contextualizado** para a próxima, independentemente de continuidade de pessoas.

### 2.2 Hipóteses específicas a investigar

**H1 — Modelagem de conhecimento institucional:** A representação de processos recorrentes de associações científicas (ciclos de filiação, eventos, publicações) como modelos de dados com histórico auditável e anotações contextuais é suficiente para reduzir o tempo de onboarding de novas diretorias em pelo menos 50% em relação ao processo atual baseado em planilhas.

**H2 — Arquitetura adaptativa a perfis de gestão:** Uma interface adaptativa que se reconfigura conforme o perfil técnico da diretoria ativa (gestores experientes vs. iniciantes em sistemas) resulta em taxas de adoção sustentada superiores a interfaces padronizadas — conectando-se diretamente à expertise do PR em sistemas adaptativos investigada no mestrado (ECA/USP, 2000).

**H3 — Integração de fluxos acadêmicos:** A integração nativa entre gestão de membros, gestão de eventos e fluxo de submissão/publicação de trabalhos científicos em uma única plataforma elimina redundâncias operacionais que, na configuração atual de ferramentas desconectadas, consomem em média X horas/mês de trabalho voluntário de gestores. *(X a ser mensurado na Fase 1 com dados da ABCiber)*

### 2.3 O que não se sabe e precisa ser pesquisado

Não está estabelecido na literatura de engenharia de software e sistemas de informação:
- Quais são os **requisitos mínimos de modelagem de dados** para preservação de memória institucional em organizações com liderança rotativa de curto prazo
- Como projetar **transições de estado entre mandatos** (transferência de acesso, arquivamento contextual, onboarding guiado) de forma que não dependam de documentação manual pelos gestores
- Qual é o **limiar de complexidade de interface** aceitável para usuários voluntários sem perfil técnico em sistemas de gestão científica

Essas questões serão respondidas na Fase 1 por meio de: revisão sistemática da literatura, entrevistas estruturadas com gestores de 5 a 8 associações científicas paulistas, prototipagem iterativa e testes de usabilidade com usuários reais da ABCiber.

---

## 3. Equipe e Capacidade de Execução

### 3.1 Pesquisador Responsável

O PR reúne a combinação de competências diretamente necessária para este projeto:

**Domínio técnico:** Engenheiro Mecânico (EESC/USP) com especialização em desenvolvimento web/sistemas (frontend + backend), com carreira de mais de 20 anos em projetos de TI para instituições públicas e privadas. Experiência documentada em desenvolvimento de sistemas para unidades USP (ECA, FAU, IP, FEA, SIBI).

**Domínio acadêmico-científico:** Mestre em Ciências da Comunicação pela ECA/USP (2000), com dissertação sobre sistemas personalizados e adaptativos para Web — base direta para a H2 desta proposta. Familiaridade com o ecossistema de pesquisa, suas instituições, processos e cultura organizacional.

**Conhecimento longitudinal do problema:** 10 anos de suporte técnico contínuo à ABCiber, com observação direta de 5 ciclos de troca de diretoria e registro das disfunções operacionais recorrentes. Essa profundidade de observação é o ativo mais difícil de replicar e o que diferencia esta proposta de um desenvolvimento de software convencional.

**Histórico FAPESP:** Bolsista TT5 no projeto Neumat/NeuroMat (2018), com entrega documentada de sistema interativo desenvolvido em Unity (game.numec.prp.usp.br), sem pendências com a Fundação.

**Produto pré-existente:** O PR desenvolveu o Wellflows (wellflows.online), plataforma SaaS de CRM com módulos de gestão de relacionamento, comunicação e financeiro. Aproximadamente 80% da arquitetura base desta plataforma é reutilizável para o domínio acadêmico/científico, reduzindo significativamente o risco técnico da Fase 1 e permitindo que o projeto se concentre na investigação dos requisitos específicos do segmento, não na construção de infraestrutura do zero.

### 3.2 Infraestrutura disponível

- Ambiente de desenvolvimento web completo (frontend + backend + banco de dados)
- Código-fonte do Wellflows como base tecnológica reutilizável
- Acesso a usuários reais da ABCiber para pesquisa, prototipagem e testes
- Rede de contatos em unidades USP para expansão da amostra de pesquisa (entrevistas com gestores de associações)

### 3.3 Previsão de equipe complementar

Para a Fase 1, está prevista a contratação de:
- 1 bolsista TT (nível a definir) com perfil em UX/design de interfaces ou engenharia de software, para apoio no desenvolvimento de protótipos e condução de testes de usabilidade
- Consultor eventual em ciência da informação ou gestão do conhecimento para revisão das hipóteses de modelagem de dados (a definir conforme necessidade identificada na revisão de literatura)

---

*Proposta elaborada para submissão ao PIPE Jornada Tecnológica – Fase 1, 1ª Rodada 2026*
*Prazo de pré-proposta: 29/07/2026 | Proposta completa (se enquadrada): 28/09/2026*
