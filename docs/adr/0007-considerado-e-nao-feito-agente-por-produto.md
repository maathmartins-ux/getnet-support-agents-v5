# ADR 0007 — Considerado e NÃO feito: um agente especialista por produto

Status: rejeitado por ora (v5, frente D).

**Proposta.** Um agente por produto (maquininhas, Pix, antecipação, crediário, link de pagamento) em vez de um
Knowledge único sobre o corpus inteiro (`faq_agent` em `src/app/agents.py` + `src/app/rag.py`).

**Por que não agora.** O Router (`src/app/router.py`) teria de acertar o produto além da intenção, multiplicando os
pontos de erro de roteamento; o corpus é um só (site oficial, `data/knowledge/`) e o buscador híbrido já filtra por
trecho; o motor está congelado e o prazo da tentativa não comporta medir a troca.

**Alternativa mantida.** Knowledge único com `expand_query` (glossário) e `covered_hits` (cobertura mínima ou oferta
de humano).

**Gatilho para revisitar.** Se o eval por produto mostrar que o erro do Knowledge se concentra num produto com regra
própria (ex.: antecipação com taxa por cliente) ou se o corpus de um produto passar a vir de fonte separada (API
interna), reabrir este ADR e medir com o mesmo split antes de trocar.
