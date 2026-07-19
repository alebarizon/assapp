# Pré-Proposta (v3) — PIPE Jornada Tecnológica – Fase 1
**Prazo de submissão: 29/07/2026**
**Versão:** v3 — H3 removida como hipótese e reposicionada como diferencial de produto na seção 1.3; três hipóteses remanescentes (H1, H2, H4)

---

## Identificação

**Título do projeto:**
Arquitetura de software para gestão de conhecimento institucional e análise de redes de colaboração em associações científicas: investigação de requisitos, modelagem e plataforma SaaS adaptativa

**Empresa Sede:** Alexandre Barizon ME
**CNPJ:** 05.562.968/0001-25
**Pesquisador Responsável:** Alexandre Barizon
**Formação:** Engenheiro Mecânico (EESC/USP, 1993); Mestre em Ciências da Comunicação — Sistemas Adaptativos para Web (ECA/USP, 2000)
**Bolsistas FAPESP anteriores:**
- TT5 — Projeto METRICS: Métricas para Avaliação de Revistas Científicas em Ciências Sociais (2011)
- TT5 — Projeto Neumat/NeuroMat (2018)

---

## 1. Problema de Mercado

### 1.1 Contexto e dimensão do problema

O Brasil conta com um dos maiores ecossistemas de organizações sem fins lucrativos do mundo. Segundo o IBGE (FASFIL 2016), havia 237 mil Fundações Privadas e Associações sem Fins Lucrativos ativas no país, representando 4,3% de todas as organizações formais cadastradas no CEMPRE. O Mapa das Organizações da Sociedade Civil do IPEA registra 820 mil organizações em atividade. Desse universo, destacam-se os segmentos diretamente endereçáveis por esta proposta: 29 mil associações patronais e profissionais (12,2% do total), 15,9 mil organizações de educação e pesquisa (6,7%) e 32,3 mil de cultura e recreação (13,6%) — perfazendo mais de 77 mil organizações com estrutura de membros, eventos e gestão financeira recorrente.

Essas organizações compartilham uma característica estrutural crítica sistematicamente ignorada pelas soluções de software comerciais existentes: **diretorias eleitas com mandatos curtos** (tipicamente de 2 anos), renovadas periodicamente por processo democrático. Essa rotatividade produz um fenômeno recorrente e de alto custo operacional: a **ruptura cíclica de memória institucional**.

A cada troca de diretoria, informações críticas sobre associados, histórico financeiro, regras de eventos anteriores, contratos com fornecedores e padrões de comunicação com membros se perdem — não por negligência, mas porque estão dispersas em planilhas pessoais, e-mails de gestores que saem e sistemas desconectados entre si. A diretoria entrante recomeça do zero, repetindo erros já cometidos e reinventando processos que funcionaram no passado.

A pesquisa proposta será conduzida no nicho de **associações científicas**, onde o PR dispõe de acesso privilegiado a dados e usuários reais acumulado ao longo de 10 anos. Os requisitos investigados na Fase 1 são estruturalmente generalizáveis para o mercado endereçável total de mais de 237 mil organizações no Brasil — posicionando a plataforma resultante como solução vertical para o terceiro setor organizado.

### 1.2 Evidência empírica do problema

Esta proposta parte de observação longitudinal direta: o Pesquisador Responsável presta suporte técnico contínuo à ABCiber — Associação Brasileira de Pesquisadores em Cibercultura (www.abciber.org.br), sediada em São Paulo, há aproximadamente 10 anos, acompanhando cinco ciclos completos de troca de diretoria. Nesse período, as seguintes disfunções se repetiram sistematicamente em cada ciclo:

- **Gestão caótica de filiações e anuidades:** cadastros desatualizados, inadimplência não monitorada, ausência de automação de cobranças e renovações.
- **Fragmentação da comunicação com membros:** listas de e-mail desatualizadas, perda de histórico de interações entre mandatos.
- **Gestão de eventos com ferramentas improvisadas:** submissão de trabalhos por formulários Google, inscrições por planilhas, ausência de integração entre submissão, avaliação e publicação de anais.
- **Falta de visão financeira integrada:** receitas de filiações, inscrições e patrocínios gerenciadas em sistemas separados, sem consolidação para tomada de decisão.

Esses problemas não são específicos da ABCiber. O PR identificou padrões idênticos nas unidades USP com as quais trabalhou (ECA, FAU, IP/USP, FEA, SIBI) e nas associações científicas que atende — Intercom, ABCiber — sugerindo falha sistêmica do segmento.

### 1.3 Por que soluções existentes não resolvem — e o diferencial desta plataforma

CRMs comerciais genéricos (Salesforce, HubSpot, Zoho) foram concebidos para empresas com equipes estáveis e relacionamentos comerciais contínuos. Plataformas de gestão de associações internacionais (Wild Apricot, MemberPress, Raklet, NeonCRM, MemberClicks) não contemplam: (a) o modelo de governança democrática com mandatos curtos; (b) a preservação ativa de memória institucional entre gestões; (c) as especificidades regulatórias e fiscais de associações sem fins lucrativos no Brasil (LGPD, Marco Legal das OSC, NF de serviços). Em termos de produto, a plataforma proposta diferencia-se ainda por **integrar nativamente os fluxos de gestão de membros, eventos e submissão/publicação de trabalhos científicos** — eliminando a fragmentação atual entre ferramentas desconectadas (PKP-OCS para eventos, PKP-OJS para publicações, planilhas para filiações) que hoje impõe ao gestor voluntário o papel de operador manual de sincronização de dados entre sistemas. Essa integração é uma característica de produto, não uma hipótese de pesquisa: seu resultado é esperado por design. O que é genuinamente incerto — e constitui o objeto de investigação desta proposta — são as três questões descritas a seguir.

Adicionalmente, **nenhuma plataforma AMS existente captura os dados comportamentais de pesquisadores em estrutura de grafo temporal** — dado que esta plataforma gerará de forma nativa como subproduto da gestão associativa, abrindo a possibilidade de análise inédita de redes de colaboração científica (H4).

---

## 2. Incerteza Técnica e Hipóteses de Pesquisa

### 2.1 A questão central

A questão de pesquisa que esta proposta se propõe a investigar na Fase 1 é:

> **É possível projetar uma arquitetura de software que (i) preserve e transfira ativamente conhecimento institucional entre ciclos de gestão em associações científicas, (ii) adapte sua interface ao perfil técnico variável de gestores voluntários, e (iii) capture, de forma nativa, dados comportamentais de pesquisadores em estrutura de grafo temporal — e quais são os requisitos funcionais, de modelagem de dados e de interface necessários para que essa arquitetura seja adotada por diretorias sucessivas e produza dados analiticamente úteis para inferência de redes de colaboração científica?**

O desafio técnico não é construir um CRM convencional. É investigar como modelar entidades, fluxos e transições de estado de forma que o conhecimento gerado por uma gestão seja estruturalmente acessível para a próxima — e simultaneamente estruturar o esquema de dados de modo que as sequências de interação dos pesquisadores com a plataforma (filiação, submissão, avaliação, participação em eventos, renovação) componham um **grafo temporal de relações científicas** analiticamente explorável.

### 2.2 Hipóteses específicas a investigar

**H1 — Modelagem de conhecimento institucional:**
A representação de processos recorrentes de associações científicas (ciclos de filiação, eventos, publicações) como modelos de dados com histórico auditável e anotações contextuais vinculadas a cada ciclo de mandato é suficiente para reduzir o tempo de onboarding de novas diretorias em pelo menos 50% em relação ao processo atual baseado em planilhas dispersas.

*Métrica de validação:* tempo médio (em horas) para que um novo gestor localize, compreenda e execute os três principais processos recorrentes da associação, medido por protocolo de observação em sessões com a diretoria entrante da ABCiber — comparado ao baseline documentado antes da implantação do sistema. Métrica secundária: número de decisões revertidas por falta de contexto histórico no primeiro trimestre do mandato.

**H2 — Arquitetura adaptativa a perfis de gestão:**
Uma interface que infere implicitamente o perfil técnico do gestor a partir de padrões de navegação e frequência de uso — e reconfigura dinamicamente a complexidade dos fluxos exibidos — resulta em taxas de adoção sustentada e tempo de conclusão de tarefas significativamente superiores às de uma interface padronizada, para o perfil específico de usuário voluntário com uso ocasional.

*Métrica de validação:* taxa de conclusão de tarefas sem assistência externa (task completion rate), tempo médio por tarefa (time-on-task) e NPS interno — comparados entre versão adaptativa e versão estática em teste A/B com gestores da ABCiber e de 2 a 3 associações adicionais. A hipótese é genuinamente incerta porque a literatura de sistemas adaptativos (ACM UMAP) foca em usuários frequentes de plataformas de consumo; o comportamento de usuários ocasionais em sistemas organizacionais não foi investigado.

**H4 — Predição de colaboração científica via análise de redes de engajamento associativo:**
Sequências temporais de interação de pesquisadores com a plataforma (eventos de filiação → submissão → avaliação como parecerista → participação em evento → renovação) formam um grafo temporal cujas propriedades topológicas — grau nodal, centralidade de intermediação, coeficiente de clustering e força de laços fracos — são preditivas de colaborações científicas futuras, mensuráveis por co-autorias em periódicos indexados no período subsequente.

*Fundamentação matemática:* A hipótese se apoia na teoria dos grafos (Erdős–Rényi; Barabási–Albert para redes livre de escala) e em modelos de predição de links em grafos dinâmicos (índices Adamic–Adar, Jaccard e Common Neighbors). A plataforma gerará, como subproduto nativo da gestão associativa, o primeiro dataset longitudinal de interações de pesquisadores em associações científicas brasileiras — dado atualmente inexistente por ausência de sistema integrado que capture simultaneamente filiação, submissão e participação em eventos.

*Conexão com projetos anteriores FAPESP do PR:* O projeto METRICS (TT5, 2011) investigou métricas para avaliação de revistas científicas em Ciências Sociais — contexto de mensuração do ecossistema de publicação científica. O projeto Neumat (TT5, 2018) aplicou modelos de árvores de contexto probabilístico (VLMC — Variable Length Markov Chains) para inferir padrões de aprendizagem a partir de sequências comportamentais. A H4 é a convergência natural dessas duas linhas: modelagem probabilística de sequências comportamentais (Neumat) aplicada à inferência de redes de colaboração científica (METRICS), com a plataforma de gestão associativa como ambiente de coleta de dados.

*Métrica de validação na Fase 1:* (i) modelagem do esquema de grafo temporal (definição de nós, arestas tipadas e timestamps); (ii) coleta dos primeiros dados piloto com a ABCiber — mínimo de 1 ciclo completo de evento científico; (iii) cálculo de métricas de rede baseline (grau médio, densidade, distribuição de grau); (iv) teste preliminar de predição de links com AUC-ROC como métrica de desempenho. A validação completa da hipótese requer dados longitudinais e será conduzida na Fase 2.

### 2.3 O que não se sabe e precisa ser pesquisado

Não está estabelecido na literatura de engenharia de software, sistemas de informação e ciência de redes:

- Quais são os **requisitos mínimos de modelagem de dados** para preservação ativa de memória institucional em organizações com liderança rotativa de curto prazo — a literatura trata o problema como desafio organizacional, não tecnológico (H1)
- Qual é o **limiar de complexidade de interface** aceitável para usuários voluntários com uso ocasional de sistemas organizacionais, e se técnicas de modelagem implícita de perfil da literatura ACM UMAP são transferíveis a esse contexto (H2)
- **Se e em que grau** as sequências de engajamento em plataformas de gestão associativa são preditivas de futuras colaborações científicas — problema de predição de links em grafos temporais que, neste contexto específico, nunca foi investigado por ausência de dados adequados (H4)

Essas questões serão respondidas na Fase 1 por meio de: revisão sistemática da literatura (H1, H2, H4), entrevistas estruturadas com gestores de 5 a 8 associações científicas paulistas (H1), prototipagem iterativa e testes de usabilidade A/B (H2), e modelagem e coleta de dados de grafo temporal com a ABCiber como ambiente piloto (H4).

---

## 3. Equipe e Capacidade de Execução

### 3.1 Pesquisador Responsável

O PR reúne a combinação de competências diretamente necessária para este projeto:

**Domínio técnico:** Engenheiro Mecânico (EESC/USP, 1993) com especialização em desenvolvimento web/sistemas (frontend + backend), com carreira de mais de 20 anos em projetos de TI para instituições acadêmicas. Experiência documentada em implantação e manutenção de sistemas PKP-OJS (publicações eletrônicas), PKP-OCS (gestão de eventos científicos), DSpace e AtoM (repositórios institucionais) em unidades USP (ECA, FEA, IP/USP) e em associações científicas nacionais (Intercom, ABCiber).

**Domínio acadêmico-científico e continuidade intelectual:** Mestre em Ciências da Comunicação pela ECA/USP (2000), com dissertação sobre sistemas personalizados e adaptativos para Web — base direta para a H2. Bolsista TT5 FAPESP no projeto METRICS (2011), sobre métricas para avaliação de revistas científicas em Ciências Sociais — base direta para a H4. Bolsista TT5 FAPESP no projeto Neumat/NeuroMat (2018), onde modelos VLMC foram aplicados à inferência de padrões a partir de sequências comportamentais — base matemática da H4. A proposta representa a convergência natural dessas três linhas ao longo de 26 anos.

**Conhecimento longitudinal do problema:** 10 anos de suporte técnico contínuo à ABCiber, com observação direta de 5 ciclos de troca de diretoria e registro das disfunções operacionais recorrentes. Esse dado empírico não é reproduzível por pesquisa de campo convencional no horizonte de uma Fase 1.

**Produto pré-existente:** O PR desenvolveu o Wellflows (wellflows.online), plataforma SaaS de CRM com módulos de gestão de relacionamento, comunicação e financeiro. Aproximadamente 80% da arquitetura base é reutilizável para o domínio acadêmico/científico, reduzindo o risco técnico da Fase 1 e concentrando o projeto na investigação das três hipóteses.

### 3.2 Infraestrutura disponível

- Ambiente de desenvolvimento web completo (frontend + backend + banco de dados relacional e orientado a grafos)
- Código-fonte do Wellflows como base tecnológica reutilizável
- Acesso a dados e usuários reais da ABCiber para pesquisa, prototipagem e testes (incluindo dados históricos de eventos científicos, filiações e comunicações para bootstrap do grafo temporal H4)
- Rede de contatos em associações científicas paulistas para expansão da amostra (Intercom e parceiros da ABCiber)

### 3.3 Previsão de equipe complementar

Para a Fase 1, está prevista a contratação de:

- **1 bolsista TT com perfil duplo:** graduando ou mestrando em Ciência da Computação ou Sistemas de Informação, com interesse em análise de redes e desenvolvimento web — para apoio no desenvolvimento do protótipo, modelagem do grafo temporal (H4) e condução dos testes de usabilidade (H2)
- **Consultor em ciência de dados/grafos** (eventual): para revisão da modelagem matemática da H4 e definição das métricas de validação — preferencialmente docente de CC ou Matemática Aplicada de instituição paulista (ICMC/USP, UNICAMP ou similar)

---

## Nota sobre o enquadramento na FAPESP

A proposta cruza três áreas do conhecimento com hipóteses distintas e complementares:

| Área | Hipótese | Perfil do avaliador |
|---|---|---|
| Ciência da Computação / Sistemas de Informação | H1 | SI, Banco de Dados, Engenharia de Software |
| Comunicação / HCI / Sistemas Adaptativos | H2 | Computação, IHC, ACM UMAP |
| Matemática Aplicada / Ciência de Redes | H4 | Matemática, Grafos, Ciência de Dados |

**Enquadramento recomendado:** Interdisciplinar > Ciência da Computação > Sistemas de Informação

---

## Histórico de versões

| Versão | Data | Alterações principais |
|---|---|---|
| v1 | jul/2026 | Versão inicial — H1, H2, H3; bolsa TT5 2018 |
| v2 | jul/2026 | Adição de H4 (grafos/predição); CV atualizado com bolsa TT5 2011 |
| v3 | jul/2026 | H3 removida como hipótese; conteúdo de H3 reposicionado como diferencial de produto na seção 1.3; tabela de enquadramento atualizada |

---

*Proposta v3 elaborada para submissão ao PIPE Jornada Tecnológica – Fase 1, 1ª Rodada 2026*
*Prazo de pré-proposta: 29/07/2026 | Proposta completa (se enquadrada): 28/09/2026*
*Alexandre Barizon ME — CNPJ 05.562.968/0001-25*
