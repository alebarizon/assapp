# Prompts de Levantamento Acadêmico
## Tema: SaaS Adaptativo para Gestão de Conhecimento Institucional em Associações Científicas
### Base para Proposta PIPE/FAPESP — Fase 1 (Submissão: setembro 2026)

> **Como usar:** Cada prompt abaixo deve ser executado separadamente em uma sessão de IA (Claude, Perplexity ou ChatGPT com acesso à web). Os resultados alimentarão as seções técnicas da proposta completa. A ordem sugerida é a mesma sequência dos documentos que você produziu para o tema anterior.

---

## PROMPT 1 — Estado da Arte
**Equivalente ao arquivo:** `synthetic_data_unity_pecuaria.html`
**Alimenta:** Seção 2 da proposta (Incerteza Técnica e Hipótese de Pesquisa)

```
Você é um pesquisador especialista em sistemas de informação, gestão do conhecimento 
e software para organizações sem fins lucrativos. Quero fazer um levantamento 
acadêmico completo sobre o seguinte tema:

  Sistemas de software para gestão de associações científicas e preservação de 
  memória institucional em organizações com liderança rotativa

Meu objetivo é cobrir 4 dimensões:
  1. Papers e publicações científicas relevantes
  2. Centros e grupos de pesquisa ativos no mundo e no Brasil
  3. Referências de mercado (soluções AMS existentes e suas limitações)
  4. Lacunas e oportunidades de pesquisa originais

Para começar, me dê:
  a) Um panorama do estado da arte em 3–4 parágrafos cobrindo:
     - O campo de Association Management Software (AMS) e suas limitações documentadas
     - Pesquisa sobre gestão do conhecimento em organizações com liderança rotativa
     - O que se sabe sobre falhas de continuidade institucional em associações 
       científicas e do terceiro setor
     - O papel de sistemas adaptativos e personalizados na mitigação desse problema

  b) Os 5 subtemas mais relevantes dentro deste campo:
     - Gestão do conhecimento em organizações voluntárias
     - Sistemas adaptativos para usuários não-técnicos
     - Continuidade institucional em mandatos rotativos
     - AMS especializados para o contexto acadêmico-científico
     - Modelagem de dados para organizações do terceiro setor no Brasil

  c) As 10 palavras-chave mais usadas na literatura para buscas em 
     Google Scholar, IEEE Xplore, ACM Digital Library e Semantic Scholar

  d) Quais combinações de eixos (AMS + conhecimento institucional + 
     organizações científicas + sistemas adaptativos) estão mais exploradas 
     na literatura e quais ainda são lacunas genuínas

Use linguagem técnica e científica. Seja preciso com nomes de técnicas, 
frameworks e termos da literatura. Cite DOIs ou links quando disponível.
```

---

## PROMPT 2 — Gap Analysis
**Equivalente ao arquivo:** `gap_analysis_synthetic_data_plf.html`
**Alimenta:** Seção 2.3 da proposta (O que não se sabe e precisa ser pesquisado)

```
Você é um pesquisador especialista em engenharia de software, sistemas de informação 
e gestão de organizações sem fins lucrativos. Com base no estado da arte em:

  - Association Management Software (AMS): Wild Apricot, MemberPress, Raklet, 
    MemberClicks, NeonCRM, YourMembership
  - Gestão do conhecimento em organizações com liderança rotativa
  - Sistemas de informação para associações científicas e acadêmicas no Brasil
  - Arquiteturas de software para preservação de memória institucional

Identifique e detalhe:

1. LACUNAS DE PESQUISA não exploradas ou sub-representadas na literatura atual
   (mínimo 6 lacunas, com evidência de que são genuínas)
   Foque especialmente em:
   - Modelagem de transições de mandato em sistemas de gestão associativa
   - Requisitos específicos de associações científicas vs. comerciais
   - Preservação ativa de contexto entre gestões (não apenas arquivamento)
   - Interfaces adaptativas para gestores voluntários com perfis técnicos variáveis
   - Especificidades do terceiro setor brasileiro (fiscal, jurídico, cultural)

2. PROBLEMAS ABERTOS (open problems) sem solução consolidada
   - O que a literatura identifica como desafio mas ainda não resolveu?

3. LIMITAÇÕES DOCUMENTADAS das soluções AMS existentes
   - Por que Wild Apricot, MemberPress, Raklet e similares falham especificamente 
     para associações científicas com governança democrática rotativa?
   - Quais são as limitações verificadas em benchmarks ou estudos de caso?

4. OPORTUNIDADES onde uma arquitetura especializada poderia oferecer 
   vantagem sobre soluções genéricas:
   - Modelagem de ciclos de mandato com histórico auditável
   - Onboarding guiado para diretorias entrantes
   - Integração nativa com fluxos de publicação acadêmica (submissão, pareceristas, anais)
   - Visão financeira integrada específica para OSCIP/associações brasileiras

Para cada lacuna identificada, indique:
- Evidência de que é real (paper, limitação documentada, ausência na literatura)
- Por que não foi resolvida até agora
- Oportunidade específica que ela abre para esta pesquisa
```

---

## PROMPT 3 — Comparativo de Ferramentas AMS
**Equivalente ao arquivo:** `comparativo_ferramentas_synthetic_data_agro.html`
**Alimenta:** Seção 1.3 da proposta (Por que soluções existentes não resolvem)

```
Você é um especialista em software para organizações sem fins lucrativos e 
Association Management Software (AMS). Compare as principais soluções existentes 
para gestão de associações científicas e do terceiro setor:

Ferramentas a comparar:
  1. Wild Apricot (Personify)
  2. MemberPress (WordPress)
  3. Raklet
  4. NeonCRM
  5. MemberClicks
  6. Soluções brasileiras genéricas (Sympla, Eventbrite, sistemas customizados)

Critérios de análise (para cada ferramenta):
  A. Gestão de ciclos de mandato e transição de diretoria
     - Suporte a transferência de acesso entre gestões?
     - Histórico auditável de ações por gestão?
     - Onboarding para diretoria entrante?

  B. Preservação de memória institucional
     - Arquivamento contextualizado de decisões e processos?
     - Acesso a histórico de comunicações com membros?
     - Documentação de regras e processos internos?

  C. Aderência ao contexto científico-acadêmico
     - Módulo de submissão de trabalhos / call for papers?
     - Gestão de pareceristas e avaliação de propostas?
     - Integração com sistemas de publicação (anais, DOI)?

  D. Adequação ao terceiro setor brasileiro
     - Suporte a CNPJ de associação sem fins lucrativos?
     - NF de serviços / gestão fiscal brasileira?
     - Conformidade com LGPD?
     - Suporte em português / atendimento BR?

  E. Adaptabilidade a perfis técnicos variáveis de gestores
     - Interface adequada para gestores não-técnicos (voluntários)?
     - Personalização de fluxos sem necessidade de desenvolvedor?
     - Curva de aprendizado para novos membros de diretoria?

  F. Custo e modelo de licenciamento para associações pequenas/médias
     - Custo mensal para associação com 200–500 membros?
     - Limitações de funcionalidades em planos básicos?

Para cada critério, classifique: Atende plenamente / Atende parcialmente / 
Não atende / Não documentado.

Ao final, produza uma matriz comparativa e identifique explicitamente 
quais necessidades específicas de associações científicas brasileiras 
NENHUMA das ferramentas atende adequadamente.
```

---

## PROMPT 4 — Papers e Publicações Científicas
**Equivalente ao arquivo:** `papers_synthetic_data_unity_pecuaria.html`
**Alimenta:** Referências bibliográficas da proposta completa

```
Você é um pesquisador com acesso à literatura científica atualizada. Faça um 
levantamento de papers, teses e publicações relevantes para a seguinte 
interseção de temas:

  TEMA CENTRAL: Arquitetura de software para preservação de memória institucional 
  em organizações com liderança rotativa — com aplicação a associações científicas

Busque em: ACM Digital Library, IEEE Xplore, Google Scholar, Semantic Scholar, 
SciELO, BRAPCI (base brasileira de CI)

Categorias de busca:

1. GESTÃO DO CONHECIMENTO EM ORGANIZAÇÕES VOLUNTÁRIAS E SEM FINS LUCRATIVOS
   Queries sugeridas:
   - "knowledge management" AND "volunteer organizations"
   - "institutional memory" AND "nonprofit" OR "NGO"
   - "knowledge transfer" AND "leadership transition"
   - "organizational memory" AND "board turnover"

2. SISTEMAS DE INFORMAÇÃO PARA ASSOCIAÇÕES CIENTÍFICAS
   Queries sugeridas:
   - "association management system" AND "scientific societies"
   - "membership management software" AND "academic associations"
   - "information systems" AND "scholarly associations"

3. SISTEMAS ADAPTATIVOS E PERSONALIZAÇÃO PARA USUÁRIOS NÃO-TÉCNICOS
   Queries sugeridas:
   - "adaptive interface" AND "non-technical users"
   - "personalized systems" AND "volunteer" OR "occasional users"
   - "user adaptation" AND "organizational software"
   (Inclua: sistemas adaptativos para Web — área do mestrado ECA/USP 2000)

4. CONTINUIDADE INSTITUCIONAL E TRANSIÇÃO DE MANDATO
   Queries sugeridas:
   - "board transition" AND "information continuity"
   - "leadership succession" AND "knowledge retention"
   - "organizational continuity" AND "elected boards"

5. TERCEIRO SETOR E TECNOLOGIA NO BRASIL
   Queries sugeridas:
   - "terceiro setor" AND "sistemas de informação" (português)
   - "associações científicas" AND "gestão" AND "tecnologia"
   - "OSCIP" OR "associação sem fins lucrativos" AND "software"

Para cada paper encontrado, forneça:
- Título completo
- Autores e ano
- Periódico/conferência e fator de impacto quando disponível
- DOI ou link
- Resumo em 2–3 linhas com relevância específica para esta proposta
- Classificação: Alta / Média / Baixa relevância

Priorize papers dos últimos 10 anos (2015–2025). Inclua referências 
clássicas (antes de 2015) quando forem fundacionais para o campo.
```

---

## PROMPT 5 — Levantamento de Grants e Financiamentos
**Equivalente ao arquivo:** `grants_cv_livestock_synthetic_data.html`
**Alimenta:** Contextualização do ecossistema de fomento na proposta

```
Você é um especialista em fomento à pesquisa e inovação tecnológica. Faça um 
levantamento de projetos financiados (grants, editais, chamadas) ativos ou 
recentes (2020–2025) nas seguintes áreas:

  1. Sistemas de informação e software para o terceiro setor / sociedade civil
  2. Gestão do conhecimento em organizações sem fins lucrativos
  3. Transformação digital de associações científicas e acadêmicas
  4. Sistemas adaptativos e personalizados para usuários não-técnicos
  5. Inovação em software (SaaS) para gestão organizacional no Brasil

Agências a pesquisar:
  - FAPESP (especialmente PIPE, PITE, Pesquisa Inovativa em Pequenas Empresas)
  - CNPq (editais universais, chamadas temáticas)
  - FINEP (Inovação para a Competitividade, Inovacred)
  - BNDES (crédito para inovação em software)
  - NSF (EUA) — programas relevantes em software de impacto social
  - Horizon Europe — programas para software para sociedade civil
  - Fundações privadas brasileiras (Itaú Social, Lemann, Tide Setubal)

Para cada projeto/edital encontrado, forneça:
  - Título e número do edital/projeto
  - Agência financiadora
  - Instituição executora (quando aplicável)
  - Valor e período
  - Status (ativo / encerrado / em chamada)
  - Relevância para a proposta em questão (1 parágrafo)

Destaque especialmente:
  - Chamadas FAPESP PIPE aprovadas em áreas de SaaS, sistemas de gestão 
    ou software para o terceiro setor (buscar na Biblioteca Virtual FAPESP: 
    bv.fapesp.br)
  - Projetos que abordem digitalização de associações científicas no Brasil
  - Editais abertos ou previstos para 2025–2026 que sejam complementares 
    ou alternativos ao PIPE Jornada
```

---

## PROMPT 6 — Centros de Pesquisa e Grupos Relevantes
**Equivalente ao arquivo:** `centros_pesquisa_synthetic_data_plf.html`
**Alimenta:** Identificação de potenciais colaboradores e referências de autoridade

```
Você é um pesquisador com conhecimento do ecossistema acadêmico brasileiro e 
internacional. Mapeie grupos de pesquisa e centros relevantes para o tema:

  Sistemas de informação para gestão de organizações científicas, 
  gestão do conhecimento em terceiro setor e sistemas adaptativos para Web

BRASIL — pesquise no Diretório de Grupos de Pesquisa do CNPq (dgp.cnpq.br):

  1. Grupos em Ciência da Informação com foco em gestão do conhecimento
     - IBICT (Instituto Brasileiro de Informação em Ciência e Tecnologia)
     - Grupos nas ECA/USP, UFMG, UNB, UNESP Marília
  
  2. Grupos em Sistemas de Informação com foco em terceiro setor ou OSC
     - IME/USP, ICMC/USP, UNICAMP, PUC-SP
  
  3. Grupos em Comunicação e Cibercultura relevantes para associações científicas
     - ECA/USP (CELACC, POLIFONIAS, grupos de pós-graduação)
     - ABCiber como rede de pesquisadores (não como objeto de estudo)
  
  4. Núcleos de estudos sobre terceiro setor e organizações da sociedade civil
     - GESET (FGV), CEATS (FEA/USP), NESTH

INTERNACIONAL:

  1. Centros de referência em nonprofit technology e software para OSC
     - NTEN (Nonprofit Technology Enterprise Network — EUA)
     - TechSoup Global
     - Grupos acadêmicos em Information Systems for Civil Society

  2. Grupos de pesquisa em adaptive information systems
     - Grupos que trabalham com user modeling e personalization (relevante 
       para a H2 da proposta sobre interfaces adaptativas)

Para cada grupo/centro, forneça:
  - Nome e instituição
  - Líder/coordenador
  - Linha de pesquisa relevante para esta proposta
  - Publicações recentes de interesse
  - Possibilidade de colaboração (consultor, parceiro, referência de autoridade)
  - Link/contato
```

---

## PROMPT 7 — Recursos Online e Referências de Mercado
**Equivalente ao arquivo:** `recursos_online_synthetic_data_unity_plf.html`
**Alimenta:** Argumentação da seção 1.3 (por que soluções existentes falham)

```
Você é um especialista em software para associações e terceiro setor. 
Mapeie os principais recursos online, comunidades, relatórios de mercado 
e referências práticas sobre:

  Association Management Software (AMS) e gestão de associações científicas

1. RELATÓRIOS DE MERCADO E BENCHMARKS
   - Relatórios de analistas sobre o mercado de AMS (Gartner, Forrester, G2, Capterra)
   - Tamanho do mercado global de AMS e projeções de crescimento
   - Principais players e suas participações de mercado
   - Relatórios específicos sobre software para nonprofit/terceiro setor

2. COMUNIDADES E FÓRUNS RELEVANTES
   - ASAE (American Society of Association Executives) — recursos e pesquisas
   - NTEN (Nonprofit Technology Enterprise Network)
   - Comunidades brasileiras de gestores de associações e OSC
   - Fóruns de usuários das principais ferramentas AMS

3. SURVEYS E PESQUISAS DE USUÁRIO
   - Pesquisas sobre satisfação de usuários de AMS existentes
   - Relatórios sobre digitalização do terceiro setor no Brasil
   - Dados sobre adoção de tecnologia em associações científicas brasileiras
   - Surveys sobre dores de gestão em organizações com liderança rotativa

4. REFERÊNCIAS TÉCNICAS
   - Documentação técnica de APIs das principais ferramentas AMS
   - Padrões de interoperabilidade para dados de membros (se existirem)
   - Frameworks de modelagem de dados para associações (se existirem)

5. CASOS DE ESTUDO DOCUMENTADOS
   - Casos de falha de continuidade institucional em associações por falta de 
     sistema adequado (qualquer setor)
   - Cases de sucesso de digitalização de associações científicas
   - Exemplos de customização de AMS genéricos para contexto acadêmico

Para cada recurso, forneça: URL, tipo de recurso, relevância para a proposta 
e dado específico mais útil que ele contém.
```

---

## PROMPT 8 — Bibliografia Estruturada
**Equivalente ao arquivo:** `bibliografia_synthetic_data_plf_unity.html`
**Alimenta:** Referências bibliográficas da proposta completa (ABNT)

```
Com base nos resultados dos levantamentos anteriores sobre:
  - Gestão do conhecimento em organizações voluntárias com liderança rotativa
  - Association Management Software (AMS) e suas limitações
  - Sistemas adaptativos e personalizados para usuários não-técnicos
  - Terceiro setor e tecnologia no Brasil
  - Memória institucional e continuidade organizacional

Monte uma bibliografia estruturada em formato ABNT com:

SEÇÃO 1 — FUNDAMENTOS TEÓRICOS (10–15 referências)
  - Obras clássicas sobre gestão do conhecimento organizacional
    (Nonaka & Takeuchi; Davenport & Prusak; referências fundacionais)
  - Memória organizacional e continuidade institucional
  - Sistemas adaptativos para Web (incluir referências do mestrado ECA/USP 
    se disponíveis: sistemas adaptativos/personalizados Web, 2000)

SEÇÃO 2 — SISTEMAS DE INFORMAÇÃO PARA TERCEIRO SETOR (8–12 referências)
  - Papers sobre AMS e suas limitações documentadas
  - Estudos sobre digitalização de associações científicas
  - Pesquisas sobre adoção de tecnologia em organizações voluntárias

SEÇÃO 3 — CONTEXTO BRASILEIRO (5–8 referências)
  - IBGE/FASFIL — Fundações Privadas e Associações sem Fins Lucrativos no Brasil 
    (2016 e edições anteriores)
  - IPEA — Mapa das Organizações da Sociedade Civil
  - Pesquisas sobre terceiro setor tecnológico no Brasil

SEÇÃO 4 — REFERÊNCIAS DE MERCADO E DADOS (3–5 referências)
  - Relatórios de mercado AMS (Gartner/G2/Capterra)
  - Dados de tamanho de mercado e adoção

SEÇÃO 5 — LEGISLAÇÃO E NORMAS (3–5 referências)
  - Marco Legal das OSC (Lei 13.019/2014)
  - LGPD aplicada ao terceiro setor
  - Normas de governança para associações científicas no Brasil

Para cada referência forneça o formato ABNT completo e uma linha indicando 
a relevância específica para a proposta PIPE.
```

---

## Ordem de execução recomendada

| Prioridade | Prompt | Urgência para pré-proposta (29/07) | Urgência para proposta completa (28/09) |
|---|---|---|---|
| 1 | Prompt 1 — Estado da arte | Alta | Alta |
| 2 | Prompt 2 — Gap analysis | Alta | Alta |
| 3 | Prompt 3 — Comparativo AMS | Alta | Alta |
| 4 | Prompt 5 — Grants/fomento | Média | Alta |
| 5 | Prompt 4 — Papers | Baixa | Alta |
| 6 | Prompt 6 — Centros de pesquisa | Baixa | Média |
| 7 | Prompt 7 — Recursos online | Baixa | Média |
| 8 | Prompt 8 — Bibliografia | Não necessário | Alta |

**Para a pré-proposta de 29/07:** Execute os prompts 1, 2 e 3 esta semana. 
Os resultados fortalecem diretamente as seções 1.3 e 2 da pré-proposta atual.

**Para a proposta completa de 28/09:** Execute todos os 8 prompts e 
consolide os resultados como anexos técnicos da proposta.
```

---

*Documento gerado como parte da estratégia de submissão PIPE Jornada Tecnológica 2026*
*Alexandre Barizon ME — CNPJ 05.562.968/0001-25*
