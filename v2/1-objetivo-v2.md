# Campo a — Objetivos
## Proposta PIPE Jornada Tecnológica 2026 · Alexandre Barizon ME
## Arquivo: objetivo-v2.md · Limite: 4.000 caracteres

---

## TEXTO PARA SUBMISSÃO

Este projeto tem como objetivo geral investigar duas questões de pesquisa originais no domínio de sistemas de informação para organizações associativas com liderança rotativa, utilizando como ambiente experimental uma plataforma SaaS de gestão de associações científicas já desenvolvida pelo PR e implantada na ABCiber (Associação Brasileira de Pesquisadores em Cibercultura) como piloto.

A plataforma — que integra gestão de membros, eventos científicos com submissão de trabalhos, avaliação por pareceristas e gestão financeira — já se encontra funcional e em uso. Os recursos da Fase 1 não serão destinados ao desenvolvimento do produto, mas sim à investigação científica das duas hipóteses descritas a seguir, que dependem de coleta e análise de dados em ambiente real de uso.

**Objetivo 1 — Preservação ativa de memória institucional em organizações com liderança rotativa (H1)**

Investigar os requisitos mínimos de modelagem de dados para preservação ativa de memória institucional em organizações com governança democrática e mandatos curtos. A literatura de gestão do conhecimento organizacional (Nonaka & Takeuchi, Alavi & Leidner) concentra-se em empresas com quadros permanentes; organizações associativas com rotatividade obrigatória de liderança permanecem sub-representadas. A pesquisa buscará identificar quais entidades, relacionamentos e mecanismos de anotação contextual permitem que uma diretoria entrante acesse, compreenda e utilize o conhecimento acumulado pela gestão anterior sem depender de documentação manual ou da disponibilidade de pessoas. A investigação incluirá entrevistas estruturadas com gestores de associações científicas paulistas para mapear as dores reais de transição de mandato e confrontá-las com os requisitos propostos. O projeto avaliará se o módulo de memória institucional implementado na plataforma é capaz de reduzir em pelo menos 50% o tempo de onboarding de novas diretorias em relação ao processo atual baseado em planilhas e e-mails dispersos. Produzirá um framework de requisitos formais, inédito para o contexto de associações científicas brasileiras, contribuindo para a literatura de Sistemas de Informação e Gestão do Conhecimento.

**Objetivo 2 — Modelagem e análise de grafo temporal de colaboração científica (H2)**

Especificar e implementar o esquema de dados necessário para que as sequências de interação de pesquisadores com a plataforma (filiação → submissão → avaliação como parecerista → participação em evento → renovação) componham um grafo temporal de relações científicas analiticamente explorável. Hoje, os dados de engajamento associativo estão fragmentados em sistemas desconectados (planilhas de filiação, formulários de submissão, listas de presença) e nunca foram estruturados como grafo — o que impede qualquer análise de rede sobre esse tipo de interação. O objetivo é investigar se as propriedades topológicas desse grafo — grau nodal, centralidade de intermediação, coeficiente de clustering e força de laços fracos — são preditivas de colaborações científicas futuras, mensuráveis por co-autorias em periódicos indexados. A fundamentação matemática apoia-se na teoria dos grafos e em modelos de predição de links (Adamic–Adar, Jaccard, Common Neighbors), com AUC-ROC como métrica de desempenho. O dataset resultante será o primeiro do tipo disponível para associações científicas brasileiras.

A plataforma funcional existente é condição viabilizadora — não objeto — da pesquisa: ela gera os dados comportamentais necessários para a investigação das duas hipóteses. Sem sistema integrado em uso real, esses dados simplesmente não existem.

---

*Campo a — Objetivos · objetivo-v2.md*
*Proposta PIPE Jornada Tecnológica 2026 · Alexandre Barizon ME · CNPJ 05.562.968/0001-25*
