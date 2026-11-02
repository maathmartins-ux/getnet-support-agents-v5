# ADR 0008 — Rerank local com orçamento de 3 s por busca

Status: aceito no relógio do V5 (02/11/2026). Código: `src/app/rag.py` (`CrossRerankRetriever`), escolha em
`data/retriever.json` (`run_evals --choose-retriever --fast --apply --latency-budget-ms 3000`). Complementa a ADR 0004.

**Contexto.** A escolha medida com o orçamento padrão da ADR 0004 (p95 ≤ 1500 ms por busca) ficou com o denso e5-large
sozinho: Recall@3 0,842 e MRR 0,715 no gold de passagens essenciais deste corpus, as duas abaixo das metas da
avaliação da v4 (≥ 0,85 e ≥ 0,80). O denso + rerank bge-reranker-v2-m3-int8 (pool 10, 600 caracteres) mediu 0,947 e
0,807, e foi rejeitado só pelo p95 de 2862 ms, medido com 8 subagentes do relógio disputando a CPU de 4 vCPU. No
ensaio do kit (máquina sem outra carga) o mesmo rerank mediu p95 de 1,13–1,25 s.

**Decisão.** Orçamento de 3 s por busca e rerank ligado na entrega. Uma resposta do Knowledge leva 7–14 s (LLM); o
rerank soma ~1–2 s a ela e é a única configuração medida que passa as duas metas de busca. A rodada 1 ao vivo rodou com
o denso (a escolha anterior); a rodada 2 e a entrega usam o denso + rerank, e o README separa as duas.

**Alternativas consideradas.** *Denso sozinho* (p95 235 ms): mais rápido, abaixo das duas metas. *Rerank por LLM*
(Haiku sobre o top-10): medido no ensaio do kit, +0,01 de Recall@3 com +1 s por busca e custo por chamada; não
compensa. *Pool 20*: p95 de ~4,7 s no ensaio, acima de qualquer orçamento razoável.

**Não provado.** p95 do rerank em máquina dedicada neste corpus (a medida do relógio foi sob carga); efeito do rerank no
juiz ao vivo, que só a rodada 2 mede.
