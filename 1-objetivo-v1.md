# Campo a — Objetivos
## Proposta PIPE Jornada Tecnológica 2026 · Alexandre Barizon ME
## Arquivo: objetivo-v1.md · Limite: 4.000 caracteres · Estimativa: ~3.100 caracteres

---

## TEXTO PARA SUBMISSÃO

Este projeto tem como objetivo geral investigar e especificar a arquitetura de software necessária para uma plataforma SaaS de gestão de associações científicas que: (i) preserve e transfira ativamente conhecimento institucional entre ciclos de diretoria; (ii) adapte sua interface ao perfil técnico variável de gestores voluntários; e (iii) capture dados comportamentais de pesquisadores em estrutura de grafo temporal, viabilizando a inferência de redes de colaboração científica.

**Objetivo 1 — Modelagem de conhecimento institucional (H1)**
Investigar os requisitos mínimos de modelagem de dados para preservação ativa de memória institucional em organizações com liderança rotativa de curto prazo. A pesquisa buscará identificar quais entidades, relacionamentos e mecanismos de anotação contextual permitem que uma diretoria entrante acesse, compreenda e utilize o conhecimento acumulado pela gestão anterior sem depender de documentação manual ou da disponibilidade de pessoas. Como métrica central, o projeto avaliará se a arquitetura proposta é capaz de reduzir em pelo menos 50% o tempo de onboarding de novas diretorias em relação ao processo atual baseado em planilhas e e-mails dispersos.

**Objetivo 2 — Interface adaptativa para gestores voluntários (H2)**
Investigar se técnicas de modelagem implícita de perfil de usuário — inferência de nível técnico a partir de padrões de navegação e frequência de uso, sem formulários explícitos — são transferíveis ao contexto específico de gestores voluntários com uso ocasional de sistemas organizacionais. A literatura de sistemas adaptativos (ACM UMAP) foca em usuários frequentes de plataformas de consumo; o comportamento de usuários ocasionais em sistemas organizacionais permanece sub-representado. O projeto produzirá e testará em ambiente real um protótipo de interface adaptativa, comparando métricas de adoção (task completion rate, time-on-task, NPS) entre versão adaptativa e versão estática.

**Objetivo 3 — Modelagem e análise de grafo temporal de colaboração científica (H4)**
Especificar e implementar o esquema de dados necessário para que as sequências de interação de pesquisadores com a plataforma (filiação → submissão → avaliação como parecerista → participação em evento → renovação) componham um grafo temporal de relações científicas analiticamente explorável. O objetivo é investigar se as propriedades topológicas desse grafo — grau nodal, centralidade de intermediação, coeficiente de clustering e força de laços fracos — são preditivas de colaborações científicas futuras, mensuráveis por co-autorias em periódicos indexados. A fundamentação matemática apoia-se na teoria dos grafos e em modelos de predição de links (Adamic–Adar, Jaccard, Common Neighbors), com AUC-ROC como métrica de desempenho na Fase 1.

**Objetivo instrumental**
Como condição necessária para a investigação das três hipóteses acima, o projeto desenvolverá um protótipo funcional da plataforma SaaS — baseado na arquitetura pré-existente do Wellflows (wellflows.online) e especializado para o domínio de associações científicas — implantado com a ABCiber (Associação Brasileira de Pesquisadores em Cibercultura) como ambiente piloto. A plataforma integrará nativamente os fluxos de gestão de membros, eventos científicos e submissão/publicação de trabalhos, eliminando a fragmentação atual entre ferramentas desconectadas (PKP-OCS, PKP-OJS, planilhas) e gerando os dados necessários para a investigação das hipóteses H1, H2 e H4.

---

*Campo a — Objetivos · objetivo-v1.md*
*Proposta PIPE Jornada Tecnológica 2026 · Alexandre Barizon ME · CNPJ 05.562.968/0001-25*
