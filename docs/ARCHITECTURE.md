# Arquitetura — Getnet Support Agents (v5)

Descreve só o que o motor (`src/app/*.py`, congelado) faz. A spec é `docs/SPEC.md`; o domínio do desafio fica em
`src/app/domain/challenge/` (`flow.py`, `tools.py`) e `src/app/domain/challenge_prompts/`.

## 1. Agentes e supervisor

```mermaid
flowchart TD
  U["Lojista: POST /chat<br/>src/app/api.py"] --> G["Guardrail de entrada<br/>src/app/guardrails.py check_input"]
  G -- blocked --> B["Recusa sem plano"]
  G --> R["Router: intent + plano<br/>src/app/router.py (KNN + LLM)"]
  R --> S["Supervisor: run / run_table / run_llm<br/>src/app/supervisor.py"]
  S --> K["Knowledge = faq_agent<br/>src/app/agents.py"]
  S --> SP["Support = records_agent<br/>src/app/agents.py + domain/challenge/tools.py"]
  S --> E["Escalation = escalation_agent<br/>src/app/agents.py"]
  SP -- "needs (collect_needs / accept_need)" --> S
  K -- "falha → replanejar (_defer_dependents)" --> S
  S --> P["Enforce: número com evidência, idioma, PII<br/>src/app/pipeline.py _enforce + grounding.py"]
  P --> M["Memória da conversa<br/>src/app/memory.py Ledger + store.py"]
  P --> O["Resposta + trace_id<br/>src/app/observability.py"]
```

- `pipeline.handle` → `_guard_and_route` → `supervisor.run`. O supervisor executa o plano em lotes (`next_batch`,
  `run_batch`; `multi` roda faq ∥ records), aceita `needs` pedidos por um agente (`collect_needs`, `accept_need`),
  e numa falha adia os dependentes e replaneja (`_defer_dependents`, `next_step`). Ablação por `SUPERVISOR_REPLAN`
  (`on`, `no_needs`, `off`).
- Condição de parada por turno: `MAX_MODEL_CALLS`, `MAX_TURN_USD`, `NODE_TIMEOUT_S` (`budget_exceeded`,
  `_invoke_timed`). Estourou → entrega o já respondido e abre caso humano (`_exhaust`).

## 2. RAG e dados ao vivo (Knowledge)

```mermaid
flowchart LR
  Q["Pergunta + histórico<br/>agents.py expand_query (glossary.json)"] --> I["Índice híbrido BM25 + denso<br/>src/app/rag.py Index / FastEmbedEmbedder"]
  C["Corpus do site oficial<br/>data/knowledge/ via src/app/ingest.py"] --> I
  I --> H["Cobertura mínima<br/>agents.py covered_hits"]
  H -- coberto --> A["Resposta com citação<br/>agents.py cite_ids"]
  H -- sem cobertura --> W["Web restrita / gap → oferta humana<br/>agents.py _web_evidence, supervisor _offer_human_on_gap"]
  L["general: clima, câmbio<br/>src/app/live_data.py (Open-Meteo, BCB PTAX)"] --> A
  A --> N["Número só com evidência<br/>src/app/grounding.py unsupported_numbers"]
```

- O buscador é escolhido por medida (`run_evals --choose-retriever`, `data/retriever.json`; ADR 0004).
- `general` nunca abre caso; número de clima/câmbio só vem da API com data (`live_data.py`).

## 3. Escritas com confirmação e humano no laço (HITL)

```mermaid
sequenceDiagram
  participant L as Lojista
  participant SP as records_agent (agents.py)
  participant A as actions.py run_tool
  participant RK as risk.py classify
  participant OP as Operador (/operator, api.py)
  participant RS as resume.py
  L->>SP: "contesta a TX1006"
  SP->>A: open_dispute(args) — identidade do servidor (auth.py)
  A->>RK: classify (risk high)
  A-->>L: pendente: confirmar? (action_id, expira)
  L->>A: POST /actions/{id}/confirm (confirm_action)
  alt exige aprovação humana
    A->>OP: fila (POST /actions/{id}/approve | reject → decide_action)
  end
  Note over SP,OP: escalation_agent abre handoff (store.py); operador responde em /handoffs/{id}/reply
  OP->>RS: resume_after_human retoma o plano salvo (_save_pending)
  RS-->>L: resposta com a decisão do humano
```

- Nenhuma escrita roda sem confirmação explícita; ação expirada não executa (`actions._expired`).
- SLA do handoff: `api.sla_check` / `POST /handoffs/sla-check`; notificação em `src/app/notify.py`.
