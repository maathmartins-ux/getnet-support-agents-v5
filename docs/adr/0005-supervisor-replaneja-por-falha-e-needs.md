# ADR 0005 — Supervisor que replaneja por falha e por `needs`, em vez de plano fixo

Status: aceito (v5, frente D). Código: `src/app/supervisor.py` (`collect_needs`, `accept_need`, `_defer_dependents`,
`next_step`, `run_table`, `run_llm`).

**Contexto.** `troubleshoot` precisa do dado do cliente (records) e, a partir dele, do manual (faq). O Router não sabe
de antemão qual dos dois será preciso, e um agente pode falhar (timeout, tool fora). No V5 o plano do `troubleshoot` é
só `records`: o faq entra pelo `needs` que a tool devolve (terminal offline → passos de conexão; código de recusa →
significado e o que fazer), e não por um plano fixo de dois passos (`tests/test_domain_router.py`, plano do `troubleshoot`; a ablação `no_needs` do eval mede o efeito).

**Decisão.** O plano inicial vem do Router (`docs/SPEC.md`); o supervisor aceita `needs` declarados pelo agente e,
numa falha, adia os dependentes e escolhe o próximo passo. Limites por turno (`MAX_MODEL_CALLS`, `MAX_TURN_USD`,
`NODE_TIMEOUT_S`) garantem parada.

**Alternativa descartada.** Plano fixo do Router (`SUPERVISOR_REPLAN=off`). Foi descartada pelo split `replan` /
`dependent` do eval: o número que a descarta é o da ablação em `evals/results/ablation_replan*.json`, publicado pelo
bloco do `scripts/fill_readme.py` (não copiado à mão aqui).

**Consequências.** Mais um modo a testar; a ablação `no_needs` isola o ganho do `needs` sobre o replanejamento só por falha.
