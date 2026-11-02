# ADR 0006 — Escrita no dinheiro do cliente só com confirmação explícita e risco classificado

Status: aceito (v5, frente D). Código: `src/app/actions.py` (`run_tool`, `confirm_action`, `decide_action`,
`_expired`), `src/app/risk.py` (`classify`, `policy`), `src/app/auth.py` (identidade do servidor).

**Contexto.** `open_dispute` e `request_anticipation` mexem em dinheiro (risk high); `request_terminal_support` abre
chamado. Um LLM que executa direto pode agir por injeção ou mal-entendido.

**Decisão.** A tool devolve uma ação pendente com `action_id` e validade; só `POST /actions/{id}/confirm` do próprio
cliente executa; acima do limite de `risk.py` ela vai para aprovação do operador (`/approve`, `/reject`). A identidade
vem do token, nunca do schema da tool.

**Alternativa descartada.** Executar na hora quando o LLM "entendeu" a confirmação no texto. Descartada pelo split
`approval` do eval (casos de confirmação ambígua e injeção); o resultado entra pelo bloco do `fill_readme`.

**Consequências.** Um turno a mais para o lojista em ações de risco; trilha completa em `GET /audit`.
