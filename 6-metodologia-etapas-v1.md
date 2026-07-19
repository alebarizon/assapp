# Campo 3 — Mãos à Obra (Metodologia e Etapas)
## Proposta PIPE Jornada Tecnológica 2026 · Alexandre Barizon ME
## Arquivo: metodologia-etapas-v1.md · Limite: 2.000 caracteres · Estimativa: ~1.880 caracteres

---

## TEXTO PARA SUBMISSÃO

A Fase 1 (12 meses) está organizada em quatro marcos sequenciais, cada um com entregável verificável:

**Marco 1 — Meses 1–3 · Revisão sistemática e especificação de requisitos (H1)**
Revisão da literatura em gestão do conhecimento organizacional, sistemas de informação para nonprofits e modelagem de memória institucional. Entrevistas estruturadas com gestores de 5 a 8 associações científicas paulistas (ABCiber, Intercom e parceiros) para mapeamento das dores reais de transição de diretoria. Entregável: framework de requisitos funcionais para módulo de memória institucional, com definição do esquema de dados de mandatos, histórico auditável e anotações contextuais.

**Marco 2 — Meses 2–6 · Prototipagem da interface adaptativa e testes A/B (H2)**
Desenvolvimento de dois protótipos do sistema: versão com interface adaptativa (inferência implícita de perfil por padrão de navegação) e versão estática de controle. Sessões de teste com gestores reais da ABCiber com coleta de task completion rate, time-on-task e NPS. Iteração baseada nos resultados. Entregável: relatório técnico comparando adoção entre as duas versões, com análise estatística.

**Marco 3 — Meses 4–9 · Implantação do protótipo e coleta de dados do grafo temporal (H4)**
Implantação do protótipo funcional na ABCiber cobrindo ao menos um ciclo completo de evento científico (submissão → avaliação → publicação de anais). Cada interação de pesquisador com o sistema é registrada como aresta tipada com timestamp no grafo. Entregável: dataset piloto do grafo temporal + cálculo de métricas de rede baseline (grau médio, densidade, coeficiente de clustering) + teste preliminar de predição de links (índices Adamic–Adar e Common Neighbors, avaliados por AUC-ROC).

**Marco 4 — Meses 10–12 · Validação integrada e documentação**
Medição do baseline de onboarding antes/após o sistema (H1). Análise final dos dados de usabilidade (H2). Avaliação do poder preditivo do grafo (H4). Submissão de artigo científico. Entregável: relatório final de Fase 1, framework publicável e dataset estruturado para a Fase 2.

---

## CONTAGEM DE CARACTERES (aproximada por seção)

| Seção | Caracteres estimados |
|---|---|
| Abertura ("Fase 1 em quatro marcos...") | ~75 |
| Marco 1 | ~430 |
| Marco 2 | ~410 |
| Marco 3 | ~500 |
| Marco 4 | ~330 |
| Frase de fechamento | ~100 |
| **Total estimado** | **~1.845** |

## NOTAS DE REDAÇÃO

**Marcos com sobreposição temporal:** os marcos 2 e 3 se sobrepõem intencionalmente (meses 2–6 e 4–9). Isso é realista — prototipagem e implantação acontecem em paralelo — e mostra ao avaliador que o PR sabe planejar um projeto de desenvolvimento com eficiência. Evite a armadilha de marcos perfeitamente sequenciais que somam 12 meses sem sobreposição: parece irrealista para avaliadores com experiência em P&D.

**Cada marco tem entregável nomeado:** "Entregável: X" ao final de cada marco responde diretamente ao que o avaliador precisa ver para aprovar pagamentos por etapa na Fase 1. O PIPE trabalha com relatórios de progresso — entregáveis claros facilitam essa prestação de contas.

**AUC-ROC e índices Adamic-Adar no Marco 3:** essa precisão matemática no campo de metodologia é o sinal para avaliadores de Exatas de que H4 é hipótese séria, não enfeite. Não é necessário explicar o que é AUC-ROC neste campo — qualquer avaliador de CC ou Matemática reconhece.

**Marco 4 — "baseline antes/após":** mencionar a medição de baseline de onboarding antes da implantação (H1) reforça que o projeto tem desenho experimental adequado — comparação com controle, não apenas medição pós-intervenção.

**Se precisar comprimir até 2.000:** cortar os conectores entre frases dentro de cada marco. O conteúdo essencial de cada entregável é inegociável.

---

*Campo 3 — Mãos à Obra (Metodologia e Etapas) · metodologia-etapas-v1.md*
*Proposta PIPE Jornada Tecnológica 2026 · Alexandre Barizon ME · CNPJ 05.562.968/0001-25*
