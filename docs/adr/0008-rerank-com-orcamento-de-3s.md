# ADR 0008 — Rerank local medido e NÃO adotado; portão do denso recalibrado

Status: decidido no relógio do V5 (02/11/2026). Código: `src/app/rag.py` (`CrossRerankRetriever`), escolha em
`data/retriever.json` (`run_evals --choose-retriever --fast --apply --latency-budget-ms 3000`), limiar do portão em
`data/retriever.json` (`gate.min_cosine`). Complementa a ADR 0004.

**Contexto.** No gold de passagens essenciais deste corpus (38 perguntas com fonte), o denso e5-large mediu Recall@3
0,842 e MRR 0,715, abaixo das metas da avaliação da v4 (≥ 0,85 e ≥ 0,80); o denso + rerank bge-reranker-v2-m3-int8
(pool 10, 600 caracteres) mediu 0,947 e 0,807. Na rodada 1 ao vivo, 4 das 10 oficiais (official-01, 04, 06, 09, em
inglês) foram ao humano por `faq_no_source`: com o denso, o cosseno das perguntas com e sem fonte fica na mesma faixa
(0,82–0,88) e o piso de 0,88 recusava pergunta com fonte.

**Decisão.** A escolha foi refeita com orçamento explícito de 3 s por busca e o rerank continuou fora: medido com a
CPU disputada pelos subagentes do relógio, o p95 dele passou do orçamento (2862 ms na 1ª medida, acima de 3 s na
reavaliação). Ficou o denso, com o piso de cosseno do portão recalibrado de 0,88 para 0,82 (prova offline no commit
`5d7cee5`: as 4 oficiais passam a ter 2–5 trechos cobertos). Com o piso mais baixo o portão deixa de separar as
perguntas sem fonte; a recusa delas fica com o agente (`NOT_IN_SOURCES` no prompt do Knowledge) e é medida ao vivo.

**Consequências.** Recall@3 e MRR ficam abaixo da meta e assim são publicados no placar, com o rerank como próximo
passo medido (+0,105 de Recall@3 e +0,092 de MRR). A recusa de pergunta sem fonte depende do LLM, não do limiar.

**Alternativas consideradas.** *Rerank ligado* (0,947 / 0,807): passa as duas metas de busca, mas o p95 medido no
relógio ficou acima de 3 s por busca. *Manter o piso 0,88*: as 4 oficiais em inglês continuariam indo ao humano com
a fonte no índice. *Rerank por LLM*: medido no ensaio do kit, +0,01 de Recall@3 com +1 s por busca; não compensa.

**Não provado.** p95 do rerank neste corpus em máquina sem carga (no ensaio do kit, 1,13–1,25 s); taxa de recusa das
perguntas sem fonte só pelo LLM fora do eval.
